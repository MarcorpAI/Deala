from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, chain
import os
from langchain_core.runnables.config import run_in_executor
from .models import ProductDeal, UserPreference  # Changed this line
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import logging
import re
from langchain_groq import ChatGroq
from .deal_providers import DealAggregator
from transformers import pipeline

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

# class UniversalSearchExtractor:
#     def __init__(self):
#         # Initialize Groq model
#         self.llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.3)
#         # Load spaCy model for fallback parsing
#         try:
#             self.nlp = spacy.load('en_core_web_sm')
#         except OSError:
#             logging.warning("Downloading spaCy model...")
#             import subprocess
#             subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
#             self.nlp = spacy.load('en_core_web_sm')

#     def extract_search_parameters(self, query: str) -> Dict:
#         """
#         Dynamically extract search parameters from any query using Groq
#         """
#         prompt = f"""
#         Analyze this shopping query carefully. Consider the main product and any contextual requirements.
#         Focus on what the user actually wants to buy, not just mentioned items.
        
#         For example:
#         - "suit that goes with black tie" → Main product is a suit, black tie is context
#         - "running shoes and socks" → Two products: running shoes, socks
#         - "dress for a beach wedding" → Main product is a dress, beach/wedding are contexts

#         In some cases , the User might be searching for multiple products at once, so you mus make sure you include those products in the search keywords as well.
        
#         For example:
#         - "i am going for a dinner and i need what to wear, i want to buy a midi dress, high heels (most be comfortable), and a purse -> Here the user has expressed need for multipl products, A purse , a dress and high heels.
#         - "i am looking for some home furniture a desk an ergonimic chair, a lamp and some wall shelves -> Here the user has expressed need for multiple products, A desk , an ergonimic chair, a lamp and some wall shelves. 
#         SO ALWAYS KEEP THIS IN MIND WHEN ANALYZING THE QUERY. VERY IMPORTANT.
        
#         Return a JSON object with the following keys:
#         {{
#             "product_type": "main product category",
#             "key_attributes": ["list of descriptive features"],
#             "color": "color if mentioned, null if not",
#             "brand": "brand if mentioned, null if not",
#             "price_range": {{
#                 "min": null or minimum price number,
#                 "max": null or maximum price number
#             }},
#             "search_keywords": ["important search terms"]
#         }}

#         Query: {query}
#         """

#         try:
#             # Get response from Groq
#             response = self.llm.invoke(prompt)
            
#             # Extract JSON from response
#             content = response.content
#             json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
#             if json_match:
#                 parameters = json.loads(json_match.group(0))
#                 return parameters
            
#             return self._fallback_parse(query)

#         except Exception as e:
#             logging.error(f"Search parameter extraction error: {str(e)}")
#             return self._fallback_parse(query)


    

    
     

#     def _fallback_parse(self, query: str) -> Dict:
#         """Basic fallback parsing method"""
#         return {
#             "product_type": self._extract_product_type(query),
#             "key_attributes": self._extract_attributes(query),
#             "color": self._extract_color(query),
#             "brand": None,
#             "price_range": {
#                 "min": None,
#                 "max": self._extract_max_price(query)
#             },
#             "search_keywords": query.split()
#         }

#     def _extract_product_type(self, query: str) -> str:
#         """Extract product type using spaCy"""
#         product_types = [
#             'laptop', 'phone', 'dress', 'shoes', 
#             'camera', 'headphones', 'watch', 
#             'bag', 'computer', 'tablet'
#         ]
        
#         doc = self.nlp(query.lower())
        
#         # Check for nouns that match product types
#         for token in doc:
#             if token.lemma_ in product_types:
#                 return token.lemma_
            
#         # Look for nouns if no specific product type is found
#         for token in doc:
#             if token.pos_ == 'NOUN':
#                 return token.lemma_
        
#         return 'item'

#     def _extract_attributes(self, query: str) -> List[str]:
#         """Extract descriptive attributes using spaCy"""
#         doc = self.nlp(query.lower())
        
