# -*- coding: utf-8 -*-
"""测试数据适配层"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from data_adapter import DataAdapter
from templates.unified_report_template import generate_unified_report

# 创建适配器
adapter = DataAdapter()

# 获取完整数据
data, pattern_data = adapter.get_complete_data('002402', '和尔泰')

print('数据完整性检查:')
print('- 行情数据: [OK]' if data.get('quote') else '- 行情数据: [缺失]')
print('- 技术指标: [OK]' if data.get('technical') else '- 技术指标: [缺失]')
print('- 基本面: [OK]' if data.get('fundamental') else '- 基本面: [缺失]')
print('- 消息面: [OK]' if data.get('news') else '- 消息面: [缺失]')
print('- 资金面: [OK]' if data.get('money_flow') else '- 资金面: [缺失]')
print('- 形态面: [OK]' if pattern_data else '- 形态面: [缺失]')

if pattern_data:
    print('  - K线数量:', pattern_data.get('kline_count', 0))
    candlestick = pattern_data.get('candlestick', {})
    print('  - 识别形态:', candlestick.get('bullish_count', 0), '看涨 /', candlestick.get('bearish_count', 0), '看跌')

# 生成报告
report = generate_unified_report(data, pattern_data, output_format='text')
print('\n报告生成成功!')
print('报告长度:', len(report.get('text', '')), '字符')

# 显示报告内容
print('\n' + '='*60)
print('报告内容:')
print('='*60)
text = report.get('text', '')
# 移除emoji避免编码问题
import re
text_clean = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\n\r\t]', '', text)
print(text_clean)
