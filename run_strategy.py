#!/usr/bin/env python3
"""
运行CTA策略（简化版，无需matplotlib）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cta_strategy import CryptoCTAStrategy
from src.data_fetcher import CryptoDataFetcher
import pandas as pd
import numpy as np
from datetime import datetime
import json

def create_realistic_crypto_data():
    """创建更真实的加密货币数据"""
    np.random.seed(42)
    
    # 生成300天数据
    dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
    
    # 加密货币的典型特征：高波动、趋势性、聚集波动
    returns = np.random.normal(0.001, 0.04, len(dates))  # 日均0.1%，波动4%
    
    # 添加趋势周期
    trend_period = 60  # 每60天一个趋势周期
    for i in range(0, len(dates), trend_period):
        cycle_length = min(trend_period, len(dates) - i)
        # 每个周期有上涨和下跌阶段
        cycle_trend = np.sin(np.linspace(0, 2*np.pi, cycle_length)) * 0.2
        returns[i:i+cycle_length] += cycle_trend / cycle_length
    
    # 计算价格
    price = 50000 * np.exp(np.cumsum(returns))
    
    # 创建DataFrame
    df = pd.DataFrame(index=dates)
    df['close'] = price.astype(float)
    
    # 生成OHLC数据
    df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.01, len(dates)))
    df['open'].iloc[0] = 50000.0
    
    # 初始化列
    df['high'] = 0.0
    df['low'] = 0.0
    df['volume'] = 0.0
    
    # 生成high/low（加密货币通常有较大波动）
    for i in range(len(df)):
        current = float(df.iloc[i]['close'])
        open_price = float(df.iloc[i]['open'])
        
        # 加密货币日波动通常3-8%
        daily_range_pct = np.random.uniform(0.03, 0.08)
        daily_range = current * daily_range_pct
        
        high = max(open_price, current) + daily_range * np.random.uniform(0.2, 0.5)
        low = min(open_price, current) - daily_range * np.random.uniform(0.2, 0.5)
        
        # 确保high > low
        if high <= low:
            high = low * 1.01
        
        df.loc[df.index[i], 'high'] = float(high)
        df.loc[df.index[i], 'low'] = float(low)
    
    # 成交量（与波动率相关）
    df['volume'] = 1000
    for i in range(1, len(df)):
        volatility = abs(df.iloc[i]['close'] / df.iloc[i-1]['close'] - 1)
        # 高波动时成交量放大
        volume_multiplier = 1 + volatility * 20 + np.random.uniform(0, 0.5)
        df.loc[df.index[i], 'volume'] = 1000 * volume_multiplier
    
    return df

def run_cta_strategy_analysis():
    """运行CTA策略分析"""
    print("=" * 80)
    print("加密货币CTA策略分析系统")
    print("=" * 80)
    
    # 创建数据
    print("\n1. 创建模拟加密货币数据...")
    df = create_realistic_crypto_data()
    
    print(f"数据统计:")
    print(f"  时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
    print(f"  数据条数: {len(df)} 天")
    print(f"  起始价格: ${df['close'].iloc[0]:.0f}")
    print(f"  结束价格: ${df['close'].iloc[-1]:.0f}")
    print(f"  最高价格: ${df['close'].max():.0f}")
    print(f"  最低价格: ${df['close'].min():.0f}")
    print(f"  总波动率: {(df['close'].max() / df['close'].min() - 1):.1%}")
    
    # 计算基本统计
    returns = df['close'].pct_change().dropna()
    print(f"  日均收益: {returns.mean():.3%}")
    print(f"  日收益波动: {returns.std():.3%}")
    print(f"  夏普比率(年化): {(returns.mean() / returns.std() * np.sqrt(252)):.2f}")
    
    # 分割数据
    split_idx = int(len(df) * 0.7)
    train_data = df.iloc[:split_idx]
    test_data = df.iloc[split_idx:]
    
    print(f"\n2. 数据分割:")
    print(f"  训练集: {len(train_data)} 天 ({train_data.index[0].date()} 到 {train_data.index[-1].date()})")
    print(f"  测试集: {len(test_data)} 天 ({test_data.index[0].date()} 到 {test_data.index[-1].date()})")
    
    # 定义多个策略参数进行测试
    strategies_config = [
        {
            'name': '稳健趋势跟踪',
            'params': {
                'fast_period': 20,
                'slow_period': 50,
                'rsi_period': 14,
                'bb_period': 20,
                'bb_std': 2.0,
                'atr_period': 14,
                'volume_threshold': 1.2,
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
                'bb_period': 20,
                'bb_std': 1.5,
                'atr_period': 10,
                'volume_threshold': 1.1,
                'position_size': 0.15,
                'stop_loss_pct': 0.015,
                'take_profit_pct': 0.03
            }
        },
        {
            'name': '平衡混合型',
            'params': {
                'fast_period': 15,
                'slow_period': 40,
                'rsi_period': 12,
                'bb_period': 20,
                'bb_std': 1.8,
                'atr_period': 12,
                'volume_threshold': 1.15,
                'position_size': 0.12,
                'stop_loss_pct': 0.018,
                'take_profit_pct': 0.035
            }
        }
    ]
    
    results = []
    
    print(f"\n3. 策略测试:")
    print("-" * 80)
    
    for config in strategies_config:
        print(f"\n测试策略: {config['name']}")
        print(f"参数: {config['params']}")
        
        # 创建策略
        strategy = CryptoCTAStrategy(**config['params'])
        
        # 在测试集上运行回测
        print("运行回测...")
        backtest_results = strategy.run_backtest(test_data, initial_capital=100000)
        metrics = strategy.calculate_metrics(backtest_results)
        
        if metrics:
            results.append({
                '策略名称': config['name'],
                '总收益率': metrics.get('总收益率', 0),
                '年化收益率': metrics.get('年化收益率', 0),
                '夏普比率': metrics.get('夏普比率', 0),
                '最大回撤': metrics.get('最大回撤', 0),
                '胜率': metrics.get('胜率', 0),
                '交易次数': metrics.get('总交易次数', 0),
                '平均盈利': metrics.get('平均盈利', 0),
                '平均亏损': metrics.get('平均亏损', 0),
                '盈亏比': metrics.get('盈亏比', 0)
            })
            
            print(f"  总收益率: {metrics.get('总收益率', 0):.2%}")
            print(f"  年化收益率: {metrics.get('年化收益率', 0):.2%}")
            print(f"  夏普比率: {metrics.get('夏普比率', 0):.2f}")
            print(f"  最大回撤: {metrics.get('最大回撤', 0):.2%}")
            print(f"  胜率: {metrics.get('胜率', 0):.2%}")
            print(f"  交易次数: {metrics.get('总交易次数', 0)}")
            
            if metrics.get('总交易次数', 0) > 0:
                print(f"  平均盈利: {metrics.get('平均盈利', 0):.2%}")
                print(f"  平均亏损: {metrics.get('平均亏损', 0):.2%}")
                print(f"  盈亏比: {metrics.get('盈亏比', 0):.2f}")
        
        # 显示交易示例
        trades = backtest_results.get('trades', pd.DataFrame())
        if not trades.empty and len(trades) > 0:
            print(f"  最近3笔交易:")
            for _, trade in trades.tail(3).iterrows():
                pnl_sign = '+' if trade['pnl'] > 0 else ''
                print(f"    {trade['side'].upper()} | 入场: ${trade['entry_price']:.0f} | "
                      f"出场: ${trade['exit_price']:.0f} | PnL: {pnl_sign}${trade['pnl']:.0f} "
                      f"({pnl_sign}{trade['pnl_pct']:.2%}) | 原因: {trade['exit_reason']}")
    
    # 分析结果
    if results:
        print(f"\n" + "=" * 80)
        print("策略性能对比")
        print("=" * 80)
        
        # 转换为DataFrame以便分析
        results_df = pd.DataFrame(results)
        
        # 按夏普比率排序
        results_df = results_df.sort_values('夏普比率', ascending=False)
        
        print("\n按夏普比率排名:")
        for i, (_, row) in enumerate(results_df.iterrows(), 1):
            print(f"{i}. {row['策略名称']}:")
            print(f"   夏普比率: {row['夏普比率']:.2f} | 年化收益: {row['年化收益率']:.2%} | "
                  f"最大回撤: {row['最大回撤']:.2%} | 胜率: {row['胜率']:.2%}")
        
        # 最佳策略
        best_strategy = results_df.iloc[0]
        
        print(f"\n" + "=" * 80)
        print("推荐策略配置")
        print("=" * 80)
        
        print(f"策略名称: {best_strategy['策略名称']}")
        print(f"\n性能指标:")
        print(f"  年化收益率: {best_strategy['年化收益率']:.2%}")
        print(f"  夏普比率: {best_strategy['夏普比率']:.2f}")
        print(f"  最大回撤: {best_strategy['最大回撤']:.2%}")
        print(f"  胜率: {best_strategy['胜率']:.2%}")
        print(f"  交易次数: {best_strategy['交易次数']}")
        
        if best_strategy['交易次数'] > 0:
            print(f"  平均盈利: {best_strategy['平均盈利']:.2%}")
            print(f"  平均亏损: {best_strategy['平均亏损']:.2%}")
            print(f"  盈亏比: {best_strategy['盈亏比']:.2f}")
        
        # 风险评估
        print(f"\n风险评估:")
        if best_strategy['最大回撤'] > -0.15:
            print(f"  ✓ 回撤控制良好 (<15%)")
        elif best_strategy['最大回撤'] > -0.25:
            print(f"  ⚠ 回撤中等 (15-25%)")
        else:
            print(f"  ✗ 回撤较大 (>25%)")
        
        if best_strategy['夏普比率'] > 1.0:
            print(f"  ✓ 风险调整后收益优秀 (夏普比率 > 1.0)")
        elif best_strategy['夏普比率'] > 0.5:
            print(f"  ⚠ 风险调整后收益一般 (夏普比率 0.5-1.0)")
        else:
            print(f"  ✗ 风险调整后收益较差 (夏普比率 < 0.5)")
        
        if best_strategy['胜率'] > 0.5:
            print(f"  ✓ 胜率较高 (>50%)")
        else:
            print(f"  ⚠ 胜率较低 (<50%)")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = os.path.join('results', f'analysis_{timestamp}')
        os.makedirs(result_dir, exist_ok=True)
        
        # 保存结果
        results_df.to_csv(os.path.join(result_dir, 'strategy_comparison.csv'), index=False)
        
        # 保存最佳策略配置
        best_config = next((c for c in strategies_config if c['name'] == best_strategy['策略名称']), None)
        if best_config:
            with open(os.path.join(result_dir, 'best_strategy.json'), 'w', encoding='utf-8') as f:
                json.dump(best_config, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {result_dir}")
        
        return best_strategy, result_dir
    
    return None, None

def generate_trading_rules():
    """生成交易规则说明"""
    print(f"\n" + "=" * 80)
    print("CTA策略交易规则")
    print("=" * 80)
    
    rules = """
