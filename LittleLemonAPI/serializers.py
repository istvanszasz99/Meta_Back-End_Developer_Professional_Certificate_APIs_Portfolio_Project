from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MenuItem, Category, Cart, Order, OrderItem

# UserSerializer: Serializes the User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

# CategorySerializer: Serializes the Category model
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','slug', 'title']

# MenuItemSerializer: Serializes the MenuItem model, including a nested CategorySerializer
class MenuItemSerializer(serializers.ModelSerializer):
    category=CategorySerializer
    class Meta():
        model = MenuItem
        fields = ['id','title','price','featured','category']

# CartSerializer: Serializes the Cart model, including a nested MenuItemSerializer
class CartSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer
    user = User
    class Meta():
        model = Cart
        fields = ['id','user','menuitem','quantity','unit_price','price']

# OrderItemSerializer: Serializes the OrderItem model, including a nested MenuItemSerializer
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())

    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']

# OrderSerializer: Serializes the Order model, including nested OrderItemSerializer for order items
class OrderSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    delivery_crew = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']

    def get_order_items(self, obj):
        order_items = OrderItem.objects.filter(order=obj)
        return OrderItemSerializer(order_items, many=True).data