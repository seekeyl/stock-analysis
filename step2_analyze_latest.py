#!/usr/bin/env python3
"""
步骤2: 逐个分析股票
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
import time

DATA_DIR = '/home/seekey/dev/workspace/openclaw/stock/tmp'
STOCK_LIST_FILE = f'{DATA_DIR}/stock_info.csv'
STATUS_FILE = '/home/seekey/dev/workspace/openclaw/stock/tmp/analyze_status.csv'
SLEEP_SECONDS = 0

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def format_date(val):
    if val is None: return 'N/A'
    s = str(val)
    return s[:10] if len(s) >= 10 else s

def get_one_year_ago():
    return (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

def get_one_week_ago():
    return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

def is_doji(row, threshold=0.03):
    try:
        body = abs(row['open'] - row['close'])
        range_val = row['high'] - row['low']
        if range_val <= 0 or body <= 0: return False
        return (body / range_val) < threshold
    except: return False

def is_hammer(row):
    try:
        body = abs(row['open'] - row['close'])
        range_val = row['high'] - row['low']
        if range_val <= 0: return False
        lower = row['open'] - row['low'] if row['close'] >= row['open'] else row['close'] - row['low']
        return lower >= body * 2
    except: return False

def is_shooting_star(row):
    try:
        body = abs(row['open'] - row['close'])
        range_val = row['high'] - row['low']
        if range_val <= 0: return False
        upper = row['high'] - row['close'] if row['close'] >= row['open'] else row['high'] - row['open']
        return upper >= body * 2
    except: return False

def analyze_period(df_period, period_name):
    if df_period is None or df_period.empty: return {"时间段": period_name, "数据": "无数据"}
    results = {"时间段": period_name}
    if 'close' in df_period.columns and len(df_period) > 1:
        first, last = df_period.iloc[0], df_period.iloc[-1]
        change = (last['close'] - first['close']) / first['close'] * 100 if first['close'] > 0 else 0
        results['涨跌幅'] = f"{change:.2f}%"
        results['最高价'] = f"{df_period['high'].max():.2f}"
        results['最低价'] = f"{df_period['low'].min():.2f}"
        results['交易日数'] = len(df_period)
    pattern_list = []
    doji = sum(df_period.apply(is_doji, axis=1))
    if doji > 0: pattern_list.append(f"十字星{doji}次")
    hammer = sum(df_period.apply(is_hammer, axis=1))
    if hammer > 0: pattern_list.append(f"锤子线{hammer}次")
    star = sum(df_period.apply(is_shooting_star, axis=1))
    if star > 0: pattern_list.append(f"流星线{star}次")
    if 'pct_chg' in df_period.columns:
        df_copy = df_period.copy()
        df_copy['pct_chg_calc'] = (df_copy['close'] - df_copy['close'].shift(1)) / df_copy['close'].shift(1) * 100
        up = len(df_copy[df_copy['pct_chg_calc'] >= 9.9])
        down = len(df_copy[df_copy['pct_chg_calc'] <= -9.9])
        if up > 0: pattern_list.append(f"涨停{up}次")
        if down > 0: pattern_list.append(f"跌停{down}次")
    if pattern_list: results['K线形态'] = ", ".join(pattern_list)
    if 'volume' in df_period.columns:
        avg_vol = df_period['volume'].mean()
        results['日均成交量'] = f"{avg_vol:,.0f}"
        high_vol = df_period[df_period['volume'] > avg_vol * 2]
        if len(high_vol) > 0: results['放量交易日'] = f"{len(high_vol)}次"
    return results

def get_stock_news(code, name):
    news_list = []
    try:
        news = ak.stock_news_em(symbol=code)
        if news is not None and not news.empty:
            cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            for _, row in news.iterrows():
                news_date = str(row.get('发布时间', ''))[:10]
                title = row.get('新闻标题', '')
                if title and (news_date >= cutoff or news_date == 'N/A' or news_date == ''):
                    news_list.append({'date': news_date, 'title': title[:80]})
            news_list.sort(key=lambda x: x['date'], reverse=True)
    except: pass
    return news_list[:10]

_fund_flow_cache = None
def get_fund_flow():
    global _fund_flow_cache
    if _fund_flow_cache is not None: return _fund_flow_cache
    try:
        df = ak.stock_fund_flow_individual()
        if df is not None and not df.empty:
            _fund_flow_cache = df
            return df
    except: pass
    return None

_pe_cache = None
def get_pe_data():
    global _pe_cache
    if _pe_cache is not None: return _pe_cache
    try:
        df = ak.stock_market_pe_lg()
        if df is not None and not df.empty:
            _pe_cache = df
            return df
    except: pass
    return None

# 大盘走势数据缓存
_market_cache = None
def get_market_data():
    """获取大盘PE/PB历史走势"""
    global _market_cache
    if _market_cache is not None: return _market_cache
    
    _market_cache = {}
    
    # 市场PE历史
    try:
        df = ak.stock_a_ttm_lyr()
        if df is not None and not df.empty:
            _market_cache['pe'] = df
    except: pass
    
    # 市场PB历史
    try:
        df = ak.stock_a_all_pb()
        if df is not None and not df.empty:
            _market_cache['pb'] = df
    except: pass
    
    return _market_cache

def get_market_summary():
    """生成大盘走势简评"""
    data = get_market_data()
    if not data: return None
    
    summary = []
    
    # PE走势
    if 'pe' in data and not data['pe'].empty:
        df = data['pe'].tail(30).copy()
        if 'middlePETTM' in df.columns:
            latest_pe = df['middlePETTM'].iloc[-1]
            pe_30d_ago = df['middlePETTM'].iloc[0] if len(df) > 0 else latest_pe
            pe_change = (latest_pe - pe_30d_ago) / pe_30d_ago * 100 if pe_30d_ago else 0
            
            # PE估值判断
            if latest_pe < 15:
                pe_label = "低估"
            elif latest_pe < 25:
                pe_label = "合理"
            else:
                pe_label = "高估"
            
            summary.append(f"市场PE: {latest_pe:.1f} ({pe_label}, 30日{pe_change:+.1f}%)")
    
    # PB走势
    if 'pb' in data and not data['pb'].empty:
        df = data['pb'].tail(30).copy()
        if 'middlePB' in df.columns:
            latest_pb = df['middlePB'].iloc[-1]
            
            if latest_pb < 1.5:
                pb_label = "低估"
            elif latest_pb < 3:
                pb_label = "合理"
            else:
                pb_label = "高估"
            
            summary.append(f"市场PB: {latest_pb:.2f} ({pb_label})")
    
    return " | ".join(summary) if summary else None

import numpy as np

def get_z_score(prices, min_periods=20):
    if len(prices) < min_periods: return None
    mean = np.mean(prices)
    std = np.std(prices)
    if std == 0: return 0
    return (prices[-1] - mean) / std

def calculate_ema(prices, period):
    """计算指数移动平均(EMA)"""
    return pd.Series(prices).ewm(span=period, adjust=False).mean().values

def calculate_ma(prices, period):
    """计算简单移动平均(MA)"""
    if len(prices) < period: return None
    return np.mean(prices[-period:])

def calculate_macd(prices):
    """
    计算MACD指标
    返回: (dif, dea, macd_histogram, signal)
    signal: 金叉/死叉/None
    """
    if len(prices) < 34: return None, None, None, None
    
    try:
        # 计算EMA
        ema12 = calculate_ema(prices, 12)
        ema26 = calculate_ema(prices, 26)
        
        # DIF = EMA12 - EMA26
        dif = ema12 - ema26
        
        # DEA = EMA(DIF, 9)
        dea = calculate_ema(dif, 9)
        
        # MACD柱 = (DIF - DEA) * 2
        macd_histogram = (dif - dea) * 2
        
        # 获取最近几天的DIF和DEA来判断金叉死叉
        if len(dif) >= 2 and len(dea) >= 2:
            # 昨天DIF <= DEA (死叉), 今天DIF > DEA (金叉)
            if dif[-1] > dea[-1] and dif[-2] <= dea[-2]:
                signal = "金叉"
            elif dif[-1] < dea[-1] and dif[-2] >= dea[-2]:
                signal = "死叉"
            elif dif[-1] > dea[-1]:
                signal = "多头"  # DIF在DEA上方
            elif dif[-1] < dea[-1]:
                signal = "空头"  # DIF在DEA下方
            else:
                signal = None
        else:
            signal = None
            
        return dif[-1], dea[-1], macd_histogram[-1], signal
    except:
        return None, None, None, None

def calculate_rsi(prices, period=14):
    """
    计算RSI指标
    period: RSI周期，默认14
    返回: RSI值 (0-100)
    """
    if len(prices) < period + 1: return None
    
    try:
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 使用EMA计算平均涨幅和跌幅
        avg_gain = pd.Series(gains).ewm(span=period, adjust=False).mean().values[-1]
        avg_loss = pd.Series(losses).ewm(span=period, adjust=False).mean().values[-1]
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return None

def calculate_ma_system(prices):
    """
    计算均线系统 (MA5, MA10, MA20, MA60)
    返回: (ma5, ma10, ma20, ma60, signal)
    signal: 多头排列/空头排列/缠绕
    """
    if len(prices) < 60: return None, None, None, None, None
    
    try:
        ma5 = calculate_ma(prices, 5)
        ma10 = calculate_ma(prices, 10)
        ma20 = calculate_ma(prices, 20)
        ma60 = calculate_ma(prices, 60)
        
        if ma5 is None: return ma5, ma10, ma20, ma60, None
        
        # 判断均线排列
        if ma5 > ma10 > ma20 > ma60:
            signal = "多头排列"
        elif ma5 < ma10 < ma20 < ma60:
            signal = "空头排列"
        else:
            signal = "缠绕"
            
        return ma5, ma10, ma20, ma60, signal
    except:
        return None, None, None, None, None

def generate_summary(code, name, market, daily_df, news_list):
    analysis = []
    if daily_df is not None and not daily_df.empty:
        # 确保有date列
        if 'date' not in daily_df.columns:
            return ["无日期数据"]
        
        try:
            daily_df = daily_df.copy()
            daily_df['date'] = pd.to_datetime(daily_df['date'])
        except:
            return ["日期格式错误"]
        # 1年涨跌
        one_year_ago = get_one_year_ago()
        df_year = daily_df[pd.to_datetime(daily_df['date']) >= one_year_ago]
        if len(df_year) > 1:
            change = (df_year.iloc[-1]['close'] - df_year.iloc[0]['close']) / df_year.iloc[0]['close'] * 100
            if change > 20: analysis.append(f"近1年涨幅{change:.1f}%")
            elif change < -30: analysis.append(f"近1年跌幅{abs(change):.1f}%超跌")
        
        # 1月涨跌
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        df_month = daily_df[pd.to_datetime(daily_df['date']) >= one_month_ago]
        if len(df_month) > 1:
            change = (df_month.iloc[-1]['close'] - df_month.iloc[0]['close']) / df_month.iloc[0]['close'] * 100
            if change >= 10: analysis.append(f"近1月涨幅{change:.1f}%")
            elif change <= -10: analysis.append(f"近1月跌幅{abs(change):.1f}%")
        
        # 本周涨跌
        one_week = get_one_week_ago()
        df_week = daily_df[pd.to_datetime(daily_df['date']) >= one_week]
        if len(df_week) > 1:
            change = (df_week.iloc[-1]['close'] - df_week.iloc[0]['close']) / df_week.iloc[0]['close'] * 100
            if change >= 5: analysis.append(f"本周大涨{change:.1f}%")
            elif change <= -5: analysis.append(f"本周大跌{abs(change):.1f}%")
        # 成交量
        if 'volume' in daily_df.columns:
            recent = daily_df['volume'].tail(5).mean()
            avg = daily_df['volume'].mean()
            if recent >= avg * 2.5: analysis.append("成交量显著放大")
            elif recent <= avg * 0.4: analysis.append("成交量明显萎缩")
        # 均线系统
        if len(daily_df) >= 60:
            prices = daily_df['close'].values
            ma5, ma10, ma20, ma60, ma_signal = calculate_ma_system(prices)
            if ma_signal:
                analysis.append(f"均线{ma_signal}")
            # 均线金叉信号
            ma5_curr = calculate_ma(prices, 5)
            ma10_curr = calculate_ma(prices, 10)
            ma20_curr = calculate_ma(prices, 20)
            if ma5_curr and ma10_curr and ma20_curr and len(prices) >= 22:
                ma5_prev = calculate_ma(prices[:-1], 5)
                ma10_prev = calculate_ma(prices[:-1], 10)
                if ma5_curr > ma10_curr and ma5_prev <= ma10_prev:
                    analysis.append("均线金叉(5日上穿10日)")
        
        # MACD指标
        if len(daily_df) >= 34:
            prices = daily_df['close'].values
            dif, dea, macd_hist, macd_signal = calculate_macd(prices)
            if macd_signal:
                analysis.append(f"MACD{macd_signal}")
        
        # RSI指标
        if len(daily_df) >= 30:
            prices = daily_df['close'].values
            rsi = calculate_rsi(prices, 14)
            if rsi:
                if rsi >= 70:
                    analysis.append(f"RSI(14)={rsi:.0f}超买")
                elif rsi <= 30:
                    analysis.append(f"RSI(14)={rsi:.0f}超卖")
                
        # Z-Score
        z10 = get_z_score(daily_df['close'].tail(10).values, 10) if len(daily_df) >= 10 else None
        z30 = get_z_score(daily_df['close'].tail(30).values) if len(daily_df) >= 30 else None
        z60 = get_z_score(daily_df['close'].tail(60).values) if len(daily_df) >= 60 else None
        if z10 and z10 > 2: analysis.append(f"Z-Score(10日)={z10:.1f}严重高估")
        elif z10 and z10 < -2: analysis.append(f"Z-Score(10日)={z10:.1f}严重低估")
        if z30 and z30 > 2: analysis.append(f"Z-Score(30日)={z30:.1f}严重高估")
        elif z30 and z30 < -2: analysis.append(f"Z-Score(30日)={z30:.1f}严重低估")
        if z60 and z60 > 2: analysis.append(f"Z-Score(60日)={z60:.1f}严重高估")
        elif z60 and z60 < -2: analysis.append(f"Z-Score(60日)={z60:.1f}严重低估")
    if news_list:
        analysis.append(f"有{len(news_list)}条新闻")
    return analysis

def generate_report(code, name, market, daily_df, news_list):
    period_results = []
    # 确保daily_df有有效的date列
    if daily_df is not None and not daily_df.empty:
        # 检查是否有date列
        if 'date' not in daily_df.columns:
            # 尝试常见的中文日期列名
            for col in ['日期', '交易日期', 'time', 'datetime']:
                if col in daily_df.columns:
                    daily_df = daily_df.rename(columns={col: 'date'})
                    break
        
        if 'date' not in daily_df.columns:
            period_results.append({"时间段": "2年内", "数据": "无日期数据"})
            period_results.append({"时间段": "1年以内", "数据": "无日期数据"})
            period_results.append({"时间段": "1月以内", "数据": "无日期数据"})
            period_results.append({"时间段": "本周", "数据": "无日期数据"})
        else:
            try:
                daily_df = daily_df.copy()
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                period_results.append(analyze_period(daily_df, "2年内"))
                one_year = get_one_year_ago()
                df_year = daily_df[pd.to_datetime(daily_df['date']) >= one_year]
                period_results.append(analyze_period(df_year, "1年以内"))
                one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                df_month = daily_df[pd.to_datetime(daily_df['date']) >= one_month_ago]
                period_results.append(analyze_period(df_month, "1月以内"))
                one_week = get_one_week_ago()
                df_week = daily_df[pd.to_datetime(daily_df['date']) >= one_week]
                period_results.append(analyze_period(df_week, "本周"))
            except Exception as e:
                period_results.append({"时间段": "2年内", "数据": f"处理错误: {str(e)[:20]}"})
                period_results.append({"时间段": "1年以内", "数据": "处理错误"})
                period_results.append({"时间段": "1月以内", "数据": "处理错误"})
                period_results.append({"时间段": "本周", "数据": "处理错误"})
    else:
        period_results.append({"时间段": "2年内", "数据": "无数据"})
        period_results.append({"时间段": "1年以内", "数据": "无数据"})
        period_results.append({"时间段": "1月以内", "数据": "无数据"})
        period_results.append({"时间段": "本周", "数据": "无数据"})
    
    summary = generate_summary(code, name, market, daily_df, news_list)
    
    # 获取大盘走势
    market_info = get_market_summary()
    
    report = f"""# {name} ({code}) 分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**市场**: {market}  
