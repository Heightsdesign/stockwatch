# Generated by Django 5.1.1 on 2024-09-24 10:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndicatorLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='alert',
            name='stock_symbol',
        ),
        migrations.RemoveField(
            model_name='alert',
            name='target_price',
        ),
        migrations.AddField(
            model_name='alert',
            name='alert_type',
            field=models.CharField(choices=[('PRICE', 'Price Target'), ('PERCENT_CHANGE', 'Percentage Change'), ('INDICATOR_CHAIN', 'Indicator Chain')], default='None', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='alert',
            name='stock',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='alerts.stock'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='IndicatorChainAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='indicator_chain', to='alerts.alert')),
            ],
        ),
        migrations.CreateModel(
            name='Indicator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('lines', models.ManyToManyField(related_name='indicators', to='alerts.indicatorline')),
            ],
        ),
        migrations.CreateModel(
            name='PercentageChangeAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('lookback_period', models.CharField(blank=True, choices=[('1D', '1 Day'), ('1W', '1 Week'), ('1M', '1 Month'), ('1Y', '1 Year'), ('CUSTOM', 'Custom')], max_length=10, null=True)),
                ('custom_lookback_days', models.PositiveIntegerField(blank=True, null=True)),
                ('direction', models.CharField(choices=[('UP', 'Up'), ('DOWN', 'Down')], max_length=4)),
                ('percentage_change', models.DecimalField(decimal_places=2, max_digits=5)),
                ('alert', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='percentage_change', to='alerts.alert')),
            ],
        ),
        migrations.CreateModel(
            name='PriceTargetAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('alert', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='price_target', to='alerts.alert')),
            ],
        ),
        migrations.CreateModel(
            name='IndicatorCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_in_chain', models.PositiveIntegerField()),
                ('condition_operator', models.CharField(choices=[('GT', '>'), ('LT', '<'), ('EQ', '='), ('GTE', '≥'), ('LTE', '≤')], max_length=3)),
                ('value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('indicator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alerts.indicator')),
                ('indicator_chain_alert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='alerts.indicatorchainalert')),
                ('indicator_line', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='alerts.indicatorline')),
            ],
            options={
                'unique_together': {('indicator_chain_alert', 'position_in_chain')},
            },
        ),
    ]
