#!/bin/bash
# 安装1小时级别CTA回测系统依赖

echo "安装1小时级别CTA回测系统依赖..."
echo "========================================"

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 安装基础依赖
echo "安装基础依赖..."
pip install --upgrade pip

# 安装数据处理库
echo "安装数据处理库..."
pip install pandas numpy

# 安装币安API库
echo "安装币安API库..."
pip install python-binance ccxt

# 安装可视化库
echo "安装可视化库..."
pip install matplotlib

# 安装其他工具库
echo "安装其他工具库..."
pip install scipy scikit-learn

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data_1h
mkdir -p results_1h
mkdir -p logs_1h
mkdir -p data_1h/cache

echo "========================================"
echo "依赖安装完成！"
echo ""
echo "使用方法:"
echo "1. 查看可用交易对: python run_1h_backtest.py --list-symbols"
echo "2. 运行单个回测: python run_1h_backtest.py --symbol BTCUSDT --days 90"
echo "3. 批量回测: python run_1h_backtest.py --batch BTCUSDT ETHUSDT BNBUSDT"
echo "4. 自定义参数: python run_1h_backtest.py --symbol ETHUSDT --days 180 --capital 5000"
echo ""
echo "配置文件: config_1h.json"
echo "数据目录: data_1h/"
echo "结果目录: results_1h/"