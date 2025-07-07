from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
import traceback
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth.models import User
from firebase_admin import auth as firebase_auth
from firebase_config import init_firebase
from django.http import JsonResponse, HttpResponseBadRequest
from firebase_admin import auth



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(APIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "tokens": tokens,
            "message":"User Created Successfully"
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            user = validated_data["user"]
            message = validated_data["message"]
            tokens = get_tokens_for_user(user)

            return Response({
                "message": message,
                "user": UserSerializer(user).data,
                "tokens": tokens
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("LOGIN ERROR:", e)
            traceback.print_exc() 
            return Response(
                {"detail": "Sorry, this account does not exist"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
def firebase_view(request):
    init_firebase()
    
    if request.method == "POST":
        import json
        body = json.loads(request.body)

        id_token = body.get("token")
        if not id_token:
            return HttpResponseBadRequest("Missing ID token")

        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '')
            picture = decoded_token.get('picture', '')

            return JsonResponse({
                "uid": uid,
                "email": email,
                "name": name,
                "picture": picture,
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return HttpResponseBadRequest("Only POST requests allowed")
    
    
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    
    def post(self, request):
        init_firebase() 
        token = request.data.get('token')
        
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            
            email = decoded_token.get('email')
            name = decoded_token.get('name')
            
            user, _ = User.objects.get_or_create(username=email, defaults={'email':email, 'first_name':name})
            refresh = RefreshToken.for_user(user)
            
            return Response ({
               'tokens': {
                    'refresh':str(refresh),
                    'access': str(refresh.access_token),
               },
                'user':{
                    'username':user.username,
                    'email':user.email
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print("❌ Google Login Error:", str(e))
            traceback.print_exc()
            return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)