"""
1小时级别CTA策略回测系统
专门针对币安1小时K线数据进行回测
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import os
import sys
from typing import Dict, List, Tuple, Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance_fetcher import BinanceDataFetcher
from src.cta_strategy import CryptoCTAStrategy
from src.backtester import Backtester

class HourlyBacktester:
    """
    1小时级别回测器
    专门优化用于1小时K线数据的回测
    """
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        """
        初始化回测器
        
        Args:
            initial_capital: 初始资金
            commission: 交易手续费（默认0.1%）
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.results_dir = 'results_1h'
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 初始化数据获取器
        self.fetcher = BinanceDataFetcher(data_dir='data_1h')
        
        # 初始化策略（针对1小时级别优化参数）
        self.strategy = CryptoCTAStrategy(
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
        
        # 初始化回测器
        self.backtester = Backtester(results_dir=self.results_dir)
    
    def run_backtest(self, symbol: str = 'BTCUSDT', days: int = 90, 
                    train_ratio: float = 0.7) -> Dict:
        """
        运行1小时级别回测
        
        Args:
            symbol: 交易对
            days: 回测天数
            train_ratio: 训练集比例
            
        Returns:
            回测结果字典
        """
        print(f"\n{'='*60}")
        print(f"开始1小时级别回测")
        print(f"交易对: {symbol}")
        print(f"回测天数: {days}天")
        print(f"初始资金: ${self.initial_capital:,.2f}")
        print(f"手续费: {self.commission*100:.1f}%")
        print(f"{'='*60}\n")
        
        # 1. 获取数据
        print("1. 获取数据...")
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        df = self.fetcher.fetch_klines(
            symbol=symbol,
            interval='1h',
            start_time=start_time.strftime('%Y-%m-%d'),
            end_time=end_time.strftime('%Y-%m-%d'),
            limit=1000
        )
        
        if df is None or df.empty:
            print("错误: 无法获取数据")
            return None
        
        print(f"  获取到 {len(df)} 条1小时K线数据")
        print(f"  时间范围: {df.index[0]} 到 {df.index[-1]}")
        print(f"  价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        
        # 2. 数据预处理
        print("\n2. 数据预处理...")
        df = self._preprocess_data(df)
        
        # 3. 分割训练集和测试集
        print("\n3. 数据分割...")
        split_idx = int(len(df) * train_ratio)
        train_data = df.iloc[:split_idx]
        test_data = df.iloc[split_idx:]
        
        print(f"  训练集: {len(train_data)} 条 ({train_ratio*100:.0f}%)")
        print(f"  测试集: {len(test_data)} 条 ({(1-train_ratio)*100:.0f}%)")
        print(f"  训练集时间: {train_data.index[0]} 到 {train_data.index[-1]}")
        print(f"  测试集时间: {test_data.index[0]} 到 {test_data.index[-1]}")
        
        # 4. 在训练集上优化参数（可选）
        print("\n4. 策略参数优化...")
        optimized_params = self._optimize_parameters(train_data)
        if optimized_params:
            self.strategy.update_parameters(**optimized_params)
            print(f"  优化后的参数: {optimized_params}")
        
        # 5. 生成交易信号
        print("\n5. 生成交易信号...")
        test_data_with_signals = self.strategy.generate_signals(test_data)
        
        # 6. 运行回测
        print("\n6. 运行回测...")
        results = self.backtester.run(test_data_with_signals)
        
        # 7. 分析结果
        print("\n7. 分析结果...")
        analysis = self._analyze_results(results, test_data)
        
        # 8. 保存结果
        print("\n8. 保存结果...")
        self._save_results(results, analysis, symbol)
        
        # 9. 可视化
        print("\n9. 生成可视化图表...")
        self._create_visualizations(results, test_data, symbol)
        
        return {
            'results': results,
            'analysis': analysis,
            'data_info': {
                'symbol': symbol,
                'period_days': days,
                'data_points': len(df),
                'train_size': len(train_data),
                'test_size': len(test_data)
            }
        }
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        df = df.copy()
        
        # 确保数据按时间排序
        df = df.sort_index()
        
        # 检查并处理缺失值
        missing_values = df.isnull().sum()
        if missing_values.any():
            print(f"  发现缺失值: {missing_values[missing_values > 0].to_dict()}")
            df = df.ffill().bfill()
        
        # 添加技术指标计算所需的列
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 计算波动率（用于风险控制）
        df['volatility_20'] = df['returns'].rolling(20).std()
        
        # 计算真实波动幅度（ATR）
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        df['true_range'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = df['true_range'].rolling(14).mean()
        
        # 删除NaN值
        df = df.dropna()
        
        return df
    
    def _optimize_parameters(self, train_data: pd.DataFrame) -> Optional[Dict]:
        """
        在训练集上优化策略参数
        使用简单的网格搜索
        """
        print("  在训练集上进行参数优化...")
        
        # 定义参数网格
        param_grid = {
            'fast_period': [8, 12, 16],
            'slow_period': [36, 48, 60],
            'position_size': [0.08, 0.1, 0.12],
            'stop_loss_pct': [0.01, 0.015, 0.02],
            'take_profit_pct': [0.025, 0.03, 0.035]
        }
        
        best_sharpe = -np.inf
        best_params = None
        
        # 简化搜索（实际应用中可以使用更复杂的优化方法）
        for fast in param_grid['fast_period']:
            for slow in param_grid['slow_period']:
                if slow <= fast:
                    continue
                
                # 创建临时策略
                temp_strategy = CryptoCTAStrategy(
                    fast_period=fast,
                    slow_period=slow,
                    position_size=0.1,
                    stop_loss_pct=0.015,
                    take_profit_pct=0.03
                )
                
                # 在训练集上测试
                train_with_signals = temp_strategy.generate_signals(train_data)
                temp_backtester = Backtester(
                    initial_capital=self.initial_capital,
                    commission=self.commission
                )
                temp_results = temp_backtester.run(train_with_signals)
                
                # 计算夏普比率
                if 'sharpe_ratio' in temp_results.get('metrics', {}):
                    sharpe = temp_results['metrics']['sharpe_ratio']
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = {
                            'fast_period': fast,
                            'slow_period': slow
                        }
        
        if best_params:
            print(f"  最佳夏普比率: {best_sharpe:.3f}")
        
        return best_params
    
    def _analyze_results(self, results: Dict, test_data: pd.DataFrame) -> Dict:
        """分析回测结果"""
        metrics = results.get('metrics', {})
        trades = results.get('trades', [])
        
        analysis = {
            'performance': {},
            'risk_metrics': {},
            'trade_analysis': {}
        }
        
        # 性能指标
        analysis['performance'] = {
            'total_return': metrics.get('total_return', 0),
            'annualized_return': metrics.get('annualized_return', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'sortino_ratio': metrics.get('sortino_ratio', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'calmar_ratio': metrics.get('calmar_ratio', 0)
        }
        
        # 交易分析
        if trades:
            trades_df = pd.DataFrame(trades)
            
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] <= 0]
            
            analysis['trade_analysis'] = {
                'total_trades': len(trades_df),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0,
                'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
                'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
                'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0,
                'largest_win': trades_df['pnl'].max(),
                'largest_loss': trades_df['pnl'].min(),
                'avg_trade_duration': trades_df['duration'].mean() if 'duration' in trades_df.columns else 0
            }
        
        # 风险指标
        equity_curve = results.get('equity_curve', [])
        if equity_curve:
            equity_df = pd.DataFrame(equity_curve)
            equity_df['date'] = pd.to_datetime(equity_df['date'])
            equity_df.set_index('date', inplace=True)
            
            # 计算滚动风险指标
            rolling_volatility = equity_df['equity'].pct_change().rolling(20).std()
            analysis['risk_metrics']['avg_volatility'] = rolling_volatility.mean()
            analysis['risk_metrics']['max_volatility'] = rolling_volatility.max()
        
        return analysis
    
    def _save_results(self, results: Dict, analysis: Dict, symbol: str):
        """保存回测结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{symbol}_{timestamp}"
        
        # 保存指标
        metrics_file = os.path.join(self.results_dir, f"{base_filename}_metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump({
                'performance': analysis['performance'],
                'trade_analysis': analysis['trade_analysis'],
                'risk_metrics': analysis['risk_metrics']
            }, f, indent=2, default=str)
        
        # 保存交易记录
        if 'trades' in results:
            trades_file = os.path.join(self.results_dir, f"{base_filename}_trades.csv")
            trades_df = pd.DataFrame(results['trades'])
            trades_df.to_csv(trades_file, index=False)
        
        # 保存权益曲线
        if 'equity_curve' in results:
            equity_file = os.path.join(self.results_dir, f"{base_filename}_equity.csv")
            equity_df = pd.DataFrame(results['equity_curve'])
            equity_df.to_csv(equity_file, index=False)
        
        print(f"  结果已保存到: {self.results_dir}/")
        print(f"  指标文件: {metrics_file}")
    
    def _create_visualizations(self, results: Dict, test_data: pd.DataFrame, symbol: str):
        """创建可视化图表"""
        try:
            import matplotlib.pyplot as plt
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 创建图表
            fig, axes = plt.subplots(3, 1, figsize=(12, 15))
            
            # 1. 价格和交易信号
            ax1 = axes[0]
            ax1.plot(test_data.index, test_data['close'], label='Close Price', linewidth=1)
            
            # 标记买入信号
            if 'signals' in results:
                buy_signals = results['signals'].get('buy', [])
                for signal in buy_signals:
                    if 'timestamp' in signal:
                        ts = pd.to_datetime(signal['timestamp'])
                        price = signal.get('price', test_data.loc[ts, 'close'] if ts in test_data.index else test_data['close'].iloc[-1])
                        ax1.scatter(ts, price, color='green', marker='^', s=100, label='Buy' if 'Buy' not in ax1.get_legend_handles_labels()[1] else "")
            
            # 标记卖出信号
            if 'signals' in results:
                sell_signals = results['signals'].get('sell', [])
                for signal in sell_signals:
                    if 'timestamp' in signal:
                        ts = pd.to_datetime(signal['timestamp'])
                        price = signal.get('price', test_data.loc[ts, 'close'] if ts in test_data.index else test_data['close'].iloc[-1])
                        ax1.scatter(ts, price, color='red', marker='v', s=100, label='Sell' if 'Sell' not in ax1.get_legend_handles_labels()[1] else "")
            
            ax1.set_title(f'{symbol} - Price and Trading Signals (1h)')
            ax1.set_ylabel('Price (USDT)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 权益曲线
            ax2 = axes[1]
            if 'equity_curve' in results:
                equity_df = pd.DataFrame(results['equity_curve'])
                equity_df['date'] = pd.to_datetime(equity_df['date'])
                ax2.plot(equity_df['date'], equity_df['equity'], label='Equity Curve', linewidth=2, color='blue')
                ax2.axhline(y=self.initial_capital, color='red', linestyle='--', alpha=0.5, label='Initial Capital')
            
            ax2.set_title('Equity Curve')
            ax2.set_ylabel('Equity (USDT)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. 回撤曲线
            ax3 = axes[2]
            if 'equity_curve' in results:
                equity_df = pd.DataFrame(results['equity_curve'])
                equity_df['date'] = pd.to_datetime(equity_df['date'])
                
                # 计算回撤
                equity_series = pd.Series(equity_df['equity'].values, index=equity_df['date'])
                rolling_max = equity_series.expanding().max()
                drawdown = (equity_series - rolling_max) / rolling_max * 100
                
                ax3.fill_between(equity_df['date'], 0, drawdown.values, alpha=0.3, color='red', label='Drawdown')
                ax3.plot(equity_df['date'], drawdown.values, color='red', linewidth=1)
            
            ax3.set_title('Drawdown')
            ax3.set_ylabel('Drawdown (%)')
            ax3.set_xlabel('Date')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            chart_file = os.path.join(self.results_dir, f"{symbol}_{timestamp}_report.png")
            plt.savefig(chart_file, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  图表已保存: {chart_file}")
            
        except ImportError:
            print("  警告: matplotlib不可用，跳过图表生成")
        except Exception as e:
            print(f"  生成图表失败: {e}")
    
    def run_quick_test(self, symbol: str = 'BTCUSDT', days: int = 7) -> Dict:
        """
        快速测试（用于验证系统是否正常工作）
        
        Args:
            symbol: 交易对
            days: 测试天数
            
        Returns:
            简化版结果
        """
        print(f"快速测试: {symbol} ({days}天)")
        
        # 获取数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        df = self.fetcher.fetch_klines(
            symbol=symbol,
            interval='1h',
            start_time=start_time.strftime('%Y-%m-%d'),
            end_time=end_time.strftime('%Y-%m-%d'),
            limit=100
        )
        
        if df is None or df.empty:
            return {'error': '无法获取数据'}
        
        # 生成信号
        df_with_signals = self.strategy.generate_signals(df)
        
        # 运行回测
        results = self.backtester.run(df_with_signals)
        
        return {
            'data_points': len(df),
            'signals_generated': len(results.get('signals', {}).get('buy', [])) + len(results.get('signals', {}).get('sell', [])),
            'trades_executed': len(results.get('trades', [])),
            'final_equity': results.get('final_equity', self.initial_capital)
        }