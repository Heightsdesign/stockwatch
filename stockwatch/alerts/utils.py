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
        result = df.ta.sma(length=length)
        print(f"[DEBUG] In calculate_indicator: indicator_name={indicator_name}, line={line}, parameters={parameters}")

        if result is None:
            print("[DEBUG] calculate_indicator is about to return None!")
        else:
            print("[DEBUG] calculate_indicator result head:")
            print(result.tail() if hasattr(result, 'head') else result)
            print("Dataframe length : ", len(result))

        if line == "ma":
            return float(result.iloc[-1])
        else:
            raise ValueError(f"Unknown line '{line}' for Moving Average.")

    elif indicator_name == "bollinger_bands":
        length = int(parameters.get('length', 20))
        stddev = float(parameters.get('stddev', 2.0))
        result = df.ta.bbands(length=length, std=stddev)

        print(f"[DEBUG] In calculate_indicator: indicator_name={indicator_name}, line={line}, parameters={parameters}")

        if result is None:
            print("[DEBUG] calculate_indicator is about to return None!")
        else:
            print("[DEBUG] calculate_indicator result head:")
            print(result.tail() if hasattr(result, 'head') else result)
            print("Dataframe length : ", len(result))

        if line == "upper_band":
            return float(result[f'BBU_{length}_{stddev}'].iloc[-1])
        elif line == "middle_band":
            return float(result[f'BBM_{length}_{stddev}'].iloc[-1])
        elif line == "lower_band":
            return float(result[f'BBL_{length}_{stddev}'].iloc[-1])
        else:
            raise ValueError(f"Unknown line '{line}' for Bollinger Bands.")

    elif indicator_name == "macd":
        fast_period = int(parameters.get('fast_period', 12))
        slow_period = int(parameters.get('slow_period', 26))
        signal_period = int(parameters.get('signal_period', 9))
        result = df.ta.macd(fast=fast_period, slow=slow_period, signal=signal_period)

        print(f"[DEBUG] In calculate_indicator: indicator_name={indicator_name}, line={line}, parameters={parameters}")

        if result is None:
            print("[DEBUG] calculate_indicator is about to return None!")
        else:
            print("[DEBUG] calculate_indicator result head:")
            print(result.tail() if hasattr(result, 'head') else result)
            print("Dataframe length : ", len(result))

        if line == "macd_line":
            return float(result[f'MACD_{fast_period}_{slow_period}_{signal_period}'].iloc[-1])
        elif line == "signal_line":
            return float(result[f'MACDs_{fast_period}_{slow_period}_{signal_period}'].iloc[-1])
        elif line == "histogram":
            return float(result[f'MACDh_{fast_period}_{slow_period}_{signal_period}'].iloc[-1])
        else:
            raise ValueError(...)

    # Add other indicators...

    else:
        raise ValueError(f"Indicator '{indicator_name}' is not supported.")

