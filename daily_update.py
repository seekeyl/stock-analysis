#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
import load_env
"""
每日股票数据更新脚本
1. 更新股票列表 (stock_list)
2. 更新7天股票历史 (stock_history)  
3. 更新7天股票新闻 (stock_news)
4. 更新7天大盘信息 (stock_market)
"""

import os
import akshare as ak
import pandas as pd
import pymysql
from datetime import datetime, timedelta
import time

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

def update_stock_list(conn):
    """更新股票列表"""
    log("1. 更新股票列表...")
    
    try:
        # A股股票列表
        df = ak.stock_info_a_code_name()
        if df is None or df.empty:
            log("  ⚠️ 获取股票列表失败")
            return 0
        
        cursor = conn.cursor()
        
        # 清空并重新导入
        cursor.execute("TRUNCATE TABLE stock_list")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                code = str(row.get('code', '')).zfill(6)
                name = row.get('name', '')
                if code and name:
                    cursor.execute(
                        "INSERT IGNORE INTO stock_list (code, name) VALUES (%s, %s)",
                        (code, name)
                    )
                    inserted += 1
            except:
                pass
        
        conn.commit()
        cursor.close()
        log(f"  ✅ 股票列表更新完成: {inserted} 只")
        return inserted
    except Exception as e:
        log(f"  ❌ 股票列表更新失败: {e}")
        return 0

def update_stock_history(conn, days=7):
    """更新股票历史"""
    log(f"2. 更新最近{days}天股票历史...")
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')  # 只取30天
    
    cursor = conn.cursor()
    
    # 全量更新：获取所有股票
    cursor.execute("SELECT code FROM stock_list")
    all_stocks = [row[0] for row in cursor.fetchall()]
    
    log(f"  待更新: {len(all_stocks)} 只")
    
    updated = 0
    for code in all_stocks:
        try:
            df = ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust='')
            if df is None or df.empty:
                continue
            
            # 重命名列
            rename_map = {
                '日期': 'trade_date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume',
                '成交额': 'amount', '振幅': 'amplitude', '涨跌幅': 'pct_chg',
                '涨跌额': 'change_price', '换手率': 'turnover'
            }
            for cn, en in rename_map.items():
                if cn in df.columns:
                    df = df.rename(columns={cn: en})
            
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
            
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                    INSERT IGNORE INTO stock_history 
                    (code, trade_date, open, high, low, close, volume, amount, pct_chg, change_price, turnover_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        code, row['trade_date'],
                        float(row['open']) if pd.notna(row.get('open')) else None,
                        float(row['high']) if pd.notna(row.get('high')) else None,
                        float(row['low']) if pd.notna(row.get('low')) else None,
                        float(row['close']) if pd.notna(row.get('close')) else None,
                        int(row['volume']) if pd.notna(row.get('volume')) else None,
                        int(row['amount']) if pd.notna(row.get('amount')) else None,
                        float(row['pct_chg']) if pd.notna(row.get('pct_chg')) else None,
                        float(row['change_price']) if pd.notna(row.get('change_price')) else None,
                        float(row['turnover']) if pd.notna(row.get('turnover')) else None
                    ))
                except:
                    pass
            updated += 1
            if updated % 100 == 0:
                log(f"  进度: {updated}/{len(all_stocks)}")
        except Exception as e:
            pass
        time.sleep(0.2)
    
    conn.commit()
    cursor.close()
    log(f"  ✅ 股票历史更新完成: {updated} 只")
    return updated

def update_stock_news(conn, days=7):
    """更新股票新闻"""
    log(f"3. 更新最近{days}天股票新闻...")
    
    cursor = conn.cursor()
    
    # 全量更新：获取所有有历史的股票
    cursor.execute("SELECT DISTINCT code FROM stock_history")
    all_stocks = [row[0] for row in cursor.fetchall()]
    
    log(f"  待更新: {len(all_stocks)} 只")
    
    total_news = 0
    for i, code in enumerate(all_stocks):
        try:
            df = ak.stock_news_em(symbol=code)
            if df is None or df.empty:
                continue
            
            for _, row in df.iterrows():
                try:
                    pub_date = row.get('发布时间')
                    if pd.notna(pub_date):
                        if isinstance(pub_date, str):
                            try:
                                pub_date = pd.to_datetime(pub_date)
                            except:
                                continue
                        pub_date = pub_date.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        continue
                    
                    cursor.execute('''
                    INSERT IGNORE INTO stock_news 
                    (code, title, content, pub_date, source, url, keywords)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        code,
                        row.get('新闻标题', '')[:500] if pd.notna(row.get('新闻标题')) else None,
                        row.get('新闻内容') if pd.notna(row.get('新闻内容')) else None,
                        pub_date,
                        row.get('文章来源') if pd.notna(row.get('文章来源')) else None,
                        row.get('新闻链接') if pd.notna(row.get('新闻链接')) else None,
                        row.get('关键词') if pd.notna(row.get('关键词')) else None
                    ))
                    total_news += 1
                except:
                    pass
        except:
            pass
        
        if (i + 1) % 100 == 0:
            log(f"  进度: {i+1}/{len(all_stocks)}")
        time.sleep(0.3)
    
    conn.commit()
    cursor.close()
    log(f"  ✅ 股票新闻更新完成: {total_news} 条")
    return total_news

def update_stock_market(conn, days=7):
    """更新大盘信息"""
    log(f"4. 更新最近{days}天大盘信息...")
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days+10)).strftime('%Y%m%d')
    
    cursor = conn.cursor()
    total = 0
    
    for symbol, market in [('sh000001', 'SH'), ('sz399001', 'SZ')]:
        try:
            # 使用 stock_zh_index_daily_em，有成交额字段
            df = ak.stock_zh_index_daily_em(symbol=symbol)
            if df is None or df.empty:
                continue
            
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            df = df[df['date'] >= start_date]
            
            # 计算涨跌幅
            df['pct_chg'] = df['close'].pct_change() * 100
            
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                    INSERT IGNORE INTO stock_market 
                    (market, trade_date, open, high, low, close, volume, amount, pct_chg)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        market, row['date'], row['open'], row['high'],
                        row['low'], row['close'], row['volume'],
                        int(row['amount']) if pd.notna(row.get('amount')) else None,
                        round(row['pct_chg'], 4) if pd.notna(row['pct_chg']) else None
                    ))
                    total += 1
                except:
                    pass
        except Exception as e:
            log(f"  ⚠️ {market} 更新失败: {e}")
    
    conn.commit()
    cursor.close()
    log(f"  ✅ 大盘信息更新完成: {total} 条")
    return total

def main():
    log("=" * 60)
    log("  每日股票数据更新")
    log("=" * 60)
    
    conn = pymysql.connect(**DB_CONFIG)
    
    t1 = update_stock_list(conn)
    t2 = update_stock_history(conn, days=7)
    t3 = update_stock_news(conn, days=7)
    t4 = update_stock_market(conn, days=7)
    
    conn.close()
    
    log("=" * 60)
    log(f"✅ 全部完成!")
    log(f"  - 股票列表: {t1} 只")
    log(f"  - 股票历史: {t2} 只")
    log(f"  - 股票新闻: {t3} 条")
    log(f"  - 大盘信息: {t4} 条")
    log("=" * 60)

if __name__ == "__main__":
    main()
