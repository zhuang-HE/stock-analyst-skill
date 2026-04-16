# -*- coding: utf-8 -*-
"""数据审计工具 - 检查数据完整性和准确性"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from data_adapter import DataAdapter
import json

def audit_data(code, name):
    """审计股票数据完整性"""
    print(f'\n{"="*60}')
    print(f'数据审计: {code} {name}')
    print('='*60)
    
    adapter = DataAdapter()
    data, pattern_data = adapter.get_complete_data(code, name)
    
    issues = []
    
    # 1. 检查行情数据
    print('\n【1. 行情数据检查】')
    quote = data.get('quote', {})
    required_quote_fields = ['price', 'pct_change', 'volume', 'pe', 'pb', 'market_cap']
    for field in required_quote_fields:
        if field not in quote:
            issues.append(f'行情数据缺失: {field}')
            print(f'  ❌ 缺失: {field}')
        else:
            print(f'  ✓ {field}: {quote[field]}')
    
    # 2. 检查技术指标
    print('\n【2. 技术指标检查】')
    tech = data.get('technical', {})
    required_tech_fields = ['k', 'd', 'j', 'macd', 'rsi', 'ma5', 'ma10', 'ma20']
    for field in required_tech_fields:
        if field not in tech:
            issues.append(f'技术指标缺失: {field}')
            print(f'  ❌ 缺失: {field}')
        else:
            print(f'  ✓ {field}: {tech[field]:.2f}')
    
    # 3. 检查基本面
    print('\n【3. 基本面检查】')
    fund = data.get('fundamental', {})
    financial = fund.get('financial', {})
    latest = financial.get('latest', {})
    required_fund_fields = ['revenue', 'net_profit', 'roe', 'pe', 'pb']
    for field in required_fund_fields:
        if field not in latest:
            issues.append(f'基本面缺失: {field}')
            print(f'  ❌ 缺失: {field}')
        else:
            print(f'  ✓ {field}: {latest[field]}')
    
    # 4. 检查消息面
    print('\n【4. 消息面检查】')
    news = data.get('news', {})
    if not news:
        issues.append('消息面数据缺失')
        print('  ❌ 消息面数据缺失')
    else:
        print(f'  ✓ 情感评分: {news.get("sentiment_score", "N/A")}')
        print(f'  ✓ 新闻条数: {len(news.get("items", []))}')
    
    # 5. 检查资金面
    print('\n【5. 资金面检查】')
    money = data.get('money_flow', {})
    main_flow = money.get('main_flow', {})
    if 'main_net' not in main_flow:
        issues.append('资金面主力净流入缺失')
        print('  ❌ 主力净流入缺失')
    else:
        print(f'  ✓ 主力净流入: {main_flow["main_net"]}亿')
    
    flow_20d = money.get('flow_20d', [])
    print(f'  ✓ 20日资金数据: {len(flow_20d)}条')
    
    # 6. 检查形态面
    print('\n【6. 形态面检查】')
    if not pattern_data:
        issues.append('形态面数据缺失')
        print('  ❌ 形态面数据缺失')
    else:
        print(f'  ✓ K线数量: {pattern_data.get("kline_count", 0)}')
        candlestick = pattern_data.get('candlestick', {})
        print(f'  ✓ 看涨形态: {candlestick.get("bullish_count", 0)}')
        print(f'  ✓ 看跌形态: {candlestick.get("bearish_count", 0)}')
        
        chanlun = pattern_data.get('chanlun', {})
        print(f'  ✓ 缠论买点: {len(chanlun.get("buy_points", []))}')
        print(f'  ✓ 缠论卖点: {len(chanlun.get("sell_points", []))}')
        
        resonance = pattern_data.get('resonance', {})
        if resonance:
            if hasattr(resonance, 'total_score'):
                print(f'  ✓ 共振评分: {resonance.total_score}')
            else:
                issues.append('共振评分格式异常')
                print('  ❌ 共振评分格式异常')
    
    # 7. 检查建议数据
    print('\n【7. 建议数据检查】')
    suggestion = data.get('suggestion', {})
    required_sugg_fields = ['total_score', 'action', 'target_price', 'stop_loss', 'position']
    for field in required_sugg_fields:
        if field not in suggestion:
            issues.append(f'建议数据缺失: {field}')
            print(f'  ❌ 缺失: {field}')
        else:
            print(f'  ✓ {field}: {suggestion[field]}')
    
    # 汇总
    print('\n' + '='*60)
    print('审计结果汇总')
    print('='*60)
    if issues:
        print(f'发现 {len(issues)} 个问题:')
        for i, issue in enumerate(issues, 1):
            print(f'  {i}. {issue}')
    else:
        print('✓ 所有数据检查通过，无缺失字段')
    
    return len(issues) == 0

# 测试多只股票
stocks = [
    ('002402', '和而泰'),
    ('002149', '西部材料'),
    ('000001', '平安银行'),
]

print('\n开始批量数据审计...')
results = {}
for code, name in stocks:
    results[code] = audit_data(code, name)

print('\n' + '='*60)
print('批量审计结果')
print('='*60)
for code, name in stocks:
    status = '✓ 通过' if results[code] else '❌ 有问题'
    print(f'{code} {name}: {status}')
