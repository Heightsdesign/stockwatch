# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomUser
from .models import SubscriptionPlan

@receiver(post_save, sender=CustomUser)
def assign_default_plan(sender, instance, created, **kwargs):
    if created and not instance.subscription_plan:
        # Create or get the free plan
        free_plan, _ = SubscriptionPlan.objects.get_or_create(
            tier='tier0',
            defaults={'name': 'Free', 'price': 0.00},
        )
        instance.subscription_plan = free_plan
        instance.save()
