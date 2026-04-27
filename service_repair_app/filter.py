from quantumways.filter import CustomDateCreatedFilter
import django_filters
from .models import ServiceRepair

class ServiceRepairFilter(django_filters.FilterSet):

    equipment = django_filters.CharFilter(field_name='tools_equipment', lookup_expr='icontains')
    date_created = CustomDateCreatedFilter()
    last_active = CustomDateCreatedFilter()

    class Meta:
        model = ServiceRepair
        fields = ['equipment', 'date_created', 'last_active']

