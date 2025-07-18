import pandas as pd
import talib
import numpy as np
import logging
from globals import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Рассчитывает VWAP для бинарных опционов."""
    if 'close' not in df.columns or 'volume' not in df.columns:
        return pd.Series(np.nan, index=df.index)
    
    # Типичная цена
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    price_volume = typical_price * df['volume']
    cumulative_price_volume = price_volume.cumsum()
    cumulative_volume = df['volume'].cumsum()
    vwap = cumulative_price_volume / cumulative_volume
    
    return vwap.fillna(method='ffill')

def calculate_macd(df: pd.DataFrame) -> tuple:
    """Рассчитывает MACD."""
    if 'close' not in df.columns:
        return pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)
    
    macd, macdsignal, macdhist = talib.MACD(
        df['close'],
        fastperiod=MACD_FAST_PERIOD,
        slowperiod=MACD_SLOW_PERIOD,
        signalperiod=MACD_SIGNAL_PERIOD
    )
    return macd, macdsignal, macdhist

def calculate_rsi(df: pd.DataFrame) -> pd.Series:
    """Рассчитывает RSI."""
    if 'close' not in df.columns:
        return pd.Series(np.nan, index=df.index)
    return talib.RSI(df['close'], timeperiod=RSI_PERIOD)

def calculate_supertrend(df: pd.DataFrame) -> pd.Series:
    """Рассчитывает Supertrend для бинарных опционов."""
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return pd.Series(np.nan, index=df.index)

    atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=SUPERTREND_PERIOD)
    hl2 = (df['high'] + df['low']) / 2
    
    basic_upper_band = hl2 + (SUPERTREND_MULTIPLIER * atr)
    basic_lower_band = hl2 - (SUPERTREND_MULTIPLIER * atr)
    
    final_upper_band = basic_upper_band.copy()
    final_lower_band = basic_lower_band.copy()
    
    for i in range(1, len(df)):
        if df['close'].iloc[i-1] > final_upper_band.iloc[i-1]:
            final_upper_band.iloc[i] = max(basic_upper_band.iloc[i], final_upper_band.iloc[i-1])
        else:
            final_upper_band.iloc[i] = basic_upper_band.iloc[i]
            
        if df['close'].iloc[i-1] < final_lower_band.iloc[i-1]:
            final_lower_band.iloc[i] = min(basic_lower_band.iloc[i], final_lower_band.iloc[i-1])
        else:
            final_lower_band.iloc[i] = basic_lower_band.iloc[i]
    
    supertrend = pd.Series(np.nan, index=df.index)
    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = final_upper_band.iloc[i] if df['close'].iloc[i] <= final_upper_band.iloc[i] else final_lower_band.iloc[i]
        else:
            if supertrend.iloc[i-1] == final_upper_band.iloc[i-1] and df['close'].iloc[i] <= final_upper_band.iloc[i]:
                supertrend.iloc[i] = final_upper_band.iloc[i]
            elif supertrend.iloc[i-1] == final_upper_band.iloc[i-1] and df['close'].iloc[i] > final_upper_band.iloc[i]:
                supertrend.iloc[i] = final_lower_band.iloc[i]
            elif supertrend.iloc[i-1] == final_lower_band.iloc[i-1] and df['close'].iloc[i] >= final_lower_band.iloc[i]:
                supertrend.iloc[i] = final_lower_band.iloc[i]
            else:
                supertrend.iloc[i] = final_upper_band.iloc[i]
    
    return supertrend

def calculate_bollinger_bands(df: pd.DataFrame) -> tuple:
    """Рассчитывает Bollinger Bands."""
    if 'close' not in df.columns:
        return pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)
    
    upper, middle, lower = talib.BBANDS(
        df['close'],
        timeperiod=BOLLINGER_PERIOD,
        nbdevup=BOLLINGER_NUM_STD_DEV,
        nbdevdn=BOLLINGER_NUM_STD_DEV,
        matype=0
    )
    return upper, middle, lower

def calculate_stochastic(df: pd.DataFrame) -> tuple:
    """Рассчитывает Stochastic Oscillator."""
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return pd.Series(np.nan, index=df.index), pd.Series(np.nan, index=df.index)
    
    stoch_k, stoch_d = talib.STOCH(
        df['high'], df['low'], df['close'],
        fastk_period=STOCH_K_PERIOD,
        slowk_period=STOCH_SMOOTH_K_PERIOD,
        slowk_matype=0,
        slowd_period=STOCH_D_PERIOD,
        slowd_matype=0
    )
    return stoch_k, stoch_d

def calculate_atr(df: pd.DataFrame) -> pd.Series:
    """Рассчитывает ATR."""
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return pd.Series(np.nan, index=df.index)
    return talib.ATR(df['high'], df['low'], df['close'], timeperiod=ATR_PERIOD)

def calculate_williams_r(df: pd.DataFrame) -> pd.Series:
    """Рассчитывает Williams %R."""
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return pd.Series(np.nan, index=df.index)
    return talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Рассчитывает все индикаторы для бинарных опционов."""
    if df.empty:
        return df

    df = df.copy()
    
    # Основные индикаторы
    df['vwap'] = calculate_vwap(df)
    macd, macdsignal, macdhist = calculate_macd(df)
    df['macd'] = macd
    df['macd_signal'] = macdsignal
    df['macd_hist'] = macdhist
    df['rsi'] = calculate_rsi(df)
    df['supertrend'] = calculate_supertrend(df)
    
    # Bollinger Bands
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(df)
    df['bb_upper'] = upper_bb
    df['bb_middle'] = middle_bb
    df['bb_lower'] = lower_bb
    df['bb_width'] = (upper_bb - lower_bb) / middle_bb
    df['bb_position'] = (df['close'] - lower_bb) / (upper_bb - lower_bb)
    
    # Stochastic
    stoch_k, stoch_d = calculate_stochastic(df)
    df['stoch_k'] = stoch_k
    df['stoch_d'] = stoch_d
    df['stoch_diff'] = stoch_k - stoch_d
    
    # Дополнительные индикаторы
    df['atr'] = calculate_atr(df)
    df['williams_r'] = calculate_williams_r(df)
    df['sma_volume'] = talib.SMA(df['volume'], timeperiod=20)
    df['volume_ratio'] = df['volume'] / df['sma_volume']
    
    # Производные для стратегии
    df['pct_change'] = df['close'].pct_change()
    df['vwap_gradient'] = df['vwap'].diff()
    df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap']
    df['price_momentum'] = df['close'].pct_change(periods=3)
    
    # Сигналы разворота
    df['supertrend_signal'] = 0
    df.loc[df['close'] > df['supertrend'], 'supertrend_signal'] = 1
    df.loc[df['close'] < df['supertrend'], 'supertrend_signal'] = -1
    
    # Сжатие Bollinger Bands
    df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(20).mean() * 0.8
    
    # Пересечения Stochastic
    df['stoch_crossover'] = 0
    df.loc[(df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1)), 'stoch_crossover'] = 1
    df.loc[(df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1)), 'stoch_crossover'] = -1
    
    # Нормализация ATR
    df['atr_normalized'] = df['atr'] / df['close']
    
    df.dropna(inplace=True)
    return df
  
