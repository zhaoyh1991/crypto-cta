"""
模拟交易所 - 用于模拟交易测试
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)

class MockExchange:
    """
    模拟交易所
    用于模拟交易测试，不涉及真实资金
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模拟交易所
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 账户信息
        self.initial_balance = config.get('initial_balance', 10000.0)
        self.balance = self.initial_balance
        self.commission = config.get('commission', 0.001)  # 0.1%
        
        # 持仓
        self.positions = {}  # symbol -> position_info
        self.orders = []
        
        # 市场数据
        self.market_prices = {
            'BTCUSDT': 50000.0,
            'ETHUSDT': 3000.0,
            'BNBUSDT': 400.0
        }
        
        # 交易历史
        self.trade_history = []
        
        # 订单ID计数器
        self.order_id_counter = 1
        
        logger.info(f"模拟交易所初始化完成，初始余额: ${self.balance:.2f}")
    
    # ========== 账户相关 ==========
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取模拟账户信息
        
        Returns:
            账户信息
        """
        account_info = {
            'accountType': 'SPOT',
            'balances': [
                {
                    'asset': 'USDT',
                    'free': self.balance,
                    'locked': 0.0
                }
            ],
            'permissions': ['SPOT'],
            'updateTime': int(time.time() * 1000)
        }
        
        # 添加持仓信息
        for symbol, position in self.positions.items():
            asset = symbol.replace('USDT', '')
            account_info['balances'].append({
                'asset': asset,
                'free': position['quantity'],
                'locked': 0.0
            })
        
        return account_info
    
    def get_balance(self, asset: str = 'USDT') -> float:
        """
        获取资产余额
        
        Args:
            asset: 资产符号
            
        Returns:
            可用余额
        """
        if asset == 'USDT':
            return self.balance
        
        # 查找持仓
        for symbol, position in self.positions.items():
            if symbol.replace('USDT', '') == asset:
                return position['quantity']
        
        return 0.0
    
    # ========== 市场数据 ==========
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取模拟行情
        
        Args:
            symbol: 交易对
            
        Returns:
            行情数据
        """
        if symbol not in self.market_prices:
            # 生成随机价格
            base_price = 100.0
            if 'BTC' in symbol:
                base_price = 50000.0
            elif 'ETH' in symbol:
                base_price = 3000.0
            
            self.market_prices[symbol] = base_price
        
        current_price = self.market_prices[symbol]
        
        # 模拟价格波动
        change_pct = random.uniform(-0.02, 0.02)  # ±2%
        new_price = current_price * (1 + change_pct)
        self.market_prices[symbol] = new_price
        
        ticker = {
            'symbol': symbol,
            'priceChange': new_price - current_price,
            'priceChangePercent': change_pct * 100,
            'weightedAvgPrice': (current_price + new_price) / 2,
            'prevClosePrice': current_price,
            'lastPrice': new_price,
            'lastQty': 0.1,
            'bidPrice': new_price * 0.999,
            'bidQty': 1.0,
            'askPrice': new_price * 1.001,
            'askQty': 1.0,
            'openPrice': current_price,
            'highPrice': max(current_price, new_price) * 1.01,
            'lowPrice': min(current_price, new_price) * 0.99,
            'volume': random.uniform(1000, 10000),
            'quoteVolume': random.uniform(50000000, 500000000),
            'openTime': int((time.time() - 86400) * 1000),  # 24小时前
            'closeTime': int(time.time() * 1000),
            'firstId': 0,
            'lastId': 100,
            'count': 100
        }
        
        return ticker
    
    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        获取模拟订单簿
        
        Args:
            symbol: 交易对
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        current_price = self.market_prices.get(symbol, 100.0)
        
        # 生成买卖盘
        bids = []
        asks = []
        
        for i in range(limit):
            bid_price = current_price * (1 - (i + 1) * 0.001)  # 逐渐降低
            ask_price = current_price * (1 + (i + 1) * 0.001)  # 逐渐升高
            
            bids.append([f"{bid_price:.2f}", f"{random.uniform(0.1, 1.0):.4f}"])
            asks.append([f"{ask_price:.2f}", f"{random.uniform(0.1, 1.0):.4f}"])
        
        orderbook = {
            'lastUpdateId': int(time.time() * 1000),
            'bids': bids,
            'asks': asks
        }
        
        return orderbook
    
    def get_klines(self, symbol: str, interval: str = '1h', 
                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取模拟K线数据
        
        Args:
            symbol: 交易对
            interval: K线间隔
            limit: 数据条数
            
        Returns:
            K线数据列表
        """
        if symbol not in self.market_prices:
            self.get_ticker(symbol)  # 初始化价格
        
        base_price = self.market_prices[symbol]
        klines = []
        
        # 生成历史K线
        for i in range(limit):
            timestamp = int((time.time() - (limit - i) * 3600) * 1000)  # 每小时一根
            
            # 模拟价格波动
            open_price = base_price * (1 + random.uniform(-0.05, 0.05))
            close_price = open_price * (1 + random.uniform(-0.03, 0.03))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = random.uniform(100, 1000)
            
            kline = [
                timestamp,                          # 开盘时间
                f"{open_price:.2f}",               # 开盘价
                f"{high_price:.2f}",               # 最高价
                f"{low_price:.2f}",                # 最低价
                f"{close_price:.2f}",              # 收盘价
                f"{volume:.4f}",                   # 成交量
                timestamp + 3600000,               # 收盘时间
                f"{close_price * volume:.2f}",     # 成交额
                100,                               # 成交笔数
                f"{volume * 0.6:.4f}",             # 主动买入成交量
                f"{close_price * volume * 0.6:.2f}",  # 主动买入成交额
                "0"                                # 请忽略
            ]
            
            klines.append(kline)
            
            # 更新基础价格
            base_price = close_price
        
        return klines
    
    # ========== 交易相关 ==========
    
    def create_order(self, symbol: str, side: str, order_type: str,
                    quantity: float, price: Optional[float] = None,
                    **kwargs) -> Dict[str, Any]:
        """
        创建模拟订单
        
        Args:
            symbol: 交易对
            side: 订单方向 (BUY/SELL)
            order_type: 订单类型
            quantity: 数量
            price: 价格（限价单需要）
            
        Returns:
            订单响应
        """
        # 获取当前价格
        ticker = self.get_ticker(symbol)
        current_price = float(ticker['lastPrice'])
        
        # 确定成交价格
        if price is None:
            price = current_price  # 市价单使用当前价格
        
        # 计算交易金额
        trade_value = price * quantity
        
        # 计算手续费
        commission = trade_value * self.commission
        
        # 检查资金是否充足
        if side == 'BUY':
            total_cost = trade_value + commission
            if self.balance < total_cost:
                raise ValueError(f"资金不足: 需要${total_cost:.2f}, 可用${self.balance:.2f}")
            
            # 更新余额
            self.balance -= total_cost
            
            # 更新持仓
            if symbol in self.positions:
                self.positions[symbol]['quantity'] += quantity
                self.positions[symbol]['avg_price'] = (
                    (self.positions[symbol]['avg_price'] * self.positions[symbol]['quantity'] + price * quantity) /
                    (self.positions[symbol]['quantity'] + quantity)
                )
            else:
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'entry_time': datetime.now()
                }
                
        else:  # SELL
            if symbol not in self.positions or self.positions[symbol]['quantity'] < quantity:
                raise ValueError(f"持仓不足: 需要{quantity}, 可用{self.positions.get(symbol, {}).get('quantity', 0)}")
            
            # 计算盈亏
            entry_price = self.positions[symbol]['avg_price']
            pnl = (price - entry_price) * quantity - commission
            
            # 更新余额
            self.balance += trade_value - commission
            
            # 更新持仓
            self.positions[symbol]['quantity'] -= quantity
            if self.positions[symbol]['quantity'] <= 0:
                del self.positions[symbol]
        
        # 生成订单响应
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        order_response = {
            'symbol': symbol,
            'orderId': order_id,
            'orderListId': -1,
            'clientOrderId': f"mock_{order_id}",
            'transactTime': int(time.time() * 1000),
            'price': f"{price:.2f}",
            'origQty': f"{quantity:.4f}",
            'executedQty': f"{quantity:.4f}",
            'cummulativeQuoteQty': f"{trade_value:.2f}",
            'status': 'FILLED',
            'timeInForce': 'GTC',
            'type': order_type,
            'side': side,
            'fills': [
                {
                    'price': f"{price:.2f}",
                    'qty': f"{quantity:.4f}",
                    'commission': f"{commission:.4f}",
                    'commissionAsset': 'USDT' if side == 'BUY' else symbol.replace('USDT', ''),
                    'tradeId': order_id
                }
            ]
        }
        
        # 记录订单
        self.orders.append({
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'timestamp': datetime.now()
        })
        
        # 记录交易历史
        self.trade_history.append({
            'trade_id': order_id,
            'symbol': symbol,
            'side': side.lower(),
            'quantity': quantity,
            'price': price,
            'value': trade_value,
            'commission': commission,
            'timestamp': datetime.now(),
            'balance_after': self.balance
        })
        
        logger.info(f"模拟订单执行: {symbol} {side} {quantity} @ ${price:.2f}, "
                   f"手续费: ${commission:.2f}, 余额: ${self.balance:.2f}")
        
        return order_response
    
    def create_market_order(self, symbol: str, side: str, 
                           quantity: float) -> Dict[str, Any]:
        """
        创建模拟市价订单
        
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
            order_type='MARKET',
            quantity=quantity
        )
    
    def create_limit_order(self, symbol: str, side: str,
                          quantity: float, price: float) -> Dict[str, Any]:
        """
        创建模拟限价订单
        
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
            order_type='LIMIT',
            quantity=quantity,
            price=price
        )
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        查询模拟订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            订单信息
        """
        # 查找订单
        for order in self.orders:
            if str(order['order_id']) == order_id:
                return {
                    'symbol': symbol,
                    'orderId': order['order_id'],
                    'clientOrderId': f"mock_{order['order_id']}",
                    'price': f"{order['price']:.2f}",
                    'origQty': f"{order['quantity']:.4f}",
                    'executedQty': f"{order['quantity']:.4f}",
                    'cummulativeQuoteQty': f"{order['price'] * order['quantity']:.2f}",
                    'status': 'FILLED',
                    'timeInForce': 'GTC',
                    'type': 'LIMIT',
                    'side': 'BUY' if order['side'] == 'BUY' else 'SELL',
                    'stopPrice': '0.00',
                    'icebergQty': '0.00',
                    'time': int(order['timestamp'].timestamp() * 1000),
                    'updateTime': int(order['timestamp'].timestamp() * 1000),
                    'isWorking': False,
                    'origQuoteOrderQty': '0.00'
                }
        
        raise ValueError(f"订单不存在: {order_id}")
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        取消模拟订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            取消响应
        """
        # 模拟订单立即成交，无法取消
        logger.warning(f"模拟订单已成交，无法取消: {order_id}")
        
        return {
            'symbol': symbol,
            'orderId': order_id,
            'origClientOrderId': f"mock_{order_id}",
            'clientOrderId': f"mock_{order_id}_canceled",
            'transactTime': int(time.time() * 1000),
            'price': '0.00',
            'origQty': '0.00',
            'executedQty': '0.00',
            'cummulativeQuoteQty': '0.00',
            'status': 'CANCELED',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'BUY'
        }
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取模拟未成交订单
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            未成交订单列表
        """
        # 模拟订单立即成交，没有未成交订单
        return []
    
    def get_all_orders(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取所有模拟订单
        
        Args:
            symbol: 交易对
            limit: 限制条数
            
        Returns:
            订单列表
        """
        # 过滤指定交易对的订单
        symbol_orders = [order for order in self.orders 
                        if order['symbol'] == symbol]
        
        # 限制数量
        symbol_orders = symbol_orders[-limit:] if limit > 0 else symbol_orders
        
        # 转换为API格式
        orders = []
        for order in symbol_orders:
            orders.append({
                'symbol': order['symbol'],
                'orderId': order['order_id'],
                'clientOrderId': f"mock_{order['order_id']}",
                'price': f"{order['price']:.2f}",
                'origQty': f"{order['quantity']:.4f}",
                'executedQty': f"{order['quantity']:.4f}",
                'cummulativeQuoteQty': f"{order['price'] * order['quantity']:.2f}",
                'status': 'FILLED',
                'timeInForce': 'GTC',
                'type': 'LIMIT',
                'side': 'BUY' if order['side'] == 'BUY' else 'SELL',
                'stopPrice': '0.00',
                'icebergQty': '0.00',
                'time': int(order['timestamp'].timestamp() * 1000),
                'updateTime': int(order['timestamp'].timestamp() * 1000),
                'isWorking': False,
                'origQuoteOrderQty': '0.00'
            })
        
        return orders
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模拟交易所信息
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            交易所信息
        """
        # 简化实现
        exchange_info = {
            'timezone': 'UTC',
            'serverTime': int(time.time() * 1000),
            'rateLimits': [],
            'exchangeFilters': [],
            'symbols': []
        }
        
        # 添加支持的交易对
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        for sym in symbols:
            if symbol is None or sym == symbol:
                exchange_info['symbols'].append({
                    'symbol': sym,
                    'status': 'TRADING',
                    'baseAsset': sym.replace('USDT', ''),
                    'quoteAsset': 'USDT',
                    'filters': [
                        {
                            'filterType': 'PRICE_FILTER',
                            'minPrice': '0.01000000',
                            'maxPrice': '1000000.00000000',
                            'tickSize': '0.01000000'
                        },
                        {
                            'filterType': 'LOT_SIZE',
                            'minQty': '0.00001000',
                            'maxQty': '10000.00000000',
                            'stepSize': '0.00001000'
                        }
                    ]
                })
        
        return exchange_info
    
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
        # 简化实现
        return {
            'price': 8,
            'quantity': 8
        }
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        获取交易历史
        
        Returns:
            交易历史列表
        """
        return self.trade_history.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要
        """
        if not self.trade_history:
            return {
                'initial_balance': self.initial_balance,
                'current_balance': self.balance,
                'total_return': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'total_pnl': 0.0
            }
        
        # 计算总盈亏
        total_pnl = self.balance - self.initial_balance
        
        # 计算胜率
        winning_trades = 0
        for trade in self.trade_history:
            if trade.get('pnl', 0) > 0:
                winning_trades += 1
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_return': (self.balance - self.initial_balance) / self.initial_balance,
            'total_trades': len(self.trade_history),
            'winning_trades': winning_trades,
            'win_rate': winning_trades / len(self.trade_history) if self.trade_history else 0,
            'total_pnl': total_pnl,
            'positions': self.positions.copy()
        }
    
    def reset(self):
        """重置模拟交易所"""
        self.balance = self.initial_balance
        self.positions = {}
        self.orders = []
        self.trade_history = []
        self.order_id_counter = 1
        
        logger.info("模拟交易所已重置")
                'executedQty': f"{order['quantity']:.4f}",
                'cummulativeQuoteQty': f"{order['price'] * order['quantity']:.2f}",
                'status': 'FILLED',
                'timeInForce': 'GTC',
                'type': 'LIMIT',
                'side': 'BUY' if order['side'] == 'BUY' else 'SELL',
                'stopPrice': '0.00',
                'icebergQty': '0.00',
                'time': int(order['timestamp'].timestamp() * 1000),
