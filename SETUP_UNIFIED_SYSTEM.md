# 统一CTA交易系统 - 安装与设置指南

## 🎯 系统概述

统一CTA交易系统是一个既能回测又能实盘交易的完整量化交易框架。系统基于模块化设计，支持：

### 核心功能
- ✅ **统一策略接口**：同一套代码支持回测和实盘
- ✅ **多数据源支持**：币安API、模拟数据、缓存机制
- ✅ **完整风险控制**：仓位管理、止损止盈、风险限制
- ✅ **实时监控**：交易状态、性能指标、异常警报
- ✅ **专业分析**：夏普比率、最大回撤、胜率等指标

### 系统架构
```
统一交易引擎 (UnifiedTradingEngine)
    ├── 策略管理器 (Strategy Manager)
    ├── 数据管理器 (Data Manager)
    ├── 交易执行器 (Trade Executor)
    ├── 风险控制器 (Risk Controller)
    └── 监控系统 (Monitoring System)
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 进入项目目录
cd crypto_cta

# 安装依赖
pip install pandas numpy python-binance ccxt matplotlib

# 或使用安装脚本
chmod +x install_deps.sh
./install_deps.sh
```

### 2. 目录结构
```
crypto_cta/
├── unified_trading_engine.py    # 统一交易引擎
├── cta_strategy_unified.py      # CTA策略实现
├── run_unified_system.py        # 运行脚本
├── config_unified.json          # 配置文件
├── binance_fetcher.py           # 数据获取
├── data/                        # 数据存储
├── logs/                        # 日志文件
├── results/                     # 回测结果
└── strategies/                  # 策略目录
```

### 3. 运行回测（测试系统）
```bash
# 基本回测
python run_unified_system.py --mode backtest --symbol BTCUSDT

# 自定义参数回测
python run_unified_system.py --mode backtest \
  --symbol ETHUSDT \
  --capital 5000 \
  --fast-period 8 \
  --slow-period 24 \
  --start-date 2025-01-01 \
  --end-date 2025-03-01
```

### 4. 查看结果
回测完成后，结果保存在 `results/{timestamp}/` 目录：
- `metrics.json` - 性能指标
- `trades.csv` - 交易记录
- `equity_curve.csv` - 权益曲线
- `config.json` - 回测配置

## ⚙️ 配置系统

### 1. 编辑配置文件
修改 `config_unified.json` 自定义设置：

```json
{
  "strategies": {
    "cta_1h": {
      "parameters": {
        "fast_period": 12,
        "slow_period": 48,
        "position_size": 0.1,
        "stop_loss_pct": 0.015,
        "take_profit_pct": 0.03
      }
    }
  },
  "backtest": {
    "defaults": {
      "initial_capital": 10000,
      "commission": 0.001
    }
  }
}
```

### 2. 数据源配置
```json
{
  "data_sources": {
    "binance": {
      "api_key": "your_api_key_here",
      "api_secret": "your_api_secret_here",
      "use_public_data": true
    }
  }
}
```

### 3. 风险控制配置
```json
{
  "risk_controls": {
    "global": {
      "max_total_exposure": 0.5,
      "max_loss_per_day": 0.05,
      "max_loss_per_trade": 0.02
    }
  }
}
```

## 🔧 高级功能

### 1. 多策略运行
系统支持同时运行多个策略：
```python
# 注册多个策略
engine.register_strategy("cta_1h_btc", CTAStrategy, config_btc)
engine.register_strategy("cta_1h_eth", CTAStrategy, config_eth)

# 激活策略
engine.activate_strategy("cta_1h_btc", "BTCUSDT")
engine.activate_strategy("cta_1h_eth", "ETHUSDT")
```

### 2. 参数优化
系统内置参数优化框架：
```bash
# 运行参数优化（未来版本）
python optimize_strategy.py --strategy cta_1h --symbol BTCUSDT
```

### 3. 实时监控
启动Web监控面板：
```bash
# 启动监控服务（未来版本）
python monitor.py --port 8080
```

## 📊 策略开发

### 1. 创建新策略
继承 `BaseStrategy` 类：

