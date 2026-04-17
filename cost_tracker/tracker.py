# -*- coding: utf-8 -*-
""" Token 成本追踪器
借鉴 OpenClaw 的成本透明机制，追踪 LLM 调用的 Token 消耗。

功能：
1. 追踪每次 LLM 调用的 prompt_tokens / completion_tokens
2. 按模块/场景分类统计
3. 按日/周/月汇总
4. 生成成本报告（Markdown）
5. 成本告警（超过阈值时触发）
6. SQLite 持久化存储

支持追踪的场景：
- 形态分析（形态识别、缠论分析）
- 策略建议生成
- 情绪分析
- 数据增强
- 新闻摘要
"""

import json
import os
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 默认价格（每 1M tokens，单位：美元）
# GPT-4o: input $2.5, output $10
# GPT-4o-mini: input $0.15, output $0.60
# DeepSeek-V3: input $0.27, output $1.10
MODEL_PRICING = {
    'gpt-4o': {'input': 2.5, 'output': 10.0, 'currency': 'USD'},
    'gpt-4o-mini': {'input': 0.15, 'output': 0.60, 'currency': 'USD'},
    'gpt-4-turbo': {'input': 10.0, 'output': 30.0, 'currency': 'USD'},
    'gpt-3.5-turbo': {'input': 0.5, 'output': 1.5, 'currency': 'USD'},
    'deepseek-v3': {'input': 0.27, 'output': 1.10, 'currency': 'USD'},
    'deepseek-chat': {'input': 0.14, 'output': 0.28, 'currency': 'USD'},
    'qwen-plus': {'input': 0.8, 'output': 2.0, 'currency': 'USD'},
    'qwen-turbo': {'input': 0.3, 'output': 0.6, 'currency': 'USD'},
    'default': {'input': 1.0, 'output': 3.0, 'currency': 'USD'},
}


@dataclass
class TokenUsage:
    """单次 Token 使用记录"""
    id: Optional[int] = None
    timestamp: str = ''
    scene: str = ''           # 使用场景：pattern_analysis, strategy, sentiment, etc.
    model: str = 'default'
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    stock_code: str = ''       # 关联的股票代码（可选）
    extra: str = ''            # 额外备注（JSON）


@dataclass
class CostAlert:
    """成本告警"""
    threshold_daily_usd: float = 5.0       # 日成本阈值（美元）
    threshold_weekly_usd: float = 20.0     # 周成本阈值
    threshold_monthly_usd: float = 50.0    # 月成本阈值
    threshold_single_call_usd: float = 1.0 # 单次调用阈值


