#!/usr/bin/env python3
"""
步骤1: 获取A股所有股票列表
保存到 tmp/stock_info.csv
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import os

DATA_DIR = '/home/seekey/dev/workspace/openclaw/stock/tmp'

def main():
    print("=" * 60)
    print("  步骤1: 获取A股股票列表")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 获取上证股票列表
    print("\n📋 获取上证股票列表...")
    sh_stocks = ak.stock_info_sh_name_code()
    sh_stocks['市场'] = 'SH'
    sh_stocks = sh_stocks.rename(columns={
        '证券代码': 'code',
        '证券简称': 'name',
        '公司全称': 'company',
        '上市日期': 'list_date'
    })
    sh_stocks = sh_stocks[['code', 'name', 'company', 'list_date', '市场']]
    print(f"  上证: {len(sh_stocks)} 只")
    
    # 获取深证股票列表
    print("\n📋 获取深证股票列表...")
    sz_stocks = ak.stock_info_sz_name_code()
    sz_stocks['市场'] = 'SZ'
    sz_stocks = sz_stocks.rename(columns={
        'A股代码': 'code',
        'A股简称': 'name',
        'A股总股本': 'total_share',
        'A股流通股本': 'float_share',
        '所属行业': 'industry'
    })
    sz_stocks = sz_stocks[['code', 'name', 'total_share', 'float_share', 'industry', '市场']]
    print(f"  深证: {len(sz_stocks)} 只")
    
    # 合并
    print("\n📊 合并数据...")
    all_stocks = pd.concat([sh_stocks, sz_stocks], ignore_index=True)
    print(f"  合计: {len(all_stocks)} 只")
    
    # 添加分析状态列
    all_stocks['analyzed'] = '否'
    all_stocks['analyze_date'] = ''
    
    # 保存
    output_path = f'{DATA_DIR}/stock_info.csv'
    all_stocks.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 已保存到: {output_path}")
    print(f"   共 {len(all_stocks)} 只股票")
    
    # 显示前几行
    print("\n📋 前10行预览:")
    print(all_stocks.head(10).to_string())

if __name__ == "__main__":
    main()