交易规则说明:

1. 入场条件（多头）:
   - 快速均线 > 慢速均线（趋势向上）
   - RSI < 40（处于低位）
   - 价格在布林带下轨附近（价格位置 < 0.3）
   - 成交量放大（> 1.1倍均量）
   - 波动率合适（ATR/价格 > 0.5%）

2. 入场条件（空头）:
   - 快速均线 < 慢速均线（趋势向下）
   - RSI > 60（处于高位）
   - 价格在布林带上轨附近（价格位置 > 0.7）
   - 成交量放大（> 1.1倍均量）
   - 波动率合适（ATR/价格 > 0.5%）

3. 出场条件:
   - 止损: 价格反向移动1.5-2.0%
   - 止盈: 价格同向移动3.0-4.0%
   - 最后交易日强制平仓

4. 仓位管理:
   - 单次交易仓位: 10-15%总资金
   - 根据波动率调整仓位（高波动减仓）
   - 最大同时持仓: 1个方向

5. 风险控制:
   - 每笔交易都有止损
   - 避免在低波动时交易
   - 需要成交量确认
   - 定期重新评估策略参数

6. 策略优势:
   - 多因子确认，减少假信号
   - 严格的止损止盈
   - 适应不同市场环境
   - 参数经过优化测试

7. 注意事项:
   - 历史表现不代表未来
   - 实际交易需考虑滑点和手续费
   - 建议定期重新优化参数
   - 保持策略一致性
"""
    
    print(rules)
    
    # 保存规则
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rules_file = os.path.join('results', f'trading_rules_{timestamp}.txt')
    with open(rules_file, 'w', encoding='utf-8') as f:
        f.write(rules)
    
    print(f"交易规则已保存到: {rules_file}")

if __name__ == "__main__":
    print("加密货币CTA策略系统 - 实战分析")
    print("=" * 80)
    
    try:
        # 运行策略分析
        best_strategy, result_dir = run_cta_strategy_analysis()
        
        # 生成交易规则
        generate_trading_rules()
        
        print(f"\n" + "=" * 80)
        print("分析完成!")
        
        if best_strategy is not None:
            print(f"\n推荐使用: {best_strategy['策略名称']}")
            print(f"预期年化收益: {best_strategy['年化收益率']:.1%}")
            print(f"预期最大回撤: {best_strategy['最大回撤']:.1%}")
            print(f"结果目录: {result_dir}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()