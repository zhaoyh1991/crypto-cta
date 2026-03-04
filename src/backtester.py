"""
CTA策略回测和可视化模块
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

# 尝试导入matplotlib，如果失败则提供替代方案
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("警告: matplotlib不可用，将跳过图表生成")

class Backtester:
    """
    策略回测和结果分析类
    """
    
    def __init__(self, results_dir='results'):
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        
    def run_complete_backtest(self, strategy, train_data, test_data, initial_capital=100000):
        """
        运行完整的回测（训练集优化 + 测试集验证）
        """
        print("=" * 60)
        print("开始完整回测")
        print("=" * 60)
        
        # 1. 在训练集上运行回测（用于参数优化参考）
        print("\n1. 训练集回测...")
        train_results = strategy.run_backtest(train_data, initial_capital)
        train_metrics = strategy.calculate_metrics(train_results)
        
        print("\n训练集表现:")
        self.print_metrics(train_metrics)
        
        # 2. 在测试集上运行回测（样本外测试）
        print("\n2. 测试集回测（样本外验证）...")
        test_results = strategy.run_backtest(test_data, initial_capital)
        test_metrics = strategy.calculate_metrics(test_results)
        
        print("\n测试集表现:")
        self.print_metrics(test_metrics)
        
        # 3. 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_id = f"backtest_{timestamp}"
        
        self.save_results(result_id, {
            'train_results': train_results,
            'train_metrics': train_metrics,
            'test_results': test_results,
            'test_metrics': test_metrics,
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
            }
        })
        
        # 4. 生成可视化报告
        print("\n3. 生成可视化报告...")
        report_path = self.generate_report(result_id, train_results, test_results, train_metrics, test_metrics)
        
        return {
            'result_id': result_id,
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'report_path': report_path
        }
    
    def print_metrics(self, metrics):
        """
        打印性能指标
        """
        if not metrics:
            print("无有效指标")
            return
        
        print(f"{'指标':<20} {'数值':>15}")
        print("-" * 40)
        
        for key, value in metrics.items():
            if isinstance(value, float):
                if '率' in key or '比' in key:
                    print(f"{key:<20} {value:>15.4f}")
                elif '资金' in key:
                    print(f"{key:<20} {value:>15.2f}")
                else:
                    print(f"{key:<20} {value:>15.6f}")
            else:
                print(f"{key:<20} {value:>15}")
    
    def save_results(self, result_id, results):
        """
        保存回测结果
        """
        result_dir = os.path.join(self.results_dir, result_id)
        os.makedirs(result_dir, exist_ok=True)
        
        # 保存指标
        metrics_path = os.path.join(result_dir, 'metrics.json')
        with open(metrics_path, 'w', encoding='utf-8') as f:
            # 转换numpy类型为Python原生类型
            def convert(obj):
                if isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                elif isinstance(obj, pd.DataFrame):
                    return obj.to_dict('records')
                elif isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(item) for item in obj]
                else:
                    return obj
            
            json.dump(convert(results), f, indent=2, ensure_ascii=False)
        
        # 保存交易记录
        if 'test_results' in results and 'trades' in results['test_results']:
            trades_df = results['test_results']['trades']
            if not trades_df.empty:
                trades_path = os.path.join(result_dir, 'trades.csv')
                trades_df.to_csv(trades_path, index=False)
        
        print(f"结果已保存到: {result_dir}")
        
        return result_dir
    
    def generate_report(self, result_id, train_results, test_results, train_metrics, test_metrics):
        """
        生成可视化报告
        """
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib不可用，跳过图表生成")
            return os.path.join(self.results_dir, result_id, 'report.txt')
        
        print("生成可视化图表...")
        
        result_dir = os.path.join(self.results_dir, result_id)
        
        # 创建图表
        fig = plt.figure(figsize=(16, 12))
        
        # 1. 权益曲线对比
        ax1 = plt.subplot(3, 2, 1)
        if 'equity_curve' in train_results and not train_results['equity_curve'].empty:
            train_equity = train_results['equity_curve']['equity']
            ax1.plot(train_equity.index, train_equity.values, 'b-', label='训练集', alpha=0.7)
        
        if 'equity_curve' in test_results and not test_results['equity_curve'].empty:
            test_equity = test_results['equity_curve']['equity']
            ax1.plot(test_equity.index, test_equity.values, 'r-', label='测试集', alpha=0.7)
        
        ax1.set_title('权益曲线对比')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('权益')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 回撤曲线
        ax2 = plt.subplot(3, 2, 2)
        if 'equity_curve' in test_results and not test_results['equity_curve'].empty:
            test_equity = test_results['equity_curve']['equity']
            cummax = test_equity.cummax()
            drawdown = (test_equity - cummax) / cummax
            
            ax2.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
            ax2.plot(drawdown.index, drawdown.values, 'r-', alpha=0.7)
            ax2.set_title('回撤曲线')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('回撤')
            ax2.grid(True, alpha=0.3)
        
        # 3. 月度收益热力图
        ax3 = plt.subplot(3, 2, 3)
        if 'equity_curve' in test_results and not test_results['equity_curve'].empty:
            test_equity = test_results['equity_curve']
            test_equity['returns'] = test_equity['equity'].pct_change()
            test_equity['month'] = test_equity.index.strftime('%Y-%m')
            
            monthly_returns = test_equity.groupby('month')['returns'].sum()
            
            # 创建热力图数据
            months = monthly_returns.index.tolist()
            returns_values = monthly_returns.values
            
            # 简单条形图代替热力图
            colors = ['green' if x >= 0 else 'red' for x in returns_values]
            ax3.bar(range(len(months)), returns_values, color=colors, alpha=0.7)
            ax3.set_title('月度收益')
            ax3.set_xlabel('月份')
            ax3.set_ylabel('收益')
            ax3.set_xticks(range(len(months)))
            ax3.set_xticklabels(months, rotation=45, ha='right')
            ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 交易统计
        ax4 = plt.subplot(3, 2, 4)
        if 'trades' in test_results and not test_results['trades'].empty:
            trades = test_results['trades']
            
            if not trades.empty:
                # 盈利交易 vs 亏损交易
                winning = trades[trades['pnl'] > 0]
                losing = trades[trades['pnl'] <= 0]
                
                labels = ['盈利交易', '亏损交易']
                sizes = [len(winning), len(losing)]
                colors = ['lightgreen', 'lightcoral']
                
                ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax4.set_title('交易盈亏分布')
        
        # 5. 关键指标对比
        ax5 = plt.subplot(3, 2, 5)
        if train_metrics and test_metrics:
            metrics_to_compare = ['总收益率', '年化收益率', '夏普比率', '最大回撤', '胜率']
            
            train_values = []
            test_values = []
            for metric in metrics_to_compare:
                if metric in train_metrics:
                    train_values.append(train_metrics[metric])
                if metric in test_metrics:
                    test_values.append(test_metrics[metric])
            
            x = np.arange(len(metrics_to_compare))
            width = 0.35
            
            ax5.bar(x - width/2, train_values, width, label='训练集', alpha=0.7)
            ax5.bar(x + width/2, test_values, width, label='测试集', alpha=0.7)
            
            ax5.set_title('关键指标对比')
            ax5.set_xticks(x)
            ax5.set_xticklabels(metrics_to_compare, rotation=45, ha='right')
            ax5.legend()
            ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. 累积收益曲线
        ax6 = plt.subplot(3, 2, 6)
        if 'equity_curve' in test_results and not test_results['equity_curve'].empty:
            test_equity = test_results['equity_curve']
            test_equity['cumulative_return'] = (test_equity['equity'] / test_equity['equity'].iloc[0]) - 1
            
            # 对比基准（假设买入持有）
            if 'price' in test_equity.columns:
                test_equity['benchmark_return'] = (test_equity['price'] / test_equity['price'].iloc[0]) - 1
                ax6.plot(test_equity.index, test_equity['benchmark_return'], 'g-', label='买入持有', alpha=0.5)
            
            ax6.plot(test_equity.index, test_equity['cumulative_return'], 'b-', label='策略收益', alpha=0.7)
            ax6.set_title('累积收益 vs 基准')
            ax6.set_xlabel('日期')
            ax6.set_ylabel('累积收益')
            ax6.legend()
            ax6.grid(True, alpha=0.3)
        
        plt.suptitle(f'CTA策略回测报告 - {result_id}', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # 保存图表
        report_path = os.path.join(result_dir, 'report.png')
        plt.savefig(report_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"报告已保存到: {report_path}")
        
        return report_path
    
    def analyze_trades(self, trades_df):
        """
        深入分析交易记录
        """
        if trades_df.empty:
            print("无交易记录可分析")
            return {}
        
        analysis = {}
        
        # 按方向分析
        long_trades = trades_df[trades_df['side'] == 'long']
        short_trades = trades_df[trades_df['side'] == 'short']
        
        analysis['long_trades'] = len(long_trades)
        analysis['short_trades'] = len(short_trades)
        
        # 按退出原因分析
        exit_reasons = trades_df['exit_reason'].value_counts()
        analysis['exit_reasons'] = exit_reasons.to_dict()
        
        # 按小时分析（假设数据有时区信息）
        if 'exit_time' in trades_df.columns:
            trades_df['hour'] = pd.to_datetime(trades_df['exit_time']).dt.hour
            hour_dist = trades_df['hour'].value_counts().sort_index()
            analysis['hourly_distribution'] = hour_dist.to_dict()
        
        # 持仓时间分布
        if 'hold_time' in trades_df.columns:
            hold_stats = {
                'mean': trades_df['hold_time'].mean(),
                'median': trades_df['hold_time'].median(),
                'min': trades_df['hold_time'].min(),
                'max': trades_df['hold_time'].max(),
                'std': trades_df['hold_time'].std()
            }
            analysis['hold_time_stats'] = hold_stats
        
        return analysis
    
    def generate_summary(self, backtest_result):
        """
        生成回测总结
        """
        train_metrics = backtest_result.get('train_metrics', {})
        test_metrics = backtest_result.get('test_metrics', {})
        
        summary = {
            '总体评价': '',
            '关键优势': [],
            '潜在风险': [],
            '改进建议': []
        }
        
        # 总体评价
        if test_metrics.get('夏普比率', 0) > 1.5:
            summary['总体评价'] = '优秀策略，风险调整后收益很高'
        elif test_metrics.get('夏普比率', 0) > 1.0:
            summary['总体评价'] = '良好策略，具有正的风险调整后收益'
        elif test_metrics.get('夏普比率', 0) > 0.5:
            summary['总体评价'] = '一般策略，需要进一步优化'
        else:
            summary['总体评价'] = '需要大幅改进的策略'
        
        # 关键优势
        if test_metrics.get('胜率', 0) > 0.6:
            summary['关键优势'].append('高胜率')
        if test_metrics.get('盈亏比', 0) > 2:
            summary['关键优势'].append('高盈亏比')
        if test_metrics.get('最大回撤', 0) > -0.1:  # 回撤小于10%
            summary['关键优势'].append('低回撤')
        if test_metrics.get('总交易次数', 0) > 20:
            summary['关键优势'].append('充足的交易样本')
        
        # 潜在风险
        if test_metrics.get('最大回撤', 0) < -0.2:  # 回撤大于20%
            summary['潜在风险'].append('回撤较大')
        if test_metrics.get('年化波动率', 0) > 0.3:
            summary['潜在风险'].append('高波动性')
        if test_metrics.get('总交易次数', 0) < 10:
            summary['潜在风险'].append('交易样本不足')
        
        # 改进建议
        if test_metrics.get('夏普比率', 0) < train_metrics.get('夏普比率', 0) * 0.8:
            summary['改进建议'].append('策略可能存在过拟合，需要简化参数')
        if test_metrics.get('平均持仓时间(小时)', 0) < 24:
            summary['改进建议'].append('考虑降低交易频率以减少交易成本')
        if test_metrics.get('胜率', 0) < 0.4:
            summary['改进建议'].append('需要提高信号质量或优化入场条件')
        
        return summary