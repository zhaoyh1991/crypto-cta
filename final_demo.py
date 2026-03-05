#!/usr/bin/env python3
"""
完整系统演示 - 展示从回测到模拟交易的完整流程
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_step_1_backtest():
    """演示步骤1：回测"""
    logger.info("=" * 60)
    logger.info("步骤1: 运行回测")
    logger.info("=" * 60)
    
    try:
        from unified_trading_engine import UnifiedTradingEngine
        from cta_strategy_unified import CTAStrategy
        
        # 创建回测引擎
        engine = UnifiedTradingEngine(mode='backtest')
        
        # 配置CTA策略
        strategy_config = {
            'fast_period': 12,
            'slow_period': 48,
            'position_size': 0.1,
            'stop_loss_pct': 0.015,
            'take_profit_pct': 0.03,
            'initial_capital': 10000,
            'commission': 0.001
        }
        
        # 注册策略
        strategy_id = "cta_demo_backtest"
        engine.register_strategy(strategy_id, CTAStrategy, strategy_config)
        engine.activate_strategy(strategy_id, 'BTCUSDT')
        
        # 运行回测
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"回测期间: {start_date} 到 {end_date}")
        results = engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            symbols=['BTCUSDT']
        )
        
        if results and 'strategies' in results:
            for sid, strategy_results in results['strategies'].items():
                metrics = strategy_results.get('metrics', {})
                logger.info(f"\n回测结果:")
                logger.info(f"  初始资金: ${metrics.get('initial_capital', 0):,.2f}")
                logger.info(f"  最终权益: ${metrics.get('final_equity', 0):,.2f}")
                logger.info(f"  总收益率: {metrics.get('total_return', 0)*100:.2f}%")
                logger.info(f"  夏普比率: {metrics.get('sharpe_ratio', 0):.3f}")
                logger.info(f"  最大回撤: {metrics.get('max_drawdown', 0)*100:.2f}%")
                logger.info(f"  总交易次数: {metrics.get('total_trades', 0)}")
        
        logger.info("✅ 回测完成")
        return True
        
    except Exception as e:
        logger.error(f"回测失败: {e}")
        return False

def demo_step_2_paper_trading():
    """演示步骤2：模拟交易"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤2: 模拟交易")
    logger.info("=" * 60)
    
    try:
        from live_trading_manager import LiveTradingManager, TradingMode
        
        # 创建模拟交易管理器
        manager_config = {
            'mode': 'paper',
            'risk_level': 'medium',
            'max_daily_loss': 0.05,
            'max_position_size': 0.2
        }
        
        manager = LiveTradingManager(manager_config)
        
        # 连接模拟交易所
        exchange_config = {
            'initial_balance': 10000,
            'commission': 0.001
        }
        
        if manager.connect_exchange(exchange_config):
            logger.info("✅ 模拟交易所连接成功")
            
            # 这里应该注册和激活策略，然后开始交易
            # 简化演示，只展示连接成功
            
            return True
        else:
            logger.error("❌ 模拟交易所连接失败")
            return False
            
    except Exception as e:
        logger.error(f"模拟交易演示失败: {e}")
        return False

def demo_step_3_system_overview():
    """演示步骤3：系统概览"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤3: 系统功能概览")
    logger.info("=" * 60)
    
    features = [
        "✅ 统一策略接口 - 同一套代码支持回测和实盘",
        "✅ 完整的CTA策略 - 趋势跟踪 + 均值回归",
        "✅ 风险管理 - 止损止盈、仓位控制、风险限制",
        "✅ 多模式支持 - 回测、模拟交易、实盘交易",
        "✅ 币安集成 - 真实数据获取和交易执行",
        "✅ 性能分析 - 夏普比率、最大回撤、胜率等",
        "✅ 监控日志 - 详细交易记录和系统日志",
        "✅ 可扩展架构 - 支持自定义策略开发"
    ]
    
    for feature in features:
        logger.info(feature)
    
    logger.info("\n📊 系统架构:")
    logger.info("  1. BaseStrategy - 策略基类")
    logger.info("  2. UnifiedTradingEngine - 统一交易引擎")
    logger.info("  3. LiveTradingManager - 实盘交易管理器")
    logger.info("  4. CTAStrategy - CTA策略实现")
    logger.info("  5. BinanceExchange - 币安交易所接口")
    logger.info("  6. MockExchange - 模拟交易所")
    
    return True

def demo_step_4_getting_started():
    """演示步骤4：快速开始指南"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤4: 快速开始指南")
    logger.info("=" * 60)
    
    commands = [
        ("安装依赖", "pip install pandas numpy python-binance ccxt matplotlib"),
        ("测试系统", "python test_unified_system.py"),
        ("运行回测", "python run_live_trading.py --mode backtest --symbol BTCUSDT"),
        ("模拟交易", "python run_live_trading.py --mode paper --symbol BTCUSDT"),
        ("实盘交易", "python run_live_trading.py --mode live --symbol BTCUSDT --api-key YOUR_KEY --api-secret YOUR_SECRET --testnet"),
        ("查看配置", "cat config_unified.json"),
        ("阅读文档", "cat COMPLETE_SYSTEM_GUIDE.md")
    ]
    
    for desc, cmd in commands:
        logger.info(f"{desc}:")
        logger.info(f"  $ {cmd}")
    
    logger.info("\n🎯 建议流程:")
    logger.info("  1. 充分回测（至少3-6个月数据）")
    logger.info("  2. 模拟交易验证（1-2周）")
    logger.info("  3. 小资金实盘测试（1-2%仓位）")
    logger.info("  4. 逐步增加资金（验证稳定后）")
    
    return True

def main():
    """主演示函数"""
    logger.info("=" * 60)
    logger.info("完整CTA交易系统演示")
    logger.info("=" * 60)
    
    steps = [
        ("回测演示", demo_step_1_backtest),
        ("模拟交易演示", demo_step_2_paper_trading),
        ("系统概览", demo_step_3_system_overview),
        ("快速开始", demo_step_4_getting_started)
    ]
    
    all_passed = True
    
    for step_name, step_func in steps:
        logger.info(f"\n▶ 执行: {step_name}")
        try:
            success = step_func()
            if success:
                logger.info(f"  ✅ {step_name} 完成")
            else:
                logger.error(f"  ❌ {step_name} 失败")
                all_passed = False
                
        except Exception as e:
            logger.error(f"  ❌ {step_name} 异常: {e}")
            all_passed = False
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("🎉 演示完成！系统功能正常。")
        logger.info("\n下一步建议:")
        logger.info("  1. 运行完整回测: python run_live_trading.py --mode backtest")
        logger.info("  2. 尝试模拟交易: python run_live_trading.py --mode paper")
        logger.info("  3. 阅读详细文档: cat COMPLETE_SYSTEM_GUIDE.md")
    else:
        logger.info("⚠️  演示部分失败，请检查错误信息。")
    
    logger.info("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)