**代码**: {code}
{f"**大盘**: {market_info}" if market_info else ""}

---

## 📊 分时段分析

| 指标 | 2年内 | 1年以内 | 1月以内 | 本周 |
|------|----------|---------|------|
"""
    keys = set()
    for p in period_results: keys.update(p.keys())
    keys.discard('时间段')
    for key in sorted(keys):
        vals = [p.get(key, '-') for p in period_results]
        report += f"| {key} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |\n"
    
    # K线表格 - 处理中英文列名
    close_col = '收盘' if daily_df is not None and '收盘' in daily_df.columns else 'close'
    open_col = '开盘' if daily_df is not None and '开盘' in daily_df.columns else 'open'
    high_col = '最高' if daily_df is not None and '最高' in daily_df.columns else 'high'
    low_col = '最低' if daily_df is not None and '最低' in daily_df.columns else 'low'
    vol_col = '成交量' if daily_df is not None and '成交量' in daily_df.columns else 'volume'
    amt_col = '成交额' if daily_df is not None and '成交额' in daily_df.columns else 'amount'
    amp_col = '振幅' if daily_df is not None and '振幅' in daily_df.columns else 'amplitude'
    pct_col = '涨跌幅' if daily_df is not None and '涨跌幅' in daily_df.columns else 'pct_chg'
    change_col = '涨跌额' if daily_df is not None and '涨跌额' in daily_df.columns else 'change'
    turnover_col = '换手率' if daily_df is not None and '换手率' in daily_df.columns else 'turnover'
    date_col = '日期' if daily_df is not None and '日期' in daily_df.columns else 'date'
    
    if daily_df is not None and not daily_df.empty and close_col in daily_df.columns:
        # 构建表头
        header = "| 日期 | 开盘 | 收盘 | 最高 | 最低"
        if amt_col in daily_df.columns: header += " | 成交额"
        if amp_col in daily_df.columns: header += " | 振幅"
        if pct_col in daily_df.columns: header += " | 涨跌幅"
        if change_col in daily_df.columns: header += " | 涨跌额"
        if turnover_col in daily_df.columns: header += " | 换手率"
        header += " |\n"
        
        # 分隔行
        col_count = header.count("|") - 1
        separator = "|" + "|".join(["---" for _ in range(col_count)]) + "|\n"
        
        report += """
