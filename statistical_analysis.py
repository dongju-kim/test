"""
통계적 분석 및 성과 측정 도구
- 샤프 비율, 소르티노 비율
- 최대 낙폭 (MDD)
- 몬테카를로 시뮬레이션
- 리스크 분석
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from kiwoom_scalping_strategies import Trade


@dataclass
class PerformanceMetrics:
    """성과 지표 종합"""
    # 기본 지표
    total_return_pct: float
    annual_return_pct: float
    total_trades: int
    win_rate: float
    
    # 수익성 지표
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_trade: float
    best_trade: float
    worst_trade: float
    
    # 리스크 지표
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    
    # 연속성 지표
    max_consecutive_wins: int
    max_consecutive_losses: int
    avg_trade_duration: float
    
    # 기타
    recovery_factor: float
    expectancy: float


class PerformanceAnalyzer:
    """성과 분석기"""
    
    def __init__(self, trades: List[Trade], initial_capital: float = 10000000):
        self.trades = trades
        self.initial_capital = initial_capital
        self.equity_curve = self._calculate_equity_curve()
    
    def _calculate_equity_curve(self) -> pd.Series:
        """자산 곡선 계산"""
        if not self.trades:
            return pd.Series([self.initial_capital])
        
        equity = [self.initial_capital]
        for trade in self.trades:
            equity.append(equity[-1] + trade.pnl)
        
        return pd.Series(equity)
    
    def calculate_returns(self) -> pd.Series:
        """수익률 시계열 계산"""
        if len(self.equity_curve) < 2:
            return pd.Series([0.0])
        
        returns = self.equity_curve.pct_change().dropna()
        return returns
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        샤프 비율 계산
        
        Sharpe Ratio = (평균 수익률 - 무위험 수익률) / 수익률 표준편차
        
        Args:
            risk_free_rate: 연간 무위험 수익률 (기본값: 3%)
        """
        returns = self.calculate_returns()
        
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        
        # 일간 무위험 수익률 (연 250 거래일 가정)
        daily_rf_rate = (1 + risk_free_rate) ** (1/250) - 1
        
        excess_returns = returns - daily_rf_rate
        sharpe = excess_returns.mean() / returns.std()
        
        # 연환산
        sharpe_annual = sharpe * np.sqrt(250)
        
        return sharpe_annual
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        소르티노 비율 계산
        
        Sortino Ratio = (평균 수익률 - 무위험 수익률) / 하방 표준편차
        
        샤프 비율과 다르게 하방 변동성만 고려
        """
        returns = self.calculate_returns()
        
        if len(returns) < 2:
            return 0.0
        
        daily_rf_rate = (1 + risk_free_rate) ** (1/250) - 1
        excess_returns = returns - daily_rf_rate
        
        # 하방 편차 (손실만 고려)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        sortino = excess_returns.mean() / downside_returns.std()
        
        # 연환산
        sortino_annual = sortino * np.sqrt(250)
        
        return sortino_annual
    
    def calculate_max_drawdown(self) -> Tuple[float, int]:
        """
        최대 낙폭 (MDD) 및 회복 기간 계산
        
        Returns:
            (MDD %, 회복에 걸린 거래 수)
        """
        if len(self.equity_curve) < 2:
            return 0.0, 0
        
        cummax = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - cummax) / cummax * 100
        
        max_dd = drawdown.min()
        
        # 회복 기간 계산
        dd_start = drawdown.idxmin()
        recovery_period = 0
        
        for i in range(dd_start, len(self.equity_curve)):
            if self.equity_curve.iloc[i] >= cummax.iloc[dd_start]:
                recovery_period = i - dd_start
                break
        else:
            # 아직 회복 못함
            recovery_period = len(self.equity_curve) - dd_start
        
        return abs(max_dd), recovery_period
    
    def calculate_calmar_ratio(self) -> float:
        """
        칼마 비율 계산
        
        Calmar Ratio = 연간 수익률 / 최대 낙폭
        
        리스크 대비 수익성 측정
        """
        max_dd, _ = self.calculate_max_drawdown()
        
        if max_dd == 0:
            return 0.0
        
        total_return = (self.equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 거래 기간 (거래 수로 대략 계산)
        num_days = len(self.trades)  # 간소화
        annual_return = (1 + total_return) ** (250 / max(num_days, 1)) - 1
        
        calmar = annual_return / (max_dd / 100)
        
        return calmar
    
    def calculate_consecutive_stats(self) -> Tuple[int, int]:
        """연속 승리/패배 횟수 계산"""
        if not self.trades:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in self.trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def calculate_expectancy(self) -> float:
        """
        기대값 계산
        
        Expectancy = (승률 × 평균 수익) - (패율 × 평균 손실)
        
        양수일 때 장기적으로 수익 기대
        """
        if not self.trades:
            return 0.0
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.trades)
        loss_rate = 1 - win_rate
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([t.pnl for t in losing_trades])) if losing_trades else 0
        
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        return expectancy
    
    def get_comprehensive_metrics(self) -> PerformanceMetrics:
        """종합 성과 지표 계산"""
        if not self.trades:
            return PerformanceMetrics(
                total_return_pct=0, annual_return_pct=0, total_trades=0, win_rate=0,
                profit_factor=0, avg_win=0, avg_loss=0, avg_trade=0, best_trade=0, worst_trade=0,
                sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0, max_drawdown=0, max_drawdown_duration=0,
                max_consecutive_wins=0, max_consecutive_losses=0, avg_trade_duration=0,
                recovery_factor=0, expectancy=0
            )
        
        # 기본 통계
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in self.trades)
        total_return_pct = (total_pnl / self.initial_capital) * 100
        
        # 연환산 수익률
        num_days = len(self.trades)
        annual_return_pct = ((1 + total_return_pct/100) ** (250/max(num_days, 1)) - 1) * 100
        
        # 수익성 지표
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        avg_trade = np.mean([t.pnl for t in self.trades])
        
        best_trade = max(t.pnl for t in self.trades)
        worst_trade = min(t.pnl for t in self.trades)
        
        # 리스크 지표
        sharpe = self.calculate_sharpe_ratio()
        sortino = self.calculate_sortino_ratio()
        calmar = self.calculate_calmar_ratio()
        max_dd, dd_duration = self.calculate_max_drawdown()
        
        # 연속성
        max_wins, max_losses = self.calculate_consecutive_stats()
        
        # 평균 거래 기간
        durations = []
        for trade in self.trades:
            if trade.exit_time and trade.entry_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 60  # 분 단위
                durations.append(duration)
        avg_duration = np.mean(durations) if durations else 0
        
        # Recovery Factor
        recovery_factor = total_return_pct / max_dd if max_dd > 0 else 0
        
        # Expectancy
        expectancy = self.calculate_expectancy()
        
        return PerformanceMetrics(
            total_return_pct=total_return_pct,
            annual_return_pct=annual_return_pct,
            total_trades=len(self.trades),
            win_rate=(len(winning_trades) / len(self.trades)) * 100,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            best_trade=best_trade,
            worst_trade=worst_trade,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_dd,
            max_drawdown_duration=dd_duration,
            max_consecutive_wins=max_wins,
            max_consecutive_losses=max_losses,
            avg_trade_duration=avg_duration,
            recovery_factor=recovery_factor,
            expectancy=expectancy
        )
    
    def print_report(self):
        """성과 리포트 출력"""
        metrics = self.get_comprehensive_metrics()
        
        print("=" * 100)
        print("📊 종합 성과 분석 리포트")
        print("=" * 100)
        print()
        
        print("💰 수익성 지표")
        print("-" * 100)
        print(f"  초기 자본:        {self.initial_capital:>15,}원")
        print(f"  최종 자본:        {self.equity_curve.iloc[-1]:>15,.0f}원")
        print(f"  총 수익:          {sum(t.pnl for t in self.trades):>15,.0f}원")
        print(f"  총 수익률:        {metrics.total_return_pct:>15.2f}%")
        print(f"  연환산 수익률:    {metrics.annual_return_pct:>15.2f}%")
        print()
        
        print("📈 거래 통계")
        print("-" * 100)
        print(f"  총 거래 횟수:     {metrics.total_trades:>15}회")
        print(f"  승리 거래:        {int(metrics.total_trades * metrics.win_rate / 100):>15}회")
        print(f"  패배 거래:        {int(metrics.total_trades * (1 - metrics.win_rate / 100)):>15}회")
        print(f"  승률:             {metrics.win_rate:>15.2f}%")
        print(f"  Profit Factor:    {metrics.profit_factor:>15.2f}")
        print()
        
        print("💵 거래당 수익/손실")
        print("-" * 100)
        print(f"  평균 거래:        {metrics.avg_trade:>15,.0f}원")
        print(f"  평균 수익:        {metrics.avg_win:>15,.0f}원")
        print(f"  평균 손실:        {metrics.avg_loss:>15,.0f}원")
        print(f"  최대 수익:        {metrics.best_trade:>15,.0f}원")
        print(f"  최대 손실:        {metrics.worst_trade:>15,.0f}원")
        print(f"  기대값:           {metrics.expectancy:>15,.0f}원")
        print()
        
        print("⚠️ 리스크 지표")
        print("-" * 100)
        print(f"  샤프 비율:        {metrics.sharpe_ratio:>15.2f}")
        print(f"  소르티노 비율:    {metrics.sortino_ratio:>15.2f}")
        print(f"  칼마 비율:        {metrics.calmar_ratio:>15.2f}")
        print(f"  최대 낙폭(MDD):   {metrics.max_drawdown:>15.2f}%")
        print(f"  MDD 회복 기간:    {metrics.max_drawdown_duration:>15}거래")
        print(f"  Recovery Factor:  {metrics.recovery_factor:>15.2f}")
        print()
        
        print("🔄 연속성 지표")
        print("-" * 100)
        print(f"  최대 연속 승리:   {metrics.max_consecutive_wins:>15}회")
        print(f"  최대 연속 패배:   {metrics.max_consecutive_losses:>15}회")
        print(f"  평균 거래 시간:   {metrics.avg_trade_duration:>15.1f}분")
        print()
        
        print("✅ 종합 평가")
        print("-" * 100)
        
        # 평가 기준
        score = 0
        comments = []
        
        if metrics.sharpe_ratio > 2.0:
            score += 2
            comments.append("✅ 샤프 비율 우수")
        elif metrics.sharpe_ratio > 1.0:
            score += 1
            comments.append("⚠️  샤프 비율 양호")
        else:
            comments.append("❌ 샤프 비율 부족")
        
        if metrics.max_drawdown < 10:
            score += 2
            comments.append("✅ 낙폭 관리 우수")
        elif metrics.max_drawdown < 20:
            score += 1
            comments.append("⚠️  낙폭 관리 양호")
        else:
            comments.append("❌ 낙폭 과다")
        
        if metrics.win_rate > 65:
            score += 2
            comments.append("✅ 승률 우수")
        elif metrics.win_rate > 55:
            score += 1
            comments.append("⚠️  승률 양호")
        else:
            comments.append("❌ 승률 부족")
        
        if metrics.profit_factor > 2.0:
            score += 2
            comments.append("✅ Profit Factor 우수")
        elif metrics.profit_factor > 1.5:
            score += 1
            comments.append("⚠️  Profit Factor 양호")
        else:
            comments.append("❌ Profit Factor 부족")
        
        for comment in comments:
            print(f"  {comment}")
        
        print()
        print(f"  종합 점수: {score}/8")
        
        if score >= 7:
            print("  평가: ⭐⭐⭐ 매우 우수한 전략")
        elif score >= 5:
            print("  평가: ⭐⭐ 우수한 전략")
        elif score >= 3:
            print("  평가: ⭐ 개선 필요")
        else:
            print("  평가: ❌ 전략 재수립 필요")
        
        print("=" * 100)


class MonteCarloSimulator:
    """몬테카를로 시뮬레이션"""
    
    def __init__(self, trades: List[Trade], initial_capital: float = 10000000):
        self.trades = trades
        self.initial_capital = initial_capital
    
    def simulate(self, num_simulations: int = 1000, num_trades: int = None) -> Dict:
        """
        몬테카를로 시뮬레이션 실행
        
        과거 거래를 무작위로 재배열하여 미래 성과 예측
        
        Args:
            num_simulations: 시뮬레이션 횟수
            num_trades: 시뮬레이션할 거래 수 (None이면 전체)
        """
        if not self.trades:
            return {
                'mean_return': 0,
                'median_return': 0,
                'best_case': 0,
                'worst_case': 0,
                'probability_of_profit': 0,
                'simulations': []
            }
        
        if num_trades is None:
            num_trades = len(self.trades)
        
        # 거래별 수익률 추출
        trade_returns = [t.pnl_pct for t in self.trades]
        
        simulations = []
        
        for _ in range(num_simulations):
            # 무작위로 거래 선택 (복원 추출)
            sampled_returns = np.random.choice(trade_returns, size=num_trades, replace=True)
            
            # 자산 곡선 계산
            capital = self.initial_capital
            for ret in sampled_returns:
                capital *= (1 + ret / 100)
            
            total_return = (capital - self.initial_capital) / self.initial_capital * 100
            simulations.append(total_return)
        
        simulations = np.array(simulations)
        
        return {
            'mean_return': np.mean(simulations),
            'median_return': np.median(simulations),
            'std_return': np.std(simulations),
            'best_case': np.percentile(simulations, 95),  # 상위 5%
            'worst_case': np.percentile(simulations, 5),   # 하위 5%
            'probability_of_profit': np.sum(simulations > 0) / len(simulations) * 100,
            'simulations': simulations
        }
    
    def print_simulation_report(self, num_simulations: int = 1000):
        """시뮬레이션 결과 리포트"""
        result = self.simulate(num_simulations)
        
        print("=" * 100)
        print(f"🎲 몬테카를로 시뮬레이션 결과 ({num_simulations:,}회)")
        print("=" * 100)
        print()
        
        print("📊 예상 수익률 분포")
        print("-" * 100)
        print(f"  평균 수익률:      {result['mean_return']:>15.2f}%")
        print(f"  중간 수익률:      {result['median_return']:>15.2f}%")
        print(f"  표준편차:         {result['std_return']:>15.2f}%")
        print(f"  최선의 경우(95%): {result['best_case']:>15.2f}%")
        print(f"  최악의 경우(5%):  {result['worst_case']:>15.2f}%")
        print(f"  수익 확률:        {result['probability_of_profit']:>15.2f}%")
        print()
        
        print("💡 해석")
        print("-" * 100)
        if result['probability_of_profit'] > 70:
            print("  ✅ 높은 수익 확률 - 전략 신뢰도 높음")
        elif result['probability_of_profit'] > 50:
            print("  ⚠️  중간 수익 확률 - 개선 여지 있음")
        else:
            print("  ❌ 낮은 수익 확률 - 전략 재검토 필요")
        
        if abs(result['worst_case']) < 20:
            print("  ✅ 최악의 경우도 감내 가능한 수준")
        else:
            print(f"  ⚠️  최악의 경우 {result['worst_case']:.1f}% 손실 가능 - 리스크 관리 필수")
        
        print("=" * 100)


class RiskAnalyzer:
    """리스크 분석기"""
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
        """
        VaR (Value at Risk) 계산
        
        주어진 신뢰수준에서 예상되는 최대 손실
        
        Args:
            returns: 수익률 시계열
            confidence_level: 신뢰수준 (기본값: 95%)
        """
        if len(returns) == 0:
            return 0.0
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return abs(var) * 100  # 백분율로 변환
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
        """
        CVaR (Conditional VaR) 계산
        
        VaR을 초과하는 손실의 평균
        
        Args:
            returns: 수익률 시계열
            confidence_level: 신뢰수준
        """
        if len(returns) == 0:
            return 0.0
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        cvar = returns[returns <= var].mean()
        return abs(cvar) * 100
    
    @staticmethod
    def print_risk_report(trades: List[Trade], initial_capital: float = 10000000):
        """리스크 분석 리포트"""
        if not trades:
            print("거래 데이터 없음")
            return
        
        analyzer = PerformanceAnalyzer(trades, initial_capital)
        returns = analyzer.calculate_returns()
        
        var_95 = RiskAnalyzer.calculate_var(returns, 0.95)
        var_99 = RiskAnalyzer.calculate_var(returns, 0.99)
        cvar_95 = RiskAnalyzer.calculate_cvar(returns, 0.95)
        
        print("=" * 100)
        print("⚠️  리스크 분석 리포트")
        print("=" * 100)
        print()
        
        print("📉 VaR (Value at Risk)")
        print("-" * 100)
        print(f"  VaR (95% 신뢰수준):  {var_95:>15.2f}%")
        print(f"  → 95% 확률로 일일 손실이 {var_95:.2f}% 이내")
        print()
        print(f"  VaR (99% 신뢰수준):  {var_99:>15.2f}%")
        print(f"  → 99% 확률로 일일 손실이 {var_99:.2f}% 이내")
        print()
        
        print("📉 CVaR (Conditional VaR)")
        print("-" * 100)
        print(f"  CVaR (95%):          {cvar_95:>15.2f}%")
        print(f"  → VaR 초과 시 평균 손실 {cvar_95:.2f}%")
        print()
        
        print("💡 권장 리스크 관리")
        print("-" * 100)
        print(f"  일일 손절 한도:     {var_95 * 1.5:>15.2f}% (VaR의 1.5배)")
        print(f"  최대 포지션 크기:   {100 / (var_95 * 2):>15.0f}% (VaR의 2배로 분산)")
        print("=" * 100)


if __name__ == "__main__":
    print("=" * 100)
    print("📊 통계적 분석 도구")
    print("=" * 100)
    print()
    
    print("구현된 분석 도구:")
    print()
    print("1. PerformanceAnalyzer - 종합 성과 분석")
    print("   - 샤프/소르티노/칼마 비율")
    print("   - 최대 낙폭 (MDD)")
    print("   - 기대값, Profit Factor")
    print("   - 연속 승/패 분석")
    print()
    print("2. MonteCarloSimulator - 몬테카를로 시뮬레이션")
    print("   - 미래 성과 예측")
    print("   - 수익 확률 계산")
    print("   - 최선/최악 시나리오")
    print()
    print("3. RiskAnalyzer - 리스크 분석")
    print("   - VaR (Value at Risk)")
    print("   - CVaR (Conditional VaR)")
    print("   - 리스크 관리 권장사항")
    print()
    print("=" * 100)
