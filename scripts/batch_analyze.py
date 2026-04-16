# -*- coding: utf-8 -*-
"""
批量分析脚本 - 支持GitHub Actions定时执行
分析多只股票并生成报告
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from full_analysis import StockFullAnalyzer
from market_regime import MarketAnalyzer
from templates.dashboard_template import format_dashboard


def parse_stock_list(stock_str: str) -> List[str]:
    """解析股票列表字符串"""
    if not stock_str:
        return []
    
    stocks = []
    for item in stock_str.split(','):
        item = item.strip()
        if item:
            stocks.append(item)
    
    return stocks


def analyze_single_stock(code: str, analyzer: StockFullAnalyzer) -> Dict[str, Any]:
    """分析单只股票"""
    print(f"正在分析: {code}")
    
    try:
        result = analyzer.get_full_analysis(code)
        
        if result.get('success'):
            # 格式化输出
            dashboard = format_dashboard(result)
            result['dashboard'] = dashboard
            print(f"✅ {code} 分析完成")
        else:
            print(f"❌ {code} 分析失败: {result.get('error', '未知错误')}")
        
        return result
        
    except Exception as e:
        print(f"❌ {code} 分析异常: {str(e)}")
        return {
            'code': code,
            'success': False,
            'error': str(e)
        }


def generate_market_report(output_dir: str) -> str:
    """生成市场报告"""
    print("正在生成市场环境报告...")
    
    analyzer = MarketAnalyzer()
    report = analyzer.get_market_summary()
    
    # 保存报告
    date_str = datetime.now().strftime('%Y-%m-%d')
    report_path = Path(output_dir) / f"market_regime_{date_str}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 市场报告已保存: {report_path}")
    return report


def generate_summary_report(results: List[Dict], output_dir: str):
    """生成汇总报告"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r.get('success'))
    failed = total - success
    
    # 分类统计
    buy_count = 0
    hold_count = 0
    sell_count = 0
    
    scores = []
    for r in results:
        if r.get('success'):
            suggestion = r.get('suggestion', {})
            action = suggestion.get('action', '观望')
            score = suggestion.get('total_score', 50)
            scores.append(score)
            
            if '买入' in action:
                buy_count += 1
            elif '卖出' in action:
                sell_count += 1
            else:
                hold_count += 1
    
    avg_score = sum(scores) / len(scores) if scores else 50
    
    # 生成汇总报告
    lines = [
        f"# 📊 股票分析汇总报告 - {date_str}",
        "",
        "## 分析概况",
        "",
        f"- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **股票总数**: {total}",
        f"- **成功分析**: {success}",
        f"- **分析失败**: {failed}",
        f"- **平均评分**: {avg_score:.1f}",
        "",
        "## 操作建议分布",
        "",
        f"- 🟢 **建议买入**: {buy_count} 只",
        f"- 🟡 **建议观望**: {hold_count} 只",
        f"- 🔴 **建议卖出**: {sell_count} 只",
        "",
        "## 详细结果",
        "",
        "| 股票代码 | 股票名称 | 综合评分 | 操作建议 | 目标价 | 止损价 |",
        "|---------|---------|---------|---------|--------|--------|"
    ]
    
    for r in results:
        if r.get('success'):
            code = r.get('code', '')
            name = r.get('stock_name', '')
            suggestion = r.get('suggestion', {})
            score = suggestion.get('total_score', 0)
            action = suggestion.get('action', '观望')
            target = suggestion.get('target_price', 0)
            stop = suggestion.get('stop_loss', 0)
            
            lines.append(f"| {code} | {name} | {score} | {action} | {target} | {stop} |")
    
    lines.extend([
        "",
        "## 评分排名（Top 10）",
        ""
    ])
    
    # 排序并取前10
    sorted_results = sorted(
        [r for r in results if r.get('success')],
        key=lambda x: x.get('suggestion', {}).get('total_score', 0),
        reverse=True
    )[:10]
    
    for i, r in enumerate(sorted_results, 1):
        code = r.get('code', '')
        name = r.get('stock_name', '')
        score = r.get('suggestion', {}).get('total_score', 0)
        action = r.get('suggestion', {}).get('action', '观望')
        lines.append(f"{i}. **{name}** ({code}) - 评分: {score} - {action}")
    
    lines.extend([
        "",
        "---",
        "",
        "*免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。*"
    ])
    
    # 保存汇总报告
    summary_path = Path(output_dir) / f"summary_{date_str}.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ 汇总报告已保存: {summary_path}")
    return summary_path


