#!/usr/bin/env python3
print("测试开始")

import pandas as pd
import numpy as np

# 创建简单数据
dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
df = pd.DataFrame({
    'open': np.random.normal(50000, 1000, 100),
    'high': np.random.normal(51000, 1500, 100),
    'low': np.random.normal(49000, 1500, 100),
    'close': np.random.normal(50000, 2000, 100),
    'volume': np.random.normal(1000, 200, 100)
}, index=dates)

print(f"数据创建成功: {len(df)} 行")
print(f"列: {df.columns.tolist()}")

# 简单策略
class TestStrategy:
    def __init__(self):
        self.ma_period = 20
        
    def run(self, df):
        df['ma'] = df['close'].rolling(self.ma_period).mean()
        df['signal'] = np.where(df['close'] > df['ma'], 1, -1)
        return df

strategy = TestStrategy()
result = strategy.run(df)

print(f"策略运行成功")
print(f"信号统计: 买入 {(result['signal'] == 1).sum()}, 卖出 {(result['signal'] == -1).sum()}")

# 简单回测
capital = 100000
position = 0

for i in range(20, len(result)):
    if result['signal'].iloc[i] == 1 and position == 0:
        position = capital * 0.1 / result['close'].iloc[i]
        capital -= position * result['close'].iloc[i]
    elif result['signal'].iloc[i] == -1 and position > 0:
        capital += position * result['close'].iloc[i]
        position = 0

if position > 0:
    capital += position * result['close'].iloc[-1]

print(f"回测结果: 初始 $100,000, 最终 ${capital:,.0f}")
print(f"收益率: {(capital/100000 - 1):.2%}")

print("测试完成")