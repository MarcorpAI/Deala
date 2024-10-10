from django.shortcuts import render
from .models import UserQuery, UserSubscription, CustomUser
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
## Rest Framework
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework import generics
import hmac
import hashlib
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import json
import requests
from allauth.account.models import EmailAddress
import traceback
from django.views.decorators.http import require_POST
from langchain.schema import AIMessage
from .llm_engine import tool_chain
from langchain_openai import ChatOpenAI
from .lemon_squeezy import create_checkout, verify_webhook
import uuid
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils.decorators import method_decorator

from django.views import View
from langchain_core.runnables import RunnableConfig, chain
from .serializers import UserSerializer, QuerySerializer
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from .llm_engine import tool_chain
from dotenv import load_dotenv
from django_ratelimit.decorators import ratelimit
from django.utils.timezone import now, timedelta
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import logging
from django.shortcuts import redirect
from .lemonsqueezy_utils import subscription_required





load_dotenv()
logger = logging.getLogger(__name__)
logger.debug("This is a test log for debugging")












# @subscription_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_query_api_view(request):
    logger.info(f"Received request data: {request.data}")
    
    # Create a mutable copy of request.data and add the user
    serializer = QuerySerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        query_text = serializer.validated_data['query']
        
        if not query_text.strip():
            return Response({"error": "Query cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = RunnableConfig()
            ai_response = tool_chain.invoke(query_text, config=config)
            
            logger.debug(f"AI Response: {ai_response}")
            print("AI Response:", ai_response)  
            
            if isinstance(ai_response, AIMessage):
                ai_content = ai_response.content
                deals = parse_deals(ai_content)
                
                # Save the query with the associated user
                user_query = serializer.save()
                
                return Response({
                    "query": query_text,
                    "ai_response": ai_content,
                    "deals": deals
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Unexpected AI response format: {type(ai_response)}")
                return Response({"error": "Unexpected response format from AI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Error processing query: {str(e)}")
            return Response({"error": "An error occurred while processing your query."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.warning(f"Invalid serializer data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










# this code gets each attribute of every deal like the name, description, and the product link
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


# this extracts the exact link to the url of each product and strips off every braces and special characters

def extract_link(link_part):
    # If the link is in markdown format [text](url)
    if '[' in link_part and '](' in link_part:
        return link_part.split('](')[1].rstrip(')')
    # If the link is just a URL, possibly surrounded by brackets or parentheses
    else:
        return link_part.strip('[]() ')






##### AUTHENTICATION ########

class CreateUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        try:
            user = serializer.save(is_active=False)  # Inactive until email is verified
            EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
            token = get_random_string(length=32)
            user.verification_token = token
            user.save()

            # Construct verification URL
            full_url = f"{settings.FRONTEND_URL}/verify-email/{token}/"

            html_message = render_to_string('delapp/email.html', {'verification_url': full_url})
            plain_message = strip_tags(html_message)

            # Send the verification email
            send_mail(
                subject="Verify your email address",
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            raise






class VerifyEmailView(View):
    def get(self, request, token):
        try:
            logger.info(f"Attempting to verify email with token: {token}")

            user = CustomUser.objects.get(verification_token=token)
            logger.info(f"User found: {user.email}")

            email_address = EmailAddress.objects.get(user=user, email=user.email)
            logger.info(f"Email address found: {email_address.email}")

            if not email_address.verified:
                email_address.verified = True
                email_address.save()
                logger.info(f"Email address {email_address.email} marked as verified")

                user.is_active = True
                user.email_verified = True  # Make sure this field exists in your CustomUser model
                user.verification_token = None
                user.save()
                logger.info(f"User {user.email} is now active and token cleared")

                return JsonResponse({"message": "Email verified successfully!"})
            else:
                logger.info(f"Email {email_address.email} was already verified")
                return JsonResponse({"message": "Email was already verified"})

        except CustomUser.DoesNotExist:
            logger.error(f"Invalid token: {token}, User does not exist")
            return JsonResponse({"error": "Invalid token"}, status=400)
        except EmailAddress.DoesNotExist:
            logger.error(f"Email address not found for user: {user.email}")
            return JsonResponse({"error": "Email address not found"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}")
            return JsonResponse({"error": "An unexpected error occurred"}, status=500)


# class VerifyEmailView(View):
#     def get(self, request, token):
#         user = get_object_or_404(CustomUser, verification_token=token)
#         if user.email_verified:
#             return JsonResponse({"message": "Email already verified!"}, status=400)

#         # Verify the email and set user to active
#         user.email_verified = True
#         user.is_active = True
#         user.verification_token = None  # Clear the token
#         user.save()

#         logger.info(f"Email verified for user: {user.email}")
#         return JsonResponse({"message": "Email verified successfully!"})






 

# class VerifyEmailView(View):
#     def get(self, request, token):
#         try:
#             logger.info(f"Attempting to verify email with token: {token}")
#             user = CustomUser.objects.get(verification_token=token, email_verified=False)
            
#             user.verify_email()
#             logger.info(f"Email verified successfully for user: {user.email}")
            
#             return JsonResponse({
#                 "message": "Email verified successfully. You can now log in.",
#                 "email": user.email
#             })
        
#         except ObjectDoesNotExist:
#             logger.warning(f"Invalid or already used token: {token}")
#             return JsonResponse({
#                 "error": "Invalid or expired verification link. Please request a new one."
#             }, status=400)
        
#         except Exception as e:
#             logger.error(f"Error during email verification: {str(e)}")
#             return JsonResponse({
#                 "error": "An unexpected error occurred. Please try again later."
#             }, status=500)

 















 



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

# def handle_subscription_created(payload):
#     try:



#         logger.info(f"Received subscription_created webhook with payload: {payload}")

#         # Adjust subscription_data extraction based on the actual structure of the payload
#         subscription_data = payload.get('data', {}).get('attributes', {})
#         subscription_data = payload.get('data', {}).get('object', {})



#         user_email = subscription_data.get('user_email')
#         lemonsqueezy_subscription_id = subscription_data.get('id')
#         lemonsqueezy_customer_id = subscription_data.get('customer_id')
#         subscription_start_date = subscription_data.get('created_at')
#         subscription_end_date = subscription_data.get('ends_at')

#         # Fetch the user associated with the subscription
#         user = CustomUser.objects.get(email=user_email)

#         user.lemonsqueezy_customer_id = lemonsqueezy_customer_id  # Save customer ID to user model
#         user.save()

#         # Update or create the subscription for this user
#         subscription, created = UserSubscription.objects.update_or_create(
#             user=user,
#             defaults={
#                 'lemonsqueezy_subscription_id': lemonsqueezy_subscription_id,
#                 'is_active': True,
#                 'subscription_start_date': subscription_start_date,
#                 'subscription_end_date': subscription_end_date
#             }
#         )

#         if created:
#             logger.info(f"New subscription created for user {user_email}")
#         else:
#             logger.info(f"Subscription updated for user {user_email}")

#     except CustomUser.DoesNotExist:
#         logger.error(f"User with email {user_email} does not exist.")
#     except Exception as e:
#         logger.error(f"Error handling subscription created: {e}")







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
