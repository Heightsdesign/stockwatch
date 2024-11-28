# alerts/utils.py

import pandas as pd
import pandas_ta as ta
from .models import Indicator
import yfinance as yf


def get_stock_data(symbol, period='1mo', interval='1d'):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        data.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_indicator(indicator_name: str, df: pd.DataFrame, line: str = None, parameters: dict = None):
    """
    Calculate the specified indicator using pandas_ta.

    Args:
        indicator_name (str): Name of the indicator to calculate.
        df (pd.DataFrame): DataFrame with stock data.
        line (str): Specific line of the indicator to return, if applicable.
        parameters (dict): Parameters for the indicator.

    Returns:
        pd.Series: Calculated indicator values.
    """
    indicator_name = indicator_name.lower()
    line = line.lower() if line else None
    parameters = parameters or {}

    if indicator_name == "moving_average":
        length = parameters.get('length', 14)
        result = ta.sma(df['close'], length=length)
        if line == "ma":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Moving Average.")

    elif indicator_name == "bollinger_bands":
        length = parameters.get('length', 20)
        stddev = parameters.get('stddev', 2.0)
        result = ta.bbands(df['close'], length=length, std=stddev)
        if line == "upper band":
            return result[f'BBU_{length}_{stddev}']
        elif line == "middle band":
            return result[f'BBM_{length}_{stddev}']
        elif line == "lower band":
            return result[f'BBL_{length}_{stddev}']
        else:
            raise ValueError(f"Unknown line '{line}' for Bollinger Bands.")

    elif indicator_name == "macd":
        fast_period = parameters.get('fast_period', 12)
        slow_period = parameters.get('slow_period', 26)
        signal_period = parameters.get('signal_period', 9)
        result = ta.macd(df['close'], fast=fast_period, slow=slow_period, signal=signal_period)
        if line == "macd line":
            return result[f'MACD_{fast_period}_{slow_period}_{signal_period}']
        elif line == "signal line":
            return result[f'MACDs_{fast_period}_{slow_period}_{signal_period}']
        elif line == "histogram":
            return result[f'MACDh_{fast_period}_{slow_period}_{signal_period}']
        else:
            raise ValueError(f"Unknown line '{line}' for MACD.")

    # Add other indicators...

    else:
        raise ValueError(f"Indicator '{indicator_name}' is not supported.")

