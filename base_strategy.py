"""
策略基类 - 支持回测和实盘的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    策略基类
    所有策略都应该继承这个类，实现统一的接口
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            name: 策略名称
            config: 策略配置
        """
        self.name = name
        self.config = config
        self.initialized = False
        self.position = 0  # 当前仓位：1=多头，-1=空头，0=空仓
        self.entry_price = 0.0
        self.equity = config.get('initial_capital', 10000.0)
        self.commission = config.get('commission', 0.001)  # 默认0.1%手续费
        
        # 交易记录
        self.trades = []
        self.signals = []
        
        # 性能指标
        self.metrics = {}
        
        logger.info(f"策略 '{name}' 初始化完成")
    
    @abstractmethod
    def initialize(self, data: pd.DataFrame) -> None:
        """
        策略初始化
        在开始回测或交易前调用
        
        Args:
            data: 初始化数据（用于计算初始指标）
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            data: 原始数据
            
        Returns:
            包含技术指标的数据
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Args:
            data: 包含技术指标的数据
            
        Returns:
            信号序列：1=买入，-1=卖出，0=持有
        """
        pass
    
    def on_bar(self, bar: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理新的K线数据（回测和实盘通用）
        
        Args:
            bar: 单根K线数据
            
        Returns:
            包含信号和决策的字典
        """
        # 将单根K线转换为DataFrame（为了兼容性）
        bar_df = pd.DataFrame([bar])
        bar_df.set_index('timestamp', inplace=True)
        
        # 计算指标
        bar_with_indicators = self.calculate_indicators(bar_df)
        
        # 生成信号
        signals = self.generate_signals(bar_with_indicators)
        
        # 获取最新信号
        latest_signal = signals.iloc[-1] if len(signals) > 0 else 0
        
        # 记录信号
        signal_record = {
            'timestamp': bar['timestamp'],
            'price': bar['close'],
            'signal': latest_signal,
            'position': self.position,
            'equity': self.equity
        }
        self.signals.append(signal_record)
        
        # 生成交易决策
        decision = self._make_trading_decision(latest_signal, bar)
        
        return {
            'signal': latest_signal,
            'decision': decision,
            'position': self.position,
            'equity': self.equity,
            'indicators': bar_with_indicators.iloc[-1].to_dict() if not bar_with_indicators.empty else {}
        }
    
    def _make_trading_decision(self, signal: int, bar: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据信号生成交易决策
        
        Args:
            signal: 交易信号
            bar: K线数据
            
        Returns:
            交易决策
        """
        decision = {
            'action': 'hold',  # hold, buy, sell, close
            'reason': '',
            'price': bar['close'],
            'quantity': 0.0,
            'stop_loss': 0.0,
            'take_profit': 0.0
        }
        
        # 空仓状态
        if self.position == 0:
            if signal == 1:  # 买入信号
                decision['action'] = 'buy'
                decision['reason'] = '开多头仓位'
                decision['quantity'] = self._calculate_position_size(bar['close'])
                decision['stop_loss'] = bar['close'] * (1 - self.config.get('stop_loss_pct', 0.02))
                decision['take_profit'] = bar['close'] * (1 + self.config.get('take_profit_pct', 0.04))
            elif signal == -1:  # 卖出信号（做空）
                decision['action'] = 'sell'
                decision['reason'] = '开空头仓位'
                decision['quantity'] = self._calculate_position_size(bar['close'])
                decision['stop_loss'] = bar['close'] * (1 + self.config.get('stop_loss_pct', 0.02))
                decision['take_profit'] = bar['close'] * (1 - self.config.get('take_profit_pct', 0.04))
        
        # 持有多头仓位
        elif self.position == 1:
            if signal == -1:  # 卖出信号
                decision['action'] = 'sell'
                decision['reason'] = '平多头仓位'
                decision['quantity'] = abs(self.position)
            else:
                # 检查止损止盈
                current_price = bar['close']
                if hasattr(self, 'stop_loss_price') and current_price <= self.stop_loss_price:
                    decision['action'] = 'sell'
                    decision['reason'] = '触发止损'
                    decision['quantity'] = abs(self.position)
                elif hasattr(self, 'take_profit_price') and current_price >= self.take_profit_price:
                    decision['action'] = 'sell'
                    decision['reason'] = '触发止盈'
                    decision['quantity'] = abs(self.position)
        
        # 持有空头仓位
        elif self.position == -1:
            if signal == 1:  # 买入信号
                decision['action'] = 'buy'
                decision['reason'] = '平空头仓位'
                decision['quantity'] = abs(self.position)
            else:
                # 检查止损止盈
                current_price = bar['close']
                if hasattr(self, 'stop_loss_price') and current_price >= self.stop_loss_price:
                    decision['action'] = 'buy'
                    decision['reason'] = '触发止损'
                    decision['quantity'] = abs(self.position)
                elif hasattr(self, 'take_profit_price') and current_price <= self.take_profit_price:
                    decision['action'] = 'buy'
                    decision['reason'] = '触发止盈'
                    decision['quantity'] = abs(self.position)
        
        return decision
    
    def _calculate_position_size(self, price: float) -> float:
        """
        计算仓位大小
        
        Args:
            price: 当前价格
            
        Returns:
            仓位数量
        """
        position_size_pct = self.config.get('position_size', 0.1)  # 默认10%
        position_value = self.equity * position_size_pct
        quantity = position_value / price
        
        # 考虑手续费
        commission_cost = quantity * price * self.commission
        if position_value - commission_cost <= 0:
            return 0.0
        
        return quantity
    
    def update_position(self, trade: Dict[str, Any]) -> None:
        """
        更新仓位状态
        
        Args:
            trade: 交易记录
        """
        if trade['action'] == 'buy':
            if self.position == 0:  # 开多头
                self.position = 1
                self.entry_price = trade['price']
                self.stop_loss_price = trade.get('stop_loss', trade['price'] * 0.98)
                self.take_profit_price = trade.get('take_profit', trade['price'] * 1.04)
            elif self.position == -1:  # 平空头
                self.position = 0
                self.entry_price = 0.0
        
        elif trade['action'] == 'sell':
            if self.position == 0:  # 开空头
                self.position = -1
                self.entry_price = trade['price']
                self.stop_loss_price = trade.get('stop_loss', trade['price'] * 1.02)
                self.take_profit_price = trade.get('take_profit', trade['price'] * 0.96)
            elif self.position == 1:  # 平多头
                self.position = 0
                self.entry_price = 0.0
        
        # 记录交易
        self.trades.append(trade)
        
        # 更新权益
        if 'pnl' in trade:
            self.equity += trade['pnl']
    
    def calculate_metrics(self) -> Dict[str, float]:
        """
        计算策略性能指标
        
        Returns:
            性能指标字典
        """
        if not self.trades:
            return {}
        
        trades_df = pd.DataFrame(self.trades)
        
        # 基础指标
        total_return = (self.equity - self.config.get('initial_capital', 10000)) / self.config.get('initial_capital', 10000)
        
        # 交易分析
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]
        
        metrics = {
            'initial_capital': self.config.get('initial_capital', 10000),
            'final_equity': self.equity,
            'total_return': total_return,
            'total_trades': len(trades_df),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0,
            'total_pnl': trades_df['pnl'].sum(),
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(),
            'sharpe_ratio': self._calculate_sharpe_ratio()
        }
        
        self.metrics = metrics
        return metrics
    
    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.trades:
            return 0.0
        
        # 简化计算，实际应该基于权益曲线
        equity_curve = [self.config.get('initial_capital', 10000)]
        for trade in self.trades:
            if 'equity_after' in trade:
                equity_curve.append(trade['equity_after'])
        
        if len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if not self.trades or len(self.trades) < 2:
            return 0.0
        
        # 简化计算
        returns = []
        for i in range(1, len(self.trades)):
            if 'equity_after' in self.trades[i] and 'equity_after' in self.trades[i-1]:
                ret = (self.trades[i]['equity_after'] - self.trades[i-1]['equity_after']) / self.trades[i-1]['equity_after']
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (avg_return - risk_free_rate/252) / std_return * np.sqrt(252)  # 年化
        
        return sharpe
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取策略当前状态
        
        Returns:
            状态字典
        """
        return {
            'name': self.name,
            'position': self.position,
            'entry_price': self.entry_price,
            'equity': self.equity,
            'total_trades': len(self.trades),
            'current_signal': self.signals[-1]['signal'] if self.signals else 0,
            'metrics': self.metrics
        }
    
    def reset(self) -> None:
        """重置策略状态"""
        self.position = 0
        self.entry_price = 0.0
        self.equity = self.config.get('initial_capital', 10000.0)
        self.trades = []
        self.signals = []
        self.metrics = {}
        self.initialized = False
        logger.info(f"策略 '{self.name}' 已重置")