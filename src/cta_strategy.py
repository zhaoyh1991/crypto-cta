"""
稳健的加密货币CTA策略
结合趋势跟踪和均值回归，实现稳定盈利
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class CryptoCTAStrategy:
    """
    多因子CTA策略类
    结合以下因子：
    1. 双均线趋势跟踪
    2. RSI均值回归
    3. 布林带突破
    4. ATR波动率过滤
    5. 成交量确认
    """
    
    def __init__(self, 
                 fast_period=20,      # 快速均线周期
                 slow_period=50,      # 慢速均线周期
                 rsi_period=14,       # RSI周期
                 bb_period=20,        # 布林带周期
                 bb_std=2.0,          # 布林带标准差
                 atr_period=14,       # ATR周期
                 volume_threshold=1.2, # 成交量阈值
                 position_size=0.1,   # 仓位大小（占总资金比例）
                 stop_loss_pct=0.02,  # 止损百分比
                 take_profit_pct=0.04 # 止盈百分比
                ):
        
        # 策略参数
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period
        self.volume_threshold = volume_threshold
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # 状态变量
        self.position = 0  # 当前仓位：1=多头，-1=空头，0=空仓
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        
    def calculate_indicators(self, df):
        """
        计算所有技术指标
        """
        df = df.copy()
        
        # 1. 移动平均线
        df['MA_fast'] = df['close'].rolling(window=self.fast_period).mean()
        df['MA_slow'] = df['close'].rolling(window=self.slow_period).mean()
        
        # 2. RSI指标
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 3. 布林带
        df['BB_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * self.bb_std)
        df['BB_lower'] = df['BB_middle'] - (bb_std * self.bb_std)
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        
        # 4. ATR（平均真实波幅）
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=self.atr_period).mean()
        
        # 5. 成交量指标
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 6. 价格动量
        df['momentum'] = df['close'].pct_change(periods=10)
        
        # 7. 价格位置（相对于布林带）
        df['price_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        return df
    
    def generate_signals(self, df):
        """
        生成交易信号
        返回：1=买入，-1=卖出，0=持有
        """
        df = self.calculate_indicators(df)
        
        # 初始化信号列
        df['signal'] = 0
        
        # 条件1：趋势方向（双均线）
        trend_up = df['MA_fast'] > df['MA_slow']
        trend_down = df['MA_fast'] < df['MA_slow']
        
        # 条件2：RSI超买超卖
        rsi_oversold = df['RSI'] < 30
        rsi_overbought = df['RSI'] > 70
        
        # 条件3：布林带突破
        bb_breakout_up = df['close'] > df['BB_upper']
        bb_breakout_down = df['close'] < df['BB_lower']
        
        # 条件4：成交量确认
        volume_confirmed = df['volume_ratio'] > self.volume_threshold
        
        # 条件5：波动率过滤（避免在低波动时交易）
        volatility_ok = df['ATR'] / df['close'] > 0.005
        
        # 生成买入信号（多头） - 放宽条件
        buy_conditions = (
            (trend_up | (df['price_position'] < 0.3)) &  # 趋势向上或价格在布林带低位
            (rsi_oversold | (df['RSI'] < 40)) &          # RSI超卖或较低
            (bb_breakout_down | (df['price_position'] < 0.2)) &  # 触及下轨或在低位
            (volume_confirmed | (df['volume_ratio'] > 0.8)) &    # 成交量确认或正常
            volatility_ok                                 # 波动率合适
        )
        
        # 生成卖出信号（空头） - 放宽条件
        sell_conditions = (
            (trend_down | (df['price_position'] > 0.7)) &  # 趋势向下或价格在布林带高位
            (rsi_overbought | (df['RSI'] > 60)) &          # RSI超买或较高
            (bb_breakout_up | (df['price_position'] > 0.8)) &    # 触及上轨或在高位
            (volume_confirmed | (df['volume_ratio'] > 0.8)) &    # 成交量确认或正常
            volatility_ok                                 # 波动率合适
        )
        
        # 应用信号
        df.loc[buy_conditions, 'signal'] = 1
        df.loc[sell_conditions, 'signal'] = -1
        
        # 信号过滤：避免频繁交易
        df['signal_filtered'] = 0
        signal_changes = df['signal'].diff().fillna(0)
        
        # 只在信号变化时交易
        for i in range(1, len(df)):
            if signal_changes.iloc[i] != 0:
                df.loc[df.index[i], 'signal_filtered'] = df['signal'].iloc[i]
        
        return df
    
    def calculate_position_sizing(self, capital, current_price, atr):
        """
        根据凯利公式和波动率计算仓位大小
        """
        # 基础仓位
        base_position = capital * self.position_size
        
        # 根据波动率调整（波动率越高，仓位越小）
        volatility_adj = 0.01 / (atr / current_price) if atr > 0 else 1
        volatility_adj = np.clip(volatility_adj, 0.5, 2.0)
        
        # 最终仓位
        position_value = base_position * volatility_adj
        
        # 计算数量
        position_qty = position_value / current_price
        
        return position_qty, position_value
    
    def run_backtest(self, df, initial_capital=100000):
        """
        运行回测
        """
        print("开始回测...")
        
        # 生成信号
        df = self.generate_signals(df)
        
        # 初始化回测变量
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = []
        
        for i in range(max(self.slow_period, self.bb_period, self.atr_period), len(df)):
            current_data = df.iloc[i]
            current_price = current_data['close']
            current_time = df.index[i]
            
            # 计算当前权益
            current_equity = capital + (position * current_price)
            equity_curve.append({
                'timestamp': current_time,
                'equity': current_equity,
                'price': current_price
            })
            
            # 检查止损止盈
            if position != 0:
                # 计算盈亏比例
                if position > 0:  # 多头
                    pnl_pct = (current_price - self.entry_price) / self.entry_price
                    hit_stop_loss = current_price <= self.stop_loss
                    hit_take_profit = current_price >= self.take_profit
                else:  # 空头
                    pnl_pct = (self.entry_price - current_price) / self.entry_price
                    hit_stop_loss = current_price >= self.stop_loss
                    hit_take_profit = current_price <= self.take_profit
                
                # 执行止损止盈
                if hit_stop_loss or hit_take_profit:
                    # 平仓
                    exit_reason = '止损' if hit_stop_loss else '止盈'
                    exit_price = self.stop_loss if hit_stop_loss else self.take_profit
                    
                    # 计算收益
                    if position > 0:
                        pnl = (exit_price - self.entry_price) * abs(position)
                    else:
                        pnl = (self.entry_price - exit_price) * abs(position)
                    
                    capital += pnl
                    
                    trades.append({
                        'entry_time': self.entry_time,
                        'exit_time': current_time,
                        'side': 'long' if position > 0 else 'short',
                        'entry_price': self.entry_price,
                        'exit_price': exit_price,
                        'position': abs(position),
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason
                    })
                    
                    position = 0
                    self.entry_price = 0
                    self.stop_loss = 0
                    self.take_profit = 0
            
            # 生成新信号
            signal = current_data['signal_filtered']
            
            # 如果有信号且当前没有仓位
            if signal != 0 and position == 0:
                # 计算仓位大小
                position_qty, position_value = self.calculate_position_sizing(
                    capital, current_price, current_data['ATR']
                )
                
                if position_value < capital * 0.95:  # 确保有足够资金
                    position = position_qty if signal == 1 else -position_qty
                    self.entry_price = current_price
                    self.entry_time = current_time
                    
                    # 设置止损止盈
                    if signal == 1:  # 多头
                        self.stop_loss = current_price * (1 - self.stop_loss_pct)
                        self.take_profit = current_price * (1 + self.take_profit_pct)
                    else:  # 空头
                        self.stop_loss = current_price * (1 + self.stop_loss_pct)
                        self.take_profit = current_price * (1 - self.take_profit_pct)
        
        # 处理最后未平仓的仓位
        if position != 0:
            last_price = df.iloc[-1]['close']
            if position > 0:
                pnl = (last_price - self.entry_price) * abs(position)
            else:
                pnl = (self.entry_price - last_price) * abs(position)
            
            capital += pnl
            
            trades.append({
                'entry_time': self.entry_time,
                'exit_time': df.index[-1],
                'side': 'long' if position > 0 else 'short',
                'entry_price': self.entry_price,
                'exit_price': last_price,
                'position': abs(position),
                'pnl': pnl,
                'pnl_pct': (last_price - self.entry_price) / self.entry_price if position > 0 else (self.entry_price - last_price) / self.entry_price,
                'exit_reason': '最后平仓'
            })
        
        # 创建回测结果
        equity_df = pd.DataFrame(equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        
        return {
            'equity_curve': equity_df,
            'trades': trades_df,
            'final_capital': capital,
            'initial_capital': initial_capital,
            'total_return': (capital - initial_capital) / initial_capital,
            'total_trades': len(trades)
        }
    
    def calculate_metrics(self, backtest_results):
        """
        计算策略性能指标
        """
        equity_curve = backtest_results['equity_curve']
        trades = backtest_results['trades']
        initial_capital = backtest_results['initial_capital']
        final_capital = backtest_results['final_capital']
        
        if len(equity_curve) == 0:
            return {}
        
        # 计算收益率序列
        equity_curve['returns'] = equity_curve['equity'].pct_change().fillna(0)
        
        # 总收益率
        total_return = backtest_results['total_return']
        
        # 年化收益率
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = max(days / 365.25, 0.001)
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 年化波动率
        annual_volatility = equity_curve['returns'].std() * np.sqrt(252)
        
        # 夏普比率（假设无风险利率为2%）
        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['cummax']) / equity_curve['cummax']
        max_drawdown = equity_curve['drawdown'].min()
        
        # 卡玛比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
        
        # 索提诺比率
        negative_returns = equity_curve['returns'][equity_curve['returns'] < 0]
        downside_std = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = (annual_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # 交易统计
        if len(trades) > 0:
            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] <= 0]
            
            win_rate = len(winning_trades) / len(trades) if len(trades) > 0 else 0
            avg_win = winning_trades['pnl_pct'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl_pct'].mean() if len(losing_trades) > 0 else 0
            profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if losing_trades['pnl'].sum() != 0 else float('inf')
            
            # 平均持仓时间
            trades['hold_time'] = (trades['exit_time'] - trades['entry_time']).dt.total_seconds() / 3600  # 小时
            avg_hold_time = trades['hold_time'].mean()
        else:
            win_rate = avg_win = avg_loss = profit_factor = avg_hold_time = 0
        
        metrics = {
            '初始资金': initial_capital,
            '最终资金': final_capital,
            '总收益率': total_return,
            '年化收益率': annual_return,
            '年化波动率': annual_volatility,
            '夏普比率': sharpe_ratio,
            '最大回撤': max_drawdown,
            '卡玛比率': calmar_ratio,
            '索提诺比率': sortino_ratio,
            '总交易次数': len(trades),
            '胜率': win_rate,
            '平均盈利': avg_win,
            '平均亏损': avg_loss,
            '盈亏比': profit_factor,
            '平均持仓时间(小时)': avg_hold_time
        }
        
        return metrics