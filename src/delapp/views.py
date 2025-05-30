from django.shortcuts import render
from .models import UserQuery, UserSubscription, CustomUser, UserDevice
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
## Rest Framework
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView
import hmac
from  .models import *
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
import hashlib
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import json
from django.http import StreamingHttpResponse
import requests

import re
import base64
from .utils import sanitize_input, validate_query
from django.core.cache import cache
import traceback
from django.views.decorators.http import require_POST
from langchain.schema import AIMessage
# from .llm_engine import tool_chain
from .lemon_squeezy import create_checkout, verify_webhook
import uuid
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils.decorators import method_decorator

from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer

from django.views import View
from langchain_core.runnables import RunnableConfig, chain
from .serializers import UserSerializer, QuerySerializer
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from .llm_engine import ConversationalDealFinder
from dotenv import load_dotenv
from django_ratelimit.decorators import ratelimit
from django.utils.timezone import now, timedelta
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import logging
from django.shortcuts import redirect
from .lemonsqueezy_utils import subscription_required
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from django.utils import timezone
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
import asyncio
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

from django.http import JsonResponse
from rest_framework.decorators import api_view
import asyncio

@api_view(['POST'])
def find_deals(request):
    """
    Wrapper to handle async find_deals in sync Django view
    """
    try:
        query = request.data.get('query', '')
        context = request.data.get('context', '')
        user_id = request.data.get('user_id', None)
        
        # Create event loop for async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize and call async function
        finder = ConversationalDealFinder()
        result = loop.run_until_complete(
            finder.find_deals(query, context, user_id)
        )
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)






load_dotenv()
logger = logging.getLogger(__name__)
logger.debug("This is a test log for debugging")





def generate_cache_key(user_id, query):
    # Truncate the query if it's too long
    truncated_query = query[:100]  # Adjust this number as needed
    
    # Create a string that combines user_id and the truncated query
    key_base = f"query_{user_id}_{truncated_query}"
    
    # Hash the key_base to ensure it's a valid cache key
    hashed_key = hashlib.md5(key_base.encode()).hexdigest()
    
    return f"query_hash:{hashed_key}"







deal_finder = ConversationalDealFinder()



