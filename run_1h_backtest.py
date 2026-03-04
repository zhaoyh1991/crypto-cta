#!/usr/bin/env python3
"""
1小时级别CTA策略回测运行脚本
简化使用，支持命令行参数
"""

import argparse
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtest_1h import HourlyBacktester

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行1小时级别CTA策略回测')
    
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='交易对 (默认: BTCUSDT)')
    parser.add_argument('--days', type=int, default=90,
                       help='回测天数 (默认: 90)')
    parser.add_argument('--capital', type=float, default=10000,
                       help='初始资金 (默认: 10000)')
    parser.add_argument('--commission', type=float, default=0.001,
                       help='交易手续费比例 (默认: 0.001 = 0.1%%)')
    parser.add_argument('--train-ratio', type=float, default=0.7,
                       help='训练集比例 (默认: 0.7)')
    parser.add_argument('--list-symbols', action='store_true',
                       help='列出可用的交易对')
    parser.add_argument('--batch', type=str, nargs='+',
                       help='批量回测多个交易对，例如: --batch BTCUSDT ETHUSDT')
    
    return parser.parse_args()

def list_available_symbols():
    """列出可用的交易对"""
    from binance_fetcher import BinanceDataFetcher
    
    print("获取可用的交易对列表...")
    fetcher = BinanceDataFetcher()
    symbols = fetcher.get_available_symbols()
    
    print(f"\n共找到 {len(symbols)} 个交易对:")
    print("-" * 60)
    
    # 分组显示
    for i in range(0, len(symbols), 10):
        chunk = symbols[i:i+10]
        print("  " + "  ".join(chunk))
    
    print("-" * 60)
    print("\n常用交易对:")
    common_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
                     'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT']
    for symbol in common_symbols:
        if symbol in symbols:
            print(f"  ✓ {symbol}")
        else:
            print(f"  ✗ {symbol} (不可用)")
    
    return symbols

def run_single_backtest(args):
    """运行单个交易对回测"""
    print(f"\n{'='*70}")
    print(f"1小时级别CTA策略回测")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # 创建回测器
    backtester = HourlyBacktester(
        initial_capital=args.capital,
        commission=args.commission
    )
    
    # 运行回测
    result = backtester.run_backtest(
        symbol=args.symbol,
        days=args.days,
        train_ratio=args.train_ratio
    )
    
    if result is None:
        print("\n回测失败！")
        return False
    
    # 显示结果摘要
    print(f"\n{'='*70}")
    print(f"回测结果摘要")
    print(f"{'='*70}")
    
    analysis = result['analysis']
    data_info = result['data_info']
    
    # 性能指标
    perf = analysis['performance']
    print(f"\n📈 性能指标:")
    print(f"  总收益率: {perf.get('total_return', 0)*100:.2f}%")
    print(f"  年化收益率: {perf.get('annualized_return', 0)*100:.2f}%")
    print(f"  夏普比率: {perf.get('sharpe_ratio', 0):.3f}")
    print(f"  索提诺比率: {perf.get('sortino_ratio', 0):.3f}")
    print(f"  最大回撤: {perf.get('max_drawdown', 0)*100:.2f}%")
    print(f"  卡玛比率: {perf.get('calmar_ratio', 0):.3f}")
    
    # 交易分析
    trade_analysis = analysis['trade_analysis']
    print(f"\n💰 交易分析:")
    print(f"  总交易次数: {trade_analysis.get('total_trades', 0)}")
    print(f"  盈利交易: {trade_analysis.get('winning_trades', 0)}")
    print(f"  亏损交易: {trade_analysis.get('losing_trades', 0)}")
    print(f"  胜率: {trade_analysis.get('win_rate', 0)*100:.1f}%")
    print(f"  平均盈利: ${trade_analysis.get('avg_win', 0):.2f}")
    print(f"  平均亏损: ${trade_analysis.get('avg_loss', 0):.2f}")
    print(f"  盈亏比: {trade_analysis.get('profit_factor', 0):.2f}")
    
    # 数据信息
    print(f"\n📊 数据信息:")
    print(f"  交易对: {data_info.get('symbol', 'N/A')}")
    print(f"  回测天数: {data_info.get('period_days', 0)}天")
    print(f"  总数据点: {data_info.get('data_points', 0)}")
    print(f"  训练集: {data_info.get('train_size', 0)}条")
    print(f"  测试集: {data_info.get('test_size', 0)}条")
    
    print(f"\n📁 结果文件保存在: crypto_cta/results_1h/")
    print(f"{'='*70}\n")
    
    return True

