#!/usr/bin/env python3
"""
加密货币CTA策略主程序
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cta_strategy import CryptoCTAStrategy
from src.data_fetcher import CryptoDataFetcher
from src.backtester import Backtester
import pandas as pd
import numpy as np
from datetime import datetime
import argparse

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='加密货币CTA策略回测系统')
    parser.add_argument('--symbol', type=str, default='BTC-USD', help='交易对符号')
    parser.add_argument('--period', type=str, default='1y', help='数据周期')
    parser.add_argument('--interval', type=str, default='1d', help='数据间隔')
    parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    parser.add_argument('--train-ratio', type=float, default=0.7, help='训练集比例')
    parser.add_argument('--use-sample', action='store_true', help='使用模拟数据')
    parser.add_argument('--data-file', type=str, help='使用本地数据文件')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("加密货币CTA策略回测系统")
    print("=" * 70)
    print(f"交易对: {args.symbol}")
    print(f"数据周期: {args.period}")
    print(f"数据间隔: {args.interval}")
    print(f"初始资金: ${args.capital:,.2f}")
    print(f"训练集比例: {args.train_ratio:.0%}")
    print("=" * 70)
    
    # 1. 初始化组件
    data_fetcher = CryptoDataFetcher(data_dir='data')
    backtester = Backtester(results_dir='results')
    
    # 2. 获取数据
    if args.data_file:
        print(f"\n使用本地数据文件: {args.data_file}")
        df = data_fetcher.load_from_csv(args.data_file)
    elif args.use_sample:
        print("\n使用模拟数据...")
        df = data_fetcher.generate_sample_data(days=365, start_price=50000)
    else:
        print("\n从Yahoo Finance获取数据...")
        df = data_fetcher.fetch_from_yahoo(
            symbol=args.symbol,
            period=args.period,
            interval=args.interval
        )
    
    if df is None or df.empty:
        print("错误: 无法获取数据，使用模拟数据替代")
        df = data_fetcher.generate_sample_data(days=365, start_price=50000)
    
    print(f"\n数据统计:")
    print(f"数据条数: {len(df)}")
    print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
    print(f"价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"平均成交量: {df['volume'].mean():,.0f}")
    
    # 3. 准备数据
    train_data, test_data = data_fetcher.prepare_data(df, train_ratio=args.train_ratio)
    
    # 4. 创建策略（使用稳健参数）
    print("\n初始化CTA策略...")
    strategy = CryptoCTAStrategy(
        fast_period=20,      # 快速均线
        slow_period=50,      # 慢速均线
        rsi_period=14,       # RSI周期
        bb_period=20,        # 布林带周期
        bb_std=2.0,          # 布林带标准差
        atr_period=14,       # ATR周期
        volume_threshold=1.2, # 成交量确认阈值
        position_size=0.1,   # 仓位大小（10%）
        stop_loss_pct=0.02,  # 止损2%
        take_profit_pct=0.04 # 止盈4%
    )
    
    print("策略参数:")
    print(f"  快速均线周期: {strategy.fast_period}")
    print(f"  慢速均线周期: {strategy.slow_period}")
    print(f"  RSI周期: {strategy.rsi_period}")
    print(f"  布林带周期: {strategy.bb_period}")
    print(f"  布林带标准差: {strategy.bb_std}")
    print(f"  ATR周期: {strategy.atr_period}")
    print(f"  仓位大小: {strategy.position_size:.0%}")
    print(f"  止损: {strategy.stop_loss_pct:.1%}")
    print(f"  止盈: {strategy.take_profit_pct:.1%}")
    
    # 5. 运行回测
    print("\n" + "=" * 70)
    print("开始回测...")
    print("=" * 70)
    
    result = backtester.run_complete_backtest(
        strategy=strategy,
        train_data=train_data,
        test_data=test_data,
        initial_capital=args.capital
    )
    
    # 6. 生成总结
    print("\n" + "=" * 70)
    print("回测总结")
    print("=" * 70)
    
    summary = backtester.generate_summary(result)
    
    print(f"\n总体评价: {summary['总体评价']}")
    
    if summary['关键优势']:
        print(f"\n关键优势:")
        for advantage in summary['关键优势']:
            print(f"  ✓ {advantage}")
    
    if summary['潜在风险']:
        print(f"\n潜在风险:")
        for risk in summary['潜在风险']:
            print(f"  ⚠ {risk}")
    
    if summary['改进建议']:
        print(f"\n改进建议:")
        for suggestion in summary['改进建议']:
            print(f"  💡 {suggestion}")
    
    # 7. 显示详细结果
    print("\n" + "=" * 70)
    print("详细结果")
    print("=" * 70)
    
    test_metrics = result['test_metrics']
    
    print(f"\n📊 收益表现:")
    print(f"  初始资金: ${test_metrics.get('初始资金', args.capital):,.2f}")
    print(f"  最终资金: ${test_metrics.get('最终资金', args.capital):,.2f}")
    print(f"  总收益率: {test_metrics.get('总收益率', 0):.2%}")
    print(f"  年化收益率: {test_metrics.get('年化收益率', 0):.2%}")
    
    print(f"\n📈 风险指标:")
    print(f"  年化波动率: {test_metrics.get('年化波动率', 0):.2%}")
    print(f"  夏普比率: {test_metrics.get('夏普比率', 0):.2f}")
    print(f"  最大回撤: {test_metrics.get('最大回撤', 0):.2%}")
    print(f"  卡玛比率: {test_metrics.get('卡玛比率', 0):.2f}")
    print(f"  索提诺比率: {test_metrics.get('索提诺比率', 0):.2f}")
    
    print(f"\n🎯 交易统计:")
    print(f"  总交易次数: {test_metrics.get('总交易次数', 0)}")
    print(f"  胜率: {test_metrics.get('胜率', 0):.2%}")
    print(f"  平均盈利: {test_metrics.get('平均盈利', 0):.2%}")
    print(f"  平均亏损: {test_metrics.get('平均亏损', 0):.2%}")
    print(f"  盈亏比: {test_metrics.get('盈亏比', 0):.2f}")
    print(f"  平均持仓时间: {test_metrics.get('平均持仓时间(小时)', 0):.1f}小时")
    
    # 8. 保存配置
    config = {
        'timestamp': datetime.now().isoformat(),
        'symbol': args.symbol,
        'period': args.period,
        'interval': args.interval,
        'initial_capital': args.capital,
        'train_ratio': args.train_ratio,
        'strategy_params': {
            'fast_period': strategy.fast_period,
            'slow_period': strategy.slow_period,
            'rsi_period': strategy.rsi_period,
            'bb_period': strategy.bb_period,
            'bb_std': strategy.bb_std,
            'atr_period': strategy.atr_period,
            'position_size': strategy.position_size,
            'stop_loss_pct': strategy.stop_loss_pct,
            'take_profit_pct': strategy.take_profit_pct
        },
        'result_id': result['result_id'],
        'report_path': result['report_path']
    }
    
    config_path = os.path.join('results', result['result_id'], 'config.json')
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 回测完成!")
    print(f"结果ID: {result['result_id']}")
    print(f"报告文件: {result['report_path']}")
    print(f"配置文件: {config_path}")
    
    return result

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)