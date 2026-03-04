"""
加密货币数据获取模块
支持多种数据源和格式
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

# 尝试导入yfinance，如果失败则提供替代方案
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("警告: yfinance不可用，将使用模拟数据")

class CryptoDataFetcher:
    """
    加密货币数据获取类
    支持：
    1. Yahoo Finance (yfinance)
    2. 本地CSV文件
    3. 模拟数据生成（用于测试）
    """
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def fetch_from_yahoo(self, symbol='BTC-USD', period='1y', interval='1d'):
        """
        从Yahoo Finance获取数据
        """
        print(f"从Yahoo Finance获取 {symbol} 数据...")
        
        if not YFINANCE_AVAILABLE:
            print("yfinance不可用，使用模拟数据")
            return self.generate_sample_data()
        
        try:
            # 下载数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"无法获取 {symbol} 数据，使用模拟数据")
                return self.generate_sample_data()
            
            # 重命名列以符合我们的格式
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 确保有需要的列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = np.nan
            
            # 保存到本地
            filename = f"{symbol.replace('-', '_')}_{period}_{interval}.csv"
            filepath = os.path.join(self.data_dir, filename)
            df.to_csv(filepath)
            print(f"数据已保存到: {filepath}")
            
            return df
            
        except Exception as e:
            print(f"获取数据失败: {e}，使用模拟数据")
            # 返回模拟数据作为备选
            return self.generate_sample_data()
    
    def load_from_csv(self, filepath):
        """
        从CSV文件加载数据
        """
        print(f"从CSV文件加载数据: {filepath}")
        
        try:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            # 检查必要的列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"警告: 缺少列: {missing_columns}")
                # 尝试重命名
                column_mapping = {
                    'Open': 'open', 'OPEN': 'open',
                    'High': 'high', 'HIGH': 'high',
                    'Low': 'low', 'LOW': 'low',
                    'Close': 'close', 'CLOSE': 'close',
                    'Volume': 'volume', 'VOLUME': 'volume'
                }
                
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns and new_col not in df.columns:
                        df[new_col] = df[old_col]
                
                # 再次检查
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    raise ValueError(f"数据缺少必要的列: {missing_columns}")
            
            return df
            
        except Exception as e:
            print(f"加载CSV文件失败: {e}")
            return None
    
    def generate_sample_data(self, days=365, start_price=50000):
        """
        生成模拟的加密货币数据
        用于测试和演示
        """
        print("生成模拟数据...")
        
        # 生成日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 基础价格序列（带趋势和波动）
        np.random.seed(42)
        
        # 随机游走
        returns = np.random.normal(0.0005, 0.02, len(dates))  # 日均收益0.05%，波动2%
        
        # 添加一些趋势
        trend = np.linspace(0, 0.3, len(dates))  # 30%的趋势
        returns += trend / len(dates)
        
        # 计算价格
        price = start_price * np.exp(np.cumsum(returns))
        
        # 生成OHLC数据
        df = pd.DataFrame(index=dates)
        df['close'] = price
        
        # 生成开盘价（接近前一日收盘价）
        df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
        df['open'].iloc[0] = start_price * (1 + np.random.normal(0, 0.01))
        
        # 生成最高价和最低价
        daily_range = df['close'] * 0.02  # 2%的日波动范围
        df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.5, len(dates)) * daily_range
        df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.5, len(dates)) * daily_range
        
        # 确保 high >= low
        df['high'] = df[['high', 'low']].max(axis=1)
        df['low'] = df[['high', 'low']].min(axis=1)
        
        # 生成成交量（与价格波动相关）
        base_volume = 1000
        df['volume'] = base_volume * (1 + np.abs(returns) * 10) * np.random.uniform(0.8, 1.2, len(dates))
        
        # 添加一些异常波动（模拟市场事件）
        event_days = np.random.choice(len(dates), size=10, replace=False)
        df.loc[df.index[event_days], 'close'] *= (1 + np.random.uniform(-0.1, 0.1, 10))
        
        # 重新计算受影响日期的high/low
        for idx in event_days:
            if idx > 0:
                df.iloc[idx, df.columns.get_loc('high')] = max(df.iloc[idx]['open'], df.iloc[idx]['close']) * 1.01
                df.iloc[idx, df.columns.get_loc('low')] = min(df.iloc[idx]['open'], df.iloc[idx]['close']) * 0.99
        
        # 填充NaN值
        df = df.ffill().bfill()
        
        print(f"生成 {len(df)} 天的模拟数据，价格范围: {df['close'].min():.0f} - {df['close'].max():.0f}")
        
        return df
    
    def prepare_data(self, df, train_ratio=0.7):
        """
        准备训练和测试数据
        """
        if df is None or len(df) == 0:
            raise ValueError("输入数据为空")
        
        # 确保数据按时间排序
        df = df.sort_index()
        
        # 分割训练集和测试集
        split_idx = int(len(df) * train_ratio)
        train_data = df.iloc[:split_idx]
        test_data = df.iloc[split_idx:]
        
        print(f"数据分割: 训练集 {len(train_data)} 条, 测试集 {len(test_data)} 条")
        print(f"训练集时间范围: {train_data.index[0]} 到 {train_data.index[-1]}")
        print(f"测试集时间范围: {test_data.index[0]} 到 {test_data.index[-1]}")
        
        return train_data, test_data
    
    def get_available_datasets(self):
        """
        获取可用的数据集
        """
        datasets = []
        
        # 检查数据目录
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.endswith('.csv'):
                    filepath = os.path.join(self.data_dir, file)
                    try:
                        # 尝试读取文件信息
                        df = pd.read_csv(filepath, nrows=1)
                        datasets.append({
                            'filename': file,
                            'path': filepath,
                            'columns': list(df.columns)
                        })
                    except:
                        continue
        
        return datasets
    
    def create_technical_features(self, df):
        """
        创建技术特征（供机器学习策略使用）
        """
        df = df.copy()
        
        # 价格特征
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 移动平均
        for window in [5, 10, 20, 50]:
            df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
            df[f'ma_ratio_{window}'] = df['close'] / df[f'ma_{window}']
        
        # 波动率
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_50'] = df['returns'].rolling(50).std()
        
        # 成交量特征
        df['volume_ma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        
        # 价格范围
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['body_size'] = np.abs(df['close'] - df['open']) / df['close']
        
        # 滞后特征
        for lag in [1, 2, 3, 5, 10]:
            df[f'return_lag_{lag}'] = df['returns'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        # 目标变量（未来收益）
        df['target_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['target_5d'] = df['close'].shift(-5) / df['close'] - 1
        
        # 删除NaN值
        df = df.dropna()
        
        return df