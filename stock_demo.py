#!/usr/bin/env python3
"""
AkShare 股票数据 Demo (简化版)
安装: pip install akshare
运行: python3 stock_demo.py
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def demo_stock_list():
    """演示：获取股票列表"""
    print("\n📋 A股股票列表 (前20只)")
    print("-" * 50)
    df = ak.stock_info_sh_name_code()
    print(df.head(20).to_string(index=False))

def demo_history():
    """演示：获取历史K线"""
    print("\n📊 历史K线 (茅台最近20天)")
    print("-" * 50)
    try:
        df = ak.stock_zh_a_hist(symbol="600519", period="daily", 
                               start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
                               end_date=datetime.now().strftime("%Y%m%d"),
                               adjust="qfq")
        if not df.empty:
            print(df[['日期', '开盘', '收盘', '涨跌幅']].tail(20).to_string(index=False))
        else:
            print("无数据")
    except Exception as e:
        print(f"获取失败: {e}")

def demo_fund():
    """演示：获取基金数据"""
    print("\n💰 基金ETF列表 (前10只)")
    print("-" * 50)
    try:
        df = ak.fund_etf_spot_em()
        print(df[['代码', '名称', '最新价', '涨跌幅']].head(10).to_string(index=False))
    except Exception as e:
        print(f"获取失败: {e}")

def demo_index():
    """演示：获取指数行情"""
    print("\n📈 大盘指数")
    print("-" * 50)
    try:
        df = ak.stock_zh_index_spot()
        print(df[['代码', '名称', '最新价', '涨跌幅']].head(10).to_string(index=False))
    except Exception as e:
        print(f"获取失败: {e}")

def demo_realtime_simple():
    """演示：单只股票实时行情"""
    print("\n🔥 单只股票实时 (贵州茅台)")
    print("-" * 50)
    try:
        df = ak.stock_zh_a_daily(symbol="sh600519")
        if not df.empty:
            latest = df.iloc[-1]
            print(f"日期: {latest['date']}")
            print(f"开盘: {latest['open']}")
            print(f"收盘: {latest['close']}")
            print(f"最高: {latest['high']}")
            print(f"最低: {latest['low']}")
            print(f"成交量: {latest['volume']:,}")
    except Exception as e:
        print(f"获取失败: {e}")

def main():
    print("=" * 60)
    print("  AkShare 股票数据 Demo")
    print("  安装: pip install akshare")
    print("  运行: python3 stock_demo.py")
    print("=" * 60)
    
    print("\n选择功能:")
    print("  1. A股股票列表")
    print("  2. 历史K线")
    print("  3. 基金ETF")
    print("  4. 大盘指数")
    print("  5. 单只股票实时")
    print("  6. 全部运行")
    
    choice = input("\n请输入选项 (1-6): ").strip()
    
    if choice in ['1', '6']:
        demo_stock_list()
    if choice in ['2', '6']:
        demo_history()
    if choice in ['3', '6']:
        demo_fund()
    if choice in ['4', '6']:
        demo_index()
    if choice in ['5', '6']:
        demo_realtime_simple()
    
    print("\n✅ 完成!")

if __name__ == "__main__":
    main()
