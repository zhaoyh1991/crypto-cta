"""
统一交易引擎 - 支持回测和实盘交易
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Any, Callable
import json
import os
from base_strategy import BaseStrategy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedTradingEngine:
    """
    统一交易引擎
    支持回测模式和实盘交易模式
    """
    
    def __init__(self, mode: str = 'backtest', config: Dict[str, Any] = None):
        """
        初始化交易引擎
        
        Args:
            mode: 运行模式，'backtest' 或 'live'
            config: 引擎配置
        """
        self.mode = mode
        self.config = config or {}
        
        # 策略相关
        self.strategies = {}
        self.active_strategies = {}
        
        # 数据相关
        self.data_source = None
        self.market_data = {}
        
        # 交易相关
        self.exchange = None
        self.orders = []
        self.positions = {}
        
        # 状态相关
        self.is_running = False
        self.start_time = None
        self.initial_capital = self.config.get('initial_capital', 10000.0)
        
        # 性能监控
        self.performance_metrics = {}
        
        # 创建必要的目录
        self._create_directories()
        
        logger.info(f"交易引擎初始化完成，模式: {mode}")
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = ['logs', 'data', 'results', 'configs', 'strategies']
        for dir_name in directories:
            os.makedirs(dir_name, exist_ok=True)
    
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
            logger.error(f"注册策略 '{strategy_id}' 失败: {e}")
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
        
        strategy_info = self.strategies[strategy_id]
        
        # 检查是否已经激活
        if strategy_id in self.active_strategies:
            logger.warning(f"策略 '{strategy_id}' 已经激活")
            return True
        
        # 初始化策略
        try:
            # 获取初始化数据
            init_data = self._get_init_data(symbol)
            if init_data is None or init_data.empty:
                logger.error(f"无法获取 {symbol} 的初始化数据")
                return False
            
            # 初始化策略
            strategy_info['instance'].initialize(init_data)
            
            # 添加到活跃策略
            self.active_strategies[strategy_id] = {
                'strategy': strategy_info['instance'],
                'symbol': symbol,
                'status': 'active',
                'activated_at': datetime.now(),
                'performance': {}
            }
            
            logger.info(f"策略 '{strategy_id}' 激活成功，交易对: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"激活策略 '{strategy_id}' 失败: {e}")
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
            del self.active_strategies[strategy_id]
            
            logger.info(f"策略 '{strategy_id}' 已停用")
            return True
            
        except Exception as e:
            logger.error(f"停用策略 '{strategy_id}' 失败: {e}")
            return False
    
    def set_data_source(self, data_source: Any):
        """
        设置数据源
        
        Args:
            data_source: 数据源对象
        """
        self.data_source = data_source
        logger.info("数据源设置完成")
    
    def set_exchange(self, exchange: Any):
        """
        设置交易所连接
        
        Args:
            exchange: 交易所连接对象
        """
        self.exchange = exchange
        logger.info("交易所连接设置完成")
    
    def run_backtest(self, start_date: str, end_date: str, 
                    symbols: List[str] = None) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            symbols: 交易对列表
            
        Returns:
            回测结果
        """
        if self.mode != 'backtest':
            logger.warning("当前不是回测模式，但正在运行回测")
        
        logger.info(f"开始回测: {start_date} 到 {end_date}")
        
        # 获取历史数据
        historical_data = self._get_historical_data(start_date, end_date, symbols)
        if not historical_data:
            logger.error("无法获取历史数据")
            return {}
        
        # 初始化结果
        results = {
            'backtest_id': f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_date': start_date,
            'end_date': end_date,
            'symbols': symbols,
            'strategies': {},
            'overall_metrics': {},
            'trades': [],
            'equity_curve': []
        }
        
        # 为每个活跃策略运行回测
        for strategy_id, strategy_info in self.active_strategies.items():
            symbol = strategy_info['symbol']
            
            if symbol not in historical_data:
                logger.warning(f"策略 '{strategy_id}' 的交易对 {symbol} 无历史数据")
                continue
            
            # 运行策略回测
            strategy_results = self._run_strategy_backtest(
                strategy_id, historical_data[symbol]
            )
            
            results['strategies'][strategy_id] = strategy_results
        
        # 计算总体指标
        results['overall_metrics'] = self._calculate_overall_metrics(results)
        
        # 保存结果
        self._save_backtest_results(results)
        
        logger.info("回测完成")
        return results
    
    def start_live_trading(self):
        """
        开始实盘交易
        """
        if self.mode != 'live':
            logger.error("当前不是实盘交易模式")
            return False
        
        if not self.exchange:
            logger.error("未设置交易所连接")
            return False
        
        logger.info("开始实盘交易")
        self.is_running = True
        self.start_time = datetime.now()
        
        # 启动交易循环
        self._trading_loop()
        
        return True
    
    def stop_trading(self):
        """
        停止交易
        """
        logger.info("停止交易")
        self.is_running = False
        
        # 平掉所有仓位
        for strategy_id in list(self.active_strategies.keys()):
            self._close_all_positions(strategy_id)
        
        # 保存状态
        self._save_engine_state()
    
    def _get_init_data(self, symbol: str, lookback_days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取初始化数据
        
        Args:
            symbol: 交易对
            lookback_days: 回溯天数
            
        Returns:
            初始化数据
        """
        try:
            if self.data_source:
                # 使用数据源获取数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=lookback_days)
                
                data = self.data_source.fetch_klines(
                    symbol=symbol,
                    interval='1h',
                    start_time=start_date.strftime('%Y-%m-%d'),
                    end_time=end_date.strftime('%Y-%m-%d'),
                    limit=lookback_days * 24
                )
                return data
            else:
                # 生成模拟数据
                return self._generate_sample_data(symbol, lookback_days)
                
        except Exception as e:
            logger.error(f"获取初始化数据失败: {e}")
            return None
    
    def _get_historical_data(self, start_date: str, end_date: str, 
                           symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        获取历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            symbols: 交易对列表
            
        Returns:
            历史数据字典
        """
        historical_data = {}
        
        for symbol in symbols or []:
            try:
                if self.data_source:
                    data = self.data_source.fetch_klines(
                        symbol=symbol,
                        interval='1h',
                        start_time=start_date,
                        end_time=end_date,
                        limit=1000
                    )
                else:
                    # 生成模拟数据
                    days = (datetime.strptime(end_date, '%Y-%m-%d') - 
                           datetime.strptime(start_date, '%Y-%m-%d')).days
                    data = self._generate_sample_data(symbol, days)
                
                if data is not None and not data.empty:
                    historical_data[symbol] = data
                    logger.info(f"获取 {symbol} 历史数据: {len(data)} 条")
                    
            except Exception as e:
                logger.error(f"获取 {symbol} 历史数据失败: {e}")
        
        return historical_data
    
    def _run_strategy_backtest(self, strategy_id: str, 
                             historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        运行单个策略回测
        
        Args:
            strategy_id: 策略ID
            historical_data: 历史数据
            
        Returns:
            策略回测结果
        """
        strategy_info = self.active_strategies[strategy_id]
        strategy = strategy_info['strategy']
        
        logger.info(f"运行策略 '{strategy_id}' 回测，数据量: {len(historical_data)}")
        
        # 重置策略状态
        strategy.reset()
        
        trades = []
        equity_curve = []
        
        # 按时间顺序处理每根K线
        for idx, (timestamp, row) in enumerate(historical_data.iterrows()):
            # 准备K线数据
            bar = {
                'timestamp': timestamp,
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row.get('volume', 0)
            }
            
            # 策略处理
            result = strategy.on_bar(bar)
            
            # 执行交易决策
            if result['decision']['action'] != 'hold':
                trade = self._execute_trade(
                    strategy_id=strategy_id,
                    symbol=strategy_info['symbol'],
                    decision=result['decision'],
                    bar=bar,
                    is_backtest=True
                )
                
                if trade:
                    trades.append(trade)
                    
                    # 更新策略仓位
                    strategy.update_position(trade)
            
            # 记录权益曲线
            equity_record = {
                'timestamp': timestamp,
                'equity': strategy.equity,
                'price': bar['close'],
                'position': strategy.position
            }
            equity_curve.append(equity_record)
        
        # 计算策略指标
        metrics = strategy.calculate_metrics()
        
        # 整理结果
        strategy_results = {
            'strategy_id': strategy_id,
            'symbol': strategy_info['symbol'],
            'metrics': metrics,
            'trades': trades,
            'equity_curve': equity_curve,
            'final_status': strategy.get_status()
        }
        
        return strategy_results
    
    def _execute_trade(self, strategy_id: str, symbol: str, 
                      decision: Dict[str, Any], bar: Dict[str, Any],
                      is_backtest: bool = True) -> Optional[Dict[str, Any]]:
        """
        执行交易
        
        Args:
            strategy_id: 策略ID
            symbol: 交易对
            decision: 交易决策
            bar: K线数据
            is_backtest: 是否为回测
            
        Returns:
            交易记录
        """
        try:
            if is_backtest:
                # 回测模式：模拟交易
                trade = self._simulate_trade(strategy_id, symbol, decision, bar)
            else:
                # 实盘模式：实际下单
                trade = self._place_real_order(strategy_id, symbol, decision, bar)
            
            if trade:
                self.orders.append(trade)
                logger.info(f"交易执行: {trade}")
            
            return trade
            
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return None
    
    def _simulate_trade(self, strategy_id: str, symbol: str,
                       decision: Dict[str, Any], bar: Dict[str, Any]) -> Dict[str, Any]:
        """
        模拟交易（回测用）
        
        Args:
            strategy_id: 策略ID
            symbol: 交易对
            decision: 交易决策
            bar: K线数据
            
        Returns:
            交易记录
        """
        # 获取策略实例
        strategy_info = self.active_strategies[strategy_id]
        strategy = strategy_info['strategy']
        
        # 计算交易成本
        price = decision['price']
        quantity = decision['quantity']
        trade_value = price * quantity
        commission = trade_value * strategy.commission
        
        # 计算盈亏（简化计算）
        pnl = 0.0
        if strategy.position != 0:  # 平仓
            position_change = price - strategy.entry_price
            if strategy.position == -1:  # 空头平仓
                position_change = -position_change
            pnl = position_change * quantity - commission * 2
        
        # 创建交易记录
        trade = {
            'trade_id': f"trade_{int(time.time())}_{len(self.orders)}",
            'strategy_id': strategy_id,
            'symbol': symbol,
            'timestamp': bar['timestamp'],
            'action': decision['action'],
            'side': 'buy' if decision['action'] == 'buy' else 'sell',
            'price': price,
            'quantity': quantity,
            'value': trade_value,
            'commission': commission,
            'pnl': pnl,
            'reason': decision['reason'],
            'stop_loss': decision.get('stop_loss'),
            'take_profit': decision.get('take_profit'),
            'equity_before': strategy.equity,
            'equity_after': strategy.equity + pnl,
            'is_backtest': True
        }
        
        return trade
    
    def _place_real_order(self, strategy_id: str, symbol: str,
                         decision: Dict[str, Any], bar: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        下实盘订单
        
        Args:
            strategy_id: 策略ID
            symbol: 交易对
            decision: 交易决策
            bar: K线数据
            
        Returns:
            交易记录
        """
        if not self.exchange:
            logger.error("未设置交易所连接")
            return None
        
        try:
            # 实际下单逻辑（需要根据具体交易所API实现）
            order_params = {
                'symbol': symbol,
                'side': 'buy' if decision['action'] == 'buy' else 'sell',
                'type': 'limit',  # 或 'market'
                'quantity': decision['quantity'],
                'price': decision['price']
            }
            
            # 这里需要根据具体交易所API调用下单接口
            # order_result = self.exchange.create_order(**order_params)
            
            # 模拟下单成功
            order_result = {
                'order_id': f"order_{int(time.time())}",
                'status': 'filled',
                'filled_quantity': decision['quantity'],
                'avg_price': decision['price']
            }
            
            # 创建交易记录
            trade = {
                'trade_id': order_result['order_id'],
                'strategy_id': strategy_id,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'action': decision['action'],
                'side': order_params['side'],
                'price': order_result['avg_price'],
                'quantity': order_result['filled_quantity'],
                'value': order_result['avg_price'] * order_result['filled_quantity'],
                'commission': 0.0,  # 实际需要计算
                'pnl': 0.0,  # 平仓时计算
                'reason': decision['reason'],
                'stop_loss': decision.get('stop_loss'),
                'take_profit': decision.get('take_profit'),
                'is_backtest': False,
                'order_result': order_result
            }
            
            logger.info(f"实盘订单执行成功: {trade}")
            return trade
            
        except Exception as e:
            logger.error(f"实盘下单失败: {e}")
            return None
    
    def _trading_loop(self):
        """
        交易主循环（实盘模式）
        """
        logger.info("启动交易循环")
        
        while self.is_running:
            try:
                # 获取最新市场数据
                for strategy_id, strategy_info in self.active_strategies.items():
                    symbol = strategy_info['symbol']
                    
                    # 这里需要实现实时数据获取
                    # 暂时使用模拟数据
                    current_time = datetime.now()
                    
                    # 模拟市场数据
                    mock_bar = {
                        'timestamp': current_time,
                        'open': 50000,
                        'high': 50500,
                        'low': 49500,
                        'close': 50200,
                        'volume': 1000
                    }
                    
                    # 策略处理
                    strategy = strategy_info['strategy']
                    result = strategy.on_bar(mock_bar)
                    
                    # 执行交易决策
                    if result['decision']['action'] != 'hold':
                        trade = self._execute_trade(
                            strategy_id=strategy_id,
                            symbol=symbol,
                            decision=result['decision'],
                            bar=mock_bar,
                            is_backtest=False
                        )
                
                # 等待下一次循环
                time.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"交易循环错误: {e}")
                time.sleep(10)
    
    def _close_all_positions(self, strategy_id: str):
        """
        平掉所有仓位
        
        Args:
            strategy_id: 策略ID
        """
        logger.info(f"平掉策略 '{strategy_id}' 的所有仓位")
        # 这里需要实现实际的平仓逻辑
    
    def _save_strategy_state(self, strategy_id: str):
        """
        保存策略状态
        
        Args:
            strategy_id: 策略ID
        """
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]['instance']
            state = strategy.get_status()
            
            state_file = f"strategies/{strategy_id}_state.json"
            with open(state_file, 'w') as f:
                import json
                json.dump(state, f, indent=2, default=str)
            
            logger.info(f"策略 '{strategy_id}' 状态已保存")
    
    def _save_backtest_results(self, results: Dict[str, Any]):
        """
        保存回测结果
        
        Args:
            results: 回测结果
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_dir = f"results/{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # 保存总体结果
        results_file = os.path.join(results_dir, 'overall_results.json')
        with open(results_file, 'w') as f:
            import json
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"回测结果已保存到: {results_dir}")
    
    def _calculate_overall_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算总体性能指标
        
        Args:
            results: 各策略结果
            
        Returns:
            总体指标
        """
        if not results.get('strategies'):
            return {}
        
        total_initial_capital = 0
        total_final_equity = 0
        all_trades = []
        
        for strategy_id, strategy_results in results['strategies'].items():
            metrics = strategy_results.get('metrics', {})
            total_initial_capital += metrics.get('initial_capital', 0)
            total_final_equity += metrics.get('final_equity', 0)
            
            if 'trades' in strategy_results:
                all_trades.extend(strategy_results['trades'])
        
        if total_initial_capital == 0:
            return {}
        
        total_return = (total_final_equity - total_initial_capital) / total_initial_capital
        
        overall_metrics = {
            'total_initial_capital': total_initial_capital,
            'total_final_equity': total_final_equity,
            'total_return': total_return,
            'total_trades': len(all_trades),
            'strategy_count': len(results['strategies'])
        }
        
        return overall_metrics
    
    def _generate_sample_data(self, symbol: str, days: int) -> pd.DataFrame:
        """
        生成模拟数据
        
        Args:
            symbol: 交易对
            days: 天数
            
        Returns:
            模拟数据
        """
        import numpy as np
        from datetime import datetime, timedelta
        
        # 生成时间序列
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='1h')
        
        # 基础价格
        if 'BTC' in symbol:
            start_price = 50000
        elif 'ETH' in symbol:
            start_price = 3000
        else:
            start_price = 100
        
        np.random.seed(42)
        
        # 随机游走
        returns = np.random.normal(0.0005, 0.01, len(dates))
        price = start_price * np.exp(np.cumsum(returns))
        
        # 生成OHLCV数据
        df = pd.DataFrame(index=dates)
        df['close'] = price
        df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
        df['open'].iloc[0] = start_price
        
        # 高低价
        price_range = df['close'] * 0.02
        df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.5, len(dates)) * price_range
        df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.5, len(dates)) * price_range
        
        # 成交量
        df['volume'] = 1000 * (1 + np.abs(returns) * 10) * np.random.uniform(0.8, 1.2, len(dates))
        
        return df.dropna()
    
    def _save_engine_state(self):
        """保存引擎状态"""
        state = {
            'mode': self.mode,
            'is_running': self.is_running,
            'start_time': self.start_time,
            'active_strategies': list(self.active_strategies.keys()),
            'total_orders': len(self.orders)
        }
        
        state_file = 'engine_state.json'
        with open(state_file, 'w') as f:
            import json
            json.dump(state, f, indent=2, default=str)
        
        logger.info("引擎状态已保存")
