"""
币安交易所接口 - 支持实盘交易
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import hmac
import hashlib
import urllib.parse
from enum import Enum

logger = logging.getLogger(__name__)

class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    """订单类型"""
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"

class OrderStatus(Enum):
    """订单状态"""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class BinanceExchange:
    """
    币安交易所接口
    支持现货交易和实时数据
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        初始化币安交易所连接
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网络
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # 设置API端点
        if testnet:
            self.base_url = "https://testnet.binance.vision"
            self.ws_url = "wss://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443"
        
        # 会话管理
        self.session = None
        self.ws_connections = {}
        
        # 账户信息
        self.account_info = {}
        self.balances = {}
        
        # 订单簿缓存
        self.orderbooks = {}
        
        # 初始化
        self._init_session()
        
        logger.info(f"币安交易所初始化完成，测试网: {testnet}")
    
    def _init_session(self):
        """初始化HTTP会话"""
        import requests
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """
        签名请求参数
        
        Args:
            params: 请求参数
            
        Returns:
            签名字符串
        """
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名
            
        Returns:
            响应数据
        """
        import requests
        
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        # 添加时间戳（签名请求需要）
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._sign_request(params)
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, params=params)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP请求失败: {e}")
            raise
        except ValueError as e:
            logger.error(f"JSON解析失败: {e}")
            raise
    
    # ========== 账户相关 ==========
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        endpoint = "/api/v3/account"
        response = self._make_request('GET', endpoint, signed=True)
        
        self.account_info = response
        self.balances = {
            asset['asset']: {
                'free': float(asset['free']),
                'locked': float(asset['locked'])
            }
            for asset in response.get('balances', [])
        }
        
        logger.info(f"账户信息获取成功，资产数量: {len(self.balances)}")
        return response
    
    def get_balance(self, asset: str = 'USDT') -> float:
        """
        获取资产余额
        
        Args:
            asset: 资产符号
            
        Returns:
            可用余额
        """
        if not self.balances:
            self.get_account_info()
        
        balance = self.balances.get(asset, {'free': 0.0, 'locked': 0.0})
        return balance['free']
    
    # ========== 市场数据 ==========
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取交易对行情
        
        Args:
            symbol: 交易对
            
        Returns:
            行情数据
        """
        endpoint = "/api/v3/ticker/24hr"
        params = {'symbol': symbol}
        
        response = self._make_request('GET', endpoint, params)
        return response
    
    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        获取订单簿
        
        Args:
            symbol: 交易对
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        endpoint = "/api/v3/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        response = self._make_request('GET', endpoint, params)
        
        # 缓存订单簿
        self.orderbooks[symbol] = {
            'bids': [(float(price), float(qty)) for price, qty in response.get('bids', [])],
            'asks': [(float(price), float(qty)) for price, qty in response.get('asks', [])],
            'timestamp': response.get('lastUpdateId', 0)
        }
        
        return response
    
    def get_klines(self, symbol: str, interval: str = '1h', 
                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: K线间隔
            limit: 数据条数
            
        Returns:
            K线数据列表
        """
        endpoint = "/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = self._make_request('GET', endpoint, params)
        
        # 转换格式
        klines = []
        for kline in response:
            klines.append({
                'timestamp': kline[0],
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'close_time': kline[6],
                'quote_volume': float(kline[7]),
                'trades': kline[8],
                'taker_buy_base': float(kline[9]),
                'taker_buy_quote': float(kline[10])
            })
        
        return klines
    
    # ========== 交易相关 ==========
    
    def create_order(self, symbol: str, side: OrderSide, 
                    order_type: OrderType, quantity: float,
                    price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            symbol: 交易对
            side: 订单方向
            order_type: 订单类型
            quantity: 数量
            price: 价格（限价单需要）
            stop_price: 止损价格
            
        Returns:
            订单响应
        """
        endpoint = "/api/v3/order"
        
        params = {
            'symbol': symbol,
            'side': side.value,
            'type': order_type.value,
            'quantity': self._format_quantity(symbol, quantity),
            'newOrderRespType': 'FULL'  # 返回完整订单信息
        }
        
        # 添加价格参数
        if price is not None:
            params['price'] = self._format_price(symbol, price)
        
        # 添加止损价格
        if stop_price is not None:
            params['stopPrice'] = self._format_price(symbol, stop_price)
        
        # 设置时间戳
        params['timestamp'] = int(time.time() * 1000)
        
        # 签名请求
        params['signature'] = self._sign_request(params)
        
        response = self._make_request('POST', endpoint, params)
        
        logger.info(f"订单创建成功: {symbol} {side.value} {order_type.value} "
                   f"数量: {quantity} 价格: {price}")
        
        return response
    
    def create_market_order(self, symbol: str, side: OrderSide, 
                           quantity: float) -> Dict[str, Any]:
        """
        创建市价订单
        
        Args:
            symbol: 交易对
            side: 订单方向
            quantity: 数量
            
        Returns:
            订单响应
        """
        return self.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
    
    def create_limit_order(self, symbol: str, side: OrderSide,
                          quantity: float, price: float) -> Dict[str, Any]:
        """
        创建限价订单
        
        Args:
            symbol: 交易对
            side: 订单方向
            quantity: 数量
            price: 价格
            
        Returns:
            订单响应
        """
        return self.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
    
    def create_stop_loss_order(self, symbol: str, side: OrderSide,
                              quantity: float, stop_price: float) -> Dict[str, Any]:
        """
        创建止损订单
        
        Args:
            symbol: 交易对
            side: 订单方向
            quantity: 数量
            stop_price: 止损价格
            
        Returns:
            订单响应
        """
        return self.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.STOP_LOSS,
            quantity=quantity,
            stop_price=stop_price
        )
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        查询订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            订单信息
        """
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        response = self._make_request('GET', endpoint, params, signed=True)
        return response
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            取消响应
        """
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        response = self._make_request('DELETE', endpoint, params, signed=True)
        
        logger.info(f"订单取消成功: {symbol} 订单ID: {order_id}")
        return response
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取未成交订单
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            未成交订单列表
        """
        endpoint = "/api/v3/openOrders"
        params = {}
        
        if symbol:
            params['symbol'] = symbol
        
        response = self._make_request('GET', endpoint, params, signed=True)
        return response
    
    def get_all_orders(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取所有订单
        
        Args:
            symbol: 交易对
            limit: 限制条数
            
        Returns:
            订单列表
        """
        endpoint = "/api/v3/allOrders"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        response = self._make_request('GET', endpoint, params, signed=True)
        return response
    
    # ========== 工具方法 ==========
    
    def _format_price(self, symbol: str, price: float) -> str:
        """
        格式化价格（根据交易对精度）
        
        Args:
            symbol: 交易对
            price: 价格
            
        Returns:
            格式化后的价格字符串
        """
        # 这里需要根据交易对的实际精度进行格式化
        # 简化处理：保留8位小数
        return f"{price:.8f}"
    
    def _format_quantity(self, symbol: str, quantity: float) -> str:
        """
        格式化数量（根据交易对精度）
        
        Args:
            symbol: 交易对
            quantity: 数量
            
        Returns:
            格式化后的数量字符串
        """
        # 这里需要根据交易对的实际精度进行格式化
        # 简化处理：保留8位小数
        return f"{quantity:.8f}"
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取交易所信息
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            交易所信息
        """
        endpoint = "/api/v3/exchangeInfo"
        params = {}
        
        if symbol:
            params['symbol'] = symbol
        
        response = self._make_request('GET', endpoint, params)
        return response
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取交易对信息
        
        Args:
            symbol: 交易对
            
        Returns:
            交易对信息
        """
        exchange_info = self.get_exchange_info()
        
        for symbol_info in exchange_info.get('symbols', []):
            if symbol_info['symbol'] == symbol:
                return symbol_info
        
        return None
    
    def get_precision(self, symbol: str) -> Dict[str, int]:
        """
        获取交易对精度
        
        Args:
            symbol: 交易对
            
        Returns:
            精度信息
        """
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return {'price': 8, 'quantity': 8}
        
        filters = symbol_info.get('filters', [])
        
        price_precision = 8
        quantity_precision = 8
        
        for filter_item in filters:
            if filter_item['filterType'] == 'PRICE_FILTER':
                tick_size = filter_item.get('tickSize', '0.00000001')
                # 计算小数点后位数
                price_precision = len(tick_size.split('.')[1].rstrip('0'))
            
            elif filter_item['filterType'] == 'LOT_SIZE':
                step_size = filter_item.get('stepSize', '0.00000001')
                # 计算小数点后位数
                quantity_precision = len(step_size.split('.')[1].rstrip('0'))
        
        return {
            'price': price_precision,
            'quantity': quantity_precision
        }
    
    # ========== WebSocket 连接 ==========
    
    def start_websocket(self, symbol: str, callback):
        """
        启动WebSocket连接
        
        Args:
            symbol: 交易对
            callback: 回调函数
        """
        import websocket
        import threading
        
        # 构建WebSocket URL
        stream_name = f"{symbol.lower()}@kline_1h"
        ws_url = f"{self.ws_url}/ws/{stream_name}"
        
        def on_message(ws, message):
            """WebSocket消息处理"""
            import json
            try:
                data = json.loads(message)
                callback(data)
            except Exception as e:
                logger.error(f"WebSocket消息处理失败: {e}")
        
        def on_error(ws, error):
            """WebSocket错误处理"""
            logger.error(f"WebSocket错误: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            """WebSocket关闭处理"""
            logger.info(f"WebSocket连接关闭: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            """WebSocket打开处理"""
            logger.info(f"WebSocket连接已建立: {symbol}")
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # 保存连接
        self.ws_connections[symbol] = ws
        
        # 启动WebSocket线程
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        logger.info(f"WebSocket连接启动: {symbol}")
    
    def stop_websocket(self, symbol: str):
        """
        停止WebSocket连接
        
        Args:
            symbol: 