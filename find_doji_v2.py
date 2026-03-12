#!/usr/bin/env python3
"""
批量获取A股数据，找出昨天十字星的个股
优化: 使用批量接口减少网络请求
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def is_doji(row, body_ratio=0.03):
    """判断是否为十字星 (实体占比 < 3%)"""
    try:
        body = abs(row['open'] - row['close'])
        range_val = row['high'] - row['low']
        
        if range_val <= 0 or body <= 0:
            return False
        
        return (body / range_val) < body_ratio
    except:
        return False

def get_yesterday_str():
    """获取昨天的字符串"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

def main():
    print("=" * 70)
    print("  A股十字星筛选 (批量版)")
    print(f"  日期: 昨天 ({get_yesterday_str()})")
    print("=" * 70)
    
    # 方法1: 尝试获取所有A股日线数据
    print("\n📥 尝试批量获取A股日线数据...")
    
    try:
        # 这个接口可以获取所有A股的日线
        df = ak.stock_zh_a_daily(symbol="sh000001")  # 先获取一个看看格式
        
        if df is not None and not df.empty:
            print(f"  数据列: {df.columns.tolist()}")
            print(f"  最近日期: {df['date'].iloc[-1] if 'date' in df.columns else 'N/A'}")
    except Exception as e:
        print(f"  获取失败: {e}")
    
    # 方法2: 用指数成分股来筛选
    print("\n📊 获取主要指数成分股...")
    
    try:
        # 获取上证50成分股
        df_sh50 = ak.stock_zh_index_cons_sina(symbol="sh000016")
        print(f"  上证50: {len(df_sh50)} 只")
    except:
        df_sh50 = None
    
    try:
        # 获取创业板指成分股
        df_cyb = ak.stock_zh_index_cons_sina(symbol="sz399006")
        print(f"  创业板指: {len(df_cyb)} 只")
    except:
        df_cyb = None
    
    # 方法3: 直接用涨停池数据
    print("\n🔥 获取昨日涨停池...")
    
    yesterday = get_yesterday_str()
    try:
        zhangting = ak.stock_zt_pool_em(date=yesterday)
        if zhangting is not None and not zhangting.empty:
            print(f"  昨日涨停: {len(zhangting)} 只")
            
            # 检查涨停股中是否有十字星
            if 'close' in zhangting.columns and 'open' in zhangting.columns:
                zhangting['is_doji'] = zhangting.apply(is_doji, axis=1)
                doji_in_zhangting = zhangting[zhangting['is_doji']]
                
                if not doji_in_zhangting.empty:
                    print(f"\n  昨日涨停中含十字星: {len(doji_in_zhangting)} 只")
                    print(doji_in_zhangting[['代码', '名称', '涨跌幅']].to_string())
    except Exception as e:
        print(f"  获取失败: {e}")
    
    # 方法4: 用融资融券数据
    print("\n💰 获取融资融券数据...")
    
    try:
        margin = ak.stock_margin_sse()
        if margin is not None and not margin.empty:
            print(f"  融资融券股票: {len(margin)} 只")
            
            # 随机抽样检查十字星
            sample = margin.sample(min(20, len(margin)))
            
            doji_list = []
            for _, row in sample.iterrows():
                try:
                    code = row['证券代码']
                    symbol = f"sh{code}"
                    
                    daily = ak.stock_zh_a_daily(symbol=symbol)
                    if daily is not None and not daily.empty:
                        yesterday_data = daily.iloc[-1]
                        if is_doji(yesterday_data):
                            doji_list.append({
                                'code': code,
                                'name': row.get('证券简称', '未知'),
                                'close': yesterday_data['close']
                            })
                except:
                    pass
            
            if doji_list:
                print(f"\n  抽样检查十字星 (20只):")
                for s in doji_list:
                    print(f"    {s['code']} {s['name']} 收盘:{s['close']}")
    except Exception as e:
        print(f"  获取失败: {e}")
    
    # 方法5: 尝试用日线批量接口
    print("\n📈 尝试获取指数历史...")
    
    try:
        # 尝试获取沪深300历史
        hs300 = ak.stock_zh_index_daily(symbol="sh000300")
        if hs300 is not None and not hs300.empty:
            latest = hs300.iloc[-1]
            print(f"  沪深300 最新:")
            print(f"    日期: {latest.get('date', 'N/A')}")
            print(f"    开: {latest.get('open', 'N/A'):.2f}" if 'open' in latest else "")
            print(f"    收: {latest.get('close', 'N/A'):.2f}" if 'close' in latest else "")
            print(f"    高: {latest.get('high', 'N/A'):.2f}" if 'high' in latest else "")
            print(f"    低: {latest.get('low', 'N/A'):.2f}" if 'low' in latest else "")
            
            if is_doji(latest):
                print(f"    ⚠️ 十字星!")
    except Exception as e:
        print(f"  获取失败: {e}")
    
    print("\n" + "=" * 70)
    print("  说明")
    print("=" * 70)
    print("""
由于A股数量众多(4500+只)，逐个获取K线太慢。
推荐方案:
1. 使用专业回测框架 (Backtrader, Zipline)
2. 使用Tushare Pro (有缓存,更快)
3. 预先下载历史数据到本地数据库

如需快速演示，可以用融资融券列表抽样检查。
""")

if __name__ == "__main__":
    main()
