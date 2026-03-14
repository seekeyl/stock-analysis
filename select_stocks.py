#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
import load_env
import os
"""
从 stock_daily 表筛选优质股票推荐
"""

import pymysql
from datetime import datetime

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

def get_recommendations(limit=20):
    """从 stock_daily 筛选优质股票"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 筛选条件：
    # 1. Z-Score 30天 <= -0.5 (低估)
    # 2. MACD 多头或金叉
    # 3. 换手率 > 1% (有流动性)
    # 4. 涨幅为正
    
    sql = '''
    SELECT 
        code, name, market, latest_price, change_pct, turnover_rate,
        zscore_10d, zscore_30d, zscore_60d,
        macd_signal, rsi_14, ma_signal
    FROM stock_daily
    WHERE 1=1
        AND latest_price IS NOT NULL
        AND zscore_30d IS NOT NULL
        AND zscore_30d <= -0.5
        AND turnover_rate > 1
        AND change_pct > -5
    ORDER BY zscore_30d ASC, turnover_rate DESC
    LIMIT 100
    '''
    
    cursor.execute(sql)
    candidates = cursor.fetchall()
    
    # 二次筛选：综合评分
    results = []
    for row in candidates:
        code, name, market, price, change, turnover, z10, z30, z60, macd, rsi, ma = row
        
        score = 0
        reasons = []
        
        # Z-Score 越低越好
        if z30 <= -1.5:
            score += 30
            reasons.append(f"Z30严重低估({z30:.2f})")
        elif z30 <= -1:
            score += 20
            reasons.append(f"Z30低估({z30:.2f})")
        elif z30 <= -0.5:
            score += 10
            reasons.append(f"Z30偏低({z30:.2f})")
        
        # MACD 多头加分
        if macd == '多头':
            score += 20
            reasons.append("MACD多头")
        elif macd == '金叉':
            score += 25
            reasons.append("MACD金叉")
        
        # RSI 不过高也不过低
        if rsi:
            if 30 < rsi < 70:
                score += 10
                reasons.append(f"RSI健康({rsi:.0f})")
        
        # 均线多头排列
        if ma == '多头':
            score += 15
            reasons.append("均线多头")
        
        # 换手率适中
        if 3 < turnover < 15:
            score += 10
            reasons.append(f"换手率{turnover:.1f}%")
        
        # 近期涨幅为正
        if change and change > 0:
            score += 5
            reasons.append(f"今日涨{change:.2f}%")
        
        results.append({
            'code': code,
            'name': name,
            'price': price,
            'change': change,
            'turnover': turnover,
            'z30': z30,
            'macd': macd,
            'rsi': rsi,
            'ma': ma,
            'score': score,
            'reasons': reasons
        })
    
    # 按评分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    cursor.close()
    conn.close()
    
    return results[:limit]

def generate_report(recommendations):
    """生成推荐报告"""
    lines = []
    lines.append("# 📈 股票推荐报告")
    lines.append("")
    lines.append(f"**生成时间**: " + datetime.now().strftime('%Y-%m-%d %H:%M'))
    lines.append(f"**推荐数量**: {len(recommendations)} 只")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for i, stock in enumerate(recommendations, 1):
        lines.append(f"### {i}. {stock['code']} {stock['name']}")
        lines.append("")
        lines.append(f"- **现价**: {stock['price']:.2f} (今日 {stock['change']:+.2f}%)")
        lines.append(f"- **换手率**: {stock['turnover']:.1f}%")
        lines.append(f"- **Z-Score 30天**: {stock['z30']:.2f}")
        lines.append(f"- **MACD**: {stock['macd']}")
        lines.append(f"- **RSI**: {stock['rsi']:.0f}" if stock['rsi'] else "- **RSI**: N/A")
        lines.append(f"- **均线**: {stock['ma']}")
        lines.append(f"- **评分**: {stock['score']}")
        lines.append(f"- **推荐理由**: {', '.join(stock['reasons'])}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    log("=" * 60)
    log("  股票筛选推荐")
    log("=" * 60)
    
    recommendations = get_recommendations(20)
    
    if not recommendations:
        log("未找到符合条件的股票")
        return
    
    report = generate_report(recommendations)
    
    # 输出报告
    print(report)
    
    # 保存报告
    with open('/home/seekey/dev/workspace/openclaw/stock/tmp/recommendation.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    log(f"\n✅ 推荐报告已生成: recommendation.md")

if __name__ == "__main__":
    main()
