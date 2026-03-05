# PR: 添加1小时级别CTA策略回测系统

## 📋 PR 概述

此PR为加密货币CTA项目添加了完整的1小时级别回测系统，支持从币安获取数据并进行专业的量化回测。

## 🎯 解决的问题

1. **数据获取问题**：原系统仅支持Yahoo Finance，无法获取币安数据
2. **时间级别限制**：原系统只支持日线级别，缺少1小时级别的回测能力
3. **用户体验**：缺少完整的命令行工具和配置系统
4. **测试验证**：缺少系统测试和演示工具

## ✨ 新增功能

### 核心模块
| 模块 | 功能描述 | 重要性 |
|------|----------|--------|
| `binance_fetcher.py` | 币安数据获取，支持API/CCXT/模拟数据 | 🔥 核心 |
| `backtest_1h.py` | 1小时级别专用回测器 | 🔥 核心 |
| `run_1h_backtest.py` | 命令行回测工具 | 🔥 核心 |
| `run_demo.py` | 演示脚本（无需API） | ⭐ 重要 |
| `config_1h.json` | 配置文件系统 | ⭐ 重要 |

### 辅助工具
| 工具 | 用途 |
|------|------|
| `install_deps.sh` | 一键安装依赖 |
| `README_1H_BACKTEST.md` | 详细使用文档 |
| `test_system.py` | 系统测试工具 |
| `test_system_fixed.py` | 修复版测试工具 |

## 🔧 技术实现

### 数据获取架构
```
数据源优先级：
1. 币安官方API (python-binance)
2. CCXT通用接口
3. 模拟数据（备用方案）
```

### 策略优化（针对1小时级别）
```python
# 优化后的参数
fast_period=12      # 12小时均线（原20）
slow_period=48      # 48小时均线（原50）
position_size=0.1   # 10%仓位
stop_loss_pct=0.015 # 1.5%止损（原2%）
take_profit_pct=0.03 # 3%止盈（原4%）
```

### 回测流程
```
1. 数据获取 → 2. 预处理 → 3. 信号生成 → 
4. 回测执行 → 5. 结果分析 → 6. 可视化输出
```

## 📊 性能特点

### 策略特性
- **多因子融合**：趋势跟踪 + 均值回归 + 波动率过滤
- **风险控制**：严格的止损止盈和仓位管理
- **适应性**：针对1小时K线优化的参数

### 技术指标
1. 双均线交叉（12h/48h）
2. RSI超买超卖（14周期）
3. 布林带突破（20周期，2倍标准差）
4. ATR波动率过滤（14周期）
5. 成交量确认（1.2倍均量）

## 🚀 使用方式

### 快速开始
```bash
# 1. 安装依赖
./install_deps.sh

# 2. 运行演示（无需API）
python run_demo.py --symbol BTCUSDT --days 30

# 3. 完整回测（需要API）
python run_1h_backtest.py --symbol BTCUSDT --days 90
```

### 高级功能
```bash
# 批量回测多个交易对
python run_1h_backtest.py --batch BTCUSDT ETHUSDT BNBUSDT

# 自定义参数
python run_1h_backtest.py --symbol ETHUSDT --days 180 --capital 50000

# 查看可用交易对
python run_1h_backtest.py --list-symbols
```

## 📈 输出结果

回测完成后生成：
1. **性能指标** (`*_metrics.json`) - 夏普比率、最大回撤等
2. **交易记录** (`*_trades.csv`) - 每笔交易详情
3. **可视化图表** (`*_chart.png`) - 价格和权益曲线
4. **原始数据** (`*_data.csv`) - 包含信号的数据

## 🧪 测试验证

### 已通过的测试
- ✅ 模块导入测试
- ✅ 策略信号生成测试
- ✅ 回测执行测试
- ✅ 演示脚本完整运行

### 测试命令
```bash
# 运行系统测试
python test_system_fixed.py

# 运行演示回测
python run_demo.py --symbol BTCUSDT --days 7
```

## 🔄 兼容性

### 向后兼容
- 保留原有日线级别功能
- 新增1小时级别模块
- 配置文件独立，不影响原有设置

### 依赖更新
```bash
新增依赖：
- python-binance (币安API)
- ccxt (交易所通用接口)
- matplotlib (可视化)

原有依赖：
- pandas, numpy (数据处理)
- yfinance (保留兼容)
```

## 📁 文件结构变化

```
crypto_cta/
├── 📄 binance_fetcher.py      # 新增：币安数据获取
├── 📄 backtest_1h.py          # 新增：1小时回测器
├── 📄 run_1h_backtest.py      # 新增：命令行工具
├── 📄 run_demo.py             # 修改：增强演示功能
├── 📄 config_1h.json          # 新增：配置文件
├── 📄 install_deps.sh         # 新增：安装脚本
├── 📄 README_1H_BACKTEST.md   # 新增：详细文档
├── 📄 test_system.py          # 新增：测试工具
├── 📄 test_system_fixed.py    # 新增：修复版测试
└── src/                       # 原有策略代码不变
```

## 🎨 用户体验改进

### 命令行界面
```
$ python run_1h_backtest.py --help
用法: 运行1小时级别CTA策略回测

选项:
  --symbol SYMBOL     交易对 (默认: BTCUSDT)
  --days DAYS         回测天数 (默认: 90)
  --capital CAPITAL   初始资金 (默认: 10000)
  --batch [SYMBOLS...] 批量回测多个交易对
  --list-symbols      列出可用的交易对
```

### 配置文件
```json
{
  "binance_api": {
    "api_key": "可选，公开数据不需要",
    "api_secret": "可选"
  },
  "strategy_parameters": {
    "fast_period": 12,
    "slow_period": 48,
    "position_size": 0.1
  }
}
```

## 📚 文档完善

### 新增文档
- `README_1H_BACKTEST.md` - 完整的使用指南
- 命令行帮助文档
- 配置说明文档
- 策略原理说明

### 示例代码
提供完整的示例代码，包括：
- 数据获取示例
- 策略使用示例
- 回测执行示例
- 结果分析示例

## 🔮 未来扩展计划

### 短期计划
- [ ] 实时数据流支持
- [ ] 多时间框架分析
- [ ] 机器学习信号增强

### 长期计划
- [ ] 实时交易接口
- [ ] 风险平价组合
- [ ] 策略市场平台

## ⚠️ 注意事项

### 风险提示
1. **回测局限性**：历史表现不代表未来
2. **过拟合风险**：需定期优化参数
3. **执行差异**：实际交易存在滑点等问题
4. **市场风险**：加密货币波动性极高

### 使用建议
1. 先用小资金测试
2. 定期评估策略表现
3. 设置严格的风险控制
4. 多样化投资组合

## ✅ 验收标准

- [x] 所有新模块可通过导入测试
- [x] 演示脚本可完整运行
- [x] 生成完整的回测结果
- [x] 输出可视化图表
- [x] 文档齐全且准确
- [x] 向后兼容原有功能

## 🤝 贡献者

- 鲁班 (项目负责人)
- 小布 (AI助手，代码实现)

---

**提交哈希**: `be72207`
**分支**: `master`
**状态**: ✅ 已完成所有功能开发和测试