@api_view(['POST'])
@permission_classes([AllowAny])
def product_description_view(request):
    """Generate AI descriptions for products"""
    try:
        product_data = request.data.get('product')
        query = request.data.get('query')
        
        if not product_data or not query:
            return Response({
                "error": "Both product data and query are required"
            }, status=status.HTTP_400_BAD_REQUEST)
            

        enhanced_description = deal_finder.generate_product_description(product_data, query)
        
        return Response({
            "description": enhanced_description
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating product description: {str(e)}")
        return Response({
            "error": "Failed to generate product description"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








 







 

 


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_query_api_view(request):
    logger.info(f"Received request data: {request.data}")
    
    serializer = QuerySerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        query_text = serializer.validated_data['query']
        user = request.user
        conversation_id = request.data.get('conversation_id')
        previous_deals = request.data.get('previous_deals', [])
        
        try:
            with transaction.atomic():
                # Get or create conversation
                if conversation_id:
                    conversation = Conversation.objects.get(id=conversation_id, user=user)
                else:
                    conversation = Conversation.objects.create(
                        user=user,
                        title=f"Search: {query_text[:50]}..."
                    )
                
                # Get or create conversation state for this conversation
                from .models import ConversationState
                try:
                    conv_state = ConversationState.objects.get(conversation=conversation)
                except ConversationState.DoesNotExist:
                    conv_state = ConversationState.objects.create(conversation=conversation)
                
                # Create event loop for async call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # AGENT-BASED IMPLEMENTATION - Use the new agent instead of ConversationalDealFinder
                from .agent.api import process_query
                
                # Run the agent-based search
                result = loop.run_until_complete(
                    process_query(
                        query=query_text,
                        conversation_id=str(conversation.id),
                        user_id=str(user.id)
                    )
                )
                
                # Map agent state to conversation state
                # The agent will handle most state internally through its memory components
                if 'agent_state' in result:
                    agent_state = result['agent_state']
                    conv_state.current_products = agent_state.get('current_products', [])
                    conv_state.last_query = agent_state.get('last_query', query_text)
                    conv_state.last_category = agent_state.get('last_category', '')
                    conv_state.applied_filters = agent_state.get('applied_filters', {})
                    conv_state.last_intent = agent_state.get('last_intent', None)
                    conv_state.conversation_turn = agent_state.get('conversation_turn', conv_state.conversation_turn + 1)
                    conv_state.product_references = agent_state.get('product_references', {})
                    conv_state.user_preferences = agent_state.get('user_preferences', {})
                    conv_state.keywords = agent_state.get('keywords', [])
                    conv_state.last_action = agent_state.get('last_action', None)
                else:
                    # If no agent state is returned, increment conversation turn at minimum
                    conv_state.conversation_turn += 1
                    conv_state.last_query = query_text
                    # Use products from agent response if available
                    if 'products' in result:
                        conv_state.current_products = result['products']
                
                conv_state.save()
                
                # Process the response from the agent
                structured_deals = result.get('products', [])
                is_mock_data = result.get('mock_data', False)
                
                # Add extra debug logging
                logger.info(f"Agent result: products={len(structured_deals)}, is_mock_data={is_mock_data}, result_keys={list(result.keys())}")
                
                # If we have no products but response text mentions products, try to extract them from elsewhere
                if not structured_deals and ('I found' in result.get('response', '') and 'product' in result.get('response', '')):
                    logger.warning(f"Response mentions products but no 'products' in result, trying to find mock data")
                    
                    # See if there's a raw_products field we can use
                    if 'raw_products' in result and isinstance(result['raw_products'], list) and result['raw_products']:
                        structured_deals = result['raw_products']
                        logger.info(f"Retrieved {len(structured_deals)} products from raw_products field")
                    
                if not structured_deals:
                    logger.warning(f"No products returned from agent for query: {query_text}")
                    return JsonResponse({
                        "message_id": 0,
                        "conversation_id": conversation.id,
                        "response": result.get('response', "I couldn't find any products matching your query. Try being more specific or changing your search terms."),
                        "deals": []
                    })
                
                # Format deals for frontend - this array will be used directly
                formatted_deals = []
                if 'products' in result:
                    logger.debug(f"Raw products received from agent: {len(result['products'])} items")
                    for product in result['products']:
                        try:
                            # Safely extract price - accept either string or direct numeric value
                            price = None
                            if isinstance(product.get('price'), (int, float)):
                                price = float(product.get('price'))
                            else:
                                price_str = str(product.get('price', '')).strip()
                                if price_str:
                                    try:
                                        price = float(re.sub(r'[^\d.]', '', price_str.split()[0]))
                                    except (ValueError, IndexError):
                                        logger.debug(f"Could not parse price: {price_str}")
                                        continue
                            
                            if price is None:
                                logger.debug(f"Skipping product with no price: {product.get('title')}")
                                continue
                                
                            # Handle original price
                            original_price = None
                            if isinstance(product.get('original_price'), (int, float)):
                                original_price = float(product.get('original_price'))
                            elif 'original_price' in product:
                                try:
                                    original_str = str(product['original_price']).strip()
                                    if original_str:
                                        original_price = float(re.sub(r'[^\d.]', '', original_str))
                                except (ValueError, AttributeError):
                                    pass
                            
                            # Format data specifically for the React frontend's expected structure
                            formatted_deal = {
                                'id': product.get('product_id', '') or product.get('id', ''),
                                'name': product.get('title', 'No title'),  # Frontend expects 'name'
                                'currentPrice': price,  # Frontend uses camelCase
                                'originalPrice': original_price,  # Frontend uses camelCase
                                'image_url': product.get('image_url', '') or product.get('thumbnail', ''),  # Try both field names
                                'productLink': product.get('url', '#'),  # Frontend expects 'productLink'
                                'retailer': product.get('retailer', 'Online retailer'),
                                'description': product.get('description', '')
                            }
                            
                            # Calculate savings if possible
                            if original_price and price and original_price > price:
                                formatted_deal['savings'] = {
                                    'amount': original_price - price,
                                    'percent': int((original_price - price) / original_price * 100)
                                }
                                
                            formatted_deals.append(formatted_deal)
                            logger.debug(f"Added formatted product: {formatted_deal['name']}")
                            
                        except Exception as e:
                            logger.error(f"Product formatting error: {str(e)}", exc_info=True)
                            continue
                
                # Save user message
                user_message = ConversationMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=query_text
                )
                
                # Create AI response message
                # The agent response is more structured, so prioritize getting the proper response text
                ai_response_text = result.get('response', result.get('message', 'Here are some options:'))
                
                # Save assistant message with search results
                assistant_message = ConversationMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=ai_response_text,
                    search_results=formatted_deals,  # Use the formatted deals for frontend
                    has_products=bool(formatted_deals)
                )
                
                # Get follow-up questions if available from the agent
                followup_questions = result.get('followup_questions', [])
                
                # Add debug log to see the final response structure
                logger.debug(f"Returning {len(formatted_deals)} formatted deals to frontend")
                for deal in formatted_deals[:2]:  # Log first two deals for debugging
                    logger.debug(f"  Deal: {deal['name']}, Price: {deal['currentPrice']}")
                
                # Add helpful follow-up question suggestions if we have products
                if formatted_deals and not followup_questions:
                    followup_questions = [
                        "Which of these products would you like to know more about?",
                        "Would you like to see similar products?",
                        "Would you like to filter these results by price?"
                    ]
                    
                # Add explicit logging to confirm what's being returned to frontend
                logger.info(f"API response: message_id={assistant_message.id}, conversation_id={conversation.id}, "
                           f"has_products={bool(formatted_deals)}, product_count={len(formatted_deals)}, "
                           f"first 50 chars of response: {ai_response_text[:50]}")
                
                # Add debug message to assist during development
                debug_msg = (
                    f"\n\nIMPORTANT: Debug Info - Products should display as cards.\n"
                    f"                Product count: {len(formatted_deals)}\n"
                    f"                First product: {formatted_deals[0]['name'] if formatted_deals else 'No products'}\n\n"
                    f"                If you don't see product cards above, please refresh the page."
                )
                
                # Log the actual structure of formatted_deals to debug the issue
                logger.info(f"FORMATTED DEALS STRUCTURE: {json.dumps([{k: type(v).__name__ for k, v in deal.items()} for deal in formatted_deals[:1]]) if formatted_deals else 'Empty array'}")
                
                # The response data to send to frontend
                response_data = {
                    "message_id": assistant_message.id,
                    "conversation_id": conversation.id,
                    "response": ai_response_text + "\n\n" + debug_msg,  # Always include debug info for now
                    "deals": formatted_deals,  # Return the properly formatted deals array
                    "followup_questions": followup_questions,  # Add follow-up questions if provided by agent
                    "debug_info": {
                        "has_products": bool(formatted_deals),
                        "product_count": len(formatted_deals),
                        "first_product": formatted_deals[0] if formatted_deals else None,
                        "source": "mock_data" if result.get('mock_data', False) else "api_data"
                    }
                }
                
                # Important: The frontend definitely needs these fields at the top level
                response_data["has_products"] = bool(formatted_deals)
                
                # Force log the full response for debugging
                logger.info(f"FINAL RESPONSE TO FRONTEND: message_id={response_data['message_id']}, "  
                           f"has_products={response_data['has_products']}, "
                           f"deals_count={len(response_data['deals'])}")
                
                return JsonResponse(response_data)
        
        except Exception as e:
            logger.exception(f"Error processing query: {str(e)}")
            return Response({
                "error": "An error occurred while processing your query.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    data = [{
        'id': conv.id,
        'title': conv.title,
        'created_at': conv.created_at,
        'updated_at': conv.updated_at
    } for conv in conversations]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        messages = conversation.messages.all().order_by('created_at')
        
        data = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'created_at': msg.created_at,
                'has_products': msg.has_products
            }
            if msg.has_products:
                message_data['products'] = msg.search_results
            data.append(message_data)
            
        return Response(data)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=404)










 


