"""
统一的CTA策略实现 - 支持回测和实盘
继承自BaseStrategy基类
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging
from base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class CTAStrategy(BaseStrategy):
    """
    统一的CTA策略
    结合趋势跟踪和均值回归
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化CTA策略
        
        Args:
            name: 策略名称
            config: 策略配置
        """
        super().__init__(name, config)
        
        # CTA特定参数
        self.fast_period = config.get('fast_period', 12)
        self.slow_period = config.get('slow_period', 48)
        self.rsi_period = config.get('rsi_period', 14)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        self.atr_period = config.get('atr_period', 14)
        self.volume_threshold = config.get('volume_threshold', 1.2)
        
        # 风险控制参数
        self.position_size = config.get('position_size', 0.1)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.015)
        self.take_profit_pct = config.get('take_profit_pct', 0.03)
        
        # 状态变量
        self.indicators_cache = {}
        
        logger.info(f"CTA策略 '{name}' 初始化完成")
    
    def initialize(self, data: pd.DataFrame) -> None:
        """
        策略初始化
        
        Args:
            data: 初始化数据
        """
        if data.empty:
            logger.warning("初始化数据为空")
            return
        
        # 计算初始技术指标
        data_with_indicators = self.calculate_indicators(data)
        
        # 缓存最后的技术指标值
        if not data_with_indicators.empty:
            last_row = data_with_indicators.iloc[-1]
            for col in data_with_indicators.columns:
                if col not in ['open', 'high', 'low', 'close', 'volume']:
                    self.indicators_cache[col] = last_row[col]
        
        self.initialized = True
        logger.info(f"策略 '{self.name}' 初始化完成，数据量: {len(data)}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            data: 原始数据
            
        Returns:
            包含技术指标的数据
        """
        df = data.copy()
        
        # 确保有必要的列
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"数据缺少 {col} 列，使用close替代")
                df[col] = df.get('close', 0)
        
        # 1. 移动平均线
        df['ma_fast'] = df['close'].rolling(window=self.fast_period).mean()
        df['ma_slow'] = df['close'].rolling(window=self.slow_period).mean()
        
        # 2. RSI指标
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # 3. 布林带
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        
        # 4. ATR（平均真实波幅）
        df['atr'] = self._calculate_atr(df, self.atr_period)
        
        # 5. 成交量指标
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        else:
            df['volume_ratio'] = 1.0
        
        # 6. 价格位置（相对于布林带）
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 7. 趋势强度
        df['trend_strength'] = abs(df['ma_fast'] - df['ma_slow']) / df['close']
        
        # 填充NaN值
        df = df.ffill().bfill()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Args:
            data: 包含技术指标的数据
            
        Returns:
            信号序列：1=买入，-1=卖出，0=持有
        """
        if data.empty:
            return pd.Series([], dtype=int)
        
        df = data.copy()
        signals = pd.Series(0, index=df.index)
        
        # 条件1: 双均线交叉
        ma_cross_up = (df['ma_fast'] > df['ma_slow']) & (df['ma_fast'].shift(1) <= df['ma_slow'].shift(1))
        ma_cross_down = (df['ma_fast'] < df['ma_slow']) & (df['ma_fast'].shift(1) >= df['ma_slow'].shift(1))
        
        # 条件2: RSI超买超卖
        rsi_oversold = df['rsi'] < 30
        rsi_overbought = df['rsi'] > 70
        
        # 条件3: 布林带位置
        bb_lower_touch = df['bb_position'] < 0.2  # 接近下轨
        bb_upper_touch = df['bb_position'] > 0.8  # 接近上轨
        
        # 条件4: 成交量确认
        volume_confirmation = df['volume_ratio'] > self.volume_threshold
        
        # 条件5: 波动率过滤（避免在低波动时交易）
        volatility_ok = df['atr'] / df['close'] > 0.005  # 至少0.5%的波动
        
        # 买入信号（多头）
        buy_conditions = (
            ma_cross_up &           # 均线金叉
            rsi_oversold &          # RSI超卖
            bb_lower_touch &        # 布林带下轨
            volume_confirmation &   # 成交量确认
            volatility_ok           # 波动率合适
        )
        
        # 卖出信号（空头）
        sell_conditions = (
            ma_cross_down &         # 均线死叉
            rsi_overbought &        # RSI超买
            bb_upper_touch &        # 布林带上轨
            volume_confirmation &   # 成交量确认
            volatility_ok           # 波动率合适
        )
        
        # 应用信号
        signals[buy_conditions] = 1
        signals[sell_conditions] = -1
        
        # 信号过滤：避免频繁交易
        signals = self._filter_signals(signals)
        
        return signals
    
    def _filter_signals(self, signals: pd.Series) -> pd.Series:
        """
        过滤信号，避免频繁交易
        
        Args:
            signals: 原始信号
            
        Returns:
            过滤后的信号
        """
        if signals.empty:
            return signals
        
        filtered_signals = signals.copy()
        
        # 找到信号点
        signal_indices = signals[signals != 0].index
        
        if len(signal_indices) < 2:
            return filtered_signals
        
        # 设置最小交易间隔（例如至少间隔4根K线）
        min_interval = 4
        
        last_signal_idx = signal_indices[0]
        for i in range(1, len(signal_indices)):
            current_idx = signal_indices[i]
            
            # 计算距离上次信号的间隔
            idx_diff = signals.index.get_loc(current_idx) - signals.index.get_loc(last_signal_idx)
            
            if idx_diff < min_interval:
                # 间隔太短，过滤掉这个信号
                filtered_signals[current_idx] = 0
            else:
                last_signal_idx = current_idx
        
        return filtered_signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算RSI指标
        
        Args:
            prices: 价格序列
            period: RSI周期
            
        Returns:
            RSI序列
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算ATR（平均真实波幅）
        
        Args:
            df: 包含OHLC的数据
            period: ATR周期
            
        Returns:
            ATR序列
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # 计算真实波幅
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算ATR
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def on_bar(self, bar: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理新的K线数据
        
        Args:
            bar: 单根K线数据
            
        Returns:
            包含信号和决策的字典
        """
        # 调用父类方法
        result = super().on_bar(bar)
        
        # CTA策略特定的处理
        if not self.initialized:
            logger.warning(f"策略 '{self.name}' 未初始化，跳过处理")
            return result
        
        # 更新技术指标缓存
        if 'indicators' in result and result['indicators']:
            for key, value in result['indicators'].items():
                self.indicators_cache[key] = value
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取策略当前状态
        
        Returns:
            状态字典
        """
        base_status = super().get_status()
        
        # 添加CTA特定状态
        cta_status = {
            'indicators': self.indicators_cache.copy(),
            'parameters': {
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'rsi_period': self.rsi_period,
                'bb_period': self.bb_period,
                'position_size': self.position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct
            }
        }
        
        base_status.update(cta_status)
        return base_status
    
    def update_parameters(self, **kwargs):
        """
        更新策略参数
        
        Args:
            **kwargs: 参数键值对
        """
        valid_params = [
            'fast_period', 'slow_period', 'rsi_period', 'bb_period',
            'bb_std', 'atr_period', 'volume_threshold',
            'position_size', 'stop_loss_pct', 'take_profit_pct'
        ]
        
        for param, value in kwargs.items():
            if param in valid_params and hasattr(self, param):
                setattr(self, param, value)
                logger.info(f"更新参数 {param} = {value}")
            else:
                logger.warning(f"忽略无效参数: {param}")
        
        # 重置初始化状态，因为参数变化需要重新计算指标
        self.initialized = False
        self.indicators_cache = {}