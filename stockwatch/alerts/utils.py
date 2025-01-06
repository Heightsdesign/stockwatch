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
        float: Calculated indicator value.
    """
    indicator_name = indicator_name.lower()
    line = line.lower() if line else None
    parameters = parameters or {}

    if indicator_name == "moving_average":
        length = parameters.get('length', 14)
        if len(df) < length:
            raise ValueError(
                f"Not enough data to calculate a {length}-period SMA. Required: {length}, Available: {len(df)}")

        # Calculate SMA without appending to the DataFrame
        result = df.ta.sma(length=length, append=False)
        print(f"[DEBUG] In calculate_indicator: indicator_name={indicator_name}, line={line}, parameters={parameters}")
        print(f"[DEBUG] Indicator result type: {type(result)}")

        if isinstance(result, pd.Series):
            try:
                sma_value = float(result.iloc[-1])
                print(f"[DEBUG] Extracted SMA value: {sma_value}")
                return sma_value
            except (IndexError, ValueError) as e:
                print(f"[DEBUG] Error extracting SMA value from Series: {e}")
                raise ValueError(f"Error extracting SMA value: {e}")
        elif isinstance(result, pd.DataFrame):
            sma_column = f'SMA_{length}'
            print(f"[DEBUG] Indicator DataFrame columns: {result.columns.tolist()}")
            if sma_column in result.columns:
                try:
                    sma_value = float(result[sma_column].iloc[-1])
                    print(f"[DEBUG] Extracted SMA value from DataFrame: {sma_value}")
                    return sma_value
                except (IndexError, ValueError) as e:
                    print(f"[DEBUG] Error extracting SMA value from DataFrame: {e}")
                    raise ValueError(f"Error extracting SMA value: {e}")
            else:
                raise ValueError(f"SMA column '{sma_column}' not found in result.")
        else:
            raise ValueError(f"Unexpected result type for SMA: {type(result)}")

    elif indicator_name == "bollinger_bands":
        length = int(parameters.get('length', 20))
        stddev = float(parameters.get('stddev', 2.0))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate Bollinger Bands. Required: {length}, Available: {len(df)}")

        # Calculate Bollinger Bands without appending to the DataFrame
        result = df.ta.bbands(length=length, std=stddev, append=False)
        print(f"[DEBUG] In calculate_indicator: indicator_name={indicator_name}, line={line}, parameters={parameters}")
        print(f"[DEBUG] Indicator result type: {type(result)}")

        if isinstance(result, pd.DataFrame):
            print("[DEBUG] calculate_indicator result head:")
            print(result.tail())
            print("Dataframe length : ", len(result))
            if line == "upper_band":
                column = f'BBU_{length}_{stddev}'
            elif line == "middle_band":
                column = f'BBM_{length}_{stddev}'
            elif line == "lower_band":
                column = f'BBL_{length}_{stddev}'
            else:
                raise ValueError(f"Unknown line '{line}' for Bollinger Bands.")

            if column in result.columns:
                try:
                    bb_value = float(result[column].iloc[-1])
                    print(f"[DEBUG] Extracted Bollinger Bands value from column '{column}': {bb_value}")
                    return bb_value
                except (IndexError, ValueError) as e:
                    print(f"[DEBUG] Error extracting Bollinger Bands value: {e}")
                    raise ValueError(f"Error extracting Bollinger Bands value: {e}")
            else:
                raise ValueError(f"Bollinger Bands column '{column}' not found in result.")
        else:
            raise ValueError(f"Unexpected result type for Bollinger Bands: {type(result)}")

    elif indicator_name == "macd":
        fast_period = int(parameters.get('fast_period', 12))
        slow_period = int(parameters.get('slow_period', 26))
        signal_period = int(parameters.get('signal_period', 9))
        required_length = slow_period + signal_period
        if len(df) < required_length:
            raise ValueError(f"Not enough data to calculate MACD. Required: {required_length}, Available: {len(df)}")

        # Calculate MACD without appending to the DataFrame
        result = df.ta.macd(fast=fast_period, slow=slow_period, signal=signal_period, append=False)
        print(f"[DEBUG] In calculate_indicator: indicator_name={indicator_name}, line={line}, parameters={parameters}")
        print(f"[DEBUG] Indicator result type: {type(result)}")

        if isinstance(result, pd.DataFrame):
            print("[DEBUG] calculate_indicator result head:")
            print(result.tail())
            print("Dataframe length : ", len(result))
            if line == "macd_line":
                column = f'MACD_{fast_period}_{slow_period}_{signal_period}'
            elif line == "signal_line":
                column = f'MACDs_{fast_period}_{slow_period}_{signal_period}'
            elif line == "histogram":
                column = f'MACDh_{fast_period}_{slow_period}_{signal_period}'
            else:
                raise ValueError(f"Unknown line '{line}' for MACD.")

            if column in result.columns:
                try:
                    macd_value = float(result[column].iloc[-1])
                    print(f"[DEBUG] Extracted MACD value from column '{column}': {macd_value}")
                    return macd_value
                except (IndexError, ValueError) as e:
                    print(f"[DEBUG] Error extracting MACD value: {e}")
                    raise ValueError(f"Error extracting MACD value: {e}")
            else:
                raise ValueError(f"MACD column '{column}' not found in result.")
        else:
            raise ValueError(f"Unexpected result type for MACD: {type(result)}")

    else:
        raise ValueError(f"Indicator '{indicator_name}' is not supported.")