def parse_deals(ai_content):
    """
    Parse the AI response into a structured format for deals
    """
    try:
        if not ai_content or ai_content.lower().startswith("i'm sorry") or ai_content.lower().startswith("i am unable"):
            return [{
                "status": "no_deals_found",
                "message": "No current deals found. Try modifying your search terms or check back later.",
                "suggested_retailers": ["Amazon", "Best Buy", "Walmart", "Target"],
                "suggested_actions": [
                    "Set up price alerts",
                    "Check during major sale events",
                    "Consider similar products",
                    "Monitor deal websites"
                ]
            }]

        deals = []
        # Split content into individual deals using numbered headers
        deal_sections = ai_content.split('\n---\n')
        if len(deal_sections) == 1:
            deal_sections = ai_content.split('\n1. ')
            if len(deal_sections) > 1:
                deal_sections = ['1. ' + section for section in deal_sections[1:]]
            else:
                deal_sections = [ai_content]

        for section in deal_sections:
            if not section.strip():
                continue

            deal = {
                'name': None,
                'currentPrice': None,
                'originalPrice': None,
                'description': None,
                'productLink': None,
                'coupons': [],
                'cashback': [],
                'steps': [],
                'expiration': None,
                'savings': {
                    'amount': None,
                    'percentage': None
                }
            }

            # Extract product name
            name_match = section.split('**')
            if len(name_match) > 1:
                deal['name'] = name_match[1].strip()

            # Extract prices
            price_section = section.split('Base Price Details')[1].split('Additional Savings')[0] if 'Base Price Details' in section else ''
            if 'Current Price:' in price_section:
                current_price = price_section.split('Current Price:')[1].split('\n')[0].strip()
                deal['currentPrice'] = current_price.replace('$', '').replace(',', '').strip()
            if 'Original Price:' in price_section:
                original_price = price_section.split('Original Price:')[1].split('\n')[0].strip()
                deal['originalPrice'] = original_price.replace('$', '').replace(',', '').strip()

            # Extract coupons
            if 'Available Coupons:' in section:
                coupon_section = section.split('Available Coupons:')[1].split('Cashback Offers:')[0]
                coupon_lines = [line.strip() for line in coupon_section.split('\n') if 'Code:' in line]
                for line in coupon_lines:
                    if '-' in line:
                        code, description = line.split('-', 1)
                        code = code.replace('*', '').replace('Code:', '').strip()
                        deal['coupons'].append({
                            'code': code,
                            'description': description.strip()
                        })

            # Extract cashback offers
            if 'Cashback Offers:' in section:
                cashback_section = section.split('Cashback Offers:')[1].split('Maximum Potential Savings:')[0]
                cashback_lines = [line.strip() for line in cashback_section.split('\n') if '*' in line and ':' in line]
                for line in cashback_lines:
                    if 'No current cashback offers found' not in line:
                        platform, amount = line.replace('*', '').split(':', 1)
                        deal['cashback'].append({
                            'platform': platform.strip(),
                            'amount': amount.strip()
                        })

            # Extract product details
            if 'Product Details:' in section:
                details_section = section.split('Product Details:')[1].split('How to Get This Deal:')[0]
                for line in details_section.split('\n'):
                    line = line.strip()
                    if 'Description:' in line:
                        deal['description'] = line.split('Description:')[1].strip()
                    elif 'Product URL:' in line:
                        deal['productLink'] = line.split('Product URL:')[1].strip()
                    elif 'Expiration:' in line:
                        deal['expiration'] = line.split('Expiration:')[1].strip()

            # Extract steps
            if 'How to Get This Deal:' in section:
                steps_section = section.split('How to Get This Deal:')[1].split('\n')
                deal['steps'] = [step.strip().lstrip('123456789.') for step in steps_section if step.strip() and any(char.isdigit() for char in step)]

            # Calculate savings
            if deal['originalPrice'] and deal['currentPrice']:
                try:
                    original = float(deal['originalPrice'])
                    current = float(deal['currentPrice'])
                    if original > current:
                        savings_amount = original - current
                        savings_percentage = (savings_amount / original) * 100
                        deal['savings'] = {
                            'amount': f"{savings_amount:.2f}",
                            'percentage': f"{savings_percentage:.1f}"
                        }
                except ValueError:
                    pass

            # Only add deals that have at least a name and price
            if deal['name'] and (deal['currentPrice'] or deal['originalPrice']):
                deals.append(deal)

        return deals if deals else [{
            "status": "no_deals_found",
            "message": "No valid deals could be parsed from the response."
        }]

    except Exception as e:
        logger.exception(f"Error parsing deals: {str(e)}")
        return [{
            "status": "error",
            "message": "Error processing deal information",
            "error": str(e)
        }]

