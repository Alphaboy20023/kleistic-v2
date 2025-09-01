from django.contrib import admin
from .models import Product, Order, ItemOrder, Payment, Receipt

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'old_price', 'price', 'category')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'payment_method', 'shipping_fee', 'total', 'shipping_address')
    
class ItemOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'item_total')
    
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'payment', 'amount', 'currency', 'status')
    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'amount', 'reference', 'status')
    
admin.site.register(Product, ProductAdmin)  
admin.site.register(Order, OrderAdmin)  
admin.site.register(ItemOrder, ItemOrderAdmin)  
admin.site.register(Payment, PaymentAdmin)  
admin.site.register(Receipt, ReceiptAdmin)  