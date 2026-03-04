#!/usr/bin/env python3
"""
最简单的测试
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建简单的测试数据
def create_simple_data():
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # 创建有明显趋势和波动的价格
    np.random.seed(42)
    
    # 基础趋势
    trend = np.linspace(0, 0.3, len(dates))  # 30%上涨
    
    # 添加周期性波动
    price = 50000 * np.exp(trend)
    
    # 每20天添加一个明显的回调
    for i in range(len(dates)):
        if i % 20 == 10:  # 在第10、30、50、70、90天回调
            # 回调8-12%
            pullback = np.random.uniform(0.08, 0.12)
            for j in range(i, min(i+3, len(dates))):
                price[j] *= (1 - pullback * (1 - (j-i)/3))
    
    # 创建DataFrame
    df = pd.DataFrame(index=dates)
    df['close'] = price
    
    # 生成OHLC数据
    df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.01, len(dates)))
    df['open'].iloc[0] = 50000
    
    # 生成high/low
    for i in range(len(df)):
        current = df.iloc[i]['close']
        open_price = df.iloc[i]['open']
        
        # 日波动2-4%
        daily_range = current * np.random.uniform(0.02, 0.04)
        high = max(open_price, current) + daily_range * 0.3
        low = min(open_price, current) - daily_range * 0.3
        
        df.loc[df.index[i], 'high'] = high
        df.loc[df.index[i], 'low'] = low
    
    # 成交量
    df['volume'] = 1000 * (1 + np.abs(df['close'].pct_change()) * 20)
    df['volume'].iloc[0] = 1000
    
    return df

# 测试简单策略
def test_simple_mean_reversion():
    print("测试简单均值回归策略")
    print("=" * 50)
    
    # 创建数据
    df = create_simple_data()
    print(f"数据范围: {len(df)} 天")
    print(f"价格: ${df['close'].iloc[0]:.0f} -> ${df['close'].iloc[-1]:.0f}")
    print(f"涨幅: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1):.1%}")
    
    # 简单策略：价格低于20日均线时买入，高于时卖出
    df['ma20'] = df['close'].rolling(20).mean()
    
    # 生成信号
    df['signal'] = 0
    df.loc[df['close'] < df['ma20'] * 0.98, 'signal'] = 1  # 低于均线2%买入
    df.loc[df['close'] > df['ma20'] * 1.02, 'signal'] = -1  # 高于均线2%卖出
    
    # 统计信号
    buy_signals = (df['signal'] == 1).sum()
    sell_signals = (df['signal'] == -1).sum()
    
    print(f"\n信号统计:")
    print(f"买入信号: {buy_signals}")
    print(f"卖出信号: {sell_signals}")
    
    # 简单回测
    capital = 100000
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(20, len(df)):  # 从第20天开始（确保有MA20）
        price = df['close'].iloc[i]
        signal = df['signal'].iloc[i]
        
        if signal == 1 and position == 0:  # 买入
            # 买入10%仓位
            position_value = capital * 0.1
            position = position_value / price
            capital -= position_value
            entry_price = price
            
            trades.append({
                'type': 'BUY',
                'day': i,
                'price': price,
                'position': position
            })
            
        elif signal == -1 and position > 0:  # 卖出
            # 卖出
            sell_value = position * price
            capital += sell_value
            pnl = sell_value - (position * entry_price)
            pnl_pct = (price / entry_price - 1)
            
            trades.append({
                'type': 'SELL',
                'day': i,
                'price': price,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
            position = 0
    
    # 最后平仓
    if position > 0:
        sell_value = position * df['close'].iloc[-1]
        capital += sell_value
        pnl = sell_value - (position * entry_price)
        trades.append({
            'type': 'SELL_FINAL',
            'price': df['close'].iloc[-1],
            'pnl': pnl
        })
    
    print(f"\n回测结果:")
    print(f"初始资金: $100,000")
    print(f"最终资金: ${capital:,.0f}")
    print(f"总收益率: {(capital/100000 - 1):.2%}")
    print(f"交易次数: {len([t for t in trades if t['type'] in ['SELL', 'SELL_FINAL']])}")
    
    if trades:
        print(f"\n交易记录:")
        for trade in trades[-5:]:  # 显示最后5笔
            if trade['type'] == 'BUY':
                print(f"  买入 @ ${trade['price']:.0f}, 仓位: {trade['position']:.4f}")
            elif trade['type'] == 'SELL':
                print(f"  卖出 @ ${trade['price']:.0f}, 盈利: ${trade['pnl']:,.0f} ({trade['pnl_pct']:.2%})")
    
    # 对比基准
    buy_hold = df['close'].iloc[-1] / df['close'].iloc[0] - 1
    strategy_return = capital/100000 - 1
    
    print(f"\n策略对比:")
    print(f"买入持有: {buy_hold:.2%}")
    print(f"CTA策略: {strategy_return:.2%}")
    
    if strategy_return > buy_hold:
        print(f"✓ 策略表现更好: +{(strategy_return - buy_hold):.2%}")
    else:
        print(f"✗ 策略表现较差: {(strategy_return - buy_hold):.2%}")
    
    return capital

if __name__ == "__main__":
    print("加密货币CTA策略 - 简单测试")
    print("=" * 60)
    
    try:
        test_simple_mean_reversion()
        
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()