def extract_link(link_part):
    # If the link is in markdown format [text](url)
    if '[' in link_part and '](' in link_part:
        return link_part.split('](')[1].rstrip(')')
    # If the link is just a URL, possibly surrounded by brackets or parentheses
    else:
        return link_part.strip('[]() ')













 









# ##### AUTHENTICATION ########
# class CreateUserView(generics.CreateAPIView):
#     queryset = CustomUser.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [AllowAny]

#     def perform_create(self, serializer):
#         try:
#             # Save the user with inactive status
#             user = serializer.save(is_active=False)  # Inactive until email is verified
            
#             # Generate verification token and save it in the CustomUser model
#             token = get_random_string(length=32)
#             user.verification_token = token
#             user.save()

#             # Construct verification URL
#             full_url = f"{settings.FRONTEND_URL}/verify-email/{token}/"

#             # Render email template
#             html_message = render_to_string('delapp/email.html', {'verification_url': full_url})
#             plain_message = strip_tags(html_message)

#             # Send the verification email
#             send_mail(
#                 subject="Verify your email address",
#                 message=plain_message,
#                 html_message=html_message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[user.email],
#             )

#         except Exception as e:
#             logger.error(f"Error during user registration: {str(e)}")
#             raise



# class VerifyEmailView(View):
#     def get(self, request, token):
#         logger.info(f"Received GET request for token: {token}")
#         try:
#             user = CustomUser.objects.get(verification_token=token)
#             logger.info(f"Found user: {user.email}, is_active: {user.is_active}, email_verified: {user.email_verified}")

