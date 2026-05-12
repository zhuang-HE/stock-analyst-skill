"""
缠论分析模块
实现缠论核心概念：笔、线段、中枢、买卖点
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class BiDirection(Enum):
    """笔方向"""
    UP = "向上"
    DOWN = "向下"


class BuyPointType(Enum):
    """买卖点类型"""
    FIRST_BUY = "一买"
    SECOND_BUY = "二买"
    THIRD_BUY = "三买"
    FIRST_SELL = "一卖"
    SECOND_SELL = "二卖"
    THIRD_SELL = "三卖"


@dataclass
class Bi:
    """笔"""
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    direction: BiDirection
    
    @property
    def height(self) -> float:
        return abs(self.end_price - self.start_price)


@dataclass
class Zhongshu:
    """中枢"""
    start_idx: int
    end_idx: int
    gg: float  # 高点
    dd: float  # 低点
    zg: float  # 中枢高点
    zd: float  # 中枢低点
    
    @property
    def center(self) -> float:
        return (self.zg + self.zd) / 2


@dataclass
class BuyPoint:
    """买卖点"""
    idx: int
    price: float
    bp_type: BuyPointType
    confidence: float
    description: str


class ChanlunAnalyzer:
    """缠论分析器"""
    
    def __init__(self, min_bi_klines: int = 5):
        """
        初始化
        
        Args:
            min_bi_klines: 构成一笔的最少K线数（默认5根）
        """
        self.min_bi_klines = min_bi_klines
        self.df = None
        self.bis = []
        self.zhongshus = []
        self.buy_points = []
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        执行完整缠论分析
        
        Args:
            df: 包含high, low的DataFrame
            
        Returns:
            分析结果字典
        """
        self.df = df.copy()
        
        # 1. 识别分型
        fenxings = self._identify_fenxing()
        
        # 2. 构建笔
        self.bis = self._build_bi(fenxings)
        
        # 3. 识别中枢
        self.zhongshus = self._identify_zhongshu()
        
        # 4. 识别买卖点
        self.buy_points = self._identify_buy_points()
        
        return {
            'fenxing_count': len(fenxings),
            'bi_count': len(self.bis),
            'zhongshu_count': len(self.zhongshus),
            'buy_points': self.buy_points,
            'current_trend': self._get_current_trend(),
            'nearest_zhongshu': self._get_nearest_zhongshu(),
            'summary': self._generate_summary()
        }
    
    def _identify_fenxing(self) -> List[Dict]:
        """识别顶底分型"""
        highs = self.df['high'].values
        lows = self.df['low'].values
        
        fenxings = []
        
        for i in range(1, len(self.df) - 1):
            # 顶分型
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                fenxings.append({
                    'idx': i,
                    'type': 'top',
                    'price': highs[i]
                })
            # 底分型
            elif lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                fenxings.append({
                    'idx': i,
                    'type': 'bottom',
                    'price': lows[i]
                })
        
        return fenxings
    
    def _build_bi(self, fenxings: List[Dict]) -> List[Bi]:
        """构建笔"""
        if len(fenxings) < 2:
            return []
        
        bis = []
        last_fenxing = fenxings[0]
        
        for i in range(1, len(fenxings)):
            current = fenxings[i]
            
            # 检查是否形成新笔（顶底交替且间隔足够）
            if current['type'] != last_fenxing['type']:
                kline_distance = current['idx'] - last_fenxing['idx']
                
                if kline_distance >= self.min_bi_klines:
                    direction = BiDirection.UP if current['type'] == 'top' else BiDirection.DOWN
                    
                    bi = Bi(
                        start_idx=last_fenxing['idx'],
                        end_idx=current['idx'],
                        start_price=last_fenxing['price'],
                        end_price=current['price'],
                        direction=direction
                    )
                    bis.append(bi)
                    last_fenxing = current
        
        return bis
    
    def _identify_zhongshu(self) -> List[Zhongshu]:
        """识别中枢（三笔重叠区间）"""
        if len(self.bis) < 3:
            return []

        zhongshus = []

        for i in range(len(self.bis) - 2):
            bi1, bi2, bi3 = self.bis[i], self.bis[i+1], self.bis[i+2]

            # 收集三笔的起止价格
            prices = [bi1.start_price, bi1.end_price,
                      bi2.start_price, bi2.end_price,
                      bi3.start_price, bi3.end_price]

            # 中枢核心区间：三笔重叠部分的上下沿
            # zg = 重叠区间的上沿（三笔最低的高点）
            # zd = 重叠区间的下沿（三笔最高的低点）
            bi_highs = [max(bi1.start_price, bi1.end_price),
                        max(bi2.start_price, bi2.end_price),
                        max(bi3.start_price, bi3.end_price)]
            bi_lows = [min(bi1.start_price, bi1.end_price),
                       min(bi2.start_price, bi2.end_price),
                       min(bi3.start_price, bi3.end_price)]

            zg = min(bi_highs)  # 三笔中最低的高点 = 重叠上沿
            zd = max(bi_lows)   # 三笔中最高的低点 = 重叠下沿
            gg = max(bi_highs)  # 三笔中最高的高点
            dd = min(bi_lows)   # 三笔中最低的低点
            
            # 确认有重叠区域
            if zg > zd:
                zhongshu = Zhongshu(
                    start_idx=bi1.start_idx,
                    end_idx=bi3.end_idx,
                    gg=gg,
                    dd=dd,
                    zg=zg,
                    zd=zd
                )
                zhongshus.append(zhongshu)
        
        return zhongshus
    
    def _identify_buy_points(self) -> List[BuyPoint]:
        """识别买卖点（遍历所有笔序列，非仅最近5笔）"""
        buy_points = []
        n = len(self.bis)

        if n < 3:
            return buy_points

        # 遍历笔序列，寻找背驰段
        for i in range(n - 2):
            bi_a = self.bis[i]
            bi_b = self.bis[i + 1]
            bi_c = self.bis[i + 2]

            # ===== 一买：下跌趋势背驰 =====
            if (bi_a.direction == BiDirection.DOWN
                    and bi_b.direction == BiDirection.UP
                    and bi_c.direction == BiDirection.DOWN
                    and bi_c.height < bi_a.height * 0.8):
                buy_points.append(BuyPoint(
                    idx=bi_c.end_idx,
                    price=bi_c.end_price,
                    bp_type=BuyPointType.FIRST_BUY,
                    confidence=0.80,
                    description=f"一买：下跌趋势背驰，第一笔高度{bi_a.height:.2f}，第三笔高度{bi_c.height:.2f}"
                ))

            # ===== 一卖：上涨趋势背驰 =====
            if (bi_a.direction == BiDirection.UP
                    and bi_b.direction == BiDirection.DOWN
                    and bi_c.direction == BiDirection.UP
                    and bi_c.height < bi_a.height * 0.8):
                buy_points.append(BuyPoint(
                    idx=bi_c.end_idx,
                    price=bi_c.end_price,
                    bp_type=BuyPointType.FIRST_SELL,
                    confidence=0.80,
                    description=f"一卖：上涨趋势背驰，第一笔高度{bi_a.height:.2f}，第三笔高度{bi_c.height:.2f}"
                ))

        # ===== 二买：一买后的回调不创新低 =====
        first_buys = [bp for bp in buy_points if bp.bp_type == BuyPointType.FIRST_BUY]
        for fb in first_buys:
            # 找到一买对应的笔在 bis 中的索引
            fb_bi_idx = None
            for j, bi in enumerate(self.bis):
                if bi.end_idx == fb.idx:
                    fb_bi_idx = j
                    break
            if fb_bi_idx is None or fb_bi_idx + 2 >= n:
                continue
            # 一买后的笔应为向上
            bi_after = self.bis[fb_bi_idx + 1] if fb_bi_idx + 1 < n else None
            # 再后面一笔向下回调，不创新低
            bi_pullback = self.bis[fb_bi_idx + 2] if fb_bi_idx + 2 < n else None
            if (bi_after and bi_pullback
                    and bi_after.direction == BiDirection.UP
                    and bi_pullback.direction == BiDirection.DOWN
                    and bi_pullback.end_price > fb.price):
                buy_points.append(BuyPoint(
                    idx=bi_pullback.end_idx,
                    price=bi_pullback.end_price,
                    bp_type=BuyPointType.SECOND_BUY,
                    confidence=0.75,
                    description=f"二买：一买后回调不创新低（一买价{fb.price:.2f}，回调价{bi_pullback.end_price:.2f}）"
                ))

        # ===== 二卖：一卖后的反弹不创新高 =====
        first_sells = [bp for bp in buy_points if bp.bp_type == BuyPointType.FIRST_SELL]
        for fs in first_sells:
            fs_bi_idx = None
            for j, bi in enumerate(self.bis):
                if bi.end_idx == fs.idx:
                    fs_bi_idx = j
                    break
            if fs_bi_idx is None or fs_bi_idx + 2 >= n:
                continue
            bi_after = self.bis[fs_bi_idx + 1] if fs_bi_idx + 1 < n else None
            bi_pullback = self.bis[fs_bi_idx + 2] if fs_bi_idx + 2 < n else None
            if (bi_after and bi_pullback
                    and bi_after.direction == BiDirection.DOWN
                    and bi_pullback.direction == BiDirection.UP
                    and bi_pullback.end_price < fs.price):
                buy_points.append(BuyPoint(
                    idx=bi_pullback.end_idx,
                    price=bi_pullback.end_price,
                    bp_type=BuyPointType.SECOND_SELL,
                    confidence=0.75,
                    description=f"二卖：一卖后反弹不创新高（一卖价{fs.price:.2f}，反弹价{bi_pullback.end_price:.2f}）"
                ))

        # ===== 三买：突破中枢后回抽不进入中枢 =====
        if self.zhongshus:
            zs = self.zhongshus[-1]
            for i in range(max(0, n - 3), n - 1):
                bi_up = self.bis[i]
                bi_pullback = self.bis[i + 1]
                if (bi_up.direction == BiDirection.UP
                        and bi_pullback.direction == BiDirection.DOWN
                        and bi_up.end_price > zs.zg
                        and bi_pullback.end_price > zs.zg):
                    buy_points.append(BuyPoint(
                        idx=bi_pullback.end_idx,
                        price=bi_pullback.end_price,
                        bp_type=BuyPointType.THIRD_BUY,
                        confidence=0.85,
                        description=f"三买：突破中枢{zs.zg:.2f}后回抽不进入（回抽价{bi_pullback.end_price:.2f}）"
                    ))
                    break  # 只取最近一个

        # ===== 三卖：跌破中枢后回抽不进入中枢 =====
        if self.zhongshus:
            zs = self.zhongshus[-1]
            for i in range(max(0, n - 3), n - 1):
                bi_down = self.bis[i]
                bi_pullback = self.bis[i + 1]
                if (bi_down.direction == BiDirection.DOWN
                        and bi_pullback.direction == BiDirection.UP
                        and bi_down.end_price < zs.zd
                        and bi_pullback.end_price < zs.zd):
                    buy_points.append(BuyPoint(
                        idx=bi_pullback.end_idx,
                        price=bi_pullback.end_price,
                        bp_type=BuyPointType.THIRD_SELL,
                        confidence=0.85,
                        description=f"三卖：跌破中枢{zs.zd:.2f}后回抽不进入（回抽价{bi_pullback.end_price:.2f}）"
                    ))
                    break  # 只取最近一个

        # 按 idx 排序并去重（同一位置只保留最高置信度的）
        buy_points.sort(key=lambda bp: bp.idx)
        seen = set()
        unique = []
        for bp in buy_points:
            if bp.idx not in seen:
                seen.add(bp.idx)
                unique.append(bp)
        return unique
    
    def _get_current_trend(self) -> str:
        """获取当前趋势"""
        if not self.bis:
            return "未知"
        
        last_bi = self.bis[-1]
        
        if last_bi.direction == BiDirection.UP:
            return "向上笔进行中"
        else:
            return "向下笔进行中"
    
    def _get_nearest_zhongshu(self) -> Optional[Dict]:
        """获取最近的中枢信息"""
        if not self.zhongshus:
            return None
        
        zs = self.zhongshus[-1]
        return {
            'zg': round(zs.zg, 2),
            'zd': round(zs.zd, 2),
            'center': round(zs.center, 2),
            'range': f"{zs.zd:.2f} - {zs.zg:.2f}"
        }
    
    def _generate_summary(self) -> str:
        """生成分析摘要"""
        if not self.buy_points:
            return f"当前处于{self._get_current_trend()}，未识别到明确买卖点"
        
        latest_bp = self.buy_points[-1]
        return f"最新信号：{latest_bp.bp_type.value}（置信度{latest_bp.confidence:.0%}）"
    
    def get_buy_point_advice(self) -> Dict:
        """获取买卖点建议"""
        if not self.buy_points:
            return {
                'has_signal': False,
                'advice': "暂无明确买卖点信号",
                'action': "观望"
            }
        
        latest_bp = self.buy_points[-1]
        
        if latest_bp.bp_type in [BuyPointType.FIRST_BUY, BuyPointType.SECOND_BUY, BuyPointType.THIRD_BUY]:
            return {
                'has_signal': True,
                'signal_type': latest_bp.bp_type.value,
                'price': round(latest_bp.price, 2),
                'confidence': round(latest_bp.confidence, 2),
                'advice': latest_bp.description,
                'action': "买入"
            }
        else:
            return {
                'has_signal': True,
                'signal_type': latest_bp.bp_type.value,
                'price': round(latest_bp.price, 2),
                'confidence': round(latest_bp.confidence, 2),
                'advice': latest_bp.description,
                'action': "卖出"
            }


def analyze_chanlun(df: pd.DataFrame, min_bi_klines: int = 5) -> Dict:
    """
    缠论分析入口函数
    
    Args:
        df: 包含high, low的DataFrame
        min_bi_klines: 构成一笔的最少K线数
        
    Returns:
        缠论分析结果
    """
    analyzer = ChanlunAnalyzer(min_bi_klines=min_bi_klines)
    return analyzer.analyze(df)
