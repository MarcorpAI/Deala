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
from typing import List, Dict, Optional
import json
import logging
import re
from langchain_groq import ChatGroq
from .searchapi_io import DealAggregator  
from transformers import pipeline
import asyncio
import hashlib

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
            r'\$?(\d+(?:\.\d{2})?)\s*(?:-|to)\s*\$?(\d+(?:\.\d{2})?)',
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



class ConversationalDealFinder:
    """Enhanced conversational deal finder with memory and follow-ups"""
    
    def __init__(self):
        self.llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.3)
        from .searchapi_io import DealAggregator
        self.provider = DealAggregator()
        self.provider.set_llm(self)
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.user_preferences = {}

        self.conversation_state = {
            'current_products': [],
            'search_intent': None,
            'user_preferences': {}
        }
        self.extractor = UniversalSearchExtractor()

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

    def detect_intent(self, query: str, context: str = "") -> dict:
        """Determine if the user wants a new search or just more info"""
        prompt = f"""
        Conversation Context: {context}
        Current Query: {query}
        
        Determine if the user wants to:
        1. COMPARE existing products (e.g., "which is best")
        2. FILTER current results (e.g., "only under $50")
        3. GET_MORE similar products
        4. NEW_SEARCH unrelated items
        
        Return JSON with: {intent, requires_search, explanation}
        """
        
        try:
            response = self.llm.invoke(prompt)
            intent_data = json.loads(response.content)
            
            if any(term in query.lower() for term in ["under $", "below $", "less than $"]):
                intent_data = {
                    "intent": "filter",
                    "requires_search": True,
                    "explanation": "Price filter requires new search"
                }
                
            return intent_data
        except Exception as e:
            logger.error(f"Error detecting intent: {str(e)}")
            return {
                "intent": "new_search",
                "requires_search": True,
                "explanation": "Fallback to search"
            }

    def generate_product_description(self, product: ProductDeal, query: str) -> str:
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

    def get_user_preferences(self, user_id: str) -> UserPreference:
        """Get or create user preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreference()
        return self.user_preferences[user_id]

    def generate_comparison(self, products: List[ProductDeal], user_id: str) -> str:
        """Generate a comparison of products"""
        if len(products) < 2:
            return ""
            
        prefs = self.get_user_preferences(user_id)
        
        product_list = "\n".join([
            f"Product {i+1}:\n"
            f"Title: {p.title}\n"
            f"Price: ${p.price}\n"
            f"Condition: {p.condition or 'Not specified'}\n"
            f"Rating: {p.rating or 'Not rated'}\n"
            for i, p in enumerate(products)
        ])
        
        prompt = f"""
        Compare these products based on the user's preferences:
        {product_list}
        
        User Preferences:
        - Max Price: {prefs.max_price or 'No limit'}
        - Preferred Condition: {prefs.preferred_condition or 'No preference'}
        - Min Rating: {prefs.min_rating or 'No minimum'}
        
        Provide a concise comparison (3-4 sentences) highlighting:
        1. Best value option
        2. Best quality option
        3. Any standout features
        4. Which one you recommend and why
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating comparison: {str(e)}")
            return "Here's a comparison of the products..."

    def _generate_followup_questions(self, query: str, results: List[ProductDeal], user_id: str) -> str:
        """Generate engaging follow-up prompts"""
        if not results:
            return random.choice([
                "Want to try a different search?",
                "Should we adjust the filters?",
                "Maybe try more general terms?"
            ])
        
        prompt = f"""Based on this query and results, suggest 2 fun follow-up questions:
        Original Query: {query}
        Results Shown: {len(results)} products
        
        Requirements:
        - Use emojis and humor
        - Suggest natural next steps
        - Max 1 line per question
        
        Examples:
        - "Want me to pick a favorite? I've got strong opinions! 🏆"
        - "Should we check shipping details? 🚚💨"
        - "Need help deciding? I'm great at spending imaginary money! 💸"
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return "Would you like more details about any of these?"

    
    def find_deals(self, natural_query: str, user_id: str, conversation_id: str = None) -> Dict:
        """Enhanced conversational deal finder with proper error handling"""
        try:
            # Initialize context and previous deals
            context = ""
            previous_deals = []
            
            # Build conversation context if conversation_id exists
            if conversation_id:
                try:
                    from .models import ConversationMessage
                    messages = ConversationMessage.objects.filter(
                        conversation_id=conversation_id
                    ).order_by('-created_at')[:5]  # Get last 5 messages
                    
                    context_parts = []
                    for msg in messages:
                        role = "User" if msg.role == 'user' else "Assistant"
                        context_parts.append(f"{role}: {msg.content}")
                    
                    context = "\n".join(context_parts)
                    previous_deals = self._get_previous_deals_from_context(conversation_id) or []
                    
                except Exception as e:
                    logger.error(f"Error loading conversation context: {str(e)}")
                    context = ""
                    previous_deals = []

            # Initialize result structure
            result = {
                "deals": {'searchapi': []},
                "comparison": "",
                "followup_questions": "",
                "user_preferences": self.get_user_preferences(user_id),
                "shared_context": {},
                "query_understanding": "",
                "response": ""
            }

            # Detect intent with proper error handling
            try:
                intent_data = self.detect_intent(natural_query, context)
                intent = intent_data.get('intent', 'new_search')  # Default to new search
                logger.info(f"Detected intent: {intent}")
            except Exception as e:
                logger.error(f"Error detecting intent: {str(e)}")
                intent = 'new_search'  # Safe default
                intent_data = {
                    "intent": intent,
                    "requires_search": True,
                    "explanation": "Fallback to search due to error"
                }

            # Handle different intents appropriately
            if intent == 'comparison' and previous_deals:
                logger.info("Handling comparison intent with previous deals")
                result['deals']['searchapi'] = previous_deals
                result['comparison'] = self.generate_comparison(previous_deals, user_id)
                result['response'] = "Let me analyze your options... ✨"
                
            elif intent in ['new_search', 'filter'] or not previous_deals:
                logger.info(f"Performing new search for intent: {intent}")
                query_result = self._parse_natural_language_query(f"{context}\nUser: {natural_query}")
                
                # Inject conversation context into search parameters
                if previous_deals:
                    query_result['shared_context'] = {
                        **query_result.get('shared_context', {}),
                        'previous_products': [p.title for p in previous_deals[:3]]
                    }
                
                if query_result.get('products'):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        search_results = loop.run_until_complete(
                            self._search_products_parallel(
                                query_result['products'],
                                context=context
                            )
                        )
                        # Validate results match conversation context
                        validated_results = [
                            r for r in search_results[0].get('searchapi', [])
                            if self._validate_result_relevance(r, natural_query, context)
                        ]
                        result['deals']['searchapi'] = validated_results
                    except Exception as e:
                        logger.error(f"Search error: {str(e)}")
                        result['deals']['searchapi'] = []
                    finally:
                        loop.close()

            # Generate appropriate response based on results
            try:
                if intent == 'comparison' and result['comparison']:
                    result['response'] = result['comparison']
                else:
                    result['response'] = self._generate_response_from_results(
                        products=result['deals']['searchapi'],
                        query=natural_query,
                        user_id=user_id,
                        context=context
                    )
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                result['response'] = "Here are some options I found..."

            # Generate follow-ups using current context
            try:
                result['followup_questions'] = self._generate_followup_questions(
                    query=natural_query,
                    results=result['deals']['searchapi'],
                    user_id=user_id,
                    context=context
                )
            except Exception as e:
                logger.error(f"Error generating followups: {str(e)}")
                result['followup_questions'] = "Would you like more details?"

            return result

        except Exception as e:
            logger.error(f"Critical error in find_deals: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "deals": {'searchapi': []},
                "comparison": "",
                "followup_questions": "Want to try a different search?",
                "user_preferences": self.get_user_preferences(user_id),
                "shared_context": {},
                "query_understanding": "",
                "response": "Oops! My shopping cart hit a bump 😅 Let's try again?"
            }
        
    def _generate_response_from_results(self, products: List[ProductDeal], query: str, user_id: str) -> str:
        """Generate response using actual found products"""
        if not products:
            return random.choice([
                "🕵️♂️ My shopping radar came up empty! Let's try different terms?",
                "Hmm, the shopping gremlins hid all the good stuff! 🧌 Try another search?"
            ])
        
        # Build product highlights
        highlights = []
        for i, product in enumerate(products[:3]):  # Use top 3 products
            price = f"${product.price:.2f}"
            emoji = self._get_price_emoji(product.price)
            highlights.append(
                f"- {product.title} - {self._get_creative_description(product)} {emoji} ({price})"
            )
        
        # Generate response
        prompt = f"""You're a fun shopping assistant who just found these products:
        {chr(10).join(highlights)}
        
        Create a 2-3 sentence response with:
        1. Exciting opening line
        2. Brief mention of what makes these special
        3. Playful call-to-action
        Include relevant emojis and keep it under 200 characters.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return f"Found {len(products)} options for '{query}'! Need details on any?"

    
    def _generate_friendly_response(self, products: List[ProductDeal], query: str, user_id: str) -> str:
        """Generate initial friendly product presentation"""
        if not products:
            return random.choice([
                "🕵️♂️ My shopping radar came up empty! Let's try different terms?",
                "Hmm, the shopping gremlins hid all the good stuff! 🧌 Try another search?"
            ])
        
        # Count products by price range to make the response more dynamic
        budget_friendly = sum(1 for p in products if p.price < 50)
        mid_range = sum(1 for p in products if 50 <= p.price < 200)
        premium = sum(1 for p in products if p.price >= 200)
        
        prompt = f"""You're a fun shopping assistant responding to: '{query}'
        Found {len(products)} products including:
        - {budget_friendly} budget-friendly options 💰
        - {mid_range} mid-range picks ⚖️  
        - {premium} premium finds 💎

        Create a response with:
        1. Playful opening line matching the query tone
        2. Highlight 1-2 standout products with emojis
        3. Fun fact about one product
        4. Playful call-to-action
        
        Example style:
        "Holy guacamole! 🥑 Found these gems while searching for '{query}':
        - The '{products[0].title}' is flying off shelves! {products[0].price} {'💸' if products[0].price > 100 else '💰'}
        - '{products[1].title}' has shoppers raving ({products[1].rating}⭐)
        Did you know? The {products[2].title} comes with {random.choice(['free shipping', 'a surprise gift', 'a 2-year warranty'])}!
        Want me to work my magic on any of these? ✨"
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating friendly response: {str(e)}")
            top_products = "\n".join([f"- {p.title} (${p.price})" for p in products[:2]])
            return f"Found some cool options for '{query}'!\n{top_products}\nWant details about any?"


    
    def _get_price_emoji(self, price: float) -> str:
        if price < 20: return "💰"
        if price < 100: return "💸"
        return "🤑"

    def _get_creative_description(self, product: ProductDeal) -> str:
        prompts = [
            f"Describe '{product.title}' in 5 words or less",
            f"What's quirky about {product.title}?",
            f"Make a playful tagline for {product.title}"
        ]
        try:
            response = self.llm.invoke(random.choice(prompts))
            return response.content.strip('"\'')
        except Exception:
            return "Great find!"
    

    def _generate_comparison_response(self, products: List[ProductDeal], user_id: str) -> str:
        """Generate fun product comparison"""
        if len(products) < 2:
            return ""
        
        prefs = self.get_user_preferences(user_id)
        product_list = "\n".join([f"{p.title} (${p.price})" for p in products])
        
        prompt = f"""Compare these products like a witty friend:
        {product_list}
        
        User Preferences:
        - Budget: {'$'+str(prefs.max_price) if prefs.max_price else 'No limit'}
        - Condition: {prefs.preferred_condition or 'Any'}
        
        Include:
        1. Funny analogies ("This blender is the Ferrari of kitchen gadgets")
        2. Emoji reactions to key features
        3. Clear recommendation with humorous reasoning
        4. Avoid bullet points - keep it conversational
        
        Example style:
        "The $45 vase is like a reliable Honda 🚗 (gets the job done), while the $89 coffee kit \
        is that extra friend who brings espresso to funerals ☕️⚰️ (intense but memorable). \
        My vote? Go wild with coffee - life's too short for boring gifts! 😈"
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return "Here's how these compare..."

    
    def _generate_safe_response(self, products: List[ProductDeal], query: str, user_id: str, intent: str, previous_deals: List) -> str:
        """Generate response with null checks"""
        products = products or []
        try:
            if intent == 'comparison':
                return self._generate_comparison_response(products, user_id)
            
            # Always try to generate friendly response for non-comparison queries
            friendly_response = self._generate_friendly_response(products, query, user_id)
            if friendly_response:
                return friendly_response
                
            # Fallbacks only if friendly response fails
            if not products:
                return random.choice([
                    "🕵️♂️ My shopping radar came up empty! Let's try different terms?",
                    "Hmm, the shopping gremlins hid all the good stuff! 🧌 Try another search?"
                ])
                
            return "Here are some options I found..."
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Here are some options I found..."

    
    def _generate_safe_comparison(self, products: List[ProductDeal], user_id: str) -> str:
        """Generate comparison with null checks"""
        products = products or []
        try:
            if len(products) >= 2:
                return self._generate_comparison_response(products, user_id)
            return ""
        except Exception:
            return ""

    
    def _generate_safe_followups(self, query: str, results: List[ProductDeal], user_id: str) -> str:
        """Generate followups with null checks"""
        results = results or []
        try:
            return self._generate_followup_questions(query, results, user_id)
        except Exception:
            return "Would you like more details?"

    

    def _validate_result_relevance(self, product: ProductDeal, query: str, context: str) -> bool:
        """Validate if product matches conversation context"""
        context = context.lower()
        query = query.lower()
        title = product.title.lower()
        
        # Must not match these irrelevant terms
        blacklist = ['magazine', 'subscription', 'user manual']
        if any(term in title for term in blacklist):
            return False
            
        # Should match context keywords
        keywords = []
        if "birthday" in context:
            keywords.extend(['gift', 'present'])
        if "18 year old" in context:
            keywords.extend(['teen', 'young adult', 'college'])
            
        return any(kw in title for kw in keywords) if keywords else True

    
    def _validate_search_results(self, products: List[ProductDeal], context: str) -> List[ProductDeal]:
        """Filter irrelevant results"""
        return [
            p for p in products 
            if self._matches_context(p, context) and 
            not self._is_irrelevant(p)
        ]


    


    def _parse_natural_language_query(self, query: str) -> Dict:
        """Inject conversation context into searches"""
        params = self.extractor.extract_search_parameters(query)
        if self.conversation_state['current_products']:
            params['shared_context'] = {
                **params.get('shared_context', {}),
                'previous_products': [p.title for p in self.conversation_state['current_products'][:3]]
            }
        return params

    async def _search_products_parallel(self, products: List[Dict], context: str = "") -> List[Dict]:
        """Enhanced parallel search with conversation context awareness"""
        search_tasks = []
        
        for product in products:
            # Enhance search terms with context if needed
            search_terms = list(dict.fromkeys([
                *product.get('search_keywords', []),
                product.get('product_type'),
                *product.get('key_attributes', []),
                product.get('color')
            ]))
            
            # If no specific terms, use conversation context
            if not search_terms and context:
                doc = self.nlp(context.lower())
                nouns = [chunk.text for chunk in doc.noun_chunks]
                search_terms = list(set(nouns))[:5]  # Use top 5 nouns from context
            
            if not search_terms:
                search_terms = [product.get('product_type', 'gift')]
                
            search_query = ' '.join(search_terms).strip()
            
            # Add context-based modifiers
            if "birthday" in context.lower() and "18" in context.lower():
                search_query = f"birthday gift for 18 year old {search_query}"
            
            price_range = product.get('price_range', {})
            
            logger.info(f"Searching for: {search_query} (context: {context[:50]}...)")
            
            search_tasks.append(
                self.provider.search_deals_async(
                    query=search_query,
                    min_price=price_range.get('min'),
                    max_price=price_range.get('max'),
                    max_results=5
                )
            )
        
        results = await asyncio.gather(*search_tasks)
        
        # Post-process results for context relevance
        processed_results = []
        for retailer_result in results:
            processed_products = []
            for product in retailer_result.get('searchapi', []):
                if self._validate_result_relevance(product, "", context):
                    processed_products.append(product)
            processed_results.append({'searchapi': processed_products})
        
        return processed_results