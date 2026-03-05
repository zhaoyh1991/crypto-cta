"""
实盘交易管理器 - 管理实盘交易流程
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import time
import json
import os
from enum import Enum

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    """交易模式"""
    PAPER_TRADING = "paper"      # 模拟交易
    LIVE_TRADING = "live"        # 实盘交易
    BACKTEST = "backtest"        # 回测模式

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"          # 低风险（保守）
    MEDIUM = "medium"    # 中风险（平衡）
    HIGH = "high"        # 高风险（激进）

class LiveTradingManager:
    """
    实盘交易管理器
    负责管理实盘交易的全流程
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化交易管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.mode = TradingMode(config.get('mode', 'paper'))
        self.risk_level = RiskLevel(config.get('risk_level', 'medium'))
        
        # 交易所连接
        self.exchange = None
        
        # 策略管理
        self.strategies = {}
        self.active_strategies = {}
        
        # 交易状态
        self.is_running = False
        self.start_time = None
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        
        # 风险控制
        self.max_daily_loss = config.get('max_daily_loss', 0.05)  # 5%
        self.max_position_size = config.get('max_position_size', 0.2)  # 20%
        self.max_concurrent_trades = config.get('max_concurrent_trades', 3)
        
        # 监控
        self.monitoring_interval = config.get('monitoring_interval', 60)  # 秒
        self.health_check_interval = config.get('health_check_interval', 300)  # 秒
        
        # 日志和记录
        self.trades_log = []
        self.performance_log = []
        
        # 创建目录
        self._create_directories()
        
        logger.info(f"实盘交易管理器初始化完成，模式: {self.mode.value}")
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = ['logs/live', 'data/live', 'results/live', 'backups']
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)
    
    def connect_exchange(self, exchange_config: Dict[str, Any]) -> bool:
        """
        连接交易所
        
        Args:
            exchange_config: 交易所配置
            
        Returns:
            是否连接成功
        """
        try:
            if self.mode == TradingMode.PAPER_TRADING:
                # 模拟交易所
                from mock_exchange import MockExchange
                self.exchange = MockExchange(exchange_config)
                logger.info("连接到模拟交易所")
                
            elif self.mode == TradingMode.LIVE_TRADING:
                # 真实交易所
                from binance_exchange import BinanceExchange
                self.exchange = BinanceExchange(
                    api_key=exchange_config.get('api_key'),
                    api_secret=exchange_config.get('api_secret'),
                    testnet=exchange_config.get('testnet', True)
                )
                logger.info("连接到币安交易所")
                
            else:
                logger.error(f"不支持的模式: {self.mode}")
                return False
            
            # 测试连接
            if self._test_connection():
                logger.info("交易所连接测试成功")
                return True
            else:
                logger.error("交易所连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"连接交易所失败: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """测试交易所连接"""
        try:
            # 获取账户信息或市场数据
            if hasattr(self.exchange, 'get_account_info'):
                account_info = self.exchange.get_account_info()
                logger.info(f"账户信息获取成功: {account_info.get('accountType', 'N/A')}")
                return True
            elif hasattr(self.exchange, 'get_ticker'):
                ticker = self.exchange.get_ticker('BTCUSDT')
                logger.info(f"市场数据获取成功: BTCUSDT = {ticker.get('lastPrice', 'N/A')}")
                return True
            else:
                logger.warning("无法测试连接，跳过")
                return True
                
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False
    
    def register_strategy(self, strategy_id: str, strategy_class: Callable,
                         strategy_config: Dict[str, Any]) -> bool:
        """
        注册策略
        
        Args:
            strategy_id: 策略ID
            strategy_class: 策略类
            strategy_config: 策略配置
            
        Returns:
            是否注册成功
        """
        try:
            # 创建策略实例
            strategy = strategy_class(
                name=strategy_id,
                config=strategy_config
            )
            
            self.strategies[strategy_id] = {
                'instance': strategy,
                'class': strategy_class,
                'config': strategy_config,
                'status': 'registered'
            }
            
            logger.info(f"策略 '{strategy_id}' 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"注册策略失败: {e}")
            return False
    
    def activate_strategy(self, strategy_id: str, symbol: str) -> bool:
        """
        激活策略
        
        Args:
            strategy_id: 策略ID
            symbol: 交易对
            
        Returns:
            是否激活成功
        """
        if strategy_id not in self.strategies:
            logger.error(f"策略 '{strategy_id}' 未注册")
            return False
        
        # 检查是否已经激活
        if strategy_id in self.active_strategies:
            logger.warning(f"策略 '{strategy_id}' 已经激活")
            return True
        
        # 获取初始化数据
        try:
            # 获取历史数据用于初始化
            historical_data = self._get_historical_data(symbol, days=30)
            if historical_data is None or historical_data.empty:
                logger.error(f"无法获取 {symbol} 的历史数据")
                return False
            
            # 初始化策略
            strategy = self.strategies[strategy_id]['instance']
            strategy.initialize(historical_data)
            
            # 添加到活跃策略
            self.active_strategies[strategy_id] = {
                'strategy': strategy,
                'symbol': symbol,
                'status': 'active',
                'activated_at': datetime.now(),
                'performance': {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_pnl': 0.0
                }
            }
            
            logger.info(f"策略 '{strategy_id}' 激活成功，交易对: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"激活策略失败: {e}")
            return False
    
    def deactivate_strategy(self, strategy_id: str) -> bool:
        """
        停用策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否停用成功
        """
        if strategy_id not in self.active_strategies:
            logger.warning(f"策略 '{strategy_id}' 未激活")
            return True
        
        try:
            # 平掉所有仓位
            self._close_all_positions(strategy_id)
            
            # 保存策略状态
            self._save_strategy_state(strategy_id)
            
            # 从活跃策略中移除
            strategy_info = self.active_strategies.pop(strategy_id)
            
            # 记录性能
            performance = strategy_info['performance']
            logger.info(f"策略 '{strategy_id}' 停用，"
                       f"总交易: {performance['total_trades']}, "
                       f"总盈亏: {performance['total_pnl']:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"停用策略失败: {e}")
            return False
    
    def start_trading(self) -> bool:
        """
        开始交易
        
        Returns:
            是否启动成功
        """
        if not self.exchange:
            logger.error("未连接交易所")
            return False
        
        if not self.active_strategies:
            logger.error("没有激活的策略")
            return False
        
        # 确认风险
        if not self._confirm_risk():
            logger.warning("用户取消交易")
            return False
        
        logger.info("=" * 60)
        logger.info("开始实盘交易")
        logger.info(f"模式: {self.mode.value}")
        logger.info(f"风险等级: {self.risk_level.value}")
        logger.info(f"活跃策略: {len(self.active_strategies)} 个")
        logger.info("=" * 60)
        
        # 启动交易循环
        self.is_running = True
        self.start_time = datetime.now()
        
        # 启动监控线程
        self._start_monitoring()
        
        # 启动交易主循环
        self._trading_loop()
        
        return True
    
    def stop_trading(self) -> bool:
        """
        停止交易
        
        Returns:
            是否停止成功
        """
        logger.info("停止交易...")
        
        self.is_running = False
        
        # 平掉所有仓位
        for strategy_id in list(self.active_strategies.keys()):
            self._close_all_positions(strategy_id)
        
        # 保存状态
        self._save_manager_state()
        
        # 生成报告
        self._generate_performance_report()
        
        logger.info("交易已停止")
        return True
    
    def _confirm_risk(self) -> bool:
        """确认风险"""
        if self.mode == TradingMode.PAPER_TRADING:
            return True
        
        # 实盘交易需要额外确认
        warning_message = f"""
        ⚠️  实盘交易风险警告 ⚠️
        
        您即将开始实盘交易，涉及真实资金！
        
        交易模式: {self.mode.value}
        风险等级: {self.risk_level.value}
        最大单日亏损: {self.max_daily_loss*100}%
        最大仓位: {self.max_position_size*100}%
        
        请确认：
        1. 您已充分理解交易风险
        2. 您已进行充分的回测和模拟测试
        3. 您使用的是可承受损失的资金
        4. 您已设置适当的风险控制
        
        输入 'CONFIRM' 继续，或输入其他内容取消：
        """
        
        print(warning_message)
        confirmation = input("> ")
        
        return confirmation.strip().upper() == 'CONFIRM'
    
    def _trading_loop(self):
        """交易主循环"""
        logger.info("启动交易循环")
        
        last_health_check = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # 健康检查
                if current_time - last_health_check > self.health_check_interval:
                    if not self._health_check():
                        logger.error("健康检查失败，停止交易")
                        self.stop_trading()
                        break
                    last_health_check = current_time
                
                # 检查每日亏损限制
                if self._check_daily_loss_limit():
                    logger.warning("达到每日亏损限制，停止交易")
                    self.stop_trading()
                    break
                
                # 为每个活跃策略处理市场数据
                for strategy_id, strategy_info in self.active_strategies.items():
                    symbol = strategy_info['symbol']
                    
                    # 获取最新市场数据
                    market_data = self._get_market_data(symbol)
                    if not market_data:
                        continue
                    
                    # 策略处理
                    strategy = strategy_info['strategy']
                    result = strategy.on_bar(market_data)
                    
                    # 执行交易决策
                    if result['decision']['action'] != 'hold':
                        self._execute_trade(
                            strategy_id=strategy_id,
                            symbol=symbol,
                            decision=result['decision'],
                            market_data=market_data
                        )
                
                # 等待下一次循环
                time.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                logger.info("用户中断交易")
                self.stop_trading()
                break
                
            except Exception as e:
                logger.error(f"交易循环错误: {e}")
                time.sleep(10)  # 错误后等待10秒
    
    def _execute_trade(self, strategy_id: str, symbol: str,
                      decision: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
        """
        执行交易
        
        Args:
            strategy_id: 策略ID
            symbol: 交易对
            decision: 交易决策
            market_data: 市场数据
            
        Returns:
            是否执行成功
        """
        try:
            # 检查风险限制
            if not self._check_risk_limits(strategy_id, decision):
                logger.warning(f"风险检查失败，跳过交易: {strategy_id}")
                return False
            
            # 执行订单
            if self.mode == TradingMode.PAPER_TRADING:
                # 模拟交易
                trade_result = self._execute_paper_trade(strategy_id, symbol, decision, market_data)
            else:
                # 实盘交易
                trade_result = self._execute_live_trade(strategy_id, symbol, decision, market_data)
            
            if trade_result:
                # 更新策略状态
                strategy = self.active_strategies[strategy_id]['strategy']
                strategy.update_position(trade_result)
                
                # 更新性能记录
                self._update_performance(strategy_id, trade_result)
                
                # 记录交易
                self._log_trade(trade_result)
                
                logger.info(f"交易执行成功: {trade_result.get('trade_id', 'N/A')}")
                return True
            else:
                logger.warning("交易执行失败")
                return False
                
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return False
    
    def _execute_paper_trade(self, strategy_id: str, symbol: str,
                           decision: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行模拟交易"""
        # 获取策略
        strategy = self.active_strategies[strategy_id]['strategy']
        
        # 模拟交易逻辑
        trade_id = f"paper_{int(time.time())}_{len(self.trades_log)}"
        
        trade = {
            'trade_id': trade_id,
            'strategy_id': strategy_id,
            'symbol': symbol,
            'timestamp': datetime.now(),
            'action': decision['action'],
            'side': 'buy' if decision['action'] == 'buy' else 'sell',
            'price': market_data['close'],
            'quantity': decision['quantity'],
            'value': market_data['close'] * decision['quantity'],
            'commission': market_data['close'] * decision['quantity'] * strategy.commission,
            'pnl': 0.0,  # 模拟交易简化处理
            'reason': decision['reason'],
            'stop_loss': decision.get('stop_loss'),
            'take_profit': decision.get('take_profit'),
            'is_paper': True
        }
        
        return trade
    
    def _execute_live_trade(self, strategy_id: str, symbol: str,
                          decision: Dict[str, Any], market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行实盘交易"""
        try:
            from .binance_exchange import OrderSide
            
            # 确定订单方向
            if decision['action'] == 'buy':
                side = OrderSide.BUY
            else:
                side = OrderSide.SELL
            
            # 创建订单
            order_result = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                quantity=decision['quantity']
            )
            
            # 构建交易记录
            trade = {
                'trade_id': order_result.get('orderId', f"live_{int(time.time())}"),
                'strategy_id': strategy_id,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'action': decision['action'],
                'side': side.value.lower(),
                'price': float(order_result.get('price', market_data['close'])),
                'quantity': float(order_result.get('executedQty', decision['quantity'])),
                'value': float(order_result.get('cummulativeQuoteQty', 0)),
                'commission': float(order_result.get('commission', 0)),
                'commission_asset': order_result.get('commissionAsset', ''),
                'pnl': 0.0,  # 需要后续计算
                'reason': decision['reason'],
                'stop_loss': decision.get('stop_loss'),
                'take_profit': decision.get('take_profit'),
                'is_paper': False,
                'order_result': order_result
            }
            
            return trade
            
        except Exception as e:
            logger.error(f"实盘交易执行失败: {e}")
            return None
    
    def _check_risk_limits(self, strategy_id: str, decision: Dict[str, Any]) -> bool:
        """检查风险限制"""
        # 检查仓位大小
        position_size = decision.get('quantity', 0) * decision.get('price', 0)
        account_balance = self._get_account_balance()
        
        if account_balance > 0 and position_size / account_balance > self.max_position_size:
            logger.warning(f"仓位超过限制: {position_size/account_balance*100:.1f}% > {self.max_position_size*100}%")
            return False
        
        # 检查并发交易数量
        active_trades = len([t for t in self.trades_log 
                           if t.get('strategy_id') == strategy_id and not t.get('is_closed', False)])
        
        if active_trades >= self.max_concurrent_trades:
            logger.warning(f"并发交易数量超过限制: {active_trades} >= {self.max_concurrent_trades}")
            return False
        
        return True
    
    def _check_daily_loss_limit(self) -> bool:
        """检查每日亏损限制"""
       