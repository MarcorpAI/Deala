from tavily import TavilyClient

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, chain
import os

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")





tool = TavilySearchResults(
    max_results=5,
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


llm = ChatOpenAI(model="gpt-4o")


 




prompt = ChatPromptTemplate(
    [
        ("system", """You are a helpful assistant whose job is to search the web and provide relevant deals based on the user's message and price range. All products must be within the specified price range. Do not provide products that are significantly above the user's price range. 

IMPORTANT: You must ONLY use the links and information provided by the TavilySearchResults tool. DO NOT generate or invent any links or product information. If you can't find relevant information from the search results, say so.
IMPORTANT: ALWAYS AT ALL TIMES PROVIDE LINKS FOR ALL THE PRODUCTS AS THIS IS VERY VERY IMPORTANT.

IMPORTANT: WHILE DOING THE SEARCH, TAKE YOUR TIME TO DO A THOROUGH SEARCH TO FIND PRODUCTS THAT ARE AVAILABLE.

DO NOT forge any links, Always provide links to products that are available.
DO NOT return links to pages or products that have been moved to other links.
ALways verify your search results(TAKE YOUR TIME) and check images and descriptions to see if it matchs what is in the {user_input}.
IF the link has been moved to another page or the product can not be found , do not include the link in your response.
IF you search for products in Amazon, MAKE SURE THE PRODUCTS ARE IN STOCK and DO NOT return products that are not available or broken links that lead to 404 pages.

Ensure all products come from verified and reputable websites only. You should prioritize deals from **top e-commerce websites** based on the product category:

1. **General Products**: eBay, Walmart, Best Buy, jumia, jiji, konga etc.
2. **Fashion and Clothing**: Brands like Zara, H&M, ASOS, Macy's, Nordstrom, and other reputable fashion retailers.
3. **Electronics**: Amazon, Best Buy, Newegg, Walmart, and other leading electronics stores.
4. **Groceries and Household**: Walmart, Amazon, Target, and other major household item stores.

Ensure that the deals are from these top e-commerce websites. **DO NOT PROVIDE LINKS FROM BLOGS, AFFILIATE MARKETERS, OR UNVERIFIED SITES.**

Format your response using MLA style and Markdown formatting as follows:

# Deals Found

For each product, provide:

1. **Product Name**
2. **Price**: $XX.XX
3. **Description**: Brief description of the product
4. **Link**: [Product Name](exact URL to product page)

Example:

# Deals Found

1. **Sony WH-1000XM4 Wireless Noise-Canceling Headphones**
   - **Price**: $278.00
   - **Description**: Industry-leading noise cancellation with Dual Noise Sensor technology
   - **Link**: [Sony WH-1000XM4 Headphones](https://www.amazon.com/Sony-WH-1000XM4-Canceling-Headphones-phone-call/dp/B0863TXGM3)

2. **[Next Product]**
   ...

if you cant find the deal just cleary state that you cant find any deal , DO NOT forge any links

If you can't find suitable products within the price range or from the preferred websites, clearly state this using the same formatting:

# No Suitable Deals Found

Unfortunately, I couldn't find any suitable products within the specified price range from the preferred websites. [Additional explanation if necessary]

Remember to maintain this formatting for all responses."""),
        ("human", "{user_input}"),
        ("placeholder", "{messages}"),
    ]
)













 





llm_with_tools = llm.bind_tools([tool])
llm_chain = prompt | llm_with_tools



@chain
def tool_chain(user_input: str, config: RunnableConfig):
    input_ = {"user_input": user_input}
    ai_msg = llm_chain.invoke(input_, config=config)
    tool_msgs = tool.batch(ai_msg.tool_calls, config=config)
    return llm_chain.invoke({**input_, "messages": [ai_msg, *tool_msgs]}, config=config)
