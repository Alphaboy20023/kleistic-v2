from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *
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
    mainCategory = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # removed image cos of testing, add back later
        fields = ['id','title', 'price', 'oldPrice', 'discount','rating', 'image','reviews', 'category', 'mainCategory']
        
    def get_category(self, obj):
        return obj.get_category_display()
    
    def get_mainCategory(self, obj):
        return obj.get_main_category_display()
    
    def get_image(self, obj):
        request = self.context.get("request")
        # print("request:", request)
        # print("obj.image:", obj.image)
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class ItemOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    quantity = serializers.IntegerField(default=1)
    unit_price = serializers.IntegerField(read_only=True)
    item_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = ItemOrder
        fields = ["product", "quantity", "unit_price", "item_total"]
        extra_kwargs = {
            "product": {"write_only": True},  # allow product ID input
        }


class OrderSerializer(serializers.ModelSerializer):
    items = ItemOrderSerializer(many=True)
    customer = serializers.CharField(source="customer.username", read_only=True)
    total = serializers.IntegerField(read_only=True)
    shippingFee = serializers.IntegerField(read_only=True, source="shipping_fee")
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "items", "customer", "shipping_address", "payment_method",
            "shippingFee", "total", "status", "created_at"
        ]
        
    def get_shippingFee(self, obj):
        """Compute shipping fee based on total dynamically."""
        if obj.total > 10000:
            return 500
        return 200   

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        user = self.context["request"].user

        # Create the order instance
        order = Order.objects.create(customer=user, **validated_data)

        # Create associated ItemOrders
        for item in items_data:
            product = item["product"]  # This is already a Product instance thanks to PKRelatedField
            quantity = item.get("quantity", 1)
            unit_price = product.price
            item_total = unit_price * quantity

            ItemOrder.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                item_total=item_total
            )

        # Recalculate total and shipping fee
        order.calculate_total()
        order.save()

        # Return the order instance
        return order    
        
class PaymentSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    order = OrderSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    
    
    class Meta:
        model = Payment
        fields = ['user', 'order', 'amount', 'reference', 'status', 'created_at', 'updated_at']
        
class ReceiptSerializer(serializers.ModelSerializer):
    payment_reference = serializers.CharField(source = 'payment.reference', read_only = True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True)
    
    class Meta:
        model = Receipt
        fields = ["user", "order", "payment_reference", "amount", "currency", "status", "issued_at"]