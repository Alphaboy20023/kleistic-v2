from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# Create your models here.
class UserManager(BaseUserManager):

    use_in_migration = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is Required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)


class UserTypes(models.TextChoices):
    STUDENT= 'Student', 'Student'
    LECTURER= 'Lecturer', 'Lecturer'

class CustomUser(AbstractUser):

    # username = None
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f'{self.username}'

class TimeStampField(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
class Product(TimeStampField):
    title = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    old_price = models.PositiveIntegerField(blank=True, null=True)
    image = models.ImageField(upload_to="")
    discount = models.IntegerField(default=0, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200, blank=True, null=True)
    # condition=models.CharField(max_length=50, choices=(
    #     ("IN_STOCK", "In Stock"),
    #     ("OUT_OF_STOCK", "Out Of Stock")
    # ))
    category = models.CharField(
        max_length=50,
        choices=(
            ("THIS_MONTH", "This Month"),
            ("OUR_PRODUCTS", "Our Products"),
            ("FLASH_SALES", "Flash Sales"),
        ),
        default="OUR_PRODUCTS",
    )
    main_category = models.CharField(max_length=200, choices=(
        ("WOMEN'S_FASHION","Women's Fashion" ),
        ("MEN'S_FASHION", "Men's Fashion"),
        ("ELECTRONICS", "Electronics"),
        ("GAMING", "Gaming"),
        ("BABY'S_AND_TOYS", "Baby's and Toys"), 
        ("GROCERIES_AND_PETS", "Groceries and pets"),
        ("HEALTH_AND_BEAUTY", "Health and beauty"),
        ("LIFESTYLE", "Lifestyle"), 
        ("SPORTS", "Sports")
    ))

    def __str__(self):
        return f'{self.title}'


# All orders
class Order(TimeStampField):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  
    shipping_address = models.TextField()
    payment_method = models.CharField(
        max_length=50,
        choices=(
            ("BANK", "Bank"),
            ("CASH_ON_DELIVERY", "Cash on Delivery"),
        ),
    )
    total = models.PositiveIntegerField(default=0)
    shipping_fee = models.PositiveIntegerField(default=20)
    status = models.CharField(
    max_length=20,
    choices=[
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("PROCESSING", "Processing"),
        ("FULFILLED", "Fulfilled"),
        ("CANCELLED", "Cancelled"),
        ("DELIVERED", "Delivered"),
        ("REFUNDED", "Refunded")
    ],
    default="PENDING")
    
    def set_shipping_fee(self, items_total):
        """Business rule for shipping fee."""
        if items_total > 10000:
            return 500  # discount
        return 200
    
    def calculate_total(self):
        items_total = sum(item.item_total for item in self.items.all())
        self.shipping_fee = self.set_shipping_fee(items_total)
        self.total = items_total + self.shipping_fee
        return self.total
    
    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        self.calculate_total()
        super().save(update_fields=["total", "shipping_fee"])
        
    def __str__(self):
        return f"Order #{self.id} - {self.customer}"

    
# order for a single item
class ItemOrder(TimeStampField):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveIntegerField()  # snapshot of product.price at time of order
    item_total = models.PositiveIntegerField(default=0)
    
        
    def calculate_item_total(self):
        if not self.unit_price:
            self.unit_price = self.product.price
            
        item_total = self.unit_price * self.quantity
        self.item_total = item_total
        return self.item_total
    
    def save(self, *args, **kwargs):
        self.calculate_item_total()  # recalc before saving
        super().save(*args, **kwargs)
        # after saving this item, trigger parent order to recalc
        self.order.save()

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"    
    
class Payment(TimeStampField):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="PENDING", choices=(("SUCCESS", "Success"), ("FAILED", "Failed"), ("PENDING", "Pending")))
    
    def __str__(self):
        return f"{self.user} - {self.order.id} - {self.status}"
    
class Receipt(TimeStampField):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="receipts")
    order = models.OneToOneField("Order", on_delete=models.CASCADE, related_name="receipt")
    payment = models.OneToOneField("Payment", on_delete=models.CASCADE, related_name="receipt")  # Paystack ref
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    status = models.CharField(max_length=20, default="pending", choices=(
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ))  
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt #{self.id} - {self.user.email} - {self.amount}{self.currency}"