#         attributes = []
#         for token in doc:
#             # Look for adjectives and relevant descriptors
#             if token.pos_ == 'ADJ':
#                 attributes.append(token.text)
        
#         return attributes

#     def _extract_color(self, query: str) -> Optional[str]:
#         """Extract color from query"""
#         colors = [
#             'red', 'blue', 'green', 'yellow', 
#             'black', 'white', 'purple', 'pink', 
#             'orange', 'brown', 'gray', 'grey',
#             'silver', 'gold', 'navy', 'maroon'
#         ]
        
#         query_lower = query.lower()
#         words = query_lower.split()
        
#         # Check for exact color matches
#         for color in colors:
#             if color in words:
#                 return color
                
#         # Check for color variations
#         for word in words:
#             for color in colors:
#                 if color in word:  # catches things like "blackish", "bluish", etc.
#                     return color
        
#         return None

#     def _extract_max_price(self, query: str) -> Optional[float]:
#         """Extract maximum price using regex"""
#         price_patterns = [
#             r'under\s*\$?(\d+(?:\.\d{2})?)',
#             r'less\s*than\s*\$?(\d+(?:\.\d{2})?)',
#             r'\$?(\d+(?:\.\d{2})?)\s*or\s*less',
#             r'max(?:imum)?\s*\$?(\d+(?:\.\d{2})?)',
#             r'up\s*to\s*\$?(\d+(?:\.\d{2})?)'
#         ]
        
#         for pattern in price_patterns:
#             match = re.search(pattern, query, re.IGNORECASE)
#             if match:
#                 try:
#                     return float(match.group(1))
#                 except ValueError:
#                     continue
        
#         return None

#     def _extract_price_range(self, query: str) -> Dict[str, Optional[float]]:
#         """Extract price range using regex"""
#         # Pattern for range like "between $100 and $200" or "$100-$200"
#         range_patterns = [
#             r'between\s*\$?(\d+(?:\.\d{2})?)\s*(?:and|to|-)\s*\$?(\d+(?:\.\d{2})?)',
#             r'\$?(\d+(?:\.\d{2})?)\s*(?:-|to)\s*\$?(\d+(?:\.\d{2})?)'
#         ]
        
#         for pattern in range_patterns:
#             match = re.search(pattern, query, re.IGNORECASE)
#             if match:
#                 try:
#                     return {
#                         "min": float(match.group(1)),
#                         "max": float(match.group(2))
#                     }
#                 except ValueError:
#                     continue
        
