from django.db import migrations

def copy_subscription_data(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    SubscriptionPlan = apps.get_model('users', 'SubscriptionPlan')

    plan_map = {
        'tier0': 'tier0',
        'tier1': 'tier1',
        'tier2': 'tier2',
    }
    # plan_map keys = old_subscription_plan
    # plan_map values = SubscriptionPlan.tier or unique identifier

    for user in CustomUser.objects.all():
        old_value = user.old_subscription_plan
        if old_value and old_value in plan_map:
            try:
                plan_obj = SubscriptionPlan.objects.get(tier=plan_map[old_value])
                user.new_subscription_plan = plan_obj
                user.save()
            except SubscriptionPlan.DoesNotExist:
                pass  # or handle gracefully

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0005_subscriptionplan_remove_customuser_subscription_plan_and_more'),

    ]

    operations = [
        migrations.RunPython(copy_subscription_data),
    ]
