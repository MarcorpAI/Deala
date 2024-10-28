from tavily import TavilyClient

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableConfig, chain
import os
from  langchain_core.runnables.config import run_in_executor
from langchain_community.utilities.dataforseo_api_search import DataForSeoAPIWrapper
from langchain.chains import LLMChain
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")



 












tavily_search = TavilySearchResults(
    max_results=10,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
    # include_domains=[
    #     "ebay.com", "walmart.com", "bestbuy.com", "newegg.com", "asos.com", "macys.com", "hm.com", "nordstrom.com", "amazon.com"
    # ]
    # exclude_domains=[...],
    # name="...",            # overwrite default tool name
    # description="...",     # overwrite default tool description
    # args_schema=...,       # overwrite default args_schema: BaseModel
)
















# def create_search_queries(base_query):
#     """Create specialized search queries for different types of searches"""
#     return {
#         "regular": base_query,
#         "coupons": f"{base_query} coupon code promo deals site:rakuten.com OR site:retailmenot.com OR site:groupon.com OR site:coupons.com",
#         "cashback": f"{base_query} cashback rewards site:rakuten.com OR site:topcashback.com OR site:ibotta.com OR site:mrrebates.com"
#     }



def create_search_queries(base_query):
    """Create more targeted search queries for different types of searches"""
    return {
        "regular": f"{base_query} best price deals discount sale",
        "coupons": f"{base_query} promo code coupon discount site:retailmenot.com OR site:rakuten.com OR site:slickdeals.net OR site:dealnews.com",
        "cashback": f"{base_query} cashback rewards site:rakuten.com OR site:topcashback.com OR site:retailmenot.com"
    }






def debug_print(message, data):
    """Helper function to print debug information"""
    print(f"\n=== {message} ===")
    print(json.dumps(data, indent=2, default=str))

def create_search_queries(base_query):
    """Create specialized search queries for different types of searches"""
    return {
        "regular": base_query,
        "coupons": f"{base_query} coupon code promo deals site:rakuten.com OR site:retailmenot.com OR site:groupon.com OR site:coupons.com",
        "cashback": f"{base_query} cashback rewards site:rakuten.com OR site:topcashback.com OR site:ibotta.com OR site:mrrebates.com"
    }

def perform_single_search(query, search_type="regular"):
    """Perform a single search and return raw results for debugging"""
    try:
        print(f"\nExecuting {search_type} search for: {query}")
        # Adjust max_results based on search type
        tavily_search.max_results = 10 if search_type == "regular" else 5
        results = tavily_search.invoke(query)
        debug_print(f"{search_type.upper()} SEARCH RESULTS", results)
        return results
    except Exception as e:
        print(f"Error in {search_type} search: {str(e)}")
        return []








def perform_searches(query_text):
    """Enhanced search function with better error handling and result formatting"""
    queries = create_search_queries(query_text)
    results = {}
    
    for search_type, search_query in queries.items():
        try:
            # Adjust max_results based on search type for better relevance
            tavily_search.max_results = 15 if search_type == "regular" else 8
            raw_results = tavily_search.invoke(search_query)
            
            # Enhanced result filtering and cleaning
            formatted_results = []
            seen_urls = set()  # To prevent duplicate results
            
            for result in raw_results:
                url = result.get('url', '').strip()
                if not url or url in seen_urls:
                    continue
                    
                # Ensure URL is properly formatted
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'
                    
                # Extract domain for filtering
                domain = url.split('/')[2] if len(url.split('/')) > 2 else ''
                
                # Skip results from unwanted domains
                if any(blocked in domain for blocked in ['facebook.com', 'twitter.com', 'instagram.com']):
                    continue
                
                # Clean and format the content
                content = result.get('content', '').strip()
                content = ' '.join(content.split())  # Normalize whitespace
                
                formatted_result = {
                    'title': result.get('title', '').strip(),
                    'link': url,
                    'snippet': content,
                    'type': search_type,
                    'source': domain,
                    'score': result.get('score', 0)
                }
                
                formatted_results.append(formatted_result)
                seen_urls.add(url)
            
            # Sort results by relevance score
            formatted_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            results[search_type] = formatted_results
            
        except Exception as e:
            logger.exception(f"Error in {search_type} search: {str(e)}")
            results[search_type] = []
    
    return results

# Initialize OpenAI ChatGPT
llm = ChatOpenAI(model="gpt-4o")

# # Updated prompt to ensure clean URL formatting
# prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an advanced shopping assistant whose job is to find the best possible savings by combining deals, coupons, and cashback offers. 

# IMPORTANT FORMATTING RULES:
# 1. NEVER use Markdown link formatting [text](url). Instead, always provide clean, direct URLs.
# 2. ALWAYS include full URLs starting with http:// or https://
# 3. Separate URLs from descriptions with a clear dash or colon.
# 4. Each link should be on its own line.