def run_batch_backtest(symbols, args):
    """批量回测多个交易对"""
    print(f"\n{'='*70}")
    print(f"批量回测 {len(symbols)} 个交易对")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    results = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] 回测 {symbol}...")
        
        try:
            # 创建回测器
            backtester = HourlyBacktester(
                initial_capital=args.capital,
                commission=args.commission
            )
            
            # 运行回测
            result = backtester.run_backtest(
                symbol=symbol,
                days=args.days,
                train_ratio=args.train_ratio
            )
            
            if result:
                analysis = result['analysis']
                perf = analysis['performance']
                
                # 收集关键指标
                summary = {
                    'symbol': symbol,
                    'total_return': perf.get('total_return', 0),
                    'sharpe_ratio': perf.get('sharpe_ratio', 0),
                    'max_drawdown': perf.get('max_drawdown', 0),
                    'win_rate': analysis['trade_analysis'].get('win_rate', 0),
                    'total_trades': analysis['trade_analysis'].get('total_trades', 0)
                }
                
                results.append(summary)
                
                print(f"  ✓ 完成: 收益率={summary['total_return']*100:.1f}%, "
                      f"夏普={summary['sharpe_ratio']:.2f}, "
                      f"回撤={summary['max_drawdown']*100:.1f}%")
            else:
                print(f"  ✗ 失败")
                
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    # 显示批量回测总结
    if results:
        print(f"\n{'='*70}")
        print(f"批量回测总结")
        print(f"{'='*70}")
        
        # 按夏普比率排序
        results_sorted = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
        
        print(f"\n🏆 排名 (按夏普比率):")
        print("-" * 80)
        print(f"{'排名':<4} {'交易对':<10} {'收益率':<10} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<10} {'交易次数':<10}")
        print("-" * 80)
        
        for i, res in enumerate(results_sorted[:10], 1):  # 显示前10名
            print(f"{i:<4} {res['symbol']:<10} "
                  f"{res['total_return']*100:>8.1f}% "
                  f"{res['sharpe_ratio']:>9.2f} "
                  f"{res['max_drawdown']*100:>9.1f}% "
                  f"{res['win_rate']*100:>9.1f}% "
                  f"{res['total_trades']:>10}")
        
        print("-" * 80)
        
        # 统计信息
        total_returns = [r['total_return'] for r in results]
        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        
        print(f"\n📊 统计信息:")
        print(f"  平均收益率: {np.mean(total_returns)*100:.1f}%")
        print(f"  中位数收益率: {np.median(total_returns)*100:.1f}%")
        print(f"  最高收益率: {max(total_returns)*100:.1f}% ({results_sorted[0]['symbol']})")
        print(f"  最低收益率: {min(total_returns)*100:.1f}%")
        print(f"  平均夏普比率: {np.mean(sharpe_ratios):.2f}")
        
        # 保存批量结果
        import pandas as pd
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_file = f"crypto_cta/results_1h/batch_results_{timestamp}.csv"
        
        df = pd.DataFrame(results_sorted)
        df.to_csv(batch_file, index=False)
        print(f"\n📁 批量结果已保存到: {batch_file}")
    
    print(f"\n{'='*70}\n")

def main():
    """主函数"""
    args = parse_arguments()
    
    # 如果需要列出交易对
    if args.list_symbols:
        list_available_symbols()
        return
    
    # 检查是否需要安装依赖
    try:
        import numpy as np
    except ImportError:
        print("错误: 需要安装numpy，请运行: pip install numpy")
        return
    
    try:
        import pandas as pd
    except ImportError:
        print("错误: 需要安装pandas，请运行: pip install pandas")
        return
    
    # 批量回测
    if args.batch:
        run_batch_backtest(args.batch, args)
    else:
        # 单个回测
        run_single_backtest(args)

if __name__ == "__main__":
    main()