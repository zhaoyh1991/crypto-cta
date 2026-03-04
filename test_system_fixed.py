#!/usr/bin/env python3
"""
测试1小时级别CTA回测系统（修复版）
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    modules = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('matplotlib', 'matplotlib'),
        ('python-binance', 'binance'),
        ('ccxt', 'ccxt')
    ]
    
    all_ok = True
    for module_name, import_name in modules:
        try:
            __import__(import_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            all_ok = False
    
    return all_ok

def test_project_modules():
    """测试项目模块"""
    print("\n测试项目模块导入...")
    
    modules = [
        ('binance_fetcher', 'from binance_fetcher import BinanceDataFetcher'),
        ('cta_strategy', 'from src.cta_strategy import CryptoCTAStrategy'),
        ('backtester', 'from src.backtester import Backtester')
    ]
    
    all_ok = True
    for module_name, import_stmt in modules:
        try:
            exec(import_stmt)
            print(f"  ✓ {module_name}")
        except Exception as e:
            print(f"  ✗ {module_name}: {e}")
            all_ok = False
    
    return all_ok

def test_binance_fetcher():
    """测试币安数据获取"""
    print("\n测试币安数据获取...")
    
    try:
        from binance_fetcher import BinanceDataFetcher
        
        fetcher = BinanceDataFetcher()
        
        # 测试获取交易对列表
        symbols = fetcher.get_available_symbols()[:3]
        print(f"  ✓ 获取交易对列表: {symbols}")
        
        # 测试获取数据（使用模拟数据）
        df = fetcher.fetch_klines('BTCUSDT', '1h', limit=24)
        if df is not None and not df.empty:
            print(f"  ✓ 获取数据成功: {len(df)} 条记录")
            print(f"     时间范围: {df.index[0]} 到 {df.index[-1]}")
            print(f"     价格范围: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
            print(f"     数据列: {list(df.columns)}")
            return True
        else:
            print("  ✗ 获取数据失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {e}")
        return False

def test_strategy():
    """测试策略"""
    print("\n测试CTA策略...")
    
    try:
        from src.cta_strategy import CryptoCTAStrategy
        
        # 创建策略实例
        strategy = CryptoCTAStrategy()
        print(f"  ✓ 策略初始化成功")
        
        # 创建测试数据
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2023-01-01', periods=100, freq='1h')
        np.random.seed(42)
        
        test_df = pd.DataFrame(index=dates)
        test_df['open'] = np.random.normal(50000, 1000, 100)
        test_df['high'] = test_df['open'] + np.random.uniform(0, 500, 100)
        test_df['low'] = test_df['open'] - np.random.uniform(0, 500, 100)
        test_df['close'] = (test_df['high'] + test_df['low']) / 2
        test_df['volume'] = np.random.uniform(1000, 10000, 100)
        
        # 测试生成信号
        df_with_signals = strategy.generate_signals(test_df)
        print(f"  ✓ 生成信号成功")
        
        # 检查信号列
        signal_cols = [col for col in df_with_signals.columns if 'signal' in col.lower()]
        print(f"     信号列: {signal_cols}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_backtest():
    """测试简单回测"""
    print("\n测试简单回测...")
    
    try:
        from src.cta_strategy import CryptoCTAStrategy
        from src.backtester import Backtester
        
        # 创建策略
        strategy = CryptoCTAStrategy()
        
        # 创建回测器
        backtester = Backtester(results_dir='test_results')
        print(f"  ✓ 回测器初始化成功")
        
        # 创建测试数据
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2023-01-01', periods=200, freq='1h')
        np.random.seed(42)
        
        test_df = pd.DataFrame(index=dates)
        test_df['open'] = 50000 + np.cumsum(np.random.normal(0, 100, 200))
        test_df['high'] = test_df['open'] + np.random.uniform(0, 500, 200)
        test_df['low'] = test_df['open'] - np.random.uniform(0, 500, 200)
        test_df['close'] = (test_df['high'] + test_df['low']) / 2
        test_df['volume'] = np.random.uniform(1000, 10000, 200)
        
        # 生成信号
        df_with_signals = strategy.generate_signals(test_df)
        
        # 运行回测（使用策略的run_backtest方法）
        results = strategy.run_backtest(df_with_signals, initial_capital=10000)
        
        if results:
            print(f"  ✓ 回测运行成功")
            print(f"     最终权益: ${results.get('final_equity', 0):.2f}")
            print(f"     总交易次数: {len(results.get('trades', []))}")
            return True
        else:
            print("  ✗ 回测运行失败")
            return False
        
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hourly_backtester():
    """测试1小时回测器"""
    print("\n测试1小时回测器...")
    
    try:
        # 先创建必要的目录
        os.makedirs('data_1h', exist_ok=True)
        os.makedirs('results_1h', exist_ok=True)
        
        # 动态导入
        import importlib
        import sys
        
        # 导入模块
        binance_fetcher = importlib.import_module('binance_fetcher')
        backtest_1h = importlib.import_module('backtest_1h')
        
        # 创建实例
        HourlyBacktester = backtest_1h.HourlyBacktester
        backtester = HourlyBacktester(initial_capital=1000, commission=0.001)
        
        print(f"  ✓ 1小时回测器初始化成功")
        
        # 测试快速方法
        result = backtester.run_quick_test('BTCUSDT', days=3)
        
        print(f"  ✓ 快速测试完成:")
        print(f"     数据点: {result.get('data_points', 0)}")
        print(f"     信号数: {result.get('signals_generated', 0)}")
        print(f"     交易数: {result.get('trades_executed', 0)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("1小时级别CTA回测系统测试（修复版）")
    print("=" * 60)
    
    tests = [
        ("基础依赖", test_imports),
        ("项目模块", test_project_modules),
        ("币安数据获取", test_binance_fetcher),
        ("CTA策略", test_strategy),
        ("简单回测", test_simple_backtest),
        ("1小时回测器", test_hourly_backtester)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n▶ 运行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ✗ 测试异常: {type(e).__name__}: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name:20} {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！系统可以正常运行。")
    else:
        print("⚠️  部分测试失败，但核心功能可能仍可用。")
    
    print("\n使用建议:")
    print("1. 首次运行: python run_1h_backtest.py --symbol BTCUSDT --days 30")
    print("2. 查看帮助: python run_1h_backtest.py --help")
    print("3. 批量测试: python run_1h_backtest.py --batch BTCUSDT ETHUSDT")
    
    print("=" * 60)

if __name__ == "__main__":
    main()