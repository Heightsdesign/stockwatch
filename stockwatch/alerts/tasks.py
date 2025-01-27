# alerts/tasks.py
import re
from celery import shared_task
from django.utils import timezone
from .utils import get_stock_data, calculate_indicator
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from datetime import datetime

import pandas as pd
import math

from .models import Alert, IndicatorChainAlert, IndicatorCondition, Indicator
from .notifications import send_sms_notification, send_push_notification

import re
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime

def send_alert_notification(alert, current_value):
    user = alert.user
    stock = alert.stock

    # ============ (A) Build Email HTML Content ============ #
    email_context = {
        "user": user,
        "stock": stock,
        "year": datetime.now().year,
    }

    # Decide the email subject & fill the email_context accordingly
    if alert.alert_type == "PRICE":
        email_context["alert_type"] = "PRICE"
        email_context["current_value"] = current_value
        subject = f"Stock Alert Triggered for {stock.symbol}"
    elif alert.alert_type == "PERCENT_CHANGE":
        percentage_change_alert = alert.percentage_change_alert
        email_context["alert_type"] = "PERCENT_CHANGE"
        email_context["percentage_change"] = percentage_change_alert.percentage_change
        email_context["direction"] = "Up" if percentage_change_alert.direction == "UP" else "Down"
        email_context["lookback_period"] = percentage_change_alert.lookback_period
        email_context["current_value"] = current_value
        subject = f"Stock Alert: Percentage Change for {stock.symbol}"
    elif alert.alert_type == "INDICATOR_CHAIN":
        conditions = alert.indicator_chain.conditions.all()
        condition_results = []
        for condition in conditions:
            result = {
                "indicator": condition.indicator.name,
                "line": condition.indicator_line,
                "timeframe": condition.indicator_timeframe,
                "operator": condition.condition_operator,
                "value_type": condition.value_type,
            }
            if condition.value_type == "NUMBER":
                result["value"] = condition.value_number
            elif condition.value_type == "INDICATOR_LINE":
                result["value"] = {
                    "indicator": condition.value_indicator.name,
                    "line": condition.value_indicator_line,
                    "timeframe": condition.value_timeframe,
                }
            condition_results.append(result)
        email_context["alert_type"] = "INDICATOR_CHAIN"
        email_context["conditions"] = condition_results
        subject = f"Stock Alert: Indicator Chain Triggered for {stock.symbol}"
    else:
        email_context["alert_type"] = "DEFAULT"
        email_context["current_value"] = current_value
        subject = f"Stock Alert Triggered for {stock.symbol}"

    # Render the HTML email
    html_content = render_to_string("emails/alert_notification.html", email_context)

    # ============ (B) Build a Dedicated SMS Text ============ #
    sms_content = build_sms_content(alert, current_value)

    # ============ (C) Send Email (Multi-part) ============ #
    if user.receive_email_notifications and user.email:
        # Plain-text fallback for email
        #   (We remove <style> blocks if any, then strip tags)
        style_removed = re.sub(r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL)
        text_fallback = strip_tags(style_removed)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_fallback,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        try:
            email.send()
            print(f"Email sent to {user.email}.")
        except Exception as e:
            print(f"Error sending email to {user.email}: {e}")

    # ============ (D) Send SMS ============ #
    if user.receive_sms_notifications and user.phone_number:
        try:
            send_sms_notification(user, sms_content)
            print(f"SMS sent to {user.phone_number}.")
        except Exception as e:
            print(f"Error sending SMS to {user.phone_number}: {e}")

    # ============ (E) Push Notification ============ #
    if getattr(user, "receive_push_notifications", False):
        title = f"Alert Triggered for {stock.symbol}"
        # Could reuse sms_content or build something slightly different
        push_body = sms_content
        try:
            send_push_notification(user, title, push_body)
            print(f"Push notification sent to {user.username}.")
        except Exception as e:
            print(f"Error sending push notification to {user.username}: {e}")


def build_sms_content(alert, current_value):
    """
    Returns a short, plain-text message ideal for SMS (or push).
    """
    stock = alert.stock

    if alert.alert_type == "PRICE":
        return (
            f"Stock Alert for {stock.symbol}\n"
            f"PRICE alert triggered.\n"
            f"Current Value: {current_value}"
        )
    elif alert.alert_type == "PERCENT_CHANGE":
        pct = alert.percentage_change_alert.percentage_change
        direction = "Up" if alert.percentage_change_alert.direction == "UP" else "Down"
        lookback = alert.percentage_change_alert.lookback_period
        return (
            f"Stock Alert for {stock.symbol}\n"
            f"{pct}% {direction} over {lookback}.\n"
            f"Current Value: {current_value}"
        )
    elif alert.alert_type == "INDICATOR_CHAIN":
        return (
            f"Stock Alert for {stock.symbol}\n"
            f"Indicator chain conditions met.\n"
            f"Check your email for details."
        )
    else:
        return (
            f"Stock Alert for {stock.symbol}\n"
            f"Default fallback.\n"
            f"Current Value: {current_value}"
        )

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
        # No data fetched here. Let process_indicator_chain handle it.
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
        '1D': '1d', '1W': '1wk', '1M': '1mo', '3M': '3mo'
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


