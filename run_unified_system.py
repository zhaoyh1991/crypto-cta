#!/usr/bin/env python3
"""
统一交易系统运行脚本
支持回测和实盘两种模式
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
import json
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_backtest_mode(args):
    """运行回测模式"""
    logger.info("=" * 60)
    logger.info("启动回测模式")
    logger.info("=" * 60)
    
    try:
        # 导入必要的模块
        from unified_trading_engine import UnifiedTradingEngine
        from cta_strategy_unified import CTAStrategy
        from binance_fetcher import BinanceDataFetcher
        
        # 1. 创建交易引擎（回测模式）
        engine_config = {
            'initial_capital': args.capital,
            'commission': args.commission,
            'mode': 'backtest'
        }
        
        engine = UnifiedTradingEngine(mode='backtest', config=engine_config)
        
        # 2. 设置数据源
        data_fetcher = BinanceDataFetcher(data_dir='data')
        engine.set_data_source(data_fetcher)
        
        # 3. 配置CTA策略
        strategy_config = {
            'fast_period': args.fast_period,
            'slow_period': args.slow_period,
            'rsi_period': 14,
            'bb_period': 20,
            'bb_std': 2.0,
            'atr_period': 14,
            'volume_threshold': 1.2,
            'position_size': args.position_size,
            'stop_loss_pct': args.stop_loss,
            'take_profit_pct': args.take_profit,
            'initial_capital': args.capital,
            'commission': args.commission
        }
        
        # 4. 注册并激活策略
        strategy_id = f"cta_{args.symbol}_{args.timeframe}"
        engine.register_strategy(strategy_id, CTAStrategy, strategy_config)
        engine.activate_strategy(strategy_id, args.symbol)
        
        # 5. 运行回测
        logger.info(f"开始回测: {args.symbol} {args.timeframe}")
        logger.info(f"时间范围: {args.start_date} 到 {args.end_date}")
        
        results = engine.run_backtest(
            start_date=args.start_date,
            end_date=args.end_date,
            symbols=[args.symbol]
        )
        
        # 6. 显示结果
        if results and 'strategies' in results:
            for strategy_id, strategy_results in results['strategies'].items():
                logger.info(f"\n策略 '{strategy_id}' 回测结果:")
                logger.info("-" * 40)
                
                metrics = strategy_results.get('metrics', {})
                if metrics:
                    logger.info(f"初始资金: ${metrics.get('initial_capital', 0):,.2f}")
                    logger.info(f"最终权益: ${metrics.get('final_equity', 0):,.2f}")
                    logger.info(f"总收益率: {metrics.get('total_return', 0)*100:.2f}%")
                    logger.info(f"夏普比率: {metrics.get('sharpe_ratio', 0):.3f}")
                    logger.info(f"最大回撤: {metrics.get('max_drawdown', 0)*100:.2f}%")
                    logger.info(f"总交易次数: {metrics.get('total_trades', 0)}")
                    logger.info(f"胜率: {metrics.get('win_rate', 0)*100:.1f}%")
                    logger.info(f"盈亏比: {metrics.get('profit_factor', 0):.2f}")
                
                # 保存详细结果
                self._save_detailed_results(strategy_results, args)
        
        logger.info("\n回测完成！")
        return True
        
    except Exception as e:
        logger.error(f"回测运行失败: {e}", exc_info=True)
        return False

def run_live_mode(args):
    """运行实盘模式"""
    logger.info("=" * 60)
    logger.info("启动实盘交易模式")
    logger.info("警告：实盘交易涉及真实资金风险！")
    logger.info("=" * 60)
    
    # 确认用户了解风险
    confirmation = input("确认开始实盘交易？(输入 'YES' 继续): ")
    if confirmation != 'YES':
        logger.info("用户取消实盘交易")
        return False
    
    try:
        from unified_trading_engine import UnifiedTradingEngine
        from cta_strategy_unified import CTAStrategy
        
        # 1. 创建交易引擎（实盘模式）
        engine_config = {
            'initial_capital': args.capital,
            'commission': args.commission,
            'mode': 'live'
        }
        
        engine = UnifiedTradingEngine(mode='live', config=engine_config)
        
        # 2. 配置CTA策略
        strategy_config = {
            'fast_period': args.fast_period,
            'slow_period': args.slow_period,
            'position_size': args.position_size,
            'stop_loss_pct': args.stop_loss,
            'take_profit_pct': args.take_profit,
            'initial_capital': args.capital,
            'commission': args.commission
        }
        
        # 3. 注册并激活策略
        strategy_id = f"cta_live_{args.symbol}"
        engine.register_strategy(strategy_id, CTAStrategy, strategy_config)
        
        # 4. 设置交易所连接（需要实际API）
        # 这里需要根据具体交易所实现
        # from binance_exchange import BinanceExchange
        # exchange = BinanceExchange(api_key=args.api_key, api_secret=args.api_secret)
        # engine.set_exchange(exchange)
        
        logger.warning("交易所连接未实现，使用模拟模式")
        
        # 5. 激活策略
        if engine.activate_strategy(strategy_id, args.symbol):
            logger.info(f"策略 '{strategy_id}' 激活成功")
            
            # 6. 开始交易
            logger.info("开始实盘交易...")
            # engine.start_live_trading()
            
            # 这里应该进入监控循环
            logger.info("实盘交易系统就绪（模拟模式）")
            self._monitor_trading(engine)
            
            return True
        else:
            logger.error("策略激活失败")
            return False
            
    except Exception as e:
        logger.error(f"实盘交易启动失败: {e}", exc_info=True)
        return False

def _save_detailed_results(self, results: dict, args):
    """保存详细回测结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = f"results/{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 保存指标
    metrics_file = os.path.join(results_dir, 'metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(results.get('metrics', {}), f, indent=2)
    
    # 保存交易记录
    if 'trades' in results and results['trades']:
        import pandas as pd
        trades_df = pd.DataFrame(results['trades'])
        trades_file = os.path.join(results_dir, 'trades.csv')
        trades_df.to_csv(trades_file, index=False)
    
    # 保存权益曲线
    if 'equity_curve' in results and results['equity_curve']:
        import pandas as pd
        equity_df = pd.DataFrame(results['equity_curve'])
        equity_file = os.path.join(results_dir, 'equity_curve.csv')
        equity_df.to_csv(equity_file, index=False)
    
    # 保存配置
    config = {
        'args': vars(args),
        'timestamp': timestamp,
        'strategy_id': results.get('strategy_id')
    }
    config_file = os.path.join(results_dir, 'config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"详细结果已保存到: {results_dir}")

def _monitor_trading(self, engine):
    """监控交易状态"""
    import time
    
    logger.info("进入交易监控模式...")
    logger.info("按 Ctrl+C 停止交易")
    
    try:
        while True:
            # 获取策略状态
            for strategy_id in engine.active_strategies:
                status = engine.active_strategies[strategy_id]['strategy'].get_status()
                
                logger.info(f"\n策略状态: {strategy_id}")
                logger.info(f"  仓位: {status['position']}")
                logger.info(f"  权益: ${status['equity']:,.2f}")
                logger.info(f"  交易次数: {status['total_trades']}")
            
            time.sleep(10)  # 每10秒更新一次
            
    except KeyboardInterrupt:
        logger.info("\n用户停止交易")
        # engine.stop_trading()

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='统一交易系统 - 支持回测和实盘')
    
    # 模式选择
    parser.add_argument('--mode', type=str, default='backtest',
                       choices=['backtest', 'live'],
                       help='运行模式: backtest(回测) 或 live(实盘)')
    
    # 交易参数
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='交易对 (默认: BTCUSDT)')
    parser.add_argument('--timeframe', type=str, default='1h',
                       choices=['1h', '4h', '1d'],
                       help='时间框架 (默认: 1h)')
    
    # 资金参数
    parser.add_argument('--capital', type=float, default=10000,
                       help='初始资金 (默认: 10000)')
    parser.add_argument('--commission', type=float, default=0.001,
                       help='交易手续费 (默认: 0.001 = 0.1%%)')
    
    # 策略参数
    parser.add_argument('--fast-period', type=int, default=12,
                       help='快速均线周期 (默认: 12)')
    parser.add_argument('--slow-period', type=int, default=48,
                       help='慢速均线周期 (默认: 48)')
    parser.add_argument('--position-size', type=float, default=0.1,
                       help='仓位大小比例 (默认: 0.1 = 10%%)')
    parser.add_argument('--stop-loss', type=float, default=0.015,
                       help='止损比例 (默认: 0.015 = 1.5%%)')
    parser.add_argument('--take-profit', type=float, default=0.03,
                       help='止盈比例 (默认: 0.03 = 3%%)')
    
    # 回测特定参数
    parser.add_argument('--start-date', type=str, default=None,
                       help='回测开始日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='回测结束日期 (格式: YYYY-MM-DD)')
    
    # 实盘特定参数
    parser.add_argument('--api-key', type=str, default='',
                       help='交易所API Key (实盘模式需要)')
    parser.add_argument('--api-secret', type=str, default='',
                       help='交易所API Secret (实盘模式需要)')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置默认日期（如果未提供）
    if args.mode == 'backtest':
        if not args.start_date:
            args.start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        if not args.end_date:
            args.end_date = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"\n统一交易系统启动")
    logger.info(f"模式: {args.mode}")
    logger.info(f"交易对: {args.symbol}")
    logger.info(f"时间框架: {args.timeframe}")
    logger.info(f"初始资金: ${args.capital:,.2f}")
    
    if args.mode == 'backtest':
        logger.info(f"回测期间: {args.start_date} 到 {args.end_date}")
        success = run_backtest_mode(args)
    else:
        logger.info("实盘交易模式")
        success = run_live_mode(args)
    
    if success:
        logger.info("\n✅ 交易系统运行完成")
    else:
        logger.error("\n❌ 交易系统运行失败")
    
    return success

if __name__ == "__main__":
    main()