#!/usr/bin/env python3
"""
统一交易系统演示 - 使用模拟数据
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_mock_data(symbol='BTCUSDT', days=30, interval='1h'):
    """生成模拟数据"""
    logger.info(f"生成 {symbol} 模拟数据 ({days}天, {interval})")
    
    # 计算数据点数量
    if interval == '1h':
        periods = days * 24
        freq = '1h'
    elif interval == '4h':
        periods = days * 6
        freq = '4h'
    else:
        periods = days
        freq = '1D'
    
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
    returns = np.random.normal(0.0005, 0.015, len(dates))  # 0.05%平均收益，1.5%波动
    trend = np.linspace(0, 0.1, len(dates))  # 10%的趋势
    returns += trend / len(dates)
    
    price = start_price * np.exp(np.cumsum(returns))
    
    # 生成OHLCV数据
    df = pd.DataFrame(index=dates)
    df['close'] = price
    
    # 开盘价（接近前一日收盘价）
    open_prices = df['close'].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
    open_prices.iloc[0] = start_price
    df['open'] = open_prices
    
    # 高低价
    price_range = df['close'] * 0.03  # 3%的价格范围
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.5, len(dates)) * price_range
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.5, len(dates)) * price_range
    
    # 确保 high >= low
    high_low_df = df[['high', 'low']]
    df['high'] = high_low_df.max(axis=1)
    df['low'] = high_low_df.min(axis=1)
    
    # 成交量
    df['volume'] = 1000 * (1 + np.abs(returns) * 10) * np.random.uniform(0.8, 1.2, len(dates))
    
    logger.info(f"生成 {len(df)} 条数据，价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    return df

def run_demo():
    """运行演示"""
    logger.info("=" * 60)
    logger.info("统一交易系统演示")
    logger.info("=" * 60)
    
    try:
        from unified_trading_engine import UnifiedTradingEngine
        from cta_strategy_unified import CTAStrategy
        
        # 1. 创建交易引擎
        engine_config = {
            'initial_capital': 10000,
            'commission': 0.001,
            'mode': 'backtest'
        }
        
        engine = UnifiedTradingEngine(mode='backtest', config=engine_config)
        logger.info("✓ 交易引擎创建成功")
        
        # 2. 创建模拟数据源
        class MockDataSource:
            def fetch_klines(self, symbol, interval, start_time, end_time, limit):
                days = (datetime.strptime(end_time, '%Y-%m-%d') - 
                       datetime.strptime(start_time, '%Y-%m-%d')).days
                return generate_mock_data(symbol, days, interval)
        
        mock_data_source = MockDataSource()
        engine.set_data_source(mock_data_source)
        logger.info("✓ 模拟数据源设置成功")
        
        # 3. 配置CTA策略
        strategy_config = {
            'fast_period': 12,
            'slow_period': 48,
            'rsi_period': 14,
            'bb_period': 20,
            'bb_std': 2.0,
            'atr_period': 14,
            'volume_threshold': 1.2,
            'position_size': 0.1,
            'stop_loss_pct': 0.015,
            'take_profit_pct': 0.03,
            'initial_capital': 10000,
            'commission': 0.001
        }
        
        # 4. 注册并激活策略
        strategy_id = "cta_demo_btc"
        engine.register_strategy(strategy_id, CTAStrategy, strategy_config)
        
        if engine.activate_strategy(strategy_id, 'BTCUSDT'):
            logger.info("✓ 策略激活成功")
        else:
            logger.error("✗ 策略激活失败")
            return False
        
        # 5. 运行回测
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"运行回测: {start_date} 到 {end_date}")
        results = engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            symbols=['BTCUSDT']
        )
        
        # 6. 显示结果
        if results and 'strategies' in results:
            for strategy_id, strategy_results in results['strategies'].items():
                logger.info(f"\n策略 '{strategy_id}' 结果:")
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
                    
                    # 显示最近几笔交易
                    trades = strategy_results.get('trades', [])
                    if trades:
                        logger.info(f"\n最近5笔交易:")
                        for i, trade in enumerate(trades[-5:], 1):
                            side = "买入" if trade['side'] == 'buy' else "卖出"
                            pnl_pct = trade.get('pnl_pct', 0) * 100 if 'pnl_pct' in trade else 0
                            logger.info(f"  {i}. {side} @ ${trade['price']:.2f} "
                                      f"({trade.get('reason', 'N/A')}) "
                                      f"盈亏: {pnl_pct:+.2f}%")
        
        # 7. 保存结果
        if results:
            import json
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            demo_dir = f"demo_results_{timestamp}"
            os.makedirs(demo_dir, exist_ok=True)
            
            # 保存摘要
            summary = {
                'timestamp': timestamp,
                'strategy': strategy_id,
                'period': f"{start_date} to {end_date}",
                'metrics': metrics
            }
            
            with open(os.path.join(demo_dir, 'summary.json'), 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"\n演示结果已保存到: {demo_dir}/")
        
        logger.info("\n✅ 演示完成！")
        return True
        
    except Exception as e:
        logger.error(f"演示失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)