def get_valid_period(required_days):
    """
    Maps the required number of days to the closest valid yfinance period that meets or exceeds the required days.

    Args:
        required_days (int): The number of days required for the indicator calculation.

    Returns:
        str: A valid yfinance period string.
    """
    # Define valid yfinance periods with their approximate day equivalents
    period_days = [
        ('1d', 1),
        ('5d', 5),
        ('1mo', 30),
        ('3mo', 90),
        ('6mo', 180),
        ('1y', 365),
        ('2y', 730),
        ('5y', 1825),
        ('10y', 3650),
        ('ytd', None),  # Special case: Year-to-date
        ('max', None)    # Special case: Maximum available data
    ]

    for period, days in period_days:
        if days and days >= required_days:
            return period
    # If required_days exceed the largest defined period, return 'max'
    return 'max'


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

    # Define data points per day for each timeframe
    data_points_per_day = {
        '1MIN': 390,   # Assuming 6.5 trading hours
        '5MIN': 78,
        '15MIN': 26,
        '30MIN': 13,
        '1H': 6,
        '4H': 1,
        '1D': 1
    }

    # Determine maximum required length per timeframe
    max_length_per_timeframe = {}
    for condition in conditions:
        timeframe = condition.indicator_timeframe
        length = condition.indicator_parameters.get('length', 14)
        if timeframe in max_length_per_timeframe:
            if length > max_length_per_timeframe[timeframe]:
                max_length_per_timeframe[timeframe] = length
        else:
            max_length_per_timeframe[timeframe] = length

    # Calculate required number of days per timeframe using the helper function
    required_data = {}
    for timeframe, max_length in max_length_per_timeframe.items():
        points_per_day = data_points_per_day.get(timeframe, 390)  # Default to '1MIN' data points
        required_days = math.ceil(max_length / points_per_day)
        # Add a buffer of 10% to ensure data sufficiency
        buffer_days = max(1, math.ceil(required_days * 0.1))
        total_days = required_days + buffer_days
        # Use the helper function to get a valid period
        valid_period = get_valid_period(total_days)
        required_data[timeframe] = valid_period

    # Fetch data per timeframe and cache it
    data_cache = {}
    for timeframe, period in required_data.items():
        interval = {
            '1MIN': '1m',
            '5MIN': '5m',
            '15MIN': '15m',
            '30MIN': '30m',
            '1H': '60m',
            '4H': '240m',
            '1D': '1d'
        }.get(timeframe, '1d')  # Default to '1d' if timeframe not found

        try:
            main_data = get_stock_data(alert.stock.symbol, period=period, interval=interval)
            if main_data.empty:
                print(f"[DEBUG] No main data returned for {alert.stock.symbol} with timeframe {timeframe}. Condition cannot be met.")
                all_conditions_met = False
                break
            print(f"[DEBUG] Main data fetched for {alert.stock.symbol} with timeframe {timeframe}, period: {period}, tail:")
            print(main_data.tail())
            data_cache[timeframe] = main_data
        except Exception as e:
            print(f"[DEBUG] Error fetching main data for {alert.stock.symbol} with timeframe {timeframe}: {e}")
            all_conditions_met = False
            break

    if not data_cache:
        print(f"[DEBUG] No data fetched for any timeframe. Cannot process alert {alert.id}.")
        return

    # Process each condition using the cached data
    for condition in conditions:
        print(f"[DEBUG] Evaluating condition ID: {condition.id}, Position: {condition.position_in_chain}")
        print(f"[DEBUG] Main indicator: {condition.indicator.display_name} (name: {condition.indicator.name})")
        print(f"[DEBUG] Main indicator line: {condition.indicator_line}, Timeframe: {condition.indicator_timeframe}")
        print(f"[DEBUG] Main indicator parameters: {condition.indicator_parameters or {}}")

        # Retrieve pre-fetched main_data for the condition's timeframe
        timeframe = condition.indicator_timeframe
        main_data = data_cache.get(timeframe)

        if main_data is None:
            print(f"[DEBUG] No data available for timeframe {timeframe}. Condition cannot be met.")
            all_conditions_met = False
            break

        parameters = condition.indicator_parameters or {}

        # Calculate the main indicator value (now returning a float directly)
        try:
            indicator_value = calculate_indicator(
                indicator_name=condition.indicator.name,
                df=main_data,
                line=condition.indicator_line,
                parameters=parameters
            )
            if indicator_value is None:
                print("[DEBUG] calculate_indicator returned None for the main indicator. Condition cannot be met.")
                all_conditions_met = False
                break
            print(f"[DEBUG] Main indicator value: {indicator_value}")
        except Exception as e:
            print(f"[DEBUG] Error calculating main indicator '{condition.indicator.display_name}': {e}")
            all_conditions_met = False
            break

        # Determine the comparison value based on condition's value_type
        if condition.value_type == 'NUMBER':
            comparison_value = condition.value_number
            print(f"[DEBUG] Comparison type: NUMBER, value: {comparison_value}")

        elif condition.value_type == 'PRICE':
            # Last close value from main_data
            try:
                comparison_value = float(main_data['close'].iloc[-1])
                print(f"[DEBUG] Comparison type: PRICE, last close: {comparison_value}")
            except (IndexError, ValueError) as e:
                print(f"[DEBUG] Error retrieving last close price: {e}")
                all_conditions_met = False
                break

        elif condition.value_type == 'INDICATOR_LINE':
            if not condition.value_indicator:
                print(f"[DEBUG] value_indicator is required but not set for condition {condition.id}")
                all_conditions_met = False
                break

            print(f"[DEBUG] Value indicator: {condition.value_indicator.display_name} (name: {condition.value_indicator.name})")
            print(f"[DEBUG] Value indicator line: {condition.value_indicator_line}, Timeframe: {condition.value_timeframe}")
            print(f"[DEBUG] Value indicator parameters: {condition.value_indicator_parameters or {}}")

            # Retrieve pre-fetched value_data for the condition's value_timeframe
            value_timeframe = condition.value_timeframe
            value_data = data_cache.get(value_timeframe)

            if value_data is None:
                # Determine the required length for the value_indicator
                value_length = condition.value_indicator_parameters.get('length', 14)
                points_per_day_val = data_points_per_day.get(value_timeframe, 390)
                required_days_val = math.ceil(value_length / points_per_day_val)
                buffer_days_val = max(1, math.ceil(required_days_val * 0.1))
                total_days_val = required_days_val + buffer_days_val
                # Use the helper function to get a valid period
                valid_period_val = get_valid_period(total_days_val)

                interval_val = {
                    '1MIN': '1m',
                    '5MIN': '5m',
                    '15MIN': '15m',
                    '30MIN': '30m',
                    '1H': '60m',
                    '4H': '240m',
                    '1D': '1d'
                }.get(value_timeframe, '1d')  # Default to '1d' if timeframe not found

                try:
                    value_data = get_stock_data(alert.stock.symbol, period=valid_period_val, interval=interval_val)
                    if value_data.empty:
                        print(f"[DEBUG] No value data returned for {alert.stock.symbol} with timeframe {value_timeframe}. Condition cannot be met.")
                        all_conditions_met = False
                        break
                    print(f"[DEBUG] Value indicator data fetched for {alert.stock.symbol} with timeframe {value_timeframe}, period: {valid_period_val}, tail:")
                    print(value_data.tail())
                    data_cache[value_timeframe] = value_data  # Cache the fetched value_data
                except Exception as e:
                    print(f"[DEBUG] Error fetching value indicator data for {alert.stock.symbol} with timeframe {value_timeframe}: {e}")
                    all_conditions_met = False
                    break

            # Calculate the comparison indicator value (also returning a float now)
            try:
                comparison_value = calculate_indicator(
                    indicator_name=condition.value_indicator.name,
                    df=value_data,
                    line=condition.value_indicator_line,
                    parameters=condition.value_indicator_parameters or {}
                )
                if comparison_value is None:
                    print("[DEBUG] calculate_indicator returned None for the comparison indicator. Condition cannot be met.")
                    all_conditions_met = False
                    break
                print(f"[DEBUG] Comparison indicator value: {comparison_value}")
            except Exception as e:
                print(f"[DEBUG] Error calculating comparison indicator '{condition.value_indicator.display_name}': {e}")
                all_conditions_met = False
                break
        else:
            print(f"[DEBUG] Unknown value_type '{condition.value_type}' for condition {condition.id}")
            all_conditions_met = False
            break

        # Evaluate the condition based on the operator
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
