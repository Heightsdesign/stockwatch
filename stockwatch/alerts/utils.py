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

    # ------------------------------------------------------------------------------------
    # 1) RSI (Relative Strength Index)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "rsi":

        length = int(parameters.get('length', 14))

        if len(df) < length:
            raise ValueError(f"Not enough data to calculate RSI. Required: {length}, Available: {len(df)}")

        # Calculate RSI
        result = df.ta.rsi(length=length, append=False)
        # Typically RSI is a single-column Series or DataFrame
        # If a DataFrame, the column might be "RSI_{length}".
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            rsi_col = f'RSI_{length}'
            if rsi_col in result.columns:
                return float(result[rsi_col].iloc[-1])
            else:
                raise ValueError(f"RSI column '{rsi_col}' not found in DataFrame.")
        else:
            raise ValueError(f"Unexpected RSI result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 2) EMA (Exponential Moving Average)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "ema":
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate EMA({length}). Available: {len(df)}")

        result = df.ta.ema(length=length, append=False)
        # Usually a single-column Series or DataFrame. Column = f"EMA_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            ema_col = f'EMA_{length}'
            if ema_col in result.columns:
                return float(result[ema_col].iloc[-1])
            else:
                raise ValueError(f"EMA column '{ema_col}' not found.")
        else:
            raise ValueError(f"Unexpected result type for EMA: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 3) WMA (Weighted Moving Average)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "wma":
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate WMA({length}). Available: {len(df)}")

        result = df.ta.wma(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            wma_col = f'WMA_{length}'
            if wma_col in result.columns:
                return float(result[wma_col].iloc[-1])
            else:
                raise ValueError(f"WMA column '{wma_col}' not found.")
        else:
            raise ValueError(f"Unexpected result type for WMA: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 4) ADX (Average Directional Index)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "adx":
        length = int(parameters.get('length', 14))
        if len(df) < length * 2:
            raise ValueError(f"Not enough data to calculate ADX({length}). Available: {len(df)}")

        # adx usually returns a DataFrame with columns: ["ADX_{length}", "DMP_{length}", "DMN_{length}"]
        result = df.ta.adx(length=length, append=False)
        # line can be "adx_line", "diplus_line", "diminus_line" (for example)
        # We'll map them:
        if line == "adx_line":
            column = f'ADX_{length}'
        elif line == "diplus_line":
            column = f'DMP_{length}'
        elif line == "diminus_line":
            column = f'DMN_{length}'
        else:
            # Default to ADX line if not specified
            column = f'ADX_{length}'

        if isinstance(result, pd.DataFrame):
            if column in result.columns:
                return float(result[column].iloc[-1])
            else:
                raise ValueError(f"ADX column '{column}' not found in result.")
        else:
            raise ValueError(f"Unexpected result type for ADX: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 5) ATR (Average True Range)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "atr":
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate ATR({length}). Available: {len(df)}")

        result = df.ta.atr(length=length, append=False)
        # Typically a single column: "ATR_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            atr_col = f'ATR_{length}'
            if atr_col in result.columns:
                return float(result[atr_col].iloc[-1])
            else:
                raise ValueError(f"ATR column '{atr_col}' not found.")
        else:
            raise ValueError(f"Unexpected ATR result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 6) CCI (Commodity Channel Index)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "cci":
        length = int(parameters.get('length', 20))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate CCI({length}). Available: {len(df)}")

        result = df.ta.cci(length=length, append=False)
        # Usually returns a single column: "CCI_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            cci_col = f'CCI_{length}'
            if cci_col in result.columns:
                return float(result[cci_col].iloc[-1])
            else:
                raise ValueError(f"CCI column '{cci_col}' not found.")
        else:
            raise ValueError(f"Unexpected result type for CCI: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 7) TSI (True Strength Index)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "tsi":
        fast = int(parameters.get('fast', 13))
        slow = int(parameters.get('slow', 25))
        if len(df) < slow * 2:
            raise ValueError(f"Not enough data to calculate TSI({fast},{slow}). Available: {len(df)}")

        result = df.ta.tsi(fast=fast, slow=slow, append=False)
        # TSI typically returns one column: f"TSI_{fast}_{slow}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            tsi_col = f'TSI_{fast}_{slow}'
            if tsi_col in result.columns:
                return float(result[tsi_col].iloc[-1])
            else:
                raise ValueError(f"TSI column '{tsi_col}' not found.")
        else:
            raise ValueError(f"Unexpected result type for TSI: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 8) STOCH (Stochastic Oscillator)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "stoch":
        k = int(parameters.get('k', 14))  # Period for %K
        d = int(parameters.get('d', 3))  # Smoothing for %D
        smooth_k = int(parameters.get('smooth_k', 3))  # Extra smoothing for %K (if any)
        required_length = k + d
        if len(df) < required_length:
            raise ValueError(f"Not enough data to calculate Stoch. Required: {required_length}, Available: {len(df)}")

        # stoch => DataFrame with columns: ["STOCHk_{k}_{d}_{smooth_k}", "STOCHd_{k}_{d}_{smooth_k}"]
        result = df.ta.stoch(k=k, d=d, smooth_k=smooth_k, append=False)

        if isinstance(result, pd.DataFrame):
            # Decide which line user wants
            if line == "k_line":
                column = f'STOCHk_{k}_{d}_{smooth_k}'
            elif line == "d_line":
                column = f'STOCHd_{k}_{d}_{smooth_k}'
            else:
                # Default to %K if not specified
                column = f'STOCHk_{k}_{d}_{smooth_k}'

            if column in result.columns:
                return float(result[column].iloc[-1])
            else:
                raise ValueError(f"Stochastic column '{column}' not found.")
        else:
            raise ValueError(f"Unexpected Stochastic result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 9) OBV (On Balance Volume)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "obv":
        # OBV typically requires volume
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for OBV but not found in DataFrame.")

        result = df.ta.obv(append=False)
        # OBV typically returns a single column: "OBV"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            if "OBV" in result.columns:
                return float(result["OBV"].iloc[-1])
            else:
                raise ValueError("OBV column not found in DataFrame.")
        else:
            raise ValueError(f"Unexpected OBV result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 10) MFI (Money Flow Index)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "mfi":
        length = int(parameters.get('length', 14))
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for MFI but not found in DataFrame.")
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate MFI({length}). Available: {len(df)}")

        # Returns a Series or DataFrame with the column "MFI_{length}"
        result = df.ta.mfi(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            mfi_col = f'MFI_{length}'
            if mfi_col in result.columns:
                return float(result[mfi_col].iloc[-1])
            else:
                raise ValueError(f"MFI column '{mfi_col}' not found.")
        else:
            raise ValueError(f"Unexpected MFI result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 11) AO (Awesome Oscillator)
    # ------------------------------------------------------------------------------------
    if indicator_name == "ao":
        # AO doesn't usually require parameters, but you can pass in "fast" and "slow" if desired
        # In newer pandas_ta, df.ta.ao() returns a Series or DataFrame with "AO_{fast}_{slow}"
        fast = int(parameters.get('fast', 5))
        slow = int(parameters.get('slow', 34))
        required_length = slow
        if len(df) < required_length:
            raise ValueError(
                f"Not enough data to calculate AO({fast},{slow}). Required: {required_length}, Got: {len(df)}")

        result = df.ta.ao(fast=fast, slow=slow, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            ao_col = f"AO_{fast}_{slow}"
            if ao_col in result.columns:
                return float(result[ao_col].iloc[-1])
            else:
                raise ValueError(f"AO column '{ao_col}' not found.")
        else:
            raise ValueError(f"Unexpected AO result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 12) ROC (Rate of Change)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "roc":
        length = int(parameters.get('length', 10))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate ROC({length}). Available: {len(df)}")

        result = df.ta.roc(length=length, append=False)
        # Typically single column: "ROC_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            roc_col = f"ROC_{length}"
            if roc_col in result.columns:
                return float(result[roc_col].iloc[-1])
            else:
                raise ValueError(f"ROC column '{roc_col}' not found.")
        else:
            raise ValueError(f"Unexpected ROC result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 13) CMO (Chande Momentum Oscillator)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "cmo":
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate CMO({length}). Available: {len(df)}")

        result = df.ta.cmo(length=length, append=False)
        # Usually single col: "CMO_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            cmo_col = f"CMO_{length}"
            if cmo_col in result.columns:
                return float(result[cmo_col].iloc[-1])
            else:
                raise ValueError(f"CMO column '{cmo_col}' not found.")
        else:
            raise ValueError(f"Unexpected CMO result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 14) KAMA (Kaufman Adaptive Moving Average)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "kama":
        length = int(parameters.get('length', 10))
        # KAMA might also have 'fast' and 'slow' settings in some pandas_ta versions
        fast = int(parameters.get('fast', 2))
        slow = int(parameters.get('slow', 30))
        required_length = max(length, slow)
        if len(df) < required_length:
            raise ValueError(f"Not enough data to calculate KAMA. Need {required_length}, have {len(df)}")

        # Some versions of pandas_ta might let you do: df.ta.kama(length=..., fast=..., slow=..., append=False)
        result = df.ta.kama(length=length, fast=fast, slow=slow, append=False)
        # Single col: "KAMA_{length}_{fast}_{slow}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            kama_col = f"KAMA_{length}_{fast}_{slow}"
            if kama_col in result.columns:
                return float(result[kama_col].iloc[-1])
            else:
                raise ValueError(f"KAMA column '{kama_col}' not found.")
        else:
            raise ValueError(f"Unexpected KAMA result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 15) PSAR (Parabolic SAR)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "psar":
        # Typically has "step" (acceleration) and "max_step" (max acceleration)
        step = float(parameters.get('step', 0.02))
        max_step = float(parameters.get('max_step', 0.2))
        result = df.ta.psar(step=step, max_step=max_step, append=False)

        # Usually returns a DataFrame with columns: "PSARl_{step}_{max_step}" and "PSARs_{step}_{max_step}"
        # plus "PSAR_{step}_{max_step}" which might be the actual PSAR points
        if isinstance(result, pd.DataFrame):
            # If user wants the actual PSAR line or the "long" or "short" columns, handle that here:
            # e.g. line == "psar", line == "psarl", line == "psars"
            if not line:
                # default to "PSAR_{step}_{max_step}"
                line = "psar"
            if line == "psar":
                column = f"PSAR_{step}_{max_step}"
            elif line == "psarl":
                column = f"PSARl_{step}_{max_step}"
            elif line == "psars":
                column = f"PSARs_{step}_{max_step}"
            else:
                raise ValueError(f"Unknown line '{line}' for PSAR. Expected 'psar', 'psarl', or 'psars'.")

            if column in result.columns:
                return float(result[column].iloc[-1])
            else:
                raise ValueError(f"PSAR column '{column}' not found in result.")
        else:
            raise ValueError(f"Unexpected PSAR result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 16) SuperTrend
    # ------------------------------------------------------------------------------------
    elif indicator_name == "supertrend":
        # Typical parameters: "length" (10), "multiplier" (3.0)
        length = int(parameters.get('length', 10))
        multiplier = float(parameters.get('multiplier', 3.0))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate SuperTrend({length}). Have {len(df)}")

        result = df.ta.supertrend(length=length, multiplier=multiplier, append=False)
        # Typically yields columns: "SUPERT_{length}_{multiplier}", "SUPERTd_{length}_{multiplier}"
        # and "SUPERTl_{length}_{multiplier}"
        if isinstance(result, pd.DataFrame):
            # If the user wants the main line or the direction, we can parse "line"
            # e.g. line=="trend" => "SUPERT_{length}_{multiplier}"
            #     line=="direction" => "SUPERTd_{length}_{multiplier}"
            #     line=="lower" => "SUPERTl_{length}_{multiplier}"
            # or similar
            if not line:
                # default to main line
                column = f"SUPERT_{length}_{multiplier}"
            elif line == "direction":
                column = f"SUPERTd_{length}_{multiplier}"
            elif line == "lower":
                column = f"SUPERTl_{length}_{multiplier}"
            else:
                column = f"SUPERT_{length}_{multiplier}"  # fallback

            if column in result.columns:
                return float(result[column].iloc[-1])
            else:
                raise ValueError(f"SuperTrend column '{column}' not found in result.")
        else:
            raise ValueError(f"Unexpected SuperTrend result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 17) UO (Ultimate Oscillator)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "uo":
        # UO typically has 3 periods: s(7), m(14), l(28) (short, medium, long)
        s = int(parameters.get('s', 7))
        m = int(parameters.get('m', 14))
        l = int(parameters.get('l', 28))
        if len(df) < l:
            raise ValueError(f"Not enough data for Ultimate Oscillator (UO). Need {l}, have {len(df)}")

        result = df.ta.uo(s=s, m=m, l=l, append=False)
        # Usually single col: f"UO_{s}_{m}_{l}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            uo_col = f"UO_{s}_{m}_{l}"
            if uo_col in result.columns:
                return float(result[uo_col].iloc[-1])
            else:
                raise ValueError(f"UO column '{uo_col}' not found.")
        else:
            raise ValueError(f"Unexpected UO result type: {type(result)}")

    # ------------------------------------------------------------------------------------
    # 18) Williams %R (WilliamsR)
    # ------------------------------------------------------------------------------------
    elif indicator_name == "williamsr" or indicator_name == "willr":
        # Typically "length=14"
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate Williams %R({length}). Have {len(df)}")

        result = df.ta.willr(length=length, append=False)
        # Usually a single col: f"WILLR_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            wr_col = f'WILLR_{length}'
            if wr_col in result.columns:
                return float(result[wr_col].iloc[-1])
            else:
                raise ValueError(f"Williams %R column '{wr_col}' not found.")
        else:
            raise ValueError(f"Unexpected Williams %R result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 19) AROON
    # ─────────────────────────────────────────────────────────────────────────────
    if indicator_name == "aroon":
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for AROON({length}). Got {len(df)} rows.")

        # By default, aroon returns columns: ["AROOND_{length}", "AROONU_{length}"]
        result = df.ta.aroon(length=length, append=False)
        if isinstance(result, pd.DataFrame):
            # If user requests "down" or "up" or none
            if not line:
                # If none provided, let's pick "AROONU" as a default.
                line = "up"

            if line in ["down", "aroond"]:
                col = f"AROOND_{length}"
            elif line in ["up", "aroonu"]:
                col = f"AROONU_{length}"
            else:
                raise ValueError(f"Unknown line '{line}' for AROON. Try 'up' or 'down'.")

            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"Aroon column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected AROON result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 20) DEMA (Double Exponential Moving Average)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "dema":
        length = int(parameters.get('length', 14))
        if len(df) < length:
            raise ValueError(f"Not enough data to calculate DEMA({length}). Available: {len(df)}")

        result = df.ta.dema(length=length, append=False)
        # Typically single col: "DEMA_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            dema_col = f"DEMA_{length}"
            if dema_col in result.columns:
                return float(result[dema_col].iloc[-1])
            else:
                raise ValueError(f"DEMA column '{dema_col}' not found.")
        else:
            raise ValueError(f"Unexpected DEMA result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 21) VWAP (Volume Weighted Average Price)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "vwap":
        # VWAP typically requires 'volume'
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for VWAP.")
        # Some implementations also require specifying "offset" or "anchor" in pandas_ta
        # We'll just do default.
        result = df.ta.vwap(append=False)
        # Could be single col: "VWAP" or multiple col if anchor/different freq
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            # Typically "VWAP", or "VWAP_A" if anchor is used
            if "VWAP" in result.columns:
                return float(result["VWAP"].iloc[-1])
            else:
                # fallback: pick the first column if "VWAP" not found
                first_col = result.columns[0]
                return float(result[first_col].iloc[-1])
        else:
            raise ValueError(f"Unexpected VWAP result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 22) TRIX (1-line)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "trix":
        length = int(parameters.get('length', 14))
        if len(df) < length * 3:
            raise ValueError(f"Not enough data for TRIX({length}). Typically need ~3*length. Got {len(df)}")

        # TRIX typically returns 1 col: "TRIX_{length}"
        result = df.ta.trix(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            col = f"TRIX_{length}"
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"TRIX column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected TRIX result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 23) PVO (Percentage Volume Oscillator)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "pvo":
        # PVO is a MACD for volume
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for PVO but not found in DataFrame.")
        fast = int(parameters.get('fast', 12))
        slow = int(parameters.get('slow', 26))
        signal = int(parameters.get('signal', 9))
        # Need at least slow + signal to be safe
        required_length = slow + signal
        if len(df) < required_length:
            raise ValueError(f"Not enough data for PVO({fast},{slow},{signal}). Need {required_length}, got {len(df)}")

        # returns DataFrame with columns: [PVO_{fast}_{slow}_{signal}, PVOs..., PVOh...]
        result = df.ta.pvo(fast=fast, slow=slow, signal=signal, append=False)
        if not line:
            # default to main PVO line
            line = "pvo_line"

        if line == "pvo_line":
            col = f'PVO_{fast}_{slow}_{signal}'
        elif line == "signal_line":
            col = f'PVOs_{fast}_{slow}_{signal}'
        elif line == "histogram":
            col = f'PVOh_{fast}_{slow}_{signal}'
        else:
            raise ValueError(f"Unknown line '{line}' for PVO. Options: 'pvo_line', 'signal_line', 'histogram'.")

        if isinstance(result, pd.DataFrame):
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"PVO column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected PVO result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 24) STC (Schaff Trend Cycle)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "stc":
        # STC often uses MACD plus a stochastic to find cycles.
        fast = int(parameters.get('fast', 23))
        slow = int(parameters.get('slow', 50))
        factor = int(parameters.get('factor', 10))  # some versions might call it 'cycle'
        # need at least slow
        if len(df) < slow:
            raise ValueError(f"Not enough data for STC({fast},{slow}). Need {slow}, got {len(df)}")

        # returns a Series or DataFrame with col "STC_{fast}_{slow}_{factor}"
        result = df.ta.stc(fast=fast, slow=slow, factor=factor, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            col = f"STC_{fast}_{slow}_{factor}"
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"STC column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected STC result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 25) KVO (Klinger Volume Oscillator)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "kvo":
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for KVO but not found in DataFrame.")
        fast = int(parameters.get('fast', 34))
        slow = int(parameters.get('slow', 55))
        if len(df) < slow:
            raise ValueError(f"Not enough data for KVO({fast},{slow}). Need {slow}, got {len(df)}")

        # returns DataFrame with "KVO_{fast}_{slow}" and "KVOs_{fast}_{slow}" (signal)
        # line can be "kvo_line" or "signal"
        result = df.ta.kvo(fast=fast, slow=slow, append=False)

        if not line:
            line = "kvo_line"  # default

        if line == "kvo_line":
            col = f"KVO_{fast}_{slow}"
        elif line == "signal_line":
            col = f"KVOs_{fast}_{slow}"
        else:
            raise ValueError(f"Unknown line '{line}' for KVO. Options: 'kvo_line', 'signal_line'")

        if isinstance(result, pd.DataFrame):
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"KVO column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected KVO result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 26) EOM (Ease of Movement)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "eom":
        length = int(parameters.get('length', 14))
        divisor = float(parameters.get('divisor', 100000000.0))  # big number scale
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for EOM but not found in DataFrame.")
        if len(df) < length:
            raise ValueError(f"Not enough data for EOM({length}). Got {len(df)}")

        # returns a Series or DataFrame with col "EOM_{length}_{divisor}"
        result = df.ta.eom(length=length, divisor=divisor, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            eom_col = f"EOM_{length}_{divisor}"
            if eom_col in result.columns:
                return float(result[eom_col].iloc[-1])
            else:
                # might have used an integer cast of divisor, or something else
                # fallback to first col if we want
                # raise error if you prefer strict naming
                possible_cols = list(result.columns)
                raise ValueError(f"EOM column '{eom_col}' not found. Available: {possible_cols}")
        else:
            raise ValueError(f"Unexpected EOM result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 27) ALMA (Arnaud Legoux Moving Average)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "alma":
        length = int(parameters.get('length', 10))
        offset = float(parameters.get('offset', 0.85))  # 0.85 default
        sigma = float(parameters.get('sigma', 6))       # 6 default
        if len(df) < length:
            raise ValueError(f"Not enough data for ALMA({length}). Got {len(df)} rows")

        # returns Series/DataFrame with col "ALMA_{length}_{offset}_{sigma}"
        result = df.ta.alma(length=length, offset=offset, sigma=sigma, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            alma_col = f"ALMA_{length}_{offset}_{sigma}"
            if alma_col in result.columns:
                return float(result[alma_col].iloc[-1])
            else:
                raise ValueError(f"ALMA column '{alma_col}' not found.")
        else:
            raise ValueError(f"Unexpected ALMA result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 28) HMA (Hull Moving Average)
    # ─────────────────────────────────────────────────────────────────────────────
    if indicator_name == "hma":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for HMA({length}). Got {len(df)} rows.")
        result = df.ta.hma(length=length, append=False)
        # Typically single col named "HMA_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            hma_col = f"HMA_{length}"
            if hma_col in result.columns:
                return float(result[hma_col].iloc[-1])
            else:
                raise ValueError(f"HMA column '{hma_col}' not found.")
        else:
            raise ValueError(f"Unexpected HMA result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 29) ZLEMA (Zero Lag EMA)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "zlema":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for ZLEMA({length}). Got {len(df)} rows.")
        result = df.ta.zlema(length=length, append=False)
        # Usually single col "ZLEMA_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            zlema_col = f"ZLEMA_{length}"
            if zlema_col in result.columns:
                return float(result[zlema_col].iloc[-1])
            else:
                raise ValueError(f"ZLEMA column '{zlema_col}' not found.")
        else:
            raise ValueError(f"Unexpected ZLEMA result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 30) QSTICK
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "qstick":
        length = int(parameters.get("length", 10))
        if len(df) < length:
            raise ValueError(f"Not enough data for QSTICK({length}). Got {len(df)}.")
        # QSTICK often measures the difference between close and open, averaged over length
        result = df.ta.qstick(length=length, append=False)
        # Typically single col: "QSTICK_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            col = f"QSTICK_{length}"
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"QSTICK column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected QSTICK result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 31) Vortex
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "vortex":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for Vortex({length}). Got {len(df)}.")
        # Vortex typically yields columns: [VIP_{length}, VIN_{length}]
        # line can be "plus" or "minus"
        result = df.ta.vortex(length=length, append=False)
        if isinstance(result, pd.DataFrame):
            if not line:
                line = "plus"
            if line in ["plus", "vip"]:
                col = f"VIP_{length}"
            elif line in ["minus", "vin"]:
                col = f"VIN_{length}"
            else:
                raise ValueError("Unknown line for vortex. Use 'plus' or 'minus'.")
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"Vortex column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected Vortex result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 32) Ichimoku
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "ichimoku":
        # Typical parameters: tenkan=9, kijun=26, senkou=52
        tenkan = int(parameters.get("tenkan", 9))
        kijun = int(parameters.get("kijun", 26))
        senkou = int(parameters.get("senkou", 52))

        # Ichimoku can return multiple columns:
        # e.g. [ISA_{tenkan}_{kijun}, ISB_{senkou}, ITS_{tenkan}, IKS_{kijun}, ICS_{kijun}, ...
        # We might only reliably get lines if there's enough data for the largest of (tenkan, kijun, senkou)
        required_length = senkou
        if len(df) < required_length:
            raise ValueError(
                f"Not enough data for Ichimoku({tenkan},{kijun},{senkou}). Need {required_length}, got {len(df)}")

        # returns a DataFrame with multiple columns
        result = df.ta.ichimoku(tenkan=tenkan, kijun=kijun, senkou=senkou, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected Ichimoku result type: {type(result)}")

        # line can be "tenkan_sen", "kijun_sen", "senkou_a", "senkou_b", "chikou_span", etc.
        # The naming in pandas_ta might be "ITS", "IKS", "ISA", "ISB", "ICS" with appended `_9_26_52`.
        # Example: "ITS_9_26_52", "IKS_9_26_52", "ISA_9_26_52", "ISB_9_26_52", "ICS_9_26_52"
        if not line:
            # default to "ITS" (Tenkan)
            line = "tenkan_sen"

        # map them:
        base_col_name = f"_{tenkan}_{kijun}_{senkou}"
        if line in ["tenkan_sen", "its"]:
            col = f"ITS{base_col_name}"
        elif line in ["kijun_sen", "iks"]:
            col = f"IKS{base_col_name}"
        elif line in ["senkou_a", "isa"]:
            col = f"ISA{base_col_name}"
        elif line in ["senkou_b", "isb"]:
            col = f"ISB{base_col_name}"
        elif line in ["chikou_span", "ics"]:
            col = f"ICS{base_col_name}"
        else:
            raise ValueError(
                f"Unknown line '{line}' for Ichimoku. Options: tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou_span.")

        if col not in result.columns:
            raise ValueError(f"Ichimoku column '{col}' not found.")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 33) Donchian Channels
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "donchian":
        # Typically has "lower_length" and "upper_length" or just "lower" param
        lower_length = int(parameters.get("lower_length", 20))
        upper_length = int(parameters.get("upper_length", lower_length))
        # Usually returns DataFrame with "DCL_{lower_length}_{upper_length}", "DCU_...", "DCM_..."
        # line can be "lower", "upper", "middle"
        required_length = max(lower_length, upper_length)
        if len(df) < required_length:
            raise ValueError(f"Not enough data for Donchian Channels. Need {required_length}, have {len(df)}")

        result = df.ta.donchian(lower_length=lower_length, upper_length=upper_length, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected Donchian result type: {type(result)}")

        if not line:
            # default to middle
            line = "middle"
        # The columns typically: "DCU_{lower}_{upper}", "DCL_{lower}_{upper}", "DCM_{lower}_{upper}"
        if line == "upper":
            col = f"DCU_{lower_length}_{upper_length}"
        elif line == "lower":
            col = f"DCL_{lower_length}_{upper_length}"
        elif line in ["middle", "median"]:
            col = f"DCM_{lower_length}_{upper_length}"
        else:
            raise ValueError(f"Unknown line '{line}' for Donchian. Try 'upper', 'lower', or 'middle'.")

        if col not in result.columns:
            raise ValueError(f"Donchian column '{col}' not found.")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 34) LRC (Linear Regression Channel)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "lrc":
        length = int(parameters.get("length", 100))
        if len(df) < length:
            raise ValueError(f"Not enough data for LRC({length}). Need {length}, got {len(df)}")
        # returns DataFrame with "LRC_{length}" plus possibly stdev channels "LRCs_{length}", etc.
        # or "LRCA_{length}_2" for bands if alpha=2, etc. depends on param "alpha"
        alpha = float(parameters.get("alpha", 2.0))  # how many stdev for channel
        result = df.ta.lrc(length=length, alpha=alpha, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected LRC result type: {type(result)}")

        # line can be "regression" (main slope line) or "upper"/"lower" if alpha>0
        # Usually columns might be "LRC_{length}", "LRCU_{length}_{alpha}", "LRCL_{length}_{alpha}" etc.
        if not line:
            # default to main regression line
            line = "regression"

        if line in ["regression", "lrc"]:
            col = f"LRC_{length}"
        elif line == "upper":
            col = f"LRCU_{length}_{alpha}"
        elif line == "lower":
            col = f"LRCL_{length}_{alpha}"
        else:
            raise ValueError(f"Unknown line '{line}' for LRC. Options: 'regression', 'upper', 'lower'")

        if col not in result.columns:
            raise ValueError(f"LRC column '{col}' not found. Available: {list(result.columns)}")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 35) MAMA (MESA Adaptive Moving Average)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "mama":
        fastlimit = float(parameters.get("fastlimit", 0.5))
        slowlimit = float(parameters.get("slowlimit", 0.05))
        # Typically returns DataFrame with "MAMA_{fastlimit}_{slowlimit}" and "FAMA_{fastlimit}_{slowlimit}"
        result = df.ta.mama(fastlimit=fastlimit, slowlimit=slowlimit, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected MAMA result type: {type(result)}")

        # line can be "mama_line" or "fama_line"
        if not line:
            line = "mama_line"  # default
        if line == "mama_line":
            col = f"MAMA_{fastlimit}_{slowlimit}"
        elif line == "fama_line":
            col = f"FAMA_{fastlimit}_{slowlimit}"
        else:
            raise ValueError("Unknown line for MAMA. Use 'mama_line' or 'fama_line'.")

        if col not in result.columns:
            raise ValueError(f"MAMA column '{col}' not found.")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 36) PPO (Percentage Price Oscillator)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "ppo":
        fast = int(parameters.get("fast", 12))
        slow = int(parameters.get("slow", 26))
        signal = int(parameters.get("signal", 9))
        required_length = slow + signal
        if len(df) < required_length:
            raise ValueError(
                f"Not enough data for PPO({fast},{slow},{signal}). Need {required_length}, got {len(df)}")

        # Typically returns DataFrame:
        #  [PPO_{fast}_{slow}_{signal}, PPOs_{fast}_{slow}_{signal}, PPOh_{fast}_{slow}_{signal}]
        result = df.ta.ppo(fast=fast, slow=slow, signal=signal, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected PPO result type: {type(result)}")

        if not line:
            # default to main PPO line
            line = "ppo_line"
        if line == "ppo_line":
            col = f'PPO_{fast}_{slow}_{signal}'
        elif line == "signal_line":
            col = f'PPOs_{fast}_{slow}_{signal}'
        elif line == "histogram":
            col = f'PPOh_{fast}_{slow}_{signal}'
        else:
            raise ValueError(f"Unknown line '{line}' for PPO. Options: 'ppo_line', 'signal_line', 'histogram'.")

        if col not in result.columns:
            raise ValueError(f"PPO column '{col}' not found.")
        return float(result[col].iloc[-1])

        # ─────────────────────────────────────────────────────────────────────────────
        # 37) Fisher Transform
        # ─────────────────────────────────────────────────────────────────────────────
    if indicator_name == "fisher":
        length = int(parameters.get("length", 9))
        if len(df) < length:
            raise ValueError(f"Not enough data for Fisher({length}). Got {len(df)} rows.")
        # Pandas TA fisher returns DataFrame with "FISHERT_{length}" and "FISHERs_{length}" (signal).
        # line can be "fisher_line" or "signal_line".
        result = df.ta.fisher(length=length, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected fisher result type: {type(result)}")

        if not line:
            line = "fisher_line"  # default
        if line == "fisher_line":
            col = f"FISHERT_{length}"
        elif line in ("signal_line", "fisher_signal"):
            col = f"FISHERs_{length}"
        else:
            raise ValueError("Unknown line for Fisher. Use 'fisher_line' or 'signal_line'.")

        if col not in result.columns:
            raise ValueError(f"Fisher column '{col}' not found.")
        return float(result[col].iloc[-1])

        # ─────────────────────────────────────────────────────────────────────────────
        # 38) CMF (Chaikin Money Flow)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "cmf":
        length = int(parameters.get("length", 20))
        if "volume" not in df.columns:
            raise ValueError("Volume data required for CMF but not found.")
        if len(df) < length:
            raise ValueError(f"Not enough data for CMF({length}). Got {len(df)}.")

        # returns Series or DataFrame with col "CMF_{length}"
        result = df.ta.cmf(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            cmf_col = f"CMF_{length}"
            if cmf_col in result.columns:
                return float(result[cmf_col].iloc[-1])
            else:
                raise ValueError(f"CMF column '{cmf_col}' not found.")
        else:
            raise ValueError(f"Unexpected CMF result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 39) AD (Accumulation/Distribution Line)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "ad":
        # Some references name this "accdist"
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for Accum/Dist but not found.")
        # Typically a single col "AD"
        result = df.ta.ad(append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            if "AD" in result.columns:
                return float(result["AD"].iloc[-1])
            else:
                raise ValueError("AD column not found in DataFrame.")
        else:
            raise ValueError(f"Unexpected AD result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 40) BOP (Balance of Power)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "bop":
        # Typically no extra parameters, or just a 'length' for smoothing
        length = parameters.get("length", None)  # optional
        if length:
            # If user provided length, we do: df.ta.bop(length=length)
            result = df.ta.bop(length=int(length), append=False)
        else:
            # If no length, do default
            result = df.ta.bop(append=False)

        # Usually single col: "BOP" or "BOP_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            # possibly "BOP" or "BOP_{length}"
            for col in result.columns:
                if col.startswith("BOP"):
                    return float(result[col].iloc[-1])
            # If we get here, we didn't find a BOP column
            raise ValueError("No BOP column found in result.")
        else:
            raise ValueError(f"Unexpected BOP result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 41) CVI (Choppiness Index)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "cvi":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for Choppiness Index(CVI) with length={length}. Got {len(df)}")
        result = df.ta.cvi(length=length, append=False)
        # Typically single col "CVI_{length}"
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            cvi_col = f"CVI_{length}"
            if cvi_col in result.columns:
                return float(result[cvi_col].iloc[-1])
            else:
                raise ValueError(f"CVI column '{cvi_col}' not found.")
        else:
            raise ValueError(f"Unexpected CVI result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 42) T3 (T3 Moving Average)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "t3":
        length = int(parameters.get("length", 10))
        # "b" param in T3 is smoothing factor, default 0.7
        b = float(parameters.get("b", 0.7))
        if len(df) < length:
            raise ValueError(f"Not enough data for T3({length}). Have {len(df)}")

        # returns Series/DataFrame with col "T3_{length}_{b}"
        result = df.ta.t3(length=length, b=b, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            t3_col = f"T3_{length}_{b}"
            if t3_col in result.columns:
                return float(result[t3_col].iloc[-1])
            else:
                # maybe just pick the first column if the naming changed
                possible_cols = list(result.columns)
                raise ValueError(f"T3 column '{t3_col}' not found. Available: {possible_cols}")
        else:
            raise ValueError(f"Unexpected T3 result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 43) EFI (Elder Force Index)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "efi":
        length = int(parameters.get("length", 13))
        if "volume" not in df.columns:
            raise ValueError("Volume data is required for EFI but not found.")
        if len(df) < length:
            raise ValueError(f"Not enough data for EFI({length}). Need {length}, got {len(df)}")

        # returns single col "EFI_{length}"
        result = df.ta.efi(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            efi_col = f"EFI_{length}"
            if efi_col in result.columns:
                return float(result[efi_col].iloc[-1])
            else:
                raise ValueError(f"EFI column '{efi_col}' not found.")
        else:
            raise ValueError(f"Unexpected EFI result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 44) WAD (Williams AD)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "wad":
        # Typically no extra params, but let's see if length is optional
        # df.ta.wad(append=False) => returns "WAD"
        result = df.ta.wad(append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            if "WAD" in result.columns:
                return float(result["WAD"].iloc[-1])
            else:
                raise ValueError(f"WAD column not found.")
        else:
            raise ValueError(f"Unexpected WAD result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 45) Slope
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "slope":
        length = int(parameters.get("length", 5))
        if len(df) < length:
            raise ValueError(f"Not enough data for Slope({length}). Have {len(df)}")
        # slope returns the slope of a linear regression of 'close' usually
        # df.ta.slope(length=..., append=False) => col "SLOPE_{length}"
        result = df.ta.slope(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            slope_col = f"SLOPE_{length}"
            if slope_col in result.columns:
                return float(result[slope_col].iloc[-1])
            else:
                raise ValueError(f"Slope column '{slope_col}' not found.")
        else:
            raise ValueError(f"Unexpected Slope result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # 46) NATR (Normalized ATR)
        # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "natr":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for NATR({length}). Got {len(df)} rows.")
        # returns single col "NATR_{length}"
        result = df.ta.natr(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            natr_col = f"NATR_{length}"
            if natr_col in result.columns:
                return float(result[natr_col].iloc[-1])
            else:
                raise ValueError(f"NATR column '{natr_col}' not found.")
        else:
            raise ValueError(f"Unexpected NATR result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 50) TEMA (Triple Exponential Moving Average)
    # ─────────────────────────────────────────────────────────────────────────────
    if indicator_name == "tema":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for TEMA({length}). Have {len(df)}")

        # Typically returns single col "TEMA_{length}"
        result = df.ta.tema(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            tema_col = f"TEMA_{length}"
            if tema_col in result.columns:
                return float(result[tema_col].iloc[-1])
            else:
                raise ValueError(f"TEMA column '{tema_col}' not found.")
        else:
            raise ValueError(f"Unexpected TEMA result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 51) KC (Keltner Channels)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "kc":
        length = int(parameters.get("length", 20))
        scalar = float(parameters.get("scalar", 2.0))  # band width
        mamode = parameters.get("mamode", "ema").lower()  # could be "ema" or "sma" or similar
        if len(df) < length:
            raise ValueError(f"Not enough data for Keltner Channels({length}). Got {len(df)}")

        # Typically returns 3 columns: KCU, KCM, KCL
        # e.g. "KCU_{length}_{scalar}_{mamode}", "KCM_...", "KCL_..."
        result = df.ta.kc(length=length, scalar=scalar, mamode=mamode, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected Keltner Channels result type: {type(result)}")

        # line can be "upper", "middle", "lower"
        if not line:
            line = "middle"
        line = line.lower()
        if line in ("upper", "kcu"):
            col = f"KCU_{length}_{scalar}_{mamode}"
        elif line in ("middle", "kcm"):
            col = f"KCM_{length}_{scalar}_{mamode}"
        elif line in ("lower", "kcl"):
            col = f"KCL_{length}_{scalar}_{mamode}"
        else:
            raise ValueError("Unknown line for Keltner Channels. Use 'upper', 'middle', or 'lower'.")

        if col not in result.columns:
            raise ValueError(f"Keltner Channels column '{col}' not found.")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 52) EWO (Elliott Wave Oscillator)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "ewo":
        fast = int(parameters.get("fast", 5))
        slow = int(parameters.get("slow", 35))
        if len(df) < slow:
            raise ValueError(f"Not enough data for EWO({fast},{slow}). Need {slow}, got {len(df)}")

        # Typically yields single col: "EWO_{fast}_{slow}"
        result = df.ta.ewo(fast=fast, slow=slow, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            ewo_col = f"EWO_{fast}_{slow}"
            if ewo_col in result.columns:
                return float(result[ewo_col].iloc[-1])
            else:
                raise ValueError(f"EWO column '{ewo_col}' not found.")
        else:
            raise ValueError(f"Unexpected EWO result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 53) CRSI (Connors RSI)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "crsi":
        rsi_length = int(parameters.get("rsi_length", 3))
        streak_length = int(parameters.get("streak_length", 2))
        ma_length = int(parameters.get("ma_length", 100))
        # This is a combination approach: RSI, UpDown streak, and an SMA of that streak RSI
        required_length = max(rsi_length, streak_length, ma_length)
        if len(df) < required_length:
            raise ValueError(f"Not enough data for CRSI. Need {required_length}, got {len(df)}")

        # Typically returns a single column: "CRSI_{rsi_length}_{streak_length}_{ma_length}"
        result = df.ta.crsi(rsi_length=rsi_length, streak_length=streak_length, ma_length=ma_length,
                            append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            col = f"CRSI_{rsi_length}_{streak_length}_{ma_length}"
            if col in result.columns:
                return float(result[col].iloc[-1])
            else:
                raise ValueError(f"CRSI column '{col}' not found.")
        else:
            raise ValueError(f"Unexpected CRSI result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 54) ZScore (Z-Score of close or some other column)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "zscore":
        length = int(parameters.get("length", 30))
        if len(df) < length:
            raise ValueError(f"Not enough data for ZScore({length}). Have {len(df)}")
        # Usually single col: "ZSCORE_{length}"
        # By default, it calculates the zscore of 'close'.
        result = df.ta.zscore(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            z_col = f"ZSCORE_{length}"
            if z_col in result.columns:
                return float(result[z_col].iloc[-1])
            else:
                raise ValueError(f"ZScore column '{z_col}' not found.")
        else:
            raise ValueError(f"Unexpected ZScore result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 55) RVI (Relative Volatility Index)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "rvi":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for RVI({length}). Got {len(df)}")
        # Typically single col: "RVI_{length}"
        result = df.ta.rvi(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            rvi_col = f"RVI_{length}"
            if rvi_col in result.columns:
                return float(result[rvi_col].iloc[-1])
            else:
                raise ValueError(f"RVI column '{rvi_col}' not found.")
        else:
            raise ValueError(f"Unexpected RVI result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 56) BBW (Bollinger Bandwidth)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "bbw":
        length = int(parameters.get("length", 20))
        std = float(parameters.get("std", 2.0))
        if len(df) < length:
            raise ValueError(f"Not enough data for BBW({length}). Have {len(df)}")

        # Typically single col: "BBBw_{length}_{std}"
        result = df.ta.bbw(length=length, std=std, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            bbw_col = f"BBBw_{length}_{std}"
            if bbw_col in result.columns:
                return float(result[bbw_col].iloc[-1])
            else:
                raise ValueError(f"BBW column '{bbw_col}' not found.")
        else:
            raise ValueError(f"Unexpected BBW result type: {type(result)}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 57) GANNHiLo (Gann HiLo Activator)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "gannhilo":
        length = int(parameters.get("length", 10))
        if len(df) < length:
            raise ValueError(f"Not enough data for GANNHiLo({length}). Have {len(df)}")

        # Typically returns a DataFrame with "GANNHi_{length}" and "GANNLo_{length}"
        # line can be "hi" or "lo"
        result = df.ta.gannhilo(length=length, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected GANNHiLo result type: {type(result)}")

        if not line:
            line = "hi"  # default
        if line == "hi":
            col = f"GANNHi_{length}"
        elif line == "lo":
            col = f"GANNLo_{length}"
        else:
            raise ValueError("Unknown line for GANNHiLo. Use 'hi' or 'lo'.")

        if col not in result.columns:
            raise ValueError(f"GANNHiLo column '{col}' not found.")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 58) QQE (Quantitative Qualitative Estimation)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "qqe":
        length = int(parameters.get("length", 14))
        smooth = int(parameters.get("smooth", 5))  # some versions might accept float
        if len(df) < length:
            raise ValueError(f"Not enough data for QQE({length}). Have {len(df)}")
        # QQE typically returns DataFrame with columns: "QQE_{length}_{smooth}", "QQEl_{length}_{smooth}" (lower?), etc.
        result = df.ta.qqe(length=length, smooth=smooth, append=False)
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Unexpected QQE result type: {type(result)}")

        # If user wants main QQE line or "lower" line? The code might produce "QQE_14_5" and "QQEl_14_5"
        if not line:
            line = "main"
        if line == "main":
            col = f"QQE_{length}_{smooth}"
        elif line in ("lower", "qqel"):
            col = f"QQEl_{length}_{smooth}"
        else:
            raise ValueError("Unknown line for QQE. Use 'main' or 'lower' (qqel).")

        if col not in result.columns:
            raise ValueError(f"QQE column '{col}' not found.")
        return float(result[col].iloc[-1])

    # ─────────────────────────────────────────────────────────────────────────────
    # 59) TSF (Time Series Forecast)
    # ─────────────────────────────────────────────────────────────────────────────
    elif indicator_name == "tsf":
        length = int(parameters.get("length", 14))
        if len(df) < length:
            raise ValueError(f"Not enough data for TSF({length}). Have {len(df)}")

        # Typically single col: "TSF_{length}"
        result = df.ta.tsf(length=length, append=False)
        if isinstance(result, pd.Series):
            return float(result.iloc[-1])
        elif isinstance(result, pd.DataFrame):
            tsf_col = f"TSF_{length}"
            if tsf_col in result.columns:
                return float(result[tsf_col].iloc[-1])
            else:
                raise ValueError(f"TSF column '{tsf_col}' not found.")
        else:
            raise ValueError(f"Unexpected TSF result type: {type(result)}")

        # ─────────────────────────────────────────────────────────────────────────────
        # If not matched anything
        # ─────────────────────────────────────────────────────────────────────────────
    else:
        raise ValueError(f"Indicator '{indicator_name}' is not supported.")
