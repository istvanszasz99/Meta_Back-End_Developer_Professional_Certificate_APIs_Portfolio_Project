from django.urls import path, include
from . import views


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('categories/',views.CategoryView.as_view()),
    path('menu-items/',views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>',views.MenuItemView.as_view()),
    path('groups/manager/users/',views.ManagerUsersView.as_view()),
    path('groups/manager/users/<int:pk>',views.ManagerUserView.as_view()),
    path('groups/delivery-crew/users/',views.DeliveryCrewUsersView.as_view()),
    path('groups/delivery-crew/users/<int:pk>',views.DeliveryCrewUserView.as_view()),
    path('cart/menu-items/',views.CartMenuItemsView.as_view()),
    path('orders/',views.OrdersView.as_view()),
    path('orders/<int:pk>',views.OrderView.as_view()),
]
