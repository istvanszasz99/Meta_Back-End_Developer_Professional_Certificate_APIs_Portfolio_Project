from rest_framework import permissions
 
 # IsManager: Custom permission class to check if the user is in the 'Managers' group
class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
       if request.user.groups.filter(name='Managers').exists():
            return True
       
# IsDeliveryCrew: Custom permission class to check if the user is in the 'DeliveryCrew' group
class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name='Delivery crew').exists():
            return True