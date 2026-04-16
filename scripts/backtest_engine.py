# -*- coding: utf-8 -*-
"""
回测引擎 - 验证分析准确率
借鉴 daily_stock_analysis 的 AI 回测验证功能

功能：
1. 历史信号回测
2. 胜率统计
3. 收益分析
4. 生成回测报告
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')


@dataclass
class TradeSignal:
    """交易信号"""
    date: str
    code: str
    action: str  # 买入/卖出/观望
    price: float
    target_price: float
    stop_loss: float
    score: int
    reason: str


@dataclass
class TradeResult:
    """交易结果"""
    signal: TradeSignal
    exit_date: str
    exit_price: float
    exit_reason: str  # 止盈/止损/到期
    return_pct: float
    holding_days: int
    success: bool


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.signals: List[TradeSignal] = []
        self.results: List[TradeResult] = []
        self.capital = initial_capital
        self.positions: Dict[str, Dict] = {}
        
    def load_historical_signals(self, code: str, start_date: str, end_date: str) -> List[TradeSignal]:
        """
        加载历史信号
        
        实际使用时，应该从数据库或文件加载历史分析结果
        这里提供模拟数据生成逻辑
        """
        signals = []
        
        try:
            import akshare as ak
            
            # 获取历史数据
            hist = ak.stock_zh_a_daily(symbol=f'sh{code}' if code.startswith('6') else f'sz{code}', 
                                      adjust='qfq')
            
            if hist is None or hist.empty:
                return signals
            
            # 过滤日期范围
            hist['date'] = pd.to_datetime(hist.index if 'date' not in hist.columns else hist['date'])
            mask = (hist['date'] >= start_date) & (hist['date'] <= end_date)
            hist = hist[mask]
            
            # 生成模拟信号（实际应该从历史分析记录中加载）
            for i in range(len(hist) - 1):
                row = hist.iloc[i]
                next_row = hist.iloc[i + 1]
                
                # 简单策略：RSI超卖买入，超买卖出
                close_col = 'close' if 'close' in hist.columns else '收盘'
                
                # 计算RSI
                if i >= 14:
                    prices = hist[close_col].iloc[i-13:i+1]
                    delta = prices.diff()
                    gain = delta.where(delta > 0, 0).mean()
                    loss = (-delta.where(delta < 0, 0)).mean()
                    rs = gain / loss if loss != 0 else 0
                    rsi = 100 - (100 / (1 + rs))
                    
                    current_price = row[close_col]
                    
                    if rsi < 30:
                        signal = TradeSignal(
                            date=str(row['date'])[:10],
                            code=code,
                            action='买入',
                            price=current_price,
                            target_price=current_price * 1.10,
                            stop_loss=current_price * 0.95,
                            score=65,
                            reason=f'RSI超卖({rsi:.1f})'
                        )
                        signals.append(signal)
                    elif rsi > 70:
                        signal = TradeSignal(
                            date=str(row['date'])[:10],
                            code=code,
                            action='卖出',
                            price=current_price,
                            target_price=current_price * 0.90,
                            stop_loss=current_price * 1.05,
                            score=35,
                            reason=f'RSI超买({rsi:.1f})'
                        )
                        signals.append(signal)
            
        except Exception as e:
            print(f"加载历史信号失败: {e}")
        
        return signals
    
    def run_backtest(self, signals: List[TradeSignal], max_holding_days: int = 20) -> List[TradeResult]:
        """
        执行回测
        
        Args:
            signals: 交易信号列表
            max_holding_days: 最大持仓天数
        """
        results = []
        
        for signal in signals:
            result = self._simulate_trade(signal, max_holding_days)
            if result:
                results.append(result)
        
        self.results = results
        return results
    
    def _simulate_trade(self, signal: TradeSignal, max_holding_days: int) -> Optional[TradeResult]:
        """模拟单笔交易"""
        try:
            import akshare as ak
            
            code = signal.code
            market = 'sh' if code.startswith('6') else 'sz'
            
            # 获取信号日后的数据
            hist = ak.stock_zh_a_daily(symbol=f'{market}{code}', adjust='qfq')
            if hist is None or hist.empty:
                return None
            
            close_col = 'close' if 'close' in hist.columns else '收盘'
            hist['date'] = pd.to_datetime(hist.index if 'date' not in hist.columns else hist['date'])
            
            # 找到信号日
            signal_date = pd.to_datetime(signal.date)
            future_data = hist[hist['date'] > signal_date]
            
            if future_data.empty:
                return None
            
            entry_price = signal.price
            target = signal.target_price
            stop = signal.stop_loss
            
            # 模拟持仓
            for i, (_, row) in enumerate(future_data.iterrows()):
                if i >= max_holding_days:
                    # 到期平仓
                    exit_price = row[close_col]
                    return_pct = (exit_price - entry_price) / entry_price * 100
                    
                    return TradeResult(
                        signal=signal,
                        exit_date=str(row['date'])[:10],
                        exit_price=exit_price,
                        exit_reason='到期平仓',
                        return_pct=return_pct,
                        holding_days=i + 1,
                        success=return_pct > 0
                    )
                
                current_price = row[close_col]
                
                # 检查止盈
                if signal.action == '买入' and current_price >= target:
                    return_pct = (target - entry_price) / entry_price * 100
                    return TradeResult(
                        signal=signal,
                        exit_date=str(row['date'])[:10],
                        exit_price=target,
                        exit_reason='止盈',
                        return_pct=return_pct,
                        holding_days=i + 1,
                        success=True
                    )
                
                # 检查止损
                if signal.action == '买入' and current_price <= stop:
                    return_pct = (stop - entry_price) / entry_price * 100
                    return TradeResult(
                        signal=signal,
                        exit_date=str(row['date'])[:10],
                        exit_price=stop,
                        exit_reason='止损',
                        return_pct=return_pct,
                        holding_days=i + 1,
                        success=False
                    )
                
                # 卖出信号反向逻辑
                if signal.action == '卖出':
                    if current_price <= target:  # 做空止盈
                        return_pct = (entry_price - target) / entry_price * 100
                        return TradeResult(
                            signal=signal,
                            exit_date=str(row['date'])[:10],
                            exit_price=target,
                            exit_reason='止盈(做空)',
                            return_pct=return_pct,
                            holding_days=i + 1,
                            success=True
                        )
                    if current_price >= stop:  # 做空止损
                        return_pct = (entry_price - stop) / entry_price * 100
                        return TradeResult(
                            signal=signal,
                            exit_date=str(row['date'])[:10],
                            exit_price=stop,
                            exit_reason='止损(做空)',
                            return_pct=return_pct,
                            holding_days=i + 1,
                            success=False
                        )
            
        except Exception as e:
            print(f"模拟交易失败 {signal.code}: {e}")
        
        return None
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """计算回测统计指标"""
        if not self.results:
            return {'error': '无回测结果'}
        
        total_trades = len(self.results)
        winning_trades = sum(1 for r in self.results if r.success)
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        returns = [r.return_pct for r in self.results]
        avg_return = np.mean(returns) if returns else 0
        max_return = max(returns) if returns else 0
        min_return = min(returns) if returns else 0
        
        winning_returns = [r.return_pct for r in self.results if r.success]
        losing_returns = [r.return_pct for r in self.results if not r.success]
        
        avg_win = np.mean(winning_returns) if winning_returns else 0
        avg_loss = np.mean(losing_returns) if losing_returns else 0
        
        # 盈亏比
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 持仓天数
        holding_days = [r.holding_days for r in self.results]
        avg_holding_days = np.mean(holding_days) if holding_days else 0
        
        # 按退出原因统计
        exit_reasons = {}
        for r in self.results:
            reason = r.exit_reason
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        # 累计收益曲线
        cumulative_return = 0
        equity_curve = []
        for r in self.results:
            cumulative_return += r.return_pct
            equity_curve.append(cumulative_return)
        
        # 最大回撤
        max_drawdown = 0
        peak = 0
        for ret in equity_curve:
            if ret > peak:
                peak = ret
            drawdown = peak - ret
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'max_return': round(max_return, 2),
            'min_return': round(min_return, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'avg_holding_days': round(avg_holding_days, 1),
            'exit_reasons': exit_reasons,
            'max_drawdown': round(max_drawdown, 2),
            'total_return': round(cumulative_return, 2)
        }
    
    def generate_report(self, output_path: str = None) -> str:
        """生成回测报告"""
        stats = self.calculate_statistics()
        
        if 'error' in stats:
            return f"回测报告生成失败: {stats['error']}"
        
        lines = [
            "# 📊 策略回测报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 回测概况",
            "",
            f"- **总交易次数**: {stats['total_trades']}",
            f"- **盈利次数**: {stats['winning_trades']}",
            f"- **亏损次数**: {stats['losing_trades']}",
            f"- **胜率**: {stats['win_rate']}%",
            f"- **盈亏比**: 1:{stats['profit_loss_ratio']}",
            f"- **平均收益**: {stats['avg_return']}%",
            f"- **最大单笔盈利**: {stats['max_return']}%",
            f"- **最大单笔亏损**: {stats['min_return']}%",
            f"- **平均盈利**: {stats['avg_win']}%",
            f"- **平均亏损**: {stats['avg_loss']}%",
            f"- **平均持仓天数**: {stats['avg_holding_days']}天",
            f"- **最大回撤**: {stats['max_drawdown']}%",
            f"- **累计收益**: {stats['total_return']}%",
            "",
            "## 退出原因分布",
            ""
        ]
        
        for reason, count in stats['exit_reasons'].items():
            pct = count / stats['total_trades'] * 100
            lines.append(f"- {reason}: {count}次 ({pct:.1f}%)")
        
        lines.extend([
            "",
            "## 交易明细",
            "",
            "| 日期 | 代码 | 操作 | 入场价 | 出场价 | 收益 | 持仓天数 | 退出原因 |",
            "|------|------|------|--------|--------|------|----------|----------|"
        ])
        
        for r in self.results[:50]:  # 只显示前50条
            emoji = "✅" if r.success else "❌"
            lines.append(
                f"| {r.signal.date} | {r.signal.code} | {r.signal.action} | "
                f"{r.signal.price:.2f} | {r.exit_price:.2f} | "
                f"{emoji} {r.return_pct:+.2f}% | {r.holding_days}天 | {r.exit_reason} |"
            )
        
        if len(self.results) > 50:
            lines.append(f"\n*... 还有 {len(self.results) - 50} 条记录 ...*")
        
        lines.extend([
            "",
            "## 策略评估",
            ""
        ])
        
        # 策略评估
        if stats['win_rate'] >= 60 and stats['profit_loss_ratio'] >= 1.5:
            evaluation = "🟢 **优秀策略** - 胜率和盈亏比均表现良好，建议实盘使用"
        elif stats['win_rate'] >= 50 and stats['profit_loss_ratio'] >= 1.0:
            evaluation = "🟡 **良好策略** - 整体表现尚可，可优化后使用"
        elif stats['win_rate'] >= 40:
            evaluation = "🟠 **一般策略** - 需要进一步优化参数或逻辑"
        else:
            evaluation = "🔴 **较差策略** - 不建议使用，需重新设计"
        
        lines.append(evaluation)
        
        lines.extend([
            "",
            "### 改进建议",
            ""
        ])
        
        if stats['win_rate'] < 50:
            lines.append("- 胜率偏低，建议优化入场信号或增加过滤条件")
        if stats['profit_loss_ratio'] < 1.5:
            lines.append("- 盈亏比不足，建议调整止盈止损比例")
        if stats['max_drawdown'] > 20:
            lines.append("- 最大回撤过大，建议增加风险控制")
        if stats['avg_holding_days'] < 3:
            lines.append("- 持仓时间过短，可能存在过度交易")
        
        report = '\n'.join(lines)
        
        # 保存报告
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"回测报告已保存: {output_path}")
        
        return report


def run_backtest_for_stock(code: str, start_date: str = None, end_date: str = None, 
                          output_dir: str = './backtest') -> str:
    """
    对单只股票执行回测
    
    Args:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        output_dir: 输出目录
    """
    # 默认日期
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print(f"开始回测: {code}")
    print(f"回测区间: {start_date} 至 {end_date}")
    
    # 创建回测引擎
    engine = BacktestEngine()
    
    # 加载历史信号
    signals = engine.load_historical_signals(code, start_date, end_date)
    print(f"加载信号: {len(signals)} 个")
    
    if not signals:
        return "无交易信号，无法回测"
    
    # 执行回测
    results = engine.run_backtest(signals)
    print(f"完成交易: {len(results)} 笔")
    
    if not results:
        return "回测失败，无交易结果"
    
    # 生成报告
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    report_path = Path(output_dir) / f"backtest_{code}_{start_date}_{end_date}.md"
    
    return engine.generate_report(str(report_path))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票策略回测')
    parser.add_argument('--code', type=str, required=True, help='股票代码')
    parser.add_argument('--start', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default='./backtest', help='输出目录')
    
    args = parser.parse_args()
    
    report = run_backtest_for_stock(
        code=args.code,
        start_date=args.start,
        end_date=args.end,
        output_dir=args.output
    )
    
    print("\n" + "="*60)
    print(report)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
