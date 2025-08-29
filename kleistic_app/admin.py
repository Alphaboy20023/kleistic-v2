from django.contrib import admin
from .models import Product, Order, ItemOrder

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'image')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'payment_method', 'grand_total', 'shipping_address')
    
class ItemOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'item_total')
    
admin.site.register(Product, ProductAdmin)  
admin.site.register(Order, OrderAdmin)  
admin.site.register(ItemOrder, ItemOrderAdmin)  