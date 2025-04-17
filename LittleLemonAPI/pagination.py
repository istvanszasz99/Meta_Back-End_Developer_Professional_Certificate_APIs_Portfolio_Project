from rest_framework.pagination import PageNumberPagination

# MenuItemsPagination: Custom pagination class for menu items
class MenuItemsPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50

# OrdersPagination: Custom pagination class for orders
class OrdersPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100