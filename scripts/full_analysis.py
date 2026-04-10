# -*- coding: utf-8 -*-
"""
完整的股票分析报告生成 - 增强版 v2.0
包含：行情、技术面、基本面（财务+估值+行业+业绩趋势）、消息面、资金面
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import re
warnings.filterwarnings('ignore')


class StockFullAnalyzer:
    """股票全面分析器 v2.0 - 增强基本面分析"""

    # A股股票名称映射表
    STOCK_NAMES = {
        '000001': '平安银行', '600519': '贵州茅台', '600036': '招商银行',
        '000002': '万科A', '000858': '五粮液', '600887': '伊利股份',
        '000333': '美的集团', '002475': '立讯精密', '601318': '中国平安',
        '601166': '兴业银行', '600276': '恒瑞医药', '300750': '宁德时代',
        '002149': '西部材料', '600309': '万华化学', '600585': '海螺水泥',
        '002415': '海康威视', '000568': '泸州老窖', '000661': '长春高新',
        '600900': '长江电力', '601012': '隆基绿能', '002594': '比亚迪',
        '002402': '和而泰', '002230': '科大讯飞', '300059': '东方财富',
        '601899': '紫金矿业', '002714': '牧原股份', '600809': '山西汾酒',
        '688981': '中芯国际', '300274': '阳光电源', '002371': '北方华创',
    }

    # 行业关键词映射（扩展版）
    INDUSTRY_KEYWORDS = {
        '半导体': ['芯片', '半导体', '集成电路', '晶圆', '封测', '光刻', 'EDA', 'MCU', 'SoC', 'IGBT'],
        '消费电子': ['手机', '消费电子', '智能穿戴', 'VR', 'AR', 'TWS', '耳机', '智能家居', '智能控制器'],
        '新能源': ['光伏', '风电', '储能', '锂电', '新能源', '充电桩', '氢能', '逆变器'],
        '汽车': ['汽车', '智能驾驶', '自动驾驶', '新能源车', '整车', '零部件', '车载'],
        '医药': ['医药', '创新药', '生物制药', 'CRO', '医疗器械', '中药', '临床'],
        '食品饮料': ['白酒', '啤酒', '乳制品', '调味品', '食品', '饮料'],
        '金融': ['银行', '保险', '券商', '信托', '金融科技'],
        '房地产': ['地产', '房地产', '物业', '租赁'],
        '军工': ['军工', '航天', '航空', '兵器', '国防'],
        'TMT': ['软件', '云计算', '大数据', '人工智能', '5G', '通信', '互联网', 'AI', '物联网', 'IoT'],
        '高端制造': ['数控', '机器人', '工业母机', '3D打印', '精密制造'],
        '新材料': ['新材料', '碳纤维', '稀土', '钛合金', '高温合金', '稀有金属'],
    }

    # 股票代码 -> 行业硬编码映射（常见股票）
    STOCK_INDUSTRY = {
        '002402': '消费电子',  # 和而泰 - 智能控制器
        '600519': '食品饮料',  # 贵州茅台
        '000001': '金融',      # 平安银行
        '300750': '新能源',    # 宁德时代
        '002594': '汽车',      # 比亚迪
        '002415': 'TMT',       # 海康威视
        '002230': 'TMT',       # 科大讯飞
        '688981': '半导体',    # 中芯国际
        '300059': '金融',      # 东方财富
        '601899': '新材料',    # 紫金矿业
        '002149': '新材料',    # 西部材料
        '002475': '消费电子',  # 立讯精密
        '600036': '金融',      # 招商银行
        '601318': '金融',      # 中国平安
    }

    def __init__(self):
        self.data = {}

    def normalize_code(self, code: str) -> tuple:
        code = code.strip().upper()
        if code.endswith('.SH') or code.startswith('6'):
            return 'sh', code.replace('.SH', '')
        elif code.endswith('.SZ') or code.startswith(('0', '3')):
            return 'sz', code.replace('.SZ', '')
        else:
            if code.startswith('6'):
                return 'sh', code
            return 'sz', code

    def get_stock_name(self, code: str) -> str:
        return self.STOCK_NAMES.get(code, code)

    def _safe_get_column(self, df: pd.DataFrame, *names) -> str:
        for name in names:
            if name in df.columns:
                return name
        return df.columns[0] if len(df.columns) > 0 else None

    def _safe_float(self, val, default=0.0):
        """安全转换为浮点数"""
        if val is None or pd.isna(val):
            return default
        try:
            if isinstance(val, str):
                val = val.replace('%', '').replace(',', '').replace('亿', 'e8').replace('万', 'e4')
                if val in ['False', 'true', '--', '']:
                    return default
            return float(val)
        except (ValueError, TypeError):
            return default

    def _parse_chinese_number(self, val_str: str) -> float:
        """解析中文数字，如 '5.32亿' -> 532000000"""
        if not isinstance(val_str, str):
            return self._safe_float(val_str)
        val_str = val_str.strip().replace(',', '')
        try:
            if '亿' in val_str:
                return float(val_str.replace('亿', '')) * 1e8
            elif '万' in val_str:
                return float(val_str.replace('万', '')) * 1e4
            elif '%' in val_str:
                return float(val_str.replace('%', ''))
            return float(val_str)
        except (ValueError, TypeError):
            return 0.0

    def get_full_analysis(self, code: str) -> dict:
        """获取完整分析报告"""
        result = {
            'success': False,
            'code': code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            market, symbol = self.normalize_code(code)
            result['stock_name'] = self.get_stock_name(symbol)

            # ========== 1. 行情数据 ==========
            result['quote'] = self._get_quote(market, symbol)

            # ========== 2. 技术分析 ==========
            result['technical'] = self._get_technical_analysis(market, symbol)

            # ========== 3. 基本面分析（增强版）==========
            result['fundamental'] = self._get_fundamental_analysis_v2(market, symbol)

            # ========== 4. 消息面分析（增强版）==========
            result['news'] = self._get_news_analysis_v2(symbol, result.get('fundamental', {}))

            # ========== 5. 资金面分析 ==========
            result['money_flow'] = self._get_money_flow(symbol)

            # ========== 6. 综合建议（增强版）==========
            result['suggestion'] = self._generate_suggestion_v2(result)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            import traceback
            result['trace'] = str(traceback.format_exc())[:500]

        return result

    # ==================== 1. 行情数据 ====================
    def _get_quote(self, market: str, symbol: str) -> dict:
        """获取行情数据"""
        try:
            hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if hist is not None and len(hist) > 0:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest

                close_col = self._safe_get_column(hist, 'close', '收盘')
                open_col = self._safe_get_column(hist, 'open', '开盘')
                high_col = self._safe_get_column(hist, 'high', '最高')
                low_col = self._safe_get_column(hist, 'low', '最低')
                vol_col = self._safe_get_column(hist, 'volume', '成交量')
                amount_col = self._safe_get_column(hist, 'amount', '成交额')
                turnover_col = self._safe_get_column(hist, 'turnover', '换手率')

                price = float(latest[close_col])
                prev_price = float(prev[close_col])

                return {
                    'price': price,
                    'change': round(price - prev_price, 2),
                    'pct_change': round((price - prev_price) / prev_price * 100, 2),
                    'open': float(latest[open_col]),
                    'high': float(latest[high_col]),
                    'low': float(latest[low_col]),
                    'volume': int(latest[vol_col]),
                    'amount': round(float(latest[amount_col]) / 100000000, 2),
                    'turnover': round(float(latest.get(turnover_col, 0)) * 100, 2),
                    'date': str(latest.name)[:10] if hasattr(latest.name, 'year') else 'N/A'
                }
        except Exception as e:
            return {'error': str(e)}
        return {'error': '无法获取行情数据'}

    # ==================== 2. 技术分析 ====================
    def _get_technical_analysis(self, market: str, symbol: str) -> dict:
        """获取技术分析"""
        try:
            hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if hist is None or len(hist) < 30:
                return {'error': '数据不足'}

            hist = hist.rename(columns={
                self._safe_get_column(hist, 'close', '收盘'): 'close',
                self._safe_get_column(hist, 'open', '开盘'): 'open',
                self._safe_get_column(hist, 'high', '最高'): 'high',
                self._safe_get_column(hist, 'low', '最低'): 'low',
                self._safe_get_column(hist, 'volume', '成交量'): 'volume',
            })

            for period in [5, 10, 20, 60]:
                hist[f'ma{period}'] = hist['close'].rolling(window=period).mean()

            delta = hist['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['rsi'] = 100 - (100 / (1 + rs))

            low9 = hist['low'].rolling(window=9).min()
            high9 = hist['high'].rolling(window=9).max()
            rsv = (hist['close'] - low9) / (high9 - low9) * 100
            hist['k'] = rsv.ewm(com=2).mean()
            hist['d'] = hist['k'].ewm(com=2).mean()
            hist['j'] = 3 * hist['k'] - 2 * hist['d']

            exp12 = hist['close'].ewm(span=12, adjust=False).mean()
            exp26 = hist['close'].ewm(span=26, adjust=False).mean()
            hist['macd'] = exp12 - exp26
            hist['signal'] = hist['macd'].ewm(span=9, adjust=False).mean()
            hist['histogram'] = hist['macd'] - hist['signal']

            latest = hist.iloc[-1]

            ma5 = latest['ma5']
            ma20 = latest['ma20']
            ma60 = latest['ma60'] if pd.notna(latest.get('ma60')) else ma20
            price = latest['close']

            if ma5 > ma20 > ma60:
                trend, trend_score = '上升趋势', 20
            elif ma5 < ma20 < ma60:
                trend, trend_score = '下降趋势', -20
            elif ma5 > ma20:
                trend, trend_score = '震荡偏强', 10
            else:
                trend, trend_score = '震荡偏弱', -10

            k, d = latest['k'], latest['d']
            if k > 80:
                kdj_signal, kdj_score = '超买区', -15
            elif k < 20:
                kdj_signal, kdj_score = '超卖区', 15
            elif k > d:
                kdj_signal, kdj_score = '金叉', 5
            else:
                kdj_signal, kdj_score = '死叉', -5

            rsi = latest['rsi']
            if rsi > 70:
                rsi_signal, rsi_score = '超买', -10
            elif rsi < 30:
                rsi_signal, rsi_score = '超卖', 10
            else:
                rsi_signal, rsi_score = '正常', 0

            macd = latest['macd']
            signal = latest['signal']
            if macd > signal and macd > 0:
                macd_signal, macd_score = '多头', 10
            elif macd < signal and macd < 0:
                macd_signal, macd_score = '空头', -10
            else:
                macd_signal, macd_score = '盘整', 0

            return {
                'ma5': round(float(ma5), 2),
                'ma10': round(float(latest['ma10']), 2),
                'ma20': round(float(ma20), 2),
                'ma60': round(float(ma60), 2) if pd.notna(latest.get('ma60')) else None,
                'price_above_ma5': bool(price > ma5),
                'price_above_ma20': bool(price > ma20),
                'price_above_ma60': bool(price > ma60),
                'rsi': round(float(rsi), 2),
                'rsi_signal': rsi_signal,
                'k': round(float(k), 2),
                'd': round(float(d), 2),
                'j': round(float(latest['j']), 2),
                'kdj_signal': kdj_signal,
                'macd': round(float(macd), 2),
                'macd_signal': macd_signal,
                'histogram': round(float(latest['histogram']), 2),
                'trend': trend,
                'scores': {
                    'trend': trend_score,
                    'kdj': kdj_score,
                    'rsi': rsi_score,
                    'macd': macd_score
                }
            }
        except Exception as e:
            return {'error': str(e)}

    # ==================== 3. 基本面分析（增强版）====================
    def _get_fundamental_analysis_v2(self, market: str, symbol: str) -> dict:
        """增强版基本面分析：财务分析 + 估值 + 行业 + 业绩趋势"""
        fundamental = {}

        # ---------- 3.1 财务数据分析（多期）----------
        fundamental['financial'] = self._get_financial_data(symbol)

        # ---------- 3.2 估值分析 ----------
        fundamental['valuation'] = self._get_valuation_analysis(market, symbol)

        # ---------- 3.3 行业与业务分析 ----------
        fundamental['industry'] = self._get_industry_analysis(symbol)

        # ---------- 3.4 盈利预测 ----------
        fundamental['profit_forecast'] = self._get_profit_forecast(symbol)

        # ---------- 3.5 资产负债表关键指标 ----------
        fundamental['balance_sheet'] = self._get_balance_sheet_highlights(symbol)

        # ---------- 3.6 业绩趋势判断 ----------
        fundamental['performance_trend'] = self._analyze_performance_trend(fundamental)

        # ---------- 3.7 综合基本面评分 ----------
        fundamental.update(self._score_fundamental(fundamental))

        return fundamental

    def _get_financial_data(self, symbol: str) -> dict:
        """获取多期财务数据（利润表+关键指标）"""
        fin = {'periods': [], 'latest': {}, 'trend': {}}

        try:
            df = ak.stock_financial_abstract_ths(symbol=symbol)
            if df is None or len(df) == 0:
                return {'error': '无财务数据'}

            # 按报告期降序排列，取最近5期
            df = df.sort_values(by='报告期', ascending=False)
            recent = df.head(5)

            for _, row in recent.iterrows():
                period = str(row.get('报告期', ''))[:10]
                period_data = {
                    'report_date': period,
                    'net_profit': str(row.get('净利润', '')),
                    'net_profit_yoy': str(row.get('净利润同比增长率', '')),
                    'deducted_net_profit': str(row.get('扣非净利润', '')),
                    'deducted_yoy': str(row.get('扣非净利润同比增长率', '')),
                    'revenue': str(row.get('营业总收入', '')),
                    'revenue_yoy': str(row.get('营业总收入同比增长率', '')),
                    'eps': str(row.get('基本每股收益', '')),
                    'bps': str(row.get('每股净资产', '')),
                    'cps': str(row.get('每股资本公积金', '')),
                    'undistributed_ps': str(row.get('每股未分配利润', '')),
                    'ocf_ps': str(row.get('每股经营现金流', '')),
                    'net_margin': str(row.get('销售净利率', '')),
                    'gross_margin': str(row.get('销售毛利率', '')),
                    'roe': str(row.get('净资产收益率', '')),
                    'roe_diluted': str(row.get('净资产收益率-摊薄', '')),
                    'inventory_turnover': str(row.get('存货周转率', '')),
                    'current_ratio': str(row.get('流动比率', '')),
                    'quick_ratio': str(row.get('速动比率', '')),
                    'debt_ratio': str(row.get('资产负债率', '')),
                }
                fin['periods'].append(period_data)

            # 最新一期关键指标
            if len(fin['periods']) > 0:
                latest = fin['periods'][0]
                fin['latest'] = {
                    'report_date': latest['report_date'],
                    'net_profit_yoy': latest['net_profit_yoy'],
                    'revenue_yoy': latest['revenue_yoy'],
                    'roe': latest['roe'],
                    'gross_margin': latest['gross_margin'],
                    'net_margin': latest['net_margin'],
                    'debt_ratio': latest['debt_ratio'],
                    'eps': latest['eps'],
                    'ocf_ps': latest['ocf_ps'],
                }

                # 趋势分析（比较最近几期）
                if len(fin['periods']) >= 3:
                    fin['trend'] = self._analyze_financial_trend(fin['periods'])

        except Exception as e:
            fin['error'] = str(e)

        return fin

    def _analyze_financial_trend(self, periods: list) -> dict:
        """分析财务指标趋势"""
        trend = {}

        # 收入增长趋势
        rev_yoys = []
        profit_yoys = []
        roes = []
        gross_margins = []

        for p in periods:
            rev_yoy = self._safe_float(p.get('revenue_yoy', '0').replace('%', ''))
            profit_yoy = self._safe_float(p.get('net_profit_yoy', '0').replace('%', ''))
            roe = self._safe_float(p.get('roe', '0').replace('%', ''))
            gm = self._safe_float(p.get('gross_margin', '0').replace('%', ''))

            if rev_yoy != 0:
                rev_yoys.append(rev_yoy)
            if profit_yoy != 0:
                profit_yoys.append(profit_yoy)
            if roe != 0:
                roes.append(roe)
            if gm != 0:
                gross_margins.append(gm)

        # 营收趋势
        if len(rev_yoys) >= 2:
            if all(r > 0 for r in rev_yoys):
                trend['revenue_trend'] = '持续增长'
            elif all(r < 0 for r in rev_yoys):
                trend['revenue_trend'] = '持续下滑'
            elif rev_yoys[0] > rev_yoys[-1]:
                trend['revenue_trend'] = '增速放缓'
            else:
                trend['revenue_trend'] = '增速回升'

        # 利润趋势
        if len(profit_yoys) >= 2:
            if all(p > 0 for p in profit_yoys):
                trend['profit_trend'] = '持续增长'
            elif all(p < 0 for p in profit_yoys):
                trend['profit_trend'] = '持续下滑'
            elif profit_yoys[0] > profit_yoys[-1]:
                trend['profit_trend'] = '增速放缓'
            else:
                trend['profit_trend'] = '增速回升'

        # ROE趋势
        if len(roes) >= 2:
            if roes[0] > roes[-1]:
                trend['roe_trend'] = '下降'
            else:
                trend['roe_trend'] = '上升'

        # 毛利率趋势
        if len(gross_margins) >= 2:
            if gross_margins[0] > gross_margins[-1]:
                trend['gross_margin_trend'] = '下滑（成本压力）'
            else:
                trend['gross_margin_trend'] = '改善'

        return trend

    def _get_valuation_analysis(self, market: str, symbol: str) -> dict:
        """估值分析"""
        valuation = {}

        try:
            hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if hist is not None and len(hist) >= 250:
                close_col = self._safe_get_column(hist, 'close', '收盘')
                year_start = hist.iloc[-250][close_col]
                year_end = hist.iloc[-1][close_col]
                ytd_return = round((year_end - year_start) / year_start * 100, 2)

                returns = hist[close_col].pct_change().dropna()
                volatility = round(float(returns.std() * np.sqrt(250) * 100), 2)

                # 计算历史分位数
                close_prices = hist[close_col]
                current_price = close_prices.iloc[-1]
                percentile = round(float((close_prices < current_price).sum() / len(close_prices) * 100), 1)

                # 近期支撑/压力位
                recent_60 = close_prices.tail(60)
                support = round(float(recent_60.min()), 2)
                resistance = round(float(recent_60.max()), 2)

                valuation = {
                    '近一年涨跌幅': ytd_return,
                    '年化波动率': volatility,
                    '近一年最高': round(float(close_prices.tail(250).max()), 2),
                    '近一年最低': round(float(close_prices.tail(250).min()), 2),
                    '价格历史分位数': f'{percentile}%',
                    '60日支撑位': support,
                    '60日压力位': resistance,
                    '距支撑位幅度': f'{round((current_price - support) / support * 100, 2)}%',
                    '距压力位幅度': f'{round((resistance - current_price) / current_price * 100, 2)}%',
                }

                # 结合财务数据计算PE/PB（如果有的话）
                try:
                    fin_df = ak.stock_financial_abstract_ths(symbol=symbol)
                    if fin_df is not None and len(fin_df) > 0:
                        eps = self._safe_float(fin_df.iloc[0].get('基本每股收益', 0))
                        bps = self._safe_float(fin_df.iloc[0].get('每股净资产', 0))

                        if eps > 0:
                            pe = round(float(current_price) / eps, 2)
                            valuation['PE(动态)'] = pe
                            # PE评价
                            if pe < 15:
                                valuation['PE评价'] = '低估'
                            elif pe < 30:
                                valuation['PE评价'] = '合理'
                            elif pe < 50:
                                valuation['PE评价'] = '偏高'
                            else:
                                valuation['PE评价'] = '高估'

                        if bps > 0:
                            pb = round(float(current_price) / bps, 2)
                            valuation['PB'] = pb
                            if pb < 1:
                                valuation['PB评价'] = '破净'
                            elif pb < 3:
                                valuation['PB评价'] = '合理'
                            elif pb < 5:
                                valuation['PB评价'] = '偏高'
                            else:
                                valuation['PB评价'] = '高估'

                        # PEG（如果有预测数据）
                        try:
                            forecast = ak.stock_profit_forecast_ths(symbol=symbol, indicator='预测年报净利润')
                            if forecast is not None and len(forecast) > 0:
                                # 计算预期增长率
                                mean_forecast = self._safe_float(forecast.iloc[0].get('均值', 0))
                                valuation['机构预测净利润(亿)'] = mean_forecast
                        except:
                            pass
                except:
                    pass

        except Exception as e:
            valuation['error'] = str(e)

        return valuation

    def _get_industry_analysis(self, symbol: str) -> dict:
        """行业与业务板块分析"""
        industry = {'identified_industry': [], 'business_segments': [], 'industry_outlook': ''}

        # 优先使用硬编码映射
        if symbol in self.STOCK_INDUSTRY:
            mapped = self.STOCK_INDUSTRY[symbol]
            industry['identified_industry'].append({
                'name': mapped,
                'source': '预设映射',
                'keyword_hits': 99
            })
            industry['industry_outlook'] = self._get_industry_outlook(mapped)

        # 尝试从新闻中补充识别
        try:
            news_df = ak.stock_news_em(symbol=symbol)
            if news_df is not None and len(news_df) > 0:
                all_text = ' '.join([
                    str(row.get('新闻标题', '')) + ' ' + str(row.get('新闻内容', ''))[:300]
                    for _, row in news_df.head(15).iterrows()
                ])

                # 识别行业
                existing = [i['name'] for i in industry['identified_industry']]
                for ind_name, keywords in self.INDUSTRY_KEYWORDS.items():
                    if ind_name in existing:
                        continue
                    count = sum(all_text.count(kw) for kw in keywords)
                    if count >= 3:
                        industry['identified_industry'].append({
                            'name': ind_name,
                            'source': '新闻识别',
                            'keyword_hits': count
                        })

                industry['identified_industry'].sort(key=lambda x: x['keyword_hits'], reverse=True)

                # 从新闻提取业务板块信息
                segment_keywords = {
                    '汽车电子': ['汽车电子', '车载', '智能座舱', '域控制器'],
                    '智能家居': ['智能家居', '家电控制', 'IoT'],
                    '智能硬件': ['智能硬件', '可穿戴', 'TWS'],
                    '射频芯片': ['射频', 'RF', '天线', '5G'],
                    '微处理器': ['MCU', '微处理器', 'SoC', '处理器'],
                    '电池管理': ['BMS', '电池管理', '储能'],
                    '传感器': ['传感器', 'MEMS', '感知'],
                }

                for seg_name, seg_kws in segment_keywords.items():
                    count = sum(all_text.count(kw) for kw in seg_kws)
                    if count >= 2:
                        industry['business_segments'].append({
                            'name': seg_name,
                            'hits': count
                        })
        except:
            pass

        # 行业发展判断（基于识别到的行业）
        if industry['identified_industry'] and not industry['industry_outlook']:
            top_industry = industry['identified_industry'][0]['name']
            industry['industry_outlook'] = self._get_industry_outlook(top_industry)

        return industry

    def _get_industry_outlook(self, industry_name: str) -> str:
        """行业前景判断"""
        outlook_map = {
            '半导体': '国产替代加速，AI芯片需求爆发，行业景气度上行',
            '消费电子': 'AI终端驱动换机潮，短期承压但中长期看好',
            '新能源': '双碳政策支持，产能过剩隐忧，头部企业优势加大',
            '汽车': '智能化+电动化双轮驱动，竞争加剧但赛道空间大',
            '医药': '集采常态化，创新药出海加速，行业分化明显',
            '食品饮料': '消费复苏缓慢，高端化趋势延续，防御属性强',
            '金融': '利率下行压力，净息差收窄，但估值处于历史低位',
            '房地产': '政策放松但需求疲弱，行业出清进行中',
            '军工': '地缘政治紧张，国防预算增长确定性强',
            'TMT': 'AI革命驱动，云计算/大数据高景气，但估值偏高',
            '高端制造': '国产替代+制造业升级，政策支持力度大',
            '新材料': '战略性新兴产业，进口替代空间大，技术壁垒高',
        }
        return outlook_map.get(industry_name, '行业前景需进一步分析')

    def _get_profit_forecast(self, symbol: str) -> dict:
        """机构盈利预测"""
        forecast = {}

        try:
            df = ak.stock_profit_forecast_ths(symbol=symbol, indicator='预测年报净利润')
            if df is not None and len(df) > 0:
                forecast['forecasts'] = []
                for _, row in df.iterrows():
                    forecast['forecasts'].append({
                        'year': str(row.get('年度', '')),
                        'analyst_count': int(self._safe_float(row.get('预测机构数', 0))),
                        'min': self._safe_float(row.get('最小值', 0)),
                        'mean': self._safe_float(row.get('均值', 0)),
                        'max': self._safe_float(row.get('最大值', 0)),
                        'industry_avg': self._safe_float(row.get('行业平均数', 0)),
                    })

                # 计算增长预期
                if len(forecast['forecasts']) >= 2:
                    cur = forecast['forecasts'][0].get('mean', 0)
                    nxt = forecast['forecasts'][1].get('mean', 0)
                    if cur > 0:
                        growth_rate = round((nxt - cur) / cur * 100, 2)
                        forecast['expected_growth'] = f'{growth_rate}%'
                        forecast['growth_direction'] = '上升' if growth_rate > 0 else '下降'

                # 机构覆盖度
                if forecast['forecasts']:
                    forecast['analyst_coverage'] = forecast['forecasts'][0].get('analyst_count', 0)
                    if forecast['analyst_coverage'] >= 10:
                        forecast['coverage_level'] = '高关注度'
                    elif forecast['analyst_coverage'] >= 5:
                        forecast['coverage_level'] = '中等关注'
                    else:
                        forecast['coverage_level'] = '低关注度'

        except Exception as e:
            forecast['error'] = str(e)

        return forecast

    def _get_balance_sheet_highlights(self, symbol: str) -> dict:
        """资产负债表关键指标"""
        bs = {}

        try:
            df = ak.stock_financial_report_sina(stock=symbol, symbol='资产负债表')
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                bs = {
                    'report_date': str(latest.get('报告日', ''))[:10],
                    'cash': self._parse_chinese_number(str(latest.get('货币资金', '0'))),
                    'accounts_receivable': self._parse_chinese_number(str(latest.get('应收票据及应收账款', '0'))),
                    'inventory': self._parse_chinese_number(str(latest.get('存货', '0'))),
                    'total_assets': self._parse_chinese_number(str(latest.get('资产总计', '0'))),
                    'total_liabilities': self._parse_chinese_number(str(latest.get('负债合计', '0'))),
                    'total_equity': self._parse_chinese_number(str(latest.get('所有者权益合计', '0'))),
                }

                # 计算关键比率
                if bs['total_assets'] > 0:
                    bs['cash_ratio'] = f'{round(bs["cash"] / bs["total_assets"] * 100, 2)}%'
                    bs['debt_to_asset'] = f'{round(bs["total_liabilities"] / bs["total_assets"] * 100, 2)}%'

                # 现金充裕度
                if bs['cash'] > 0 and bs['total_assets'] > 0:
                    cash_pct = bs['cash'] / bs['total_assets'] * 100
                    if cash_pct > 30:
                        bs['cash_status'] = '现金充裕'
                    elif cash_pct > 15:
                        bs['cash_status'] = '现金一般'
                    else:
                        bs['cash_status'] = '现金偏紧'

                # 应收账款风险
                if bs['accounts_receivable'] > 0 and bs['total_assets'] > 0:
                    ar_pct = bs['accounts_receivable'] / bs['total_assets'] * 100
                    if ar_pct > 30:
                        bs['ar_risk'] = '应收账款占比过高'
                    elif ar_pct > 15:
                        bs['ar_risk'] = '应收账款需关注'
                    else:
                        bs['ar_risk'] = '应收账款正常'

        except Exception as e:
            bs['error'] = str(e)

        return bs

    def _analyze_performance_trend(self, fundamental: dict) -> dict:
        """综合业绩趋势判断"""
        trend = {
            'overall_trend': '中性',
            'financial_trend': '中性',
            'valuation_trend': '中性',
            'forecast_trend': '中性',
            'reasons': []
        }

        # 1. 财务趋势
        fin = fundamental.get('financial', {})
        fin_trend = fin.get('trend', {})
        if fin_trend:
            rev_trend = fin_trend.get('revenue_trend', '')
            profit_trend = fin_trend.get('profit_trend', '')
            roe_trend = fin_trend.get('roe_trend', '')
            gm_trend = fin_trend.get('gross_margin_trend', '')

            positive_count = sum([
                1 for t in [rev_trend, profit_trend]
                if '增长' in t or '回升' in t
            ])
            negative_count = sum([
                1 for t in [rev_trend, profit_trend, roe_trend, gm_trend]
                if '下滑' in t or '下降' in t or '放缓' in t or '压力' in t
            ])

            if positive_count >= 2 and negative_count == 0:
                trend['financial_trend'] = '向好'
                trend['reasons'].append(f'营收{rev_trend}，利润{profit_trend}')
            elif negative_count >= 2:
                trend['financial_trend'] = '承压'
                trend['reasons'].append(f'营收{rev_trend}，利润{profit_trend}，毛利率{gm_trend}')
            else:
                trend['financial_trend'] = '分化'
                trend['reasons'].append(f'营收{rev_trend}，利润{profit_trend}')

        # 2. 估值趋势
        val = fundamental.get('valuation', {})
        if val:
            pe_eval = val.get('PE评价', '')
            pb_eval = val.get('PB评价', '')
            percentile = val.get('价格历史分位数', '50%')

            if '低估' in pe_eval or '破净' in pb_eval:
                trend['valuation_trend'] = '低估'
                trend['reasons'].append(f'PE{pe_eval}，PB{pb_eval}，历史分位{percentile}')
            elif '高估' in pe_eval or '偏高' in pe_eval:
                trend['valuation_trend'] = '偏高'
                trend['reasons'].append(f'PE{pe_eval}，PB{pb_eval}，历史分位{percentile}')
            else:
                trend['valuation_trend'] = '合理'
                trend['reasons'].append(f'PE{pe_eval}，历史分位{percentile}')

        # 3. 预测趋势
        forecast = fundamental.get('profit_forecast', {})
        if forecast:
            growth_dir = forecast.get('growth_direction', '')
            expected_growth = forecast.get('expected_growth', '')
            if growth_dir == '上升':
                trend['forecast_trend'] = '业绩预期上行'
                trend['reasons'].append(f'机构预测增长{expected_growth}')
            elif growth_dir == '下降':
                trend['forecast_trend'] = '业绩预期下行'
                trend['reasons'].append(f'机构预测下滑{expected_growth}')
            else:
                trend['forecast_trend'] = '预期平稳'

        # 4. 综合判断
        positive = sum([
            1 for t in [trend['financial_trend'], trend['valuation_trend'], trend['forecast_trend']]
            if t in ['向好', '低估', '业绩预期上行']
        ])
        negative = sum([
            1 for t in [trend['financial_trend'], trend['valuation_trend'], trend['forecast_trend']]
            if t in ['承压', '偏高', '业绩预期下行']
        ])

        if positive >= 2:
            trend['overall_trend'] = '基本面向好'
        elif negative >= 2:
            trend['overall_trend'] = '基本面承压'
        else:
            trend['overall_trend'] = '基本面中性'

        return trend

    def _score_fundamental(self, fundamental: dict) -> dict:
        """综合基本面评分"""
        score = 50
        reasons = []

        # 1. 财务数据评分
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        trend = fin.get('trend', {})

        # ROE
        roe = self._safe_float(str(latest.get('roe', '0')).replace('%', ''))
        if roe > 20:
            score += 15
            reasons.append(f'ROE优秀({roe}%)')
        elif roe > 15:
            score += 10
            reasons.append(f'ROE良好({roe}%)')
        elif roe > 10:
            score += 5
            reasons.append(f'ROE一般({roe}%)')
        elif roe > 0:
            score -= 5
            reasons.append(f'ROE偏低({roe}%)')
        else:
            score -= 15
            reasons.append(f'ROE为负({roe}%)')

        # 净利润增速
        profit_yoy = self._safe_float(str(latest.get('net_profit_yoy', '0')).replace('%', ''))
        if profit_yoy > 30:
            score += 10
            reasons.append(f'净利润高增长({profit_yoy}%)')
        elif profit_yoy > 10:
            score += 5
            reasons.append(f'净利润稳健增长({profit_yoy}%)')
        elif profit_yoy > 0:
            score += 0
        elif profit_yoy > -10:
            score -= 5
            reasons.append(f'净利润小幅下滑({profit_yoy}%)')
        else:
            score -= 10
            reasons.append(f'净利润大幅下滑({profit_yoy}%)')

        # 毛利率
        gm = self._safe_float(str(latest.get('gross_margin', '0')).replace('%', ''))
        if gm > 50:
            score += 10
            reasons.append(f'高毛利率({gm}%)')
        elif gm > 30:
            score += 5
            reasons.append(f'毛利率良好({gm}%)')
        elif gm > 15:
            score += 0
        else:
            score -= 5
            reasons.append(f'毛利率偏低({gm}%)')

        # 财务趋势
        if trend:
            if trend.get('revenue_trend', '') in ['持续增长', '增速回升']:
                score += 5
            elif trend.get('revenue_trend', '') in ['持续下滑']:
                score -= 5
            if trend.get('gross_margin_trend', '') == '改善':
                score += 5
            elif '下滑' in trend.get('gross_margin_trend', ''):
                score -= 5

        # 2. 估值评分
        val = fundamental.get('valuation', {})
        pe_eval = val.get('PE评价', '')
        if '低估' in pe_eval:
            score += 10
            reasons.append('估值低估')
        elif '合理' in pe_eval:
            score += 5
        elif '偏高' in pe_eval:
            score -= 5
            reasons.append('估值偏高')
        elif '高估' in pe_eval:
            score -= 10
            reasons.append('估值高估')

        # 3. 业绩趋势评分
        perf = fundamental.get('performance_trend', {})
        if perf.get('overall_trend') == '基本面向好':
            score += 10
        elif perf.get('overall_trend') == '基本面承压':
            score -= 10

        # 4. 机构预测评分
        forecast = fundamental.get('profit_forecast', {})
        if forecast.get('growth_direction') == '上升':
            score += 5
            reasons.append('机构预测增长')
        elif forecast.get('growth_direction') == '下降':
            score -= 5
            reasons.append('机构预测下滑')

        return {
            'score': max(0, min(100, score)),
            'reasons': reasons
        }

    # ==================== 4. 消息面分析（增强版）====================
    def _get_news_analysis_v2(self, symbol: str, fundamental: dict) -> dict:
        """增强版消息面分析：结合基本面影响判断"""
        news_data = {'items': [], 'summary': '', 'impact_on_fundamentals': []}

        try:
            news_df = ak.stock_news_em(symbol=symbol)
            if news_df is not None and len(news_df) > 0:
                for idx, row in news_df.head(15).iterrows():
                    title = str(row.get('新闻标题', ''))
                    content = str(row.get('新闻内容', ''))[:500]
                    news_data['items'].append({
                        'title': title,
                        'content': content,
                        'date': str(row.get('发布日期', ''))
                    })
        except Exception as e:
            news_data['error'] = str(e)

        # 增强版情感分析 + 基本面影响判断
        all_text = ' '.join([n.get('title', '') + ' ' + n.get('content', '') for n in news_data['items']])

        # 情感分析
        sentiment_score = 0
        positive_keywords = ['增长', '盈利', '突破', '创新', '扩张', '合作', '增持', '买入', '看好',
                           '上调', '超预期', '订单', '量产', '中标', '获批', '首发', '分红']
        negative_keywords = ['下跌', '亏损', '风险', '减持', '卖出', '下调', '不及预期', '警告', '调查',
                           '诉讼', '处罚', '退市', '质押', '债务', '违约', '爆雷', '破产']

        for kw in positive_keywords:
            sentiment_score += all_text.count(kw) * 2
        for kw in negative_keywords:
            sentiment_score -= all_text.count(kw) * 2

        news_data['sentiment'] = '偏多' if sentiment_score > 5 else ('偏空' if sentiment_score < -5 else '中性')
        news_data['sentiment_score'] = sentiment_score

        # ===== 消息面对基本面的影响判断 =====
        impacts = []

        # 业绩相关
        if any(kw in all_text for kw in ['业绩预增', '业绩超预期', '净利增长', '营收增长']):
            impacts.append({
                'area': '业绩表现',
                'impact': '正面',
                'detail': '新闻显示业绩向好，可能带来基本面改善'
            })
        elif any(kw in all_text for kw in ['业绩预减', '业绩不及预期', '净利下滑', '亏损']):
            impacts.append({
                'area': '业绩表现',
                'impact': '负面',
                'detail': '新闻显示业绩承压，基本面可能恶化'
            })

        # 订单/业务
        if any(kw in all_text for kw in ['大单', '中标', '订单', '签约', '合作']):
            impacts.append({
                'area': '业务拓展',
                'impact': '正面',
                'detail': '新订单/合作有望提升未来营收'
            })

        # 减持/增持
        if any(kw in all_text for kw in ['减持', '套现']):
            impacts.append({
                'area': '股东信心',
                'impact': '负面',
                'detail': '股东减持反映信心不足'
            })
        elif any(kw in all_text for kw in ['增持', '回购']):
            impacts.append({
                'area': '股东信心',
                'impact': '正面',
                'detail': '股东增持/回购反映看好前景'
            })

        # 行业政策
        if any(kw in all_text for kw in ['政策利好', '补贴', '扶持', '国标', '规划']):
            impacts.append({
                'area': '行业政策',
                'impact': '正面',
                'detail': '政策利好可能带来行业机遇'
            })
        elif any(kw in all_text for kw in ['监管', '处罚', '限制', '整顿']):
            impacts.append({
                'area': '行业政策',
                'impact': '负面',
                'detail': '监管趋严可能影响业务开展'
            })

        # 技术突破/新产品
        if any(kw in all_text for kw in ['发布新品', '技术突破', '量产', '首发', '突破']):
            impacts.append({
                'area': '技术创新',
                'impact': '正面',
                'detail': '技术突破/新产品有望打开新增长点'
            })

        # 大宗交易
        if any(kw in all_text for kw in ['大宗交易']):
            if any(kw in all_text for kw in ['折价']):
                impacts.append({
                    'area': '资金动向',
                    'impact': '负面',
                    'detail': '大宗交易折价成交，暗示机构减仓'
                })

        news_data['impact_on_fundamentals'] = impacts

        # 综合消息面影响评分
        positive_impacts = sum(1 for i in impacts if i['impact'] == '正面')
        negative_impacts = sum(1 for i in impacts if i['impact'] == '负面')

        if positive_impacts > negative_impacts:
            news_data['fundamental_impact'] = '消息面利好基本面'
        elif negative_impacts > positive_impacts:
            news_data['fundamental_impact'] = '消息面利空基本面'
        else:
            news_data['fundamental_impact'] = '消息面中性'

        return news_data

    # ==================== 5. 资金面分析 ====================
    def _get_money_flow(self, symbol: str) -> dict:
        """获取资金流向"""
        money_flow = {}

        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market='sh' if symbol.startswith('6') else 'sz')
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                money_flow['main_flow'] = {
                    'date': str(latest.get('日期', ''))[:10],
                    'main_net': float(latest.get('主力净流入', 0)) / 100000000,
                    'main_pct': float(latest.get('主力净流入占比(%)', 0)),
                    'retail_net': float(latest.get('散户净流入', 0)) / 100000000,
                }
        except Exception as e:
            money_flow['flow_error'] = str(e)

        flow_score = 0
        if 'main_flow' in money_flow:
            net_flow = money_flow['main_flow'].get('main_net', 0)
            if net_flow > 0:
                flow_score += 10
            else:
                flow_score -= 10

        money_flow['score'] = max(0, min(100, 50 + flow_score))

        return money_flow

    # ==================== 6. 综合建议（增强版）====================
    def _generate_suggestion_v2(self, result: dict) -> dict:
        """增强版综合投资建议"""
        total_score = 50

        # 技术面评分（权重35%）
        tech = result.get('technical', {})
        if 'scores' in tech:
            scores = tech['scores']
            tech_score = scores.get('trend', 0) + scores.get('kdj', 0) + scores.get('rsi', 0) + scores.get('macd', 0)
            total_score += tech_score * 0.35

        # 基本面评分（权重35%）
        fund = result.get('fundamental', {})
        if 'score' in fund:
            total_score += (fund['score'] - 50) * 0.35

        # 业绩趋势额外调整
        perf_trend = fund.get('performance_trend', {})
        if perf_trend.get('overall_trend') == '基本面向好':
            total_score += 5
        elif perf_trend.get('overall_trend') == '基本面承压':
            total_score -= 5

        # 消息面影响调整
        news = result.get('news', {})
        fund_impact = news.get('fundamental_impact', '')
        if '利好' in fund_impact:
            total_score += 5
        elif '利空' in fund_impact:
            total_score -= 5

        # 资金面评分（权重15%）
        money = result.get('money_flow', {})
        if 'score' in money:
            total_score += (money['score'] - 50) * 0.15

        # 消息面情感（权重15%）
        sentiment = news.get('sentiment', '中性')
        if sentiment == '偏多':
            total_score += 7.5
        elif sentiment == '偏空':
            total_score -= 7.5

        total_score = max(0, min(100, round(total_score)))

        # 生成建议
        if total_score >= 70:
            action, level = '积极买入', '积极'
        elif total_score >= 58:
            action, level = '适量买入', '谨慎乐观'
        elif total_score >= 45:
            action, level = '观望', '谨慎'
        elif total_score >= 30:
            action, level = '谨慎卖出', '风险'
        else:
            action, level = '建议卖出', '高风险'

        price = result.get('quote', {}).get('price', 0)

        # 动态目标价（根据基本面调整）
        fund_score = fund.get('score', 50)
        if fund_score >= 70:
            target_pct = 1.15
        elif fund_score >= 50:
            target_pct = 1.10
        else:
            target_pct = 1.05

        return {
            'total_score': total_score,
            'action': action,
            'level': level,
            'target_price': round(price * target_pct, 2) if price > 0 else 0,
            'stop_loss': round(price * 0.95, 2) if price > 0 else 0,
            'position': f'{min(30, max(5, total_score // 3))}%',
            'fundamental_trend': perf_trend.get('overall_trend', '中性'),
            'news_impact': fund_impact,
            'score_breakdown': {
                'tech_weight': '35%',
                'fundamental_weight': '35%',
                'money_flow_weight': '15%',
                'news_sentiment_weight': '15%'
            }
        }


def main():
    import json

    if len(sys.argv) < 2:
        print(json.dumps({'error': '请提供股票代码'}, ensure_ascii=False, indent=2))
        return

    code = sys.argv[1]
    analyzer = StockFullAnalyzer()
    result = analyzer.get_full_analysis(code)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
