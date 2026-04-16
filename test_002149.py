# -*- coding: utf-8 -*-
"""使用002149测试数据适配层"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from data_adapter import DataAdapter
from templates.unified_report_template import generate_unified_report
import json

# 创建适配器
adapter = DataAdapter()

# 获取002149完整数据
print('正在获取 002149 西部材料 的完整数据...')
data, pattern_data = adapter.get_complete_data('002149', '西部材料')

print('\n数据完整性检查:')
print('- 行情数据:', '[OK]' if data.get('quote') else '[缺失]')
print('- 技术指标:', '[OK]' if data.get('technical') else '[缺失]')
print('- 基本面:', '[OK]' if data.get('fundamental') else '[缺失]')
print('- 消息面:', '[OK]' if data.get('news') else '[缺失]')
print('- 资金面:', '[OK]' if data.get('money_flow') else '[缺失]')
print('- 形态面:', '[OK]' if pattern_data else '[缺失]')

if pattern_data:
    print('  - K线数量:', pattern_data.get('kline_count', 0))
    candlestick = pattern_data.get('candlestick', {})
    if candlestick:
        print('  - 识别形态:', candlestick.get('bullish_count', 0), '看涨 /', candlestick.get('bearish_count', 0), '看跌')
        patterns = candlestick.get('patterns', [])
        if patterns:
            print('  - 形态详情:')
            for p in patterns[:3]:
                print(f'    - {p.name_cn} (可靠性:{p.reliability}/5)')
    
    chanlun = pattern_data.get('chanlun', {})
    if chanlun:
        print('  - 缠论买点:', len(chanlun.get('buy_points', [])), '个')
        print('  - 缠论卖点:', len(chanlun.get('sell_points', [])), '个')
    
    resonance = pattern_data.get('resonance', {})
    if resonance:
        if hasattr(resonance, 'total_score'):
            print('  - 共振评分:', f'{resonance.total_score:+.0f}分')
            print('  - 共振级别:', resonance.resonance_level)

# 生成报告
print('\n生成报告...')
report = generate_unified_report(data, pattern_data, output_format='text')
print('报告生成成功!')
text_len = len(report.get('text', ''))
print(f'报告长度: {text_len} 字符')

# 显示报告
print('\n' + '='*60)
print('报告内容:')
print('='*60)
text = report.get('text', '')
import re
text_clean = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\n\r\t]', '', text)
print(text_clean)
