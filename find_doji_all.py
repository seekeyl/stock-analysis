#!/usr/bin/env python3
"""
全量A股十字星筛选 - 优化版
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import sys
import time

def log(msg):
    print(msg)
    sys.stdout.flush()

def is_doji(row, threshold=0.03):
    try:
        body = abs(row['open'] - row['close'])
        range_val = row['high'] - row['low']
        if range_val <= 0 or body <= 0:
            return False
        return (body / range_val) < threshold
    except:
        return False

log("=" * 60)
log("  全量A股十字星筛选")
log(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log("=" * 60)

# 获取股票列表
log("\n获取股票列表...")
sh_stocks = ak.stock_info_sh_name_code()
sz_stocks = ak.stock_info_sz_name_code()

sh_codes = sh_stocks['证券代码'].tolist()
sz_codes = sz_stocks['A股代码'].tolist()

log(f"  上证: {len(sh_codes)} 只, 深证: {len(sz_codes)} 只, 合计: {len(sh_codes) + len(sz_codes)} 只")

doji_list = []
total = len(sh_codes) + len(sz_codes)
checked = 0

# 检查上证
log("\n检查上证...")
for i, code in enumerate(sh_codes):
    checked += 1
    if i % 100 == 0:
        log(f"  进度: {checked}/{total}")
    
    try:
        daily = ak.stock_zh_a_daily(symbol=f"sh{code}")
        if daily is not None and not daily.empty:
            latest = daily.iloc[-1]
            if is_doji(latest):
                name = sh_stocks[sh_stocks['证券代码'] == code]['证券简称'].values[0]
                doji_list.append({'code': f"SH{code}", 'name': name, 'data': latest.to_dict()})
    except:
        pass
    
    if i % 30 == 0:
        time.sleep(0.5)

# 检查深证  
log("\n检查深证...")
for i, code in enumerate(sz_codes):
    checked += 1
    if i % 100 == 0:
        log(f"  进度: {checked}/{total}")
    
    try:
        daily = ak.stock_zh_a_daily(symbol=f"sz{code}")
        if daily is not None and not daily.empty:
            latest = daily.iloc[-1]
            if is_doji(latest):
                name = sz_stocks[sz_stocks['A股代码'] == code]['A股简称'].values[0]
                doji_list.append({'code': f"SZ{code}", 'name': name, 'data': latest.to_dict()})
    except:
        pass
    
    if i % 30 == 0:
        time.sleep(0.5)

# 打印结果
log(f"\n{'='*60}")
log(f"  完成! 检查: {total} 只, 十字星: {len(doji_list)} 只")
log("=" * 60)

if doji_list:
    doji_list.sort(key=lambda x: x['code'])
    for i, s in enumerate(doji_list, 1):
        d = s['data']
        body = abs(d['open'] - d['close'])
        range_val = d['high'] - d['low']
        ratio = body/range_val*100 if range_val > 0 else 0
        
        log(f"\n{i:2d}. {s['code']} {s['name']}")
        log(f"    开:{d['open']:.2f} 收:{d['close']:.2f} 高:{d['high']:.2f} 低:{d['low']:.2f}")
        log(f"    实体占比: {ratio:.1f}%")
    
    # 保存
    df = pd.DataFrame([{**s, **s.pop('data')} for s in doji_list])
    df.to_csv('/root/.openclaw/workspace/projects/stock/doji_result.csv', index=False, encoding='utf-8-sig')
    log(f"\n结果已保存到: /root/.openclaw/workspace/projects/stock/doji_result.csv")
else:
    log("\n未找到十字星个股")
