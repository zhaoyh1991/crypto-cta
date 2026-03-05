#!/usr/bin/env python3
"""
实盘交易运行脚本
支持模拟交易和真实交易
"""

import argparse
import sys
import os
import json
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_file: str = 'config_unified.json') -> dict:
    """加载配置文件"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"配置文件加载成功: {config_file}")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}

def setup_environment():
    """设置环境"""
    # 创建必要的目录
    directories = ['logs/live', 'data/live', 'results/live', 'backups']
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
    
    logger.info("环境设置完成")

def run_paper_trading(args, config):
    """运行模拟交易"""
    logger.info("=" * 60)
    logger.info("启动模拟交易")
    logger.info("=" * 60)
    
    try:
        from live_trading_manager import LiveTradingManager, TradingMode
        from cta_strategy_unified import CTAStrategy
        
        # 创建交易管理器配置
        manager_config = {
            'mode': 'paper',
            'risk_level': args.risk_level,
            'max_daily_loss': args.max_daily_loss,
            'max_position_size': args.max_position_size,
            'max_concurrent_trades': args.max_concurrent_trades,
            'monitoring_interval': args.monitoring_interval
        }
        
        # 创建交易管理器
        manager = LiveTradingManager(manager_config)
        
        # 连接模拟交易所
        exchange_config = {
            'initial_balance': args.capital,
            'commission': args.commission
        }
        
        if not manager.connect_exchange(exchange_config):
            logger.error("连接交易所失败")
            return False
        
        # 配置CTA策略
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
        
        # 注册并激活策略
        strategy_id = f"cta_{args.symbol}_paper"
        manager.register_strategy(strategy_id, CTAStrategy, strategy_config)
        
        if manager.activate_strategy(strategy_id, args.symbol):
            logger.info(f"策略 '{strategy_id}' 激活成功")
        else:
            logger.error("策略激活失败")
            return False
        
        # 开始交易
        logger.info("开始模拟交易...")
        if manager.start_trading():
            logger.info("模拟交易启动成功")
            
            # 这里应该进入监控循环
            # 实际实现中，manager.start_trading()会启动后台线程
            # 这里简化处理，等待用户输入停止
            
            input("按 Enter 键停止模拟交易...\n")
            manager.stop_trading()
            
            return True
        else:
            logger.error("模拟交易启动失败")
            return False
            
    except Exception as e:
        logger.error(f"模拟交易运行失败: {e}", exc_info=True)
        return False

def run_live_trading(args, config):
    """运行实盘交易"""
    logger.info("=" * 60)
    logger.info("启动实盘交易")
    logger.info("⚠️  警告：实盘交易涉及真实资金风险！")
    logger.info("=" * 60)
    
    # 风险确认
    confirmation = input("""
    ⚠️  实盘交易风险确认 ⚠️
    
    您即将开始实盘交易，涉及真实资金！
    
    请确认：
    1. 您已充分理解交易风险
    2. 您已进行充分的回测和模拟测试
    3. 您使用的是可承受损失的资金
    4. 您已设置适当的风险控制
    
    输入 'YES' 继续，或输入其他内容取消：
    """)
    
    if confirmation.strip().upper() != 'YES':
        logger.info("用户取消实盘交易")
        return False
    
    try:
        from live_trading_manager import LiveTradingManager, TradingMode
        from cta_strategy_unified import CTAStrategy
        
        # 检查API密钥
        if not args.api_key or not args.api_secret:
            logger.error("需要API密钥和密钥进行实盘交易")
            logger.info("请使用 --api-key 和 --api-secret 参数")
            return False
        
        # 创建交易管理器配置
        manager_config = {
            'mode': 'live',
            'risk_level': args.risk_level,
            'max_daily_loss': args.max_daily_loss,
            'max_position_size': args.max_position_size,
            'max_concurrent_trades': args.max_concurrent_trades,
            'monitoring_interval': args.monitoring_interval
        }
        
        # 创建交易管理器
        manager = LiveTradingManager(manager_config)
        
        # 连接币安交易所
        exchange_config = {
            'api_key': args.api_key,
            'api_secret': args.api_secret,
            'testnet': args.testnet  # 建议先用测试网
        }
        
        if not manager.connect_exchange(exchange_config):
            logger.error("连接交易所失败")
            return False
        
        # 配置CTA策略
        strategy_config = {
            'fast_period': args.fast_period,
            'slow_period': args.slow_period,
            'position_size': args.position_size,
            'stop_loss_pct': args.stop_loss,
            'take_profit_pct': args.take_profit,
            'initial_capital': args.capital,
            'commission': args.commission
        }
        
        # 注册并激活策略
        strategy_id = f"cta_{args.symbol}_live"
        manager.register_strategy(strategy_id, CTAStrategy, strategy_config)
        
        if manager.activate_strategy(strategy_id, args.symbol):
            logger.info(f"策略 '{strategy_id}' 激活成功")
        else:
            logger.error("策略激活失败")
            return False
        
        # 开始交易
        logger.info("开始实盘交易...")
        if manager.start_trading():
            logger.info("实盘交易启动成功")
            
            # 这里应该进入监控循环
            # 实际实现中，manager.start_trading()会启动后台线程
            
            input("按 Enter 键停止实盘交易...\n")
            manager.stop_trading()
            
            return True
        else:
            logger.error("实盘交易启动失败")
            return False
            
    except Exception as e:
        logger.error(f"实盘交易运行失败: {e}", exc_info=True)
        return False

def run_backtest(args, config):
    """运行回测"""
    logger.info("=" * 60)
    logger.info("启动回测")
    logger.info("=" * 60)
    
    try:
        # 使用统一的回测系统
        from run_unified_system import run_backtest_mode
        
        # 设置参数
        import types
        args.mode = 'backtest'
        
        return run_backtest_mode(args)
        
    except Exception as e:
        logger.error(f"回测运行失败: {e}", exc_info=True)
        return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='CTA交易系统 - 支持回测、模拟交易和实盘交易')
    
    # 模式选择
    parser.add_argument('--mode', type=str, default='paper',
                       choices=['backtest', 'paper', 'live'],
                       help='运行模式: backtest(回测), paper(模拟交易), live(实盘交易)')
    
    # 交易参数
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='交易对 (默认: BTCUSDT)')
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
    
    # 风险控制
    parser.add_argument('--risk-level', type=str, default='medium',
                       choices=['low', 'medium', 'high'],
                       help='风险等级 (默认: medium)')
    parser.add_argument('--max-daily-loss', type=float, default=0.05,
                       help='最大单日亏损比例 (默认: 0.05 = 5%%)')
    parser.add_argument('--max-position-size', type=float, default=0.2,
                       help='最大仓位比例 (默认: 0.2 = 20%%)')
    parser.add_argument('--max-concurrent-trades', type=int, default=3,
                       help='最大并发交易数 (默认: 3)')
    
    # 监控参数
    parser.add_argument('--monitoring-interval', type=int, default=60,
                       help='监控间隔(秒) (默认: 60)')
    
    # 实盘交易参数
    parser.add_argument('--api-key', type=str, default='',
                       help='币安API Key (实盘交易需要)')
    parser.add_argument('--api-secret', type=str, default='',
                       help='币安API Secret (实盘交易需要)')
    parser.add_argument('--testnet', action='store_true',
                       help='使用币安测试网络 (实盘交易建议先测试)')
    
    # 其他参数
    parser.add_argument('--config', type=str, default='config_unified.json',
                       help='配置文件路径 (默认: config_unified.json)')
    parser.add_argument('--list-modes', action='store_true',
                       help='列出所有运行模式')
    
    return parser.parse_args()

def list_modes():
    """列出所有运行模式"""
    print("""
    CTA交易系统 - 运行模式
    
    1. 回测模式 (backtest)
       用途: 历史数据测试策略性能
       命令: python run_live_trading.py --mode backtest --symbol BTCUSDT
       
    2. 模拟交易模式 (paper)
       用途: 模拟真实交易，无资金风险
       命令: python run_live_trading.py --mode paper --symbol BTCUSDT --capital 10000
       
    3. 实盘交易模式 (live)
       用途: 真实资金交易，需要API密钥
       命令: python run_live_trading.py --mode live --symbol BTCUSDT --api-key YOUR_KEY --api-secret YOUR_SECRET
       
    安全建议:
    1. 先回测，再模拟，最后实盘
    2. 实盘交易从小资金开始
    3. 设置严格的风险控制
    4. 持续监控交易表现
    """)

def main():
    """主函数"""
    args = parse_arguments()
    
    if args.list_modes:
        list_modes()
        return True
    
    # 设置环境
    setup_environment()
    
    # 加载配置
    config = load_config(args.config)
    
    logger.info(f"\nCTA交易系统启动")
    logger.info(f"模式: {args.mode}")
    logger.info(f"交易对: {args.symbol}")
    logger.info(f"初始资金: ${args.capital:,.2f}")
    logger.info(f"风险等级: {args.risk_level}")
    
    # 根据模式运行
    if args.mode == 'backtest':
        success = run_backtest(args, config)
    elif args.mode == 'paper':
        success = run_paper_trading(args, config)
    elif args.mode == 'live':
        success = run_live_trading(args, config)
    else:
        logger.error(f"不支持的模式: {args.mode}")
        success = False
    
    if success:
        logger.info("\n✅ 交易系统运行完成")
    else:
        logger.error("\n❌ 交易系统运行失败")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)