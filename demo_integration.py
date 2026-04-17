# -*- coding: utf-8 -*-
""" 集成演示：多数据源降级 + Token 成本追踪

演示如何在 stock_analyzer 中集成两个新模块。

运行方式：
    python demo_integration.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def demo_fallback():
    """演示多数据源降级"""
    print("=" * 60)
    print("📋 演示1: 多数据源降级策略")
    print("=" * 60)

    from data_adapter import (
        FallbackManagerV2, RetryConfig, CircuitBreakerConfig,
        AkShareSource, BaostockSource, LocalCacheSource
    )

    # 创建降级管理器（自定义配置）
    manager = FallbackManagerV2(
        cache_dir='./cache',
        retry_config=RetryConfig(max_retries=2, base_delay=1.0, jitter=True),
        circuit_config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
        ),
    )

    # 注册数据源（优先级：AkShare > Baostock > 本地缓存）
    manager.register_source('akshare', AkShareSource(), priority=0)
    manager.register_source('baostock', BaostockSource(), priority=10)
    manager.register_source('local_cache', LocalCacheSource(cache_dir='./cache'), priority=999)

    print("\n已注册数据源:")
    for name, info in manager.sources.items():
        print(f"  - {name} (优先级: {info['priority']})")

    # 演示获取行情（带降级）
    print("\n尝试获取 600519 (贵州茅台) 行情...")
    result = manager.get_data('quote', '600519')

    if result:
        source = result.get('meta', {}).get('source', 'unknown')
        from_cache = result.get('meta', {}).get('from_cache', False)
        print(f"  ✅ 成功 | 数据源: {source} | 缓存: {'是' if from_cache else '否'}")
        if 'price' in result:
            print(f"  💰 价格: {result['price']}")
            print(f"  📈 涨跌幅: {result.get('change_pct', 'N/A')}%")
    else:
        print("  ❌ 所有数据源都不可用")

    # 查看数据源状态
    print("\n数据源状态:")
    status = manager.get_source_status()
    for name, info in status.items():
        icon = "🟢" if info['status'] == 'active' else "🔴"
        print(f"  {icon} {name}: {info['status']} "
              f"(成功: {info['success_count']}, 失败: {info['fail_count']}, "
              f"成功率: {info['success_rate']}%)")

    return manager


def demo_token_tracker():
    """演示 Token 成本追踪"""
    print("\n" + "=" * 60)
    print("💰 演示2: Token 成本追踪")
    print("=" * 60)

    from cost_tracker import get_tracker, MODEL_PRICING

    tracker = get_tracker('./cost_tracker/demo_usage.db')

    # 模拟不同场景的 LLM 调用
    scenarios = [
        ('pattern_analysis', 'gpt-4o-mini', 2000, 1200, 800, '600519'),
        ('strategy', 'gpt-4o-mini', 3500, 2000, 1200, '600519'),
        ('sentiment', 'deepseek-chat', 1500, 600, 500, '000001'),
        ('data_enhance', 'gpt-4o-mini', 800, 400, 300, '300750'),
        ('news_summary', 'deepseek-chat', 2500, 1000, 900, '600519'),
        ('pattern_analysis', 'gpt-4o', 3000, 1500, 2000, '000001'),
    ]

    print("\n模拟 LLM 调用:")
    print("-" * 70)
    print(f"{'场景':<20} {'模型':<15} {'Input':>7} {'Output':>7} {'成本':>10}")
    print("-" * 70)

    for scene, model, p_tok, c_tok, lat, code in scenarios:
        usage = tracker.record(
            scene=scene,
            model=model,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            latency_ms=lat,
            stock_code=code,
        )
        print(f"{scene:<20} {model:<15} {p_tok:>7,} {c_tok:>7,} ${usage.cost_usd:>9.4f}")

    print("-" * 70)

    # 查看今日汇总
    daily = tracker.get_summary('daily')
    if daily:
        print(f"\n📊 今日汇总:")
        print(f"  调用次数: {daily['call_count']}")
        print(f"  Token 总量: {daily['total_tokens']:,}")
        print(f"  总成本: ${daily['total_cost']:.4f}")
        print(f"  平均每次: ${daily['avg_cost_per_call']:.4f}")
        print(f"  平均延迟: {daily['avg_latency_ms']:.0f}ms")

    # 按场景分布
    by_scene = tracker.get_summary_by_scene('daily')
    if by_scene:
        print(f"\n🎯 按场景分布:")
        for s in by_scene:
            print(f"  {s['scene']:<20} {s['call_count']:>3}次  "
                  f"{s['total_tokens']:>8,} tokens  ${s['total_cost']:.4f}")

    # 按模型分布
    by_model = tracker.get_summary_by_model('daily')
    if by_model:
        print(f"\n🤖 按模型分布:")
        for m in by_model:
            print(f"  {m['model']:<15} {m['call_count']:>3}次  "
                  f"{m['total_tokens']:>8,} tokens  ${m['total_cost']:.4f}")

    return tracker


def demo_integration():
    """演示两个模块的集成使用"""
    print("\n" + "=" * 60)
    print("🔗 演示3: 两个模块集成")
    print("=" * 60)

    from cost_tracker import get_tracker

    tracker = get_tracker('./cost_tracker/demo_usage.db')

    # 场景：分析一只股票，全程追踪 Token 成本
    print("\n模拟完整分析流程（含成本追踪）:")

    # Step 1: 获取数据（降级链路保障）
    print("  [1] 获取行情数据 → 走降级链路")
    # Step 2: 技术分析（本地计算，无 Token 消耗）
    print("  [2] 计算技术指标 → 本地计算")
    # Step 3: 形态分析（LLM 调用）
    usage1 = tracker.record(
        scene='pattern_analysis', model='gpt-4o-mini',
        prompt_tokens=2500, completion_tokens=1500,
        latency_ms=1200, stock_code='600519',
        extra={'patterns_detected': 3, 'top_pattern': 'macd_golden_cross'}
    )
    print(f"  [3] K线形态分析 → ${usage1.cost_usd:.4f} ({usage1.total_tokens} tokens)")

    # Step 4: 策略生成（LLM 调用）
    usage2 = tracker.record(
        scene='strategy', model='gpt-4o-mini',
        prompt_tokens=4000, completion_tokens=2000,
        latency_ms=1800, stock_code='600519',
        extra={'suggestion': '观望', 'score': 65}
    )
    print(f"  [4] 策略建议生成 → ${usage2.cost_usd:.4f} ({usage2.total_tokens} tokens)")

    # Step 5: 情绪分析（LLM 调用）
    usage3 = tracker.record(
        scene='sentiment', model='deepseek-chat',
        prompt_tokens=1800, completion_tokens=800,
        latency_ms=600, stock_code='600519',
        extra={'greed_fear_index': 45}
    )
    print(f"  [5] 情绪指数计算 → ${usage3.cost_usd:.4f} ({usage3.total_tokens} tokens)")

    total_cost = usage1.cost_usd + usage2.cost_usd + usage3.cost_usd
    total_tokens = usage1.total_tokens + usage2.total_tokens + usage3.total_tokens
    print(f"\n  📊 本次分析总成本: ${total_cost:.4f} ({total_tokens:,} tokens)")

    # 导出报告
    print("\n生成成本报告...")
    report_path = tracker.export_report_markdown(
        './cost_tracker/demo_report.md', days=30
    )
    print(f"  📄 报告已保存: {report_path}")


def demo_model_pricing():
    """展示支持的模型定价"""
    print("\n" + "=" * 60)
    print("💵 支持的模型定价 (每 1M tokens)")
    print("=" * 60)

    from cost_tracker import MODEL_PRICING

    print(f"\n{'模型':<20} {'输入价格':>12} {'输出价格':>12}")
    print("-" * 46)
    for model, pricing in MODEL_PRICING.items():
        if model == 'default':
            continue
        print(f"{model:<20} ${pricing['input']:>10.2f} ${pricing['output']:>10.2f}")


if __name__ == '__main__':
    demo_model_pricing()
    demo_fallback()
    demo_token_tracker()
    demo_integration()

    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)
    print("\n文件结构：")
    print("  data_adapter/")
    print("    ├── __init__.py          # 包导出")
    print("    ├── sources.py           # 数据源实现 (AkShare/Baostock/Sina/Cache)")
    print("    └── fallback.py          # 降级管理器 V2 (重试/熔断/指标)")
    print("  cost_tracker/")
    print("    ├── __init__.py          # 包导出")
    print("    ├── tracker.py           # Token 成本追踪器 (SQLite/报告/告警)")
    print("    └── demo_usage.db        # 运行后自动生成")
    print("    └── demo_report.md       # 成本报告（运行后自动生成）")
