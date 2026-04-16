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
    
    def __init__(self):
        self.source_status = {
            DataSource.AKSHARE: True,
            DataSource.YFINANCE: True,
            DataSource.BAOSTOCK: True,
            DataSource.TUSHARE: True,
        }
        self.last_error = {}
    
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
            # A股策略: AkShare -> Baostock
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
            # A股实时行情
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
            # A股基本面
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