#             if not user.email_verified:
#                 user.is_active = True
#                 user.email_verified = True
#                 user.verification_token = None
#                 user.save()
#                 logger.info(f"User {user.email} verified successfully. New status - is_active: {user.is_active}, email_verified: {user.email_verified}")
#                 return JsonResponse({"message": "Email verified successfully!"})
#             else:
#                 logger.info(f"User {user.email} was already verified")
#                 return JsonResponse({"message": "Email was already verified"})

#         except CustomUser.DoesNotExist:
#             logger.warning(f"Invalid token received: {token}")
#             return JsonResponse({"error": "Invalid token"}, status=400)
#         except Exception as e:
#             logger.error(f"Unexpected error during email verification: {str(e)}", exc_info=True)
#             return JsonResponse({"error": "An unexpected error occurred"}, status=500)







class CreateUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        try:
#             # Check if email already exists
            email = serializer.validated_data.get('email')
            if CustomUser.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    "email": "A user with this email already exists."
                })
            
            # Save user with inactive status
            user = serializer.save(
                is_active=False,
                email_verified=False,
                verification_token=get_random_string(64),  # Longer token for security
                verification_token_created=timezone.now()  # Track token creation time
            )
            
            # Construct verification URL
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.verification_token}/"
            
            # Prepare email content
            context = {
                'verification_url': verification_url,
                'user_email': user.email,
                'expiry_hours': 24  # Token validity period
            }
            
            html_message = render_to_string('delapp/email.html', context)
            plain_message = strip_tags(html_message)
            
            # Send verification email
            email_sent = send_mail(
                subject="Verify your email address",
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
            
            if not email_sent:
                logger.error(f"Failed to send verification email to {user.email}")
                user.delete()  # Rollback user creation if email fails
                raise serializers.ValidationError({
                    "email": "Failed to send verification email. Please try again."
                })
                
            logger.info(f"User created successfully: {user.email}")
            
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}", exc_info=True)
            raise serializers.ValidationError({
                "error": "Registration failed. Please try again later."
            })




