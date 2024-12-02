# alerts/tasks.py

from celery import shared_task
from django.utils import timezone
from .utils import get_stock_data, calculate_indicator
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd

from .models import Alert, IndicatorChainAlert, IndicatorCondition, Indicator
from .notifications import send_sms_notification


def send_alert_notification(alert, current_value):
    user = alert.user
    message = f"Your alert condition has been met.\nCurrent Value: {current_value}"

    # Email Notification
    if user.receive_email_notifications and user.email:
        subject = f"Stock Alert Triggered for {alert.stock.symbol}"
        from_email = settings.DEFAULT_FROM_EMAIL
        try:
            send_mail(subject, message, from_email, [user.email])
        except Exception as e:
            print(f"Error sending email to {user.email}: {e}")

    # SMS Notification (if implemented)
    if user.receive_sms_notifications and user.phone_number:
        try:
            send_sms_notification(user, message)
        except Exception as e:
            print(f"Error sending SMS to {user.phone_number}: {e}")

@shared_task
def process_alerts():
    print('Processing alerts ...')
    now = timezone.now()
    active_alerts = Alert.objects.filter(is_active=True)

    # Group alerts by stock symbol
    alerts_by_symbol = {}
    for alert in active_alerts:
        print(f'Alert for {alert.stock.symbol} is active.')
        symbol = alert.stock.symbol
        if symbol not in alerts_by_symbol:
            alerts_by_symbol[symbol] = []
        alerts_by_symbol[symbol].append(alert)

    # Process alerts for each stock symbol
    for symbol, alerts in alerts_by_symbol.items():
        data = get_stock_data(symbol)
        if data.empty:
            continue  # Skip if no data is returned

        for alert in alerts:
            # Get the correct check_interval based on alert type
            if alert.alert_type == 'PRICE':
                check_interval = alert.price_target_alert.check_interval
            elif alert.alert_type == 'PERCENT_CHANGE':
                check_interval = alert.percentage_change.check_interval
            elif alert.alert_type == 'INDICATOR_CHAIN':
                check_interval = alert.indicator_chain.check_interval
            else:
                check_interval = 1  # Default if no specific interval is found

            # Check if it's time to process the alert based on its check_interval
            last_checked = alert.last_triggered_at or alert.created_at
            if (now - last_checked).total_seconds() >= check_interval * 60:
                process_single_alert(alert, data)
                alert.last_triggered_at = now
                alert.save()


def process_single_alert(alert, data):
    if alert.alert_type == 'PRICE':
        process_price_target_alert(alert, data)
    elif alert.alert_type == 'PERCENT_CHANGE':
        process_percentage_change_alert(alert, data)
    elif alert.alert_type == 'INDICATOR_CHAIN':
        process_indicator_chain_alert(alert)


def process_price_target_alert(alert, data):
    current_price = data['close'].iloc[-1]
    target_price = alert.price_target_alert.target_price
    condition = alert.price_target_alert.condition

    condition_met = (condition == 'GT' and current_price > target_price) or \
                    (condition == 'LT' and current_price < target_price)

    if condition_met:
        send_alert_notification(alert, current_price)
        alert.is_active = False  # Deactivate the alert after triggering
        alert.save()


def process_percentage_change_alert(alert, data):
    print('Processing percentage change alert ...')
    percentage_change_alert = alert.percentage_change
    direction = percentage_change_alert.direction
    target_change = float(percentage_change_alert.percentage_change)
    lookback_period = percentage_change_alert.lookback_period
    custom_days = percentage_change_alert.custom_lookback_days or 1

    # Determine the lookback period in days
    period_map = {
        '5Min': '5m', '15Min': '15m', '30Min': '30m', '60Min': '60m',
        '1D': '1d', '1W': '1wk', '1M': '1mo', '3M': '3mo', 'CUSTOM': f'{custom_days}d'
    }
    period = period_map.get(lookback_period, '1d')

    # Fetch historical data for the lookback period
    data = get_stock_data(alert.stock.symbol, period=period)
    print(f'Fetched data : {data}')

    initial_price = data['open'].iloc[0]
    print(f'Initial Price  : {initial_price}')

    current_price = data['close'].iloc[0]
    print(f'Current Price  : {current_price}')

    actual_change = ((current_price - initial_price) / initial_price) * 100

    condition_met = False
    if direction == 'UP' and actual_change >= target_change:
        condition_met = True
    elif direction == 'DOWN' and actual_change <= -target_change:
        condition_met = True

    if condition_met:
        send_alert_notification(alert, actual_change)
        alert.is_active = False  # Deactivate the alert after triggering
        alert.save()

