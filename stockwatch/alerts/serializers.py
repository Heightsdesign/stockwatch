# alerts/serializers.py

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
)

User = get_user_model()


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

    # ... other methods ...

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
        # Update PriceTargetAlert-specific fields
        instance.target_price = validated_data.get('target_price', instance.target_price)
        instance.condition = validated_data.get('condition', instance.condition)
        instance.check_interval = validated_data.get('check_interval', instance.check_interval)
        instance.save()

        # Update Alert-specific field 'is_active' if provided
        is_active = validated_data.get('alert', {}).get('is_active')
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
            'custom_lookback_days',
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
            custom_lookback_days=custom_lookback_days,
            direction=direction,
            check_interval=check_interval,
        )

        return percentage_change_alert

    def update(self, instance, validated_data):
        # Update PercentageChangeAlert-specific fields
        instance.lookback_period = validated_data.get('lookback_period', instance.lookback_period)
        instance.custom_lookback_days = validated_data.get('custom_lookback_days', instance.custom_lookback_days)
        instance.direction = validated_data.get('direction', instance.direction)
        instance.percentage_change = validated_data.get('percentage_change', instance.percentage_change)
        instance.check_interval = validated_data.get('check_interval', instance.check_interval)
        instance.save()

        # Update Alert-specific field 'is_active' if provided
        is_active = validated_data.get('is_active')
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
        fields = ['id', 'name']


class IndicatorSerializer(serializers.ModelSerializer):
    lines = IndicatorLineSerializer(many=True, read_only=True)

    class Meta:
        model = Indicator
        fields = ['id', 'name', 'lines']


class IndicatorConditionSerializer(serializers.ModelSerializer):
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
        ]

    def validate(self, data):
        value_type = data.get('value_type')

        if value_type == 'NUMBER':
            if data.get('value_number') is None:
                raise serializers.ValidationError({
                    'value_number': "This field is required when 'value_type' is 'NUMBER'."
                })
        elif value_type == 'INDICATOR_LINE':
            if not data.get('value_indicator'):
                raise serializers.ValidationError({
                    'value_indicator': "This field is required when 'value_type' is 'INDICATOR_LINE'."
                })
            if not data.get('value_indicator_line'):
                raise serializers.ValidationError({
                    'value_indicator_line': "This field is required when 'value_type' is 'INDICATOR_LINE'."
                })
            if not data.get('value_timeframe'):
                raise serializers.ValidationError({
                    'value_timeframe': "This field is required when 'value_type' is 'INDICATOR_LINE'."
                })
        elif value_type == 'PRICE':
            # No additional fields required
            pass
        else:
            raise serializers.ValidationError("Invalid 'value_type' provided.")

        return data

# serializers.py
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
        fields = ['id', 'stock', 'conditions', 'is_active']
        read_only_fields = ['id']

    def create(self, validated_data):
        conditions_data = validated_data.pop('conditions')
        stock = validated_data.pop('stock')
        is_active = validated_data.pop('is_active', True)

        user = self.context['request'].user

        # Create the Alert instance
        alert = Alert.objects.create(
            user=user,
            stock=stock,
            alert_type='INDICATOR_CHAIN',
            is_active=is_active
        )

        # Create the IndicatorChainAlert instance
        indicator_chain_alert = IndicatorChainAlert.objects.create(alert=alert)

        # Create IndicatorCondition instances
        for condition_data in conditions_data:
            IndicatorCondition.objects.create(
                indicator_chain_alert=indicator_chain_alert,
                **condition_data
            )

        return indicator_chain_alert

    def update(self, instance, validated_data):
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


