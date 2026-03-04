#!/usr/bin/env python3
"""
演示CTA策略的实际运行
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cta_strategy import CryptoCTAStrategy
from src.data_fetcher import CryptoDataFetcher
import pandas as pd
import numpy as np

def create_more_volatile_data():
    """创建更具波动性的数据以产生更多交易信号"""
    fetcher = CryptoDataFetcher()
    
    # 生成基础数据
    df = fetcher.generate_sample_data(days=365, start_price=50000)
    
    # 添加更多波动性
    np.random.seed(42)
    
    # 添加周期性波动
    for i in range(len(df)):
        # 每30天添加一个较大的波动
        if i % 30 == 15:
            df.iloc[i, df.columns.get_loc('close')] *= (1 + np.random.uniform(-0.15, 0.15))
        
        # 每10天添加一个中等波动
        elif i % 10 == 5:
            df.iloc[i, df.columns.get_loc('close')] *= (1 + np.random.uniform(-0.08, 0.08))
    
    # 重新计算high/low
    for i in range(len(df)):
        current_price = df.iloc[i]['close']
        df.iloc[i, df.columns.get_loc('high')] = max(df.iloc[i]['open'], current_price) * 1.02
        df.iloc[i, df.columns.get_loc('low')] = min(df.iloc[i]['open'], current_price) * 0.98
    
    return df

def demo_strategy_with_aggressive_params():
    """使用更积极的参数演示策略"""
    print("=" * 70)
    print("CTA策略演示 - 积极参数")
    print("=" * 70)
    
    # 创建更具波动性的数据
    print("\n1. 创建模拟数据...")
    df = create_more_volatile_data()
    print(f"数据条数: {len(df)}")
    print(f"价格范围: ${df['close'].min():.0f} - ${df['close'].max():.0f}")
    print(f"价格波动: {(df['close'].max() / df['close'].min() - 1):.1%}")
    
    # 使用更积极的策略参数
    print("\n2. 创建策略（积极参数）...")
    strategy = CryptoCTAStrategy(
        fast_period=10,       # 更短的快速均线
        slow_period=30,       # 更短的慢速均线
        rsi_period=10,        # 更短的RSI周期
        bb_period=20,
        bb_std=1.5,           # 更窄的布林带
        atr_period=10,
        volume_threshold=1.1, # 更低的成交量阈值
        position_size=0.15,   # 更大的仓位
        stop_loss_pct=0.015,  # 更紧的止损
        take_profit_pct=0.03  # 更紧的止盈
    )
    
    # 生成信号
    print("\n3. 生成交易信号...")
    df_with_signals = strategy.generate_signals(df)
    
    # 统计信号
    total_signals = (df_with_signals['signal'] != 0).sum()
    buy_signals = (df_with_signals['signal'] == 1).sum()
    sell_signals = (df_with_signals['signal'] == -1).sum()
    
    print(f"总信号数: {total_signals}")
    print(f"买入信号: {buy_signals}")
    print(f"卖出信号: {sell_signals}")
    
    if total_signals == 0:
        print("警告: 没有生成交易信号，调整策略参数...")
        # 显示一些指标值
        print("\n指标统计:")
        print(f"RSI范围: {df_with_signals['RSI'].min():.1f} - {df_with_signals['RSI'].max():.1f}")
        print(f"价格位置: {df_with_signals['price_position'].min():.3f} - {df_with_signals['price_position'].max():.3f}")
        print(f"成交量比率: {df_with_signals['volume_ratio'].min():.2f} - {df_with_signals['volume_ratio'].max():.2f}")
    
    # 运行回测
    print("\n4. 运行回测...")
    results = strategy.run_backtest(df, initial_capital=100000)
    
    print(f"\n回测结果:")
    print(f"初始资金: ${results['initial_capital']:,.2f}")
    print(f"最终资金: ${results['final_capital']:,.2f}")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"总交易次数: {results['total_trades']}")
    
    # 计算详细指标
    if results['total_trades'] > 0:
        metrics = strategy.calculate_metrics(results)
        
        print(f"\n详细指标:")
        print(f"年化收益率: {metrics.get('年化收益率', 0):.2%}")
        print(f"夏普比率: {metrics.get('夏普比率', 0):.2f}")
        print(f"最大回撤: {metrics.get('最大回撤', 0):.2%}")
        print(f"胜率: {metrics.get('胜率', 0):.2%}")
        print(f"平均盈利: {metrics.get('平均盈利', 0):.2%}")
        print(f"平均亏损: {metrics.get('平均亏损', 0):.2%}")
        print(f"盈亏比: {metrics.get('盈亏比', 0):.2f}")
        
        # 显示交易记录
        trades = results['trades']
        if not trades.empty:
            print(f"\n最近5笔交易:")
            recent_trades = trades.tail(5)
            for _, trade in recent_trades.iterrows():
                print(f"  {trade['side'].upper():4s} | 入场: {trade['entry_price']:.0f} | "
                      f"出场: {trade['exit_price']:.0f} | PnL: {trade['pnl']:.2f} ({trade['pnl_pct']:.2%}) | "
                      f"原因: {trade['exit_reason']}")
    
    return results

def demo_multiple_strategies():
    """演示多个策略版本"""
    print("\n" + "=" * 70)
    print("多策略比较演示")
    print("=" * 70)
    
    # 创建数据
    fetcher = CryptoDataFetcher()
    df = create_more_volatile_data()
    
    # 定义不同策略
    strategies = [
        {
            'name': '保守趋势跟踪',
            'params': {
                'fast_period': 20,
                'slow_period': 50,
                'rsi_period': 14,
                'position_size': 0.1,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04
            }
        },
        {
            'name': '积极均值回归',
            'params': {
                'fast_period': 10,
                'slow_period': 30,
                'rsi_period': 10,
                'bb_std': 1.5,
                'position_size': 0.15,
                'stop_loss_pct': 0.015,
                'take_profit_pct': 0.03
            }
        },
        {
            'name': '平衡混合策略',
            'params': {
                'fast_period': 15,
                'slow_period': 40,
                'rsi_period': 12,
                'bb_std': 1.8,
                'position_size': 0.12,
                'stop_loss_pct': 0.018,
                'take_profit_pct': 0.035
            }
        }
    ]
    
    results = []
    
    for strategy_info in strategies:
        print(f"\n测试策略: {strategy_info['name']}")
        print("-" * 40)
        
        # 创建策略
        strategy = CryptoCTAStrategy(**strategy_info['params'])
        
        # 运行回测
        backtest_results = strategy.run_backtest(df, initial_capital=100000)
        metrics = strategy.calculate_metrics(backtest_results)
        
        if metrics:
            results.append({
                '策略名称': strategy_info['name'],
                '总收益率': f"{metrics.get('总收益率', 0):.2%}",
                '年化收益率': f"{metrics.get('年化收益率', 0):.2%}",
                '夏普比率': f"{metrics.get('夏普比率', 0):.2f}",
                '最大回撤': f"{metrics.get('最大回撤', 0):.2%}",
                '胜率': f"{metrics.get('胜率', 0):.2%}",
                '交易次数': metrics.get('总交易次数', 0)
            })
            
            print(f"总收益率: {metrics.get('总收益率', 0):.2%}")
            print(f"夏普比率: {metrics.get('夏普比率', 0):.2f}")
            print(f"最大回撤: {metrics.get('最大回撤', 0):.2%}")
            print(f"交易次数: {metrics.get('总交易次数', 0)}")
    
    # 显示比较表格
    if results:
        print("\n" + "=" * 70)
        print("策略比较结果")
        print("=" * 70)
        
        results_df = pd.DataFrame(results)
        print(results_df.to_string(index=False))
    
    return results

if __name__ == "__main__":
    print("加密货币CTA策略演示系统")
    print("=" * 70)
    
    try:
        # 演示单个策略
        demo_strategy_with_aggressive_params()
        
        # 演示多策略比较
        demo_multiple_strategies()
        
        print("\n" + "=" * 70)
        print("演示完成!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()