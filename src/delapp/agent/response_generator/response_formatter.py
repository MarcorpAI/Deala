"""
Response Formatter for ShopAgent

This module handles formatting responses from the agent into natural language
that is appropriate for the user's query and context.
"""
from typing import Dict, Any, Optional, List, Union
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Formats agent responses into natural language"""
    
    def __init__(self):
        """Initialize the response formatter with an LLM for enhanced formatting"""
        self.llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0.4)
        self.product_response_prompt = ChatPromptTemplate.from_template("""
        You are a helpful shopping assistant. Format the following product search results into a 
        natural, conversational response that answers the user's query.

        User query: {query}

        Products found:
        {products}

        Guidelines:
        1. Be concise but informative
        2. Highlight key features, prices, and retailers
        3. Don't mention the exact number of products unless relevant
        4. Keep your tone friendly and conversational
        5. Don't say "here are the results" or similar phrases
        6. If there are no products, suggest alternatives or ask for clarification

        Your response:
        """)
        
        self.comparison_response_prompt = ChatPromptTemplate.from_template("""
        You are a helpful shopping assistant. Format the following product comparison into a 
        natural, conversational response.

        User query: {query}

        Comparison results:
        {comparison}

        Guidelines:
        1. Focus on the key differences between products
        2. Highlight price-to-value considerations
        3. Be balanced and objective in your assessment
        4. Make a recommendation if appropriate
        5. Keep your tone friendly and conversational

        Your response:
        """)
        
        self.cart_response_prompt = ChatPromptTemplate.from_template("""
        You are a helpful shopping assistant. Format the following cart operation result into a 
        natural, conversational response.

        User query: {query}

        Cart operation: {operation}
        Result: {result}
        
        Guidelines:
        1. Be concise but clear about what happened
        2. Confirm what action was taken
        3. Mention the total number of items in the cart now
        4. For view operations, briefly summarize the cart contents
        5. Keep your tone friendly and conversational

        Your response:
        """)
    
    async def format_product_search_response(self, query: str, products: List[Dict[str, Any]]) -> str:
        """
        Format a product search response.
        
        Args:
            query: The user's query
            products: List of products to format
            
        Returns:
            Formatted response string
        """
        try:
            # Handle empty results
            if not products:
                return self._get_empty_results_response(query)
            
            # Format product information
            product_summaries = [
                f"- {p.get('title', 'Product')} (${float(p.get('price', 0)):.2f} from {p.get('retailer', 'Unknown')})"
                for p in products[:5]  # Limit to top 5 products for readability
            ]
            products_text = "\n".join(product_summaries)
            
            # Use LLM to generate natural response
            response = await self.llm.ainvoke(
                self.product_response_prompt.format(
                    query=query,
                    products=products_text
                )
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error formatting product search response: {str(e)}", exc_info=True)
            return f"I found {len(products)} products matching your search for '{query}'."
    
    async def format_comparison_response(self, query: str, comparison_data: Dict[str, Any]) -> str:
        """
        Format a product comparison response.
        
        Args:
            query: The user's query
            comparison_data: Comparison data
            
        Returns:
            Formatted response string
        """
        try:
            comparison_text = f"Comparison: {comparison_data.get('comparison', '')}\n\n"
            
            if 'key_differences' in comparison_data:
                differences = comparison_data['key_differences']
                if differences:
                    comparison_text += "Key differences:\n"
                    comparison_text += "\n".join([f"- {diff}" for diff in differences])
                    comparison_text += "\n\n"
            
            if 'recommendation' in comparison_data:
                comparison_text += f"Recommendation: {comparison_data['recommendation']}"
            
            # Use LLM to generate natural response
            response = await self.llm.ainvoke(
                self.comparison_response_prompt.format(
                    query=query,
                    comparison=comparison_text
                )
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error formatting comparison response: {str(e)}", exc_info=True)
            return comparison_data.get('comparison', "I've compared these products for you.")
    
    async def format_cart_response(self, query: str, operation: str, result: Dict[str, Any]) -> str:
        """
        Format a cart operation response.
        
        Args:
            query: The user's query
            operation: The cart operation performed
            result: The operation result
            
        Returns:
            Formatted response string
        """
        try:
            # Create a summary of the result
            result_summary = ""
            if 'message' in result:
                result_summary += result['message'] + "\n"
            
            if 'cart_count' in result:
                result_summary += f"Cart has {result['cart_count']} items total.\n"
            
            if operation == 'view' and 'cart_items' in result and result['cart_items']:
                items = result['cart_items'][:3]  # Limit to first 3 for summary
                result_summary += "Items in cart:\n"
                for item in items:
                    result_summary += f"- {item.get('title', 'Product')} (${float(item.get('price', 0)):.2f})\n"
                
                if len(result['cart_items']) > 3:
                    result_summary += f"...and {len(result['cart_items']) - 3} more items\n"
            
            # Use LLM to generate natural response
            response = await self.llm.ainvoke(
                self.cart_response_prompt.format(
                    query=query,
                    operation=operation,
                    result=result_summary
                )
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error formatting cart response: {str(e)}", exc_info=True)
            return result.get('message', f"I've processed your cart {operation} request.")
    
    def _get_empty_results_response(self, query: str) -> str:
        """Generate a response for when no products are found"""
        suggestions = [
            f"I couldn't find any products matching '{query}'. Could you try different search terms?",
            f"I searched for '{query}', but didn't find any matching products. Would you like to try a more general search?",
            f"No products found for '{query}'. Maybe try using different keywords or broaden your search?"
        ]
        
        import random
        return random.choice(suggestions)
    
    def generate_followup_questions(self, query: str, products: List[Dict[str, Any]]) -> List[str]:
        """
        Generate follow-up questions based on search results.
        
        Args:
            query: The user's query
            products: List of found products
            
        Returns:
            List of follow-up question strings
        """
        if not products:
            return [
                "Would you like to try a different search?",
                "Can you tell me more about what you're looking for?",
                "Would you prefer to browse by category instead?"
            ]
        
        # Product-specific follow-ups
        followups = []
        
        # Price-related
        prices = [float(p.get('price', 0)) for p in products if p.get('price')]
        if prices:
            price_range = max(prices) - min(prices)
            if price_range > 50:
                followups.append("Would you like to see more budget-friendly options?")
                followups.append("Are you looking for something in a specific price range?")
        
        # Feature-related
        if len(products) >= 2:
            followups.append("Would you like me to compare these products for you?")
        
        # Cart-related
        followups.append("Would you like to add any of these to your cart?")
        
        # Generic follow-ups
        generic_followups = [
            "Do you want more details about any of these products?",
            "Is there a specific feature you're most interested in?",
            "Would you like to see more options like these?"
        ]
        
        # Combine and limit
        followups.extend(generic_followups)
        
        import random
        return random.sample(followups, min(3, len(followups)))
