# -*- coding: utf-8 -*-
"""
策略加载器 v1.0

从 YAML 策略配置文件中加载策略参数和规则，将配置映射为可执行的信号计算逻辑。

用法:
    loader = StrategyLoader()
    loader.load_all()  # 加载所有策略文件
    
    # 获取指标计算参数
    ma_config = loader.get_indicator_config('ma')
    # 获取信号规则
    signals = loader.evaluate_signals(indicators_data)
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Tuple


class StrategyLoader:
    """策略加载器 — 从 YAML 文件加载策略配置"""

    def __init__(self, strategy_dir: str = None):
        if strategy_dir is None:
            strategy_dir = os.path.dirname(os.path.abspath(__file__))
        self.strategy_dir = strategy_dir
        self._configs: Dict[str, dict] = {}
        self._indicators_config: dict = {}
        self._signals_config: dict = {}
        self._scoring_config: dict = {}
        self._chanlun_config: dict = {}

    def load_all(self) -> None:
        """加载所有策略配置文件"""
        config_files = {
            'indicators': 'indicators.yaml',
            'scoring': 'scoring.yaml',
            'chanlun': 'chanlun.yaml',
        }
        for name, filename in config_files.items():
            filepath = os.path.join(self.strategy_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self._configs[name] = config
                    if name == 'indicators':
                        self._indicators_config = config
                    elif name == 'scoring':
                        self._scoring_config = config
                    elif name == 'chanlun':
                        self._chanlun_config = config

    # ==================== 指标配置获取 ====================

    def get_indicator_config(self, name: str) -> dict:
        """获取指定技术指标的配置"""
        indicators = self._indicators_config.get('indicators', {})
        return indicators.get(name, {})

    def get_all_indicators(self) -> dict:
        """获取所有技术指标的配置"""
        return self._indicators_config.get('indicators', {})

    def get_ma_periods(self) -> List[int]:
        """获取均线周期列表"""
        return self.get_indicator_config('ma').get('periods', [5, 10, 20, 60])

    def get_rsi_period(self) -> int:
        """获取RSI计算周期"""
        return self.get_indicator_config('rsi').get('period', 14)

    def get_kdj_params(self) -> Tuple[int, int, int]:
        """获取KDJ参数: (k_period, d_period, j_factor)"""
        kdj = self.get_indicator_config('kdj')
        return kdj.get('k_period', 9), kdj.get('d_period', 3), 3

    def get_macd_params(self) -> Tuple[int, int, int]:
        """获取MACD参数: (fast, slow, signal)"""
        macd = self.get_indicator_config('macd')
        return macd.get('fast', 12), macd.get('slow', 26), macd.get('signal', 9)

    def get_bollinger_params(self) -> Tuple[int, float]:
        """获取布林带参数: (period, std_dev)"""
        boll = self.get_indicator_config('bollinger')
        return boll.get('period', 20), boll.get('std_dev', 2)

    # ==================== 评分配置获取 ====================

    def get_scoring_weights(self) -> dict:
        """获取各维度评分权重"""
        return self._scoring_config.get('weights', {})

    def get_resonance_levels(self) -> List[dict]:
        """获取共振级别定义"""
        return self._scoring_config.get('resonance_levels', [])

    def get_resonance_level(self, score: float) -> dict:
        """根据分数获取共振级别"""
        levels = self.get_resonance_levels()
        for level in levels:
            if score >= level['min_score']:
                return level
        return levels[-1] if levels else {'name': '未知', 'confidence': 0.0}

    # ==================== 缠论配置获取 ====================

    def get_chanlun_config(self) -> dict:
        """获取缠论分析配置"""
        return self._chanlun_config.get('chanlun', {})

    def get_chanlun_buy_point_score(self, bp_type: str) -> int:
        """获取缠论买点对应的分数"""
        scores = self._scoring_config.get('weights', {}).get(
            'chanlun', {}).get('buy_point_scores', {})
        return scores.get(bp_type, 10)

    def get_position_rules(self) -> dict:
        """获取仓位建议规则"""
        return self.get_chanlun_config().get('position_rules', {})

    # ==================== 信号评估 ====================

    def evaluate_indicator_signals(self, indicator_name: str,
                                   data: dict) -> List[dict]:
        """评估某个指标的所有信号规则，返回触发的信号列表

        Args:
            indicator_name: 指标名称 (ma/rsi/kdj/macd/bollinger/volume)
            data: 指标计算数据，如 {'rsi': 72, 'price': 15.5, 'ma5': 15.0, ...}

        Returns:
            [{'name': '超买', 'score': -10, 'description': '...'}, ...]
        """
        config = self.get_indicator_config(indicator_name)
        results = []

        for signal_group_name, signal_group in config.get('signals', {}).items():
            if isinstance(signal_group, list):
                for signal in signal_group:
                    if self._evaluate_condition(signal.get('condition', ''), data):
                        results.append({
                            'group': signal_group_name,
                            'name': signal.get('name', ''),
                            'score': signal.get('score', 0),
                            'description': signal.get('description', ''),
                            'action': signal.get('action', ''),
                            'additional': signal.get('additional', ''),
                        })

        return results

    def _evaluate_condition(self, condition: str, data: dict) -> bool:
        """安全评估条件表达式"""
        if not condition or condition.strip() == '':
            return False

        condition = condition.strip()

        # 特殊条件处理
        if condition == 'macd_hist_increasing_positive':
            return data.get('macd_hist', 0) > 0 and data.get('macd_hist_prev', 0) < data.get('macd_hist', 0)
        if condition == 'macd_hist_increasing_negative':
            return data.get('macd_hist', 0) < 0 and data.get('macd_hist_prev', 0) > data.get('macd_hist', 0)
        if condition == 'macd_hist_decreasing_positive':
            return data.get('macd_hist', 0) > 0 and data.get('macd_hist_prev', 0) > data.get('macd_hist', 0)
        if condition == 'macd_golden_cross':
            return data.get('macd_dif', 0) > data.get('macd_dea', 0) and data.get('macd_dif_prev', 0) <= data.get('macd_dea_prev', 0)
        if condition == 'macd_death_cross':
            return data.get('macd_dif', 0) < data.get('macd_dea', 0) and data.get('macd_dif_prev', 0) >= data.get('macd_dea_prev', 0)
        if condition == 'ma5_cross_above_ma20':
            return data.get('ma5', 0) > data.get('ma20', 0) and data.get('ma5_prev', 0) <= data.get('ma20_prev', 0)
        if condition == 'ma5_cross_below_ma20':
            return data.get('ma5', 0) < data.get('ma20', 0) and data.get('ma5_prev', 0) >= data.get('ma20_prev', 0)
        if condition == 'k_cross_above_d':
            return data.get('k', 0) > data.get('d', 0) and data.get('k_prev', 0) <= data.get('d_prev', 0)
        if condition == 'k_cross_below_d':
            return data.get('k', 0) < data.get('d', 0) and data.get('k_prev', 0) >= data.get('d_prev', 0)
        if condition == 'rsi_bullish_divergence':
            return data.get('rsi_divergence') == 'bullish'
        if condition == 'rsi_bearish_divergence':
            return data.get('rsi_divergence') == 'bearish'
        if condition == 'macd_bullish_divergence':
            return data.get('macd_divergence') == 'bullish'
        if condition == 'macd_bearish_divergence':
            return data.get('macd_divergence') == 'bearish'
        if 'boll_bandwidth' in condition:
            # 需要动态计算，从data获取
            bw = data.get('boll_bandwidth', 20)
            if condition == 'boll_bandwidth < 10':
                return bw < 10
            if condition == 'boll_bandwidth > 25':
                return bw > 25

        # 通用条件评估
        try:
            # 构建安全的求值环境
            safe_dict = {}
            for key, val in data.items():
                if isinstance(val, (int, float, bool)):
                    safe_dict[key] = val

            # 替换关键字
            eval_condition = condition
            # 处理 "X around Y" 语法
            if ' around ' in eval_condition:
                parts = eval_condition.split(' around ')
                var_a = parts[0].strip()
                var_b = parts[1].strip()
                if var_a in safe_dict and var_b in safe_dict:
                    return abs(safe_dict[var_a] - safe_dict[var_b]) < safe_dict[var_b] * 0.05
                return False

            return bool(eval(eval_condition, {"__builtins__": {}}, safe_dict))
        except Exception:
            return False

    # ==================== 综合信号评估 ====================

    def evaluate_all_signals(self, data: dict) -> dict:
        """评估所有策略信号

        Args:
            data: 包含所有指标值的字典
                {
                    'price': 15.5,
                    'ma5': 15.0, 'ma10': 14.8, 'ma20': 14.5, 'ma60': 13.0,
                    'ma5_prev': 14.9, ...,
                    'rsi': 65, 'k': 70, 'd': 65, 'j': 80,
                    'macd_dif': 0.5, 'macd_dea': 0.3, 'macd_hist': 0.2,
                    'macd_dif_prev': 0.3, 'macd_dea_prev': 0.3, ...,
                    'boll_upper': 16.0, 'boll_mid': 15.0, 'boll_lower': 14.0,
                    'boll_bandwidth': 15,
                    'volume': 1000000, 'avg_volume_20': 800000,
                    'close': 15.5, 'prev_close': 15.3,
                }

        Returns:
            {
                'signals': [...],     # 所有触发信号的列表
                'total_bullish': 0,   # 看涨总分数
                'total_bearish': 0,   # 看跌总分数
                'net_score': 0,       # 净得分
                'by_category': {...}  # 按类别分组的信号
            }
        """
        all_signals = []
        total_bullish = 0
        total_bearish = 0
        by_category = {}

        indicator_names = ['ma', 'rsi', 'kdj', 'macd', 'bollinger', 'volume']

        for name in indicator_names:
            signals = self.evaluate_indicator_signals(name, data)
            if signals:
                cat_signals = []
                for s in signals:
                    score = s.get('score', 0)
                    if score > 0:
                        total_bullish += score
                    else:
                        total_bearish += abs(score)
                    all_signals.append(s)
                    cat_signals.append(s)
                by_category[name] = cat_signals

        return {
            'signals': all_signals,
            'total_bullish': total_bullish,
            'total_bearish': total_bearish,
            'net_score': total_bullish - total_bearish,
            'signal_count': len(all_signals),
            'by_category': by_category,
            'resonance_level': self.get_resonance_level(total_bullish - total_bearish),
        }


# 便捷函数
def load_strategies(strategy_dir: str = None) -> StrategyLoader:
    """加载所有策略配置"""
    loader = StrategyLoader(strategy_dir)
    loader.load_all()
    return loader
