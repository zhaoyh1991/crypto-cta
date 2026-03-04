"""
币安数据获取模块
支持从币安获取K线数据，包括1小时级别
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json
from typing import Optional, List, Dict, Tuple

# 尝试导入币安相关库
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("警告: python-binance不可用，请安装: pip install python-binance")

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("警告: ccxt不可用，请安装: pip install ccxt")

class BinanceDataFetcher:
    """
    币安数据获取类
    支持：
    1. 币安官方API (python-binance)
    2. CCXT通用接口
    3. 本地缓存
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 data_dir: str = 'data', use_cache: bool = True):
        """
        初始化币安数据获取器
        
        Args:
            api_key: 币安API Key (可选，公开数据不需要)
            api_secret: 币安API Secret (可选)
            data_dir: 数据存储目录
            use_cache: 是否使用本地缓存
        """
        self.data_dir = data_dir
        self.use_cache = use_cache
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化API客户端
        self.binance_client = None
        self.ccxt_exchange = None
        
        if BINANCE_AVAILABLE and (api_key and api_secret):
            try:
                self.binance_client = Client(api_key, api_secret)
                print("币安官方API客户端初始化成功")
            except Exception as e:
                print(f"币安官方API初始化失败: {e}")
        
        if CCXT_AVAILABLE:
            try:
                self.ccxt_exchange = ccxt.binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',  # spot, future, margin
                    }
                })
                print("CCXT币安客户端初始化成功")
            except Exception as e:
                print(f"CCXT币安客户端初始化失败: {e}")
    
    def fetch_klines(self, symbol: str = 'BTCUSDT', interval: str = '1h', 
                    start_time: Optional[str] = None, end_time: Optional[str] = None,
                    limit: int = 1000) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对，如 BTCUSDT, ETHUSDT
            interval: K线间隔，支持: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
            start_time: 开始时间 (格式: '2023-01-01' 或 '2023-01-01 00:00:00')
            end_time: 结束时间
            limit: 每次请求的最大K线数量
            
        Returns:
            pandas DataFrame with OHLCV数据
        """
        print(f"获取币安数据: {symbol} {interval}")
        
        # 检查缓存
        cache_key = self._get_cache_key(symbol, interval, start_time, end_time)
        if self.use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                print(f"从缓存加载数据: {cache_key}")
                return cached_data
        
        # 优先使用币安官方API
        if self.binance_client:
            df = self._fetch_with_binance_api(symbol, interval, start_time, end_time, limit)
        elif self.ccxt_exchange:
            df = self._fetch_with_ccxt(symbol, interval, start_time, end_time, limit)
        else:
            print("警告: 没有可用的API客户端，使用模拟数据")
            df = self._generate_sample_data(symbol, interval, start_time, end_time)
        
        if df is not None and not df.empty:
            # 保存到缓存
            if self.use_cache:
                self._save_to_cache(cache_key, df)
            
            # 保存到CSV
            self._save_to_csv(symbol, interval, df)
        
        return df
    
    def _fetch_with_binance_api(self, symbol: str, interval: str, 
                               start_time: Optional[str], end_time: Optional[str], 
                               limit: int) -> Optional[pd.DataFrame]:
        """使用币安官方API获取数据"""
        try:
            # 转换时间格式
            start_ms = None
            end_ms = None
            
            if start_time:
                start_dt = pd.to_datetime(start_time)
                start_ms = int(start_dt.timestamp() * 1000)
            
            if end_time:
                end_dt = pd.to_datetime(end_time)
                end_ms = int(end_dt.timestamp() * 1000)
            
            # 获取K线数据
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=interval,
                startTime=start_ms,
                endTime=end_ms,
                limit=limit
            )
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 转换数据类型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_asset_volume', 'taker_buy_base_asset_volume', 
                          'taker_buy_quote_asset_volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 重命名列
            df = df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # 只保留需要的列
            keep_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[keep_cols]
            
            print(f"从币安API获取 {len(df)} 条 {interval} K线数据")
            return df
            
        except BinanceAPIException as e:
            print(f"币安API错误: {e}")
            return None
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def _fetch_with_ccxt(self, symbol: str, interval: str, 
                        start_time: Optional[str], end_time: Optional[str], 
                        limit: int) -> Optional[pd.DataFrame]:
        """使用CCXT获取数据"""
        try:
            # CCXT时间格式
            since = None
            if start_time:
                since = self.ccxt_exchange.parse8601(start_time)
            
            # 获取OHLCV数据
            ohlcv = self.ccxt_exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=interval,
                since=since,
                limit=limit
            )
            
            # 转换为DataFrame
            df = pd.DataFrame(ohlcv, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 转换数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            print(f"从CCXT获取 {len(df)} 条 {interval} K线数据")
            return df
            
        except Exception as e:
            print(f"CCXT获取数据失败: {e}")
            return None
    
    def _generate_sample_data(self, symbol: str, interval: str, 
                             start_time: Optional[str], end_time: Optional[str]) -> pd.DataFrame:
        """生成模拟数据（当API不可用时）"""
        print(f"生成模拟数据: {symbol} {interval}")
        
        # 解析时间
        if end_time:
            end_date = pd.to_datetime(end_time)
        else:
            end_date = datetime.now()
        
        if start_time:
            start_date = pd.to_datetime(start_time)
        else:
            # 默认获取最近30天数据
            start_date = end_date - timedelta(days=30)
        
        # 根据间隔生成时间序列
        if interval == '1h':
            freq = '1h'
            periods = int((end_date - start_date).total_seconds() / 3600)
        elif interval == '4h':
            freq = '4h'
            periods = int((end_date - start_date).total_seconds() / (3600 * 4))
        elif interval == '1d':
            freq = '1D'
            periods = int((end_date - start_date).days)
        else:
            freq = '1h'
            periods = 720  # 默认30天 * 24小时
        
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)[:periods]
        
        # 生成价格数据
        np.random.seed(42)
        
        # 基础价格（根据交易对）
        if 'BTC' in symbol:
            start_price = 50000
        elif 'ETH' in symbol:
            start_price = 3000
        else:
            start_price = 100
        
        # 随机游走
        if interval == '1h':
            volatility = 0.005  # 0.5% hourly volatility
        elif interval == '4h':
            volatility = 0.01   # 1% per 4h
        else:
            volatility = 0.02   # 2% daily
        
        returns = np.random.normal(0.0001, volatility, len(dates))
        price = start_price * np.exp(np.cumsum(returns))
        
        # 生成OHLCV数据
        df = pd.DataFrame(index=dates)
        df['close'] = price
        
        # 开盘价（接近前一根K线收盘价）
        df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, volatility/2, len(dates)))
        df['open'].iloc[0] = start_price
        
        # 最高价和最低价
        price_range = df['close'] * volatility
        df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.5, len(dates)) * price_range
        df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.5, len(dates)) * price_range
        
        # 确保 high >= low
        df['high'] = df[['high', 'low']].max(axis=1)
        df['low'] = df[['high', 'low']].min(axis=1)
        
        # 成交量
        base_volume = 1000
        df['volume'] = base_volume * (1 + np.abs(returns) * 10) * np.random.uniform(0.8, 1.2, len(dates))
        
        print(f"生成 {len(df)} 条 {interval} 模拟数据")
        return df
    
    def _get_cache_key(self, symbol: str, interval: str, 
                      start_time: Optional[str], end_time: Optional[str]) -> str:
        """生成缓存键"""
        key_parts = [symbol, interval]
        if start_time:
            key_parts.append(start_time.replace(' ', '_').replace(':', '-'))
        if end_time:
            key_parts.append(end_time.replace(' ', '_').replace(':', '-'))
        return '_'.join(key_parts) + '.pkl'
    
    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        cache_dir = os.path.join(self.data_dir, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_path = os.path.join(cache_dir, cache_key)
        if os.path.exists(cache_path):
            try:
                # 检查文件修改时间（缓存有效期24小时）
                if time.time() - os.path.getmtime(cache_path) < 24 * 3600:
                    df = pd.read_pickle(cache_path)
                    return df
            except Exception as e:
                print(f"加载缓存失败: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, df: pd.DataFrame):
        """保存数据到缓存"""
        cache_dir = os.path.join(self.data_dir, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_path = os.path.join(cache_dir, cache_key)
        try:
            df.to_pickle(cache_path)
            print(f"数据已缓存: {cache_path}")
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _save_to_csv(self, symbol: str, interval: str, df: pd.DataFrame):
        """保存数据到CSV"""
        filename = f"binance_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            df.to_csv(filepath)
            print(f"数据已保存到CSV: {filepath}")
        except Exception as e:
            print(f"保存CSV失败: {e}")
    
    def get_available_symbols(self) -> List[str]:
        """获取可用的交易对列表"""
        symbols = []
        
        if self.binance_client:
            try:
                exchange_info = self.binance_client.get_exchange_info()
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['status'] == 'TRADING':
                        symbols.append(symbol_info['symbol'])
            except Exception as e:
                print(f"获取交易对列表失败: {e}")
        
        # 如果没有获取到，返回常用交易对
        if not symbols:
            symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
                'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT'
            ]
        
        return symbols[:50]  # 返回前50个
    
    def get_historical_data_batch(self, symbols: List[str], interval: str = '1h',
                                 days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个交易对的历史数据
        
        Args:
            symbols: 交易对列表
            interval: K线间隔
            days: 获取多少天的数据
            
        Returns:
            字典，键为交易对，值为DataFrame
        """
        results = {}
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        for symbol in symbols:
            print(f"获取 {symbol} 数据...")
            try:
                df = self.fetch_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=start_time.strftime('%Y-%m-%d'),
                    end_time=end_time.strftime('%Y-%m-%d'),
                    limit=1000
                )
                
                if df is not None and not df.empty:
                    results[symbol] = df
                    print(f"  ✓ 获取 {len(df)} 条数据")
                else:
                    print(f"  ✗ 获取失败")
                    
                # 避免请求过快
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ✗ 获取 {symbol} 失败: {e}")
        
        return results
    
    def resample_data(self, df: pd.DataFrame, new_interval: str) -> pd.DataFrame:
        """
        重采样数据到不同的时间间隔
        
        Args:
            df: 原始DataFrame
            new_interval: 新的时间间隔，如 '4h', '1d'
            
        Returns:
            重采样后的DataFrame
        """
        if df.empty:
            return df
        
        # 定义重采样规则
        rule_map = {
            '1h': '1H',
            '2h': '2H',
            '4h': '4H',
            '6h': '6H',
            '8h': '8H',
            '12h': '12H',
            '1d': '1D',
            '3d': '3D',
            '1w': '1W',
            '1M': '1M'
        }
        
        if new_interval not in rule_map:
            raise ValueError(f"不支持的间隔: {new_interval}")
        
        rule = rule_map[new_interval]
        
        # 重采样
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # 删除NaN值
        resampled = resampled.dropna()
        
        print(f"重采样: {len(df)} 条 -> {len(resampled)} 条")
        return resampled
    
    def clean_old_cache(self, max_age_hours: int = 24):
        """
        清理过期的缓存文件
        
        Args:
            max_age_hours: 缓存最大保存时间（小时）
        """
        import time
        import os
        
        cache_dir = os.path.join(self.data_dir, 'cache')
        if not os.path.exists(cache_dir):
            return
        
        current_time = time.time()
        deleted_count = 0
        
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception as e:
                        print(f"删除缓存文件失败 {filename}: {e}")
        
        if deleted_count > 0:
            print(f"清理了 {deleted_count} 个过期缓存文件")
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """
        获取数据摘要统计
        
        Args:
            df: 数据DataFrame
            
        Returns:
            数据统计字典
        """
        if df.empty:
            return {}
        
        summary = {
            'start_date': df.index[0].strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': df.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
            'total_rows': len(df),
            'price_stats': {
                'open_mean': float(df['open'].mean()),
                'close_mean': float(df['close'].mean()),
                'high_max': float(df['high'].max()),
                'low_min': float(df['low'].min()),
                'close_std': float(df['close'].std())
            },
            'volume_stats': {
                'volume_mean': float(df['volume'].mean()),
                'volume_max': float(df['volume'].max()),
                'volume_min': float(df['volume'].min())
            },
            'return_stats': {
                'mean_return': float(df['close'].pct_change().mean()),
                'return_std': float(df['close'].pct_change().std()),
                'total_return': float(df['close'].iloc[-1] / df['close'].iloc[0] - 1)
            }
        }
        
        return summary