### 近期K线 (最近10日)

"""
        report += header + separator
        
        df_recent = daily_df.tail(10).copy()
        if pct_col in df_recent.columns:
            df_recent['pct_calc'] = (df_recent[close_col] - df_recent[close_col].shift(1)) / df_recent[close_col].shift(1) * 100
        
        for _, row in df_recent.iterrows():
            line = f"| {format_date(row.get(date_col))} | {row[open_col]:.2f} | {row[close_col]:.2f} | {row[high_col]:.2f} | {row[low_col]:.2f}"
            
            if amt_col in row.index:
                amt = row[amt_col]
                if pd.notna(amt):
                    if amt >= 1e8: line += f" | {amt/1e8:.2f}亿"
                    elif amt >= 1e4: line += f" | {amt/1e4:.0f}万"
                    else: line += f" | {amt:.0f}"
                else: line += " | -"
            
            if amp_col in row.index:
                amp = row[amp_col]
                line += f" | {amp:.2f}%" if pd.notna(amp) else " | -"
            
            pct = row.get('pct_calc', 0)
            if pd.isna(pct): pct = 0
            line += f" | {pct:+.2f}%"
            
            if change_col in row.index:
                chg = row[change_col]
                line += f" | {chg:+.2f}" if pd.notna(chg) else " | -"
            
            if turnover_col in row.index:
                tr = row[turnover_col]
                line += f" | {tr:.2f}%" if pd.notna(tr) else " | -"
            
            line += " |\n"
            report += line
    
    # PE
    pe_df = get_pe_data()
    pe_val = "N/A"
    if pe_df is not None and not pe_df.empty:
        pe_val = pe_df.iloc[-1].get('平均市盈率', 'N/A')
    report += f"""
