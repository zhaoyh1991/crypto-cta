#!/usr/bin/env python3
"""
演示脚本：使用模拟数据运行1小时级别CTA回测
避免API连接问题，适合快速测试
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_sample_data(symbol='BTCUSDT', days=30, interval='1h'):
    """生成模拟数据"""
    print(f"生成 {symbol} 的模拟数据 ({days}天, {interval})...")
    
    # 计算数据点数量
    if interval == '1h':
        freq = '1h'
        periods = days * 24
    elif interval == '4h':
        freq = '4h'
        periods = days * 6
    else:
        freq = '1h'
        periods = days * 24
    
    # 生成时间序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)[:periods]
    
    # 基础价格
    if 'BTC' in symbol:
        start_price = 50000
    elif 'ETH' in symbol:
        start_price = 3000
    else:
        start_price = 100
    
    np.random.seed(42)
    
    # 随机游走（带趋势）
    returns = np.random.normal(0.0005, 0.01, len(dates))  # 0.05%平均收益，1%波动
    trend = np.linspace(0, 0.1, len(dates))  # 10%的趋势
    returns += trend / len(dates)
    
    price = start_price * np.exp(np.cumsum(returns))
    
    # 生成OHLCV数据
    df = pd.DataFrame(index=dates)
    df['close'] = price
    open_prices = df['close'].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
    open_prices.iloc[0] = start_price
    df['open'] = open_prices
    
    # 高低价
    price_range = df['close'] * 0.02  # 2%的价格范围
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.5, len(dates)) * price_range
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.5, len(dates)) * price_range
    
    # 确保 high >= low
    high_low_df = df[['high', 'low']]
    df['high'] = high_low_df.max(axis=1)
    df['low'] = high_low_df.min(axis=1)
    
    # 成交量
    df['volume'] = 1000 * (1 + np.abs(returns) * 10) * np.random.uniform(0.8, 1.2, len(dates))
    
    # 删除NaN
    df = df.dropna()
    
    print(f"生成 {len(df)} 条数据，价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    return df

def run_demo_backtest(symbol='BTCUSDT', days=30, capital=10000):
    """运行演示回测"""
    print(f"\n{'='*60}")
    print(f"1小时级别CTA策略演示回测")
    print(f"交易对: {symbol}")
    print(f"回测天数: {days}天")
    print(f"初始资金: ${capital:,.2f}")
    print(f"{'='*60}\n")
    
    # 1. 生成数据
    df = generate_sample_data(symbol, days, '1h')
    
    # 2. 导入策略
    from src.cta_strategy import CryptoCTAStrategy
    
    # 使用针对1小时优化的参数
    strategy = CryptoCTAStrategy(
        fast_period=12,      # 12小时均线
        slow_period=48,      # 48小时均线
        rsi_period=14,
        bb_period=20,
        bb_std=2.0,
        atr_period=14,
        volume_threshold=1.2,
        position_size=0.1,   # 10%仓位
        stop_loss_pct=0.015, # 1.5%止损
        take_profit_pct=0.03 # 3%止盈
    )
    
    # 3. 生成信号
    print("\n生成交易信号...")
    df_with_signals = strategy.generate_signals(df)
    
    # 检查信号
    buy_signals = df_with_signals[df_with_signals['signal_filtered'] == 1]
    sell_signals = df_with_signals[df_with_signals['signal_filtered'] == -1]
    
    print(f"  买入信号: {len(buy_signals)} 个")
    print(f"  卖出信号: {len(sell_signals)} 个")
    
    # 4. 运行回测
    print("\n运行回测...")
    results = strategy.run_backtest(df_with_signals, initial_capital=capital)
    
    if not results:
        print("回测失败！")
        return
    
    # 5. 显示结果
    print(f"\n{'='*60}")
    print(f"回测结果")
    print(f"{'='*60}")
    
    # 基本结果
    final_equity = results.get('final_equity', capital)
    total_return = (final_equity - capital) / capital
    trades = results.get('trades', [])
    
    print(f"\n📈 基本指标:")
    print(f"  初始资金: ${capital:,.2f}")
    print(f"  最终权益: ${final_equity:,.2f}")
    print(f"  总收益率: {total_return*100:.2f}%")
    print(f"  总交易次数: {len(trades)}")
    
    # 交易分析
    if trades is not None and not trades.empty:
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] <= 0]
        
        print(f"\n💰 交易分析:")
        print(f"  盈利交易: {len(winning_trades)}")
        print(f"  亏损交易: {len(losing_trades)}")
        print(f"  胜率: {len(winning_trades)/len(trades)*100:.1f}%" if len(trades) > 0 else "  胜率: 0.0%")
        
        if len(winning_trades) > 0:
            print(f"  平均盈利: ${winning_trades['pnl'].mean():.2f}")
        if len(losing_trades) > 0:
            print(f"  平均亏损: ${losing_trades['pnl'].mean():.2f}")
        
        # 显示前5笔交易
        print(f"\n📝 最近5笔交易:")
        recent_trades = trades.tail(5)
        for i, (idx, trade) in enumerate(recent_trades.iterrows(), 1):
            direction = "买入" if trade['side'] == 'long' else "卖出"
            pnl_pct = trade['pnl_pct'] * 100
            
            print(f"  {i}. {direction} @ ${trade['entry_price']:.2f} -> "
                  f"${trade['exit_price']:.2f} ({pnl_pct:+.2f}%)")
    
    # 6. 保存结果
    print(f"\n💾 保存结果...")
    results_dir = 'demo_results'
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存交易记录
    if trades is not None and not trades.empty:
        trades_file = os.path.join(results_dir, f"{symbol}_{timestamp}_trades.csv")
        trades.to_csv(trades_file, index=False)
        print(f"  交易记录: {trades_file}")
    
    # 保存数据
    data_file = os.path.join(results_dir, f"{symbol}_{timestamp}_data.csv")
    df_with_signals.to_csv(data_file)
    print(f"  数据文件: {data_file}")
    
    # 7. 生成简单图表
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 价格和信号
        ax1.plot(df.index, df['close'], label='Close Price', linewidth=1, color='blue')
        
        # 标记买入信号
        if len(buy_signals) > 0:
            ax1.scatter(buy_signals.index, buy_signals['close'], 
                       color='green', marker='^', s=100, label='Buy Signal', zorder=5)
        
        # 标记卖出信号
        if len(sell_signals) > 0:
            ax1.scatter(sell_signals.index, sell_signals['close'],
                       color='red', marker='v', s=100, label='Sell Signal', zorder=5)
        
        ax1.set_title(f'{symbol} - Price and Trading Signals (Demo)')
        ax1.set_ylabel('Price (USDT)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 权益曲线（如果有）
        if 'equity_curve' in results:
            equity_df = results['equity_curve']
            ax2.plot(equity_df.index, equity_df['equity'], label='Equity Curve', linewidth=2, color='green')
            ax2.axhline(y=capital, color='red', linestyle='--', alpha=0.5, label='Initial Capital')
        
        ax2.set_title('Equity Curve')
        ax2.set_ylabel('Equity (USDT)')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        chart_file = os.path.join(results_dir, f"{symbol}_{timestamp}_chart.png")
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  图表文件: {chart_file}")
        
    except ImportError:
        print("  跳过图表生成 (matplotlib不可用)")
    
    print(f"\n{'='*60}")
    print(f"演示完成！结果保存在: {results_dir}/")
    print(f"{'='*60}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行1小时级别CTA策略演示')
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='交易对 (默认: BTCUSDT)')
    parser.add_argument('--days', type=int, default=30,
                       help='回测天数 (默认: 30)')
    parser.add_argument('--capital', type=float, default=10000,
                       help='初始资金 (默认: 10000)')
    parser.add_argument('--list-demo', action='store_true',
                       help='显示演示选项')
    
    args = parser.parse_args()
    
    if args.list_demo:
        print("演示选项:")
        print("  1. 快速测试: python run_demo.py --symbol BTCUSDT --days 7")
        print("  2. 标准测试: python run_demo.py --symbol ETHUSDT --days 30")
        print("  3. 长期测试: python run_demo.py --symbol BTCUSDT --days 90 --capital 50000")
        return
    
    run_demo_backtest(args.symbol, args.days, args.capital)

if __name__ == "__main__":
    main()