# alerts/serializers.py

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Stock,
    Alert,
    PriceTargetAlert,
    PercentageChangeAlert,
    Indicator,
    IndicatorLine,
    IndicatorChainAlert,
    IndicatorCondition,
    IndicatorDefinition,
    IndicatorParameter
)

User = get_user_model()


def enforce_plan_limit(user, requested_alert_type):
    print("=== DEBUG enforce_plan_limit ===")
    print("User ID:", user.id)
    print("User subscription_plan:", user.subscription_plan)

    plan_key = settings.TIER_TO_PLAN.get(user.subscription_plan, 'FREE')
    plan_info = settings.PLAN_LIMITS.get(plan_key, {})
    print("Plan info:", plan_info)

    max_alerts = plan_info.get('max_alerts', 0)
    allow_chain = plan_info.get('allow_indicator_chain', False)
    print("max_alerts:", max_alerts, " allow_chain:", allow_chain)

    current_total_alerts = Alert.objects.filter(user=user).count()
    print("current_total_alerts:", current_total_alerts)

    if requested_alert_type == 'INDICATOR_CHAIN' and not allow_chain:
        raise DRFValidationError({"detail": "Your subscription plan does not allow Indicator Chain alerts."})

    if current_total_alerts >= max_alerts:
        raise DRFValidationError(
            {
                "detail": f"You have reached the maximum number of alerts allowed for your subscription plan ({max_alerts})."}
        )
class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['symbol', 'name']


