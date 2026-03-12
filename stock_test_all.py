#!/usr/bin/env python3
"""
AkShare 全接口测试
自动遍历所有子接口，生成功能清单
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import warnings
import sys
warnings.filterwarnings('ignore')

# 分类定义
CATEGORIES = {
    "股票": [
        ("stock_info_sh_name_code", {}, "上证股票列表"),
        ("stock_info_sz_name_code", {}, "深证股票列表"),
        ("stock_zh_a_spot_em", {}, "A股实时行情"),
        ("stock_zh_a_daily", {"symbol": "sh600519"}, "个股历史K线"),
        ("stock_zh_a_hist", {"symbol": "600519", "period": "daily", "start_date": "20260101", "end_date": "20260304"}, "A股历史数据"),
        ("stock_zh_index_spot_em", {}, "指数实时行情"),
        ("stock_zh_index_daily", {"symbol": "000001"}, "指数历史数据"),
        ("stock_lhb_detail_em", {"trade_date": "20260303"}, "龙虎榜明细"),
        ("stock_zt_pool_em", {"date": "20260303"}, "涨停池"),
        ("stock_margin_sse", {}, "融资融券汇总"),
        ("stock_new_a_spot_em", {}, "新股列表"),
        ("stock_sz_a_spot_em", {}, "深股通列表"),
        ("stock_sh_a_spot_em", {}, "沪股通列表"),
    ],
    "基金": [
        ("fund_etf_spot_em", {}, "ETF实时行情"),
        ("fund_open_fund_daily_em", {}, "公募基金每日行情"),
        ("fund_money_fund_daily_em", {}, "货币基金每日"),
        ("fund_lof_spot_em", {}, "LOF基金行情"),
        ("fund_name_em", {}, "基金列表"),
        ("fund_etf_dividend_sina", {"symbol": "sh510300"}, "ETF分红"),
    ],
    "期货": [
        ("futures_comm_info", {}, "期货品种信息"),
        ("futures_contract_info_cffex", {}, "中金所合约"),
    ],
    "债券": [
        ("bond_zh_hs_spot", {}, "沪深债券现货"),
        ("bond_zh_hs_daily", {"symbol": "sh110007"}, "债券历史行情"),
        ("bond_cb_jsl", {"bond": "113052"}, "可转债数据"),
    ],
    "外汇": [
        ("forex_spot_em", {}, "外汇实时行情"),
        ("currency_pair_map", {}, "货币对列表"),
    ],
    "宏观": [
        ("fred_md", {"symbol": "DFF"}, "美联储利率"),
    ],
    "其他": [
        ("tool_trade_date_hist_sina", {"start_date": "20260101", "end_date": "20260304"}, "交易日历"),
    ]
}

def test_function(func_name, kwargs, desc):
    """测试单个函数"""
    try:
        func = getattr(ak, func_name)
        result = func(**kwargs)
        
        if isinstance(result, pd.DataFrame):
            rows = len(result)
            cols = len(result.columns)
            return True, f"✅ {rows}行 x {cols}列"
        elif isinstance(result, dict):
            return True, f"✅ {len(result)}条"
        elif isinstance(result, list):
            return True, f"✅ {len(result)}条"
        else:
            return True, f"✅ {type(result).__name__}"
    except Exception as e:
        err_msg = str(e)[:50]
        return False, f"❌ {err_msg}"

def main():
    print("=" * 70)
    print("  AkShare 全接口测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    total_pass = 0
    total_fail = 0
    
    for category, funcs in CATEGORIES.items():
        print(f"\n📂 {category}")
        print("-" * 70)
        results[category] = []
        
        for func_name, kwargs, desc in funcs:
            success, msg = test_function(func_name, kwargs, desc)
            status = "✅" if success else "❌"
            print(f"  {status} {desc}")
            print(f"      {func_name}: {msg}")
            
            results[category].append({
                "name": func_name,
                "desc": desc,
                "success": success,
                "msg": msg
            })
            
            if success:
                total_pass += 1
            else:
                total_fail += 1
    
    # 输出功能清单
    print("\n" + "=" * 70)
    print("  功能清单")
    print("=" * 70)
    
    all_funcs = []
    for category, funcs in results.items():
        for f in funcs:
            all_funcs.append((category, f['name'], f['desc'], f['success']))
    
    # 按状态排序：成功的在前
    all_funcs.sort(key=lambda x: (not x[3], x[0], x[1]))
    
    print(f"\n总计: {total_pass} 成功 / {total_fail} 失败")
    print("\n按类别:")
    for category in CATEGORIES.keys():
        funcs_in_cat = [f for f in all_funcs if f[0] == category]
        passed = sum(1 for f in funcs_in_cat if f[3])
        print(f"  {category}: {passed}/{len(funcs_in_cat)} 通过")
    
    print("\n可用函数列表 (成功):")
    for cat, name, desc, success in all_funcs:
        if success:
            print(f"  [{cat}] {name}: {desc}")
    
    if total_fail > 0:
        print(f"\n失败函数 ({total_fail}):")
        for cat, name, desc, success in all_funcs:
            if not success:
                print(f"  [{cat}] {name}: {desc}")

if __name__ == "__main__":
    main()
