# -*- coding: utf-8 -*-
"""
交易纪律检查模块 - 硬编码交易规则
借鉴 daily_stock_analysis 的内置交易纪律

规则：
1. 严禁追高 - 乖离率检查
2. 趋势交易 - 均线多头排列
3. 精确点位 - 买入/止损/目标价
4. 仓位管理 - 动态仓位建议
5. 新闻时效 - 消息 freshness
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CheckStatus(Enum):
    """检查状态"""
    PASS = "✅ 满足"
    WARNING = "⚠️ 注意"
    FAIL = "❌ 不满足"


@dataclass
class DisciplineCheck:
    """纪律检查项"""
    rule_name: str
    status: CheckStatus
    detail: str
    suggestion: str


class TradingDiscipline:
    """交易纪律检查器"""
    
    # 配置参数
    CONFIG = {
        # 乖离率阈值
        'bias_threshold_high': 7.0,      # 超过此值警告追高
        'bias_threshold_extreme': 10.0,  # 超过此值禁止买入
        
        # 均线配置
        'ma_periods': [5, 10, 20, 60],
        'bullish_threshold': 0.02,       # 均线多头排列阈值
        
        # RSI阈值
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        
        # KDJ阈值
        'kdj_overbought': 80,
        'kdj_oversold': 20,
        
        # 仓位配置
        'max_position': 0.30,            # 最大仓位30%
        'min_position': 0.05,            # 最小仓位5%
        
        # 止损止盈
        'default_stop_loss': 0.95,       # 默认止损5%
        'default_take_profit': 1.10,     # 默认止盈10%
        'risk_reward_min': 2.0,          # 最小盈亏比
        
        # 新闻时效（天）
        'news_max_age': 3,
    }
    
    def __init__(self):
        self.checks: List[DisciplineCheck] = []
        self.violations: List[str] = []
    
    def check_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行全部交易纪律检查
        
        Returns:
            {
                'can_trade': bool,          # 是否可交易
                'checks': List[DisciplineCheck],
                'position_suggestion': str,  # 仓位建议
                'price_levels': Dict,        # 价格点位
                'warnings': List[str],       # 警告信息
                'risk_level': str            # 风险等级
            }
        """
        self.checks = []
        self.violations = []
        
        # 1. 乖离率检查（严禁追高）
        self._check_bias(data)
        
        # 2. 均线排列检查（趋势交易）
        self._check_ma_alignment(data)
        
        # 3. 技术指标检查
        self._check_technical_indicators(data)
        
        # 4. 仓位检查
        position = self._check_position(data)
        
        # 5. 价格点位计算
        price_levels = self._calculate_price_levels(data)
        
        # 6. 盈亏比检查
        self._check_risk_reward(price_levels)
        
        # 7. 消息面时效检查
        self._check_news_freshness(data)
        
        # 综合判断
        can_trade = not any(c.status == CheckStatus.FAIL for c in self.checks)
        risk_level = self._calculate_risk_level()
        
        return {
            'can_trade': can_trade,
            'checks': self.checks,
            'position_suggestion': position,
            'price_levels': price_levels,
            'warnings': self.violations,
            'risk_level': risk_level,
            'passed_count': sum(1 for c in self.checks if c.status == CheckStatus.PASS),
            'warning_count': sum(1 for c in self.checks if c.status == CheckStatus.WARNING),
            'fail_count': sum(1 for c in self.checks if c.status == CheckStatus.FAIL)
        }
    
    def _check_bias(self, data: Dict[str, Any]):
        """检查乖离率 - 严禁追高"""
        quote = data.get('quote', {})
        tech = data.get('technical', {})
        
        current_price = quote.get('price', 0)
        ma20 = tech.get('ma20', current_price)
        
        if current_price > 0 and ma20 > 0:
            bias = (current_price - ma20) / ma20 * 100
            
            if bias > self.CONFIG['bias_threshold_extreme']:
                status = CheckStatus.FAIL
                detail = f"乖离率{bias:.1f}%，严重偏离均线"
                suggestion = "股价短期涨幅过大，禁止追高，等待回调"
                self.violations.append(f"乖离率过高: {bias:.1f}%")
            elif bias > self.CONFIG['bias_threshold_high']:
                status = CheckStatus.WARNING
                detail = f"乖离率{bias:.1f}%，偏离均线较多"
                suggestion = "谨慎追高，建议等待回踩MA20"
            else:
                status = CheckStatus.PASS
                detail = f"乖离率{bias:.1f}%，处于合理区间"
                suggestion = "股价与均线关系正常"
            
            self.checks.append(DisciplineCheck(
                rule_name="乖离率检查（严禁追高）",
                status=status,
                detail=detail,
                suggestion=suggestion
            ))
    
    def _check_ma_alignment(self, data: Dict[str, Any]):
        """检查均线排列 - 趋势交易"""
        tech = data.get('technical', {})
        
        ma5 = tech.get('ma5', 0)
        ma10 = tech.get('ma10', 0)
        ma20 = tech.get('ma20', 0)
        ma60 = tech.get('ma60', 0)
        
        # 检查多头排列
        if ma5 > 0 and ma10 > 0 and ma20 > 0:
            if ma5 > ma10 > ma20:
                if ma60 > 0 and ma20 > ma60:
                    status = CheckStatus.PASS
                    detail = "MA5 > MA10 > MA20 > MA60，完美多头排列"
                    suggestion = "趋势强劲，可顺势操作"
                else:
                    status = CheckStatus.PASS
                    detail = "MA5 > MA10 > MA20，短期多头排列"
                    suggestion = "短期趋势向好"
            elif ma5 > ma20:
                status = CheckStatus.WARNING
                detail = f"MA5({ma5:.2f}) > MA20({ma20:.2f})，但MA5 < MA10"
                suggestion = "均线有分歧，趋势不够明确"
            else:
                status = CheckStatus.FAIL
                detail = f"MA5({ma5:.2f}) < MA20({ma20:.2f})，空头排列"
                suggestion = "趋势向下，不建议买入"
                self.violations.append("均线空头排列")
            
            self.checks.append(DisciplineCheck(
                rule_name="均线排列检查（趋势交易）",
                status=status,
                detail=detail,
                suggestion=suggestion
            ))
    
    def _check_technical_indicators(self, data: Dict[str, Any]):
        """检查技术指标"""
        tech = data.get('technical', {})
        
        # RSI检查
        rsi = tech.get('rsi', 50)
        if rsi > self.CONFIG['rsi_overbought']:
            rsi_status = CheckStatus.WARNING
            rsi_detail = f"RSI={rsi:.1f}，超买区域"
            rsi_suggestion = "短期超买，注意回调风险"
        elif rsi < self.CONFIG['rsi_oversold']:
            rsi_status = CheckStatus.PASS
            rsi_detail = f"RSI={rsi:.1f}，超卖区域"
            rsi_suggestion = "超卖状态，可能存在反弹机会"
        else:
            rsi_status = CheckStatus.PASS
            rsi_detail = f"RSI={rsi:.1f}，正常区间"
            rsi_suggestion = "RSI处于正常范围"
        
        self.checks.append(DisciplineCheck(
            rule_name="RSI指标检查",
            status=rsi_status,
            detail=rsi_detail,
            suggestion=rsi_suggestion
        ))
        
        # KDJ检查
        k = tech.get('k', 50)
        d = tech.get('d', 50)
        
        if k > self.CONFIG['kdj_overbought']:
            kdj_status = CheckStatus.WARNING
            kdj_detail = f"K={k:.1f}，超买区域"
            kdj_suggestion = "KDJ超买，谨慎追高"
        elif k < self.CONFIG['kdj_oversold']:
            kdj_status = CheckStatus.PASS
            kdj_detail = f"K={k:.1f}，超卖区域"
            kdj_suggestion = "KDJ超卖，关注反弹"
        else:
            kdj_status = CheckStatus.PASS
            kdj_detail = f"K={k:.1f}，D={d:.1f}，正常区间"
            kdj_suggestion = "KDJ处于正常范围"
        
        self.checks.append(DisciplineCheck(
            rule_name="KDJ指标检查",
            status=kdj_status,
            detail=kdj_detail,
            suggestion=kdj_suggestion
        ))
    
    def _check_position(self, data: Dict[str, Any]) -> str:
        """检查并计算建议仓位"""
        suggestion = data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        
        # 基础仓位
        if total_score >= 75:
            base_position = 0.25
        elif total_score >= 60:
            base_position = 0.20
        elif total_score >= 45:
            base_position = 0.10
        else:
            base_position = 0.05
        
        # 根据纪律检查调整
        warning_count = sum(1 for c in self.checks if c.status == CheckStatus.WARNING)
        fail_count = sum(1 for c in self.checks if c.status == CheckStatus.FAIL)
        
        # 有警告减10%，有失败减20%
        adjustment = -0.10 * warning_count - 0.20 * fail_count
        final_position = base_position + adjustment
        
        # 限制范围
        final_position = max(self.CONFIG['min_position'], 
                           min(self.CONFIG['max_position'], final_position))
        
        position_pct = int(final_position * 100)
        
        status = CheckStatus.PASS if fail_count == 0 else CheckStatus.WARNING
        detail = f"综合评分{total_score}分，建议仓位{position_pct}%"
        suggestion_text = f"根据综合评分和纪律检查，建议仓位{position_pct}%"
        
        if warning_count > 0:
            detail += f"（因{warning_count}项警告已调整）"
        if fail_count > 0:
            detail += f"（因{fail_count}项违规大幅下调）"
            suggestion_text = "存在交易纪律违规，建议减仓或观望"
        
        self.checks.append(DisciplineCheck(
            rule_name="仓位管理检查",
            status=status,
            detail=detail,
            suggestion=suggestion_text
        ))
        
        return f"{position_pct}%"
    
    def _calculate_price_levels(self, data: Dict[str, Any]) -> Dict[str, float]:
        """计算精确买卖点"""
        quote = data.get('quote', {})
        tech = data.get('technical', {})
        fundamental = data.get('fundamental', {})
        
        current_price = quote.get('price', 0)
        if current_price <= 0:
            return {}
        
        # 支撑位和压力位
        ma20 = tech.get('ma20', current_price * 0.95)
        ma60 = tech.get('ma60', current_price * 0.90)
        
        # 买入区间：MA20附近
        buy_zone_low = round(ma20 * 0.98, 2)
        buy_zone_high = round(ma20 * 1.02, 2)
        
        # 止损价：MA60或-5%
        stop_loss_ma = ma60 * 0.98
        stop_loss_pct = current_price * self.CONFIG['default_stop_loss']
        stop_loss = round(max(stop_loss_ma, stop_loss_pct), 2)
        
        # 目标价：根据基本面调整
        fund_score = fundamental.get('score', 50) if isinstance(fundamental, dict) else 50
        if fund_score >= 70:
            target_pct = 1.15
        elif fund_score >= 50:
            target_pct = 1.10
        else:
            target_pct = 1.05
        
        target_price = round(current_price * target_pct, 2)
        
        price_levels = {
            'current': current_price,
            'buy_zone_low': buy_zone_low,
            'buy_zone_high': buy_zone_high,
            'stop_loss': stop_loss,
            'target': target_price,
            'ma20': round(ma20, 2),
            'ma60': round(ma60, 2) if ma60 else None
        }
        
        # 检查止损设置
        stop_distance = (current_price - stop_loss) / current_price * 100
        if stop_distance > 10:
            status = CheckStatus.WARNING
            detail = f"止损幅度{stop_distance:.1f}%过大"
            suggestion = "建议收紧止损至5-8%"
        elif stop_distance < 3:
            status = CheckStatus.WARNING
            detail = f"止损幅度{stop_distance:.1f}%过小"
            suggestion = "止损过紧易被震荡出局"
        else:
            status = CheckStatus.PASS
            detail = f"止损幅度{stop_distance:.1f}%合理"
            suggestion = "止损设置适当"
        
        self.checks.append(DisciplineCheck(
            rule_name="止损设置检查",
            status=status,
            detail=detail,
            suggestion=suggestion
        ))
        
        return price_levels
    
    def _check_risk_reward(self, price_levels: Dict[str, float]):
        """检查盈亏比"""
        if not price_levels:
            return
        
        current = price_levels.get('current', 0)
        target = price_levels.get('target', 0)
        stop = price_levels.get('stop_loss', 0)
        
        if current > 0 and target > current and stop < current:
            potential_gain = (target - current) / current
            potential_loss = (current - stop) / current
            
            if potential_loss > 0:
                risk_reward = potential_gain / potential_loss
                
                if risk_reward >= self.CONFIG['risk_reward_min']:
                    status = CheckStatus.PASS
                    detail = f"盈亏比1:{risk_reward:.1f}，符合要求"
                    suggestion = "盈亏比合理，可执行交易"
                elif risk_reward >= 1.5:
                    status = CheckStatus.WARNING
                    detail = f"盈亏比1:{risk_reward:.1f}，一般"
                    suggestion = "盈亏比一般，可谨慎参与"
                else:
                    status = CheckStatus.FAIL
                    detail = f"盈亏比1:{risk_reward:.1f}，不佳"
                    suggestion = "盈亏比不佳，建议放弃"
                    self.violations.append(f"盈亏比不佳: 1:{risk_reward:.1f}")
                
                self.checks.append(DisciplineCheck(
                    rule_name="盈亏比检查",
                    status=status,
                    detail=detail,
                    suggestion=suggestion
                ))
    
    def _check_news_freshness(self, data: Dict[str, Any]):
        """检查消息面时效"""
        news = data.get('news', {})
        items = news.get('items', [])
        
        if not items:
            self.checks.append(DisciplineCheck(
                rule_name="消息面时效检查",
                status=CheckStatus.WARNING,
                detail="无近期新闻数据",
                suggestion="缺乏消息面参考，建议关注最新动态"
            ))
            return
        
        # 检查最新新闻日期
        latest_date = items[0].get('date', '')
        if latest_date:
            try:
                from datetime import datetime
                news_date = datetime.strptime(latest_date[:10], '%Y-%m-%d')
                days_ago = (datetime.now() - news_date).days
                
                if days_ago <= self.CONFIG['news_max_age']:
                    status = CheckStatus.PASS
                    detail = f"最新新闻{days_ago}天前，时效性良好"
                    suggestion = "消息面信息新鲜"
                elif days_ago <= 7:
                    status = CheckStatus.WARNING
                    detail = f"最新新闻{days_ago}天前，时效性一般"
                    suggestion = "建议关注最新动态"
                else:
                    status = CheckStatus.WARNING
                    detail = f"最新新闻{days_ago}天前，时效性较差"
                    suggestion = "消息面滞后，需重新评估"
                
                self.checks.append(DisciplineCheck(
                    rule_name="消息面时效检查",
                    status=status,
                    detail=detail,
                    suggestion=suggestion
                ))
            except Exception:
                pass
    
    def _calculate_risk_level(self) -> str:
        """计算风险等级"""
        fail_count = sum(1 for c in self.checks if c.status == CheckStatus.FAIL)
        warning_count = sum(1 for c in self.checks if c.status == CheckStatus.WARNING)
        
        if fail_count >= 2:
            return "高风险"
        elif fail_count == 1 or warning_count >= 3:
            return "中风险"
        elif warning_count >= 1:
            return "低风险"
        else:
            return "可控"


# 便捷函数
def check_trading_discipline(data: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：执行交易纪律检查"""
    checker = TradingDiscipline()
    return checker.check_all(data)