# Format your response as follows:

# # Best Savings Found

# For each product:

# 1. **Product Name**
# 2. **Base Price Details**:
#    - Current Price: $XX.XX
#    - Original Price: $XX.XX (if available)
#    - Direct Discount: XX% off

# 3. **Additional Savings**:
#    - Available Coupons:
#      * Code: COUPON_CODE - Description ($XX or XX% off)
#      * Restrictions (if any)
#    - Cashback Offers:
#      * Platform: XX% cashback
#      * Minimum purchase requirements (if any)

# 4. **Maximum Potential Savings**:
#    - Original Price: $XX.XX
#    - Final Price: $XX.XX
#    - Total Savings: $XX.XX (XX%)
   
# 5. **Product Details**:
#    - Description: Brief description
#    - Retailer: Store name
#    - Product URL: https://full-product-url.com
#    - Coupon URL: https://full-coupon-url.com
#    - Cashback URL: https://full-cashback-url.com
#    - Expiration: Date or "Limited Time"

# 6. **How to Get This Deal**:
#    1. Step-by-step instructions
#    2. Order of applying discounts
#    3. Special requirements

# Remember: Always use complete URLs starting with http:// or https:// and never use Markdown formatting for links."""),
#     ("human", "{query}"),
#     ("human", "Regular search results: {regular_results}"),
#     ("human", "Coupon search results: {coupon_results}"),
#     ("human", "Cashback search results: {cashback_results}")
# ])

# Create an LLMChain



SYSTEM_PROMPT = """You are an advanced shopping assistant whose job is to find the best possible savings by combining deals, coupons, and cashback offers. 

Follow these STRICT formatting rules:
1. Each deal MUST include ALL of the following sections in order:
   - Product Name (with model/variant if applicable)
   - Current Price (ALWAYS in $XX.XX format)
   - Original Price (if available, in $XX.XX format)
   - Direct Discount percentage
   - ALL available coupons with exact codes
   - ALL cashback offers with exact percentages/amounts
   - Final price after ALL discounts
   - Total savings in both dollars and percentage
   - Complete product description
   - Direct product URL (must start with http:// or https://)
   - Expiration date or "Limited Time"
   - Step-by-step instructions

2. Format REQUIREMENTS:
   - Use EXACT section headers as shown in the template
   - Include ALL price values with $ symbol
   - List ALL savings opportunities
   - Separate deals with "---"
   - NO markdown links
   - FULL URLs only

Here's the REQUIRED format:

1. **[Product Name]**
**Base Price Details**:
- Current Price: $XX.XX
- Original Price: $XX.XX
- Direct Discount: XX%

**Additional Savings**:
- Available Coupons:
  * Code: [EXACT_CODE] - [Amount/Percentage] off
  * Restrictions: [if any]
- Cashback Offers:
  * [Platform]: [Exact percentage/amount]

**Maximum Potential Savings**:
- Original Price: $XX.XX
- Final Price: $XX.XX
- Total Savings: $XX.XX (XX%)

**Product Details**:
- Description: [Clear, detailed description]
- Retailer: [Store name]
- Product URL: [Full URL]
- Expiration: [Date or "Limited Time"]

**How to Get This Deal**:
1. [Step-by-step instructions]
2. [Order of applying discounts]
3. [Special requirements]

Feel free to return Products from affiliate sites and multiple sites so i can compare prices and have more options.
you will get $100 tip if you can deliver this properly.

---"""



def get_deals(query_text):
    """Enhanced function to get and process deals"""
    try:
        # Get search results with improved error handling
        all_results = perform_searches(query_text)
        
        # Create prompt with improved structure
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Search Query: {query}"),
            ("human", "Regular results: {regular_results}"),
            ("human", "Coupon results: {coupon_results}"),
            ("human", "Cashback results: {cashback_results}")
        ])
        
        # Initialize LLM with temperature setting for more consistent outputs
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,  # Lower temperature for more consistent formatting
            max_tokens=4000
        )
        
        # Create chain with retry logic
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        
        # Generate response with improved error handling
        try:
            ai_response = llm_chain.run(
                query=query_text,
                regular_results=json.dumps(all_results["regular"][:5]),  # Limit to top 5 most relevant
                coupon_results=json.dumps(all_results["coupons"][:3]),
                cashback_results=json.dumps(all_results["cashback"][:3])
            )
            
            # Validate response format
            if not any(marker in ai_response for marker in ['**Base Price Details**', '**Additional Savings**']):
                raise ValueError("AI response does not match expected format")
                
            return ai_response
            
        except Exception as e:
            logger.exception(f"Error in LLM chain: {str(e)}")
            raise
            
    except Exception as e:
        raise Exception(f"Error processing query: {str(e)}")

















