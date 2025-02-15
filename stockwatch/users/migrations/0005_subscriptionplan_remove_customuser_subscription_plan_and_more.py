# Generated by Django 5.1.1 on 2025-02-01 13:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_customuser_subscription_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('tier', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='subscription_plan',
        ),
        migrations.AddField(
            model_name='customuser',
            name='old_subscription_plan',
            field=models.CharField(blank=True, default='tier0', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='new_subscription_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='users.subscriptionplan'),
        ),
    ]
