import django_filters
from authentication_app.models import User
from django_filters import Filter
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils.timezone import make_aware

class CustomDateCreatedFilter(Filter):
    
    def filter(self, qs, value):
        if not value:
            return qs

        value = value.strip().lower()

        today = now().date()

        if value == 'last_day':
            yesterday = today - timedelta(days=1)
            return qs.filter(created_at__date=yesterday)

        elif value == 'last_15_days':
            last_15_days = today - timedelta(days=15)
            return qs.filter(created_at__gte=last_15_days)

        elif value == 'last_month':
            last_month = today - timedelta(days=31)
            return qs.filter(created_at__gte=last_month)

        # Custom dates
        elif '~' in value:
            try:
                start_str, end_str = value.split("~")
                start_date = make_aware(datetime.strptime(start_str.strip(), "%B %d, %Y"))
                end_date = make_aware(datetime.strptime(end_str.strip(), "%B %d, %Y"))
                return qs.filter(created_at__date__range=(start_date.date(), end_date.date()))
            except (ValueError, IndexError):
                return qs.none()

        return qs
    


class UserFilter(django_filters.FilterSet):
    ordering = django_filters.OrderingFilter(
        fields=(
            ('full_name', 'asc'),
        )
    )
    role = django_filters.CharFilter(
        field_name='user_role__role'
    )
    date_created = CustomDateCreatedFilter()
    active = django_filters.BooleanFilter(
        field_name='is_active',
    )
    last_active = CustomDateCreatedFilter()

  
    class Meta:
        model = User
        fields = ['ordering' ,'role', 'date_created', 'active', 'last_active']


