from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PurchaseOrder, PurchaseItem
from django.db.models import Sum
import logging
logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=PurchaseItem)
def update_total_amount(sender, instance, **kwargs):
    # Purchase request model instance
    purchase_order = instance.purchase_order
    
    total = purchase_order.items.aggregate(total=Sum('amount'))['total'] or 0

    purchase_order.total_amount = total

    purchase_order.save(update_fields=['total_amount'])

    logger.info(f"Updated total for PR {purchase_order.po_control_no} = {total}")