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


def calculate_indicator(indicator_name: str, df: pd.DataFrame, line: str = None, **kwargs):
    """
    Calculate the specified indicator using pandas_ta.

    Args:
        indicator_name (str): Name of the indicator to calculate.
        df (pd.DataFrame): DataFrame with stock data.
        line (str): Specific line of the indicator to return, if applicable.
        **kwargs: Additional parameters for the indicator.

    Returns:
        pd.Series: Calculated indicator values.
    """
    indicator_name = indicator_name.upper()
    line = line.upper() if line else None

    if indicator_name == "MOVING AVERAGE":
        # Simple Moving Average (SMA)
        result = ta.sma(df['close'], **kwargs)
        if line == "MA":
            return result
        elif line == "SIGNAL LINE":
            # Assuming Signal Line is another moving average with different parameters
            kwargs_signal = kwargs.copy()
            kwargs_signal['length'] = kwargs.get('signal_length', 9)
            return ta.sma(df['close'], **kwargs_signal)
        else:
            raise ValueError(f"Unknown line '{line}' for Moving Average.")

    elif indicator_name == "EXPONENTIAL MOVING AVERAGE":
        result = ta.ema(df['close'], **kwargs)
        if line == "EMA":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Exponential Moving Average.")

    elif indicator_name == "BOLLINGER BANDS":
        result = ta.bbands(df['close'], **kwargs)
        if line == "UPPER BAND":
            return result['BBU_20_2.0']
        elif line == "MIDDLE BAND":
            return result['BBM_20_2.0']
        elif line == "LOWER BAND":
            return result['BBL_20_2.0']
        else:
            raise ValueError(f"Unknown line '{line}' for Bollinger Bands.")

    elif indicator_name == "MACD":
        result = ta.macd(df['close'], **kwargs)
        if line == "MACD LINE":
            return result['MACD_12_26_9']
        elif line == "SIGNAL LINE":
            return result['MACDs_12_26_9']
        elif line == "HISTOGRAM":
            return result['MACDh_12_26_9']
        else:
            raise ValueError(f"Unknown line '{line}' for MACD.")

    elif indicator_name == "RSI":
        result = ta.rsi(df['close'], **kwargs)
        if line == "RSI":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for RSI.")

    elif indicator_name == "STOCHASTIC OSCILLATOR":
        result = ta.stoch(df['high'], df['low'], df['close'], **kwargs)
        if line == "%K":
            return result['STOCHk_14_3_3']
        elif line == "%D":
            return result['STOCHd_14_3_3']
        else:
            raise ValueError(f"Unknown line '{line}' for Stochastic Oscillator.")

    elif indicator_name == "ICHIMOKU CLOUD":
        result = ta.ichimoku(df['high'], df['low'], **kwargs)
        tenkan_sen = result[0]
        kijun_sen = result[1]
        senkou_span_a = result[2]
        senkou_span_b = result[3]
        chikou_span = df['close'].shift(-26)  # Typically, Chikou Span is the close shifted backward

        if line == "TENKAN-SEN":
            return tenkan_sen
        elif line == "KIJUN-SEN":
            return kijun_sen
        elif line == "SENKOU SPAN A":
            return senkou_span_a
        elif line == "SENKOU SPAN B":
            return senkou_span_b
        elif line == "CHIKOU SPAN":
            return chikou_span
        else:
            raise ValueError(f"Unknown line '{line}' for Ichimoku Cloud.")

    elif indicator_name == "AVERAGE TRUE RANGE":
        result = ta.atr(df['high'], df['low'], df['close'], **kwargs)
        if line == "ATR":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Average True Range.")

    elif indicator_name == "ON-BALANCE VOLUME":
        result = ta.obv(df['close'], df['volume'], **kwargs)
        if line == "OBV":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for On-Balance Volume.")

    elif indicator_name == "PARABOLIC SAR":
        result = ta.psar(df['high'], df['low'], df['close'], **kwargs)
        if line == "SAR":
            return result['PSARl_0.02_0.2']
        else:
            raise ValueError(f"Unknown line '{line}' for Parabolic SAR.")

    elif indicator_name == "VOLUME WEIGHTED AVERAGE PRICE":
        result = ta.vwap(df['high'], df['low'], df['close'], df['volume'], **kwargs)
        if line == "VWAP":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for VWAP.")

    elif indicator_name == "FIBONACCI RETRACEMENT":
        # Fibonacci Retracement is not directly calculated; it's based on static levels between a high and low.
        # Custom implementation required.
        raise NotImplementedError("Fibonacci Retracement requires custom implementation.")

    elif indicator_name == "PIVOT POINTS":
        result = ta.pivot_points(df['high'], df['low'], df['close'], **kwargs)
        if line == "PIVOT":
            return result['P']
        elif line == "SUPPORT1":
            return result['S1']
        elif line == "SUPPORT2":
            return result['S2']
        elif line == "RESISTANCE1":
            return result['R1']
        elif line == "RESISTANCE2":
            return result['R2']
        else:
            raise ValueError(f"Unknown line '{line}' for Pivot Points.")

    elif indicator_name == "COMMODITY CHANNEL INDEX":
        result = ta.cci(df['high'], df['low'], df['close'], **kwargs)
        if line == "CCI":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Commodity Channel Index.")

    elif indicator_name == "RATE OF CHANGE":
        result = ta.roc(df['close'], **kwargs)
        if line == "ROC":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Rate of Change.")

    elif indicator_name == "WILLIAMS %R":
        result = ta.willr(df['high'], df['low'], df['close'], **kwargs)
        if line == "%R":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Williams %R.")

    elif indicator_name == "AVERAGE DIRECTIONAL INDEX":
        result = ta.adx(df['high'], df['low'], df['close'], **kwargs)
        if line == "ADX":
            return result['ADX_14']
        elif line == "+DI":
            return result['DMP_14']
        elif line == "-DI":
            return result['DMN_14']
        else:
            raise ValueError(f"Unknown line '{line}' for Average Directional Index.")

    elif indicator_name == "CHAIKIN MONEY FLOW":
        result = ta.cmf(df['high'], df['low'], df['close'], df['volume'], **kwargs)
        if line == "CMF":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Chaikin Money Flow.")

    elif indicator_name == "DONCHIAN CHANNELS":
        result = ta.donchian(df['high'], df['low'], **kwargs)
        if line == "UPPER BAND":
            return result['DCL']
        elif line == "LOWER BAND":
            return result['DCS']
        else:
            raise ValueError(f"Unknown line '{line}' for Donchian Channels.")

    elif indicator_name == "KELTNER CHANNELS":
        result = ta.kc(df['high'], df['low'], df['close'], **kwargs)
        if line == "UPPER BAND":
            return result['KCUp_20_2_20']
        elif line == "MIDDLE BAND":
            return result['KCL_20_2_20']
        elif line == "LOWER BAND":
            return result['KCDn_20_2_20']
        else:
            raise ValueError(f"Unknown line '{line}' for Keltner Channels.")

    elif indicator_name == "ULTIMATE OSCILLATOR":
        result = ta.uo(df['high'], df['low'], df['close'], **kwargs)
        if line == "ULTIMATE OSCILLATOR":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Ultimate Oscillator.")

    elif indicator_name == "MONEY FLOW INDEX":
        result = ta.mfi(df['high'], df['low'], df['close'], df['volume'], **kwargs)
        if line == "MFI":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Money Flow Index.")

    elif indicator_name == "CHAIKIN OSCILLATOR":
        result = ta.adosc(df['high'], df['low'], df['close'], df['volume'], **kwargs)
        if line == "CHAIKIN OSCILLATOR":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Chaikin Oscillator.")

    elif indicator_name == "TRIX":
        result = ta.trix(df['close'], **kwargs)
        if line == "TRIX":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for TRIX.")

    elif indicator_name == "FORCE INDEX":
        result = ta.fi(df['close'], df['volume'], **kwargs)
        if line == "FORCE INDEX":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Force Index.")

    elif indicator_name == "ELDER-RAY INDEX":
        result = ta.eri(df['high'], df['low'], df['close'], **kwargs)
        if line == "BULL POWER":
            return result['BULLP_13']
        elif line == "BEAR POWER":
            return result['BEARP_13']
        else:
            raise ValueError(f"Unknown line '{line}' for Elder-Ray Index.")

    elif indicator_name == "COPPOCK CURVE":
        # Not directly available in pandas_ta; custom implementation required
        raise NotImplementedError("Coppock Curve requires custom implementation.")

    elif indicator_name == "AROON INDICATOR":
        result = ta.aroon(df['high'], df['low'], **kwargs)
        if line == "AROON UP":
            return result['AROONU_25']
        elif line == "AROON DOWN":
            return result['AROOND_25']
        else:
            raise ValueError(f"Unknown line '{line}' for Aroon Indicator.")

    elif indicator_name == "TTM SQUEEZE":
        # Not directly available in pandas_ta; custom implementation required
        raise NotImplementedError("TTM Squeeze requires custom implementation.")

    elif indicator_name == "PERCENTAGE PRICE OSCILLATOR":
        result = ta.ppo(df['close'], **kwargs)
        if line == "PPO LINE":
            return result['PPO_12_26_9']
        elif line == "SIGNAL LINE":
            return result['PPOs_12_26_9']
        elif line == "HISTOGRAM":
            return result['PPOh_12_26_9']
        else:
            raise ValueError(f"Unknown line '{line}' for Percentage Price Oscillator.")

    elif indicator_name == "PERCENTAGE VOLUME OSCILLATOR":
        result = ta.pvo(df['volume'], **kwargs)
        if line == "PVO LINE":
            return result['PVO_12_26_9']
        elif line == "SIGNAL LINE":
            return result['PVOs_12_26_9']
        elif line == "HISTOGRAM":
            return result['PVOh_12_26_9']
        else:
            raise ValueError(f"Unknown line '{line}' for Percentage Volume Oscillator.")

    elif indicator_name == "GATOR OSCILLATOR":
        # Not directly available in pandas_ta; custom implementation required
        raise NotImplementedError("Gator Oscillator requires custom implementation.")

    elif indicator_name == "HULL MOVING AVERAGE":
        result = ta.hma(df['close'], **kwargs)
        if line == "HMA":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Hull Moving Average.")

    elif indicator_name == "DOUBLE EXPONENTIAL MOVING AVERAGE":
        result = ta.dema(df['close'], **kwargs)
        if line == "DEMA":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Double Exponential Moving Average.")

    elif indicator_name == "TRIPLE EXPONENTIAL MOVING AVERAGE":
        result = ta.tema(df['close'], **kwargs)
        if line == "TEMA":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Triple Exponential Moving Average.")

    elif indicator_name == "STOCHASTIC RSI":
        result = ta.stochrsi(df['close'], **kwargs)
        if line == "STOCH RSI":
            return result['STOCHRSIk_14_14_3_3']
        else:
            raise ValueError(f"Unknown line '{line}' for Stochastic RSI.")

    elif indicator_name == "LINEAR REGRESSION":
        result = ta.linreg(df['close'], **kwargs)
        if line == "LINEAR REGRESSION LINE":
            return result
        else:
            raise ValueError(f"Unknown line '{line}' for Linear Regression.")

    else:
        raise ValueError(f"Indicator '{indicator_name}' is not supported.")

    # If we reach this point without returning, raise an error
    raise ValueError(f"Could not calculate indicator '{indicator_name}' with line '{line}'.")