---

## 📈 估值指标

| 指标 | 数值 |
|------|------|
| 市场PE | {pe_val} |
"""
    
    # Z-Score
    if daily_df is not None and len(daily_df) >= 20 and 'close' in daily_df.columns:
        z10 = get_z_score(daily_df['close'].tail(10).values, 10) if len(daily_df) >= 10 else None
        z30 = get_z_score(daily_df['close'].tail(30).values, 30) if len(daily_df) >= 30 else None
        z60 = get_z_score(daily_df['close'].tail(60).values, 60) if len(daily_df) >= 60 else None
        z120 = get_z_score(daily_df['close'].tail(120).values, 120) if len(daily_df) >= 120 else None
        
        def get_z_label(z):
            if z is None: return '-'
            if z < -2: return '严重低估'
            elif z < -1: return '低估'
            elif z < 1: return '正常'
            elif z < 2: return '高估'
            else: return '严重高估'
        
        if z10:
            report += f"| Z-Score(10日) | {z10:.2f} ({get_z_label(z10)}) |\n"
        if z30:
            report += f"| Z-Score(30日) | {z30:.2f} ({get_z_label(z30)}) |\n"
        if z60:
            report += f"| Z-Score(60日) | {z60:.2f} ({get_z_label(z60)}) |\n"
        if z120:
            report += f"| Z-Score(120日) | {z120:.2f} ({get_z_label(z120)}) |\n"
    
    # 技术指标 - MACD, RSI, 均线
    if daily_df is not None and len(daily_df) >= 34 and 'close' in daily_df.columns:
        prices = daily_df['close'].values
        
        # MACD
        dif, dea, macd_hist, macd_signal = calculate_macd(prices)
        if macd_signal:
            report += f"| MACD | {macd_signal} (DIF:{dif:.2f} DEA:{dea:.2f}) |\n"
        
        # RSI
        rsi = calculate_rsi(prices, 14)
        if rsi:
            rsi_label = "超买" if rsi >= 70 else "超卖" if rsi <= 30 else "正常"
            report += f"| RSI(14) | {rsi:.1f} ({rsi_label}) |\n"
        
        # 均线系统
        if len(prices) >= 60:
            ma5, ma10, ma20, ma60, ma_signal = calculate_ma_system(prices)
            if ma_signal:
                report += f"| 均线系统 | {ma_signal} |\n"
    
    # 资金流向
    fund_flow = get_fund_flow()
    if fund_flow is not None and not fund_flow.empty:
        code_clean = code.lstrip('0')
        stock = fund_flow[fund_flow['股票代码'].astype(str).str.lstrip('0') == code_clean]
        if not stock.empty:
            row = stock.iloc[0]
            report += f"""
