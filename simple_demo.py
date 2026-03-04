#!/usr/bin/env python3
"""
简单的CTA策略演示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cta_strategy import CryptoCTAStrategy
from src.data_fetcher import CryptoDataFetcher
import pandas as pd
import numpy as np

def create_trending_data_with_pullbacks():
    """创建有明显趋势和回调的数据"""
    np.random.seed(42)
    
    # 生成日期
    dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
    
    # 创建上升趋势
    base_trend = np.linspace(0, 0.5, len(dates))  # 50%的上升趋势
    
    # 添加周期性回调
    price = 50000 * np.exp(base_trend)
    
    # 添加明显的回调（每20-30天一次）
    for i in range(len(dates)):
        # 每25天左右一个回调
        if i % 25 == 15:
            # 回调5-10%
            pullback = np.random.uniform(0.05, 0.10)
            for j in range(i, min(i+5, len(dates))):
                price[j] *= (1 - pullback * (1 - (j-i)/5))
        
        # 每10天一个小波动
        elif i % 10 == 0:
            price[i] *= (1 + np.random.uniform(-0.03, 0.03))
    
    # 创建DataFrame
    df = pd.DataFrame(index=dates)
    df['close'] = price
    
    # 生成OHLC数据
    df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.01, len(dates)))
    df['open'].iloc[0] = 50000
    
    # 初始化high/low列
    df['high'] = 0.0
    df['low'] = 0.0
    df['volume'] = 0.0
    
    # 生成high/low（有足够的波动空间）
    for i in range(len(df)):
        current_price = df.iloc[i]['close']
        open_price = df.iloc[i]['open']
        
        # 确保有足够的波动
        daily_range = current_price * 0.03  # 3%的日波动
        df.loc[df.index[i], 'high'] = max(open_price, current_price) + np.random.uniform(0, 1) * daily_range
        df.loc[df.index[i], 'low'] = min(open_price, current_price) - np.random.uniform(0, 1) * daily_range
    
    # 成交量（在回调时放大）
    df['volume'] = 1000
    for i in range(len(df)):
        if i > 0:
            price_change = abs(df.iloc[i]['close'] / df.iloc[i-1]['close'] - 1)
            df.iloc[i, df.columns.get_loc('volume')] = 1000 * (1 + price_change * 10)
    
    return df

def run_simple_strategy():
    """运行简单策略"""
    print("=" * 70)
    print("简单CTA策略演示")
    print("=" * 70)
    
    # 创建数据
    print("\n1. 创建测试数据...")
    df = create_trending_data_with_pullbacks()
    print(f"数据范围: {len(df)} 天")
    print(f"起始价格: ${df['close'].iloc[0]:.0f}")
    print(f"结束价格: ${df['close'].iloc[-1]:.0f}")
    print(f"总涨幅: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1):.1%}")
    
    # 创建非常简单的策略
    print("\n2. 创建简单策略...")
    
    class SimpleCTAStrategy:
        """极简化的CTA策略"""
        def __init__(self):
            self.position = 0
            self.entry_price = 0
            
        def generate_signals(self, df):
            df = df.copy()
            df['signal'] = 0
            
            # 简单规则：价格低于20日均线时买入，高于时卖出
            df['ma20'] = df['close'].rolling(20).mean()
            df['ma50'] = df['close'].rolling(50).mean()
            
            # 买入：价格低于MA20且趋势向上（MA20 > MA50）
            buy_condition = (df['close'] < df['ma20']) & (df['ma20'] > df['ma50'])
            
            # 卖出：价格高于MA20且趋势向下（MA20 < MA50）
            sell_condition = (df['close'] > df['ma20']) & (df['ma20'] < df['ma50'])
            
            df.loc[buy_condition, 'signal'] = 1
            df.loc[sell_condition, 'signal'] = -1
            
            return df
        
        def run_backtest(self, df, initial_capital=100000):
            df = self.generate_signals(df)
            
            capital = initial_capital
            position = 0
            trades = []
            
            for i in range(50, len(df)):  # 从50开始确保有均线值
                current_price = df['close'].iloc[i]
                signal = df['signal'].iloc[i]
                
                # 如果有买入信号且没有仓位
                if signal == 1 and position == 0:
                    # 买入10%仓位
                    position_value = capital * 0.1
                    position = position_value / current_price
                    capital -= position_value
                    self.entry_price = current_price
                    
                    trades.append({
                        'type': 'BUY',
                        'price': current_price,
                        'position': position,
                        'capital': capital
                    })
                
                # 如果有卖出信号且有仓位
                elif signal == -1 and position > 0:
                    # 卖出
                    sell_value = position * current_price
                    capital += sell_value
                    pnl = sell_value - (position * self.entry_price)
                    
                    trades.append({
                        'type': 'SELL',
                        'price': current_price,
                        'pnl': pnl,
                        'pnl_pct': (current_price / self.entry_price - 1),
                        'capital': capital
                    })
                    
                    position = 0
            
            # 最后平仓
            if position > 0:
                sell_value = position * df['close'].iloc[-1]
                capital += sell_value
            
            return {
                'final_capital': capital,
                'initial_capital': initial_capital,
                'total_return': (capital - initial_capital) / initial_capital,
                'trades': trades
            }
    
    # 运行策略
    print("\n3. 运行回测...")
    strategy = SimpleCTAStrategy()
    results = strategy.run_backtest(df)
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:,.2f}")
    print(f"最终资金: ${results['final_capital']:,.2f}")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"交易次数: {len(results['trades'])}")
    
    # 显示交易详情
    if results['trades']:
        print(f"\n交易记录:")
        for i, trade in enumerate(results['trades'][-5:], 1):  # 显示最后5笔
            if trade['type'] == 'BUY':
                print(f"  买入 @ ${trade['price']:.0f}, 仓位: {trade['position']:.4f}, 剩余资金: ${trade['capital']:,.0f}")
            else:
                print(f"  卖出 @ ${trade['price']:.0f}, 盈利: ${trade['pnl']:,.0f} ({trade['pnl_pct']:.2%}), "
                      f"总资金: ${trade['capital']:,.0f}")
    
    # 对比买入持有策略
    print(f"\n4. 对比买入持有策略:")
    buy_hold_return = df['close'].iloc[-1] / df['close'].iloc[0] - 1
    print(f"买入持有收益率: {buy_hold_return:.2%}")
    
    if results['total_return'] > buy_hold_return:
        print(f"✓ 策略跑赢买入持有: +{(results['total_return'] - buy_hold_return):.2%}")
    else:
        print(f"✗ 策略跑输买入持有: {(results['total_return'] - buy_hold_return):.2%}")
    
    return results

def demonstrate_full_strategy_with_examples():
    """用具体示例演示完整策略"""
    print("\n" + "=" * 70)
    print("完整策略示例演示")
    print("=" * 70)
    
    # 创建有明显模式的测试数据
    np.random.seed(123)
    
    # 模拟一个完整的市场周期：上涨->盘整->下跌->反弹
    dates = pd.date_range(start='2024-01-01', periods=150, freq='D')
    
    # 阶段1: 上涨 (50天)
    phase1 = np.linspace(0, 0.3, 50)  # 30%上涨
    # 阶段2: 盘整 (30天)
    phase2 = np.linspace(0.3, 0.25, 30)  # 小幅回调
    # 阶段3: 下跌 (40天)
    phase3 = np.linspace(0.25, -0.1, 40)  # 下跌35%
    # 阶段4: 反弹 (30天)
    phase4 = np.linspace(-0.1, 0.1, 30)  # 反弹20%
    
    trend = np.concatenate([phase1, phase2, phase3, phase4])
    
    # 添加噪声
    noise = np.random.normal(0, 0.02, len(dates))
    cumulative_trend = trend + np.cumsum(noise) * 0.1
    
    # 计算价格
    price = 50000 * np.exp(cumulative_trend)
    
    # 创建DataFrame
    df = pd.DataFrame(index=dates)
    df['close'] = price
    
    # 生成OHLCV数据
    df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.01, len(dates)))
    df['open'].iloc[0] = 50000
    
    for i in range(len(df)):
        current_price = df.iloc[i]['close']
        open_price = df.iloc[i]['open']
        
        # 波动率随趋势变化
        volatility = 0.02 + abs(trend[i]) * 0.03 if i < len(trend) else 0.02
        
        df.iloc[i, df.columns.get_loc('high')] = max(open_price, current_price) * (1 + np.random.uniform(0, volatility))
        df.iloc[i, df.columns.get_loc('low')] = min(open_price, current_price) * (1 - np.random.uniform(0, volatility))
        
        # 成交量：在转折点放大
        if i > 0:
            price_change = abs(current_price / df.iloc[i-1]['close'] - 1)
            df.iloc[i, df.columns.get_loc('volume')] = 1000 * (1 + price_change * 15 + abs(trend[i]) * 5)
        else:
            df.iloc[i, df.columns.get_loc('volume')] = 1000
    
    # 使用完整策略
    print("\n使用完整CTA策略...")
    strategy = CryptoCTAStrategy(
        fast_period=15,
        slow_period=40,
        rsi_period=10,
        bb_period=20,
        bb_std=1.8,
        position_size=0.12,
        stop_loss_pct=0.018,
        take_profit_pct=0.03
    )
    
    # 生成信号
    df_with_signals = strategy.generate_signals(df)
    
    # 统计信号
    signals = df_with_signals['signal']
    print(f"总信号数: {(signals != 0).sum()}")
    print(f"买入信号: {(signals == 1).sum()}")
    print(f"卖出信号: {(signals == -1).sum()}")
    
    # 显示信号示例
    print("\n信号示例:")
    signal_points = df_with_signals[signals != 0].head(10)
    for idx, row in signal_points.iterrows():
        signal_type = "买入" if row['signal'] == 1 else "卖出"
        print(f"  {idx.date()}: {signal_type} @ ${row['close']:.0f}, "
              f"RSI: {row['RSI']:.1f}, 位置: {row['price_position']:.2f}")
    
    # 运行回测
    print("\n运行回测...")
    results = strategy.run_backtest(df, initial_capital=100000)
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:,.2f}")
    print(f"最终资金: ${results['final_capital']:,.2f}")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"交易次数: {results['total_trades']}")
    
    if results['total_trades'] > 0:
        metrics = strategy.calculate_metrics(results)
        
        print(f"\n性能指标:")
        print(f"年化收益率: {metrics.get('年化收益率', 0):.2%}")
        print(f"夏普比率: {metrics.get('夏普比率', 0):.2f}")
        print(f"最大回撤: {metrics.get('最大回撤', 0):.2%}")
        print(f"胜率: {metrics.get('胜率', 0):.2%}")
        
        # 显示交易统计
        trades = results['trades']
        if not trades.empty:
            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] <= 0]
            
            print(f"\n交易统计:")
            print(f"盈利交易: {len(winning_trades)}笔, 总盈利: ${winning_trades['pnl'].sum():,.0f}")
            print(f"亏损交易: {len(losing_trades)}笔, 总亏损: ${losing_trades['pnl'].sum():,.0f}")
            print(f"平均持仓时间: {trades['hold_time'].mean():.1f}小时")
    
    return results

if __name__ == "__main__":
    print("加密货币CTA策略实战演示")
    print("=" * 70)
    
    try:
        # 运行简单策略演示
        run_simple_strategy()
        
        # 运行完整策略演示
        demonstrate_full_strategy_with_examples()
        
        print("\n" + "=" * 70)
        print("演示完成!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()