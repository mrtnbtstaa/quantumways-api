from rest_framework.permissions import BasePermission
from quantumways.constants import Role
from permission_app.models import UserFeaturePermission, Feature

class HasFeatureAccess(BasePermission):

        def has_permission(self, request, view):
            
            user = request.user

            # Check if user is authenticated
            if not user or not request.user.is_authenticated:
                return False
            
            
            user_role = getattr(user, 'user_role', None)
            # Check if user has a role assigned
            if not user_role or not user_role.role:
                return False

            # Grant full access if the user is Top Management
            if user_role and user_role.role == Role.TOP_MANAGEMENT:
                return True
            
            feature_name = getattr(view, 'feature_name', None)

            if not feature_name:
                return False
             
            try:
                
                # Get the permission that has been assigned to that current authenticated user
                permission = UserFeaturePermission.objects.get(
                    user=user,
                    feature__feature_name__iexact=feature_name
                )

            except UserFeaturePermission.DoesNotExist:
                return False
            
            # Get the method from the request
            method = request.method

            if method == "POST" and permission.can_add:
                return True
            if method == "GET" and permission.can_view:
                return True
            if method in ("PUT", "PATCH") and permission.can_update:
                return True
            if method == "DELETE" and permission.can_delete:
                return True
            
            return False

class HasUserRolePermission(BasePermission):
    allowed_roles = None

    def has_permission(self, request, view):
        user = request.user

        # if user not authenticated or not exists
        if not user or not user.is_authenticated:
            return False
        
        # Allow role list to be set on the view
        roles = self.allowed_roles or getattr(view, 'allowed_roles', [])

        # Accessing the role of the user through the reverse relation: User -> UserRole (related_name='user_role')
        user_role = getattr(user, 'user_role', None)

        return user_role.role in roles

# Admin Permission
class IsAdmin(HasUserRolePermission):
    allowed_roles = ['admin']

# HR Permission
class IsHR(HasUserRolePermission):
    allowed_roles = ['hr']

# Maintenance Permission
class IsMaintenance(HasUserRolePermission):
    allowed_roles = ['maintenance']

# Construction Persmission 
class IsConstruction(HasUserRolePermission):
    allowed_roles = ['construction']

# Top management Permission
class IsTopManagement(HasUserRolePermission):
    allowed_roles = ['top management']

# All Roles
class AllRoles(HasUserRolePermission):
    allowed_roles = [
        Role.ADMIN,
        Role.HR,
        Role.MAINTENANCE,
        Role.CONSTRUCTION,
        Role.TOP_MANAGEMENT
    ]