#         # If no range found, check for maximum price
#         max_price = self._extract_max_price(query)
#         return {
#             "min": None,
#             "max": max_price
#         }





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

    def extract_search_parameters(self, query: str) -> Dict:
        """
        Dynamically extract search parameters for multiple products from a query
        """
        logger.info(f"Starting parameter extraction for query: {query}")
        
        prompt = f"""
        Analyze this shopping query and identify ALL products the user wants to buy.
        Pay special attention to multiple items and their individual requirements.
        
        Return a JSON object with the following structure:
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
                    "search_keywords": ["important search terms"]
                }}
            ],
            "shared_context": {{
                "occasion": "event/occasion if mentioned",
                "urgency": "timeframe if mentioned",
                "location": "location if relevant",
                "overall_budget": "total budget if mentioned"
            }}
        }}

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
        # self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.3)

        from .deal_providers import DealAggregator  # Delayed import
        self.provider = DealAggregator()

        self.provider.set_llm(self)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.user_preferences = {}  # Dict to store preferences by user_id
        
        # Query analysis prompt
        self.query_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a shopping assistant that extracts search parameters from natural language queries. Return a JSON object with the following keys:
            {
                "product": "product name",
                "price_range": {"min": null, "max": number or null},
                "condition": "condition or null",
                "requirements": []
            }"""),
            ("human", "{query}")
        ])

        
        self.description_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an empathetic and enthusiastic shopping assistant who truly understands what makes each product special and how it can improve people's lives. Your goal is to connect with users on a personal level while helping them find perfect products.

            When describing products, imagine you're having a warm, friendly conversation with the user. Consider their needs, emotions, and daily life experiences. Create descriptions that:
            
            1. Show genuine enthusiasm about features that matter most to the user
            2. Paint vivid pictures of how the product could fit into their life
            3. Acknowledge their specific needs based on their search query
            4. Provide honest value assessment in a caring way
            
            Format your response with these engaging sections:
            [Overview]: Share the most exciting features with genuine enthusiasm (1 compelling sentence)
            [Best For]: Paint a relatable picture of ideal usage scenarios (1-2 warm, descriptive sentences)
            [Value]: Give an honest, friendly take on the price-to-value ratio (1 conversational sentence)
            [Recommendation]: Offer heartfelt, personalized advice based on their search (1 caring, tailored suggestion)
            
            Guidelines for tone:
            - Be conversational and warm, like a knowledgeable friend
            - Use "you" and "your" to make it personal
            - Share authentic enthusiasm where deserved
            - Acknowledge potential concerns empathetically
            - Keep it honest and genuine, never overly sales-y
            
            Remember: Every user has a unique story and needs. Connect their story to the product's benefits."""),
            
            ("human", """User Query: {query}
            Product Details:
            - Name: {title}
            - Price: ${price}
            - Condition: {condition}
            - Retailer: {retailer}""")
        ])
                    
        # Comparison prompt
        self.comparison_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a shopping expert helping users compare products. Consider:
            1. Price differences and value for money
            2. Condition and seller ratings
            3. Features and specifications
            4. User's previous preferences
            
            Provide a natural, conversational comparison.
            """),
            ("human", """
            Previous preferences: {preferences}
            Products to compare: {products}
            
            Please compare these options and suggest the best choice.
            """)
        ])
        
        # Follow-up prompt
        self.followup_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            Generate relevant follow-up questions based on the user's query and the search results.
            Consider asking about:
            1. Specific features they need
            2. Preferred price range adjustments
            3. Condition preferences
            4. Alternative product suggestions
            
            Keep questions natural and contextual.
            """),
            ("human", """
            Original query: {query}
            Search results: {results}
            User preferences: {preferences}
            
            Generate 1-2 relevant follow-up questions.
            """)
        ])


   


    # def generate_product_description(self, product: ProductDeal, query: str) -> str:
    #     """Generate AI-powered product description"""
    #     try:
    #         chain = LLMChain(llm=self.llm, prompt=self.description_prompt)
    #         response = chain.invoke({
    #             "query": query,
    #             "title": product.title,
    #             "price": product.price,
    #             "condition": product.condition or "Not specified",
    #             "retailer": product.retailer,
    #             "original_desc": product.description
    #         })
    #         return response['text']
    #     except Exception as e:
    #         logger.error(f"Error generating description: {str(e)}")
    #         return product.description  # F



    def generate_product_description(self, product: ProductDeal, query: str) -> str:
        """Generate AI-powered product description with improved error handling"""
        try:
            # Validate input
            if not product or not query:
                logger.warning("Missing product or query for description generation")
                return product.description or "No description available"

            # Create chain with explicit error handling
            chain = LLMChain(llm=self.llm, prompt=self.description_prompt)
            
            # Prepare input, ensuring no None values
            input_data = {
                "query": query or "",
                "title": product.title or "Unnamed Product",
                "price": product.price or 0,
                "condition": product.condition or "Not specified",
                "retailer": product.retailer or "Unknown",
                "original_desc": product.description or ""
            }

            # Invoke with timeout and explicit error capture
            response = chain.invoke(input_data)
            
            # Validate response
            if not response or 'text' not in response:
                logger.error("Invalid response from LLM")
                return product.description

            return response['text']

        except Exception as e:
            # Comprehensive error logging
            logger.error(f"Detailed description generation error: {str(e)}")
            logger.error(f"Error Type: {type(e)}")
            
            # Optional: Log full traceback
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback to original description
            return product.description or "Unable to generate description"

    def get_user_preferences(self, user_id: str) -> UserPreference:
        """Get or create user preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreference()
        return self.user_preferences[user_id]

    def update_user_preferences(self, user_id: str, query_result: dict):
        """Update user preferences based on their queries"""
        prefs = self.get_user_preferences(user_id)
        
        if query_result.get('price_range', {}).get('max'):
            prefs.max_price = query_result['price_range']['max']
        
        if query_result.get('condition'):
            prefs.preferred_condition = query_result['condition']

 
    
    
    


    # def _parse_natural_language_query(self, query: str) -> Dict:
    #     """Universal search parameter extraction"""
    #     try:
    #         extractor = UniversalSearchExtractor()
    #         search_params = extractor.extract_search_parameters(query)
            
    #         # Generate search terms
    #         search_terms = " ".join(filter(None, [
    #             search_params.get('product_type', ''),
    #             *search_params.get('key_attributes', []),
    #             search_params.get('color', ''),
    #             search_params.get('brand', '')
    #         ]))
            
    #         return {
    #             "product": search_params.get('product_type', 'item'),
    #             "price_range": search_params.get('price_range', 
    #                 {"min": None, "max": None}),
    #             "search_terms": search_terms
    #         }
    #     except Exception as e:
    #         logger.error(f"Universal search extraction error: {str(e)}")
    #         return {
    #             "product": "item",
    #             "price_range": {"min": None, "max": None},
    #             "search_terms": query
    #         }


    def _parse_natural_language_query(self, query: str) -> Dict:
        """Universal search parameter extraction"""
        logger.info(f"Starting natural language query parsing: {query}")
        try:
            extractor = UniversalSearchExtractor()
            search_params = extractor.extract_search_parameters(query)
            logger.info(f"Extracted search parameters: {search_params}")
            
            return {
                "products": search_params.get('products', []),
                "shared_context": search_params.get('shared_context', {})
            }
        except Exception as e:
            logger.error(f"Error in natural language parsing: {str(e)}")
            logger.error(f"Full error details: {traceback.format_exc()}")
            return {
                "products": [{
                    "product_type": "item",
                    "price_range": {"min": None, "max": None},
                    "search_keywords": query.split()
                }],
                "shared_context": {}
            }



    def generate_comparison(self, products: List[ProductDeal], user_id: str) -> str:
        """Generate a comparison of products"""
        if len(products) < 2:
            return ""
            
        prefs = self.get_user_preferences(user_id)
        
        # Format the products for comparison
        formatted_products = []
        for i, p in enumerate(products):
            condition = "Not specified"
            if "Condition:" in p.description:
                condition = p.description.split("Condition:")[-1].split("\n")[0]
                
            product_str = (
                f"Product {i+1}:\n"
                f"Title: {p.title}\n"
                f"Price: ${p.price}\n"
                f"Condition: {condition}\n"
            )
            formatted_products.append(product_str)
        
        formatted_products = "\n".join(formatted_products)
        
        # Create the LLMChain
        chain = LLMChain(llm=self.llm, prompt=self.comparison_prompt)
        
        # Pass a dictionary with the required keys
        return chain.invoke({
            "preferences": str(prefs),  # Ensure this matches the prompt placeholder
            "products": formatted_products  # Ensure this matches the prompt placeholder
        })

    def generate_followup_questions(self, query: str, results: List[ProductDeal], user_id: str) -> str:
        """Generate contextual follow-up questions"""
        if not results:
            return "No products found. Would you like to adjust your search criteria?"

        prefs = self.get_user_preferences(user_id)
        formatted_results = "\n".join([
            f"- {p.title} (${p.price})"
            for p in results[:3]  # Use top 3 results for context
        ])
        
        chain = LLMChain(llm=self.llm, prompt=self.followup_prompt)
        return chain.invoke({
            "query": query,
            "results": formatted_results,
            "preferences": str(prefs)
        })

  
    # def find_deals(self, natural_query: str, user_id: str) -> Dict:
    #     """Process natural language query and return structured response"""
    #     try:
    #         # Parse the query using NLP
    #         query_result = self._parse_natural_language_query(natural_query)
    #         logger.debug(f"Parsed Query Result: {query_result}")
            
    #         # Update user preferences
    #         self.update_user_preferences(user_id, query_result)
            
    #         # Get deals using the optimized search terms
    #         deals = self.provider.search_deals(
    #             query=query_result["search_terms"],  # Use the processed search terms
    #             min_price=query_result["price_range"].get("min"),
    #             max_price=query_result["price_range"].get("max"),
    #             max_results=5
    #         )
            
    #         # Rest of your code remains the same...
    #         all_deals = deals['ebay'] + deals['amazon'] + deals['walmart']
    #         comparison = self.generate_comparison(all_deals, user_id) if len(all_deals) > 1 else ""
    #         followup = self.generate_followup_questions(natural_query, all_deals, user_id)
            
    #         return {
    #             "deals": deals,
    #             "comparison": comparison,
    #             "followup_questions": followup,
    #             "user_preferences": self.get_user_preferences(user_id)
    #         }
    #     except Exception as e:
    #         logger.error(f"Error in find_deals: {str(e)}")
    #         return {
    #             "deals": {'ebay': [], 'amazon': [], 'walmart': []},
    #             "comparison": "",
    #             "followup_questions": "An error occurred while searching for deals.",
    #             "user_preferences": self.get_user_preferences(user_id)
    #         }


    def find_deals(self, natural_query: str, user_id: str) -> Dict:
        """Process natural language query and handle multiple products while maintaining API compatibility"""
        logger.info(f"Starting deal search for query: {natural_query}")
        
        try:
            # Parse the query for multiple products
            query_result = self._parse_natural_language_query(natural_query)
            logger.info(f"Parsed query result: {query_result}")
            
            # Initialize combined results
            combined_deals = {
                'ebay': [],
                'amazon': [],
                'walmart': []
            }
            
            all_product_results = []
            
            # Search for each product
            products = query_result.get('products', [])
            logger.info(f"Found {len(products)} products to search for")
            
            for product in products:
                logger.info(f"Processing product: {product}")
                
                # Construct search terms
                search_terms = " ".join(product['search_keywords'])
                logger.info(f"Search terms for product: {search_terms}")
                
                # Get deals for this specific product
                product_deals = self.provider.search_deals(
                    query=search_terms,
                    min_price=product['price_range'].get('min'),
                    max_price=product['price_range'].get('max'),
                    max_results=3
                )
                logger.info(f"Found deals for {product['product_type']}: {product_deals}")
                
                # Combine deals into the compatible structure
                for retailer in combined_deals.keys():
                    retailer_deals = product_deals.get(retailer, [])
                    logger.info(f"Adding {len(retailer_deals)} deals from {retailer}")
                    combined_deals[retailer].extend(retailer_deals)
                
                all_product_results.append({
                    'product_type': product['product_type'],
                    'deals': product_deals,
                    'attributes': product.get('key_attributes', []),
                    'context': product.get('shared_context', {})
                })
            
            # Generate comparison for all deals combined
            all_deals = []
            for retailer_deals in combined_deals.values():
                all_deals.extend(retailer_deals)
            
            logger.info(f"Total deals found across all products: {len(all_deals)}")
            
            comparison = self.generate_comparison(all_deals, user_id) if len(all_deals) > 1 else ""
            followup = self.generate_followup_questions(natural_query, all_deals, user_id)
            
            result = {
                "deals": combined_deals,
                "comparison": comparison,
                "followup_questions": followup,
                "user_preferences": self.get_user_preferences(user_id),
                "shared_context": query_result.get('shared_context', {}),
                "product_results": all_product_results
            }
            
            logger.info(f"Returning final result structure with {sum(len(deals) for deals in combined_deals.values())} total deals")
            return result
            
        except Exception as e:
            logger.error(f"Error in find_deals: {str(e)}")
            logger.error(f"Full error details: {traceback.format_exc()}")
            return {
                "deals": {
                    'ebay': [],
                    'amazon': [],
                    'walmart': []
                },
                "comparison": "",
                "followup_questions": "An error occurred while searching for deals.",
                "user_preferences": self.get_user_preferences(user_id),
                "shared_context": {},
                "product_results": []
            }