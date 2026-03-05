#!/usr/bin/env python3
"""
测试统一交易系统
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_base_strategy():
    """测试策略基类"""
    print("测试策略基类...")
    
    try:
        # 导入基类
        from base_strategy import BaseStrategy
        
        # 创建测试策略类
        class TestStrategy(BaseStrategy):
            def initialize(self, data):
                print("  ✓ initialize方法")
                
            def calculate_indicators(self, data):
                print("  ✓ calculate_indicators方法")
                return data
                
            def generate_signals(self, data):
                print("  ✓ generate_signals方法")
                return pd.Series([0] * len(data), index=data.index)
        
        # 创建策略实例
        config = {
            'initial_capital': 10000,
            'commission': 0.001
        }
        
        strategy = TestStrategy("test_strategy", config)
        
        # 测试方法
        test_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [102, 103, 104],
            'volume': [1000, 1100, 1200]
        })
        
        strategy.initialize(test_data)
        
        bar = {
            'timestamp': datetime.now(),
            'open': 100,
            'high': 105,
            'low': 95,
            'close': 102,
            'volume': 1000
        }
        
        result = strategy.on_bar(bar)
        print(f"  ✓ on_bar方法返回: {result.get('signal', 'N/A')}")
        
        status = strategy.get_status()
        print(f"  ✓ get_status方法: {status['name']}")
        
        print("  ✅ 策略基类测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 策略基类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cta_strategy():
    """测试CTA策略"""
    print("\n测试CTA策略...")
    
    try:
        from cta_strategy_unified import CTAStrategy
        
        # 创建策略配置
        config = {
            'fast_period': 12,
            'slow_period': 48,
            'rsi_period': 14,
            'bb_period': 20,
            'position_size': 0.1,
            'stop_loss_pct': 0.015,
            'take_profit_pct': 0.03,
            'initial_capital': 10000,
            'commission': 0.001
        }
        
        # 创建策略实例
        strategy = CTAStrategy("cta_test", config)
        print("  ✓ CTA策略实例化成功")
        
        # 生成测试数据
        dates = pd.date_range('2025-01-01', periods=100, freq='1h')
        np.random.seed(42)
        
        test_data = pd.DataFrame(index=dates)
        test_data['open'] = 50000 + np.cumsum(np.random.normal(0, 100, 100))
        test_data['high'] = test_data['open'] + np.random.uniform(0, 500, 100)
        test_data['low'] = test_data['open'] - np.random.uniform(0, 500, 100)
        test_data['close'] = (test_data['high'] + test_data['low']) / 2
        test_data['volume'] = np.random.uniform(1000, 10000, 100)
        
        # 测试初始化
        strategy.initialize(test_data)
        print("  ✓ 策略初始化成功")
        
        # 测试指标计算
        data_with_indicators = strategy.calculate_indicators(test_data)
        indicator_cols = [col for col in data_with_indicators.columns 
                         if col not in ['open', 'high', 'low', 'close', 'volume']]
        print(f"  ✓ 计算技术指标: {len(indicator_cols)} 个")
        
        # 测试信号生成
        signals = strategy.generate_signals(data_with_indicators)
        buy_signals = (signals == 1).sum()
        sell_signals = (signals == -1).sum()
        print(f"  ✓ 生成信号: 买入{buy_signals}个, 卖出{sell_signals}个")
        
        # 测试单根K线处理
        bar = {
            'timestamp': dates[-1],
            'open': test_data['open'].iloc[-1],
            'high': test_data['high'].iloc[-1],
            'low': test_data['low'].iloc[-1],
            'close': test_data['close'].iloc[-1],
            'volume': test_data['volume'].iloc[-1]
        }
        
        result = strategy.on_bar(bar)
        print(f"  ✓ 处理单根K线: 信号={result.get('signal', 'N/A')}")
        
        # 测试状态获取
        status = strategy.get_status()
        print(f"  ✓ 获取策略状态: {status['name']}, 仓位={status['position']}")
        
        print("  ✅ CTA策略测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ CTA策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trading_engine():
    """测试交易引擎"""
    print("\n测试交易引擎...")
    
    try:
        from unified_trading_engine import UnifiedTradingEngine
        
        # 创建回测引擎
        engine_config = {
            'initial_capital': 10000,
            'commission': 0.001,
            'mode': 'backtest'
        }
        
        engine = UnifiedTradingEngine(mode='backtest', config=engine_config)
        print("  ✓ 交易引擎实例化成功")
        
        # 测试目录创建
        if os.path.exists('logs') and os.path.exists('data'):
            print("  ✓ 必要目录创建成功")
        
        print("  ✅ 交易引擎基础测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 交易引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """测试集成功能"""
    print("\n测试集成功能...")
    
    try:
        from unified_trading_engine import UnifiedTradingEngine
        from cta_strategy_unified import CTAStrategy
        
        # 创建引擎
        engine = UnifiedTradingEngine(mode='backtest')
        
        # 策略配置
        strategy_config = {
            'fast_period': 12,
            'slow_period': 48,
            'position_size': 0.1,
            'initial_capital': 10000
        }
        
        # 注册策略
        success = engine.register_strategy("test_integration", CTAStrategy, strategy_config)
        if success:
            print("  ✓ 策略注册成功")
        else:
            print("  ❌ 策略注册失败")
            return False
        
        print("  ✅ 集成测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("统一交易系统测试")
    print("=" * 60)
    
    tests = [
        ("策略基类", test_base_strategy),
        ("CTA策略", test_cta_strategy),
        ("交易引擎", test_trading_engine),
        ("集成功能", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n▶ 运行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:15} {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！统一系统可以正常运行。")
        print("\n下一步:")
        print("1. 运行回测: python run_unified_system.py --mode backtest")
        print("2. 查看配置: cat config_unified.json")
        print("3. 学习使用: cat SETUP_UNIFIED_SYSTEM.md")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)