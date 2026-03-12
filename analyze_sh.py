#!/usr/bin/env python3
"""只分析上海股票"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
import time

DATA_DIR = '/home/seekey/dev/workspace/openclaw/stock/tmp'
STOCK_LIST_FILE = '/home/seekey/dev/workspace/openclaw/stock/tmp/stock_info.csv'
SH_STATUS_FILE = '/home/seekey/dev/workspace/openclaw/stock/tmp/sh_only_status.csv'
SLEEP_SECONDS = 3

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
        open_col = '开盘' if '开盘' in row else 'open'
        close_col = '收盘' if '收盘' in row else 'close'
        high_col = '最高' if '最高' in row else 'high'
        low_col = '最低' if '最低' in row else 'low'
        
        body = abs(row[open_col] - row[close_col])
        range_val = row[high_col] - row[low_col]
        if range_val <= 0 or body <= 0: return False
        return (body / range_val) < threshold
    except: return False

def is_hammer(row):
    try:
        open_col = '开盘' if '开盘' in row else 'open'
        close_col = '收盘' if '收盘' in row else 'close'
        high_col = '最高' if '最高' in row else 'high'
        low_col = '最低' if '最低' in row else 'low'
        
        body = abs(row[open_col] - row[close_col])
        range_val = row[high_col] - row[low_col]
        if range_val <= 0: return False
        lower = row[open_col] - row[low_col] if row[close_col] >= row[open_col] else row[close_col] - row[low_col]
        return lower >= body * 2
    except: return False

def is_shooting_star(row):
    try:
        open_col = '开盘' if '开盘' in row else 'open'
        close_col = '收盘' if '收盘' in row else 'close'
        high_col = '最高' if '最高' in row else 'high'
        low_col = '最低' if '最低' in row else 'low'
        
        body = abs(row[open_col] - row[close_col])
        range_val = row[high_col] - row[low_col]
        if range_val <= 0: return False
        upper = row[high_col] - row[close_col] if row[close_col] >= row[open_col] else row[high_col] - row[open_col]
        return upper >= body * 2
    except: return False

def analyze_period(df_period, period_name):
    if df_period is None or df_period.empty: 
        return {"时间段": period_name, "数据": "无数据"}
    
    # 处理中英文列名
    close_col = '收盘' if '收盘' in df_period.columns else 'close'
    high_col = '最高' if '最高' in df_period.columns else 'high'
    low_col = '最低' if '最低' in df_period.columns else 'low'
    open_col = '开盘' if '开盘' in df_period.columns else 'open'
    vol_col = '成交量' if '成交量' in df_period.columns else 'volume'
    
    results = {"时间段": period_name}
    if close_col in df_period.columns and len(df_period) > 1:
        first, last = df_period.iloc[0], df_period.iloc[-1]
        change = (last[close_col] - first[close_col]) / first[close_col] * 100 if first[close_col] > 0 else 0
        results['涨跌幅'] = f"{change:.2f}%"
        results['最高价'] = f"{df_period[high_col].max():.2f}"
        results['最低价'] = f"{df_period[low_col].min():.2f}"
        results['交易日数'] = len(df_period)
    
    pattern_list = []
    try:
        doji = sum(df_period.apply(is_doji, axis=1))
        if doji > 0: pattern_list.append(f"十字星{doji}次")
    except: pass
    try:
        hammer = sum(df_period.apply(is_hammer, axis=1))
        if hammer > 0: pattern_list.append(f"锤子线{hammer}次")
    except: pass
    try:
        star = sum(df_period.apply(is_shooting_star, axis=1))
        if star > 0: pattern_list.append(f"流星线{star}次")
    except: pass
    
    if 'pct_chg' in df_period.columns:
        df_copy = df_period.copy()
        df_copy['pct_chg_calc'] = (df_copy[close_col] - df_copy[close_col].shift(1)) / df_copy[close_col].shift(1) * 100
        try:
            up = len(df_copy[df_copy['pct_chg_calc'] >= 9.9])
            down = len(df_copy[df_copy['pct_chg_calc'] <= -9.9])
            if up > 0: pattern_list.append(f"涨停{up}次")
            if down > 0: pattern_list.append(f"跌停{down}次")
        except: pass
    
    if pattern_list: results['K线形态'] = ", ".join(pattern_list)
    
    if vol_col in df_period.columns:
        try:
            avg_vol = df_period[vol_col].mean()
            results['日均成交量'] = f"{avg_vol:,.0f}"
            high_vol = df_period[df_period[vol_col] > avg_vol * 2]
            if len(high_vol) > 0: results['放量交易日'] = f"{len(high_vol)}次"
        except: pass
    
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

_market_cache = None
def get_market_data():
    global _market_cache
    if _market_cache is not None: return _market_cache
    _market_cache = {}
    try:
        df = ak.stock_a_ttm_lyr()
        if df is not None and not df.empty:
            _market_cache['pe'] = df
    except: pass
    try:
        df = ak.stock_a_all_pb()
        if df is not None and not df.empty:
            _market_cache['pb'] = df
    except: pass
    return _market_cache

def get_market_summary():
    data = get_market_data()
    if not data: return None
    summary = []
    if 'pe' in data and not data['pe'].empty:
        df = data['pe'].tail(30).copy()
        if 'middlePETTM' in df.columns:
            latest_pe = df['middlePETTM'].iloc[-1]
            pe_30d_ago = df['middlePETTM'].iloc[0] if len(df) > 0 else latest_pe
            pe_change = (latest_pe - pe_30d_ago) / pe_30d_ago * 100 if pe_30d_ago else 0
            if latest_pe < 15: pe_label = "低估"
            elif latest_pe < 25: pe_label = "合理"
            else: pe_label = "高估"
            summary.append(f"市场PE: {latest_pe:.1f} ({pe_label}, 30日{pe_change:+.1f}%)")
    if 'pb' in data and not data['pb'].empty:
        df = data['pb'].tail(30).copy()
        if 'middlePB' in df.columns:
            latest_pb = df['middlePB'].iloc[-1]
            if latest_pb < 1.5: pb_label = "低估"
            elif latest_pb < 3: pb_label = "合理"
            else: pb_label = "高估"
            summary.append(f"市场PB: {latest_pb:.2f} ({pb_label})")
    return " | ".join(summary) if summary else None

import numpy as np
def get_z_score(prices, min_periods=20):
    if len(prices) < min_periods: return None
    mean = np.mean(prices)
    std = np.std(prices)
    if std == 0: return 0
    return (prices[-1] - mean) / std

def generate_summary(code, name, market, daily_df, news_list):
    analysis = []
    close_col = '收盘' if daily_df is not None and '收盘' in daily_df.columns else 'close'
    date_col = '日期' if daily_df is not None and '日期' in daily_df.columns else 'date'
    vol_col = '成交量' if daily_df is not None and '成交量' in daily_df.columns else 'volume'
    
    if daily_df is not None and not daily_df.empty and date_col in daily_df.columns:
        one_year_ago = get_one_year_ago()
        df_year = daily_df[pd.to_datetime(daily_df[date_col]) >= one_year_ago]
        if len(df_year) > 1:
            change = (df_year.iloc[-1][close_col] - df_year.iloc[0][close_col]) / df_year.iloc[0][close_col] * 100
            if change > 20: analysis.append(f"近1年涨幅{change:.1f}%")
            elif change < -30: analysis.append(f"近1年跌幅{abs(change):.1f}%超跌")
        
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        df_month = daily_df[pd.to_datetime(daily_df[date_col]) >= one_month_ago]
        if len(df_month) > 1:
            change = (df_month.iloc[-1][close_col] - df_month.iloc[0][close_col]) / df_month.iloc[0][close_col] * 100
            if change >= 10: analysis.append(f"近1月涨幅{change:.1f}%")
            elif change <= -10: analysis.append(f"近1月跌幅{abs(change):.1f}%")
        
        one_week = get_one_week_ago()
        df_week = daily_df[pd.to_datetime(daily_df[date_col]) >= one_week]
        if len(df_week) > 1:
            change = (df_week.iloc[-1][close_col] - df_week.iloc[0][close_col]) / df_week.iloc[0][close_col] * 100
            if change >= 5: analysis.append(f"本周大涨{change:.1f}%")
            elif change <= -5: analysis.append(f"本周大跌{abs(change):.1f}%")
        if vol_col in daily_df.columns:
            recent = daily_df[vol_col].tail(5).mean()
            avg = daily_df[vol_col].mean()
            if recent >= avg * 2.5: analysis.append("成交量显著放大")
            elif recent <= avg * 0.4: analysis.append("成交量明显萎缩")
        if len(daily_df) >= 20 and close_col in daily_df.columns:
            ma5 = daily_df[close_col].tail(5).mean()
            ma20 = daily_df[close_col].tail(20).mean()
            ma5_p = daily_df[close_col].tail(6).mean()
            ma20_p = daily_df[close_col].tail(21).mean()
            if ma5 > ma20 and ma5_p <= ma20_p: analysis.append("均线金叉信号")
        z10 = get_z_score(daily_df[close_col].tail(10).values, 10) if len(daily_df) >= 10 else None
        z30 = get_z_score(daily_df[close_col].tail(30).values) if len(daily_df) >= 30 else None
        z60 = get_z_score(daily_df[close_col].tail(60).values) if len(daily_df) >= 60 else None
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
    date_col = '日期' if daily_df is not None and '日期' in daily_df.columns else 'date'
    
    if daily_df is not None and not daily_df.empty and date_col in daily_df.columns:
        period_results.append(analyze_period(daily_df, "2年内"))
        one_year = get_one_year_ago()
        df_year = daily_df[pd.to_datetime(daily_df[date_col]) >= one_year]
        period_results.append(analyze_period(df_year, "1年以内"))
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        df_month = daily_df[pd.to_datetime(daily_df[date_col]) >= one_month_ago]
        period_results.append(analyze_period(df_month, "1月以内"))
        one_week = get_one_week_ago()
        df_week = daily_df[pd.to_datetime(daily_df[date_col]) >= one_week]
        period_results.append(analyze_period(df_week, "本周"))
    else:
        period_results.append({"时间段": "2年内", "数据": "无数据"})
        period_results.append({"时间段": "1年以内", "数据": "无数据"})
        period_results.append({"时间段": "1月以内", "数据": "无数据"})
        period_results.append({"时间段": "本周", "数据": "无数据"})
    
    summary = generate_summary(code, name, market, daily_df, news_list)
    market_info = get_market_summary()
    
    report = f"""# {name} ({code}) 分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**市场**: {market}  
