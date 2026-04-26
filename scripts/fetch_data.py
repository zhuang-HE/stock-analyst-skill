# -*- coding: utf-8 -*-
"""一次性获取股票分析所需的全部数据（tushare-data 层）"""
import sys
import io
import os
import json
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tushare as ts
import pandas as pd

def fetch_all(code: str, token: str):
    pro = ts.pro_api(token)
    
    # 确定交易所
    ts_code = f"{code}.SZ" if code.startswith(('0', '3')) else f"{code}.SH"
    
    # 日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')
    
    data = {'code': code, 'ts_code': ts_code}
    
    # 1. 日线行情
    print(f"[1/7] 获取日线行情 {ts_code}...", file=sys.stderr)
    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    data['daily'] = df.to_dict('records') if df is not None and len(df) > 0 else []
    print(f"  → 获取 {len(data['daily'])} 条日线", file=sys.stderr)
    
    # 2. 每日指标
    print(f"[2/7] 获取每日指标...", file=sys.stderr)
    df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
    data['daily_basic'] = df.to_dict('records') if df is not None and len(df) > 0 else []
    print(f"  → 获取 {len(data['daily_basic'])} 条", file=sys.stderr)
    
    # 3. 利润表
    print(f"[3/7] 获取利润表...", file=sys.stderr)
    try:
        df = pro.income(ts_code=ts_code, period_type='1')
        data['income'] = df.to_dict('records')[:8] if df is not None and len(df) > 0 else []
    except:
        data['income'] = []
    print(f"  → 获取 {len(data['income'])} 期", file=sys.stderr)
    
    # 4. 财务指标
    print(f"[4/7] 获取财务指标...", file=sys.stderr)
    try:
        df = pro.fina_indicator(ts_code=ts_code)
        data['fina_indicator'] = df.to_dict('records')[:8] if df is not None and len(df) > 0 else []
    except:
        data['fina_indicator'] = []
    print(f"  → 获取 {len(data['fina_indicator'])} 期", file=sys.stderr)
    
    # 5. 资金流向
    print(f"[5/7] 获取资金流向...", file=sys.stderr)
    try:
        df = pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
        data['moneyflow'] = df.to_dict('records') if df is not None and len(df) > 0 else []
    except:
        data['moneyflow'] = []
    print(f"  → 获取 {len(data['moneyflow'])} 条", file=sys.stderr)
    
    # 6. 新闻
    print(f"[6/7] 获取新闻...", file=sys.stderr)
    try:
        df = pro.news(src='sina', start_date=(datetime.now()-timedelta(days=7)).strftime('%Y%m%d'))
        data['news'] = df.to_dict('records')[:10] if df is not None and len(df) > 0 else []
    except:
        data['news'] = []
    print(f"  → 获取 {len(data['news'])} 条", file=sys.stderr)
    
    # 7. 盈利预测
    print(f"[7/7] 获取盈利预测...", file=sys.stderr)
    try:
        df = pro.forecast(ts_code=ts_code)
        data['forecast'] = df.to_dict('records')[:5] if df is not None and len(df) > 0 else []
    except:
        data['forecast'] = []
    print(f"  → 获取 {len(data['forecast'])} 条", file=sys.stderr)
    
    return data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': '用法: python fetch_data.py <code>'}, ensure_ascii=False), file=sys.stdout)
        sys.exit(1)
    
    code = sys.argv[1]
    token = os.environ.get('TUSHARE_TOKEN', '')
    if not token:
        print(json.dumps({'error': 'TUSHARE_TOKEN 未配置'}, ensure_ascii=False), file=sys.stdout)
        sys.exit(1)
    
    data = fetch_all(code, token)
    
    # 保存到临时文件
    out_path = os.path.join(os.path.expanduser('~'), f'stock_data_{code}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    
    # 输出文件路径（供下游脚本读取）
    print(f"DATA_FILE={out_path}")