# def get_deals(query_text):
#     """Main function to get deals"""
#     try:
#         # Get search results
#         all_results = perform_searches(query_text)
        
#         # Generate response using LLMChain
#         ai_response = llm_chain.run(
#             query=query_text,
#             regular_results=all_results["regular"],
#             coupon_results=all_results["coupons"],
#             cashback_results=all_results["cashback"]
#         )
        
#         return ai_response
#     except Exception as e:
#         raise Exception(f"Error processing query: {str(e)}")








 





# tool = TavilySearchResults(
#     max_results=10,
#     search_depth="advanced",
#     include_answer=True,
#     include_raw_content=True,
#     include_images=True,
#     # include_domains=[
#     #     "ebay.com", "walmart.com", "bestbuy.com", "newegg.com", "asos.com", "macys.com", "hm.com", "nordstrom.com", "amazon.com"
#     # ]
#     # exclude_domains=[...],
#     # name="...",            # overwrite default tool name
#     # description="...",     # overwrite default tool description
#     # args_schema=...,       # overwrite default args_schema: BaseModel
# )


# llm = ChatOpenAI(model="gpt-4o")


 




 



# prompt = ChatPromptTemplate(
#     [
#         ("system", """You are a helpful assistant whose job is to search the web and provide relevant deals and discounts based on the user's message and price range. All products must be within the specified price range. Do not provide products that are significantly above the user's price range.

# IMPORTANT GUIDELINES:
# 1. ONLY use the links and information provided by the TavilySearchResults tool. DO NOT generate or invent any links or product information.
# 2. ALWAYS provide links for all products. This is critically important.
# 3. Conduct a thorough search to find available products. Take your time to verify search results.
# 4. DO NOT forge any links or return links to unavailable products or 404 pages.
# 5. Verify that images and descriptions match the user's request.
# 6. Ensure all products come from verified and reputable websites only.
# 7. Prioritize deals from top e-commerce websites based on the product category.
# 8. Look specifically for discounts on deals. Compare original prices to discounted prices when available.
# 9. Cross-reference prices across different retailers to ensure you're presenting the best deal.
# 10. If a product is on sale, clearly state the original price and the discount percentage.
# 11. If you can't find relevant information from the search results, say so.

# Preferred websites by category:
# 1. General Products: eBay, Walmart, Best Buy, Amazon, Target, Costco
# 2. Fashion and Clothing: Zara, H&M, ASOS, Macy's, Nordstrom
# 3. Electronics: Amazon, Best Buy, Newegg, Walmart
# 4. Home and Garden: Wayfair, Overstock, Home Depot
# 5. Groceries and Household: Walmart, Amazon, Target

# DO NOT PROVIDE LINKS FROM BLOGS, AFFILIATE MARKETERS, OR UNVERIFIED SITES.

# Format your response using MLA style and Markdown formatting as follows:

# # Deals Found

# For each product, provide:

# 1. **Product Name**
# 2. **Current Price**: $XX.XX
# 3. **Original Price** (if available): $XX.XX
# 4. **Discount**: XX% off (if applicable)
# 5. **Description**: Brief description of the product, including key features
# 6. **Retailer**: Name of the retailer
# 7. **Link**: [Product Name](exact URL to product page)
# 8. **Deal Expiration** (if available): Date or "Limited Time Offer"

# Example:

# # Deals Found

# 1. **Sony WH-1000XM4 Wireless Noise-Canceling Headphones**
#    - **Current Price**: $278.00
#    - **Original Price**: $349.99
#    - **Discount**: 21% off
#    - **Description**: Industry-leading noise cancellation with Dual Noise Sensor technology, up to 30-hour battery life
#    - **Retailer**: Amazon
#    - **Link**: [Sony WH-1000XM4 Headphones](https://www.amazon.com/Sony-WH-1000XM4-Canceling-Headphones-phone-call/dp/B0863TXGM3)
#    - **Deal Expiration**: Limited Time Offer

# 2. **[Next Product]**
#    ...

# If you can't find suitable products within the price range or from the preferred websites, clearly state this using the same formatting:

# # No Suitable Deals Found

# Unfortunately, I couldn't find any suitable products within the specified price range from the preferred websites. [Additional explanation if necessary]

# Remember to maintain this formatting for all responses."""),
#         ("human", "{user_input}"),
#         ("placeholder", "{messages}"),
#     ]
# )









 





# llm_with_tools = llm.bind_tools([tool])
# llm_chain = prompt | llm_with_tools



# @chain
# def tool_chain(user_input: str, config: RunnableConfig):
#     input_ = {"user_input": user_input}
#     ai_msg = llm_chain.invoke(input_, config=config)
#     tool_msgs = tool.batch(ai_msg.tool_calls, config=config)
#     return llm_chain.invoke({**input_, "messages": [ai_msg, *tool_msgs]}, config=config)
