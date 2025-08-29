from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'is_admin', 'is_staff', 'is_superuser', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=data['username'], password=data['password'])
        
        if user and user.is_active:
            return {
                "user":user,
                "message":"login successful"
            }
        raise serializers.ValidationError("Invalid credentials")


class ProductSerializer(serializers.ModelSerializer):
    oldPrice = serializers.IntegerField(source="old_price")
    mainCategory = serializers.CharField(source="main_category")
    category = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['title', 'price', 'oldPrice', 'image', 'rating', 'reviews', 'category', 'mainCategory']
        
    def get_category(self, obj):
        return obj.get_category_display()

class ItemOrderSerializer(serializers.ModelSerializer):
    unit_price = serializers.IntegerField(read_only=True)  
    item_total = serializers.IntegerField(read_only=True)
    product = serializers.CharField(source="product.title")
    class Model:
        model = ItemOrder
        fields = ["order", "product", "quanity", "unit_price", "item_total", "created_at"]

class OrderSerializer(serializers.ModelSerializer):
    items = ItemOrderSerializer(many=True, read_only=True)
    customer = serializers.CharField(source="customer.username", read_only=True)
    grand_total = serializers.IntegerField(read_only=True)
    shipping_fee = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    class Meta:
        model = Order
        fields = ['id', "items", 'customer', 'shipping_address', "payment_method","shipping_fee", "grand_total", "status","created_at", "updated_at"]
        
