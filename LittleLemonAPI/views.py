from rest_framework.response import Response
from rest_framework import status, generics
from .models import MenuItem, Category, Cart, Order, OrderItem
from django.contrib.auth.models import User, Group
from .serializers import UserSerializer, MenuItemSerializer, CategorySerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsManager, IsDeliveryCrew
from rest_framework.exceptions import NotFound
from .pagination import MenuItemsPagination, OrdersPagination

# CategoryView: Handles listing and creating categories
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]

# MenuItemsView: Handles listing and creating menu items
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    pagination_class = MenuItemsPagination
    search_fields = ['title', 'category__title']
    ordering_fields = ['price', 'inventory']

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'POST':
                permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]
        return [permission() for permission in permission_classes]

# MenuItemView: Handles retrieving, updating, and deleting a single menu item
class MenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]
        return[permission() for permission in permission_classes]

# ManagerUsersView: Handles listing and creating manager users
class ManagerUsersView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]

    def perform_create(self, serializer):
        user = serializer.save()
        manager_group = Group.objects.get_or_create(name='Manager')
        user.groups.add(manager_group)

# ManagerUserView: Handles deleting a manager user
class ManagerUserView(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]

    def perform_destroy(self, instance):
        manager_group = Group.objects.filter(name='Manager').first()
        if not manager_group:
            raise NotFound("Manager group not found.")
        instance.groups.remove(manager_group)
        if instance.groups.count() == 0:
            instance.delete()

# DeliveryCrewUsersView: Handles listing and creating delivery crew users
class DeliveryCrewUsersView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]

    def perform_create(self, serializer):
        user = serializer.save()
        delivery_crew_group, created = Group.objects.get_or_create(name='Delivery crew')
        user.groups.add(delivery_crew_group)

# DeliveryCrewUserView: Handles deleting a delivery crew user
class DeliveryCrewUserView(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & (IsManager | IsAdminUser)]

    def perform_destroy(self, instance):
        delivery_crew_group = Group.objects.filter(name='Delivery crew').first()
        if not delivery_crew_group:
            raise NotFound("Delivery crew group not found.")
        instance.groups.remove(delivery_crew_group)
        if instance.groups.count() == 0:
            instance.delete()

# CartMenuItemsView: Handles listing, creating, and deleting cart items
class CartMenuItemsView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=request.user).delete()
        return Response({"message": "Cart cleared successfully."}, status=status.HTTP_200_OK)

# OrdersView: Handles listing and creating orders
class OrdersView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrdersPagination
    search_fields = ['delivery_crew__username', 'user__username']
    ordering_fields = ['date', 'total', 'status']

    def get_queryset(self):
        user = self.request.user
        if IsManager().has_permission(self.request, self):
            return Order.objects.all()
        elif IsDeliveryCrew().has_permission(self.request, self):
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not IsManager().has_permission(self.request, self) and not IsDeliveryCrew().has_permission(self.request, self):
            cart_items = Cart.objects.filter(user=user)
            if not cart_items.exists():
                raise NotFound("Your cart is empty. Add items to your cart before placing an order.")
            order = serializer.save(user=user)
            order_items = [
                OrderItem(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price
                )
                for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
            cart_items.delete()
        else:
            raise NotFound("Only customers can create orders.")

# OrderView: Handles retrieving, updating, and deleting a single order
class OrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if IsManager().has_permission(self.request, self):
            return Order.objects.all()
        elif IsDeliveryCrew().has_permission(self.request, self):
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        order_items = OrderItem.objects.filter(order=instance)
        order_items_data = OrderItemSerializer(order_items, many=True).data
        response_data = serializer.data
        response_data['order_items'] = order_items_data
        return Response(response_data)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if IsManager().has_permission(self.request, self):
            delivery_crew = request.data.get('delivery_crew')
            status = request.data.get('status')

            if delivery_crew:
                delivery_crew_user = User.objects.filter(id=delivery_crew, groups__name='Delivery crew').first()
                if not delivery_crew_user:
                    return Response({"detail": "Invalid delivery crew user."}, status=status.HTTP_400_BAD_REQUEST)
                instance.delivery_crew = delivery_crew_user

            if status in [0, 1]:
                instance.status = status
            elif status is not None:
                return Response({"detail": "Invalid status value. Status must be 0 (out for delivery) or 1 (delivered)."}, status=status.HTTP_400_BAD_REQUEST)

            instance.save()
            serializer = self.get_serializer(instance, partial=partial)
            return Response(serializer.data)

        elif IsDeliveryCrew().has_permission(self.request, self):
            status = request.data.get('status')
            if status in [0, 1]:
                instance.status = status
                instance.save()
                serializer = self.get_serializer(instance, partial=partial)
                return Response(serializer.data)
            else:
                return Response({"detail": "Invalid status value. Status must be 0 (out for delivery) or 1 (delivered)."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        if IsManager().has_permission(self.request, self):
            return super().destroy(request, *args, **kwargs)
        else:
            return Response({"detail": "You do not have permission to delete this order."}, status=status.HTTP_403_FORBIDDEN)