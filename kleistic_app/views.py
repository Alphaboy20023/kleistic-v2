from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
import traceback
from firebase_admin import auth as firebase_auth
from firebase_config import init_firebase
from django.http import  HttpResponseBadRequest
from django.contrib.auth import get_user_model
User = get_user_model()




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
    
    
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    
    def post(self, request):
        
        init_firebase() 
        
        token = request.data.get('token')
        print('token', token[:40])
        
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