def generate_notification_json(results: List[Dict], output_dir: str):
    """生成通知用的JSON文件"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 统计
    success_count = sum(1 for r in results if r.get('success'))
    
    # 取评分最高的3只
    top_stocks = sorted(
        [r for r in results if r.get('success')],
        key=lambda x: x.get('suggestion', {}).get('total_score', 0),
        reverse=True
    )[:3]
    
    notification = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"""📊 **股票每日分析报告** - {date_str}

分析完成：**{success_count}** 只股票

🏆 **今日推荐 Top 3：**
{"".join([f"{i+1}. {r.get('stock_name', '')}({r.get('code', '')}) - 评分{r.get('suggestion', {}).get('total_score', 0)} - {r.get('suggestion', {}).get('action', '')}\\n" for i, r in enumerate(top_stocks)])}

📈 详细报告请查看附件

---
⚠️ 免责声明：本报告仅供参考，不构成投资建议
"""
        }
    }
    
    # 保存通知JSON
    notif_path = Path(output_dir) / "notification.json"
    with open(notif_path, 'w', encoding='utf-8') as f:
        json.dump(notification, f, ensure_ascii=False, indent=2)
    
    # Discord格式
    discord_embed = {
        "embeds": [{
            "title": f"📊 股票每日分析报告 - {date_str}",
            "description": f"分析完成：**{success_count}** 只股票",
            "color": 3447003,
            "fields": [
                {
                    "name": "🏆 今日推荐 Top 3",
                    "value": "\\n".join([
                        f"{i+1}. {r.get('stock_name', '')}({r.get('code', '')}) - 评分{r.get('suggestion', {}).get('total_score', 0)}"
                        for i, r in enumerate(top_stocks)
                    ]),
                    "inline": False
                }
            ],
            "footer": {
                "text": "免责声明：本报告仅供参考，不构成投资建议"
            }
        }]
    }
    
    discord_path = Path(output_dir) / "notification_discord.json"
    with open(discord_path, 'w', encoding='utf-8') as f:
        json.dump(discord_embed, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 通知文件已生成")


def main():
    parser = argparse.ArgumentParser(description='批量股票分析')
    parser.add_argument('--stocks', type=str, default='', help='股票列表，逗号分隔')
    parser.add_argument('--output-dir', type=str, default='./reports', help='输出目录')
    parser.add_argument('--type', type=str, default='full', 
                       choices=['full', 'quick', 'market_only'],
                       help='分析类型')
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取股票列表
    stock_list_str = args.stocks or os.getenv('STOCK_LIST', '')
    
    # 默认股票列表
    default_stocks = [
        '000001',   # 平安银行
        '600519',   # 贵州茅台
        '300750',   # 宁德时代
        '002149',   # 西部材料
        '002402',   # 和而泰
    ]
    
    if stock_list_str:
        stock_list = parse_stock_list(stock_list_str)
    else:
        stock_list = default_stocks
        print(f"使用默认股票列表: {stock_list}")
    
    if not stock_list:
        print("错误: 未指定股票列表")
        return 1
    
    print(f"\n{'='*60}")
    print(f"开始批量分析 - 共 {len(stock_list)} 只股票")
    print(f"{'='*60}\\n")
    
    # 市场环境分析
    if args.type in ['full', 'market_only']:
        market_report = generate_market_report(str(output_dir))
        print("\\n" + market_report)
    
    if args.type == 'market_only':
        print("\\n仅执行市场环境分析，跳过个股分析")
        return 0
    
    # 个股分析
    analyzer = StockFullAnalyzer()
    results = []
    
    for code in stock_list:
        result = analyze_single_stock(code, analyzer)
        results.append(result)
        
        # 保存单个报告
        if result.get('success') and 'dashboard' in result:
            date_str = datetime.now().strftime('%Y-%m-%d')
            report_path = output_dir / f"{code}_{date_str}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(result['dashboard'])
    
    print(f"\\n{'='*60}")
    print("生成汇总报告...")
    print(f"{'='*60}\\n")
    
    # 生成汇总报告
    generate_summary_report(results, str(output_dir))
    
    # 生成通知文件
    generate_notification_json(results, str(output_dir))
    
    print(f"\\n{'='*60}")
    print(f"分析完成！报告已保存到: {output_dir}")
    print(f"{'='*60}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