class TokenTracker:
    """Token 成本追踪器

    使用方式：
        tracker = TokenTracker()

        # 方式1：手动记录
        tracker.record(
            scene='pattern_analysis',
            model='gpt-4o-mini',
            prompt_tokens=1500,
            completion_tokens=800,
            stock_code='600519'
        )

        # 方式2：上下文管理器（自动追踪）
        with tracker.track('strategy', model='gpt-4o-mini', stock_code='000001'):
            result = llm.generate(prompt)

        # 生成报告
        report = tracker.get_cost_report()
        tracker.export_report_markdown('cost_report.md')
    """

    def __init__(self, db_path: str = './cost_tracker/token_usage.db'):
        self.db_path = db_path
        self.alert = CostAlert()
        self._current_context: Optional[TokenUsage] = None

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scene TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    latency_ms REAL DEFAULT 0.0,
                    stock_code TEXT DEFAULT '',
                    extra TEXT DEFAULT ''
                )
            ''')
            # 创建索引加速查询
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON token_usage(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scene ON token_usage(scene)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_model ON token_usage(model)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_stock_code ON token_usage(stock_code)')
            conn.commit()

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """计算成本（美元）"""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING['default'])
        input_cost = (prompt_tokens / 1_000_000) * pricing['input']
        output_cost = (completion_tokens / 1_000_000) * pricing['output']
        return round(input_cost + output_cost, 6)

    def record(
        self,
        scene: str,
        model: str = 'default',
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        stock_code: str = '',
        extra: Dict = None,
    ) -> TokenUsage:
        """记录一次 Token 使用

        Args:
            scene: 使用场景（pattern_analysis, strategy, sentiment, data_enhance, news_summary）
            model: 模型名称
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            latency_ms: 调用延迟（毫秒）
            stock_code: 关联股票代码
            extra: 额外信息字典

        Returns:
            TokenUsage 记录
        """
        total = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        usage = TokenUsage(
            timestamp=datetime.now().isoformat(),
            scene=scene,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            stock_code=stock_code,
            extra=json.dumps(extra, ensure_ascii=False) if extra else '',
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO token_usage
                (timestamp, scene, model, prompt_tokens, completion_tokens,
                 total_tokens, cost_usd, latency_ms, stock_code, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                usage.timestamp, usage.scene, usage.model,
                usage.prompt_tokens, usage.completion_tokens,
                usage.total_tokens, usage.cost_usd,
                usage.latency_ms, usage.stock_code, usage.extra,
            ))
            usage.id = cursor.lastrowid
            conn.commit()

        # 检查告警
        self._check_alerts(usage)

        logger.info(
            f"[TokenTracker] {scene}/{model} | "
            f"tokens: {total} (in:{prompt_tokens} out:{completion_tokens}) | "
            f"cost: ${cost:.4f} | latency: {latency_ms:.0f}ms"
        )

        return usage

    def record_from_response(self, scene: str, response: Any, stock_code: str = '', extra: Dict = None) -> TokenUsage:
        """从 OpenAI/兼容 API 响应自动提取 Token 使用量

        Args:
            scene: 使用场景
            response: OpenAI API 响应对象
            stock_code: 关联股票代码
            extra: 额外信息
        """
        model = getattr(response, 'model', 'default') or 'default'
        usage_obj = getattr(response, 'usage', None)

        if usage_obj:
            prompt_tokens = getattr(usage_obj, 'prompt_tokens', 0) or 0
            completion_tokens = getattr(usage_obj, 'completion_tokens', 0) or 0
        else:
            prompt_tokens = 0
            completion_tokens = 0

        # 尝试从 response 获取延迟
        latency_ms = 0.0

        return self.record(
            scene=scene,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            stock_code=stock_code,
            extra=extra,
        )

    @contextmanager
    def track(self, scene: str, model: str = 'default', stock_code: str = '', extra: Dict = None):
        """上下文管理器，自动追踪 LLM 调用

        用法：
            with tracker.track('pattern_analysis', model='gpt-4o-mini', stock_code='600519'):
                response = client.chat.completions.create(...)
                # 退出上下文时自动从 response 提取 token 数据
        """
        start_time = time.time()
        response_holder = {'response': None}

        try:
            yield response_holder
        finally:
            elapsed_ms = (time.time() - start_time) * 1000

            # 尝试从 holder 中的 response 自动提取
            resp = response_holder.get('response')
            if resp and hasattr(resp, 'usage'):
                self.record_from_response(scene, resp, stock_code, extra)
            else:
                # 没有 response，只记录耗时
                self.record(
                    scene=scene, model=model,
                    latency_ms=elapsed_ms,
                    stock_code=stock_code,
                    extra=extra or {'note': 'no_response_object'},
                )

    def _check_alerts(self, usage: TokenUsage):
        """检查成本告警"""
        if usage.cost_usd >= self.alert.threshold_single_call_usd:
            logger.warning(
                f"⚠️ 单次调用成本告警: {usage.scene}/{usage.model} "
                f"cost=${usage.cost_usd:.4f} (阈值: ${self.alert.threshold_single_call_usd})"
            )

        # 检查日成本
        daily = self.get_summary(period='daily')
        if daily and daily.get('total_cost', 0) >= self.alert.threshold_daily_usd:
            logger.warning(
                f"⚠️ 日成本告警: ${daily['total_cost']:.4f} "
                f"(阈值: ${self.alert.threshold_daily_usd})"
            )

    # ========== 查询接口 ==========

    def get_summary(self, period: str = 'daily', date: str = None) -> Optional[Dict]:
        """获取指定周期的成本汇总

        Args:
            period: 'daily' | 'weekly' | 'monthly'
            date: 指定日期（ISO格式），默认今天
        """
        now = datetime.now()
        if date:
            ref = datetime.fromisoformat(date)
        else:
            ref = now

        if period == 'daily':
            start = ref.replace(hour=0, minute=0, second=0).isoformat()
            end = ref.replace(hour=23, minute=59, second=59).isoformat()
        elif period == 'weekly':
            start = (ref - timedelta(days=ref.weekday())).replace(
                hour=0, minute=0, second=0).isoformat()
            end = ref.replace(hour=23, minute=59, second=59).isoformat()
        elif period == 'monthly':
            start = ref.replace(day=1, hour=0, minute=0, second=0).isoformat()
            end = ref.replace(hour=23, minute=59, second=59).isoformat()
        else:
            return None

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute('''
                SELECT
                    COUNT(*) as call_count,
                    COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COALESCE(AVG(latency_ms), 0) as avg_latency
                FROM token_usage
                WHERE timestamp >= ? AND timestamp <= ?
            ''', (start, end)).fetchone()

        if row and row[0] > 0:
            return {
                'period': period,
                'date': ref.strftime('%Y-%m-%d'),
                'call_count': row[0],
                'prompt_tokens': row[1],
                'completion_tokens': row[2],
                'total_tokens': row[3],
                'total_cost': round(row[4], 4),
                'avg_latency_ms': round(row[5], 1),
                'avg_cost_per_call': round(row[4] / row[0], 4) if row[0] > 0 else 0,
            }
        return None

    def get_summary_by_scene(self, period: str = 'daily') -> List[Dict]:
        """按场景分组的成本汇总"""
        now = datetime.now()
        if period == 'daily':
            start = now.replace(hour=0, minute=0, second=0).isoformat()
        elif period == 'weekly':
            start = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0).isoformat()
        elif period == 'monthly':
            start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
        else:
            start = now.replace(hour=0, minute=0, second=0).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT
                    scene,
                    COUNT(*) as call_count,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(latency_ms) as avg_latency
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY scene
                ORDER BY total_cost DESC
            ''', (start,)).fetchall()

        return [
            {
                'scene': r[0],
                'call_count': r[1],
                'total_tokens': r[2],
                'total_cost': round(r[3], 4),
                'avg_latency_ms': round(r[4], 1),
            }
            for r in rows if r[0]
        ]

    def get_summary_by_model(self, period: str = 'daily') -> List[Dict]:
        """按模型分组的成本汇总"""
        now = datetime.now()
        if period == 'daily':
            start = now.replace(hour=0, minute=0, second=0).isoformat()
        elif period == 'weekly':
            start = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0).isoformat()
        elif period == 'monthly':
            start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
        else:
            start = now.replace(hour=0, minute=0, second=0).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT
                    model,
                    COUNT(*) as call_count,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(latency_ms) as avg_latency
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY total_cost DESC
            ''', (start,)).fetchall()

        return [
            {
                'model': r[0],
                'call_count': r[1],
                'total_tokens': r[2],
                'total_cost': round(r[3], 4),
                'avg_latency_ms': round(r[4], 1),
            }
            for r in rows if r[0]
        ]

    def get_recent_calls(self, limit: int = 20) -> List[Dict]:
        """获取最近的调用记录"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT id, timestamp, scene, model, prompt_tokens,
                       completion_tokens, total_tokens, cost_usd,
                       latency_ms, stock_code
                FROM token_usage
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        return [
            {
                'id': r[0], 'timestamp': r[1], 'scene': r[2], 'model': r[3],
                'prompt_tokens': r[4], 'completion_tokens': r[5],
                'total_tokens': r[6], 'cost_usd': round(r[7], 4),
                'latency_ms': r[8], 'stock_code': r[9],
            }
            for r in rows
        ]

    def get_daily_trend(self, days: int = 30) -> List[Dict]:
        """获取每日成本趋势"""
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as call_count,
                    SUM(total_tokens) as total_tokens,
                    ROUND(SUM(cost_usd), 4) as total_cost
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''', (start,)).fetchall()

        return [
            {'date': r[0], 'call_count': r[1],
             'total_tokens': r[2], 'total_cost': r[3]}
            for r in rows
        ]

    # ========== 报告生成 ==========

    def get_cost_report(self, days: int = 7) -> Dict:
        """生成完整成本报告"""
        daily = self.get_summary('daily')
        weekly = self.get_summary('weekly')
        monthly = self.get_summary('monthly')
        by_scene = self.get_summary_by_scene('weekly')
        by_model = self.get_summary_by_model('weekly')
        trend = self.get_daily_trend(days)
        recent = self.get_recent_calls(10)

        return {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'daily': daily,
            'weekly': weekly,
            'monthly': monthly,
            'by_scene': by_scene,
            'by_model': by_model,
            'daily_trend': trend,
            'recent_calls': recent,
            'alerts': {
                'daily_threshold': self.alert.threshold_daily_usd,
                'weekly_threshold': self.alert.threshold_weekly_usd,
                'monthly_threshold': self.alert.threshold_monthly_usd,
                'daily_exceeded': daily and daily['total_cost'] >= self.alert.threshold_daily_usd,
                'weekly_exceeded': weekly and weekly['total_cost'] >= self.alert.threshold_weekly_usd,
            },
        }

    def export_report_markdown(self, filepath: str = 'cost_report.md', days: int = 7):
        """导出 Markdown 格式成本报告"""
        report = self.get_cost_report(days)

        lines = [
            f"# 💰 Token 成本报告",
            f"",
            f"> 生成时间：{report['generated_at']}",
            f"> 统计周期：近 {days} 天",
            f"",
            f"## 📊 成本概览",
            f"",
        ]

        # 概览表格
        lines.append("| 周期 | 调用次数 | Token 总量 | 总成本 | 平均延迟 |")
        lines.append("|------|---------|-----------|--------|---------|")
        for label, data in [("今日", report['daily']), ("本周", report['weekly']), ("本月", report['monthly'])]:
            if data:
                lines.append(
                    f"| {label} | {data['call_count']} | {data['total_tokens']:,} "
                    f"| ${data['total_cost']:.4f} | {data['avg_latency_ms']:.0f}ms |"
                )
            else:
                lines.append(f"| {label} | 0 | 0 | $0 | - |")

        # 按场景
        if report['by_scene']:
            lines += ["", "## 🎯 按场景分布", ""]
            lines.append("| 场景 | 调用次数 | Token 总量 | 总成本 | 平均延迟 |")
            lines.append("|------|---------|-----------|--------|---------|")
            for s in report['by_scene']:
                lines.append(
                    f"| {s['scene']} | {s['call_count']} | {s['total_tokens']:,} "
                    f"| ${s['total_cost']:.4f} | {s['avg_latency_ms']:.0f}ms |"
                )

        # 按模型
        if report['by_model']:
            lines += ["", "## 🤖 按模型分布", ""]
            lines.append("| 模型 | 调用次数 | Token 总量 | 总成本 | 平均延迟 |")
            lines.append("|------|---------|-----------|--------|---------|")
            for m in report['by_model']:
                lines.append(
                    f"| {m['model']} | {m['call_count']} | {m['total_tokens']:,} "
                    f"| ${m['total_cost']:.4f} | {m['avg_latency_ms']:.0f}ms |"
                )

        # 每日趋势
        if report['daily_trend']:
            lines += ["", "## 📈 每日趋势", ""]
            lines.append("| 日期 | 调用次数 | Token 总量 | 总成本 |")
            lines.append("|------|---------|-----------|--------|")
            for d in report['daily_trend'][:14]:  # 最多显示14天
                lines.append(
                    f"| {d['date']} | {d['call_count']} | "
                    f"{d['total_tokens']:,} | ${d['total_cost']:.4f} |"
                )

        # 告警状态
        alerts = report['alerts']
        lines += ["", "## 🔔 告警状态", ""]
        if alerts['daily_exceeded']:
            lines.append(f"⚠️ **日成本超限**: ${report['daily']['total_cost']:.4f} / ${alerts['daily_threshold']}")
        else:
            lines.append(f"✅ 日成本正常: ${report['daily']['total_cost']:.4f if report['daily'] else 0} / ${alerts['daily_threshold']}")

        if alerts['weekly_exceeded']:
            lines.append(f"⚠️ **周成本超限**: ${report['weekly']['total_cost']:.4f} / ${alerts['weekly_threshold']}")
        else:
            lines.append(f"✅ 周成本正常: ${report['weekly']['total_cost']:.4f if report['weekly'] else 0} / ${alerts['weekly_threshold']}")

        # 最近调用
        if report['recent_calls']:
            lines += ["", "## 📋 最近调用", ""]
            lines.append("| 时间 | 场景 | 模型 | Tokens | 成本 | 延迟 | 股票 |")
            lines.append("|------|------|------|--------|------|------|------|")
            for c in report['recent_calls']:
                ts = c['timestamp'][:16].replace('T', ' ')
                lines.append(
                    f"| {ts} | {c['scene']} | {c['model']} | {c['total_tokens']:,} "
                    f"| ${c['cost_usd']:.4f} | {c['latency_ms']:.0f}ms | {c['stock_code'] or '-'} |"
                )

        lines += ["", "---", f"_报告由 TokenTracker 自动生成_", ""]

        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"成本报告已导出: {filepath}")
        return filepath


# 便捷实例（模块级单例）
_default_tracker: Optional[TokenTracker] = None


def get_tracker(db_path: str = None) -> TokenTracker:
    """获取全局 TokenTracker 实例"""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = TokenTracker(db_path or './cost_tracker/token_usage.db')
    return _default_tracker