def resample_data(df, timeframe):
    """
    Resample the DataFrame according to the specified timeframe.

    Args:
        df (pd.DataFrame): Original DataFrame with datetime index.
        timeframe (str): Timeframe string, e.g., '1MIN', '5MIN', '1H', '1D'

    Returns:
        pd.DataFrame: Resampled DataFrame.
    """
    timeframe_map = {
        '1MIN': '1T',
        '5MIN': '5T',
        '15MIN': '15T',
        '30MIN': '30T',
        '1H': '1H',
        '4H': '4H',
        '1D': '1D',
    }
    resample_freq = timeframe_map.get(timeframe)
    if resample_freq:
        resampled_data = df.resample(resample_freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        }).dropna()
        return resampled_data
    else:
        raise ValueError(f"Unknown timeframe: {timeframe}")


def process_indicator_chain_alert(alert):
    print(f'Processing indicator chain alert for {alert.stock.symbol}')
    all_conditions_met = True

    # Fetch the latest data for the stock
    data = get_stock_data(alert.stock.symbol)
    if data.empty:
        print(f'No data found for {alert.stock.symbol}')
        return

    # Ensure the data has a datetime index
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)

    # Access the IndicatorChainAlert instance
    try:
        indicator_chain_alert = alert.indicator_chain  # Assuming the related name is 'indicator_chain_alert'
    except ObjectDoesNotExist:
        print(f"No IndicatorChainAlert associated with alert {alert.id}")
        return

    # Iterate over each condition in the chain
    for condition in indicator_chain_alert.conditions.all().order_by('position_in_chain'):
        print(f"Evaluating condition at position {condition.position_in_chain}")

        # Fetch the main indicator definition
        try:
            indicator_def = Indicator.objects.get(name=condition.indicator)
        except Indicator.DoesNotExist:
            print(f"Indicator '{condition.indicator}' does not exist for condition {condition.id}")
            all_conditions_met = False
            break

        # Resample data according to indicator_timeframe
        try:
            resampled_data = resample_data(data, condition.indicator_timeframe)
        except ValueError as e:
            print(f"Error resampling data: {e}")
            all_conditions_met = False
            break

        # Prepare parameters for the main indicator calculation
        parameters = condition.indicator_parameters or {}

        # Calculate the main indicator value
        try:
            indicator_value_series = calculate_indicator(
                indicator_name=indicator_def.name,
                df=resampled_data,
                line=condition.indicator_line,
                parameters=parameters
            )
            indicator_value = indicator_value_series.iloc[-1]
            print(f"Main Indicator ({indicator_def.display_name}): {indicator_value}")
        except Exception as e:
            print(f"Error calculating {indicator_def.display_name}: {e}")
            all_conditions_met = False
            break

        # Determine the comparison value
        if condition.value_type == 'NUMBER':
            comparison_value = condition.value_number
            print(f"Comparison Value (NUMBER): {comparison_value}")

        elif condition.value_type == 'PRICE':
            comparison_value = resampled_data['close'].iloc[-1]
            print(f"Comparison Value (PRICE): {comparison_value}")

        elif condition.value_type == 'INDICATOR_LINE':
            # Fetch the comparison indicator definition
            try:
                value_indicator_def = Indicator.objects.get(name=condition.value_indicator)
            except Indicator.DoesNotExist:
                print(f"Indicator '{condition.value_indicator}' does not exist for condition {condition.id}")
                all_conditions_met = False
                break

            # Resample data according to value_timeframe
            try:
                resampled_data_comp = resample_data(data, condition.value_timeframe)
            except ValueError as e:
                print(f"Error resampling data for comparison value: {e}")
                all_conditions_met = False
                break

            # Prepare parameters for comparison indicator calculation
            parameters_comp = condition.value_indicator_parameters or {}

            # Calculate the comparison indicator value
            try:
                comparison_indicator_series = calculate_indicator(
                    indicator_name=value_indicator_def.name,
                    df=resampled_data_comp,
                    line=condition.value_indicator_line,
                    parameters=parameters_comp
                )
                comparison_value = comparison_indicator_series.iloc[-1]
                print(f"Comparison Indicator ({value_indicator_def.display_name}): {comparison_value}")
            except Exception as e:
                print(f"Error calculating comparison indicator {value_indicator_def.display_name}: {e}")
                all_conditions_met = False
                break

        else:
            print(f"Unknown value type '{condition.value_type}' in condition {condition.id}")
            all_conditions_met = False
            break

        # Check the condition
        condition_met = False
        if condition.condition_operator == 'GT':
            condition_met = indicator_value > comparison_value
        elif condition.condition_operator == 'LT':
            condition_met = indicator_value < comparison_value
        elif condition.condition_operator == 'EQ':
            condition_met = indicator_value == comparison_value
        else:
            print(f"Unknown condition operator '{condition.condition_operator}' in condition {condition.id}")
            all_conditions_met = False
            break

        if not condition_met:
            all_conditions_met = False
            print(f"Condition not met for {indicator_def.display_name} at position {condition.position_in_chain}")
            break
        else:
            print(f"Condition met for {indicator_def.display_name} at position {condition.position_in_chain}")

    if all_conditions_met:
        print(f"All conditions met for alert {alert.id}")
        send_alert_notification(alert, "Indicator chain conditions met")
        alert.is_active = False  # Deactivate the alert after triggering
        alert.save()
