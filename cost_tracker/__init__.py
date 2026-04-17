# -*- coding: utf-8 -*-
""" Token 成本追踪包

提供 LLM 调用的 Token 消耗追踪、统计和报告功能。

快速使用：
    from cost_tracker import get_tracker

    tracker = get_tracker()

    # 手动记录
    tracker.record(
        scene='pattern_analysis',
        model='gpt-4o-mini',
        prompt_tokens=1500,
        completion_tokens=800,
        stock_code='600519'
    )

    # 从 API 响应自动提取
    response = client.chat.completions.create(...)
    tracker.record_from_response('strategy', response, stock_code='000001')

    # 上下文管理器（自动追踪）
    with tracker.track('sentiment', model='gpt-4o-mini', stock_code='300750'):
        response = client.chat.completions.create(...)

    # 生成报告
    tracker.export_report_markdown('cost_report.md')
"""

from .tracker import (
    TokenTracker,
    TokenUsage,
    CostAlert,
    MODEL_PRICING,
    get_tracker,
)

__all__ = [
    'TokenTracker',
    'TokenUsage',
    'CostAlert',
    'MODEL_PRICING',
    'get_tracker',
]
