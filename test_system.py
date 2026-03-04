#!/usr/bin/env python3
"""
测试1小时级别CTA回测系统
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
        ('binance_fetcher', 'BinanceDataFetcher'),
        ('backtest_1h', 'HourlyBacktester')
    ]
    
    all_ok = True
    for module_name, import_name in modules:
        try:
            if '.' in import_name:
                # 处理从模块导入类的情况
                module, cls = import_name.split('.')
                exec(f"from {module} import {cls}")
                print(f"  ✓ {module_name}")
            else:
                __import__(import_name)
                print(f"  ✓ {module_name}")
        except ImportError as e:
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
            return True
        else:
            print("  ✗ 获取数据失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy():
    """测试策略"""
    print("\n测试CTA策略...")
    
    try:
        from src.cta_strategy import CryptoCTAStrategy
        
        # 创建策略实例
        strategy = CryptoCTAStrategy()
        print(f"  ✓ 策略初始化成功")
        
        # 测试参数
        params = strategy.get_parameters()
        print(f"  ✓ 策略参数: {params}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtester():
    """测试回测器"""
    print("\n测试回测器...")
    
    try:
        from backtest_1h import HourlyBacktester
        
        # 创建回测器实例
        backtester = HourlyBacktester(initial_capital=1000, commission=0.001)
        print(f"  ✓ 回测器初始化成功")
        
        # 运行快速测试
        result = backtester.run_quick_test('BTCUSDT', days=3)
        
        if 'error' in result:
            print(f"  ✗ 快速测试失败: {result['error']}")
            return False
        
        print(f"  ✓ 快速测试成功:")
        print(f"     数据点: {result['data_points']}")
        print(f"     生成信号: {result['signals_generated']}")
        print(f"     执行交易: {result['trades_executed']}")
        print(f"     最终权益: ${result['final_equity']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("1小时级别CTA回测系统测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("币安数据获取", test_binance_fetcher),
        ("CTA策略", test_strategy),
        ("回测器", test_backtester)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n▶ 运行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ✗ 测试异常: {e}")
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
        print("\n下一步:")
        print("1. 运行完整回测: python run_1h_backtest.py")
        print("2. 查看可用交易对: python run_1h_backtest.py --list-symbols")
        print("3. 批量回测: python run_1h_backtest.py --batch BTCUSDT ETHUSDT")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
        print("\n常见问题:")
        print("1. 缺少依赖: pip install python-binance ccxt pandas numpy matplotlib")
        print("2. 网络问题: 检查网络连接")
        print("3. API限制: 币安API可能有频率限制")
    
    print("=" * 60)

if __name__ == "__main__":
    main()