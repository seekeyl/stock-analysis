#!/usr/bin/env python3
"""
AkShare 功能清单 - 稳定可用版
整理了经过测试的可用接口
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ========== 稳定可用的接口 ==========
STABLE_APIS = {
    "📈 股票行情": {
        "stock_info_sh_name_code": ("上证股票列表", {}),
        "stock_info_sz_name_code": ("深证股票列表", {}),
        "stock_zh_a_daily": ("个股历史K线", {"symbol": "sh600519"}),
        "stock_zt_pool_em": ("涨停池", {"date": "20260303"}),
        "stock_margin_sse": ("融资融券汇总", {}),
    },
    "💰 基金数据": {
        "fund_open_fund_daily_em": ("公募基金每日行情", {}),
        "fund_money_fund_daily_em": ("货币基金每日", {}),
        "fund_name_em": ("基金列表", {}),
        "fund_etf_dividend_sina": ("ETF分红", {"symbol": "sh510300"}),
    },
    "📊 期货": {
        "futures_comm_info": ("期货品种信息", {}),
        "futures_contract_info_cffex": ("中金所合约", {}),
    },
    "💵 债券": {
        "bond_zh_hs_daily": ("债券历史行情", {"symbol": "sh110007"}),
    },
}

# ========== 需要网络的接口(可能不稳定) ==========
UNSTABLE_APIS = {
    "🌐 需要网络(可能不稳定)": {
        "stock_zh_a_spot_em": ("A股实时行情", {}),
        "stock_zh_a_hist": ("A股历史数据", {"symbol": "600519", "period": "daily", "start_date": "20260101", "end_date": "20260304"}),
        "stock_zh_index_spot_em": ("指数实时行情", {}),
        "stock_new_a_spot_em": ("新股列表", {}),
        "fund_etf_spot_em": ("ETF实时行情", {}),
        "forex_spot_em": ("外汇实时行情", {}),
    }
}

def test_api(name, kwargs):
    """测试接口"""
    try:
        func = getattr(ak, name)
        result = func(**kwargs)
        
        if isinstance(result, pd.DataFrame):
            return True, f"{result.shape[0]}行 x {result.shape[1]}列"
        elif isinstance(result, (dict, list)):
            return True, f"{len(result)}条"
        else:
            return True, str(type(result).__name__)
    except Exception as e:
        return False, str(e)[:40]

def main():
    print("=" * 70)
    print("  AkShare 功能清单")
    print(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_apis = {}
    all_apis.update(STABLE_APIS)
    all_apis.update(UNSTABLE_APIS)
    
    # 打印功能清单
    for category, apis in all_apis.items():
        print(f"\n{category}")
        print("-" * 70)
        
        for func_name, (desc, kwargs) in apis.items():
            success, msg = test_api(func_name, kwargs)
            status = "✅" if success else "❌"
            print(f"  {status} {desc}")
            print(f"      ak.{func_name}")
            if not success:
                print(f"      ❌ {msg}")
    
    # 简化清单
    print("\n" + "=" * 70)
    print("  📋 简化功能清单")
    print("=" * 70)
    
    print("\n✅ 稳定可用:")
    for category, apis in STABLE_APIS.items():
        print(f"\n{category}:")
        for func_name, (desc, _) in apis.items():
            print(f"  • ak.{func_name}()  # {desc}")
    
    print("\n⚠️ 需要网络(可能不稳定):")
    for category, apis in UNSTABLE_APIS.items():
        print(f"\n{category}:")
        for func_name, (desc, _) in apis.items():
            print(f"  • ak.{func_name}()  # {desc}")
    
    # 快速调用示例
    print("\n" + "=" * 70)
    print("  💻 快速调用示例")
    print("=" * 70)
    
    examples = '''
import akshare as ak

# 股票
stock_list = ak.stock_info_sh_name_code()  # 上证股票
stock_daily = ak.stock_zh_a_daily(symbol="sh600519")  # 茅台历史
zhangting = ak.stock_zt_pool_em(date="20260303")  # 涨停池
margin = ak.stock_margin_sse()  # 融资融券

# 基金
fund_list = ak.fund_name_em()  # 基金列表
fund_daily = ak.fund_open_fund_daily_em()  # 基金每日

# 期货
futures = ak.futures_comm_info()  # 期货品种

# 债券
bond = ak.bond_zh_hs_daily(symbol="sh110007")  # 债券历史
'''
    print(examples)

if __name__ == "__main__":
    main()
