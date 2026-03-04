# 1小时级别CTA策略回测系统

专门针对币安1小时K线数据进行商品交易顾问（CTA）策略回测的系统。

## 🚀 快速开始

### 1. 安装依赖
```bash
# 进入项目目录
cd crypto_cta

# 运行安装脚本
./install_deps.sh

# 或者手动安装
pip install pandas numpy python-binance ccxt matplotlib
```

### 2. 运行回测

#### 查看可用交易对
```bash
python run_1h_backtest.py --list-symbols
```

#### 单个交易对回测（默认BTCUSDT，90天）
```bash
python run_1h_backtest.py
```

#### 自定义参数回测
```bash
# ETHUSDT，180天，初始资金5000 USDT
python run_1h_backtest.py --symbol ETHUSDT --days 180 --capital 5000

# 自定义手续费率（默认0.1%）
python run_1h_backtest.py --symbol BTCUSDT --commission 0.002
```

#### 批量回测多个交易对
```bash
python run_1h_backtest.py --batch BTCUSDT ETHUSDT BNBUSDT SOLUSDT
```

## 📊 策略特点

### 核心CTA策略
1. **双均线系统**：12小时快线 vs 48小时慢线
2. **RSI超买超卖**：14周期RSI，30/70阈值
3. **布林带突破**：20周期，2倍标准差
4. **ATR波动率过滤**：14周期ATR
5. **成交量确认**：1.2倍均量确认

### 风险控制
- **仓位管理**：单次最大10%仓位
- **止损止盈**：1.5%止损，3%止盈
- **波动率过滤**：高波动市场减少交易
- **交易频率限制**：避免过度交易

## 📈 回测流程

1. **数据获取**：从币安获取1小时K线数据
2. **数据预处理**：清洗、计算技术指标
3. **参数优化**：在训练集上优化策略参数
4. **信号生成**：应用CTA策略生成交易信号
5. **回测执行**：模拟交易，计算盈亏
6. **性能评估**：计算夏普比率、最大回撤等
7. **结果可视化**：生成图表和报告

## 📁 项目结构

```
crypto_cta/
├── binance_fetcher.py      # 币安数据获取模块
├── backtest_1h.py          # 1小时级别回测器
├── run_1h_backtest.py      # 回测运行脚本
├── config_1h.json          # 配置文件
├── install_deps.sh         # 依赖安装脚本
├── README_1H_BACKTEST.md   # 本文档
├── src/                    # 策略源代码
│   ├── cta_strategy.py     # CTA策略实现
│   ├── data_fetcher.py     # 数据获取（原版）
│   └── backtester.py       # 回测引擎
├── data_1h/                # 1小时数据存储
│   └── cache/              # 数据缓存
├── results_1h/             # 回测结果
│   ├── *.json              # 性能指标
│   ├── *.csv               # 交易记录
│   └── *.png               # 可视化图表
└── logs_1h/                # 日志文件
```

## ⚙️ 配置文件

编辑 `config_1h.json` 自定义设置：

```json
{
  "binance_api": {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
  },
  "backtest_settings": {
    "default_symbol": "BTCUSDT",
    "default_days": 90,
    "default_capital": 10000
  },
  "strategy_parameters": {
    "fast_period": 12,
    "slow_period": 48,
    "position_size": 0.1
  }
}
```

## 📊 输出结果

回测完成后，在 `results_1h/` 目录生成：

### 1. 性能指标文件 (`*_metrics.json`)
```json
{
  "performance": {
    "total_return": 0.152,
    "annualized_return": 0.423,
    "sharpe_ratio": 1.85,
    "max_drawdown": 0.087
  },
  "trade_analysis": {
    "total_trades": 24,
    "win_rate": 0.625,
    "profit_factor": 2.34
  }
}
```

### 2. 交易记录文件 (`*_trades.csv`)
包含每笔交易的详细信息：
- 入场时间、价格
- 出场时间、价格
- 盈亏金额、百分比
- 持仓时间
- 交易类型（多头/空头）

### 3. 可视化图表 (`*_report.png`)
- 价格走势和交易信号
- 权益曲线
- 回撤曲线

## 🔧 自定义策略

### 修改策略参数
编辑 `config_1h.json` 中的 `strategy_parameters` 部分：

```json
"strategy_parameters": {
  "fast_period": 8,          # 改为8小时均线
  "slow_period": 24,         # 改为24小时均线
  "position_size": 0.15,     # 改为15%仓位
  "stop_loss_pct": 0.02,     # 改为2%止损
  "take_profit_pct": 0.04    # 改为4%止盈
}
```

### 添加新的技术指标
修改 `src/cta_strategy.py` 中的 `generate_signals` 方法。

## 📈 性能评估指标

### 关键指标
- **总收益率**：策略总收益
- **年化收益率**：折算成年收益
- **夏普比率**：风险调整后收益（>1.5为佳）
- **最大回撤**：最大亏损幅度（<15%为佳）
- **胜率**：盈利交易比例（>55%为佳）
- **盈亏比**：平均盈利/平均亏损（>1.5为佳）
- **卡玛比率**：年化收益/最大回撤

### 交易质量
- **交易次数**：避免过度交易
- **平均持仓时间**：适合策略周期
- **最大连续亏损**：风险承受能力
- **恢复因子**：回撤恢复能力

## 🚨 风险提示

### 回测局限性
1. **前视偏差**：回测使用历史数据，可能包含未来信息
2. **过拟合风险**：策略可能在特定时期表现良好
3. **执行差异**：实际交易存在滑点、延迟等问题
4. **市场变化**：历史模式可能不再适用

### 实盘建议
1. **小资金测试**：先用小资金实盘测试
2. **风险控制**：严格设置止损，控制仓位
3. **持续监控**：定期评估策略表现
4. **多样化**：不要把所有资金投入单一策略

## 🔮 未来扩展

### 计划功能
- [ ] 多时间框架分析（1h + 4h + 1d）
- [ ] 机器学习信号增强
- [ ] 动态参数调整
- [ ] 实时交易接口
- [ ] 风险平价组合

### 优化方向
- 降低交易频率
- 提高夏普比率
- 减少最大回撤
- 增加策略容量

## 📚 学习资源

### CTA策略基础
1. 《趋势跟踪》- 迈克尔·卡沃尔
2. 《海龟交易法则》- 柯蒂斯·费思
3. 《交易系统与方法》- 佩里·考夫曼

### 量化交易
1. 《量化交易》- 欧内斯特·陈
2. 《算法交易》- 欧内斯特·陈
3. 《打开量化投资的黑箱》- 里什·纳兰

### 币安API
1. [币安API文档](https://binance-docs.github.io/apidocs/)
2. [CCXT文档](https://docs.ccxt.com/)
3. [Python-Binance文档](https://python-binance.readthedocs.io/)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 支持

如有问题或建议：
1. 查看 `logs_1h/` 目录下的日志文件
2. 提交GitHub Issue
3. 检查依赖是否安装完整

---

**免责声明**：本系统仅供学习和研究使用。加密货币交易风险极高，可能导致全部资金损失。历史回测结果不代表未来表现，请谨慎决策。