# -*- coding: utf-8 -*-
"""
股票完整分析 - 统一版 v4.0

架构变更：
- 数据层：由外部（tushare-data skill）通过 JSON 文件传入，不再自行获取
- 分析层：技术指标 + K线形态 + 缠论 + 信号共振 + 情绪指数 + 基本面评分 + 综合建议
- 输出：完整 JSON

用法：
  python full_analysis.py <data_json_path> [code]
  - data_json_path: tushare-data 预取的 JSON 数据文件路径
  - code: 股票代码（6位数字），如果不传则从数据文件中读取
"""
import sys
import io
import os
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patterns import CandlestickPatternRecognizer, ChanlunAnalyzer
from signals import SignalResonanceScorer
from ai_models import SentimentIndexCalculator
from signals.scoring import SignalType, SignalDirection, Signal


class StockAnalyzer:
    """股票统一分析器 v4.0 - 纯分析层"""

    # 行业关键词映射
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

    def __init__(self):
        pass

    def _safe_float(self, val, default=0.0):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return default
        try:
            if isinstance(val, str):
                val = val.replace('%', '').replace(',', '').replace('亿', 'e8').replace('万', 'e4')
                if val in ['False', 'true', '--', '', '-']:
                    return default
            return float(val)
        except (ValueError, TypeError):
            return default

    def analyze(self, data: dict, code: str) -> dict:
        """
        主分析入口

        Args:
            data: tushare-data 预取的数据字典，包含:
                - daily: 日线行情 DataFrame (JSON)
                - daily_basic: 每日指标 DataFrame (JSON)
                - income: 利润表 DataFrame (JSON)
                - fina_indicator: 财务指标 DataFrame (JSON)
                - moneyflow: 资金流向 DataFrame (JSON)
                - news: 新闻 DataFrame (JSON)
                - forecast: 盈利预测 DataFrame (JSON)
            code: 6位股票代码
        """
        result = {
            'success': False,
            'code': code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            # 构建日线 DataFrame
            df = self._build_daily_df(data.get('daily'))
            if df is None or len(df) < 20:
                return {**result, 'error': f'日线数据不足({len(df) if df is not None else 0}行)，至少需要20个交易日'}

            # 1. 行情概览
            result['quote'] = self._analyze_quote(df, data.get('daily_basic'))

            # 2. 技术分析（统一计算，供所有模块共享）
            tech_result, df_with_indicators = self._analyze_technical(df)
            result['technical'] = tech_result

            # 3. K线形态识别
            result['patterns'] = self._analyze_patterns(df_with_indicators)

            # 4. 缠论分析
            result['chanlun'] = self._analyze_chanlun(df_with_indicators)

            # 5. 信号共振评分
            result['signal_resonance'] = self._analyze_signal_resonance(
                df_with_indicators, result['patterns'], result['chanlun'],
                data.get('fina_indicator')
            )

            # 6. 情绪指数
            result['sentiment'] = self._analyze_sentiment(df_with_indicators)

            # 7. 基本面分析
            result['fundamental'] = self._analyze_fundamental(
                data.get('income'), data.get('fina_indicator'),
                data.get('daily_basic'), df, code
            )

            # 8. 资金流向分析
            result['money_flow'] = self._analyze_money_flow(data.get('moneyflow'))

            # 9. 消息面分析
            result['news'] = self._analyze_news(data.get('news'), code)

            # 10. 盈利预测
            result['forecast'] = self._analyze_forecast(data.get('forecast'))

            # 11. 综合建议
            result['suggestion'] = self._generate_suggestion(result)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            import traceback
            result['trace'] = str(traceback.format_exc())[:500]

        return result

    # ==================== 数据构建 ====================
    def _build_daily_df(self, daily_data) -> pd.DataFrame:
        """从 Tushare JSON 数据构建日线 DataFrame"""
        if daily_data is None:
            return None
        try:
            if isinstance(daily_data, str):
                df = pd.read_json(daily_data, orient='records')
            elif isinstance(daily_data, list):
                df = pd.DataFrame(daily_data)
            elif isinstance(daily_data, pd.DataFrame):
                df = daily_data
            else:
                return None

            if len(df) == 0:
                return None

            # 统一列名映射 (Tushare -> 标准名)
            col_map = {
                'trade_date': 'date', 'open': 'open', 'high': 'high',
                'low': 'low', 'close': 'close', 'vol': 'volume',
                'amount': 'amount', 'pct_chg': 'pct_change',
                'pre_close': 'pre_close', 'change': 'change'
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

            # 确保数值类型
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 按日期排序
            if 'date' in df.columns:
                df = df.sort_values('date').reset_index(drop=True)

            return df
        except Exception:
            return None

    # ==================== 1. 行情概览 ====================
    def _analyze_quote(self, df: pd.DataFrame, daily_basic) -> dict:
        """行情概览"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        price = float(latest['close'])
        prev_price = float(prev['close'])
        pct_change = self._safe_float(latest.get('pct_change', 0))
        if pct_change == 0 and prev_price > 0:
            pct_change = round((price - prev_price) / prev_price * 100, 2)

        quote = {
            'price': price,
            'change': round(price - prev_price, 2),
            'pct_change': pct_change,
            'open': float(latest.get('open', 0)),
            'high': float(latest.get('high', 0)),
            'low': float(latest.get('low', 0)),
            'volume': int(latest.get('volume', 0)),
            'amount': round(float(latest.get('amount', 0)) / 1000, 2),  # 千元 -> 万元
            'date': str(latest.get('date', '')),
        }

        # 从 daily_basic 补充 PE/PB/换手率等
        if daily_basic is not None:
            try:
                if isinstance(daily_basic, str):
                    db_df = pd.read_json(daily_basic, orient='records')
                elif isinstance(daily_basic, list):
                    db_df = pd.DataFrame(daily_basic)
                else:
                    db_df = daily_basic

                if len(db_df) > 0:
                    db_latest = db_df.iloc[-1]
                    quote['turnover_rate'] = self._safe_float(db_latest.get('turnover_rate', 0))
                    quote['pe'] = self._safe_float(db_latest.get('pe', 0))
                    quote['pe_ttm'] = self._safe_float(db_latest.get('pe_ttm', 0))
                    quote['pb'] = self._safe_float(db_latest.get('pb', 0))
                    quote['total_mv'] = self._safe_float(db_latest.get('total_mv', 0))  # 万元
                    quote['circ_mv'] = self._safe_float(db_latest.get('circ_mv', 0))
            except Exception:
                pass

        return quote

    # ==================== 2. 技术分析（统一计算） ====================
    def _analyze_technical(self, df: pd.DataFrame) -> tuple:
        """
        统一计算技术指标，返回 (分析结果dict, 带指标的DataFrame)
        DataFrame 供后续 K线形态/缠论/信号共振/情绪指数共享使用
        """
        df = df.copy()

        # 均线系统
        for period in [5, 10, 20, 60]:
            df[f'ma{period}'] = df['close'].rolling(window=period).mean()

        # RSI(14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)

        # KDJ
        low9 = df['low'].rolling(window=9).min()
        high9 = df['high'].rolling(window=9).max()
        rsv = (df['close'] - low9) / (high9 - low9).replace(0, np.nan) * 100
        rsv = rsv.fillna(50)
        df['k'] = rsv.ewm(com=2).mean()
        df['d'] = df['k'].ewm(com=2).mean()
        df['j'] = 3 * df['k'] - 2 * df['d']

        # MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd_dif'] = exp12 - exp26
        df['macd_dea'] = df['macd_dif'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd_dif'] - df['macd_dea']

        # 布林带
        df['boll_mid'] = df['close'].rolling(window=20).mean()
        boll_std = df['close'].rolling(window=20).std()
        df['boll_upper'] = df['boll_mid'] + 2 * boll_std
        df['boll_lower'] = df['boll_mid'] - 2 * boll_std

        # 提取分析结果
        latest = df.iloc[-1]
        price = latest['close']

        # 趋势判断
        ma5 = latest['ma5']
        ma20 = latest['ma20']
        ma60 = latest.get('ma60', ma20)
        if pd.isna(ma60):
            ma60 = ma20

        if ma5 > ma20 > ma60:
            trend, trend_score = '上升趋势', 20
        elif ma5 < ma20 < ma60:
            trend, trend_score = '下降趋势', -20
        elif ma5 > ma20:
            trend, trend_score = '震荡偏强', 10
        else:
            trend, trend_score = '震荡偏弱', -10

        # KDJ 信号
        k, d_val = latest['k'], latest['d']
        if k > 80:
            kdj_signal, kdj_score = '超买区', -15
        elif k < 20:
            kdj_signal, kdj_score = '超卖区', 15
        elif k > d_val:
            kdj_signal, kdj_score = '金叉', 5
        else:
            kdj_signal, kdj_score = '死叉', -5

        # RSI 信号
        rsi = latest['rsi']
        if rsi > 70:
            rsi_signal, rsi_score = '超买', -10
        elif rsi < 30:
            rsi_signal, rsi_score = '超卖', 10
        else:
            rsi_signal, rsi_score = '正常', 0

        # MACD 信号
        macd_dif = latest['macd_dif']
        macd_dea = latest['macd_dea']
        if macd_dif > macd_dea and macd_dif > 0:
            macd_signal, macd_score = '多头', 10
        elif macd_dif < macd_dea and macd_dif < 0:
            macd_signal, macd_score = '空头', -10
        else:
            macd_signal, macd_score = '盘整', 0

        tech_result = {
            'ma5': round(float(ma5), 2),
            'ma10': round(float(latest['ma10']), 2),
            'ma20': round(float(ma20), 2),
            'ma60': round(float(ma60), 2) if not pd.isna(ma60) else None,
            'price_above_ma5': bool(price > ma5),
            'price_above_ma20': bool(price > ma20),
            'price_above_ma60': bool(price > ma60),
            'rsi': round(float(rsi), 2),
            'rsi_signal': rsi_signal,
            'k': round(float(k), 2),
            'd': round(float(d_val), 2),
            'j': round(float(latest['j']), 2),
            'kdj_signal': kdj_signal,
            'macd_dif': round(float(macd_dif), 2),
            'macd_dea': round(float(macd_dea), 2),
            'macd_hist': round(float(latest['macd_hist']), 2),
            'macd_signal': macd_signal,
            'trend': trend,
            'boll_upper': round(float(latest['boll_upper']), 2) if not pd.isna(latest['boll_upper']) else None,
            'boll_mid': round(float(latest['boll_mid']), 2) if not pd.isna(latest['boll_mid']) else None,
            'boll_lower': round(float(latest['boll_lower']), 2) if not pd.isna(latest['boll_lower']) else None,
            'scores': {
                'trend': trend_score,
                'kdj': kdj_score,
                'rsi': rsi_score,
                'macd': macd_score
            }
        }

        return tech_result, df

    # ==================== 3. K线形态识别 ====================
    def _analyze_patterns(self, df: pd.DataFrame) -> dict:
        """K线形态识别"""
        try:
            recognizer = CandlestickPatternRecognizer()
            results = recognizer.recognize_all(df, lookback=5)

            # 分类
            bullish = [r for r in results if r.pattern_type.value == 'BULLISH']
            bearish = [r for r in results if r.pattern_type.value == 'BEARISH']

            # 取 top 形态
            top_bullish = sorted(bullish, key=lambda x: x.confidence, reverse=True)[:5]
            top_bearish = sorted(bearish, key=lambda x: x.confidence, reverse=True)[:5]

            return {
                'total_patterns': len(results),
                'bullish_count': len(bullish),
                'bearish_count': len(bearish),
                'top_bullish': [
                    {
                        'name': p.name,
                        'name_cn': p.name_cn,
                        'description': p.description,
                        'confidence': round(p.confidence, 2),
                        'reliability': p.reliability
                    }
                    for p in top_bullish
                ],
                'top_bearish': [
                    {
                        'name': p.name,
                        'name_cn': p.name_cn,
                        'description': p.description,
                        'confidence': round(p.confidence, 2),
                        'reliability': p.reliability
                    }
                    for p in top_bearish
                ]
            }
        except Exception as e:
            return {'error': str(e)}

    # ==================== 4. 缠论分析 ====================
    def _analyze_chanlun(self, df: pd.DataFrame) -> dict:
        """缠论买卖点分析"""
        try:
            analyzer = ChanlunAnalyzer()
            result = analyzer.analyze(df)

            # 序列化买卖点
            buy_points = []
            for bp in result.get('buy_points', []):
                buy_points.append({
                    'type': bp.bp_type.value,
                    'description': bp.description,
                    'confidence': round(bp.confidence, 2),
                    'price': round(bp.price, 2) if bp.price else None
                })

            return {
                'fenxing_count': result.get('fenxing_count', 0),
                'bi_count': result.get('bi_count', 0),
                'zhongshu_count': result.get('zhongshu_count', 0),
                'current_trend': result.get('current_trend', ''),
                'nearest_zhongshu': result.get('nearest_zhongshu'),
                'buy_points': buy_points
            }
        except Exception as e:
            return {'error': str(e)}

    # ==================== 5. 信号共振评分 ====================
    def _analyze_signal_resonance(self, df: pd.DataFrame, patterns: dict,
                                  chanlun: dict, fina_indicator) -> dict:
        """信号共振评分"""
        try:
            scorer = SignalResonanceScorer()
            all_signals = []

            # 技术信号 + 成交量信号
            all_signals.extend(scorer.analyze_technical_signals(df))
            all_signals.extend(scorer.analyze_volume_signals(df))

            # K线形态信号
            if patterns and 'error' not in patterns:
                # 需要重新获取 pattern 对象来传给 scorer
                try:
                    recognizer = CandlestickPatternRecognizer()
                    pattern_results = recognizer.recognize_all(df, lookback=5)
                    pattern_dict = {
                        'top_bullish': [r for r in pattern_results if r.pattern_type.value == 'BULLISH'][:5],
                        'top_bearish': [r for r in pattern_results if r.pattern_type.value == 'BEARISH'][:5],
                    }
                    all_signals.extend(scorer.analyze_candlestick_signals(pattern_dict))
                except:
                    pass

            # 缠论信号
            if chanlun and 'error' not in chanlun:
                # 重新获取缠论结果
                try:
                    cl_analyzer = ChanlunAnalyzer()
                    cl_result = cl_analyzer.analyze(df)
                    all_signals.extend(scorer.analyze_chanlun_signals(cl_result))
                except:
                    pass

            # 基本面信号
            fundamental_data = {}
            if fina_indicator is not None:
                try:
                    if isinstance(fina_indicator, str):
                        fi_df = pd.read_json(fina_indicator, orient='records')
                    elif isinstance(fina_indicator, list):
                        fi_df = pd.DataFrame(fina_indicator)
                    else:
                        fi_df = fina_indicator

                    if len(fi_df) > 0:
                        fi_latest = fi_df.iloc[-1]
                        fundamental_data['pe'] = self._safe_float(fi_latest.get('pe', 0))
                        fundamental_data['pb'] = self._safe_float(fi_latest.get('pb', 0))
                        fundamental_data['roe'] = self._safe_float(fi_latest.get('roe', 0))
                        fundamental_data['revenue_growth'] = self._safe_float(
                            fi_latest.get('or_yoy', 0))  # 营收同比增长率
                except:
                    pass

            if fundamental_data:
                all_signals.extend(scorer.analyze_fundamental_signals(fundamental_data))

            # 计算共振
            resonance = scorer.calculate_resonance(all_signals)

            return {
                'total_score': resonance.total_score,
                'bullish_score': resonance.bullish_score,
                'bearish_score': resonance.bearish_score,
                'signal_count': resonance.signal_count,
                'resonance_level': resonance.resonance_level,
                'confidence': resonance.confidence,
                'summary': resonance.summary,
                'signal_details': [
                    {
                        'type': s.signal_type.value,
                        'direction': s.direction.value,
                        'strength': round(s.strength, 2),
                        'description': s.description
                    }
                    for s in all_signals
                ]
            }
        except Exception as e:
            return {'error': str(e)}

    # ==================== 6. 情绪指数 ====================
    def _analyze_sentiment(self, df: pd.DataFrame) -> dict:
        """市场情绪指数"""
        try:
            calculator = SentimentIndexCalculator()
            result = calculator.calculate(df)

            return {
                'index_value': result.index_value,
                'level': result.level.value,
                'description': result.description,
                'components': result.components,
                'trend': result.trend,
                'signal': result.signal
            }
        except Exception as e:
            return {'error': str(e)}

    # ==================== 7. 基本面分析 ====================
    def _analyze_fundamental(self, income, fina_indicator, daily_basic,
                             df: pd.DataFrame, code: str) -> dict:
        """基本面综合分析"""
        fundamental = {}

        # 7.1 财务数据
        fundamental['financial'] = self._analyze_financial(income, fina_indicator)

        # 7.2 估值分析
        fundamental['valuation'] = self._analyze_valuation(daily_basic, df)

        # 7.3 行业识别
        fundamental['industry'] = self._identify_industry(code)

        # 7.4 综合基本面评分
        fundamental.update(self._score_fundamental(fundamental))

        return fundamental

    def _analyze_financial(self, income, fina_indicator) -> dict:
        """财务数据分析"""
        fin = {'periods': [], 'latest': {}, 'trend': {}}

        # 从 fina_indicator 提取多期财务指标
        if fina_indicator is not None:
            try:
                if isinstance(fina_indicator, str):
                    fi_df = pd.read_json(fina_indicator, orient='records')
                elif isinstance(fina_indicator, list):
                    fi_df = pd.DataFrame(fina_indicator)
                else:
                    fi_df = fina_indicator

                if len(fi_df) > 0:
                    # 按报告期降序
                    if 'ann_date' in fi_df.columns:
                        fi_df = fi_df.sort_values('ann_date', ascending=False)
                    recent = fi_df.head(5)

                    for _, row in recent.iterrows():
                        period_data = {
                            'report_date': str(row.get('ann_date', ''))[:10],
                            'roe': self._safe_float(row.get('roe', 0)),
                            'roe_dt': self._safe_float(row.get('roe_dt', 0)),  # ROE 摊薄
                            'grossprofit_margin': self._safe_float(row.get('grossprofit_margin', 0)),
                            'netprofit_margin': self._safe_float(row.get('netprofit_margin', 0)),
                            'or_yoy': self._safe_float(row.get('or_yoy', 0)),  # 营收同比
                            'netprofit_yoy': self._safe_float(row.get('netprofit_yoy', 0)),  # 净利润同比
                            'dt_netprofit_yoy': self._safe_float(row.get('dt_netprofit_yoy', 0)),  # 扣非同比
                            'debt_to_assets': self._safe_float(row.get('debt_to_assets', 0)),  # 资产负债率
                            'current_ratio': self._safe_float(row.get('current_ratio', 0)),
                            'quick_ratio': self._safe_float(row.get('quick_ratio', 0)),
                            'eps': self._safe_float(row.get('eps', 0)),
                            'bps': self._safe_float(row.get('bps', 0)),
                            'ocf_ps': self._safe_float(row.get('ocf_ps', 0)),
                        }
                        fin['periods'].append(period_data)

                    if len(fin['periods']) > 0:
                        latest = fin['periods'][0]
                        fin['latest'] = {
                            'report_date': latest['report_date'],
                            'roe': latest['roe'],
                            'gross_margin': latest['grossprofit_margin'],
                            'net_margin': latest['netprofit_margin'],
                            'revenue_yoy': latest['or_yoy'],
                            'net_profit_yoy': latest['netprofit_yoy'],
                            'debt_ratio': latest['debt_to_assets'],
                            'eps': latest['eps'],
                            'ocf_ps': latest['ocf_ps'],
                        }

                        if len(fin['periods']) >= 3:
                            fin['trend'] = self._analyze_financial_trend(fin['periods'])
            except Exception as e:
                fin['error'] = str(e)

        # 补充 income 利润表数据
        if income is not None:
            try:
                if isinstance(income, str):
                    inc_df = pd.read_json(income, orient='records')
                elif isinstance(income, list):
                    inc_df = pd.DataFrame(income)
                else:
                    inc_df = income

                if len(inc_df) > 0:
                    inc_latest = inc_df.iloc[-1]
                    fin['income'] = {
                        'total_revenue': self._safe_float(inc_latest.get('total_revenue', 0)),
                        'n_income': self._safe_float(inc_latest.get('n_income', 0)),
                        'n_income_attr_p': self._safe_float(inc_latest.get('n_income_attr_p', 0)),
                    }
            except:
                pass

        return fin

    def _analyze_financial_trend(self, periods: list) -> dict:
        """财务趋势分析"""
        trend = {}

        rev_yoys = [p['or_yoy'] for p in periods if p.get('or_yoy') != 0]
        profit_yoys = [p['netprofit_yoy'] for p in periods if p.get('netprofit_yoy') != 0]
        roes = [p['roe'] for p in periods if p.get('roe') != 0]
        gms = [p['grossprofit_margin'] for p in periods if p.get('grossprofit_margin') != 0]

        if len(rev_yoys) >= 2:
            if all(r > 0 for r in rev_yoys):
                trend['revenue_trend'] = '持续增长'
            elif all(r < 0 for r in rev_yoys):
                trend['revenue_trend'] = '持续下滑'
            elif rev_yoys[0] > rev_yoys[-1]:
                trend['revenue_trend'] = '增速放缓'
            else:
                trend['revenue_trend'] = '增速回升'

        if len(profit_yoys) >= 2:
            if all(p > 0 for p in profit_yoys):
                trend['profit_trend'] = '持续增长'
            elif all(p < 0 for p in profit_yoys):
                trend['profit_trend'] = '持续下滑'
            elif profit_yoys[0] > profit_yoys[-1]:
                trend['profit_trend'] = '增速放缓'
            else:
                trend['profit_trend'] = '增速回升'

        if len(roes) >= 2:
            trend['roe_trend'] = '下降' if roes[0] > roes[-1] else '上升'

        if len(gms) >= 2:
            trend['gross_margin_trend'] = '下滑（成本压力）' if gms[0] > gms[-1] else '改善'

        return trend

    def _analyze_valuation(self, daily_basic, df: pd.DataFrame) -> dict:
        """估值分析"""
        valuation = {}

        # 从 daily_basic 获取 PE/PB
        if daily_basic is not None:
            try:
                if isinstance(daily_basic, str):
                    db_df = pd.read_json(daily_basic, orient='records')
                elif isinstance(daily_basic, list):
                    db_df = pd.DataFrame(daily_basic)
                else:
                    db_df = daily_basic

                if len(db_df) > 0:
                    db_latest = db_df.iloc[-1]
                    pe_ttm = self._safe_float(db_latest.get('pe_ttm', 0))
                    pb = self._safe_float(db_latest.get('pb', 0))

                    if pe_ttm > 0:
                        valuation['PE_TTM'] = round(pe_ttm, 2)
                        if pe_ttm < 15:
                            valuation['PE评价'] = '低估'
                        elif pe_ttm < 30:
                            valuation['PE评价'] = '合理'
                        elif pe_ttm < 50:
                            valuation['PE评价'] = '偏高'
                        else:
                            valuation['PE评价'] = '高估'

                    if pb > 0:
                        valuation['PB'] = round(pb, 2)
                        if pb < 1:
                            valuation['PB评价'] = '破净'
                        elif pb < 3:
                            valuation['PB评价'] = '合理'
                        elif pb < 5:
                            valuation['PB评价'] = '偏高'
                        else:
                            valuation['PB评价'] = '高估'
            except:
                pass

        # 从日线计算历史分位数、支撑压力位
        if df is not None and len(df) >= 60:
            close = df['close']
            current = close.iloc[-1]

            # 年度涨跌幅
            if len(df) >= 250:
                year_start = close.iloc[-250]
                valuation['近一年涨跌幅'] = round((current - year_start) / year_start * 100, 2)

            # 波动率
            if len(df) >= 30:
                returns = close.pct_change().dropna().tail(30)
                valuation['30日年化波动率'] = round(float(returns.std() * np.sqrt(250) * 100), 2)

            # 历史分位数
            percentile = round(float((close < current).sum() / len(close) * 100), 1)
            valuation['价格历史分位数'] = f'{percentile}%'

            # 支撑/压力位
            recent_60 = close.tail(60)
            support = round(float(recent_60.min()), 2)
            resistance = round(float(recent_60.max()), 2)
            valuation['60日支撑位'] = support
            valuation['60日压力位'] = resistance
            valuation['距支撑位幅度'] = f'{round((current - support) / support * 100, 2)}%'
            valuation['距压力位幅度'] = f'{round((resistance - current) / current * 100, 2)}%'

        return valuation

    def _identify_industry(self, code: str) -> dict:
        """行业识别（基于代码映射）"""
        # 简化版：只做代码映射，不再从新闻中提取
        stock_industry = {
            '002402': '消费电子', '600519': '食品饮料', '000001': '金融',
            '300750': '新能源', '002594': '汽车', '002415': 'TMT',
            '002230': 'TMT', '688981': '半导体', '300059': '金融',
            '601899': '新材料', '002149': '新材料', '002475': '消费电子',
            '600036': '金融', '601318': '金融', '300263': '新材料',
        }

        industry = {'identified_industry': [], 'industry_outlook': ''}

        if code in stock_industry:
            mapped = stock_industry[code]
            industry['identified_industry'].append({
                'name': mapped,
                'source': '预设映射'
            })
            industry['industry_outlook'] = self._get_industry_outlook(mapped)

        return industry

    def _get_industry_outlook(self, industry_name: str) -> str:
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

    def _score_fundamental(self, fundamental: dict) -> dict:
        """综合基本面评分"""
        score = 50
        reasons = []

        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        trend = fin.get('trend', {})

        # ROE
        roe = self._safe_float(latest.get('roe', 0))
        if roe > 20:
            score += 15; reasons.append(f'ROE优秀({roe}%)')
        elif roe > 15:
            score += 10; reasons.append(f'ROE良好({roe}%)')
        elif roe > 10:
            score += 5; reasons.append(f'ROE一般({roe}%)')
        elif roe > 0:
            score -= 5; reasons.append(f'ROE偏低({roe}%)')
        else:
            score -= 15; reasons.append(f'ROE为负({roe}%)')

        # 净利润增速
        profit_yoy = self._safe_float(latest.get('net_profit_yoy', 0))
        if profit_yoy > 30:
            score += 10; reasons.append(f'净利润高增长({profit_yoy}%)')
        elif profit_yoy > 10:
            score += 5; reasons.append(f'净利润稳健增长({profit_yoy}%)')
        elif profit_yoy > 0:
            pass
        elif profit_yoy > -10:
            score -= 5; reasons.append(f'净利润小幅下滑({profit_yoy}%)')
        else:
            score -= 10; reasons.append(f'净利润大幅下滑({profit_yoy}%)')

        # 毛利率
        gm = self._safe_float(latest.get('gross_margin', 0))
        if gm > 50:
            score += 10; reasons.append(f'高毛利率({gm}%)')
        elif gm > 30:
            score += 5; reasons.append(f'毛利率良好({gm}%)')
        elif gm > 15:
            pass
        else:
            score -= 5; reasons.append(f'毛利率偏低({gm}%)')

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

        # 估值评分
        val = fundamental.get('valuation', {})
        pe_eval = val.get('PE评价', '')
        if '低估' in pe_eval:
            score += 10; reasons.append('估值低估')
        elif '合理' in pe_eval:
            score += 5
        elif '偏高' in pe_eval:
            score -= 5; reasons.append('估值偏高')
        elif '高估' in pe_eval:
            score -= 10; reasons.append('估值高估')

        return {'fundamental_score': max(0, min(100, score)), 'fundamental_reasons': reasons}

    # ==================== 8. 资金流向 ====================
    def _analyze_money_flow(self, moneyflow) -> dict:
        """资金流向分析"""
        result = {'score': 50}

        if moneyflow is None:
            return result

        try:
            if isinstance(moneyflow, str):
                mf_df = pd.read_json(moneyflow, orient='records')
            elif isinstance(moneyflow, list):
                mf_df = pd.DataFrame(moneyflow)
            else:
                mf_df = moneyflow

            if len(mf_df) > 0:
                mf_df = mf_df.sort_values('trade_date', ascending=False)
                latest = mf_df.iloc[0]

                buy_elg = self._safe_float(latest.get('buy_elg', 0))  # 主动买入(万元)
                sell_elg = self._safe_float(latest.get('sell_elg', 0))  # 主动卖出(万元)
                net_mf_vol = self._safe_float(latest.get('net_mf_vol', 0))  # 净流入量(手)
                net_mf_amount = self._safe_float(latest.get('net_mf_amount', 0))  # 净流入额(万元)

                result['latest'] = {
                    'date': str(latest.get('trade_date', '')),
                    'net_mf_amount': round(net_mf_amount, 2),  # 万元
                    'net_mf_vol': round(net_mf_vol, 2),  # 手
                    'buy_elg': round(buy_elg, 2),
                    'sell_elg': round(sell_elg, 2),
                }

                # 近5日资金净流入趋势
                if len(mf_df) >= 5:
                    recent_5 = mf_df.head(5)
                    total_net = recent_5['net_mf_amount'].sum() if 'net_mf_amount' in recent_5.columns else 0
                    result['recent_5d_net'] = round(self._safe_float(total_net), 2)
                    positive_days = (recent_5['net_mf_amount'] > 0).sum() if 'net_mf_amount' in recent_5.columns else 0
                    result['recent_5d_positive_days'] = int(positive_days)

                # 评分
                if net_mf_amount > 0:
                    result['score'] = min(80, 50 + min(30, abs(net_mf_amount) / 1000))
                else:
                    result['score'] = max(20, 50 - min(30, abs(net_mf_amount) / 1000))
        except Exception as e:
            result['error'] = str(e)

        return result

    # ==================== 9. 消息面 ====================
    def _analyze_news(self, news, code: str) -> dict:
        """消息面分析"""
        result = {'items': [], 'sentiment': '中性', 'sentiment_score': 0}

        if news is None:
            return result

        try:
            if isinstance(news, str):
                news_df = pd.read_json(news, orient='records')
            elif isinstance(news, list):
                news_df = pd.DataFrame(news)
            else:
                news_df = news

            if len(news_df) > 0:
                for _, row in news_df.head(10).iterrows():
                    result['items'].append({
                        'title': str(row.get('title', '')),
                        'content': str(row.get('content', ''))[:300],
                        'date': str(row.get('datetime', row.get('pub_date', '')))[:10],
                        'channels': str(row.get('channels', '')),
                    })

                # 情感分析
                all_text = ' '.join([n.get('title', '') + ' ' + n.get('content', '') for n in result['items']])
                positive_kw = ['增长', '盈利', '突破', '创新', '扩张', '合作', '增持', '买入', '看好',
                              '上调', '超预期', '订单', '量产', '中标', '获批', '首发', '分红']
                negative_kw = ['下跌', '亏损', '风险', '减持', '卖出', '下调', '不及预期', '警告', '调查',
                              '诉讼', '处罚', '退市', '质押', '债务', '违约', '爆雷', '破产']

                sentiment_score = 0
                for kw in positive_kw:
                    sentiment_score += all_text.count(kw) * 2
                for kw in negative_kw:
                    sentiment_score -= all_text.count(kw) * 2

                result['sentiment'] = '偏多' if sentiment_score > 5 else ('偏空' if sentiment_score < -5 else '中性')
                result['sentiment_score'] = sentiment_score
        except Exception as e:
            result['error'] = str(e)

        return result

    # ==================== 10. 盈利预测 ====================
    def _analyze_forecast(self, forecast) -> dict:
        """盈利预测"""
        result = {}

        if forecast is None:
            return result

        try:
            if isinstance(forecast, str):
                fc_df = pd.read_json(forecast, orient='records')
            elif isinstance(forecast, list):
                fc_df = pd.DataFrame(forecast)
            else:
                fc_df = forecast

            if len(fc_df) > 0:
                result['forecasts'] = []
                for _, row in fc_df.head(3).iterrows():
                    result['forecasts'].append({
                        'year': str(row.get('end_date', ''))[:4],
                        'analyst_count': int(self._safe_float(row.get('count', 0))),
                        'avg_net_profit': self._safe_float(row.get('avg_net_profit', 0)),  # 万元
                        'min_net_profit': self._safe_float(row.get('min_net_profit', 0)),
                        'max_net_profit': self._safe_float(row.get('max_net_profit', 0)),
                    })

                if len(result['forecasts']) >= 2:
                    cur = result['forecasts'][0].get('avg_net_profit', 0)
                    nxt = result['forecasts'][1].get('avg_net_profit', 0)
                    if cur > 0:
                        growth = round((nxt - cur) / cur * 100, 2)
                        result['expected_growth'] = f'{growth}%'
                        result['growth_direction'] = '上升' if growth > 0 else '下降'

                if result['forecasts']:
                    ac = result['forecasts'][0].get('analyst_count', 0)
                    result['analyst_coverage'] = ac
                    result['coverage_level'] = '高关注度' if ac >= 10 else ('中等关注' if ac >= 5 else '低关注度')
        except Exception as e:
            result['error'] = str(e)

        return result

    # ==================== 11. 综合建议 ====================
    def _generate_suggestion(self, result: dict) -> dict:
        """综合投资建议"""
        total_score = 50

        # 技术面 (35%)
        tech = result.get('technical', {})
        if 'scores' in tech:
            scores = tech['scores']
            tech_score = scores.get('trend', 0) + scores.get('kdj', 0) + scores.get('rsi', 0) + scores.get('macd', 0)
            total_score += tech_score * 0.35

        # 基本面 (35%)
        fund = result.get('fundamental', {})
        fund_score = fund.get('fundamental_score', 50)
        total_score += (fund_score - 50) * 0.35

        # 资金面 (15%)
        money = result.get('money_flow', {})
        total_score += (money.get('score', 50) - 50) * 0.15

        # 消息面 (15%)
        news = result.get('news', {})
        sentiment = news.get('sentiment', '中性')
        if sentiment == '偏多':
            total_score += 7.5
        elif sentiment == '偏空':
            total_score -= 7.5

        # 信号共振调整
        resonance = result.get('signal_resonance', {})
        res_score = resonance.get('total_score', 0)
        total_score += res_score * 0.1  # 10%权重

        # 情绪指数调整
        sentiment_data = result.get('sentiment', {})
        sent_idx = sentiment_data.get('index_value', 50)
        # 极端恐慌加一点分，极端贪婪减一点
        if sent_idx < 20:
            total_score += 5
        elif sent_idx > 80:
            total_score -= 5

        total_score = max(0, min(100, round(total_score)))

        # 操作建议
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
        support = result.get('fundamental', {}).get('valuation', {}).get('60日支撑位', price * 0.95)
        resistance = result.get('fundamental', {}).get('valuation', {}).get('60日压力位', price * 1.1)

        return {
            'total_score': total_score,
            'action': action,
            'level': level,
            'target_price': round(float(resistance), 2) if resistance else 0,
            'stop_loss': round(float(support), 2) if support else 0,
            'position': f'{min(30, max(5, total_score // 3))}%',
            'resonance_summary': resonance.get('summary', ''),
            'sentiment_summary': f"情绪{sentiment_data.get('level', '')}，建议{sentiment_data.get('signal', '')}",
            'score_breakdown': {
                'tech_weight': '35%',
                'fundamental_weight': '35%',
                'money_flow_weight': '15%',
                'news_sentiment_weight': '15%'
            }
        }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': '用法: python full_analysis.py <data_json_path> [code]'}, ensure_ascii=False, indent=2))
        return

    data_path = sys.argv[1]
    code = sys.argv[2] if len(sys.argv) >= 3 else None

    # 读取预取数据
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({'error': f'读取数据文件失败: {e}'}, ensure_ascii=False, indent=2))
        return

    # 从数据中提取 code
    if code is None:
        code = data.get('code', data.get('ts_code', ''))
        if '.' in code:
            code = code.split('.')[0]

    analyzer = StockAnalyzer()
    result = analyzer.analyze(data, code)

    # 自定义 JSON 序列化
    def json_serializer(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj) if isinstance(obj, float) else False:
            return None
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    print(json.dumps(result, ensure_ascii=False, indent=2, default=json_serializer))


if __name__ == '__main__':
    main()
