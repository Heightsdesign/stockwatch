# Generated by Django 5.1.1 on 2024-11-06 12:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_customuser_phone_number_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('iso_code', models.CharField(max_length=2, unique=True)),
                ('phone_prefix', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.country'),
        ),
    ]
