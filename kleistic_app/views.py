from datetime import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
import traceback
from firebase_admin import auth as firebase_auth
from firebase_config import init_firebase
from django.http import  HttpResponseBadRequest
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import *
import requests
from django.conf import settings



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
        
class ProductView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get(self, request):
        products = Product.objects.all()
        serializer = self.serializer_class(products, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(product, many=True, context={'request': request})
        return Response(serializer.data)
    
class OrderView(APIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        if pk:
            # get order by id
            try:
                order = Order.objects.get(id=pk, customer=request.user)
                serializer = self.serializer_class(order, context={'request': request}, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({"error":"Order not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # just get all orders
            orders = Order.objects.filter(customer=request.user)
            serializer = self.serializer_class(orders, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
    def post(self, request):
        # create a new order
        serializer = self.serializer_class(data=request.data, context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Update order status (e.g. cancel order)"""
        try:
            order = Order.objects.get(id=pk, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        # Example: Only allow cancel if still pending
        if request.data.get("status") == "cancelled":
            if order.status != "pending":
                return Response({"error": "Only pending orders can be cancelled"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(order, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, customer=request.user)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        
        active_orders = Order.objects.filter(customer=request.user).exclude(status="CANCELLED")
        serializer = OrderSerializer(active_orders, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ItemOrderView(APIView):
    serializer_class = ItemOrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = ItemOrder.objects.all()

    def post(self, request):
        customer = request.user

        # ✅ Get or create pending order
        order, created = Order.objects.get_or_create(
            customer=customer,
            status="PENDING",
        )

        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response({"error": "Product is required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if product already exists in order
        existing_item = ItemOrder.objects.filter(order=order, product_id=product_id).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            item_order = existing_item
        else:
            serializer = self.serializer_class(data=request.data, context={"request": request})
            if serializer.is_valid():
                item_order = serializer.save(order=order)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Recalculate order total
        order.total = sum(io.quantity * io.product.price for io in order.items.all())
        order.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            item_order = ItemOrder.objects.get(pk=pk, order__customer=request.user)
        except ItemOrder.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        order = item_order.order
        item_order.delete()

        # ✅ Recalculate total after deletion
        order.total = sum(io.quantity * io.product.price for io in order.items.all())
        order.save()

        # ✅ Exclude cancelled/removed items automatically
        active_items = order.items.all()
        serializer = ItemOrderSerializer(active_items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
class InitializePaymentView(APIView):
    serializer_class  = PaymentSerializer
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, customer=request.user, status="PENDING")
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        
        amount_naira = order.total
        amount_kobo = int(amount_naira) * 100
        
        data = {
            "email": request.user.email,
            "amount": amount_kobo,  
            "reference": f"ORD_{order.id}_{timezone.now().timestamp()}",
        }

        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
        res_data = response.json()

        if res_data.get("status") is True:
            # Save reference
            Payment.objects.create(
                order=order,
                user=request.user,
                amount=amount_naira,
                reference=data["reference"]
            )
            return Response(res_data["data"], status=status.HTTP_200_OK)

        return Response(res_data, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyPaymentView(APIView):
    def get(self, request, reference):
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        res_data = response.json()
        
        try:
            payment = Payment.objects.get(reference=reference, user=request.user)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if res_data["status"] and res_data["data"]["status"] == "success":
            payment.status = "SUCCESS"
            payment.save()

            order = payment.order
            order.status = "PAID"
            order.save()
            
        payment.status = "FAILED"
        payment.save()
        return Response({"message": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
    
class GenerateReceiptView(APIView):
    serializer_class = ReceiptSerializer
    
    def get(self, request, reference):
        try:
            payment = Payment.objects.get(reference=reference, user=request.user)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            receipt = Receipt.objects.get(payment_reference=payment, user=request.user)
        except Receipt.DoesNotExist:
            return Response({"error":"Receipt not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # validate payment
        if payment.status == "SUCCESS": 
            if receipt.status != "PAID":
                receipt.status = "PAID"
                receipt.save()
                
                serializer = self.serializer_class(receipt)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response( {"message": f"Receipt cannot be issued. Current payment status: {payment.status}"},status=status.HTTP_400_BAD_REQUEST)
            