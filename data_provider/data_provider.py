# -*- coding: utf-8 -*-
"""
数据提供者 - 多数据源降级机制
借鉴 daily_stock_analysis 的多源策略

优先级：
1. A股: AkShare(主) -> Baostock(备) -> Tushare(备)
2. 港股/美股: YFinance(主) -> AkShare(备)
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class DataSource(Enum):
    """数据源枚举"""
    AKSHARE = "akshare"
    YFINANCE = "yfinance"
    BAOSTOCK = "baostock"
    TUSHARE = "tushare"


class DataProvider:
    """统一数据提供者 - 支持多源降级"""
    
    # Tushare 配置 - 从环境变量获取 Token，避免硬编码
    @staticmethod
    def _get_tushare_token() -> str:
        """安全获取 Tushare Token（优先环境变量）"""
        import os
        # 优先从环境变量读取
        token = os.environ.get('TUSHARE_TOKEN', '')
        if token:
            return token
        # 开发环境备用（生产环境应始终使用环境变量）
        return os.environ.get('TUSHARE_TOKEN_FALLBACK', '')
    
    TUSHARE_ID = '1093699'
    
    def __init__(self):
        self.source_status = {
            DataSource.AKSHARE: True,
            DataSource.YFINANCE: True,
            DataSource.BAOSTOCK: True,
            DataSource.TUSHARE: True,
        }
        self.last_error = {}
        self._pro_api = None  # Tushare Pro API 实例（懒加载）
    
    @property
    def pro(self):
        """懒加载 Tushare Pro API"""
        if self._pro_api is None:
            try:
                import tushare as ts
                token = self._get_tushare_token()
                if not token:
                    raise ValueError("TUSHARE_TOKEN 环境变量未设置")
                ts.set_token(token)
                self._pro_api = ts.pro_api()
            except Exception as e:
                self.last_error['tushare_init'] = str(e)
                self.source_status[DataSource.TUSHARE] = False
        return self._pro_api
    
    def get_daily_data(self, code: str, days: int = 120) -> Optional[pd.DataFrame]:
        """
        获取日线数据（带降级机制）
        
        Args:
            code: 股票代码
            days: 历史天数
            
        Returns:
            DataFrame or None
        """
        market, symbol = self._normalize_code(code)
        
        # 根据市场选择数据源策略
        if market in ['sh', 'sz']:
            # A股策略: Tushare(主) -> AkShare -> Baostock
            df = self._try_tushare_daily(market, symbol, days)
            if df is not None and not df.empty:
                return df
                
            df = self._try_akshare_daily(market, symbol, days)
            if df is not None and not df.empty:
                return df
                
            df = self._try_baostock_daily(symbol, days)
            if df is not None and not df.empty:
                return df
                
        elif market == 'hk':
            # 港股策略: YFinance -> AkShare
            df = self._try_yfinance_daily(symbol, days, market='hk')
            if df is not None and not df.empty:
                return df
                
            df = self._try_akshare_hk_daily(symbol, days)
            if df is not None and not df.empty:
                return df
                
        elif market == 'us':
            # 美股策略: YFinance -> AkShare
            df = self._try_yfinance_daily(symbol, days, market='us')
            if df is not None and not df.empty:
                return df
                
            df = self._try_akshare_us_daily(symbol, days)
            if df is not None and not df.empty:
                return df
        
        return None
    
    def get_realtime_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """获取实时行情（带降级机制）"""
        market, symbol = self._normalize_code(code)
        
        if market in ['sh', 'sz']:
            # A股实时行情 - 优先 Tushare
            quote = self._try_tushare_realtime(market, symbol)
            if quote:
                return quote
            # 备用 AkShare
            quote = self._try_akshare_realtime(market, symbol)
            if quote:
                return quote
        
        elif market == 'hk':
            # 港股实时行情
            quote = self._try_yfinance_realtime(symbol, market='hk')
            if quote:
                return quote
                
        elif market == 'us':
            # 美股实时行情
            quote = self._try_yfinance_realtime(symbol, market='us')
            if quote:
                return quote
        
        return None
    
    def get_fundamental_data(self, code: str) -> Dict[str, Any]:
        """获取基本面数据（多源聚合）"""
        market, symbol = self._normalize_code(code)
        fundamental = {}
        
        if market in ['sh', 'sz']:
            # 优先使用 Tushare 获取全面的基本面数据
            tushare_data = self._get_tushare_fundamental(code)
            if tushare_data:
                fundamental.update(tushare_data)
            
            # 补充 AkShare 数据
            try:
                import akshare as ak
                
                # 财务摘要
                try:
                    df = ak.stock_financial_abstract_ths(symbol=symbol)
                    if df is not None and not df.empty:
                        fundamental['financial'] = df
                except Exception as e:
                    self.last_error['financial'] = str(e)
                
                # 盈利预测
                try:
                    df = ak.stock_profit_forecast_ths(symbol=symbol, indicator='预测年报净利润')
                    if df is not None and not df.empty:
                        fundamental['forecast'] = df
                except Exception as e:
                    self.last_error['forecast'] = str(e)
                
                # 资产负债表
                try:
                    df = ak.stock_financial_report_sina(stock=symbol, symbol='资产负债表')
                    if df is not None and not df.empty:
                        fundamental['balance_sheet'] = df
                except Exception as e:
                    self.last_error['balance_sheet'] = str(e)
                    
            except Exception as e:
                self.last_error['fundamental'] = str(e)
        
        return fundamental
    
    def get_money_flow(self, code: str) -> Optional[Dict[str, Any]]:
        """获取资金流向"""
        market, symbol = self._normalize_code(code)
        
        if market in ['sh', 'sz']:
            # 优先 Tushare
            tushare_flow = self._get_tushare_money_flow(code)
            if tushare_flow:
                return tushare_flow
            
            # 备用 AkShare
            try:
                import akshare as ak
                df = ak.stock_individual_fund_flow(
                    stock=symbol, 
                    market='sh' if symbol.startswith('6') else 'sz'
                )
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    return {
                        'date': str(latest.get('日期', ''))[:10],
                        'main_net': float(latest.get('主力净流入', 0)) / 100000000,
                        'main_pct': float(latest.get('主力净流入占比(%)', 0)),
                        'retail_net': float(latest.get('散户净流入', 0)) / 100000000,
                    }
            except Exception as e:
                self.last_error['money_flow'] = str(e)
        
        return None
    
    def get_news(self, code: str, limit: int = 15) -> list:
        """获取新闻"""
        market, symbol = self._normalize_code(code)
        
        if market in ['sh', 'sz']:
            # 优先 Tushare
            tushare_news = self._get_tushare_news(code, limit)
            if tushare_news:
                return tushare_news
            
            # 备用 AkShare
            try:
                import akshare as ak
                df = ak.stock_news_em(symbol=symbol)
                if df is not None and not df.empty:
                    news_list = []
                    for _, row in df.head(limit).iterrows():
                        news_list.append({
                            'title': str(row.get('新闻标题', '')),
                            'content': str(row.get('新闻内容', ''))[:500],
                            'date': str(row.get('发布日期', ''))
                        })
                    return news_list
            except Exception as e:
                self.last_error['news'] = str(e)
        
        return []
    
    # ==================== Tushare 数据源实现 ====================
    
    def _try_tushare_daily(self, market: str, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """尝试使用 Tushare Pro 获取日线数据"""
        if not self.source_status[DataSource.TUSHARE] or self.pro is None:
            return None
            
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            # 构建 Tushare 代码格式
            ts_code = f"{symbol}.SH" if market == 'sh' else f"{symbol}.SZ"
            
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='trade_date,open,high,low,close,vol,amount,pct_chg'
            )
            
            if df is not None and not df.empty:
                # 重命名列以标准化
                df = df.rename(columns={
                    'trade_date': 'date',
                    'vol': 'volume',
                    'pct_chg': 'pct_change'
                })
                # 按日期排序
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                return df
                
        except Exception as e:
            self.last_error['tushare_daily'] = str(e)
            self.source_status[DataSource.TUSHARE] = False
        
        return None
    
    def _try_tushare_realtime(self, market: str, symbol: str) -> Optional[Dict]:
        """尝试使用 Tushare 获取实时行情"""
        if not self.source_status[DataSource.TUSHARE] or self.pro is None:
            return None
            
        try:
            ts_code = f"{symbol}.SH" if market == 'sh' else f"{symbol}.SZ"
            
            # 使用实时行情接口
            df = self.pro.rt_k()
            if df is not None and not df.empty:
                row = df[df['ts_code'] == ts_code]
                if len(row) > 0:
                    latest = row.iloc[0]
                    return {
                        'price': float(latest.get('price', 0)),
                        'change': float(latest.get('change', 0)),
                        'pct_change': float(latest.get('pct_change', 0)),
                        'open': float(latest.get('open', 0)),
                        'high': float(latest.get('high', 0)),
                        'low': float(latest.get('low', 0)),
                        'volume': int(latest.get('volume', 0)),
                        'amount': float(latest.get('amount', 0)),
                        'date': str(latest.get('date', ''))
                    }
                    
        except Exception as e:
            self.last_error['tushare_realtime'] = str(e)
        
        return None
    
    def _get_tushare_fundamental(self, code: str) -> Dict[str, Any]:
        """使用 Tushare 获取基本面数据（更全面）"""
        if self.pro is None:
            return {}
        
        fundamental = {}
        market, symbol = self._normalize_code(code)
        ts_code = f"{symbol}.SH" if market == 'sh' else f"{symbol}.SZ"
        
        try:
            # 利润表（最近4期）
            df = self.pro.income(
                ts_code=ts_code, 
                fields='end_date,revenue,n_income,n_income_attr_p,ebit,basic_eps'
            )
            if df is not None and not df.empty:
                fundamental['income'] = df.head(8).to_dict('records')
                
            # 资产负债表（关键指标）
            df = self.pro.balancesheet(
                ts_code=ts_code,
                fields='end_date,total_assets,total_liab,total_equity,cash_eq,money_cap,notes_payable,accounts_rec'
            )
            if df is not None and not df.empty:
                fundamental['balance_sheet'] = df.head(8).to_dict('records')
                
            # 现金流量表
            df = self.pro.cashflow(
                ts_code=ts_code,
                fields='end_date,n_cashflow_act,n_cashflow_inv,n_cashflow_fin,cashpaid_invest'
            )
            if df is not None and not df.empty:
                fundamental['cashflow'] = df.head(8).to_dict('records')
                
            # 财务指标
            df = self.pro.fina_indicator(
                ts_code=ts_code,
                fields='end_date,grossprofit_margin,netprofit_margin,roe,debt_to_assets,current_ratio,eps,yoy_net_profit'
            )
            if df is not None and not df.empty:
                fundamental['indicators'] = df.head(8).to_dict('records')
                
            # 每日基本面指标（PE/PB等）
            df = self.pro.daily_basic(
                ts_code=ts_code,
                trade_date=datetime.now().strftime('%Y%m%d'),
                fields='pe_ttm,pb,ps_ttm,dv_ratio,total_mv,circ_mv,turnover_rate'
            )
            if df is not None and not df.empty:
                fundamental['daily_basic'] = df.iloc[0].to_dict()
                
            # 盈利预测（如果有权限）
            try:
                df = self.pro.report_rc(
                    ts_code=ts_code,
                    fields='eps_pred_yy,net_profit_min,net_profit_max,year'
                )
                if df is not None and not df.empty:
                    fundamental['forecast'] = df.to_dict('records')
            except:
                pass
                
        except Exception as e:
            self.last_error['tushare_fundamental'] = str(e)
        
        return fundamental
    
    def _get_tushare_money_flow(self, code: str) -> Optional[Dict[str, Any]]:
        """使用 Tushare 获取资金流向"""
        if self.pro is None:
            return None
        
        market, symbol = self._normalize_code(code)
        ts_code = f"{symbol}.SH" if market == 'sh' else f"{symbol}.SZ"
        
        try:
            # 个股资金流向（最近5天）
            trade_date = datetime.now().strftime('%Y%m%d')
            df = self.pro.moneyflow(
                ts_code=ts_code,
                start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
                end_date=trade_date
            )
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                return {
                    'date': str(latest.get('trade_date', '')),
                    'buy_elg_vol': float(latest.get('buy_elg_vol', 0)),
                    'buy_lg_vol': float(latest.get('buy_lg_vol', 0)),
                    'sell_elg_vol': float(latest.get('sell_elg_vol', 0)),
                    'sell_lg_vol': float(latest.get('sell_lg_vol', 0)),
                    'net_mf_vol': float(latest.get('net_mf_vol', 0)),  # 主力净流入
                    'mf_vol': float(latest.get('mf_vol', 0)),          # 主力成交量
                }
        except Exception as e:
            self.last_error['tushare_money_flow'] = str(e)
        
        return None
    
    def _get_tushare_news(self, code: str, limit: int = 15) -> list:
        """使用 Tushare 获取新闻"""
        if self.pro is None:
            return []
        
        news_list = []
        market, symbol = self._normalize_code(code)
        ts_code = f"{symbol}.SH" if market == 'sh' else f"{symbol}.SZ"
        
        try:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            df = self.pro.news(
                src='sina',
                start_date=start_date,
                end_date=end_date
            )
            if df is not None and not df.empty:
                for _, row in df.head(limit * 3).iterrows():
                    title = str(row.get('title', ''))
                    content = str(row.get('content', ''))
                    # 筛选包含股票代码或名称的新闻
                    if symbol in title or symbol in content:
                        news_list.append({
                            'title': title[:100],
                            'content': content[:500],
                            'date': str(row.get('datetime', row.get('time', '')))[:19]
                        })
                        if len(news_list) >= limit:
                            break
                            
        except Exception as e:
            self.last_error['tushare_news'] = str(e)
        
        return news_list

    # ==================== 私有方法：具体数据源实现 ====================
    
    def _normalize_code(self, code: str) -> Tuple[str, str]:
        """标准化股票代码"""
        code = code.strip().upper()
        
        if code.endswith('.SH') or code.startswith('6'):
            return 'sh', code.replace('.SH', '')
        elif code.endswith('.SZ') or code.startswith(('0', '3')):
            return 'sz', code.replace('.SZ', '')
        elif code.endswith('.HK'):
            return 'hk', code.replace('.HK', '').zfill(5)
        elif code.isalpha() or code.endswith('.US'):
            return 'us', code.replace('.US', '')
        else:
            # 默认A股
            return ('sh', code) if code.startswith('6') else ('sz', code)
    
    def _try_akshare_daily(self, market: str, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """尝试使用 AkShare 获取日线数据"""
        if not self.source_status[DataSource.AKSHARE]:
            return None
            
        try:
            import akshare as ak
            
            # 方法1: stock_zh_a_daily
            try:
                df = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
                if df is not None and not df.empty:
                    return self._standardize_columns(df, source='akshare')
            except Exception as e:
                pass
            
            # 方法2: stock_zh_a_hist
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
                df = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                       start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    return self._standardize_columns(df, source='akshare_hist')
            except Exception as e:
                pass
                
        except Exception as e:
            self.last_error['akshare_daily'] = str(e)
            self.source_status[DataSource.AKSHARE] = False
        
        return None
    
    def _try_baostock_daily(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """尝试使用 Baostock 获取日线数据"""
        if not self.source_status[DataSource.BAOSTOCK]:
            return None
            
        try:
            import baostock as bs
            
            # 登录
            lg = bs.login()
            if lg.error_code != '0':
                return None
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
            
            rs = bs.query_history_k_data_plus(
                f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}",
                "date,code,open,high,low,close,volume,amount,turn",
                start_date=start_date, end_date=end_date,
                frequency="d", adjustflag="3"
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            bs.logout()
            
            if data_list:
                df = pd.DataFrame(data_list, columns=rs.fields)
                return self._standardize_columns(df, source='baostock')
                
        except Exception as e:
            self.last_error['baostock'] = str(e)
            self.source_status[DataSource.BAOSTOCK] = False
        
        return None
    
    def _try_yfinance_daily(self, symbol: str, days: int, market: str = 'us') -> Optional[pd.DataFrame]:
        """尝试使用 YFinance 获取日线数据"""
        if not self.source_status[DataSource.YFINANCE]:
            return None
            
        try:
            import yfinance as yf
            
            # 转换代码格式
            if market == 'hk':
                yf_symbol = f"{symbol}.HK"
            else:
                yf_symbol = symbol
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=f"{days}d")
            
            if df is not None and not df.empty:
                return self._standardize_columns(df, source='yfinance')
                
        except Exception as e:
            self.last_error['yfinance_daily'] = str(e)
            self.source_status[DataSource.YFINANCE] = False
        
        return None
    
    def _try_akshare_hk_daily(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """尝试使用 AkShare 获取港股数据"""
        try:
            import akshare as ak
            
            # 港股日线
            df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
            if df is not None and not df.empty:
                return self._standardize_columns(df, source='akshare_hk')
                
        except Exception as e:
            self.last_error['akshare_hk'] = str(e)
        
        return None
    
    def _try_akshare_us_daily(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """尝试使用 AkShare 获取美股数据"""
        try:
            import akshare as ak
            
            # 美股日线
            df = ak.stock_us_daily(symbol=symbol, adjust="")
            if df is not None and not df.empty:
                return self._standardize_columns(df, source='akshare_us')
                
        except Exception as e:
            self.last_error['akshare_us'] = str(e)
        
        return None
    
    def _try_akshare_realtime(self, market: str, symbol: str) -> Optional[Dict]:
        """尝试使用 AkShare 获取实时行情"""
        try:
            import akshare as ak
            
            df = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                # 获取列名
                close_col = self._get_column_name(df, ['close', '收盘', 'Close'])
                open_col = self._get_column_name(df, ['open', '开盘', 'Open'])
                high_col = self._get_column_name(df, ['high', '最高', 'High'])
                low_col = self._get_column_name(df, ['low', '最低', 'Low'])
                vol_col = self._get_column_name(df, ['volume', '成交量', 'Volume'])
                
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
                    'date': str(latest.name)[:10] if hasattr(latest.name, 'year') else 'N/A'
                }
        except Exception as e:
            self.last_error['akshare_realtime'] = str(e)
        
        return None
    
    def _try_yfinance_realtime(self, symbol: str, market: str = 'us') -> Optional[Dict]:
        """尝试使用 YFinance 获取实时行情"""
        try:
            import yfinance as yf
            
            if market == 'hk':
                yf_symbol = f"{symbol}.HK"
            else:
                yf_symbol = symbol
            
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if info:
                return {
                    'price': info.get('currentPrice', 0),
                    'change': info.get('regularMarketChange', 0),
                    'pct_change': info.get('regularMarketChangePercent', 0),
                    'open': info.get('regularMarketOpen', 0),
                    'high': info.get('regularMarketDayHigh', 0),
                    'low': info.get('regularMarketDayLow', 0),
                    'volume': info.get('regularMarketVolume', 0),
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
        except Exception as e:
            self.last_error['yfinance_realtime'] = str(e)
        
        return None
    
    def _standardize_columns(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """标准化列名"""
        df = df.copy()
        
        # 列名映射
        column_mapping = {
            # AkShare
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover',
            # Baostock
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
            'turn': 'turnover',
            # YFinance
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        }
        
        # 重命名列
        for old, new in column_mapping.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)
        
        return df
    
    def _get_column_name(self, df: pd.DataFrame, candidates: list) -> str:
        """获取存在的列名"""
        for name in candidates:
            if name in df.columns:
                return name
        return df.columns[0] if len(df.columns) > 0 else None
    
    def get_source_status(self) -> Dict[str, bool]:
        """获取数据源状态"""
        return {k.value: v for k, v in self.source_status.items()}
    
    def reset_source_status(self):
        """重置数据源状态"""
        for key in self.source_status:
            self.source_status[key] = True
        self.last_error.clear()