**代码**: {code}
{f"**大盘**: {market_info}" if market_info else ""}

---

## 📊 分时段分析

| 指标 | 2年内 | 1年以内 | 1月以内 | 本周 |
|------|----------|---------|--------|------|
"""
    keys = set()
    for p in period_results: keys.update(p.keys())
    keys.discard('时间段')
    for key in sorted(keys):
        vals = [p.get(key, '-') for p in period_results]
        report += f"| {key} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |\n"
    
    # K线表格
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
    
    # 检查可用的列
    kline_cols = [date_col, open_col, close_col, high_col, low_col, vol_col]
    available_cols = [c for c in kline_cols if c in daily_df.columns]
    
    if daily_df is not None and not daily_df.empty and close_col in daily_df.columns:
        # 构建表头和分隔行
        header = "| 日期 | 开盘 | 收盘 | 最高 | 最低"
        if amt_col in daily_df.columns: header += " | 成交额"
        if amp_col in daily_df.columns: header += " | 振幅"
        if pct_col in daily_df.columns: header += " | 涨跌幅"
        if change_col in daily_df.columns: header += " | 涨跌额"
        if turnover_col in daily_df.columns: header += " | 换手率"
        header += " |\n"
        
        # 分隔行 - 计算列数并生成对应的分隔符
        col_count = header.count("|") - 1  # 去掉开头和结尾的|
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
    
    if daily_df is not None and len(daily_df) >= 20 and close_col in daily_df.columns:
        # 计算不同周期的Z-Score
        z10 = get_z_score(daily_df[close_col].tail(10).values, 10) if len(daily_df) >= 10 else None
        z30 = get_z_score(daily_df[close_col].tail(30).values) if len(daily_df) >= 30 else None
        z60 = get_z_score(daily_df[close_col].tail(60).values) if len(daily_df) >= 60 else None
        z120 = get_z_score(daily_df[close_col].tail(120).values) if len(daily_df) >= 120 else None
        
        def get_z_label(z):
            if z is None: return '-'
            if z < -2: return '严重低估'
            elif z < -1: return '低估'
            elif z < 1: return '正常'
            elif z < 2: return '高估'
            else: return '严重高估'
        
        if z10 is not None:
            report += f"| Z-Score(10日) | {z10:.2f} ({get_z_label(z10)}) |\n"
        if z30 is not None:
            report += f"| Z-Score(30日) | {z30:.2f} ({get_z_label(z30)}) |\n"
        if z60 is not None:
            report += f"| Z-Score(60日) | {z60:.2f} ({get_z_label(z60)}) |\n"
        if z120 is not None:
            report += f"| Z-Score(120日) | {z120:.2f} ({get_z_label(z120)}) |\n"
    
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
    
    if news_list:
        report += "\n---\n\n## 📰 近期新闻\n\n"
        for news in news_list[:5]:
            d = news['date'] if news['date'] != 'N/A' else '近日'
            report += f"- **{d}**: {news['title']}\n"
    else:
        report += "\n---\n\n## 📰 近期新闻\n\n暂无新闻\n"
    
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
    
    is_bj = code.startswith('8') or code.startswith('4') or (code.startswith('3') and len(code) == 6 and int(code) >= 300000)
    symbol = f"BJ{code}" if is_bj else f"{market.lower()}{code}"
    
    daily_df = None
    retry_count = 3
    for attempt in range(retry_count):
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=3650)).strftime('%Y%m%d')
            daily_df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust='')
            
            if daily_df is not None and not daily_df.empty and '日期' in daily_df.columns:
                daily_df = daily_df.sort_values('日期')
                daily_df['pct_chg'] = (daily_df['收盘'] - daily_df['收盘'].shift(1)) / daily_df['收盘'].shift(1) * 100
                break  # 成功获取数据
        except Exception as e:
            log(f"  K线获取失败 (尝试 {attempt+1}/{retry_count}): {str(e)[:50]}")
            if attempt < retry_count - 1:
                time.sleep(2)  # 等待后重试
            daily_df = None
    
    news_list = get_stock_news(code, name)
    report = generate_report(code, name, market, daily_df, news_list)
    
    safe_name = str(name).replace('/', '_').replace('*', 'ST')
    filepath = f"{DATA_DIR}/{code}_{safe_name}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    log(f"  ✅ 已保存: {code}_{safe_name}.md")
    return True

def main():
    print("=" * 60)
    print("  上海股票分析")
    print("=" * 60)
    
    if not os.path.exists(STOCK_LIST_FILE):
        print(f"错误: 找不到 {STOCK_LIST_FILE}")
        return
    
    stock_df = pd.read_csv(STOCK_LIST_FILE, dtype={'code': str})
    sh_df = stock_df[stock_df['市场'] == 'SH']
    
    # 已分析的
    analyzed = set()
    for f in os.listdir(DATA_DIR):
        if f.endswith('.md') and '_' in f:
            try:
                parts = f.replace('.md', '').split('_')
                if len(parts) >= 2:
                    code = parts[0]  # 代码在前
                    if code.isdigit() and code.startswith('6'):
                        analyzed.add(code)
            except: pass
    
    unan = sh_df[~sh_df['code'].astype(str).isin(analyzed)]
    if len(unan) == 0:
        print("上海股票全部完成!")
        return
    
    print(f"\n待分析: {len(unan)} 只")
    
    count = 0
    for idx, row in unan.iterrows():
        code = str(row['code'])
        name = row['name']
        market = 'SH'
        
        if analyze_one_stock(code, name, market):
            count += 1
            if count % 10 == 0:
                log(f"=== PROGRESS: {count}/{len(unan)} ({count/len(unan)*100:.1f}%) ===")
        
        time.sleep(SLEEP_SECONDS)
    
    print("\n✅ 上海股票分析完成!")

if __name__ == "__main__":
    main()