class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    device_id = serializers.CharField(required=False)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        device_id = attrs.get("device_id")

        user = CustomUser.objects.filter(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("This account is inactive.")
            # Generate token pair for user
            refresh = RefreshToken.for_user(user)

            # Optional: Store device-specific information if using device tracking
            if device_id:
                UserDevice.objects.update_or_create(
                    user=user,
                    device_id=device_id,
                    defaults={"refresh_token": str(refresh)}
                )

            return {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        else:
            raise serializers.ValidationError("Invalid credentials.")

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Log the login attempt
        logger.info(f"Login attempt from IP: {request.META.get('REMOTE_ADDR')} for device: {request.data.get('device_id')}")
        return super().post(request, *args, **kwargs)

















class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        logger.info(f"Processing email verification for token: {token}")
        
        try:
            # Get user and validate token
            user = CustomUser.objects.get(
                verification_token=token,
                is_active=False,
                email_verified=False
            )
            
            # Check token expiration (24 hours)
            token_age = timezone.now() - user.verification_token_created
            if token_age > timedelta(hours=24):
                logger.warning(f"Expired verification token for user {user.email}")
                
                # Generate new token and send new email
                user.verification_token = get_random_string(64)
                user.verification_token_created = timezone.now()
                user.save()
                
                # Send new verification email...
                return Response({
                    "error": "Verification link expired. A new link has been sent to your email.",
                    "expired": True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Activate user
            user.is_active = True
            user.email_verified = True
            user.verification_token = None
            user.verification_token_created = None
            user.save()
            
            logger.info(f"User {user.email} verified successfully")
            
            return Response({
                "message": "Email verified successfully!",
                "verified": True
            }, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            logger.warning(f"Invalid verification token: {token}")
            return Response({
                "error": "Invalid verification link.",
                "invalid": True
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Verification error: {str(e)}", exc_info=True)
            return Response({
                "error": "Verification failed. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)












 



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_view(request):
    variant_id = request.data.get('variant_id')
    user_email = request.user.email
    customer_id = getattr(request.user, 'lemonsqueezy_customer_id', None)
    try:
        checkout_data = create_checkout(variant_id, user_email, customer_id)
        checkout_url = checkout_data['data']['attributes']['url']
        return JsonResponse({'checkout_url': checkout_url})
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        print(f"General Exception: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)






 


@csrf_exempt
def lemon_squeezy_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            logger.info(f"Received webhook payload: {payload}")
            event_type = payload.get('event_type')
            logger.info(f"Received webhook event: {event_type}")

            lemonsqueezy_subscription_id = payload.get('data', {}).get('id')
            user_email = payload.get('data', {}).get('attributes', {}).get('user_email')
            variant_id = payload.get('data', {}).get('attributes', {}).get('variant_id')

            logger.info(f"Lemon Squeezy Subscription ID: {lemonsqueezy_subscription_id}")
            logger.info(f"User Email: {user_email}")
            logger.info(f"Variant ID: {variant_id}")
            return process_webhook_data(payload)
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received.")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

def process_webhook_data(payload):
    try:

        logger.info(f"Received webhook payload: {payload}")
        event_type = payload.get('meta', {}).get('event_name')
        logger.info(f"Webhook event type: {event_type}")

        if event_type == 'subscription_created':
            handle_subscription_created(payload)
        
        elif event_type == 'subscription_updated':
            handle_subscription_updated(payload)
        
        elif event_type == 'subscription_cancelled':
            handle_subscription_cancelled(payload)
        
        else:
            logger.warning(f"Unhandled event type: {event_type}")

        return JsonResponse({'status': 'success'}, status=200)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JsonResponse({'error': 'Processing error'}, status=500)

 



def handle_subscription_created(payload):
    try:

        logger.info(f"Received subscription_created webhook with payload: {payload}")
        # Correctly extract the subscription details
        subscription_data = payload.get('data', {}).get('attributes', {})
        user_email = subscription_data.get('user_email')
        lemonsqueezy_subscription_id = subscription_data.get('id')
        subscription_start_date = subscription_data.get('created_at')
        subscription_end_date = subscription_data.get('ends_at')
        variant_id = subscription_data.get('variant_id') 


        subscription_status = subscription_data.get('status')
        is_active = subscription_status == 'active'

        # Fetch the user associated with the subscription
        user = CustomUser.objects.get(email=user_email)

        # Update or create the subscription for this user
        subscription, created = UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'lemonsqueezy_subscription_id': lemonsqueezy_subscription_id,
                'is_active': True,
                'subscription_start_date': subscription_start_date,
                'subscription_end_date': subscription_end_date,
                'variant_id': variant_id
            }
        )
        user.is_active = True
        user.email_verified = True
        user.save()

        if created:
            logger.info(f"New subscription created for user {user_email}")
        else:
            logger.info(f"Subscription updated for user {user_email}")

    except CustomUser.DoesNotExist:
        logger.error(f"User with email {user_email} does not exist.")
    except Exception as e:
        logger.error(f"Error handling subscription created: {e}")







def handle_subscription_updated(payload):
    try:
        subscription_data = payload.get('data', {}).get('object', {})
        lemonsqueezy_subscription_id = subscription_data.get('id')
        subscription_end_date = subscription_data.get('ends_at')

        # Update the subscription in the database
        subscription = UserSubscription.objects.get(
            lemonsqueezy_subscription_id=lemonsqueezy_subscription_id
        )
        subscription.is_active = subscription_data.get('status') == 'active'
        subscription.subscription_end_date = subscription_end_date
        subscription.save()

        logger.info(f"Subscription {lemonsqueezy_subscription_id} updated.")

    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription {lemonsqueezy_subscription_id} not found.")
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")

def handle_subscription_cancelled(payload):
    logger.info("Handling subscription cancelled")
    subscription_id = payload['data']['id']
    try:
        subscription = UserSubscription.objects.get(lemonsqueezy_subscription_id=subscription_id)
        subscription.is_active = False
        subscription.save()
        logger.info(f"Subscription cancelled: {subscription_id}")
    except UserSubscription.DoesNotExist:
        logger.error(f"Subscription not found: {subscription_id}")

def handle_order_created(payload):
    logger.info("Handling order created")
    user_email = payload['data']['attributes']['user_email']
    order_id = payload['data']['id']
    try:
        user = CustomUser.objects.get(email=user_email)
        # Log or handle order details here
        logger.info(f"Order created for user: {user_email}")
    except CustomUser.DoesNotExist:
        logger.error(f"User not found: {user_email}")













# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def check_subscription(request):
#     try:
#         logger.info(f"Checking subscription for user: {request.user.email}")
        
#         subscription = UserSubscription.objects.filter(
#             user=request.user,
#             is_active=True
#         ).first()
        
#         if subscription:
#             # Check if subscription has expired
#             from django.utils import timezone
#             is_expired = (
#                 subscription.subscription_end_date and 
#                 subscription.subscription_end_date < timezone.now()
#             )
            
#             if is_expired:
#                 logger.info(f"Subscription expired for user {request.user.email}")
#                 subscription.is_active = False
#                 subscription.save()
#                 return JsonResponse({
#                     'is_subscribed': False,
#                     'error': 'Subscription expired'
#                 })
                
#             logger.info(f"Found active subscription for user {request.user.email}")
#             return JsonResponse({
#                 'is_subscribed': True,
#                 'subscription_id': subscription.lemonsqueezy_subscription_id,
#                 'start_date': subscription.subscription_start_date,
#                 'end_date': subscription.subscription_end_date,
#             })
#         else:
#             logger.info(f"No active subscription found for user {request.user.email}")
#             return JsonResponse({
#                 'is_subscribed': False,
#                 'error': 'No active subscription found'
#             })
            
#     except Exception as e:
#         logger.error(f"Error checking subscription for user {request.user.email}: {str(e)}")
#         return JsonResponse({
#             'is_subscribed': False,
#             'error': 'Error checking subscription status'
#         })




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        return JsonResponse({
            'is_subscribed': subscription.is_active,
            'subscription_id': subscription.lemonsqueezy_subscription_id,
            'start_date': subscription.subscription_start_date,
            'end_date': subscription.subscription_end_date,
        })
    except UserSubscription.DoesNotExist:
        return JsonResponse({'is_subscribed': False, 'error': 'No subscription found'})
















 