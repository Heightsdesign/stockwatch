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

    for alert in active_alerts:
        print(f'Alert {alert.id} for {alert.stock.symbol} is active.')

        # Determine check_interval
        if alert.alert_type == 'PRICE':
            check_interval = alert.price_target_alert.check_interval
        elif alert.alert_type == 'PERCENT_CHANGE':
            check_interval = alert.percentage_change.check_interval
        elif alert.alert_type == 'INDICATOR_CHAIN':
            check_interval = alert.indicator_chain.check_interval
        else:
            check_interval = 1

        last_checked = alert.last_triggered_at or alert.created_at
        if (now - last_checked).total_seconds() >= check_interval * 60:
            print(f"[DEBUG] It's time to process alert {alert.id} (type: {alert.alert_type})")
            process_single_alert(alert)  # Removed data from here
            alert.last_triggered_at = now
            alert.save()
        else:
            print(
                f"[DEBUG] Not time yet to process alert {alert.id}. Last checked: {last_checked}, interval: {check_interval} minutes.")


def process_single_alert(alert):
    print(f"[DEBUG] process_single_alert called for Alert {alert.id}, type: {alert.alert_type}")
    if alert.alert_type == 'PRICE':
        # Fetch data with the correct timeframe for PRICE alerts
        data = get_stock_data(alert.stock.symbol, period='1d', interval='1m')  # Example
        process_price_target_alert(alert, data)
    elif alert.alert_type == 'PERCENT_CHANGE':
        # Fetch data for percentage change alerts
        data = get_stock_data(alert.stock.symbol, ...) # timeframe based on alert config
        process_percentage_change_alert(alert, data)
    elif alert.alert_type == 'INDICATOR_CHAIN':
        # No data fetched here. Let process_indicator_chain_alert handle it.
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
        '1MIN': '1min',
        '5MIN': '5min',
        '15MIN': '15min',
        '30MIN': '30min',
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
    print(f"[DEBUG] process_indicator_chain_alert called for Alert {alert.id}, Symbol: {alert.stock.symbol}")

    try:
        indicator_chain_alert = alert.indicator_chain
    except ObjectDoesNotExist:
        print(f"[DEBUG] No IndicatorChainAlert associated with alert {alert.id}")
        return

    conditions = indicator_chain_alert.conditions.all().order_by('position_in_chain')
    print(f"[DEBUG] Indicator chain has {conditions.count()} conditions for Alert {alert.id}.")

    all_conditions_met = True

    for condition in conditions:
        print(f"[DEBUG] Evaluating condition ID: {condition.id}, Position: {condition.position_in_chain}")
        print(f"[DEBUG] Main indicator: {condition.indicator.display_name} (name: {condition.indicator.name})")
        print(f"[DEBUG] Main indicator line: {condition.indicator_line}, Timeframe: {condition.indicator_timeframe}")
        print(f"[DEBUG] Main indicator parameters: {condition.indicator_parameters or {}}")

        # Fetch main indicator data according to the condition's indicator_timeframe
        try:
            # Example: If condition.indicator_timeframe is '1MIN', we use period='1d', interval='1m'
            # Adjust logic based on your timeframe map
            interval_map = {
                '1MIN': ('1d', '1m'),
                '5MIN': ('1d', '5m'),
                '15MIN': ('1d', '15m'),
                '30MIN': ('1d', '30m'),
                '1H': ('5d', '60m'),
                '4H': ('1mo', '240m'),
                '1D': ('1mo', '1d')
            }
            period, interval = interval_map.get(condition.indicator_timeframe, ('1mo', '1d'))
            main_data = get_stock_data(alert.stock.symbol, period=period, interval=interval)
            if main_data.empty:
                print(f"[DEBUG] No main data returned for {alert.stock.symbol} with timeframe {condition.indicator_timeframe}. Condition cannot be met.")
                all_conditions_met = False
                break
            print(f"[DEBUG] Main data fetched for {alert.stock.symbol}, head:")
            print(main_data.head())
        except Exception as e:
            print(f"[DEBUG] Error fetching main data for {alert.stock.symbol}: {e}")
            all_conditions_met = False
            break

        parameters = condition.indicator_parameters or {}

        # Calculate the main indicator value
        try:
            indicator_value_series = calculate_indicator(
                indicator_name=condition.indicator.name,
                df=main_data,
                line=condition.indicator_line,
                parameters=parameters
            )
            indicator_value = indicator_value_series.iloc[-1]
            print(f"[DEBUG] Main indicator value: {indicator_value}")
        except Exception as e:
            print(f"[DEBUG] Error calculating main indicator '{condition.indicator.display_name}': {e}")
            all_conditions_met = False
            break

        # Determine the comparison value
        if condition.value_type == 'NUMBER':
            comparison_value = condition.value_number
            print(f"[DEBUG] Comparison type: NUMBER, value: {comparison_value}")

        elif condition.value_type == 'PRICE':
            comparison_value = main_data['close'].iloc[-1]
            print(f"[DEBUG] Comparison type: PRICE, last close: {comparison_value}")

        elif condition.value_type == 'INDICATOR_LINE':
            if not condition.value_indicator:
                print(f"[DEBUG] value_indicator is required but not set for condition {condition.id}")
                all_conditions_met = False
                break

            print(f"[DEBUG] Value indicator: {condition.value_indicator.display_name} (name: {condition.value_indicator.name})")
            print(f"[DEBUG] Value indicator line: {condition.value_indicator_line}, Timeframe: {condition.value_timeframe}")
            print(f"[DEBUG] Value indicator parameters: {condition.value_indicator_parameters or {}}")

            # Fetch value indicator data
            try:
                period_val, interval_val = interval_map.get(condition.value_timeframe, ('1mo', '1d'))
                value_data = get_stock_data(alert.stock.symbol, period=period_val, interval=interval_val)
                if value_data.empty:
                    print(f"[DEBUG] No value data returned for {alert.stock.symbol} with timeframe {condition.value_timeframe}. Condition cannot be met.")
                    all_conditions_met = False
                    break
                print("[DEBUG] Value indicator data head:")
                print(value_data.head())
            except Exception as e:
                print(f"[DEBUG] Error fetching value indicator data for {alert.stock.symbol}: {e}")
                all_conditions_met = False
                break

            parameters_comp = condition.value_indicator_parameters or {}

            # Calculate the comparison indicator value
            try:
                comparison_indicator_series = calculate_indicator(
                    indicator_name=condition.value_indicator.name,
                    df=value_data,
                    line=condition.value_indicator_line,
                    parameters=parameters_comp
                )
                comparison_value = comparison_indicator_series.iloc[-1]
                print(f"[DEBUG] Comparison indicator value: {comparison_value}")
            except Exception as e:
                print(f"[DEBUG] Error calculating comparison indicator '{condition.value_indicator.display_name}': {e}")
                all_conditions_met = False
                break
        else:
            print(f"[DEBUG] Unknown value_type '{condition.value_type}' for condition {condition.id}")
            all_conditions_met = False
            break

        # Evaluate the condition
        print(f"[DEBUG] Evaluating condition operator: {condition.condition_operator}")
        print(f"[DEBUG] Indicator value: {indicator_value}, Comparison value: {comparison_value}")

        if condition.condition_operator == 'GT':
            condition_met = indicator_value > comparison_value
        elif condition.condition_operator == 'LT':
            condition_met = indicator_value < comparison_value
        elif condition.condition_operator == 'EQ':
            condition_met = indicator_value == comparison_value
        else:
            print(f"[DEBUG] Unknown condition operator '{condition.condition_operator}' in condition {condition.id}")
            all_conditions_met = False
            break

        print(f"[DEBUG] Condition met: {condition_met}")
        if not condition_met:
            all_conditions_met = False
            break

    if all_conditions_met:
        print(f"[DEBUG] All conditions met for alert {alert.id}, triggering notification.")
        send_alert_notification(alert, "Indicator chain conditions met")
        alert.is_active = False  # Deactivate the alert after triggering
        alert.save()
    else:
        print(f"[DEBUG] Not all conditions were met for alert {alert.id}. No notification triggered.")

