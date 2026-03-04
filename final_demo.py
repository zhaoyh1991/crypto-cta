#!/usr/bin/env python3
"""
最终演示：完整的可运行CTA策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

class SimpleCryptoCTA:
    """
    简化的加密货币CTA策略
    包含完整的策略逻辑和回测功能
    """
    
    def __init__(self, 
                 ma_short=10,      # 短期均线
                 ma_long=30,       # 长期均线
                 rsi_period=14,    # RSI周期
                 position_size=0.1, # 仓位大小
                 stop_loss=0.02,   # 止损
                 take_profit=0.04  # 止盈
                ):
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.rsi_period = rsi_period
        self.position_size = position_size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        
    def calculate_rsi(self, prices, period=14):
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, df):
        """生成交易信号"""
        df = df.copy()
        
        # 计算指标
        df['ma_short'] = df['close'].rolling(self.ma_short).mean()
        df['ma_long'] = df['close'].rolling(self.ma_long).mean()
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        
        # 初始化信号
        df['signal'] = 0
        
        # 买入信号：短期均线上穿长期均线 且 RSI < 40
        buy_condition = (
            (df['ma_short'] > df['ma_long']) &  # 金叉
            (df['rsi'] < 40) &                   # RSI超卖
            (df['close'] < df['ma_short'] * 1.02)  # 价格接近均线
        )
        
        # 卖出信号：短期均线下穿长期均线 且 RSI > 60
        sell_condition = (
            (df['ma_short'] < df['ma_long']) &  # 死叉
            (df['rsi'] > 60) &                   # RSI超买
            (df['close'] > df['ma_short'] * 0.98)  # 价格接近均线
        )
        
        df.loc[buy_condition, 'signal'] = 1      # 买入
        df.loc[sell_condition, 'signal'] = -1    # 卖出
        
        return df
    
    def run_backtest(self, df, initial_capital=100000):
        """运行回测"""
        df = self.generate_signals(df)
        
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity = [initial_capital]
        
        for i in range(self.ma_long, len(df)):  # 从足够长的数据开始
            current_price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            
            # 计算当前权益
            current_equity = capital + (position * current_price)
            equity.append(current_equity)
            
            # 检查止损止盈
            if position > 0 and entry_price > 0:  # 多头仓位
                pnl_pct = (current_price - entry_price) / entry_price
                if pnl_pct <= -self.stop_loss or pnl_pct >= self.take_profit:
                    # 平仓
                    exit_price = entry_price * (1 - self.stop_loss) if pnl_pct <= -self.stop_loss else entry_price * (1 + self.take_profit)
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    
                    trades.append({
                        'type': 'SELL',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': position,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'reason': '止损' if pnl_pct <= -self.stop_loss else '止盈'
                    })
                    
                    position = 0
                    entry_price = 0
            
            # 开新仓
            if signal != 0 and position == 0:
                if signal == 1:  # 买入
                    position_value = capital * self.position_size
                    position = position_value / current_price
                    capital -= position_value
                    entry_price = current_price
                    
                    trades.append({
                        'type': 'BUY',
                        'price': current_price,
                        'position': position
                    })
                
                elif signal == -1:  # 卖出（做空）
                    # 简化为不处理做空
                    pass
        
        # 最后平仓
        if position > 0:
            exit_price = df['close'].iloc[-1]
            pnl = (exit_price - entry_price) * position
            capital += pnl
            
            trades.append({
                'type': 'SELL_FINAL',
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position': position,
                'pnl': pnl,
                'pnl_pct': (exit_price - entry_price) / entry_price,
                'reason': '最后平仓'
            })
        
        # 计算指标
        equity_series = pd.Series(equity)
        returns = equity_series.pct_change().dropna()
        
        total_return = (capital - initial_capital) / initial_capital
        annual_return = (1 + total_return) ** (365 / len(df)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0
        
        # 最大回撤
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 交易统计
        if trades:
            sell_trades = [t for t in trades if t['type'] in ['SELL', 'SELL_FINAL']]
            winning_trades = [t for t in sell_trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
            
            avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
            losing_trades = [t for t in sell_trades if t['pnl'] <= 0]
            avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
            
            profit_factor = abs(sum(t['pnl'] for t in winning_trades) / 
                               sum(t['pnl'] for t in losing_trades)) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else float('inf')
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        results = {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': trades,
            'equity_curve': equity_series
        }
        
        return results

def create_test_data():
    """创建测试数据"""
    np.random.seed(42)
    
    # 200天数据
    dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
    
    # 创建趋势+波动的价格序列
    trend = np.linspace(0, 0.4, len(dates))  # 40%趋势
    noise = np.random.normal(0, 0.02, len(dates))  # 2%日波动
    
    # 合成价格
    price = 50000 * np.exp(trend + np.cumsum(noise) * 0.1)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'open': price * (1 + np.random.normal(0, 0.01, len(dates))),
        'high': price * (1 + np.random.uniform(0.01, 0.03, len(dates))),
        'low': price * (1 - np.random.uniform(0.01, 0.03, len(dates))),
        'close': price,
        'volume': 1000 * (1 + np.abs(noise) * 10)
    }, index=dates)
    
    # 确保high > low
    df['high'] = df[['high', 'low']].max(axis=1)
    df['low'] = df[['high', 'low']].min(axis=1)
    
    return df

def main():
    """主函数"""
    print("=" * 70)
    print("加密货币CTA策略 - 完整可运行版本")
    print("=" * 70)
    
    # 1. 创建数据
    print("\n1. 创建测试数据...")
    df = create_test_data()
    print(f"数据范围: {len(df)} 天")
    print(f"价格: ${df['close'].iloc[0]:.0f} → ${df['close'].iloc[-1]:.0f}")
    print(f"涨幅: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1):.1%}")
    
    # 2. 创建策略
    print("\n2. 创建CTA策略...")
    strategy = SimpleCryptoCTA(
        ma_short=10,
        ma_long=30,
        rsi_period=14,
        position_size=0.1,
        stop_loss=0.02,
        take_profit=0.04
    )
    
    print(f"策略参数:")
    print(f"  短期均线: {strategy.ma_short}天")
    print(f"  长期均线: {strategy.ma_long}天")
    print(f"  RSI周期: {strategy.rsi_period}天")
    print(f"  仓位大小: {strategy.position_size:.0%}")
    print(f"  止损: {strategy.stop_loss:.1%}")
    print(f"  止盈: {strategy.take_profit:.1%}")
    
    # 3. 运行回测
    print("\n3. 运行回测...")
    results = strategy.run_backtest(df, initial_capital=100000)
    
    # 4. 显示结果
    print("\n" + "=" * 70)
    print("回测结果")
    print("=" * 70)
    
    print(f"\n📊 收益表现:")
    print(f"  初始资金: ${results['initial_capital']:,.0f}")
    print(f"  最终资金: ${results['final_capital']:,.0f}")
    print(f"  总收益率: {results['total_return']:.2%}")
    print(f"  年化收益率: {results['annual_return']:.2%}")
    
    print(f"\n📈 风险指标:")
    print(f"  夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {results['max_drawdown']:.2%}")
    print(f"  年化波动率: {results['volatility']:.2%}")
    
    print(f"\n🎯 交易统计:")
    print(f"  总交易次数: {results['total_trades']}")
    print(f"  胜率: {results['win_rate']:.2%}")
    print(f"  平均盈利: {results['avg_win']:.2%}")
    print(f"  平均亏损: {results['avg_loss']:.2%}")
    print(f"  盈亏比: {results['profit_factor']:.2f}")
    
    # 5. 显示交易记录
    if results['trades']:
        print(f"\n💼 交易记录:")
        sell_trades = [t for t in results['trades'] if t['type'] in ['SELL', 'SELL_FINAL']]
        
        if sell_trades:
            print(f"  盈利交易: {sum(1 for t in sell_trades if t['pnl'] > 0)}笔")
            print(f"  亏损交易: {sum(1 for t in sell_trades if t['pnl'] <= 0)}笔")
            
            print(f"\n  最近3笔交易:")
            for trade in sell_trades[-3:]:
                pnl_sign = '+' if trade['pnl'] > 0 else ''
                print(f"    {trade['type']} | 入场: ${trade['entry_price']:.0f} | "
                      f"出场: ${trade['exit_price']:.0f} | "
                      f"盈利: {pnl_sign}${trade['pnl']:.0f} ({pnl_sign}{trade['pnl_pct']:.2%}) | "
                      f"原因: {trade['reason']}")
    
    # 6. 对比基准
    print(f"\n" + "=" * 70)
    print("策略对比")
    print("=" * 70)
    
    buy_hold_return = df['close'].iloc[-1] / df['close'].iloc[0] - 1
    strategy_return = results['total_return']
    
    print(f"\n买入持有策略:")
    print(f"  收益率: {buy_hold_return:.2%}")
    
    print(f"\nCTA策略:")
    print(f"  收益率: {strategy_return:.2%}")
    
    if strategy_return > buy_hold_return:
        print(f"\n✅ CTA策略跑赢买入持有: +{(strategy_return - buy_hold_return):.2%}")
    else:
        print(f"\n⚠️  CTA策略跑输买入持有: {(strategy_return - buy_hold_return):.2%}")
    
    # 7. 风险评估
    print(f"\n" + "=" * 70)
    print("风险评估")
    print("=" * 70)
    
    print(f"\n策略稳定性评估:")
    
    if results['sharpe_ratio'] > 1.0:
        print(f"  ✅ 夏普比率优秀 (>1.0)")
    elif results['sharpe_ratio'] > 0.5:
        print(f"  ⚠️  夏普比率一般 (0.5-1.0)")
    else:
        print(f"  ❌ 夏普比率较差 (<0.5)")
    
    if results['max_drawdown'] > -0.15:
        print(f"  ✅ 回撤控制良好 (<15%)")
    elif results['max_drawdown'] > -0.25:
        print(f"  ⚠️  回撤中等 (15-25%)")
    else:
        print(f"  ❌ 回撤较大 (>25%)")
    
    if results['win_rate'] > 0.5:
        print(f"  ✅ 胜率较高 (>50%)")
    else:
        print(f"  ⚠️  胜率较低 (<50%)")
    
    if results['total_trades'] >= 10:
        print(f"  ✅ 交易样本充足 (≥10笔)")
    else:
        print(f"  ⚠️  交易样本不足 (<10笔)")
    
    # 8. 保存结果
    print(f"\n" + "=" * 70)
    print("结果保存")
    print("=" * 70)
    
    # 创建结果目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = f"cta_results_{timestamp}"
    os.makedirs(result_dir, exist_ok=True)
    
    # 保存结果
    results_to_save = results.copy()
    
    # 移除不能序列化的数据
    if 'equity_curve' in results_to_save:
        results_to_save['equity_curve'] = results_to_save['equity_curve'].tolist()
    
    # 保存为JSON
    with open(os.path.join(result_dir, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results_to_save, f, indent=2, ensure_ascii=False)
    
    # 保存策略配置
    config = {
        'ma_short': strategy.ma_short,
        'ma_long': strategy.ma_long,
        'rsi_period': strategy.rsi_period,
        'position_size': strategy.position_size,
        'stop_loss': strategy.stop_loss,
        'take_profit': strategy.take_profit,
        'timestamp': timestamp
    }
    
    with open(os.path.join(result_dir, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # 保存交易记录
    if results['trades']:
        trades_df = pd.DataFrame(results['trades'])
        trades_df.to_csv(os.path.join(result_dir, 'trades.csv'), index=False)
    
    print(f"\n✅ 所有结果已保存到目录: {result_dir}")
    print(f"   1. results.json - 完整回测结果")
    print(f"   2. config.json - 策略配置")