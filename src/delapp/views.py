from django.shortcuts import render
from .models import UserQuery, Waitlist
from .forms import EnterQueryForm, WaitlistForm
from langchain_community.tools import TavilySearchResults

from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from langchain_core.runnables import RunnableConfig, chain
from django.views.decorators.csrf import csrf_exempt

from langchain.schema import AIMessage
from .llm_engine import tool_chain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
# Create your views here
from django_ratelimit.decorators import ratelimit
from django.utils.timezone import now, timedelta
from django.views.decorators.csrf import ensure_csrf_cookie

import logging


load_dotenv()
logger = logging.getLogger(__name__)










@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})






@ratelimit(key='ip', rate='5/m', block=False)
@api_view(['POST'])
def user_query_api_view(request):

    if getattr(request, 'limited', False):
        # Calculate the retry time
        retry_after = (now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        return Response(
            {
                "error": "Rate limit exceeded. Please try again later.",
                "retry_after": retry_after  # Inform the user when they can retry
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )


    form = EnterQueryForm(request.data)
    logger.info(f"Received request data: {request.data}")

    if form.is_valid():
        user_query = form.save(commit=False)
        query_text = user_query.query
        if not query_text.strip():  # Check if query is empty after stripping whitespace
            return Response({"error": "Query cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            config = RunnableConfig()
            ai_response = tool_chain.invoke(query_text, config=config)

            print("AI Response:", ai_response)  # Debug print

            if isinstance(ai_response, AIMessage):
                ai_content = ai_response.content

                deals = parse_deals(ai_content)


                # Save the form to the database after processing
                user_query.save()

                # Return the response in JSON format
                return Response({
                    "query": query_text,
                    "ai_response": ai_content,
                    "deals": deals
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Unexpected response format from tool_chain."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)






# # this function stores the deals from the AI response in a list to ensure the response from the API in this format



# # {
# #   "query": "user's input",
# #   "ai_response": "LLM's response text",
# #   "deals": [
# #     {
# #       "name": "Product Name",
# #       "description": "Brief description of the product",
# #       "price": "$100",
# #       "link": "https://example.com/product-link"
# #     },
# #     // more deals...
# #   ]
# # }




def parse_deals(ai_content):
    # Initialize an empty list to hold the deals
    deals = []
    # Split the AI response into lines
    lines = ai_content.split('\n')
    # Initialize a dictionary to hold the current deal being processed
    current_deal = {}
    # Iterate over each line in the AI response
    for line in lines:
        # Check if the line starts with a number followed by a period, which indicates a new deal
        if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
            # If there is an existing deal being processed, add it to the list of deals
            if current_deal:
                deals.append(current_deal)
                current_deal = {}  # Reset the current deal dictionary for the next deal
            # Extract the product name, which is formatted in bold with double asterisks
            current_deal['name'] = line.split('**')[1]
        # If the line contains price information, add it to the current deal
        elif '**Price**' in line:
            current_deal['price'] = line.split('**Price**:')[1].strip()
        # If the line contains a description, add it to the current deal
        elif '**Description**' in line:
            current_deal['description'] = line.split('**Description**:')[1].strip()
        # If the line contains a link, add it to the current deal
        elif '**Link**' in line:
            link_part = line.split('**Link**:')[1].strip()
            current_deal['link'] = extract_link(link_part)
        elif '[Link to product]' in line:
            link_part = line.split('[Link to product]')[1].strip()
            current_deal['link'] = extract_link(link_part)
        elif '[Link]' in line:
            link_part = line.split('[Link]')[1].strip()
            current_deal['link'] = extract_link(link_part)
    # After processing all lines, add the last deal if it exists
    if current_deal:
        deals.append(current_deal)
    return deals




def extract_link(link_part):
    # If the link is in markdown format [text](url)
    if '[' in link_part and '](' in link_part:
        return link_part.split('](')[1].rstrip(')')
    # If the link is just a URL, possibly surrounded by brackets or parentheses
    else:
        return link_part.strip('[]() ')







#### STOP HERE #######

 

@api_view(['GET'])
def get_waitlist_url(request):
    waitlist_url = request.build_absolute_uri(reverse('waitlist_submit'))
    return Response({'url': waitlist_url})



 
@api_view(['POST'])
def waitlist_submit(request):
    form = WaitlistForm(request.data)
    if form.is_valid():
        form.save()
        return Response({"message": "Successfully joined the waitlist!"}, status=201)
    return Response(form.errors, status=400)

