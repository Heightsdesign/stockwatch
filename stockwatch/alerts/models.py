from django.db import models
from django.conf import settings  # Import settings to access AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.db.models import JSONField


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.symbol


class Alert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('PRICE', 'Price Target'),
        ('PERCENT_CHANGE', 'Percentage Change'),
        ('INDICATOR_CHAIN', 'Indicator Chain'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert ({self.get_alert_type_display()}) for {self.user.email} on {self.stock.name}"


class PriceTargetAlert(models.Model):
    CONDITION_CHOICES = [
        ('GT', 'Greater Than'),
        ('LT', 'Less Than'),
    ]

    alert = models.OneToOneField(Alert, related_name='price_target_alert', on_delete=models.CASCADE)
    target_price = models.FloatField()
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, null=True, blank=True)
    check_interval = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"PriceTargetAlert: {self.stock.symbol} {self.condition} {self.target_price}"

    def save(self, *args, **kwargs):
        if self.alert.alert_type != 'PRICE':
            raise ValidationError("Alert type must be 'PRICE' for a PriceTargetAlert.")
        super().save(*args, **kwargs)


class PercentageChangeAlert(models.Model):
    TIMEFRAME_CHOICES = [
        ('1D', '1 Day'),
        ('1W', '1 Week'),
        ('1M', '1 Month'),
        ('1Y', '1 Year'),
        ('CUSTOM', 'Custom'),
    ]

    alert = models.OneToOneField(Alert, on_delete=models.CASCADE, related_name='percentage_change')
    lookback_period = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES, null=True, blank=True)
    custom_lookback_days = models.PositiveIntegerField(null=True, blank=True)
    direction = models.CharField(max_length=4, choices=[('UP', 'Up'), ('DOWN', 'Down')])
    percentage_change = models.DecimalField(max_digits=5, decimal_places=2)
    check_interval = models.IntegerField(default=60)

    def __str__(self):
        return f"Percentage Change Alert for {self.alert.stock.name} ({self.direction} {self.percentage_change}%)"

    def clean(self):
        if not self.lookback_period:
            raise ValidationError("'lookback_period' must be provided.")
        if self.lookback_period == 'CUSTOM' and not self.custom_lookback_days:
            raise ValidationError("'custom_lookback_days' must be provided when 'lookback_period' is 'CUSTOM'.")

    def save(self, *args, **kwargs):
        if self.alert.alert_type != 'PERCENT_CHANGE':
            raise ValidationError("Alert type must be 'PERCENT_CHANGE' for a PercentageChangeAlert.")
        self.full_clean()
        super().save(*args, **kwargs)


class IndicatorDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.display_name

class IndicatorParameter(models.Model):
    PARAMETER_TYPE_CHOICES = [
        ('int', 'Integer'),
        ('float', 'Float'),
        ('string', 'String'),
        ('choice', 'Choice'),
    ]

    indicator = models.ForeignKey(
        IndicatorDefinition,
        on_delete=models.CASCADE,
        related_name='parameters'
    )
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    param_type = models.CharField(max_length=20, choices=PARAMETER_TYPE_CHOICES)
    required = models.BooleanField(default=True)
    default_value = models.CharField(max_length=100, null=True, blank=True)
    choices = JSONField(null=True, blank=True)  # For parameters with predefined choices

    def __str__(self):
        return f"{self.indicator.display_name} - {self.display_name}"


class Indicator(models.Model):
    name = models.CharField(max_length=50, unique=True)
    lines = models.ManyToManyField('IndicatorLine', related_name='indicators')

    def __str__(self):
        return self.name

class IndicatorLine(models.Model):
    indicator = models.ForeignKey(
        IndicatorDefinition,
        on_delete=models.CASCADE,
        related_name='lines',
        null=True,  # Allow null values
        blank=True
    )
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100, default='Line')

    def __str__(self):
        return f"{self.indicator.display_name if self.indicator else 'No Indicator'} - {self.display_name}"


class IndicatorChainAlert(models.Model):
    alert = models.OneToOneField(Alert, on_delete=models.CASCADE, related_name='indicator_chain')
    check_interval = models.IntegerField(default=60)  # in minutes

    def __str__(self):
        return f"Indicator Chain Alert for {self.alert.stock.name} ({self.condition_count} conditions)"

    @property
    def condition_count(self):
        return self.conditions.count()

    def save(self, *args, **kwargs):
        if self.alert.alert_type != 'INDICATOR_CHAIN':
            raise ValidationError("Alert type must be 'INDICATOR_CHAIN' for an IndicatorChainAlert.")
        super().save(*args, **kwargs)


class IndicatorCondition(models.Model):
    VALUE_TYPE_CHOICES = [
        ('NUMBER', 'Number'),
        ('PRICE', 'Current Price'),
        ('INDICATOR_LINE', 'Indicator Line'),
    ]
    CONDITION_OPERATOR_CHOICES = [
        ('GT', 'Greater Than'),
        ('LT', 'Less Than'),
        ('EQ', 'Equal To'),
        # Add other operators as needed
    ]
    TIMEFRAME_CHOICES = [
        ('1MIN', '1 Minute'),
        ('5MIN', '5 Minutes'),
        ('15MIN', '15 Minutes'),
        ('30MIN', '30 Minutes'),
        ('1H', '1 Hour'),
        ('4H', '4 Hours'),
        ('1D', '1 Day'),
        # Add other timeframes as needed
    ]

    indicator_chain_alert = models.ForeignKey(
        IndicatorChainAlert,
        on_delete=models.CASCADE,
        related_name='conditions'
    )
    # Main indicator details
    indicator = models.ForeignKey(
        IndicatorDefinition,
        on_delete=models.CASCADE,
        related_name='conditions'
    )
    indicator_line = models.CharField(max_length=50, null=True, blank=True)
    indicator_timeframe = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES, default='1H')

    condition_operator = models.CharField(max_length=20, choices=CONDITION_OPERATOR_CHOICES)

    # Comparison value details
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES, default='NUMBER')
    value_number = models.FloatField(null=True, blank=True)
    value_indicator = models.ForeignKey(
        IndicatorDefinition,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comparison_conditions'
    )
    value_indicator_line = models.CharField(max_length=50, null=True, blank=True)
    value_timeframe = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES, null=True, blank=True)

    indicator_parameters = models.JSONField(null=True, blank=True)
    value_indicator_parameters = models.JSONField(null=True, blank=True)

    position_in_chain = models.PositiveIntegerField()

    def __str__(self):
        return f"IndicatorCondition {self.position_in_chain}: {self.indicator.display_name} {self.condition_operator} {self.get_value_display()}"

    def get_value_display(self):
        if self.value_type == 'NUMBER':
            return f"{self.value_number}"
        elif self.value_type == 'PRICE':
            return "Current Price"
        elif self.value_type == 'INDICATOR_LINE':
            return f"{self.value_indicator.display_name} ({self.value_indicator_line})"
        return "Unknown Value"

    def save(self, *args, **kwargs):
        # Validate maximum number of conditions
        if self.pk is None:  # New condition
            current_count = self.indicator_chain_alert.conditions.count()
            if current_count >= 5:
                raise ValidationError("Cannot add more than 5 conditions to an indicator chain.")
        super().save(*args, **kwargs)

