from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, chain
import os
import traceback
from langchain_core.runnables.config import run_in_executor
from .models import ProductDeal, UserPreference  
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
import json
import logging
import re
from langchain_groq import ChatGroq
from .searchapi_io import DealAggregator  
from transformers import pipeline
import asyncio
import hashlib
from datetime import datetime, timedelta
from collections import Counter

#nlp imports 
import spacy
from textblob import TextBlob
import re
from dataclasses import dataclass
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
import logging


logger = logging.getLogger(__name__)
load_dotenv()
 



@dataclass
class UserPreference:
    """Store user preferences for deal searching"""
    preferred_condition: Optional[str] = None  # New, Used, Refurbished
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    favorite_categories: List[str] = None


@dataclass
class ProductSearchParams:
    product_type: str
    attributes: List[str]
    colors: List[str]
    style_references: Optional[Dict[str, str]]

    price_range: Dict[str, Optional[float]]
    occasion: Optional[str]


from langchain_groq import ChatGroq
import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional, List
import random  # Add missing random import
import spacy
from textblob import TextBlob

import nltk
nltk.download('wordnet')

class UniversalSearchExtractor:
    def __init__(self):
        # Initialize Groq model
        self.llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.3)
        # Load spaCy model for fallback parsing

        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            logging.warning("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load('en_core_web_sm')
            
        # Pricing regex patterns
        self.price_patterns = [
            r'under\s+\$?(\d+(?:\.\d+)?)',
            r'less than\s+\$?(\d+(?:\.\d+)?)',
            r'below\s+\$?(\d+(?:\.\d+)?)',
            r'up to\s+\$?(\d+(?:\.\d+)?)',
            r'around\s+\$?(\d+(?:\.\d+)?)',
            r'about\s+\$?(\d+(?:\.\d+)?)',
            r'(?:from|between)\s+\$?(\d+(?:\.\d+)?)\s+(?:to|and)\s+\$?(\d+(?:\.\d+)?)',
            r'\$?(\d+(?:\.\d+)?)\s*-\s*\$?(\d+(?:\.\d+)?)',
            r'over\s+\$?(\d+(?:\.\d+)?)',
            r'more than\s+\$?(\d+(?:\.\d+)?)',
            r'above\s+\$?(\d+(?:\.\d+)?)',
            r'at least\s+\$?(\d+(?:\.\d+)?)',
            r'\$(\d+(?:\.\d+)?)'
        ]

    def extract_search_parameters(self, query: str) -> Dict:
        """
        Dynamically extract search parameters for multiple products from a query
        """
        logger.info(f"Starting parameter extraction for query: {query}")
        
        # For simple queries, try the lightweight method first
        try:
            if len(query.split()) < 15:  # Only use fast parser for short queries
                fast_results = self._fast_query_parse(query)
                
                # If we have clear product results, use those and avoid LLM
                if fast_results and len(fast_results.get('products', [])) > 0:
                    logger.info(f"Successfully extracted parameters using fast parser: {fast_results}")
                    return fast_results
        except Exception as e:
            logger.warning(f"Fast parsing failed: {str(e)}, falling back to LLM")
        
        # For more complex queries, use the LLM for better understanding
        prompt = f"""
        You are a shopping search assistant that understands natural conversational language.
        
        Analyze this shopping query and carefully identify:
        1. ALL products the user wants to buy (even if mentioned indirectly)
        2. Budget constraints for each product
        3. Important attributes like color, size, brand, condition, etc.
        4. User preferences and requirements
        
        IMPORTANT: Pay special attention to:
        - Budget constraints (price ranges, "under $X", etc.)
        - Key product features that are must-haves
        - Contextual hints about what the user is looking for
        - Multiple products if mentioned

        IMPORTANT: If the query clearly specifies a product type (like "coffee maker"),
        that MUST be the primary product_type in the results. Never substitute it with
        other interpretations unless absolutely necessary.


       
        Return a detailed JSON object with the following structure:
        {{
            "products": [
                {{
                    "product_type": "main product category",
                    "key_attributes": ["list of descriptive features"],
                    "color": "color if mentioned, null if not",
                    "brand": "brand if mentioned, null if not",
                    "price_range": {{
                        "min": null or minimum price number,
                        "max": null or maximum price number
                    }},
                    "search_keywords": ["important search terms that will help find this exact product"],
                    "must_have_features": ["features that are absolutely required"]
                }}
            ],
            "shared_context": {{
                "occasion": "event/occasion if mentioned",
                "urgency": "timeframe if mentioned",
                "location": "location if relevant",
                "overall_budget": "total budget if mentioned",
                "search_intent": "a brief description of what the user is trying to accomplish"
            }}
        }}

        EXAMPLES:
        1. "I need a good phone under $500 that has a great camera"
           → Product: phone, max_price: 500, key feature: great camera
           
        2. "Looking for a dress for my sister's wedding next month, something elegant but not too expensive"
           → Product: dress, occasion: wedding, timeframe: next month, style: elegant, price sensitivity: moderate
           
        3. "I want to upgrade my kitchen with a new blender that can crush ice and make smoothies easily, my budget is around $100"
           → Product: blender, features: crush ice, make smoothies, max_price: 100
        
        Query: {query}
        """

        try:
            logger.info("Sending query to LLM for analysis")
            response = self.llm.invoke(prompt)
            logger.info(f"Received LLM response: {response.content}")
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                parameters = json.loads(json_match.group(0))
                logger.info(f"Successfully parsed parameters: {parameters}")
                return self._enrich_parameters(parameters, query)
            else:
                logger.warning("No JSON found in LLM response, falling back to basic parsing")
                return self._fallback_parse(query)

        except Exception as e:
            logger.error(f"Error in parameter extraction: {str(e)}")
            logger.error(f"Full error details: {traceback.format_exc()}")
            return self._fallback_parse(query)
            
    def _fast_query_parse(self, query: str) -> Dict:
        """
        Fast lightweight parsing of shopping queries without using LLM
        """
        logger.info(f"Starting fast query parsing for: {query}")
        
        # Process with spaCy
        doc = self.nlp(query)
        
        # Extract products (PRODUCT entities or nouns that might be products)
        products = []
        potential_products = []
        
        # Process price info first to filter out money terms later
        price_ranges = self._extract_price_ranges(query)
        
        # Find money-related terms to filter out from products
        money_terms = []
        money_pattern = re.compile(r'\$?\d+\s*(?:dollars|bucks|USD)?')
        for match in money_pattern.finditer(query.lower()):
            money_terms.append(match.group().strip())
        
        # First look for product entities
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG"]:
                potential_products.append(ent.text)
                
        # If no product entities found, look for noun chunks
        if not potential_products:
            for chunk in doc.noun_chunks:
                # Filter out common non-product phrases and money terms
                if (not any(word.lower() in ["i", "you", "me", "my", "your"] for word in chunk.text.split()) and
                    not any(money_term in chunk.text.lower() for money_term in money_terms)):
                    potential_products.append(chunk.text)
        
        # Filter potential products to remove money references
        filtered_products = []
        for product in potential_products:
            if not any(money_term in product.lower() for money_term in money_terms):
                filtered_products.append(product)
        
        potential_products = filtered_products
        
        # Extract colors
        colors = []
        for token in doc:
            if token.pos_ == "ADJ" and token.text.lower() in [
                "red", "blue", "green", "yellow", "black", "white", "purple", "orange", 
                "gray", "grey", "brown", "pink", "gold", "silver"
            ]:
                colors.append(token.text)
        
        # Now build product objects
        for product in potential_products:
            # Skip common non-product words and money terms
            if (product.lower() in ["i", "you", "we", "they", "it", "this", "that", "these", "those", "today", "tomorrow"] or
                any(money_term in product.lower() for money_term in money_terms)):
                continue
                
            # Find closest price range
            product_price_range = self._get_price_range(product, price_ranges) if price_ranges else {"min": None, "max": None}
            
            # Find attributes including colors
            attributes = []
            product_colors = []
            
            # Simple proximity-based attribute association
            for token in doc:
                if token.pos_ == "ADJ" and token.text.lower() != product.lower():
                    # Check if this adjective is near the product
                    for prod_token in doc:
                        if prod_token.text.lower() == product.lower():
                            # If within 5 tokens, consider it related
                            if abs(token.i - prod_token.i) < 5:
                                if token.text.lower() in ["red", "blue", "green", "yellow", "black", "white", "purple", "orange", 
                                "gray", "grey", "brown", "pink", "gold", "silver"]:
                                    product_colors.append(token.text)
                                else:
                                    attributes.append(token.text)
            
            # Create the product entry
            products.append({
                "product_type": product,
                "key_attributes": attributes,
                "color": product_colors[0] if product_colors else None,
                "brand": None,  # Simple parsing can't reliably detect brands
                "price_range": product_price_range,
                "search_keywords": [product] + attributes + product_colors
            })
        
        # If we couldn't extract products with confidence, return empty results
        if not products:
            # Force a generic product with available price range as fallback
            if price_ranges:
                # Use the whole query as keywords but remove price terms
                clean_query = query
                for money_term in money_terms:
                    clean_query = clean_query.replace(money_term, '')
                
                keywords = [word.strip() for word in clean_query.split() if word.strip() and word.lower() not in ['i', 'am', 'looking', 'for', 'want', 'need', 'under', 'below', 'above', 'over']]
                
                products.append({
                    "product_type": "item",
                    "key_attributes": [],
                    "color": None,
                    "brand": None,
                    "price_range": price_ranges[0] if price_ranges else {"min": None, "max": None},
                    "search_keywords": keywords
                })
            else:
                return {"products": []}
            
        # Create final result
        result = {
            "products": products,
            "shared_context": {
                "occasion": None,
                "urgency": None,
                "location": None,
                "overall_budget": None
            }
        }
        
        logger.info(f"Fast parsing result: {result}")
        return result

    def _enrich_parameters(self, parameters: Dict, query: str) -> Dict:
        """
        Enrich the extracted parameters with additional analysis
        """
        try:
            # Add sentiment analysis for each product
            for product in parameters.get('products', []):
                # Analyze sentiment for product requirements
                sentiment = TextBlob(' '.join(product.get('key_attributes', [])))
                product['sentiment'] = {
                    'polarity': sentiment.sentiment.polarity,
                    'subjectivity': sentiment.sentiment.subjectivity
                }
                
                # Expand search keywords with synonyms
                expanded_keywords = set(product.get('search_keywords', []))
                for keyword in list(expanded_keywords):
                    synsets = wordnet.synsets(keyword)
                    for synset in synsets[:2]:  # Limit to top 2 synonyms
                        for lemma in synset.lemmas():
                            if '_' not in lemma.name():  # Avoid multi-word synonyms
                                expanded_keywords.add(lemma.name())
                product['search_keywords'] = list(expanded_keywords)

            return parameters

        except Exception as e:
            logging.error(f"Error enriching parameters: {str(e)}")
            return parameters

    def _fallback_parse(self, query: str) -> Dict:
        """Enhanced fallback parsing for multiple products"""
        doc = self.nlp(query.lower())
        
        # Initialize results
        products = []
        current_product = {}
        attributes = []
        colors = set()
        
        # Common color terms
        color_terms = {
            'red', 'blue', 'green', 'yellow', 'black', 'white', 'purple',
            'pink', 'orange', 'brown', 'gray', 'grey', 'silver', 'gold'
        }
        
        # Extract price ranges
        price_ranges = self._extract_price_ranges(query)
        
        # Process each token
        for token in doc:
            # Handle colors
            if token.text in color_terms:
                colors.add(token.text)
                
            # Handle adjectives
            if token.pos_ == 'ADJ':
                attributes.append(token.text)
                
            # Handle nouns (potential products)
            if token.pos_ == 'NOUN' and not token.text in color_terms:
                if current_product:
                    current_product['key_attributes'] = attributes.copy()
                    current_product['color'] = list(colors)[0] if colors else None
                    products.append(current_product)
                    attributes = []
                    colors = set()
                
                current_product = {
                    "product_type": token.text,
                    "key_attributes": [],
                    "color": None,
                    "brand": None,
                    "price_range": self._get_price_range(token.text, price_ranges),
                    "search_keywords": [token.text]
                }
        
        # Add the last product if exists
        if current_product:
            current_product['key_attributes'] = attributes
            current_product['color'] = list(colors)[0] if colors else None
            products.append(current_product)
        
        # If no products found, treat entire query as one product
        if not products:
            products = [{
                "product_type": "item",
                "key_attributes": attributes,
                "color": list(colors)[0] if colors else None,
                "brand": None,
                "price_range": {"min": None, "max": None},
                "search_keywords": query.split()
            }]

        return {
            "products": products,
            "shared_context": {
                "occasion": self._extract_occasion(query),
                "urgency": self._extract_urgency(query),
                "location": self._extract_location(query),
                "overall_budget": self._extract_overall_budget(query)
            }
        }

    def _extract_price_ranges(self, query: str) -> List[Dict]:
        """Extract all price ranges mentioned in the query"""
        price_ranges = []
        
        # Pattern for specific price ranges
        range_patterns = [
            r'between\s*\$?(\d+(?:\.\d{2})?)\s*(?:and|to|-)\s*\$?(\d+(?:\.\d{2})?)',
            r'\$?(\d+)\s*-\s*\$?(\d+)',
            r'under\s*\$?(\d+(?:\.\d{2})?)',
            r'less\s*than\s*\$?(\d+(?:\.\d{2})?)',
            r'max(?:imum)?\s*\$?(\d+(?:\.\d{2})?)',
            r'up\s*to\s*\$?(\d+(?:\.\d{2})?)'
        ]
        
        for pattern in range_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    price_ranges.append({
                        "min": float(match.group(1)),
                        "max": float(match.group(2))
                    })
                else:
                    price_ranges.append({
                        "min": None,
                        "max": float(match.group(1))
                    })
        
        return price_ranges

    def _get_price_range(self, product: str, price_ranges: List[Dict]) -> Dict:
        """Associate price range with product based on proximity"""
        default_range = {"min": None, "max": None}
        if not price_ranges:
            return default_range
        
        # If only one price range, use it
        if len(price_ranges) == 1:
            return price_ranges[0]
            
        # TODO: Implement proximity-based matching
        return default_range

    def _extract_occasion(self, query: str) -> Optional[str]:
        """Extract occasion/event from query"""
        occasion_keywords = {
            'wedding': ['wedding', 'ceremony', 'reception'],
            'party': ['party', 'celebration', 'birthday'],
            'work': ['work', 'office', 'business', 'professional'],
            'casual': ['casual', 'everyday', 'daily'],
            'formal': ['formal', 'gala', 'black tie']
        }
        
        query_lower = query.lower()
        for occasion, keywords in occasion_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return occasion
        
        return None

    def _extract_urgency(self, query: str) -> Optional[str]:
        """Extract urgency indicators from query"""
        urgency_patterns = [
            (r'need.*(?:today|now|asap|immediately|urgent)', 'immediate'),
            (r'need.*(?:this|next)\s+week', 'this_week'),
            (r'need.*(?:this|next)\s+month', 'this_month'),
            (r'by\s+(?:this|next)', 'deadline')
        ]
        
        for pattern, urgency in urgency_patterns:
            if re.search(pattern, query.lower()):
                return urgency
        
        return None

    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location context from query"""
        location_keywords = {
            'home': ['home', 'house', 'apartment'],
            'office': ['office', 'workplace', 'work'],
            'outdoor': ['outdoor', 'outside', 'garden'],
            'gym': ['gym', 'fitness', 'workout']
        }
        
        query_lower = query.lower()
        for location, keywords in location_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return location
        
        return None

    def _extract_overall_budget(self, query: str) -> Optional[float]:
        """Extract total budget for all items"""
        budget_patterns = [
            r'total\s+budget\s+(?:of\s+)?\$?(\d+(?:\.\d{2})?)',
            r'budget\s+(?:of\s+)?\$?(\d+(?:\.\d{2})?)',
            r'spend\s+(?:up\s+to\s+)?\$?(\d+(?:\.\d{2})?)\s+total',
            r'altogether\s+(?:under|less\s+than)?\s+\$?(\d+(?:\.\d{2})?)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None



class ContextResolver:
    """
    Handles merging of previous context with new queries
    """
    def __init__(self, llm):
        self.llm = llm
        self.context_prompt = ChatPromptTemplate.from_template("""
        You are a shopping assistant resolving ambiguous references. 
        Current conversation context: {context}
        New query: {query}

        Clarify if the reference is ambiguous by asking ONE short question.
        If clear, return the merged context in JSON format.
        """)

    async def resolve_context(self, query: str, previous_context: dict) -> dict:
        """
        Merge previous context with new query, clarifying ambiguities
        """
        chain = self.context_prompt | self.llm
        
        # First pass - try to merge automatically
        try:
            response = await chain.ainvoke({
                'context': json.dumps(previous_context),
                'query': query
            })
            
            if '?' in response.content:  # Needs clarification
                return {'needs_clarification': response.content}
                
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Context resolution failed: {str(e)}")
            return previous_context  # Fallback to previous context

class ProductRanker:
    """
    Ranks products based on user persona and needs
    """
    def __init__(self, llm):
        self.llm = llm
        self.ranking_prompt = ChatPromptTemplate.from_template("""
        Rank these products for a {persona} based on this query: {query}
        Products: {products}
        
        Return JSON with:
        - ranked_products: list of product IDs in order
        - explanation: short reasoning for top 3
        """)
    
    async def rank_products(self, products: List[Dict], query: str, persona: str = None) -> Dict:
        """
        Rank products based on persona and query
        """
        if not persona:
            return {'ranked_products': products, 'explanation': ''}
            
        chain = self.ranking_prompt | self.llm
        try:
            response = await chain.ainvoke({
                'persona': persona,
                'query': query,
                'products': json.dumps([{
                    'id': p.get('id'),
                    'title': p.get('title'),
                    'features': p.get('features', []),
                    'price': p.get('price')
                } for p in products])
            })
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Ranking failed: {str(e)}")
            return {'ranked_products': products, 'explanation': ''}

class ProductComparator:
    """
    Compares products based on specs and user needs
    """
    def __init__(self, llm):
        self.llm = llm
        self.comparison_prompt = ChatPromptTemplate.from_template("""
        Compare these products based on the user's request: {query}
        Products: {products}
        
        Return JSON with:
        - comparison: natural language comparison
        - key_differences: list of key differences
        - recommendation: which one to choose and why
        """)
    
    async def compare(self, products: List[Dict], query: str) -> Dict:
        """
        Generate detailed product comparison
        """
        if len(products) < 2:
            return {
                'comparison': '',
                'key_differences': [],
                'recommendation': ''
            }
            
        chain = self.comparison_prompt | self.llm
        try:
            response = await chain.ainvoke({
                'query': query,
                'products': json.dumps([{
                    'id': p.get('id'),
                    'title': p.get('title'),
                    'price': p.get('price'),
                    'features': p.get('features', []),
                    'specs': p.get('specs', {})
                } for p in products])
            })
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Comparison failed: {str(e)}")
            return {
                'comparison': f"Here's how these {len(products)} compare...",
                'key_differences': [],
                'recommendation': ''
            }

class PreferenceLearner:
    """
    Tracks and learns from user choices to improve recommendations
    """
    def __init__(self):
        self.choice_history = {}
        
    def track_choice(self, user_id: str, product: Dict, query: str):
        """
        Record when a user selects a product
        """
        if user_id not in self.choice_history:
            self.choice_history[user_id] = []
            
        self.choice_history[user_id].append({
            'product': product,
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
    
    def analyze_preferences(self, user_id: str) -> Dict:
        """
        Analyze user's historical choices to detect preferences
        Returns:
            {
                'inferred_persona': str,
                'price_sensitivity': float (0-1),
                'preferred_brands': List[str]
            }
        """
        if user_id not in self.choice_history or len(self.choice_history[user_id]) < 3:
            return {}
            
        history = self.choice_history[user_id]
        
        # Analyze price sensitivity
        avg_price = sum(p['product'].get('price',0) for p in history)/len(history)
        price_sensitivity = min(1, avg_price/1000)  # Normalize to 0-1 range
        
        # Detect brands
        brands = [
            p['product'].get('brand', '').lower() 
            for p in history 
            if p['product'].get('brand')
        ]
        brand_counts = Counter(brands)
        
        # Detect persona from query patterns
        persona_keywords = {
            'gamer': ['game', 'gaming', 'esports'],
            'programmer': ['code', 'programming', 'developer'],
            'student': ['student', 'school', 'college']
        }
        
        detected_persona = None
        for persona, keywords in persona_keywords.items():
            if any(kw in p['query'].lower() for kw in keywords for p in history):
                detected_persona = persona
                break
                
        return {
            'inferred_persona': detected_persona,
            'price_sensitivity': price_sensitivity,
            'preferred_brands': [b[0] for b in brand_counts.most_common(3)]
        }

class ConversationalDealFinder:
    """Enhanced conversational deal finder with memory and follow-ups"""
    
    def __init__(self):
        self.llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.3)
        from .searchapi_io import DealAggregator
        self.provider = DealAggregator()
        self.provider.set_llm(self)
        
        # Initialize query cache
        self.query_cache = {}
        
        # Initialize conversation state tracker
        self.conversation_state = {
            'current_products': [],
            'last_query': '',
            'last_category': '',
            'applied_filters': {},
            'last_intent': None,
            'conversation_turn': 0,
            'product_references': {},
            'user_preferences': {},
            # Keywords extracted from user queries
            'keywords': set(),
            # Last action taken
            'last_action': None
        }
        
        self.extractor = UniversalSearchExtractor()
        self.context_resolver = ContextResolver(self.llm)
        self.ranker = ProductRanker(self.llm)
        self.comparator = ProductComparator(self.llm)
        self.preference_learner = PreferenceLearner()
        self.query_cache = {}  # Add cache dictionary
        self.cache_expiry = timedelta(minutes=30)

    def _get_previous_deals_from_context(self, conversation_id: str) -> List[ProductDeal]:
        """Retrieve previous deals from conversation context"""
        if not conversation_id:
            return []
            
        try:
            from .models import ConversationMessage
            last_message = ConversationMessage.objects.filter(
                conversation_id=conversation_id,
                role='assistant',
                has_products=True
            ).order_by('-created_at').first()
            
            if not last_message or not last_message.search_results:
                return []
                
            previous_deals = []
            for deal in last_message.search_results:
                try:
                    previous_deals.append(ProductDeal(
                        product_id=deal.get('product_id'),
                        title=deal.get('name'),
                        price=float(deal.get('currentPrice', 0)),
                        original_price=float(deal.get('originalPrice', 0)) if deal.get('originalPrice') else None,
                        url=deal.get('productLink'),
                        image_url=deal.get('image_url'),
                        retailer=deal.get('retailer'),
                        description=deal.get('description'),
                        rating=float(deal.get('rating', 0)) if deal.get('rating') else None,
                        condition=deal.get('condition')
                    ))
                except Exception as e:
                    logger.error(f"Error converting previous deal: {str(e)}")
                    continue
                    
            return previous_deals
            
        except Exception as e:
            logger.error(f"Error getting previous deals: {str(e)}")
            return []
    


    def _validate_product_data(self, product: Dict) -> Dict:
        """Ensure product data has all required fields with proper defaults"""
        return {
            'product_type': product.get('product_type', 'item'),
            'key_attributes': [attr for attr in product.get('key_attributes', []) if attr],
            'color': product.get('color'),
            'brand': product.get('brand'),
            'price_range': {
                'min': float(product.get('price_range', {}).get('min')) if product.get('price_range', {}).get('min') else None,
                'max': float(product.get('price_range', {}).get('max')) if product.get('price_range', {}).get('max') else None
            },
            'search_keywords': [kw for kw in product.get('search_keywords', []) if kw],
            'must_have_features': [feat for feat in product.get('must_have_features', []) if feat],
            'shared_context': product.get('shared_context', {})
        }

    async def analyze_intent(self, query: str) -> dict:
        """
        Advanced query intent analyzer that detects various types of user intents
        """
        try:
            # Check if we have previous products in our conversation state
            has_previous_products = len(self.conversation_state['current_products']) > 0
            lower_query = query.lower().strip()
            
            # Create a prompt for the LLM to analyze the intent
            intent_prompt = ChatPromptTemplate.from_template("""
            You are an intent classifier for a shopping assistant. Analyze the user's message and determine the intent.
            
            Previous conversation context:
            - Last query: {last_query}
            - Last category searched: {last_category}
            - Previous products shown to user: {has_products}
            
            Current query: "{query}"
            
            Classify this as ONE of these intents:
            - new_search: User wants to search for a completely new product category
            - refine: User wants to refine previous search with new filters or constraints
            - comparison: User wants to compare previously shown products
            - recommendation: User wants recommendations from previous results
            - question: User is asking a specific question about previously shown product(s)
            - clarification: User is asking for clarification about a specific product
            - confirmation: User is confirming or affirming something
            
            Also determine:
            - references_previous: Does the query reference previously shown products? (true/false)
            - specific_product_reference: Does the query mention a specific product from previous results? (true/false)
            - persona: Any specific persona or use case mentioned (e.g., "programmer", "gamer", "office", etc.)
            
            Output format (JSON):
            ```json
            {{
                "intent": "[intent_type]",
                "references_previous": true/false,
                "specific_product_reference": true/false,
                "persona": "[persona if mentioned, otherwise null]",
                "requires_search": true/false,
                "explanation": "brief explanation of classification"
            }}
            ```
            Output only valid JSON without additional text.
            """)
            
            # Generate the analysis using the LLM
            chain = intent_prompt | self.llm
            response = await chain.ainvoke({
                "query": query,
                "last_query": self.conversation_state['last_query'] or "None",
                "last_category": self.conversation_state['last_category'] or "None",
                "has_products": "Yes, showing " + str(len(self.conversation_state['current_products'])) + " products" if has_previous_products else "No previous products"
            })
            
            # Extract the JSON from the response
            import re
            import json
            
            # Extract JSON from the response content
            content = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find any JSON-like structure
                json_match = re.search(r'{.*}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("Could not extract JSON from LLM response")
            
            # Parse the extracted JSON
            intent_analysis = json.loads(json_str)
            
            # Log the analysis for debugging
            logger.debug(f"Intent analysis for '{query}': {intent_analysis}")
            
            # Store the intent in conversation state
            self.conversation_state['last_intent'] = intent_analysis['intent']
            
            return intent_analysis
            
        except Exception as e:
            logger.error(f"Error in intent analysis: {str(e)}", exc_info=True)
            # Fallback to a simple analysis based on pattern matching
            return self._fallback_intent_analysis(query)
    
    async def _fallback_intent_analysis(self, query: str) -> dict:
        """
        Simple rule-based intent analysis as a fallback when LLM analysis fails
        """
        lower_query = query.lower().strip()
        has_previous_products = len(self.conversation_state['current_products']) > 0
        
        # Comparison intent
        comparison_terms = ["which", "which one", "which is", "compare", "better", "best", "difference", "vs", "versus"]
        if has_previous_products and any(term in lower_query for term in comparison_terms):
            return {
                'intent': 'comparison',
                'references_previous': True,
                'specific_product_reference': False,
                'persona': None,
                'requires_search': False,
                'explanation': 'User wants to compare previous products'
            }
            
        # Specific product reference
        reference_terms = ["this one", "that one", "the first", "the second", "the last", "number", "#"]
        if has_previous_products and any(term in lower_query for term in reference_terms):
            return {
                'intent': 'question',
                'references_previous': True,
                'specific_product_reference': True,
                'persona': None,
                'requires_search': False,
                'explanation': 'User is asking about a specific product'
            }
            
        # Recommendation request
        recommendation_terms = ["recommend", "suggestion", "best for", "good for", "ideal for", "suitable for"]
        persona_match = None
        for term in recommendation_terms:
            if term in lower_query:
                # Try to extract persona (e.g., "best for programmers")
                import re
                persona_match = re.search(fr"{term}\s+([\w\s]+)", lower_query)
                if persona_match:
                    break
                    
        if has_previous_products and (any(term in lower_query for term in recommendation_terms) or persona_match):
            return {
                'intent': 'recommendation',
                'references_previous': True,
                'specific_product_reference': False,
                'persona': persona_match.group(1) if persona_match else None,
                'requires_search': False,
                'explanation': 'User wants recommendations from previous results'
            }
            
        # Refinement intent
        refinement_terms = ["filter", "show me", "only", "just", "under", "over", "cheaper", "more expensive"]
        if has_previous_products and any(term in lower_query for term in refinement_terms):
            return {
                'intent': 'refine',
                'references_previous': True,
                'specific_product_reference': False,
                'persona': None,
                'requires_search': True,
                'explanation': 'User wants to refine previous search results'
            }
            
        # Default to new search if we have no clues or no previous products
        return {
            'intent': 'new_search',
            'references_previous': False,
            'specific_product_reference': False,
            'persona': None,
            'requires_search': True,
            'explanation': 'New product search'
        }
            
        # Finally use LLM for ambiguous cases
        try:
            prompt = f"""Determine shopping intent from query:
            Query: {query}
            
            Possible intents:
            - new_search
            - filter
            - followup
            - comparison
            
            Return JSON with 'intent' and 'explanation'"""
            response = await self.llm.ainvoke(prompt)
            return json.loads(response.content)
        except Exception:
            return {
                'intent': 'new_search',
                'requires_search': True,
                'explanation': 'Fallback to search'
            }

    async def _handle_recommendation_intent(self, query: str, persona: str = None) -> Dict:
        """
        Handle recommendation requests for previous products based on persona or use case
        """
        current_products = self.conversation_state['current_products']
        if not current_products:
            logger.warning("Recommendation intent detected but no previous products available")
            return {
                'message': "I don't have any products to recommend from. Could you start with a product search first?",
                'products': [],
                'followup_questions': []
            }
        
        try:
            # Extract persona if not provided but mentioned in query
            if not persona:
                persona_terms = ["for", "best for", "good for", "ideal for", "suitable for"]
                for term in persona_terms:
                    if term in query.lower():
                        import re
                        match = re.search(fr"{term}\s+([\w\s]+)", query.lower())
                        if match:
                            persona = match.group(1).strip()
                            break
            
            persona = persona or "general use"
            
            # Create a recommendation prompt
            recommendation_prompt = ChatPromptTemplate.from_template("""
            You are a helpful shopping assistant. The user is looking for recommendations for {persona}.
            
            Based on their previous search for "{last_query}", you need to rank and recommend the most suitable products.
            
            Products available:
            {product_list}
            
            Analyze these products and recommend the best options for {persona}, explaining briefly why each is suitable.
            Focus on specific features or attributes that make each product good for this use case.
            
            Format your response as a natural-sounding recommendation, not a list.
            Keep it conversational and helpful, addressing their specific use case of {persona}.
            """)
            
            # Format product list
            product_list = []
            for i, product in enumerate(current_products[:10]):  # Limit to first 10 products
                product_name = product.get('name') or product.get('title', f"Product {i+1}")
                price = product.get('currentPrice') or product.get('price', 'unknown price')
                if isinstance(price, (int, float)):
                    price = f"${price:.2f}"
                retailer = product.get('retailer', 'unknown retailer')
                product_list.append(f"{i+1}. {product_name} ({price} from {retailer})")
            
            # Generate recommendation
            chain = recommendation_prompt | self.llm
            response = await chain.ainvoke({
                "persona": persona,
                "last_query": self.conversation_state['last_query'],
                "product_list": "\n".join(product_list)
            })
            
            # Keep the same products but with a new personalized message
            return {
                'message': response.content if hasattr(response, 'content') else str(response),
                'products': current_products,  # Return the same products with new recommendations
                'followup_questions': self._generate_followup_questions(current_products, query, persona)
            }
            
        except Exception as e:
            logger.error(f"Error handling recommendation intent: {str(e)}", exc_info=True)
            return {
                'message': f"Based on your request for {persona}, I'd recommend checking out the options I found earlier.",
                'products': current_products,
                'followup_questions': []
            }
    
    async def _handle_comparison_intent(self, query: str) -> Dict:
        """
        Handle comparison requests between products from previous search results
        """
        current_products = self.conversation_state['current_products']
        if not current_products:
            logger.warning("Comparison intent detected but no previous products available")
            return {
                'message': "I don't have any products to compare. Could you start with a product search first?",
                'products': [],
                'followup_questions': []
            }
        
        try:
            # Extract product references (e.g., "first", "second", specific names)
            import re
            
            # Check for specific product indices
            first_product = None
            second_product = None
            
            # Try to match product references like "the first and third"
            # or specific names
            
            # Define common reference patterns
            ordinal_refs = {
                "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
                "1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "5th": 4,
                "#1": 0, "#2": 1, "#3": 2, "#4": 3, "#5": 4,
                "1": 0, "2": 1, "3": 2, "4": 3, "5": 4
            }
            
            # Check for common reference patterns
            referenced_indices = []
            for ref, idx in ordinal_refs.items():
                if ref in query.lower():
                    if idx < len(current_products):
                        referenced_indices.append(idx)
            
            # If we don't have specific references, compare the top 2-3 products
            if len(referenced_indices) < 2:
                referenced_indices = [0, 1] if len(current_products) >= 2 else [0]
            
            # Get the referenced products (at most 3)
            referenced_products = [current_products[idx] for idx in referenced_indices[:3] if idx < len(current_products)]
            
            # Create a comparison prompt
            comparison_prompt = ChatPromptTemplate.from_template("""
            You are a helpful shopping assistant. The user wants to compare products from their previous search.
            
            Products to compare:
            {product_list}
            
            The user's original search query was: "{last_query}"
            Their comparison request was: "{comparison_query}"
            
            Please provide a detailed comparison of these products, focusing on:
            1. Price and value for money
            2. Key features and specifications
            3. Advantages and disadvantages of each
            4. Which one might be most suitable and why
            
            Make your comparison conversational, balanced, and helpful. Include specific details from each product in your response.
            """)
            
            # Format product list for comparison
            product_list = []
            for i, product in enumerate(referenced_products):
                product_name = product.get('name') or product.get('title', f"Product {i+1}")
                price = product.get('currentPrice') or product.get('price', 'unknown price')
                if isinstance(price, (int, float)):
                    price = f"${price:.2f}"
                retailer = product.get('retailer', 'unknown retailer')
                features = product.get('description', 'No features available')
                product_list.append(f"Product {i+1}: {product_name}\nPrice: {price}\nRetailer: {retailer}\nFeatures: {features}")
            
            # Generate comparison
            chain = comparison_prompt | self.llm
            response = await chain.ainvoke({
                "product_list": "\n\n".join(product_list),
                "last_query": self.conversation_state['last_query'],
                "comparison_query": query
            })
            
            # Return the comparison results
            return {
                'message': response.content if hasattr(response, 'content') else str(response),
                'products': referenced_products,  # Return only the compared products
                'followup_questions': self._generate_followup_questions(referenced_products, query)
            }
            
        except Exception as e:
            logger.error(f"Error handling comparison intent: {str(e)}", exc_info=True)
            return {
                'message': "I've looked at the options you mentioned. They each have different features that might suit different needs.",
                'products': current_products[:3],  # Return the top 3 products as a fallback
                'followup_questions': []
            }
    
    async def _safe_analyze_intent(self, query: str) -> Dict:
        """
        Safely analyze user intent with exception handling
        """
        try:
            # Update the last query in conversation state
            self.conversation_state['last_query'] = query
            
            # Get the actual intent analysis
            intent_result = await self.analyze_intent(query)
            
            # Store the intent for future reference
            self.conversation_state['last_intent'] = intent_result.get('intent')
            
            return intent_result
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}", exc_info=True)
            # Fallback to a safe default
            return {
                'intent': 'new_search',
                'requires_search': True,
                'references_previous': False,
                'explanation': f"Fallback due to error: {str(e)}"
            }
            
    async def _handle_question_intent(self, query: str) -> Dict:
        """
        Handle specific questions about products from previous results
        """
        current_products = self.conversation_state['current_products']
        if not current_products:
            logger.warning("Question intent detected but no previous products available")
            return {
                'message': "I don't have any products to provide information about. Could you start with a product search first?",
                'products': [],
                'followup_questions': []
            }
            
        try:
            # Try to determine which product the user is asking about
            import re
            
            # Define common reference patterns
            ordinal_refs = {
                "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
                "1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "5th": 4,
                "#1": 0, "#2": 1, "#3": 2, "#4": 3, "#5": 4,
                "1": 0, "2": 1, "3": 2, "4": 3, "5": 4,
                "this one": 0, "that one": 0, "the one": 0
            }
            
            # Check for common reference patterns
            referenced_index = 0  # Default to the first product
            for ref, idx in ordinal_refs.items():
                if ref in query.lower():
                    if idx < len(current_products):
                        referenced_index = idx
                        break
            
            # Get the referenced product
            product = current_products[referenced_index] if referenced_index < len(current_products) else current_products[0]
            
            # Create a question answering prompt
            qa_prompt = ChatPromptTemplate.from_template("""
            You are a helpful shopping assistant. The user has a question about a product from their previous search.
            
            The user's question is: "{query}"
            
            The product they are asking about is:
            Name: {product_name}
            Price: {product_price}
            Retailer: {product_retailer}
            Description: {product_description}
            
            Please answer their question as specifically as possible using the information available.
            If the exact information isn't available, provide a helpful response based on similar products or general knowledge.
            Keep your response conversational and friendly.
            """)
            
            # Format product info
            product_name = product.get('name') or product.get('title', "This product")
            product_price = product.get('currentPrice') or product.get('price', 'unknown price')
            if isinstance(product_price, (int, float)):
                product_price = f"${product_price:.2f}"
            product_retailer = product.get('retailer', 'unknown retailer')
            product_description = product.get('description', 'No detailed description available')
            
            # Generate answer
            chain = qa_prompt | self.llm
            response = await chain.ainvoke({
                "query": query,
                "product_name": product_name,
                "product_price": product_price,
                "product_retailer": product_retailer,
                "product_description": product_description
            })
            
            # Return the answer with just the referenced product
            return {
                'message': response.content if hasattr(response, 'content') else str(response),
                'products': [product],  # Return only the referenced product
                'followup_questions': self._generate_followup_questions([product], query)
            }
            
        except Exception as e:
            logger.error(f"Error handling question intent: {str(e)}", exc_info=True)
            return {
                'message': f"Regarding your question about the product, I can tell you that it's available for {current_products[0].get('currentPrice') or current_products[0].get('price', 'a competitive price')} and is sold by {current_products[0].get('retailer', 'a reputable retailer')}.",
                'products': [current_products[0]],  # Return the first product as a fallback
                'followup_questions': []
            }

    async def generate_product_description(self, product: ProductDeal, query: str) -> str:
        """Generate AI-powered product description"""
        try:
            if not product or not query:
                return product.description or "No description available"

            prompt = f"""
            You are a shopping assistant describing products to users. 
            The user asked: "{query}"
            
            Create a compelling description for this product:
            - Name: {product.title}
            - Price: ${product.price}
            - Original Price: {f'${product.original_price}' if product.original_price else 'N/A'}
            - Retailer: {product.retailer}
            - Condition: {product.condition or 'Not specified'}
            - Rating: {product.rating or 'Not rated'}
            
            Focus on:
            1. Key features that match the user's query
            2. Value for money
            3. Any special offers or discounts
            4. Retailer reputation if known
            
            Keep it concise (2-3 sentences max).
            """
            
            response = self.llm.invoke(prompt)
            return response.content

        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            return product.description or "Unable to generate description"

    def get_user_preferences(self, user_id: str) -> Dict:
        """
        Enhanced to include persona tracking
        """
        if not hasattr(self, 'conversation_state'):
            self.conversation_state = {}
            
        if 'user_preferences' not in self.conversation_state:
            self.conversation_state['user_preferences'] = {}
            
        return self.conversation_state['user_preferences'].get(user_id, {})

    async def find_deals(self, query: Union[str, Dict], context: str = "", user_id: str = None) -> Dict:
        """
        Conversational product finder that handles both new searches and contextual follow-ups
        """
        # Initialize state if missing
        if not hasattr(self, 'conversation_state'):
            self.conversation_state = {
                'last_query': '',
                'last_category': '',
                'current_products': [],
                'last_intent': None,
                'conversation_turn': 0,
                'applied_filters': {},
                'product_references': {},
                'keywords': set(),
            }
            
        try:
            logger.info(f"Starting find_deals for query: {query} | context: {context}")
            
            # Safely extract query string
            query_str = ''
            if isinstance(query, dict):
                query_str = query.get('text', '')
            elif isinstance(query, str):
                query_str = query
            else:
                raise ValueError(f"Invalid query type: {type(query)}")
                
            if not query_str.strip():
                logger.warning("Empty query received")
                return self._empty_response("Please provide a search query")
            
            # Update conversation turn counter
            self.conversation_state['conversation_turn'] += 1
            is_first_turn = self.conversation_state['conversation_turn'] == 1
                
            # Analyze user intent - categorize as new search, followup, comparison, etc.
            intent_result = await self._safe_analyze_intent(query_str)
            intent_type = intent_result.get('intent', 'new_search')
            references_previous = intent_result.get('references_previous', False)
            persona = intent_result.get('persona')
            requires_search = intent_result.get('requires_search', True)
            
            logger.info(f"Detected intent: {intent_type} | Requires search: {requires_search} | References previous: {references_previous}")
            
            # If first query or definitely a new search, just do a standard search
            if is_first_turn or intent_type == 'new_search' or not self.conversation_state['current_products']:
                # Do a regular search
                search_terms = self._build_search_terms(query_str, context, True)
                products = await self._execute_product_search(search_terms)
                
                # Store search results and metadata
                self.conversation_state['current_products'] = products
                
                # Try to extract category from query
                category_words = query_str.lower().split()
                category_words = [w for w in category_words if len(w) > 3 and w not in ['show', 'find', 'get', 'want', 'need', 'looking', 'search']]
                if category_words:
                    self.conversation_state['last_category'] = category_words[0]
                
                # Generate conversational response
                if products:
                    ai_message = await self._generate_conversational_response(products, query_str)
                else:
                    ai_message = "I couldn't find any products that match your criteria. Would you like to try a different search?"
                    
                return {
                    'message': ai_message,
                    'products': products,
                    'followup_questions': self._generate_followup_questions(products, query_str, user_id) if products else []
                }
            
            # Handle different types of follow-up intents
            if intent_type == 'recommendation':
                # User wants recommendations from previous results based on a persona/use case
                return await self._handle_recommendation_intent(query_str, persona)
                
            elif intent_type == 'comparison':
                # User wants to compare products from previous results
                return await self._handle_comparison_intent(query_str)
                
            elif intent_type == 'question' or intent_type == 'clarification':
                # User has a specific question about a product
                return await self._handle_question_intent(query_str)
                
            elif intent_type == 'refine':
                # User wants to refine previous search results
                # Combine previous search with new constraints
                combined_query = f"{self.conversation_state['last_query']} {query_str}"
                search_terms = self._build_search_terms(combined_query, context, True)
                products = await self._execute_product_search(search_terms)
                
                # Update conversation state
                self.conversation_state['current_products'] = products
                
                # Generate response
                if products:
                    ai_message = await self._generate_conversational_response(products, combined_query)
                    ai_message = f"Based on your refinement, {ai_message.lower()}"
                else:
                    ai_message = "I couldn't find any products that match your refined criteria. Would you like to try different filters?"
                    
                return {
                    'message': ai_message,
                    'products': products,
                    'followup_questions': self._generate_followup_questions(products, query_str, user_id) if products else []
                }
            
            # Default fallback - treat as a new search
            search_terms = self._build_search_terms(query_str, context, True)
            products = await self._execute_product_search(search_terms)
            self.conversation_state['current_products'] = products
            
            if products:
                ai_message = await self._generate_conversational_response(products, query_str)
            else:
                ai_message = "I couldn't find any products that match your criteria. Would you like to try a different search?"
                
            return {
                'message': ai_message,
                'products': products,
                'followup_questions': self._generate_followup_questions(products, query_str, user_id) if products else []
            }
        except Exception as e:
            logger.error(f"Error in find_deals: {str(e)}", exc_info=True)
            return self._empty_response(f"I encountered an issue while searching: {str(e)}")
            
    async def _execute_product_search(self, search_terms: str) -> List[Dict]:
        """Execute the actual product search using the search provider"""
        # Check cache first
        cached = self.query_cache.get(search_terms)
        if cached and (datetime.now() - cached['timestamp']).total_seconds() < 3600:  # 1 hour cache
            logger.info(f"Using cached results for query: {search_terms}")
            return cached['products']
            
        try:
            # First validate we should proceed
            if not search_terms.strip():
                logger.warning("Empty search terms - skipping API call")
                return []
                
            logger.info(f"Executing REAL API search for: {search_terms}")
            
            # Extract price filters first
            max_price = None
            if 'under' in search_terms.lower() or 'below' in search_terms.lower():
                match = re.search(r'(under|below)\s*\$?(\d+)', search_terms.lower())
                if match:
                    max_price = float(match.group(2))
                    logger.info(f"Extracted max_price: {max_price} from search terms: {search_terms}")
            
            # Make the actual API call with conservative parameters
            results = await self.provider.search_deals_async(
                query=search_terms,
                max_price=max_price,
                max_results=10  # Increase to get more results
            )
            
            if not results or not isinstance(results, dict):
                logger.error(f"Invalid API response format: {type(results)}")
                return []
            
            # Log the complete structure of the results for debugging
            logger.debug(f"Raw results structure: {results.keys()}")
            
            # First check for 'searchapi' key (the actual key used by DealAggregator)
            if 'searchapi' in results and isinstance(results['searchapi'], list):
                products = results['searchapi']
                logger.info(f"Found {len(products)} products under 'searchapi' key")
            else:
                # Fall back to 'products' key if searchapi isn't present
                products = results.get('products', [])
                logger.info(f"Falling back to 'products' key, found {len(products)} products")
            
            # Convert products to appropriate format
            formatted_products = []
            for product in products:
                if isinstance(product, dict):
                    # Already a dict, keep as is
                    formatted_products.append(product)
                else:
                    # Convert ProductDeal object to dict
                    try:
                        formatted_products.append({
                            'product_id': getattr(product, 'product_id', ''),
                            'title': getattr(product, 'title', ''),
                            'price': getattr(product, 'price', 0),
                            'original_price': getattr(product, 'original_price', None),
                            'url': getattr(product, 'url', ''),
                            'image_url': getattr(product, 'image_url', ''),
                            'retailer': getattr(product, 'retailer', ''),
                            'description': getattr(product, 'description', ''),
                            'rating': getattr(product, 'rating', None),
                            'condition': getattr(product, 'condition', None),
                        })
                    except Exception as e:
                        logger.error(f"Error converting product object to dict: {str(e)}")
            
            if not formatted_products:
                logger.warning(f"No valid products returned for: {search_terms}")
                return []
                
            logger.info(f"API search successful - found {len(formatted_products)} formatted products")
            self.query_cache[search_terms] = {'products': formatted_products, 'timestamp': datetime.now()}
            return formatted_products
            
        except Exception as e:
            logger.error(f"API search failed: {str(e)}", exc_info=True)
            return []

    async def _generate_conversational_response(self, products: List[Dict], query: str) -> str:
        """Generate a truly dynamic AI response about the products found using the LLM"""
        try:
            if not products:
                return "I couldn't find any products matching your search. Would you like to try different search terms?"
            
            # Prepare a summary of the found products to feed to the LLM
            product_count = len(products)
            
            # Extract price information
            prices = []
            for p in products:
                if isinstance(p.get('price'), (int, float)):
                    prices.append(p.get('price'))
                elif p.get('currentPrice'):
                    prices.append(p.get('currentPrice'))
            
            price_range = "varied prices"
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                if min_price == max_price:
                    price_range = f"${min_price:.2f}"
                else:
                    price_range = f"${min_price:.2f} to ${max_price:.2f}"
            
            # Extract product details for the top 3 products
            top_products = []
            for i, product in enumerate(products[:3]):
                product_name = product.get('title') or product.get('name', 'unknown product')
                product_price = None
                
                if isinstance(product.get('price'), (int, float)):
                    product_price = product.get('price')
                elif product.get('currentPrice'):
                    product_price = product.get('currentPrice')
                    
                product_price_str = f"${product_price:.2f}" if product_price else "price unavailable"
                product_retailer = product.get('retailer', 'unknown retailer')
                
                top_products.append(f"{product_name} ({product_price_str} from {product_retailer})")
            
            # Create a prompt for the LLM to generate a conversational response
            prompt = ChatPromptTemplate.from_template("""
            You are a helpful shopping assistant. The user searched for: "{query}"
            
            Your search found {product_count} products with prices ranging from {price_range}.
            
            Some notable options include:
            {top_products}
            
            Please generate a friendly, conversational response that:
            1. Acknowledges their search query
            2. Mentions the number of results and price range
            3. Highlights 1-2 interesting aspects of the results
            4. Feels warm and helpful, not robotic
            5. Is concise (max 2-3 sentences)
            
            Your response should NOT include any placeholders or variables. It should be ready to show to the user.
            """)
            
            # Generate the response using the LLM
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "query": query,
                "product_count": product_count,
                "price_range": price_range,
                "top_products": "\n- " + "\n- ".join(top_products) if top_products else "No specific product details available"
            })
            
            # Extract just the content of the response
            ai_message = response.content if hasattr(response, 'content') else str(response)
            return ai_message
        
        except Exception as e:
            logger.error(f"Error generating LLM-based response: {str(e)}", exc_info=True)
            # Fallback to a simple response
            return f"I found {len(products)} results for your search on '{query}'."


    def _empty_response(self, message: str) -> Dict:
        """Standardized empty response"""
        return {
            'message': message,
            'products': [],
            'followup_questions': []
        }

    def _parse_natural_language_query(self, query: str) -> Dict:
        """Inject conversation context into searches"""
        params = self.extractor.extract_search_parameters(query)
        # Only inject previous products if the query is short or ambiguous
        inject_context = False
        if len(query.split()) < 5 and self.conversation_state['current_products']:
            inject_context = True
        # Optionally, check for ambiguous/follow-up keywords
        followup_keywords = ["more", "again", "like last", "similar", "another", "show me more"]
        if any(kw in query.lower() for kw in followup_keywords) and self.conversation_state['current_products']:
            inject_context = True
        if inject_context:
            import logging
            logging.info(f"Injecting previous products into context for query: '{query}'")
            params['shared_context'] = {
                **params.get('shared_context', {}),
                'previous_products': [p.title for p in self.conversation_state['current_products'][:3]]
            }
        else:
            import logging
            logging.info(f"NOT injecting previous products for query: '{query}' (specific or long query)")
        return params

    async def handle_comparison(self, query: str) -> Dict:
        """
        Handle comparison requests and generate response
        """
        comparison = await self.comparator.compare(self.conversation_state['current_products'], query)
        
        # Format final response
        response_parts = []
        if comparison.get('comparison'):
            response_parts.append(comparison['comparison'])
        if comparison.get('key_differences'):
            response_parts.append("\nKey differences:" + 
                "\n- " + "\n- ".join(comparison['key_differences']))
        if comparison.get('recommendation'):
            response_parts.append("\nRecommendation: " + comparison['recommendation'])
        
        return {
            'response': "\n".join(response_parts),
            'comparison_data': comparison
        }

    def _generate_followup_questions(self, products: List[Dict], query: str, user_id: str = None) -> List[str]:
        """
        Generate intelligent follow-up questions based on:
        - Current products
        - User's query
        - User preferences
        """
        if not products:
            return []
            
        prefs = self.get_user_preferences(user_id)
        questions = []
        
        # Price-related questions
        prices = [p.get('price', 0) for p in products]
        if len(products) >= 2 and max(prices) - min(prices) > 50:
            questions.append(
                f"Would you like me to focus on {'budget' if prefs.get('max_price') else 'higher-end'} options?"
            )
        
        # Comparison questions
        if len(products) >= 2:
            questions.extend([
                "Would you like a detailed comparison between these?",
                "Should I highlight the key differences?"
            ])
        
        # Persona-specific questions
        if prefs.get('persona'):
            questions.append(
                f"Would you like recommendations tailored for {prefs['persona']}?"
            )
        
        # Query-specific questions
        if 'cheap' in query.lower():
            questions.append("Should I look for more budget-friendly options?")
        elif 'best' in query.lower():
            questions.append("Would you like me to filter for top-rated items only?")
            
        # Default questions if none generated
        if not questions:
            questions = [
                "Would you like more details about any of these?",
                "Should I refine the search in any way?"
            ]
            
        return questions[:3]  # Return max 3 most relevant questions

    def record_user_choice(self, user_id: str, product: Dict, query: str):
        """
        Call this when user selects a product
        """
        self.preference_learner.track_choice(user_id, product, query)
        
        # Immediately update preferences for active session
        user_prefs = self.get_user_preferences(user_id)
        if product.get('price'):
            user_prefs['max_price'] = min(
                user_prefs.get('max_price', float('inf')), 
                product['price'] * 1.2  # Add 20% buffer
            )
        if product.get('brand'):
            if 'preferred_brands' not in user_prefs:
                user_prefs['preferred_brands'] = []
            if product['brand'] not in user_prefs['preferred_brands']:
                user_prefs['preferred_brands'].append(product['brand'])
                
    def _validate_result_relevance(self, product: Union[Dict, ProductDeal], search_query: str, context: str) -> bool:
        """
        Updated with robust price handling
        """
        try:
            # Get title safely
            title = getattr(product, 'title', None) or (product.get('title') if isinstance(product, dict) else None)
            if not title:
                return False
                
            # Handle price safely
            price_str = str(getattr(product, 'price', '') or (product.get('price', '') if isinstance(product, dict) else ''))
            try:
                float(price_str.replace('$', '').replace(',', '').split()[0])
            except (ValueError, AttributeError):
                return False
                
            # Rest of validation remains the same
            # Get attributes safely for both types
            description = getattr(product, 'description', '') or \
                         (product.get('description', '') if isinstance(product, dict) else '')
            categories = getattr(product, 'categories', []) or \
                        (product.get('categories', []) if isinstance(product, dict) else [])
            
            # Query matching
            query_terms = {term.lower() for term in search_query.split() if len(term) > 3}
            product_text = f"{title.lower()} {description.lower()}"
            
            if query_terms and not any(term in product_text for term in query_terms):
                return False
                
            # Context checks
            if context:
                context_lower = context.lower()
                important_terms = {'gift', 'present', 'birthday', 'anniversary', 'wedding'}
                
                if any(term in context_lower for term in important_terms):
                    if not any(cat.lower() in context_lower for cat in categories):
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
            
    def _get_user_persona(self, user_id: str) -> Optional[str]:
        """Get persona from user preferences"""
        if not user_id:
            return None
            
        prefs = self.get_user_preferences(user_id)
        return prefs.get('persona')

    def _build_search_terms(self, query: str, context: str, requires_search: bool) -> str:
        """
        Construct final search terms from query and context
        Returns: space-joined string of search terms
        """
        try:
            # Don't modify the query if it's already formatted with price filters
            price_patterns = [
                r'(under|below|less than)\s*\$?(\d+)',
                r'(over|above|more than)\s*\$?(\d+)',
                r'\$?(\d+)\s*-\s*\$?(\d+)'
            ]
            
            # Check if query already contains price filters
            query_has_price_filter = any(re.search(pattern, query.lower()) for pattern in price_patterns)
            
            # If query already has price filters, use it as is
            if query_has_price_filter:
                logger.debug(f"Query already contains price filters: {query}")
                # Only add context if needed
                if requires_search and context.strip():
                    return f"{query.strip()} {context.strip()}"
                return query.strip()
            
            # Otherwise build with components
            terms = []
            
            # Always include main query
            if query.strip():
                terms.append(query.strip())
                
            # Add context if exists and search is required
            if requires_search and context.strip():
                terms.append(context.strip())
                
            # Extract and include price filters only if not in original query
            price_filters = self._extract_price_filters(query)
            if price_filters:
                terms.append(price_filters)
                
            logger.debug(f"Built search terms from query: {query} | context: {context}")
            return ' '.join(terms) if terms else query
            
        except Exception as e:
            logger.error(f"Error building search terms: {str(e)}")
            return query
            
    def _extract_price_filters(self, query: str) -> str:
        """Extract price range filters from natural language"""
        price_patterns = [
            (r'(under|below|less than)\s*\$?(\d+)', 'max_price'),
            (r'(over|above|more than)\s*\$?(\d+)', 'min_price'),
            (r'\$?(\d+)\s*-\s*\$?(\d+)', 'range')
        ]
        
        for pattern, filter_type in price_patterns:
            match = re.search(pattern, query)
            if match:
                if filter_type == 'max_price':
                    return f"under {match.group(2)}"
                elif filter_type == 'min_price':
                    return f"over {match.group(2)}"
                elif filter_type == 'range':
                    return f"{match.group(1)} to {match.group(2)}"
        return ""

    async def _validate_product(self, product: Union[Dict, ProductDeal]) -> bool:
        """Robust product validation with price parsing"""
        try:
            # Validate product type
            if isinstance(product, str):
                return False
                
            # Check required fields
            if isinstance(product, dict):
                title = product.get('title')
                price = product.get('price')
            else:
                title = getattr(product, 'title', None)
                price = getattr(product, 'price', None)
            
            # Basic validation
            if not title:
                logger.debug(f"Product validation failed: missing title")
                return False
                
            # Price validation - price should already be a float from ProductDeal
            if not isinstance(price, (int, float)) or price <= 0:
                logger.debug(f"Product validation failed: invalid price {price}")
                return False
                
            return True
                
        except Exception as e:
            logger.exception(f"Product validation failed: {str(e)}")
            return False
            
        except Exception:
            logger.exception("Product validation failed")
            return False