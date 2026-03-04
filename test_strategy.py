#!/usr/bin/env python3
"""
测试CTA策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cta_strategy import CryptoCTAStrategy
from src.data_fetcher import CryptoDataFetcher
import pandas as pd
import numpy as np

def test_basic_functionality():
    """测试基本功能"""
    print("测试CTA策略基本功能...")
    
    # 1. 创建策略
    strategy = CryptoCTAStrategy()
    print("✓ 策略创建成功")
    
    # 2. 生成模拟数据
    fetcher = CryptoDataFetcher()
    df = fetcher.generate_sample_data(days=100, start_price=50000)
    print(f"✓ 生成 {len(df)} 条模拟数据")
    
    # 3. 计算指标
    df_with_indicators = strategy.calculate_indicators(df)
    required_indicators = ['MA_fast', 'MA_slow', 'RSI', 'BB_upper', 'BB_lower', 'ATR']
    for indicator in required_indicators:
        if indicator in df_with_indicators.columns:
            print(f"✓ 指标 {indicator} 计算成功")
        else:
            print(f"✗ 指标 {indicator} 缺失")
    
    # 4. 生成信号
    df_with_signals = strategy.generate_signals(df)
    if 'signal' in df_with_signals.columns and 'signal_filtered' in df_with_signals.columns:
        signal_counts = df_with_signals['signal'].value_counts()
        print(f"✓ 信号生成成功: {dict(signal_counts)}")
    else:
        print("✗ 信号生成失败")
    
    # 5. 测试仓位计算
    capital = 100000
    current_price = 50000
    atr = 1000
    position_qty, position_value = strategy.calculate_position_sizing(capital, current_price, atr)
    print(f"✓ 仓位计算成功: 数量={position_qty:.4f}, 价值=${position_value:.2f}")
    
    # 6. 运行简单回测
    print("\n运行简单回测...")
    results = strategy.run_backtest(df, initial_capital=100000)
    
    if 'equity_curve' in results and 'trades' in results:
        print(f"✓ 回测运行成功")
        print(f"  初始资金: ${results['initial_capital']:,.2f}")
        print(f"  最终资金: ${results['final_capital']:,.2f}")
        print(f"  总收益率: {results['total_return']:.2%}")
        print(f"  总交易次数: {results['total_trades']}")
    else:
        print("✗ 回测失败")
    
    # 7. 计算指标
    metrics = strategy.calculate_metrics(results)
    if metrics:
        print(f"\n✓ 指标计算成功")
        print(f"  夏普比率: {metrics.get('夏普比率', 0):.2f}")
        print(f"  最大回撤: {metrics.get('最大回撤', 0):.2%}")
        print(f"  胜率: {metrics.get('胜率', 0):.2%}")
    else:
        print("✗ 指标计算失败")
    
    return True

def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况...")
    
    strategy = CryptoCTAStrategy()
    fetcher = CryptoDataFetcher()
    
    # 1. 空数据
    try:
        empty_df = pd.DataFrame()
        strategy.generate_signals(empty_df)
        print("✗ 空数据测试失败 - 应该抛出异常")
    except:
        print("✓ 空数据处理正确")
    
    # 2. 单行数据
    single_data = pd.DataFrame({
        'open': [50000], 'high': [51000], 'low': [49000], 
        'close': [50500], 'volume': [1000]
    }, index=[pd.Timestamp('2024-01-01')])
    
    try:
        strategy.generate_signals(single_data)
        print("✓ 单行数据处理正确")
    except Exception as e:
        print(f"✗ 单行数据处理失败: {e}")
    
    # 3. 异常值数据
    outlier_data = fetcher.generate_sample_data(days=10, start_price=50000)
    outlier_data.loc[outlier_data.index[5], 'close'] = 1000000  # 极端价格
    outlier_data.loc[outlier_data.index[6], 'volume'] = 0  # 零成交量
    
    try:
        df_with_signals = strategy.generate_signals(outlier_data)
        print("✓ 异常值数据处理正确")
    except Exception as e:
        print(f"✗ 异常值数据处理失败: {e}")
    
    return True

def test_strategy_variations():
    """测试不同策略参数"""
    print("\n测试不同策略参数...")
    
    fetcher = CryptoDataFetcher()
    df = fetcher.generate_sample_data(days=200, start_price=50000)
    
    # 测试不同参数组合
    param_sets = [
        {'name': '保守型', 'position_size': 0.05, 'stop_loss_pct': 0.01},
        {'name': '激进型', 'position_size': 0.2, 'stop_loss_pct': 0.03},
        {'name': '短线型', 'fast_period': 10, 'slow_period': 30},
        {'name': '长线型', 'fast_period': 30, 'slow_period': 100}
    ]
    
    results = []
    for params in param_sets:
        print(f"\n测试 {params['name']} 策略...")
        
        # 创建策略
        strategy_params = {
            'fast_period': 20,
            'slow_period': 50,
            'rsi_period': 14,
            'position_size': 0.1,
            'stop_loss_pct': 0.02
        }
        strategy_params.update(params)
        
        # 移除name参数
        strategy_params_copy = strategy_params.copy()
        if 'name' in strategy_params_copy:
            del strategy_params_copy['name']
        
        strategy = CryptoCTAStrategy(**strategy_params_copy)
        
        # 运行回测
        backtest_results = strategy.run_backtest(df, initial_capital=100000)
        metrics = strategy.calculate_metrics(backtest_results)
        
        if metrics:
            results.append({
                'name': params['name'],
                'total_return': metrics.get('总收益率', 0),
                'sharpe': metrics.get('夏普比率', 0),
                'max_dd': metrics.get('最大回撤', 0),
                'win_rate': metrics.get('胜率', 0)
            })
            
            print(f"  总收益率: {metrics.get('总收益率', 0):.2%}")
            print(f"  夏普比率: {metrics.get('夏普比率', 0):.2f}")
            print(f"  最大回撤: {metrics.get('最大回撤', 0):.2%}")
    
    # 显示比较结果
    if results:
        print("\n" + "=" * 60)
        print("策略参数比较")
        print("=" * 60)
        
        results_df = pd.DataFrame(results)
        print(results_df.to_string(index=False))
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("CTA策略测试套件")
    print("=" * 60)
    
    try:
        # 运行测试
        test_basic_functionality()
        test_edge_cases()
        test_strategy_variations()
        
        print("\n" + "=" * 60)
        print("所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)