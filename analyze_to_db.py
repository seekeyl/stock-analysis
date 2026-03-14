#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
import load_env
import os
"""
分析股票并写入数据库
从 stock_history 读取数据，计算技术指标，写入 stock_daily
"""

import akshare as ak
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import numpy as np
import json

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_z_score(prices, window):
    """计算Z-Score"""
    if len(prices) < window:
        return None
    recent = prices[-window:]
    mean = np.mean(recent)
    std = np.std(recent)
    if std == 0:
        return None
    return (prices[-1] - mean) / std

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD"""
    if len(prices) < slow:
        return None, None, None
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2
    return '多头' if dif.iloc[-1] > dea.iloc[-1] else '空头', dif.iloc[-1], dea.iloc[-1]

def calculate_rsi(prices, period=14):
    """计算RSI"""
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_ma(prices):
    """计算均线信号"""
    if len(prices) < 60:
        return '数据不足'
    ma5 = np.mean(prices[-5:])
    ma10 = np.mean(prices[-10:])
    ma20 = np.mean(prices[-20:])
    ma60 = np.mean(prices[-60:])
    if ma5 > ma10 > ma20 > ma60:
        return '多头'
    elif ma5 < ma10 < ma20 < ma60:
        return '空头'
    else:
        return '震荡'

def analyze_stock(code, conn):
    """分析单只股票"""
    cursor = conn.cursor()
    
    # 从数据库读取120天历史
    start_date = (datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT trade_date, open, high, low, close, volume, turnover_rate
        FROM stock_history 
        WHERE code = %s AND trade_date >= %s AND trade_date <= %s
        ORDER BY trade_date
    ''', (code, start_date, end_date))
    
    rows = cursor.fetchall()
    if not rows or len(rows) < 30:
        cursor.close()
        return False
    
    # 转换为DataFrame
    df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'turnover_rate'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    if len(df) < 60:
        cursor.close()
        return False
    
    prices = df['close'].values
    
    # 计算技术指标
    latest_price = float(prices[-1])
    change_pct = float((prices[-1] - prices[-2]) / prices[-2] * 100) if len(prices) >= 2 else 0
    turnover_rate = float(df['turnover_rate'].iloc[-1]) if pd.notna(df['turnover_rate'].iloc[-1]) else 0
    
    zscore_10d = get_z_score(prices, 10)
    zscore_30d = get_z_score(prices, 30)
    zscore_60d = get_z_score(prices, 60)
    
    macd_signal, macd_dif, macd_dea = calculate_macd(prices)
    rsi_14 = calculate_rsi(prices)
    ma_signal = calculate_ma(prices)
    
    # 获取股票名称和市场
    cursor.execute('SELECT name, market FROM stock_list WHERE code = %s', (code,))
    row = cursor.fetchone()
    if row:
        name, market = row
    else:
        name, market = code, 'SH' if code.startswith('6') else 'SZ'
    
    # 写入数据库
    try:
        sql = '''
        INSERT INTO stock_daily (
            code, name, market, latest_price, change_pct, turnover_rate,
            zscore_10d, zscore_30d, zscore_60d,
            macd_signal, macd_dif, macd_dea, rsi_14, ma_signal,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE 
            name=VALUES(name), market=VALUES(market), latest_price=VALUES(latest_price),
            change_pct=VALUES(change_pct), turnover_rate=VALUES(turnover_rate),
            zscore_10d=VALUES(zscore_10d), zscore_30d=VALUES(zscore_30d), zscore_60d=VALUES(zscore_60d),
            macd_signal=VALUES(macd_signal), macd_dif=VALUES(macd_dif), macd_dea=VALUES(macd_dea),
            rsi_14=VALUES(rsi_14), ma_signal=VALUES(ma_signal),
            updated_at=NOW()
        '''
        cursor.execute(sql, (
            code, name, market, latest_price, change_pct, turnover_rate,
            zscore_10d, zscore_30d, zscore_60d,
            macd_signal, macd_dif, macd_dea, rsi_14, ma_signal
        ))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        log(f"  ❌ {code}: {str(e)[:50]}")
        cursor.close()
        return False

def main():
    log("=" * 60)
    log("  股票分析（从数据库读取）")
    log("=" * 60)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取所有股票
    cursor.execute("SELECT code FROM stock_list")
    all_stocks = [row[0] for row in cursor.fetchall()]
    
    # 获取已分析的股票
    cursor.execute("SELECT code FROM stock_daily")
    analyzed = set([row[0] for row in cursor.fetchall()])
    
    # 筛选未分析或需要更新的
    to_analyze = [s for s in all_stocks if s not in analyzed]
    
    log(f"待分析: {len(to_analyze)} / {len(all_stocks)} 只")
    
    count = 0
    for code in to_analyze:
        if analyze_stock(code, conn):
            count += 1
            if count % 100 == 0:
                log(f"=== 进度: {count}/{len(to_analyze)} ===")
    
    cursor.close()
    conn.close()
    log(f"\n✅ 完成! 分析了 {count} 只股票")

if __name__ == "__main__":
    main()
