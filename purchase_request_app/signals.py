# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import PurchaseItem, PurchaseRequest
# from django.db.models import Sum
# import logging
# logger = logging.getLogger(__name__)

# @receiver([post_save, post_delete], sender=PurchaseItem)
# def update_total_amount(sender, instance, **kwargs):
#     # Purchase request model instance
#     purchase_request = instance.purchase_request
    
#     total = purchase_request.purchase_items.aggregate(total=Sum('amount'))['total'] or 0

#     purchase_request.total_amount = total

#     purchase_request.save(update_fields=['total_amount'])

#     logger.info(f"Updated total for PR {purchase_request.control_number} = {total}")


