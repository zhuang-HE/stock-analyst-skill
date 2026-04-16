# -*- coding: utf-8 -*-
"""
基本面分析器 - 四大维度分析
借鉴 daily_stock_analysis 的 fundamental_context 设计

四大维度：
1. 估值维度 (Valuation)
2. 成长维度 (Growth)
3. 资金维度 (Capital Flow)
4. 机构维度 (Institution)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class FundamentalAnalyzer:
    """基本面四维分析器"""
    
    def __init__(self):
        self.data = {}
    
    def analyze(self, symbol: str, market: str = 'sh') -> Dict[str, Any]:
        """
        执行四维基本面分析
        
        Returns:
            {
                'valuation': {...},      # 估值维度
                'growth': {...},         # 成长维度
                'capital_flow': {...},   # 资金维度
                'institution': {...},    # 机构维度
                'overall_score': int,    # 综合评分
                'overall_assessment': str # 综合评估
            }
        """
        result = {
            'symbol': symbol,
            'market': market,
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # 1. 估值维度分析
        result['valuation'] = self._analyze_valuation(symbol, market)
        
        # 2. 成长维度分析
        result['growth'] = self._analyze_growth(symbol, market)
        
        # 3. 资金维度分析
        result['capital_flow'] = self._analyze_capital_flow(symbol, market)
        
        # 4. 机构维度分析
        result['institution'] = self._analyze_institution(symbol, market)
        
        # 5. 综合评分
        result.update(self._calculate_overall_score(result))
        
        return result
    
    def _analyze_valuation(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        估值维度分析
        
        指标：
        - PE/PB/PS
        - 历史分位数
        - 行业对比
        - 支撑压力位
        """
        valuation = {
            'dimension': '估值',
            'score': 50,
            'level': '合理',
            'metrics': {},
            'assessment': ''
        }
        
        try:
            import akshare as ak
            
            # 获取历史价格计算分位数
            hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if hist is not None and len(hist) >= 250:
                close_col = self._get_column(hist, ['close', '收盘'])
                close_prices = hist[close_col]
                current_price = close_prices.iloc[-1]
                
                # 历史分位数
                percentile = round((close_prices < current_price).sum() / len(close_prices) * 100, 1)
                valuation['metrics']['price_percentile'] = f'{percentile}%'
                
                # 近一年高低点
                year_high = round(close_prices.tail(250).max(), 2)
                year_low = round(close_prices.tail(250).min(), 2)
                valuation['metrics']['year_high'] = year_high
                valuation['metrics']['year_low'] = year_low
                
                # 支撑压力位（60日）
                recent_60 = close_prices.tail(60)
                support = round(recent_60.min(), 2)
                resistance = round(recent_60.max(), 2)
                valuation['metrics']['support_60d'] = support
                valuation['metrics']['resistance_60d'] = resistance
                
                # 距支撑/压力幅度
                valuation['metrics']['to_support'] = f'{round((current_price - support) / support * 100, 1)}%'
                valuation['metrics']['to_resistance'] = f'{round((resistance - current_price) / current_price * 100, 1)}%'
            
            # 获取财务数据计算估值指标
            try:
                fin_df = ak.stock_financial_abstract_ths(symbol=symbol)
                if fin_df is not None and len(fin_df) > 0:
                    latest = fin_df.iloc[0]
                    
                    eps = self._safe_float(latest.get('基本每股收益', 0))
                    bps = self._safe_float(latest.get('每股净资产', 0))
                    revenue_ps = self._safe_float(latest.get('营业总收入', '0').replace('亿', '')) / 100  # 简化处理
                    
                    if eps > 0:
                        pe = round(current_price / eps, 2)
                        valuation['metrics']['pe_ttm'] = pe
                        
                        # PE评价
                        if pe < 15:
                            valuation['metrics']['pe_evaluation'] = '低估'
                            valuation['score'] += 15
                        elif pe < 30:
                            valuation['metrics']['pe_evaluation'] = '合理'
                            valuation['score'] += 5
                        elif pe < 50:
                            valuation['metrics']['pe_evaluation'] = '偏高'
                            valuation['score'] -= 5
                        else:
                            valuation['metrics']['pe_evaluation'] = '高估'
                            valuation['score'] -= 15
                    
                    if bps > 0:
                        pb = round(current_price / bps, 2)
                        valuation['metrics']['pb'] = pb
                        
                        # PB评价
                        if pb < 1:
                            valuation['metrics']['pb_evaluation'] = '破净'
                            valuation['score'] += 10
                        elif pb < 3:
                            valuation['metrics']['pb_evaluation'] = '合理'
                            valuation['score'] += 5
                        elif pb < 5:
                            valuation['metrics']['pb_evaluation'] = '偏高'
                            valuation['score'] -= 5
                        else:
                            valuation['metrics']['pb_evaluation'] = '高估'
                            valuation['score'] -= 10
            except Exception as e:
                valuation['metrics']['error'] = str(e)
            
            # 根据历史分位数调整评分
            if percentile < 20:
                valuation['score'] += 10
                valuation['level'] = '低估区域'
            elif percentile < 40:
                valuation['score'] += 5
                valuation['level'] = '偏低'
            elif percentile < 60:
                valuation['level'] = '合理'
            elif percentile < 80:
                valuation['score'] -= 5
                valuation['level'] = '偏高'
            else:
                valuation['score'] -= 10
                valuation['level'] = '高估区域'
            
            # 生成评估
            pe_eval = valuation['metrics'].get('pe_evaluation', '未知')
            pb_eval = valuation['metrics'].get('pb_evaluation', '未知')
            valuation['assessment'] = f"PE{pe_eval}，PB{pb_eval}，价格位于历史{percentile}分位"
            
        except Exception as e:
            valuation['error'] = str(e)
        
        valuation['score'] = max(0, min(100, valuation['score']))
        return valuation
    
    def _analyze_growth(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        成长维度分析
        
        指标：
        - 营收增长率
        - 净利润增长率
        - ROE趋势
        - 毛利率趋势
        """
        growth = {
            'dimension': '成长',
            'score': 50,
            'level': '稳健',
            'metrics': {},
            'trends': {},
            'assessment': ''
        }
        
        try:
            import akshare as ak
            
            df = ak.stock_financial_abstract_ths(symbol=symbol)
            if df is not None and len(df) >= 3:
                # 取最近5期
                df = df.sort_values(by='报告期', ascending=False).head(5)
                
                periods = []
                revenues = []
                profits = []
                roes = []
                margins = []
                
                for _, row in df.iterrows():
                    periods.append(str(row.get('报告期', ''))[:10])
                    
                    rev_yoy = self._safe_float(str(row.get('营业总收入同比增长率', '0')).replace('%', ''))
                    profit_yoy = self._safe_float(str(row.get('净利润同比增长率', '0')).replace('%', ''))
                    roe = self._safe_float(str(row.get('净资产收益率', '0')).replace('%', ''))
                    margin = self._safe_float(str(row.get('销售毛利率', '0')).replace('%', ''))
                    
                    revenues.append(rev_yoy)
                    profits.append(profit_yoy)
                    roes.append(roe)
                    margins.append(margin)
                
                # 最新数据
                growth['metrics']['latest_revenue_yoy'] = f'{revenues[0]:.1f}%' if revenues else 'N/A'
                growth['metrics']['latest_profit_yoy'] = f'{profits[0]:.1f}%' if profits else 'N/A'
                growth['metrics']['latest_roe'] = f'{roes[0]:.1f}%' if roes else 'N/A'
                growth['metrics']['latest_gross_margin'] = f'{margins[0]:.1f}%' if margins else 'N/A'
                
                # 趋势分析
                if len(revenues) >= 2:
                    if all(r > 20 for r in revenues[:2]):
                        growth['trends']['revenue'] = '高增长'
                        growth['score'] += 15
                    elif all(r > 10 for r in revenues[:2]):
                        growth['trends']['revenue'] = '稳健增长'
                        growth['score'] += 10
                    elif all(r > 0 for r in revenues[:2]):
                        growth['trends']['revenue'] = '低速增长'
                        growth['score'] += 5
                    elif revenues[0] > revenues[-1]:
                        growth['trends']['revenue'] = '增速回升'
                        growth['score'] += 5
                    else:
                        growth['trends']['revenue'] = '增速放缓'
                        growth['score'] -= 10
                
                if len(profits) >= 2:
                    if all(p > 30 for p in profits[:2]):
                        growth['trends']['profit'] = '高增长'
                        growth['score'] += 15
                    elif all(p > 10 for p in profits[:2]):
                        growth['trends']['profit'] = '稳健增长'
                        growth['score'] += 10
                    elif profits[0] > 0:
                        growth['trends']['profit'] = '正增长'
                        growth['score'] += 5
                    else:
                        growth['trends']['profit'] = '下滑'
                        growth['score'] -= 15
                
                # ROE评价
                if roes:
                    if roes[0] > 20:
                        growth['metrics']['roe_level'] = '优秀'
                        growth['score'] += 15
                    elif roes[0] > 15:
                        growth['metrics']['roe_level'] = '良好'
                        growth['score'] += 10
                    elif roes[0] > 10:
                        growth['metrics']['roe_level'] = '一般'
                        growth['score'] += 5
                    elif roes[0] > 0:
                        growth['metrics']['roe_level'] = '偏低'
                        growth['score'] -= 5
                    else:
                        growth['metrics']['roe_level'] = '亏损'
                        growth['score'] -= 15
                    
                    if len(roes) >= 2 and roes[0] > roes[-1]:
                        growth['trends']['roe'] = '改善'
                        growth['score'] += 5
                    elif len(roes) >= 2:
                        growth['trends']['roe'] = '下降'
                        growth['score'] -= 5
                
                # 毛利率趋势
                if len(margins) >= 2:
                    if margins[0] > margins[-1]:
                        growth['trends']['margin'] = '改善'
                        growth['score'] += 5
                    else:
                        growth['trends']['margin'] = '承压'
                        growth['score'] -= 5
                
                # 确定成长等级
                if growth['score'] >= 75:
                    growth['level'] = '高成长'
                elif growth['score'] >= 60:
                    growth['level'] = '稳健成长'
                elif growth['score'] >= 45:
                    growth['level'] = '成长放缓'
                else:
                    growth['level'] = '成长承压'
                
                # 生成评估
                growth['assessment'] = f"营收{growth['trends'].get('revenue', '未知')}，利润{growth['trends'].get('profit', '未知')}，ROE{growth['metrics'].get('roe_level', '未知')}"
                
        except Exception as e:
            growth['error'] = str(e)
        
        growth['score'] = max(0, min(100, growth['score']))
        return growth
    
    def _analyze_capital_flow(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        资金维度分析
        
        指标：
        - 主力资金流向
        - 散户资金流向
        - 资金流向趋势
        - 龙虎榜数据（如有）
        """
        capital = {
            'dimension': '资金',
            'score': 50,
            'level': '中性',
            'metrics': {},
            'trends': {},
            'assessment': ''
        }
        
        try:
            import akshare as ak
            
            # 获取资金流向
            df = ak.stock_individual_fund_flow(
                stock=symbol,
                market='sh' if symbol.startswith('6') else 'sz'
            )
            
            if df is not None and len(df) >= 5:
                latest = df.iloc[-1]
                
                # 最新资金流向
                main_net = float(latest.get('主力净流入', 0)) / 100000000  # 转为亿
                retail_net = float(latest.get('散户净流入', 0)) / 100000000
                main_pct = float(latest.get('主力净流入占比(%)', 0))
                
                capital['metrics']['main_net_latest'] = f'{main_net:+.2f}亿'
                capital['metrics']['retail_net_latest'] = f'{retail_net:+.2f}亿'
                capital['metrics']['main_pct'] = f'{main_pct:.2f}%'
                
                # 近5日资金流向
                main_5d = sum(float(df.iloc[i].get('主力净流入', 0)) for i in range(min(5, len(df)))) / 100000000
                capital['metrics']['main_net_5d'] = f'{main_5d:+.2f}亿'
                
                # 评分逻辑
                if main_net > 1:
                    capital['score'] += 20
                    capital['level'] = '强势流入'
                elif main_net > 0.5:
                    capital['score'] += 15
                    capital['level'] = '明显流入'
                elif main_net > 0:
                    capital['score'] += 5
                    capital['level'] = '小幅流入'
                elif main_net > -0.5:
                    capital['score'] -= 5
                    capital['level'] = '小幅流出'
                elif main_net > -1:
                    capital['score'] -= 15
                    capital['level'] = '明显流出'
                else:
                    capital['score'] -= 20
                    capital['level'] = '大幅流出'
                
                # 趋势判断
                if len(df) >= 10:
                    main_10d = sum(float(df.iloc[i].get('主力净流入', 0)) for i in range(min(10, len(df)))) / 100000000
                    capital['metrics']['main_net_10d'] = f'{main_10d:+.2f}亿'
                    
                    if main_10d > 2:
                        capital['trends']['short_term'] = '持续流入'
                        capital['score'] += 10
                    elif main_10d < -2:
                        capital['trends']['short_term'] = '持续流出'
                        capital['score'] -= 10
                    else:
                        capital['trends']['short_term'] = '震荡'
                
                # 散户反向指标
                if retail_net > 0 and main_net < 0:
                    capital['metrics']['signal'] = '散户接盘，主力出货'
                    capital['score'] -= 10
                elif retail_net < 0 and main_net > 0:
                    capital['metrics']['signal'] = '主力吸筹，散户恐慌'
                    capital['score'] += 10
                else:
                    capital['metrics']['signal'] = '资金方向一致'
                
                capital['assessment'] = f"主力{capital['level']}，近5日{main_5d:+.2f}亿，{capital['metrics'].get('signal', '')}"
                
        except Exception as e:
            capital['error'] = str(e)
        
        capital['score'] = max(0, min(100, capital['score']))
        return capital
    
    def _analyze_institution(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        机构维度分析
        
        指标：
        - 机构持股数量
        - 机构持股比例
        - 机构评级
        - 盈利预测
        """
        institution = {
            'dimension': '机构',
            'score': 50,
            'level': '中性',
            'metrics': {},
            'assessment': ''
        }
        
        try:
            import akshare as ak
            
            # 机构持股
            try:
                holder_df = ak.stock_institute_hold_detail(symbol=symbol)
                if holder_df is not None and len(holder_df) > 0:
                    institution['metrics']['institution_count'] = len(holder_df)
                    
                    # 计算总持股比例
                    total_ratio = 0
                    for _, row in holder_df.iterrows():
                        ratio = self._safe_float(str(row.get('持股比例', '0')).replace('%', ''))
                        total_ratio += ratio
                    
                    institution['metrics']['total_hold_ratio'] = f'{total_ratio:.2f}%'
                    
                    # 评分
                    if total_ratio > 50:
                        institution['score'] += 20
                        institution['level'] = '机构重仓'
                    elif total_ratio > 30:
                        institution['score'] += 15
                        institution['level'] = '机构高持仓'
                    elif total_ratio > 10:
                        institution['score'] += 10
                        institution['level'] = '机构中度持仓'
                    elif total_ratio > 5:
                        institution['score'] += 5
                        institution['level'] = '机构轻度持仓'
                    else:
                        institution['level'] = '机构低配'
            except Exception as e:
                institution['metrics']['holder_error'] = str(e)
            
            # 盈利预测
            try:
                forecast_df = ak.stock_profit_forecast_ths(symbol=symbol, indicator='预测年报净利润')
                if forecast_df is not None and len(forecast_df) > 0:
                    latest_forecast = forecast_df.iloc[0]
                    
                    analyst_count = int(self._safe_float(latest_forecast.get('预测机构数', 0)))
                    mean_forecast = self._safe_float(latest_forecast.get('均值', 0))
                    
                    institution['metrics']['analyst_count'] = analyst_count
                    institution['metrics']['forecast_profit'] = f'{mean_forecast:.2f}亿'
                    
                    # 机构覆盖度评分
                    if analyst_count >= 20:
                        institution['score'] += 15
                        institution['metrics']['coverage'] = '高覆盖'
                    elif analyst_count >= 10:
                        institution['score'] += 10
                        institution['metrics']['coverage'] = '中等覆盖'
                    elif analyst_count >= 5:
                        institution['score'] += 5
                        institution['metrics']['coverage'] = '低覆盖'
                    else:
                        institution['metrics']['coverage'] = '极少覆盖'
                    
                    # 预测增长
                    if len(forecast_df) >= 2:
                        cur = self._safe_float(forecast_df.iloc[0].get('均值', 0))
                        nxt = self._safe_float(forecast_df.iloc[1].get('均值', 0))
                        if cur > 0:
                            growth = (nxt - cur) / cur * 100
                            institution['metrics']['forecast_growth'] = f'{growth:.1f}%'
                            
                            if growth > 30:
                                institution['score'] += 10
                            elif growth > 10:
                                institution['score'] += 5
                            elif growth < 0:
                                institution['score'] -= 10
            except Exception as e:
                institution['metrics']['forecast_error'] = str(e)
            
            # 生成评估
            coverage = institution['metrics'].get('coverage', '未知')
            hold_ratio = institution['metrics'].get('total_hold_ratio', '未知')
            institution['assessment'] = f"机构{coverage}，持股{hold_ratio}"
            
        except Exception as e:
            institution['error'] = str(e)
        
        institution['score'] = max(0, min(100, institution['score']))
        return institution
    
    def _calculate_overall_score(self, result: Dict) -> Dict[str, Any]:
        """计算综合评分"""
        valuation_score = result['valuation'].get('score', 50)
        growth_score = result['growth'].get('score', 50)
        capital_score = result['capital_flow'].get('score', 50)
        institution_score = result['institution'].get('score', 50)
        
        # 权重：估值30%，成长30%，资金20%，机构20%
        overall_score = round(
            valuation_score * 0.30 +
            growth_score * 0.30 +
            capital_score * 0.20 +
            institution_score * 0.20
        )
        
        # 评估等级
        if overall_score >= 75:
            assessment = '基本面优秀'
        elif overall_score >= 60:
            assessment = '基本面良好'
        elif overall_score >= 45:
            assessment = '基本面一般'
        else:
            assessment = '基本面偏弱'
        
        return {
            'overall_score': overall_score,
            'overall_assessment': assessment,
            'dimension_scores': {
                'valuation': valuation_score,
                'growth': growth_score,
                'capital_flow': capital_score,
                'institution': institution_score
            }
        }
    
    def _safe_float(self, val, default=0.0) -> float:
        """安全转换为浮点数"""
        if val is None or pd.isna(val):
            return default
        try:
            if isinstance(val, str):
                val = val.replace('%', '').replace(',', '').replace('亿', '').replace('万', '')
                if val in ['--', '', 'False', 'true']:
                    return default
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def _get_column(self, df: pd.DataFrame, candidates: List[str]) -> str:
        """获取存在的列名"""
        for name in candidates:
            if name in df.columns:
                return name
        return df.columns[0] if len(df.columns) > 0 else None


# 便捷函数
def analyze_fundamental(symbol: str, market: str = 'sh') -> Dict[str, Any]:
    """便捷函数：执行基本面四维分析"""
    analyzer = FundamentalAnalyzer()
    return analyzer.analyze(symbol, market)
