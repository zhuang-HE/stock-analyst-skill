# -*- coding: utf-8 -*-
"""
数据适配层使用示例

演示如何使用 data_adapter 获取完整数据并生成报告
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data_adapter import DataAdapter, get_stock_analysis_data
from templates.unified_report_template import generate_unified_report


def example1_basic_usage():
    """示例1：基础用法"""
    print("="*60)
    print("示例1：基础用法 - 一键获取完整数据")
    print("="*60)
    
    # 创建适配器
    adapter = DataAdapter()
    
    # 获取完整数据
    code = '002402'
    stock_name = '和而泰'
    
    print(f"\n正在获取 {code} {stock_name} 的数据...")
    data, pattern_data = adapter.get_complete_data(code, stock_name)
    
    print(f"\n数据获取完成！")
    print(f"- 股票代码: {data['code']}")
    print(f"- 股票名称: {data['stock_name']}")
    print(f"- 数据时间: {data['timestamp']}")
    
    # 检查各模块数据
    print("\n数据完整性检查:")
    print(f"- 行情数据: {'[OK]' if data.get('quote') else '[缺失]'}")
    print(f"- 技术指标: {'[OK]' if data.get('technical') else '[缺失]'}")
    print(f"- 基本面: {'[OK]' if data.get('fundamental') else '[缺失]'}")
    print(f"- 消息面: {'[OK]' if data.get('news') else '[缺失]'}")
    print(f"- 资金面: {'[OK]' if data.get('money_flow') else '[缺失]'}")
    print(f"- 形态面: {'[OK]' if pattern_data else '[缺失]'}")
    
    return data, pattern_data


def example2_generate_report(data, pattern_data):
    """示例2：生成报告"""
    print("\n" + "="*60)
    print("示例2：生成分析报告")
    print("="*60)
    
    # 生成Markdown报告
    print("\n生成Markdown报告...")
    report = generate_unified_report(data, pattern_data, output_format='markdown')
    
    # 保存报告
    output_file = f"report_{data['code']}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report['markdown'])
    
    print(f"报告已保存: {output_file}")
    
    # 显示报告预览（过滤掉emoji避免编码问题）
    print("\n报告预览（前1000字符）:")
    preview = report['markdown'][:1000]
    # 移除emoji字符
    import re
    preview_clean = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\n\r\t]', '', preview)
    print(preview_clean)
    print("\n...")
    
    return report


def example3_convenient_function():
    """示例3：使用便捷函数"""
    print("\n" + "="*60)
    print("示例3：使用便捷函数")
    print("="*60)
    
    # 一行代码获取数据
    data, pattern_data = get_stock_analysis_data('000001', '平安银行')
    
    print(f"\n获取到 {data['stock_name']} 的数据")
    print(f"综合评分: {data['suggestion']['total_score']}")
    print(f"操作建议: {data['suggestion']['action']}")
    
    return data, pattern_data


def example4_with_fallback():
    """示例4：多数据源备用"""
    print("\n" + "="*60)
    print("示例4：多数据源备用")
    print("="*60)
    
    from data_adapter import FallbackManager
    from data_adapter.sources import AkShareSource, TushareSource, LocalCacheSource
    
    # 创建备用管理器
    manager = FallbackManager()
    
    # 注册多个数据源
    manager.register_source('akshare', AkShareSource(), priority=0)
    # manager.register_source('tushare', TushareSource(token='your_token'), priority=1)
    manager.register_source('local_cache', LocalCacheSource(), priority=999)
    
    # 获取数据（自动切换备用源）
    result = manager.get_data_with_fallback('quote', '002402')
    
    print(f"\n数据源: {result['source']}")
    print(f"状态: {result['status']}")
    if result.get('is_fallback'):
        print("注意: 使用了备用数据源")
    
    if result['data']:
        print(f"数据: {result['data']}")
    
    # 查看数据源状态
    print("\n数据源状态:")
    for name, status in manager.get_source_status().items():
        print(f"- {name}: {status['status']} (成功{status['success_count']}/失败{status['fail_count']})")


def example5_custom_data():
    """示例5：使用自定义数据"""
    print("\n" + "="*60)
    print("示例5：使用自定义数据（从finance-data-retrieval获取）")
    print("="*60)
    
    # 假设你从finance-data-retrieval获取了原始数据
    raw_data = {
        'quote': {
            'price': 31.91,
            'pct_change': 1.88,
            'volume': 2690000,
            'pe': 80.99,
            'pb': 5.62
        },
        'klines': []  # K线数据列表
    }
    
    # 使用适配器转换
    adapter = DataAdapter()
    
    # 手动构建数据（如果你有部分数据）
    data = {
        'code': '002402',
        'stock_name': '和而泰',
        'timestamp': '2026-04-17 03:45:00',
        'quote': raw_data['quote'],
        'technical': adapter._calculate_technical_indicators(raw_data['klines']) if raw_data['klines'] else {},
        'fundamental': {},  # 从finance-data-retrieval获取
        'news': {},  # 从finance-data-retrieval获取
        'money_flow': {},  # 从finance-data-retrieval获取
        'suggestion': {
            'total_score': 41,
            'action': '观望',
            'target_price': 34.0,
            'stop_loss': 29.5
        }
    }
    
    # 形态面分析
    pattern_data = None
    if raw_data['klines']:
        pattern_data = adapter._analyze_patterns(raw_data['klines'], data['technical'])
    
    # 生成报告
    report = generate_unified_report(data, pattern_data, output_format='text')
    print("\n生成文本报告:")
    text = report.get('text', report.get('markdown', '无报告'))
    # 移除特殊字符避免编码问题
    import re
    text_clean = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\n\r\t]', '', text)
    print(text_clean[:500])
    print("...")


def main():
    """主函数"""
    print("Stock Analyst 数据适配层使用示例")
    print("="*60)
    
    # 运行示例
    try:
        # 示例1：基础用法
        data, pattern_data = example1_basic_usage()
        
        # 示例2：生成报告
        if data:
            example2_generate_report(data, pattern_data)
        
        # 示例3：便捷函数
        example3_convenient_function()
        
        # 示例4：多数据源备用
        example4_with_fallback()
        
        # 示例5：自定义数据
        example5_custom_data()
        
    except Exception as e:
        print(f"\n运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("示例运行完成！")
    print("="*60)


if __name__ == '__main__':
    main()