```python
from unified_trading_engine import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, name, config):
        super().__init__(name, config)
        # 自定义初始化
    
    def calculate_indicators(self, data):
        # 计算技术指标
        pass
    
    def generate_signals(self, data):
        # 生成交易信号
        pass
```

### 2. 策略配置
```python
strategy_config = {
    "name": "my_strategy",
    "parameters": {
        "param1": value1,
        "param2": value2
    },
    "risk_management": {
        "position_size": 0.1,
        "stop_loss": 0.02
    }
}
```

### 3. 注册策略
```python
engine.register_strategy("my_strategy", MyCustomStrategy, strategy_config)
engine.activate_strategy("my_strategy", "BTCUSDT")
```

## 🚨 实盘交易准备

### 1. 安全第一
```bash
# 1. 充分回测（至少6个月数据）
python run_unified_system.py --mode backtest --start-date 2024-01-01

# 2. 模拟交易（Paper Trading）
python run_unified_system.py --mode live --paper-trading

# 3. 小资金测试
python run_unified_system.py --mode live --capital 100
```

### 2. 交易所配置
```python
# 配置币安API（需要申请）
from binance_exchange import BinanceExchange

exchange = BinanceExchange(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    testnet=True  # 先用测试网
)

engine.set_exchange(exchange)
```

### 3. 风险控制检查
- [ ] 设置最大仓位限制
- [ ] 配置止损止盈
- [ ] 设置每日亏损限额
- [ ] 启用紧急停止功能

## 📈 性能分析

### 1. 关键指标
- **夏普比率** > 1.5（良好）
- **最大回撤** < 15%（可接受）
- **胜率** > 55%（良好）
- **盈亏比** > 1.5（良好）

### 2. 回测验证
```bash
# 样本外测试
python run_unified_system.py --mode backtest \
  --start-date 2024-01-01 --end-date 2024-06-30  # 训练集
python run_unified_system.py --mode backtest \
  --start-date 2024-07-01 --end-date 2024-12-31  # 测试集
```

### 3. 稳定性测试
- 不同市场环境测试（牛市、熊市、震荡市）
- 参数敏感性分析
- 过拟合检查

## 🔍 故障排除

### 常见问题

#### 1. 数据获取失败
```bash
# 检查网络连接
ping api.binance.com

# 使用模拟数据
python run_unified_system.py --mode backtest --use-simulation
```

#### 2. 策略不交易
- 检查信号生成逻辑
- 验证技术指标计算
- 调整交易频率参数

#### 3. 性能不佳
- 优化策略参数
- 添加更多过滤条件
- 调整风险控制参数

### 日志分析
```bash
# 查看交易日志
tail -f logs/trading.log

# 查看错误日志
grep ERROR logs/trading.log
```

## 🔮 未来扩展

### 计划功能
- [ ] 机器学习策略集成
- [ ] 多时间框架分析
- [ ] 自动参数优化
- [ ] Web监控界面
- [ ] 手机通知提醒
- [ ] 多交易所支持

### 技术路线
1. **v1.0** - 基础回测+实盘框架 ✓
2. **v1.1** - 增强风险控制
3. **v1.2** - 机器学习集成
4. **v2.0** - 分布式回测引擎

## 📚 学习资源

### 推荐阅读
1. 《趋势跟踪》- 迈克尔·卡沃尔
2. 《海龟交易法则》- 柯蒂斯·费思
3. 《量化交易》- 欧内斯特·陈

### 在线资源
- [币安API文档](https://binance-docs.github.io/apidocs/)
- [CCXT文档](https://docs.ccxt.com/)
- [量化交易社区](https://www.quantconnect.com/)

## ⚠️ 风险提示

### 重要警告
1. **实盘交易风险极高**，可能导致全部资金损失
2. **历史回测不代表未来表现**
3. **过度优化可能导致过拟合**
4. **技术故障可能造成意外损失**

### 建议措施
1. 先用模拟账户测试
2. 小资金开始实盘
3. 设置严格的风险控制
4. 定期备份和监控
5. 持续学习和改进

---

**开始使用前，请确保充分理解所有风险！**

如有问题，请查看日志文件或提交Issue。