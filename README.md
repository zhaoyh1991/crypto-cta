# 加密货币CTA策略系统

一个稳健的加密货币商品交易顾问（CTA）策略系统，结合趋势跟踪和均值回归，实现稳定盈利。

## 🎯 策略特点

### 核心策略
1. **多因子融合**：结合趋势、动量、波动率和成交量多个维度
2. **风险控制**：内置止损止盈、仓位管理和波动率调整
3. **稳健参数**：经过优化的参数，避免过拟合

### 技术指标
- 双均线系统（20日/50日）
- RSI超买超卖（14日）
- 布林带突破（20日，2倍标准差）
- ATR波动率过滤（14日）
- 成交量确认

## 📊 性能目标

- **年化收益率**：15-30%
- **夏普比率**：>1.5
- **最大回撤**：<15%
- **胜率**：>55%

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install pandas numpy matplotlib yfinance
```

### 2. 运行回测
```bash
# 使用默认参数（BTC-USD，1年数据）
python main.py

# 使用模拟数据
python main.py --use-sample

# 自定义参数
python main.py --symbol ETH-USD --period 2y --capital 50000
```

### 3. 查看结果
结果保存在 `results/` 目录下，包括：
- `metrics.json` - 性能指标
- `trades.csv` - 交易记录
- `report.png` - 可视化报告
- `config.json` - 配置文件

## 📁 项目结构

```
crypto_cta/
├── main.py              # 主程序
├── config.json          # 配置文件
├── README.md           # 说明文档
├── src/                # 源代码
│   ├── cta_strategy.py # CTA策略实现
│   ├── data_fetcher.py # 数据获取模块
│   └── backtester.py   # 回测和可视化
├── data/               # 数据目录
├── results/            # 回测结果
├── logs/               # 日志文件
└── tests/              # 测试文件
```

## 🔧 策略参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| fast_period | 20 | 快速均线周期 |
| slow_period | 50 | 慢速均线周期 |
| rsi_period | 14 | RSI周期 |
| bb_period | 20 | 布林带周期 |
| bb_std | 2.0 | 布林带标准差 |
| atr_period | 14 | ATR周期 |
| volume_threshold | 1.2 | 成交量确认阈值 |
| position_size | 0.1 | 仓位大小（10%） |
| stop_loss_pct | 0.02 | 止损比例（2%） |
| take_profit_pct | 0.04 | 止盈比例（4%） |

## 📈 策略逻辑

### 买入信号（多头）
1. 快速均线上穿慢速均线（趋势向上）
2. RSI < 30（超卖）
3. 价格触及布林带下轨
4. 成交量放大（>1.2倍均量）
5. 波动率合适（ATR/价格 > 0.5%）

### 卖出信号（空头）
1. 快速均线下穿慢速均线（趋势向下）
2. RSI > 70（超买）
3. 价格触及布林带上轨
4. 成交量放大（>1.2倍均量）
5. 波动率合适（ATR/价格 > 0.5%）

## 🛡️ 风险控制

### 仓位管理
- 凯利公式调整仓位
- 波动率调整（高波动减仓）
- 最大仓位限制（单次10%）

### 止损止盈
- 固定比例止损（2%）
- 固定比例止盈（4%）
- 移动止损（未来版本）

### 交易过滤
- 避免频繁交易
- 波动率过滤
- 成交量确认

## 🔍 性能评估

### 关键指标
- **夏普比率**：风险调整后收益
- **最大回撤**：最大亏损幅度
- **卡玛比率**：收益/回撤比
- **胜率**：盈利交易比例
- **盈亏比**：平均盈利/平均亏损

### 回测验证
- 训练集/测试集分割（70%/30%）
- 样本外测试
- 参数稳定性检验

## 📝 使用示例

### 基本使用
```python
from src.cta_strategy import CryptoCTAStrategy
from src.data_fetcher import CryptoDataFetcher

# 获取数据
fetcher = CryptoDataFetcher()
df = fetcher.fetch_from_yahoo('BTC-USD', '1y', '1d')

# 创建策略
strategy = CryptoCTAStrategy()

# 生成信号
df_with_signals = strategy.generate_signals(df)
```

### 自定义策略
```python
# 自定义参数
strategy = CryptoCTAStrategy(
    fast_period=15,
    slow_period=60,
    rsi_period=10,
    position_size=0.15,
    stop_loss_pct=0.015,
    take_profit_pct=0.03
)
```

## 🚨 风险提示

1. **历史表现不代表未来**：回测结果仅供参考
2. **市场风险**：加密货币波动性极高
3. **过拟合风险**：策略可能在特定时期表现良好
4. **执行风险**：实际交易可能存在滑点、延迟等问题
5. **技术风险**：系统故障、网络问题等

## 🔮 未来改进

### 计划功能
- [ ] 机器学习信号增强
- [ ] 多时间框架分析
- [ ] 动态参数优化
- [ ] 实时交易接口
- [ ] 风险平价组合

### 优化方向
- 降低交易频率
- 提高夏普比率
- 减少最大回撤
- 增加策略容量

## 📚 参考资料

1. 《趋势跟踪》- 迈克尔·卡沃尔
2. 《海龟交易法则》- 柯蒂斯·费思
3. 《交易系统与方法》- 佩里·考夫曼
4. 《量化交易》- 欧内斯特·陈

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系

如有问题或建议，请提交Issue。