---

## 💰 资金流向

| 指标 | 数值 |
|------|------|
| 最新价 | {row.get('最新价', '-')} |
| 涨跌幅 | {row.get('涨跌幅', '-')} |
| 成交额 | {row.get('成交额', '-')} |
| 净额 | {row.get('净额', '-')} |
"""
    
    # 新闻
    if news_list:
        report += "\n---\n\n## 📰 近期新闻\n\n"
        for news in news_list[:5]:
            d = news['date'] if news['date'] != 'N/A' else '近日'
            report += f"- **{d}**: {news['title']}\n"
    else:
        report += "\n---\n\n## 📰 近期新闻\n\n暂无新闻\n"
    
    # 总结
    report += f"""
---

## 💡 AI分析总结

"""
    if summary:
        for s in summary:
            report += f"- {s}\n"
    else:
        report += "无明显信号\n"
    
    report += """
---

**免责声明**: 本分析仅供参考，不构成投资建议。
"""
    return report

def analyze_one_stock(code, name, market):
    log(f"分析 {code} {name}...")
    
    # 判断市场：6开头=上海，0/3开头深圳，8/4/3开头北交所
    # 北交所用stock_zh_a_hist接口，其他用stock_zh_a_daily
    is_bj = code.startswith('8') or code.startswith('4') or (code.startswith('3') and len(code) == 6 and int(code) >= 300000)
    symbol = f"BJ{code}" if is_bj else f"{market.lower()}{code}"
    
    daily_df = None
    try:
        if is_bj:
            # 北交所用hist接口
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y%m%d')
            # 只获取120天数据（MACD需要34天，RSI需要30天，均线需要60天）
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
            daily_df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust='')
        else:
            # 用hist接口限制120天数据（MACD需要34天，RSI需要30天，均线需要60天）
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
            daily_df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust='')
        
        # 如果返回空数据，尝试备用接口
        if daily_df is None or daily_df.empty:
            # 尝试用daily接口
            symbol_daily = f"{market.lower()}{code}"
            daily_df = ak.stock_zh_a_daily(symbol=symbol_daily, adjust="qfq")
            if daily_df is not None and not daily_df.empty:
                daily_df = daily_df.tail(120)  # 只取最近120天
        
        if daily_df is not None and not daily_df.empty:
            # 检查是否有date列，如果没有尝试使用其他日期列
            if 'date' not in daily_df.columns:
                # 尝试常见的中文日期列名
                for col in ['日期', '交易日期', 'time', 'datetime']:
                    if col in daily_df.columns:
                        daily_df = daily_df.rename(columns={col: 'date'})
                        break
            
            # 重命名常见的中文字段名
            rename_map = {
                '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
                '成交量': 'volume', '成交额': 'amount', '振幅': 'amplitude',
                '涨跌幅': 'pct_chg', '涨跌额': 'change', '换手率': 'turnover',
                '股票代码': 'symbol'
            }
            for cn, en in rename_map.items():
                if cn in daily_df.columns:
                    daily_df = daily_df.rename(columns={cn: en})
            
            # 如果还是没有date列，跳过这只股票
            if 'date' not in daily_df.columns:
                log(f"  ⚠️ 无日期数据，跳过")
                return False
            
            daily_df = daily_df.sort_values('date')
            daily_df['pct_chg'] = (daily_df['close'] - daily_df['close'].shift(1)) / daily_df['close'].shift(1) * 100
    except Exception as e:
        log(f"  K线失败: {str(e)[:50]}")
    
    # 跳过新闻获取以加快速度（如需新闻可取消注释）
    # news_list = get_stock_news(code, name)
    news_list = []
    report = generate_report(code, name, market, daily_df, news_list)
    
    safe_name = str(name).replace('/', '_').replace('*', 'ST')
    filepath = f"{DATA_DIR}/{code}_{safe_name}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    log(f"  ✅ 已保存: {code}_{safe_name}.md")
    return True

def main():
    print("=" * 60)
    print("  步骤2: 逐个分析股票")
    print("=" * 60)
    if not os.path.exists(STOCK_LIST_FILE):
        print(f"错误: 找不到 {STOCK_LIST_FILE}")
        return
    
    # 读取股票列表（全部股票）
    stock_df = pd.read_csv(STOCK_LIST_FILE, dtype={'code': str})
    
    # 读取分析状态
    if os.path.exists(STATUS_FILE):
        status_df = pd.read_csv(STATUS_FILE, dtype={'code': str})
        analyzed_codes = set(status_df[status_df['analyzed'] == '是']['code'].astype(str))
    else:
        analyzed_codes = set()
    
    # 筛选未分析的股票
    unan = stock_df[~stock_df['code'].astype(str).isin(analyzed_codes)]
    if len(unan) == 0:
        print("全部完成!")
        return
    
    print(f"\n待分析: {len(unan)} 只")
    
    count = 0
    for idx, row in unan.iterrows():
        code = str(row['code'])
        name = row['name']
        market = 'SH' if code.startswith('6') else 'SZ'
        
        if analyze_one_stock(code, name, market):
            # 更新状态文件
            new_row = pd.DataFrame([{'code': code, 'analyzed': '是', 'analyze_date': datetime.now().strftime('%Y-%m-%d')}])
            if os.path.exists(STATUS_FILE):
                status_df = pd.read_csv(STATUS_FILE, dtype={'code': str})
                # 如果已存在则更新，否则追加
                if code in status_df['code'].astype(str).values:
                    status_df.loc[status_df['code'].astype(str) == code, 'analyzed'] = '是'
                    status_df.loc[status_df['code'].astype(str) == code, 'analyze_date'] = datetime.now().strftime('%Y-%m-%d')
                else:
                    status_df = pd.concat([status_df, new_row], ignore_index=True)
            else:
                status_df = new_row
            status_df.to_csv(STATUS_FILE, index=False, encoding='utf-8-sig')
            
            count += 1
            if count % 10 == 0:
                total_done = len(analyzed_codes) + count
                log(f"=== PROGRESS: {total_done}/4586 ({total_done/4586*100:.1f}%) ===")
        
        log(f"  等待 {SLEEP_SECONDS} 秒...\n")
        time.sleep(SLEEP_SECONDS)
    
    print("\n✅ 全部完成!")

if __name__ == "__main__":
    main()
