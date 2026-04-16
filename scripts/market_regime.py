# -*- coding: utf-8 -*-
"""
大盘环境判断模块 - 进攻/均衡/防守策略
借鉴 daily_stock_analysis 的市场策略系统

A股策略：三段式复盘（进攻/均衡/防守）
美股策略：Regime Strategy（risk-on/neutral/risk-off）
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class MarketRegime(Enum):
    """市场环境状态"""
    OFFENSIVE = "进攻"      # 积极做多
    BALANCED = "均衡"       # 灵活配置
    DEFENSIVE = "防守"      # 控制风险


class MarketAnalyzer:
    """大盘环境分析器"""
    
    # 指数代码映射
    INDEX_CODES = {
        '上证指数': '000001',
        '深证成指': '399001',
        '创业板指': '399006',
        '沪深300': '000300',
        '科创50': '000688',
        '纳斯达克': 'IXIC',
        '标普500': 'SPX',
        '道琼斯': 'DJI',
    }
    
    def __init__(self):
        self.data = {}
    
    def analyze_a_share_market(self) -> Dict[str, Any]:
        """
        A股市场环境分析
        
        返回三段式策略：进攻/均衡/防守
        """
        result = {
            'market': 'A股',
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'indices': {},
            'regime': MarketRegime.BALANCED.value,
            'regime_score': 50,
            'position_suggestion': '50%',
            'sector_rotation': {},
            'analysis': ''
        }
        
        try:
            import akshare as ak
            
            # 1. 分析主要指数
            for name, code in [('上证指数', '000001'), ('深证成指', '399001'), 
                              ('创业板指', '399006'), ('沪深300', '000300')]:
                try:
                    result['indices'][name] = self._analyze_index(code, name)
                except Exception as e:
                    result['indices'][name] = {'error': str(e)}
            
            # 2. 板块轮动分析
            result['sector_rotation'] = self._analyze_sector_rotation()
            
            # 3. 综合判断市场环境
            regime_result = self._determine_a_share_regime(result['indices'])
            result['regime'] = regime_result['regime']
            result['regime_score'] = regime_result['score']
            result['position_suggestion'] = regime_result['position']
            result['analysis'] = regime_result['analysis']
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def analyze_us_market(self) -> Dict[str, Any]:
        """
        美股市场环境分析
        
        返回 Regime Strategy：risk-on/neutral/risk-off
        """
        result = {
            'market': '美股',
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'indices': {},
            'regime': 'neutral',
            'regime_score': 50,
            'position_suggestion': '50%',
            'vix_level': 'normal',
            'analysis': ''
        }
        
        try:
            # 使用YFinance获取美股数据
            import yfinance as yf
            
            # 分析主要指数
            indices = {
                'SPX': '^GSPC',    # 标普500
                'DJI': '^DJI',     # 道琼斯
                'IXIC': '^IXIC',   # 纳斯达克
                'VIX': '^VIX'      # 波动率指数
            }
            
            for name, symbol in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='3mo')
                    
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        ma20 = hist['Close'].rolling(20).mean().iloc[-1]
                        ma60 = hist['Close'].rolling(60).mean().iloc[-1]
                        
                        # 计算涨跌幅
                        month_return = (current - hist['Close'].iloc[-20]) / hist['Close'].iloc[-20] * 100
                        
                        result['indices'][name] = {
                            'price': round(current, 2),
                            'ma20': round(ma20, 2),
                            'ma60': round(ma60, 2),
                            'month_return': round(month_return, 2),
                            'above_ma20': current > ma20,
                            'above_ma60': current > ma60
                        }
                        
                        # VIX特殊处理
                        if name == 'VIX':
                            if current > 30:
                                result['vix_level'] = 'high'
                            elif current > 20:
                                result['vix_level'] = 'elevated'
                            else:
                                result['vix_level'] = 'normal'
                except Exception as e:
                    result['indices'][name] = {'error': str(e)}
            
            # 判断Regime
            regime_result = self._determine_us_regime(result['indices'], result['vix_level'])
            result['regime'] = regime_result['regime']
            result['regime_score'] = regime_result['score']
            result['position_suggestion'] = regime_result['position']
            result['analysis'] = regime_result['analysis']
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_index(self, code: str, name: str) -> Dict[str, Any]:
        """分析单个指数"""
        import akshare as ak
        
        # 获取指数数据
        if code in ['399001', '399006']:  # 深证指数
            df = ak.index_zh_a_hist(symbol=code, period="daily", 
                                   start_date=(datetime.now() - pd.Timedelta(days=120)).strftime('%Y%m%d'),
                                   end_date=datetime.now().strftime('%Y%m%d'))
        else:  # 上证指数、沪深300等
            df = ak.index_zh_a_hist(symbol=code, period="daily",
                                   start_date=(datetime.now() - pd.Timedelta(days=120)).strftime('%Y%m%d'),
                                   end_date=datetime.now().strftime('%Y%m%d'))
        
        if df is None or df.empty:
            return {'error': '无数据'}
        
        # 计算指标
        latest = df.iloc[-1]
        close_col = '收盘' if '收盘' in df.columns else 'close'
        
        current = latest[close_col]
        
        # 均线
        df['MA5'] = df[close_col].rolling(5).mean()
        df['MA20'] = df[close_col].rolling(20).mean()
        df['MA60'] = df[close_col].rolling(60).mean()
        
        ma5 = df['MA5'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma60 = df['MA60'].iloc[-1]
        
        # 涨跌幅
        month_ago = df[close_col].iloc[-20] if len(df) >= 20 else df[close_col].iloc[0]
        month_return = (current - month_ago) / month_ago * 100
        
        return {
            'current': round(current, 2),
            'ma5': round(ma5, 2),
            'ma20': round(ma20, 2),
            'ma60': round(ma60, 2),
            'month_return': round(month_return, 2),
            'trend': '上升' if ma5 > ma20 > ma60 else ('下降' if ma5 < ma20 < ma60 else '震荡'),
            'above_ma20': current > ma20,
            'above_ma60': current > ma60
        }
    
    def _analyze_sector_rotation(self) -> Dict[str, Any]:
        """分析板块轮动"""
        sectors = {}
        
        try:
            import akshare as ak
            
            # 获取板块涨跌
            try:
                sector_df = ak.stock_sector_spot()
                if sector_df is not None and not sector_df.empty:
                    # 领涨板块
                    top_sectors = sector_df.nlargest(5, '涨跌幅')[['板块名称', '涨跌幅']].to_dict('records')
                    # 领跌板块
                    bottom_sectors = sector_df.nsmallest(5, '涨跌幅')[['板块名称', '涨跌幅']].to_dict('records')
                    
                    sectors['top'] = top_sectors
                    sectors['bottom'] = bottom_sectors
            except Exception:
                pass
            
        except Exception as e:
            sectors['error'] = str(e)
        
        return sectors
    
    def _determine_a_share_regime(self, indices: Dict) -> Dict[str, Any]:
        """判断A股市场环境"""
        score = 50
        reasons = []
        
        # 分析上证指数
        sh_index = indices.get('上证指数', {})
        if 'current' in sh_index:
            # 均线判断
            if sh_index.get('trend') == '上升':
                score += 15
                reasons.append("大盘均线多头排列")
            elif sh_index.get('trend') == '下降':
                score -= 15
                reasons.append("大盘均线空头排列")
            
            # 站上MA20
            if sh_index.get('above_ma20'):
                score += 10
                reasons.append("大盘站上20日均线")
            else:
                score -= 10
                reasons.append("大盘跌破20日均线")
            
            # 月度涨跌
            month_return = sh_index.get('month_return', 0)
            if month_return > 5:
                score += 10
                reasons.append(f"大盘月涨{month_return:.1f}%，强势")
            elif month_return < -5:
                score -= 10
                reasons.append(f"大盘月跌{abs(month_return):.1f}%，弱势")
        
        # 分析创业板指（风险偏好）
        cy_index = indices.get('创业板指', {})
        if 'current' in cy_index:
            if cy_index.get('above_ma20'):
                score += 5
                reasons.append("创业板强势，风险偏好高")
            else:
                score -= 5
                reasons.append("创业板弱势，风险偏好低")
        
        # 确定策略
        if score >= 70:
            regime = MarketRegime.OFFENSIVE
            position = '70-80%'
            analysis = f"市场环境积极，建议进攻策略。{'；'.join(reasons)}"
        elif score >= 45:
            regime = MarketRegime.BALANCED
            position = '40-60%'
            analysis = f"市场环境中性，建议均衡配置。{'；'.join(reasons)}"
        else:
            regime = MarketRegime.DEFENSIVE
            position = '20-30%'
            analysis = f"市场环境偏弱，建议防守策略。{'；'.join(reasons)}"
        
        return {
            'regime': regime.value,
            'score': max(0, min(100, score)),
            'position': position,
            'analysis': analysis
        }
    
    def _determine_us_regime(self, indices: Dict, vix_level: str) -> Dict[str, Any]:
        """判断美股市场环境"""
        score = 50
        reasons = []
        
        # 分析标普500
        spx = indices.get('SPX', {})
        if 'price' in spx:
            if spx.get('above_ma20') and spx.get('above_ma60'):
                score += 15
                reasons.append("标普500均线多头排列")
            elif not spx.get('above_ma20'):
                score -= 10
                reasons.append("标普500跌破20日均线")
            
            month_return = spx.get('month_return', 0)
            if month_return > 3:
                score += 10
            elif month_return < -3:
                score -= 10
        
        # 分析纳斯达克
        ixic = indices.get('IXIC', {})
        if 'price' in ixic:
            if ixic.get('above_ma20'):
                score += 5
                reasons.append("纳指强势，科技股活跃")
            else:
                score -= 5
        
        # VIX判断
        if vix_level == 'high':
            score -= 20
            reasons.append("VIX高企，市场恐慌")
        elif vix_level == 'elevated':
            score -= 10
            reasons.append("VIX偏高，谨慎情绪")
        else:
            score += 5
            reasons.append("VIX正常，情绪稳定")
        
        # 确定Regime
        if score >= 70:
            regime = 'risk-on'
            position = '70-80%'
            analysis = f"Risk-on环境，积极做多。{'；'.join(reasons)}"
        elif score >= 45:
            regime = 'neutral'
            position = '40-60%'
            analysis = f"Neutral环境，灵活配置。{'；'.join(reasons)}"
        else:
            regime = 'risk-off'
            position = '20-30%'
            analysis = f"Risk-off环境，防御为主。{'；'.join(reasons)}"
        
        return {
            'regime': regime,
            'score': max(0, min(100, score)),
            'position': position,
            'analysis': analysis
        }
    
    def get_market_summary(self) -> str:
        """获取市场总结报告"""
        a_share = self.analyze_a_share_market()
        
        lines = [
            "╔══════════════════════════════════════════════════════════════════╗",
            "║                    📊 大盘环境分析报告                            ║",
            f"║  报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M'):<47}║",
            "╚══════════════════════════════════════════════════════════════════╝",
            "",
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  🇨🇳 A股市场                                                    │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  市场环境: {a_share.get('regime', '未知'):<10}  评分: {a_share.get('regime_score', 0)}/100                    │",
            f"│  建议仓位: {a_share.get('position_suggestion', '50%'):<10}                                        │",
            "├─────────────────────────────────────────────────────────────────┤",
        ]
        
        # 指数状态
        for name, data in a_share.get('indices', {}).items():
            if 'current' in data:
                trend_icon = "📈" if data.get('trend') == '上升' else ("📉" if data.get('trend') == '下降' else "➡️")
                lines.append(f"│  {trend_icon} {name:<8}: {data['current']:>8.2f}  月涨跌: {data.get('month_return', 0):>+6.2f}%      │")
        
        lines.extend([
            "├─────────────────────────────────────────────────────────────────┤",
            "│  分析:                                                          │",
        ])
        
        # 分析文字换行
        analysis = a_share.get('analysis', '')
        for i in range(0, len(analysis), 56):
            chunk = analysis[i:i+56]
            lines.append(f"│  {chunk:<63}│")
        
        lines.extend([
            "└─────────────────────────────────────────────────────────────────┘",
            "",
            "💡 策略建议:",
            f"   当前A股处于【{a_share.get('regime', '未知')}】阶段，",
            f"   建议仓位控制在 {a_share.get('position_suggestion', '50%')}。",
            ""
        ])
        
        return '\n'.join(lines)


# 便捷函数
def analyze_market_regime(market: str = 'a_share') -> Dict[str, Any]:
    """便捷函数：分析市场环境"""
    analyzer = MarketAnalyzer()
    
    if market.lower() in ['a_share', 'a股', 'cn']:
        return analyzer.analyze_a_share_market()
    elif market.lower() in ['us', '美股', 'usa']:
        return analyzer.analyze_us_market()
    else:
        return {'error': f'不支持的市场: {market}'}


def get_market_summary() -> str:
    """便捷函数：获取市场总结"""
    analyzer = MarketAnalyzer()
    return analyzer.get_market_summary()