class AlertSerializer(serializers.ModelSerializer):
    stock_details = serializers.SerializerMethodField()
    price_target_alert = serializers.SerializerMethodField()
    percentage_change_alert = serializers.SerializerMethodField()
    indicator_chain_alert = serializers.SerializerMethodField()

    stock = serializers.SlugRelatedField(
        slug_field='symbol',
        queryset=Stock.objects.all(),
        required=True
    )
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    alert_type = serializers.CharField(read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id',
            'user',
            'stock',
            'stock_details',
            'alert_type',
            'is_active',
            'created_at',
            'last_triggered_at',
            'price_target_alert',
            'percentage_change_alert',
            'indicator_chain_alert',
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['alert_type'] = self.context.get('alert_type')
        return Alert.objects.create(**validated_data)

    def update(self, instance, validated_data):
        stock_data = validated_data.pop('stock', None)
        if stock_data:
            instance.stock = stock_data  # Assign the Stock instance directly

        instance.alert_type = validated_data.get('alert_type', instance.alert_type)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.last_triggered_at = validated_data.get('last_triggered_at', instance.last_triggered_at)
        instance.save()
        return instance

    def get_price_target_alert(self, obj):
        try:
            price_alert = obj.price_target_alert  # Use the correct related_name
            return PriceTargetAlertSerializer(price_alert).data
        except PriceTargetAlert.DoesNotExist:
            return None

    def get_percentage_change_alert(self, obj):
        try:
            percent_alert = obj.percentage_change  # Use the correct related_name
            return PercentageChangeAlertSerializer(percent_alert).data
        except PercentageChangeAlert.DoesNotExist:
            return None

    def get_indicator_chain_alert(self, obj):
        try:
            indicator_alert = obj.indicator_chain  # Use the correct related_name
            return IndicatorChainAlertSerializer(indicator_alert).data
        except IndicatorChainAlert.DoesNotExist:
            return None

    def get_stock_details(self, obj):
        stock_instance = obj.stock
        return {
            'symbol': stock_instance.symbol,
            'name': stock_instance.name,
        }


class PriceTargetAlertSerializer(serializers.ModelSerializer):
    stock = serializers.SlugRelatedField(
        slug_field='symbol',
        queryset=Stock.objects.all(),
        required=True,
        write_only=True
    )
    stock_details = serializers.SerializerMethodField(read_only=True)
    condition = serializers.ChoiceField(
        choices=PriceTargetAlert.CONDITION_CHOICES,
        required=True
    )
    check_interval = serializers.IntegerField(
        required=True,
        min_value=1
    )
    is_active = serializers.BooleanField(source='alert.is_active', required=False)

    class Meta:
        model = PriceTargetAlert
        fields = [
            'id',
            'stock',
            'stock_details',
            'target_price',
            'condition',
            'check_interval',
            'is_active'
        ]
        read_only_fields = ['id', 'stock_details']

    def get_stock_details(self, obj):
        stock = obj.alert.stock
        return {
            'symbol': stock.symbol,
            'name': stock.name
        }

    def create(self, validated_data):
        user = self.context['request'].user
        stock = validated_data.pop('stock')
        target_price = validated_data.get('target_price')
        condition = validated_data.get('condition')
        check_interval = validated_data.get('check_interval')
        is_active = validated_data.get('alert', {}).get('is_active', True)

        enforce_plan_limit(user, requested_alert_type='PRICE')

        # Create the Alert instance
        alert = Alert.objects.create(
            user=user,
            stock=stock,
            alert_type='PRICE',
            is_active=is_active
        )

        # Create the PriceTargetAlert instance
        price_target_alert = PriceTargetAlert.objects.create(
            alert=alert,
            target_price=target_price,
            condition=condition,
            check_interval=check_interval
        )

        return price_target_alert

    def update(self, instance, validated_data):

        # Update Alert-specific field 'is_active' if provided
        is_active = validated_data.get('alert', {}).get('is_active')

        # If the user is trying to reactivate the alert, check plan limits
        if is_active and not instance.alert.is_active:
            user = self.context['request'].user
            enforce_plan_limit(user, 'PRICE')

        # Update PriceTargetAlert-specific fields
        instance.target_price = validated_data.get('target_price', instance.target_price)
        instance.condition = validated_data.get('condition', instance.condition)
        instance.check_interval = validated_data.get('check_interval', instance.check_interval)
        instance.save()


        if is_active is not None:
            instance.alert.is_active = is_active
            instance.alert.save()

        return instance


class PercentageChangeAlertSerializer(serializers.ModelSerializer):
    stock = serializers.SlugRelatedField(
        slug_field='symbol',
        queryset=Stock.objects.all(),
        required=True,
        write_only=True
    )
    stock_details = serializers.SerializerMethodField(read_only=True)
    is_active = serializers.BooleanField(source='alert.is_active', required=False)

    class Meta:
        model = PercentageChangeAlert
        fields = [
            'id',
            'stock',
            'stock_details',
            'lookback_period',
            'direction',
            'percentage_change',
            'check_interval',
            'is_active'
        ]
        read_only_fields = ['id', 'stock_details']

    def get_stock_details(self, obj):
        stock = obj.alert.stock
        return {
            'symbol': stock.symbol,
            'name': stock.name
        }

    def create(self, validated_data):
        user = self.context['request'].user
        stock = validated_data.pop('stock')

        is_active = validated_data.pop('is_active', True)

        # Extract other fields from validated_data
        percentage_change = validated_data['percentage_change']
        lookback_period = validated_data['lookback_period']
        custom_lookback_days = validated_data.get('custom_lookback_days')
        direction = validated_data['direction']
        check_interval = validated_data.get('check_interval', 60)  # Default to 60 if not provided

        enforce_plan_limit(user, requested_alert_type='PERCENTAGE_CHANGE')

        # Create the Alert instance
        alert = Alert.objects.create(
            user=user,
            stock=stock,
            alert_type='PERCENT_CHANGE',
            is_active=is_active
        )

        # Create the PercentageChangeAlert instance
        percentage_change_alert = PercentageChangeAlert.objects.create(
            alert=alert,
            percentage_change=percentage_change,
            lookback_period=lookback_period,
            direction=direction,
            check_interval=check_interval,
        )

        return percentage_change_alert

    def update(self, instance, validated_data):

        is_active = validated_data.get('alert', {}).get('is_active', instance.alert.is_active)

        # If the user is trying to reactivate the alert, check plan limits
        if is_active and not instance.alert.is_active:
            user = self.context['request'].user
            enforce_plan_limit(user, 'PERCENTAGE_CHANGE')

        # Update PercentageChangeAlert-specific fields
        instance.lookback_period = validated_data.get('lookback_period', instance.lookback_period)
        instance.custom_lookback_days = validated_data.get('custom_lookback_days', instance.custom_lookback_days)
        instance.direction = validated_data.get('direction', instance.direction)
        instance.percentage_change = validated_data.get('percentage_change', instance.percentage_change)
        instance.check_interval = validated_data.get('check_interval', instance.check_interval)
        instance.save()

        if is_active is not None:
            instance.alert.is_active = is_active
            instance.alert.save()

        return instance

    def validate(self, data):
        if data.get('lookback_period') == 'CUSTOM':
            if not data.get('custom_lookback_days'):
                raise serializers.ValidationError({
                    'custom_lookback_days': "'custom_lookback_days' must be provided when 'lookback_period' is 'CUSTOM'."
                })
        else:
            data['custom_lookback_days'] = None  # Ensure it's set to None when not used
        return data


class IndicatorLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorLine
        fields = ['name', 'display_name']


class IndicatorSerializer(serializers.ModelSerializer):
    lines = IndicatorLineSerializer(many=True, read_only=True)

    class Meta:
        model = Indicator
        fields = ['id', 'name', 'lines']


class IndicatorConditionSerializer(serializers.ModelSerializer):

    indicator = serializers.SlugRelatedField(
        slug_field='name',
        queryset=IndicatorDefinition.objects.all()
    )
    value_indicator = serializers.SlugRelatedField(
        slug_field='name',
        queryset=IndicatorDefinition.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = IndicatorCondition
        fields = [
            'id',
            'indicator',
            'indicator_line',
            'indicator_timeframe',
            'condition_operator',
            'value_type',
            'value_number',
            'value_indicator',
            'value_indicator_line',
            'value_timeframe',
            'position_in_chain',
            'indicator_parameters',
            'value_indicator_parameters'
        ]

    def validate(self, data):
        # Existing validation...
        indicator = data.get('indicator')
        parameters = data.get('indicator_parameters', {})

        # Retrieve parameter definitions from the database
        param_definitions = indicator.parameters.all()

        validated_parameters = {}
        for param_def in param_definitions:
            param_name = param_def.name
            param_type = param_def.param_type
            required = param_def.required
            default_value = param_def.default_value

            if param_name in parameters:
                value = parameters[param_name]
                # Type validation
                if param_type == 'int' and not isinstance(value, int):
                    raise serializers.ValidationError({param_name: "Must be an integer."})
                if param_type == 'float' and not isinstance(value, (int, float)):
                    raise serializers.ValidationError({param_name: "Must be a float."})
                if param_type == 'string' and not isinstance(value, str):
                    raise serializers.ValidationError({param_name: "Must be a string."})
                if param_type == 'choice' and value not in param_def.choices:
                    raise serializers.ValidationError({param_name: f"Invalid choice. Available choices are: {param_def.choices}"})

                if param_name in ['length', 'lookback']:  # or any param name you want to constrain
                    if float(value) > 400:  # or int(value) > 400, depending on param_type
                        raise serializers.ValidationError(
                            {param_name: "Maximum allowed length is 400."}
                        )

                validated_parameters[param_name] = value
            else:
                if required:
                    raise serializers.ValidationError({param_name: "This parameter is required."})
                else:
                    # Use default value if provided
                    if default_value:
                        # Convert default_value to the correct type
                        if param_type == 'int':
                            validated_parameters[param_name] = int(default_value)
                        elif param_type == 'float':
                            validated_parameters[param_name] = float(default_value)
                        else:
                            validated_parameters[param_name] = default_value
                    else:
                        validated_parameters[param_name] = None

        data['indicator_parameters'] = validated_parameters
        return data

    def create(self, validated_data):
        parameters = validated_data.pop('indicator_parameters', {})
        condition = super().create(validated_data)
        condition.indicator_parameters = parameters
        condition.save()
        return condition

    def update(self, instance, validated_data):
        parameters = validated_data.pop('indicator_parameters', {})
        instance = super().update(instance, validated_data)
        instance.indicator_parameters = parameters
        instance.save()
        return instance


class IndicatorChainAlertSerializer(serializers.ModelSerializer):
    conditions = IndicatorConditionSerializer(many=True)
    stock = serializers.SlugRelatedField(
        slug_field='symbol',
        queryset=Stock.objects.all(),
        write_only=True
    )
    is_active = serializers.BooleanField(source='alert.is_active', required=False)

    class Meta:
        model = IndicatorChainAlert
        fields = ['id', 'stock', 'conditions', 'is_active', 'check_interval']
        read_only_fields = ['id']

    def create(self, validated_data):

        conditions_data = validated_data.pop('conditions')
        check_interval = validated_data.pop('check_interval', 60)
        stock = validated_data.pop('stock')
        is_active = validated_data.pop('is_active', True)

        user = self.context['request'].user

        enforce_plan_limit(user, 'INDICATOR_CHAIN')

        # Create the Alert instance
        alert = Alert.objects.create(
            user=user,
            stock=stock,
            alert_type='INDICATOR_CHAIN',
            is_active=is_active
        )

        # Create the IndicatorChainAlert instance
        indicator_chain_alert = IndicatorChainAlert.objects.create(
            alert=alert,
            check_interval=check_interval,
        )

        # Create IndicatorCondition instances
        for condition_data in conditions_data:
            IndicatorCondition.objects.create(
                indicator_chain_alert=indicator_chain_alert,
                **condition_data
            )

        return indicator_chain_alert

    def update(self, instance, validated_data):
        user = self.context['request'].user
        is_active = validated_data.get('is_active', instance.alert.is_active)

        # Enforce plan limits when reactivating the alert
        if is_active and not instance.alert.is_active:
            enforce_plan_limit(user, requested_alert_type='INDICATOR_CHAIN')

        conditions_data = validated_data.pop('conditions', None)
        stock = validated_data.get('stock', None)
        is_active = validated_data.get('is_active')

        # Update Alert fields if needed
        alert = instance.alert
        if stock:
            alert.stock = stock
        if is_active is not None:
            alert.is_active = is_active
        alert.save()

        # Handle the conditions
        if conditions_data is not None:
            # Delete existing conditions
            instance.conditions.all().delete()

            # Create new conditions
            for condition_data in conditions_data:
                IndicatorCondition.objects.create(
                    indicator_chain_alert=instance,
                    **condition_data
                )

        return instance


class IndicatorParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorParameter
        fields = ['name', 'display_name', 'param_type', 'required', 'default_value', 'choices']


class IndicatorDefinitionSerializer(serializers.ModelSerializer):
    parameters = IndicatorParameterSerializer(many=True, read_only=True)
    lines = IndicatorLineSerializer(many=True, read_only=True)

    class Meta:
        model = IndicatorDefinition
        fields = ['name', 'display_name', 'description', 'parameters', 'lines']


