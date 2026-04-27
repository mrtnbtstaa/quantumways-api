from django.urls import path
from .views import AssignUserBasedPermissionsView


urlpatterns = [
    path('v1/users/<uuid:user_id>/permissions/', AssignUserBasedPermissionsView.as_view(), name='create_retrieve_permission')
]


