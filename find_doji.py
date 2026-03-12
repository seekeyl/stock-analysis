#!/usr/bin/env python3
"""
遍历所有A股，找出昨天十字星的个股
十字星: 实体很小，上下影线差不多长
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def is_doji(row, threshold=0.03):
    """
    判断是否为十字星
    实体(开盘-收盘)占整体(最高-最低)的比例小于threshold
    """
    try:
        body = abs(row['open'] - row['close'])
        range_val = row['high'] - row['low']
        
        if range_val == 0 or body == 0:
            return False
        
        # 实体占比小于 threshold 认为是非十字星(可以考虑为十字星)
        ratio = body / range_val
        return ratio < threshold
    except:
        return False

def get_yesterday():
    """获取昨天的日期"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

def check_doji_for_stock(symbol, date):
    """检查单只股票昨天是否为十字星"""
    try:
        # 尝试沪市
        df = ak.stock_zh_a_daily(symbol=f"sh{symbol}")
        if df is None or df.empty:
            # 尝试深市
            df = ak.stock_zh_a_daily(symbol=f"sz{symbol}")
        
        if df is None or df.empty:
            return None
        
        # 找昨天日期
        date_str = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        
        # 尝试多种日期格式
        for col in ['date', '日期']:
            if col in df.columns:
                yesterday_data = df[df[col] == date_str]
                if not yesterday_data.empty:
                    row = yesterday_data.iloc[0]
                    if is_doji(row):
                        return {
                            'code': symbol,
                            'open': row['open'],
                            'close': row['close'],
                            'high': row['high'],
                            'low': row['low']
                        }
                break
        return None
    except Exception as e:
        return None

def main():
    print("=" * 70)
    print("  A股十字星筛选")
    print(f"  日期: 昨天 ({get_yesterday()})")
    print("=" * 70)
    
    date = get_yesterday()
    date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    
    # 获取股票列表
    print("\n📋 获取股票列表...")
    try:
        sh_stocks = ak.stock_info_sh_name_code()
        sz_stocks = ak.stock_info_sz_name_code()
        
        sh_codes = sh_stocks['证券代码'].tolist()
        sz_codes = sz_stocks['A股代码'].tolist()
        
        print(f"  上证: {len(sh_codes)} 只")
        print(f"  深证: {len(sz_codes)} 只")
    except Exception as e:
        print(f"  获取失败: {e}")
        return
    
    # 遍历检查
    print(f"\n🔍 遍历检查十字星 (共 {len(sh_codes) + len(sz_codes)} 只)...")
    
    doji_stocks = []
    total = len(sh_codes) + len(sz_codes)
    checked = 0
    
    # 限制数量先测试
    limit = 100  # 先检查100只
    
    for codes, market in [(sh_codes[:limit], 'SH'), (sz_codes[:limit], 'SZ')]:
        for code in codes:
            checked += 1
            if checked % 20 == 0:
                print(f"  进度: {checked}/{min(limit*2, total)}...")
            
            result = check_doji_for_stock(code, date)
            if result:
                result['market'] = market
                doji_stocks.append(result)
    
    # 打印结果
    print(f"\n{'='*70}")
    print(f"  筛选结果: 昨天({date_fmt})十字星个股")
    print(f"{'='*70}")
    
    if doji_stocks:
        print(f"\n找到 {len(doji_stocks)} 只十字星:\n")
        
        # 获取股票名称
        sh_names = dict(zip(sh_stocks['证券代码'], sh_stocks['证券简称']))
        sz_names = dict(zip(sz_stocks['A股代码'], sz_stocks['A股简称']))
        
        for stock in doji_stocks:
            name = sh_names.get(stock['code']) or sz_names.get(stock['code'], '未知')
            body = abs(stock['open'] - stock['close'])
            range_val = stock['high'] - stock['low']
            ratio = (body / range_val * 100) if range_val > 0 else 0
            
            print(f"  {stock['market']}{stock['code']} {name}")
            print(f"      开:{stock['open']:.2f} 收:{stock['close']:.2f} 高:{stock['high']:.2f} 低:{stock['low']:.2f}")
            print(f"      实体占比: {ratio:.1f}%")
            print()
    else:
        print("\n未找到十字星个股")
        print("可能原因: 数据未更新或筛选条件过严")
    
    print(f"\n注意: 仅检查了前 {limit*2} 只股票作为演示")
    print("如需全量检查，需要更多时间")

if __name__ == "__main__":
    main()
