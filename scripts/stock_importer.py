# -*- coding: utf-8 -*-
"""
股票导入器 - 批量导入功能
支持：CSV文件、Excel文件、剪贴板粘贴、图片识别

借鉴 daily_stock_analysis 的多源导入设计
"""
import pandas as pd
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import io
import base64


class StockImporter:
    """股票批量导入器"""
    
    # A股代码正则
    A_SHARE_PATTERN = re.compile(r'^(\d{6})(\.SH|\.SZ|\.SS)?$', re.IGNORECASE)
    # 港股代码正则
    HK_PATTERN = re.compile(r'^(\d{4,5})(\.HK)?$', re.IGNORECASE)
    # 美股代码正则
    US_PATTERN = re.compile(r'^([A-Z]{1,5})(\.US)?$', re.IGNORECASE)
    
    # 常见股票名称映射（用于模糊匹配）
    STOCK_NAME_MAP = {
        '平安银行': '000001', '万科': '000002', '国农科技': '000004',
        '贵州茅台': '600519', '招商银行': '600036', '五粮液': '000858',
        '伊利股份': '600887', '美的集团': '000333', '立讯精密': '002475',
        '中国平安': '601318', '兴业银行': '601166', '恒瑞医药': '600276',
        '宁德时代': '300750', '中芯国际': '688981', '东方财富': '300059',
        '比亚迪': '002594', '海康威视': '002415', '隆基绿能': '601012',
        '长江电力': '600900', '紫金矿业': '601899', '山西汾酒': '600809',
        '泸州老窖': '000568', '牧原股份': '002714', '科大讯飞': '002230',
        '北方华创': '002371', '阳光电源': '300274', '海螺水泥': '600585',
        '万华化学': '600309', '和而泰': '002402', '西部材料': '002149',
    }
    
    def __init__(self):
        self.imported_stocks = []
        self.errors = []
    
    def import_from_csv(self, file_path: str) -> List[Dict[str, str]]:
        """
        从CSV文件导入股票
        
        支持的列：code, name, 代码, 股票代码, 名称, 股票名称
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            return self._parse_dataframe(df)
        except UnicodeDecodeError:
            # 尝试GBK编码
            df = pd.read_csv(file_path, encoding='gbk')
            return self._parse_dataframe(df)
        except Exception as e:
            self.errors.append(f"CSV导入失败: {str(e)}")
            return []
    
    def import_from_excel(self, file_path: str) -> List[Dict[str, str]]:
        """
        从Excel文件导入股票
        
        支持 .xlsx 和 .xls 格式
        """
        try:
            df = pd.read_excel(file_path)
            return self._parse_dataframe(df)
        except Exception as e:
            self.errors.append(f"Excel导入失败: {str(e)}")
            return []
    
    def import_from_clipboard(self) -> List[Dict[str, str]]:
        """
        从剪贴板导入股票
        
        支持格式：
        - 代码列表（每行一个）
        - 代码,名称（逗号分隔）
        - 制表符分隔
        """
        try:
            # 尝试读取剪贴板
            df = pd.read_clipboard()
            if not df.empty:
                return self._parse_dataframe(df)
        except Exception:
            pass
        
        # 尝试作为纯文本解析
        try:
            import pyperclip
            text = pyperclip.paste()
            return self._parse_text(text)
        except Exception as e:
            self.errors.append(f"剪贴板导入失败: {str(e)}")
            return []
    
    def import_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        从文本导入股票
        
        支持格式：
        - 600519 贵州茅台
        - 000001.SZ
        - 平安银行,000001
        - 每行一个代码
        """
        return self._parse_text(text)
    
    def import_from_image(self, image_path: str) -> List[Dict[str, str]]:
        """
        从图片导入股票（OCR识别）
        
        需要安装：easyocr 或 pytesseract
        """
        try:
            # 尝试使用 easyocr
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'])
            result = reader.readtext(image_path)
            
            # 提取文本
            texts = [item[1] for item in result]
            full_text = '\n'.join(texts)
            
            return self._parse_text(full_text)
            
        except ImportError:
            # 尝试使用 pytesseract
            try:
                from PIL import Image
                import pytesseract
                
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                
                return self._parse_text(text)
                
            except Exception as e:
                self.errors.append(f"图片OCR失败: {str(e)}")
                return []
        except Exception as e:
            self.errors.append(f"图片导入失败: {str(e)}")
            return []
    
    def _parse_dataframe(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """解析DataFrame提取股票信息"""
        stocks = []
        
        # 可能的列名映射
        code_columns = ['code', '股票代码', '代码', 'stock_code', 'symbol', '股票代码']
        name_columns = ['name', '股票名称', '名称', 'stock_name', '股票名称']
        
        # 查找代码列
        code_col = None
        for col in df.columns:
            if any(c.lower() in col.lower() for c in code_columns):
                code_col = col
                break
        
        # 查找名称列
        name_col = None
        for col in df.columns:
            if any(n.lower() in col.lower() for n in name_columns):
                name_col = col
                break
        
        # 如果没有找到代码列，尝试第一列
        if code_col is None and len(df.columns) > 0:
            code_col = df.columns[0]
        
        # 提取股票
        for _, row in df.iterrows():
            code_value = str(row.get(code_col, '')).strip()
            name_value = str(row.get(name_col, '')).strip() if name_col else ''
            
            parsed = self._parse_stock_code(code_value, name_value)
            if parsed:
                stocks.append(parsed)
        
        return stocks
    
    def _parse_text(self, text: str) -> List[Dict[str, str]]:
        """解析文本提取股票信息"""
        stocks = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试多种分隔符
            for delimiter in [',', '\t', ' ', '|']:
                if delimiter in line:
                    parts = line.split(delimiter)
                    
                    # 尝试识别代码和名称
                    for i, part in enumerate(parts):
                        part = part.strip()
                        parsed = self._parse_stock_code(part)
                        
                        if parsed:
                            # 尝试找名称
                            name = ''
                            for j, other_part in enumerate(parts):
                                if j != i and not self._is_stock_code(other_part.strip()):
                                    name = other_part.strip()
                                    break
                            
                            if name:
                                parsed['name'] = name
                            
                            stocks.append(parsed)
                            break
                    
                    if stocks and stocks[-1] in [p for p in stocks[:-1]]:
                        break
            else:
                # 没有分隔符，尝试整行解析
                parsed = self._parse_stock_code(line)
                if parsed:
                    stocks.append(parsed)
        
        # 去重
        seen = set()
        unique_stocks = []
        for stock in stocks:
            if stock['code'] not in seen:
                seen.add(stock['code'])
                unique_stocks.append(stock)
        
        return unique_stocks
    
    def _parse_stock_code(self, code_str: str, name: str = '') -> Optional[Dict[str, str]]:
        """解析单个股票代码"""
        code_str = code_str.strip().upper()
        
        # 尝试匹配A股
        match = self.A_SHARE_PATTERN.match(code_str)
        if match:
            code = match.group(1)
            suffix = match.group(2) or ('.SH' if code.startswith('6') else '.SZ')
            return {
                'code': code + suffix,
                'pure_code': code,
                'market': 'A股',
                'name': name or self.STOCK_NAME_MAP.get(code_str, '')
            }
        
        # 尝试匹配港股
        match = self.HK_PATTERN.match(code_str)
        if match:
            code = match.group(1).zfill(5)
            return {
                'code': code + '.HK',
                'pure_code': code,
                'market': '港股',
                'name': name
            }
        
        # 尝试匹配美股
        match = self.US_PATTERN.match(code_str)
        if match:
            code = match.group(1)
            return {
                'code': code,
                'pure_code': code,
                'market': '美股',
                'name': name
            }
        
        # 尝试从名称映射查找
        if code_str in self.STOCK_NAME_MAP:
            code = self.STOCK_NAME_MAP[code_str]
            return {
                'code': code + ('.SH' if code.startswith('6') else '.SZ'),
                'pure_code': code,
                'market': 'A股',
                'name': code_str
            }
        
        return None
    
    def _is_stock_code(self, text: str) -> bool:
        """判断文本是否为股票代码"""
        text = text.strip().upper()
        return bool(
            self.A_SHARE_PATTERN.match(text) or
            self.HK_PATTERN.match(text) or
            self.US_PATTERN.match(text)
        )
    
    def get_watchlist_template(self) -> str:
        """生成自选股列表模板"""
        template = """# 股票列表模板
# 支持格式：代码,名称（可选）
# 支持市场：A股、港股、美股

# A股示例
600519,贵州茅台
000001,平安银行
300750,宁德时代
002149,西部材料

# 港股示例
00700.HK,腾讯控股
09988.HK,阿里巴巴

# 美股示例
AAPL,苹果
TSLA,特斯拉
MSFT,微软
"""
        return template
    
    def export_to_csv(self, stocks: List[Dict[str, str]], output_path: str):
        """导出股票列表到CSV"""
        df = pd.DataFrame(stocks)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    def validate_stocks(self, stocks: List[Dict[str, str]]) -> Dict[str, List]:
        """验证股票列表有效性"""
        valid = []
        invalid = []
        
        for stock in stocks:
            code = stock.get('code', '')
            if self._is_stock_code(code):
                valid.append(stock)
            else:
                invalid.append(stock)
        
        return {'valid': valid, 'invalid': invalid}


# 便捷函数
def import_stocks_from_file(file_path: str) -> List[Dict[str, str]]:
    """从文件导入股票"""
    importer = StockImporter()
    
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.csv':
        return importer.import_from_csv(file_path)
    elif suffix in ['.xlsx', '.xls']:
        return importer.import_from_excel(file_path)
    elif suffix in ['.png', '.jpg', '.jpeg', '.bmp']:
        return importer.import_from_image(file_path)
    else:
        # 尝试作为文本文件读取
        with open(file_path, 'r', encoding='utf-8') as f:
            return importer.import_from_text(f.read())


def import_stocks_from_text(text: str) -> List[Dict[str, str]]:
    """从文本导入股票"""
    importer = StockImporter()
    return importer.import_from_text(text)
