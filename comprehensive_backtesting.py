"""
종합 백테스팅 및 시각화 시스템
- 모든 전략 통합 테스트
- 고급 통계 분석
- 시각화 차트
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

from backtest_example import generate_sample_data
from kiwoom_scalping_strategies import StrategyManager
from advanced_strategies import (
    MultiTimeframeStrategy, AdaptiveStrategy, 
    HybridStrategy, VolumeProfileStrategy, OrderFlowStrategy
)
from statistical_analysis import PerformanceAnalyzer, MonteCarloSimulator, RiskAnalyzer


def run_comprehensive_backtest():
    """모든 전략의 종합 백테스팅"""
    
    print("=" * 120)
    print("🚀 키움 스캘핑 전략 종합 백테스팅 시스템")
    print("=" * 120)
    print()
    
    # 테스트 설정
    initial_capital = 10000000
    test_days = 30
    timeframe = '3min'
    
    print(f"📋 테스트 설정")
    print(f"  초기 자본: {initial_capital:,}원")
    print(f"  테스트 기간: {test_days}일")
    print(f"  시간프레임: {timeframe}")
    print()
    
    # 샘플 데이터 생성
    print(f"📊 샘플 데이터 생성 중...")
    df = generate_sample_data(timeframe, days=test_days)
    print(f"  생성 완료: {len(df):,}개 데이터 포인트")
    print()
    
    # 전략 목록
    strategies_config = [
        ('strategy_a', 'RSI 평균회귀 (기본)'),
        ('strategy_b', '볼린저밴드 반등 (추천) ⭐'),
        ('strategy_c', '모멘텀 브레이크아웃'),
        ('strategy_d', 'VWAP 회귀'),
    ]
    
    # 고급 전략
    advanced_strategies = {
        'multi_tf': MultiTimeframeStrategy(),
        'adaptive': AdaptiveStrategy(),
        'hybrid': HybridStrategy(),
        'volume_profile': VolumeProfileStrategy(),
        'order_flow': OrderFlowStrategy(),
    }
    
    # 전략 매니저
    manager = StrategyManager()
    
    # 결과 저장
    all_results = []
    
    print("=" * 120)
    print("🔍 전략별 백테스팅 실행")
    print("=" * 120)
    print()
    
    # 기본 전략 테스트
    for strategy_id, strategy_name in strategies_config:
        print(f"\n{'='*60}")
        print(f"전략: {strategy_name}")
        print('='*60)
        
        result = manager.backtest(strategy_id, df, initial_capital)
        result['strategy_name'] = strategy_name
        result['strategy_type'] = 'basic'
        all_results.append(result)
        
        # 간략한 결과 출력
        print(f"  총 거래: {result['total_trades']:>4}회")
        print(f"  승률:    {result['win_rate']:>6.2f}%")
        print(f"  수익률:  {result['total_return_pct']:>6.2f}%")
        print(f"  PF:      {result['profit_factor']:>6.2f}")
    
    # 고급 전략 테스트
    print(f"\n\n{'='*120}")
    print("🚀 고급 전략 백테스팅")
    print('='*120)
    
    for strategy_id, strategy_obj in advanced_strategies.items():
        print(f"\n{'='*60}")
        print(f"전략: {strategy_obj.name}")
        print('='*60)
        
        manager.strategies[strategy_id] = strategy_obj
        result = manager.backtest(strategy_id, df, initial_capital)
        result['strategy_name'] = strategy_obj.name
        result['strategy_type'] = 'advanced'
        all_results.append(result)
        
        print(f"  총 거래: {result['total_trades']:>4}회")
        print(f"  승률:    {result['win_rate']:>6.2f}%")
        print(f"  수익률:  {result['total_return_pct']:>6.2f}%")
        print(f"  PF:      {result['profit_factor']:>6.2f}")
    
    return all_results, df


def analyze_and_visualize(all_results):
    """결과 분석 및 시각화"""
    
    print(f"\n\n{'='*120}")
    print("📊 전체 전략 비교 분석")
    print('='*120)
    print()
    
    # DataFrame 변환
    comparison_df = pd.DataFrame([{
        '전략명': r['strategy_name'],
        '유형': r['strategy_type'],
        '거래수': r['total_trades'],
        '승률(%)': r['win_rate'],
        '수익률(%)': r['total_return_pct'],
        'PF': r['profit_factor'],
        '평균수익': r['avg_win'],
        '평균손실': r['avg_loss'],
    } for r in all_results])
    
    # 수익률 기준 정렬
    comparison_df = comparison_df.sort_values('수익률(%)', ascending=False)
    
    print(comparison_df.to_string(index=False))
    print()
    
    # 상세 분석 (상위 3개 전략)
    print(f"\n{'='*120}")
    print("🏆 상위 3개 전략 상세 분석")
    print('='*120)
    
    top_3_results = sorted(all_results, key=lambda x: x['total_return_pct'], reverse=True)[:3]
    
    for i, result in enumerate(top_3_results, 1):
        print(f"\n{i}위: {result['strategy_name']}")
        print("-" * 60)
        
        if result['trades']:
            analyzer = PerformanceAnalyzer(result['trades'], 10000000)
            metrics = analyzer.get_comprehensive_metrics()
            
            print(f"  📊 성과 지표:")
            print(f"    - 총 수익률: {metrics.total_return_pct:.2f}%")
            print(f"    - 연환산 수익률: {metrics.annual_return_pct:.2f}%")
            print(f"    - 승률: {metrics.win_rate:.2f}%")
            print(f"    - Profit Factor: {metrics.profit_factor:.2f}")
            print()
            print(f"  ⚠️  리스크 지표:")
            print(f"    - 샤프 비율: {metrics.sharpe_ratio:.2f}")
            print(f"    - 소르티노 비율: {metrics.sortino_ratio:.2f}")
            print(f"    - 최대 낙폭(MDD): {metrics.max_drawdown:.2f}%")
            print(f"    - Recovery Factor: {metrics.recovery_factor:.2f}")
            print()
            print(f"  🔄 연속성:")
            print(f"    - 최대 연속 승리: {metrics.max_consecutive_wins}회")
            print(f"    - 최대 연속 패배: {metrics.max_consecutive_losses}회")
            print(f"    - 평균 거래 시간: {metrics.avg_trade_duration:.1f}분")
    
    # 시각화
    create_visualizations(all_results)


def create_visualizations(all_results):
    """시각화 차트 생성"""
    
    print(f"\n\n{'='*120}")
    print("📈 시각화 차트 생성 중...")
    print('='*120)
    
    # Figure 설정
    fig = plt.figure(figsize=(20, 12))
    
    # 1. 전략별 수익률 비교 (막대 그래프)
    ax1 = plt.subplot(2, 3, 1)
    strategy_names = [r['strategy_name'][:15] for r in all_results]
    returns = [r['total_return_pct'] for r in all_results]
    colors = ['#2ecc71' if r > 0 else '#e74c3c' for r in returns]
    
    ax1.barh(strategy_names, returns, color=colors)
    ax1.set_xlabel('Return (%)', fontsize=10)
    ax1.set_title('Strategy Returns Comparison', fontsize=12, fontweight='bold')
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax1.grid(axis='x', alpha=0.3)
    
    # 2. 승률 vs Profit Factor (산점도)
    ax2 = plt.subplot(2, 3, 2)
    win_rates = [r['win_rate'] for r in all_results]
    profit_factors = [r['profit_factor'] for r in all_results]
    
    scatter = ax2.scatter(win_rates, profit_factors, s=100, alpha=0.6, c=returns, cmap='RdYlGn')
    ax2.set_xlabel('Win Rate (%)', fontsize=10)
    ax2.set_ylabel('Profit Factor', fontsize=10)
    ax2.set_title('Win Rate vs Profit Factor', fontsize=12, fontweight='bold')
    ax2.grid(alpha=0.3)
    plt.colorbar(scatter, ax=ax2, label='Return (%)')
    
    # 3. 리스크-수익 프로필 (최상위 전략)
    ax3 = plt.subplot(2, 3, 3)
    
    sharpe_ratios = []
    strategy_names_sharpe = []
    
    for r in all_results:
        if r['trades'] and len(r['trades']) > 5:
            analyzer = PerformanceAnalyzer(r['trades'], 10000000)
            metrics = analyzer.get_comprehensive_metrics()
            sharpe_ratios.append(metrics.sharpe_ratio)
            strategy_names_sharpe.append(r['strategy_name'][:15])
    
    if sharpe_ratios:
        colors_sharpe = ['#2ecc71' if s > 1.0 else '#e74c3c' for s in sharpe_ratios]
        ax3.barh(strategy_names_sharpe, sharpe_ratios, color=colors_sharpe)
        ax3.set_xlabel('Sharpe Ratio', fontsize=10)
        ax3.set_title('Risk-Adjusted Returns (Sharpe)', fontsize=12, fontweight='bold')
        ax3.axvline(x=1.0, color='orange', linestyle='--', linewidth=1, label='Target: 1.0')
        ax3.legend()
        ax3.grid(axis='x', alpha=0.3)
    
    # 4. 거래 횟수 vs 수익률
    ax4 = plt.subplot(2, 3, 4)
    trade_counts = [r['total_trades'] for r in all_results]
    
    scatter2 = ax4.scatter(trade_counts, returns, s=100, alpha=0.6, c=win_rates, cmap='viridis')
    ax4.set_xlabel('Total Trades', fontsize=10)
    ax4.set_ylabel('Return (%)', fontsize=10)
    ax4.set_title('Trade Frequency vs Return', fontsize=12, fontweight='bold')
    ax4.grid(alpha=0.3)
    plt.colorbar(scatter2, ax=ax4, label='Win Rate (%)')
    
    # 5. 최대 낙폭 비교
    ax5 = plt.subplot(2, 3, 5)
    
    mdds = []
    strategy_names_mdd = []
    
    for r in all_results:
        if r['trades'] and len(r['trades']) > 5:
            analyzer = PerformanceAnalyzer(r['trades'], 10000000)
            metrics = analyzer.get_comprehensive_metrics()
            mdds.append(metrics.max_drawdown)
            strategy_names_mdd.append(r['strategy_name'][:15])
    
    if mdds:
        colors_mdd = ['#2ecc71' if m < 10 else '#e74c3c' if m > 20 else '#f39c12' for m in mdds]
        ax5.barh(strategy_names_mdd, mdds, color=colors_mdd)
        ax5.set_xlabel('Max Drawdown (%)', fontsize=10)
        ax5.set_title('Maximum Drawdown', fontsize=12, fontweight='bold')
        ax5.axvline(x=10, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Good: <10%')
        ax5.axvline(x=20, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Warning: >20%')
        ax5.legend()
        ax5.grid(axis='x', alpha=0.3)
    
    # 6. 자산 곡선 (상위 3개 전략)
    ax6 = plt.subplot(2, 3, 6)
    
    top_3 = sorted(all_results, key=lambda x: x['total_return_pct'], reverse=True)[:3]
    
    for r in top_3:
        if r['trades']:
            analyzer = PerformanceAnalyzer(r['trades'], 10000000)
            equity = analyzer.equity_curve
            ax6.plot(range(len(equity)), equity.values, label=r['strategy_name'][:15], linewidth=2)
    
    ax6.set_xlabel('Trade Number', fontsize=10)
    ax6.set_ylabel('Equity (KRW)', fontsize=10)
    ax6.set_title('Equity Curves (Top 3 Strategies)', fontsize=12, fontweight='bold')
    ax6.legend()
    ax6.grid(alpha=0.3)
    ax6.axhline(y=10000000, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Initial Capital')
    
    plt.tight_layout()
    plt.savefig('/workspace/strategy_comparison.png', dpi=150, bbox_inches='tight')
    print("  ✅ 차트 저장 완료: strategy_comparison.png")
    
    # 개별 전략 상세 차트
    create_detailed_chart(top_3[0])
    
    print("  ✅ 모든 시각화 완료")


def create_detailed_chart(best_result):
    """최고 성과 전략의 상세 차트"""
    
    if not best_result['trades'] or len(best_result['trades']) < 5:
        return
    
    print(f"\n  📊 상세 분석 차트 생성: {best_result['strategy_name']}")
    
    analyzer = PerformanceAnalyzer(best_result['trades'], 10000000)
    
    fig = plt.figure(figsize=(20, 10))
    
    # 1. 자산 곡선
    ax1 = plt.subplot(2, 2, 1)
    equity = analyzer.equity_curve
    ax1.plot(range(len(equity)), equity.values, linewidth=2, color='#2ecc71')
    ax1.fill_between(range(len(equity)), equity.values, 10000000, alpha=0.3, color='#2ecc71')
    ax1.axhline(y=10000000, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_xlabel('Trade Number', fontsize=10)
    ax1.set_ylabel('Equity (KRW)', fontsize=10)
    ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
    ax1.grid(alpha=0.3)
    
    # 2. 낙폭 차트
    ax2 = plt.subplot(2, 2, 2)
    cummax = equity.expanding().max()
    drawdown = (equity - cummax) / cummax * 100
    ax2.fill_between(range(len(drawdown)), drawdown.values, 0, alpha=0.6, color='#e74c3c')
    ax2.set_xlabel('Trade Number', fontsize=10)
    ax2.set_ylabel('Drawdown (%)', fontsize=10)
    ax2.set_title('Drawdown Over Time', fontsize=12, fontweight='bold')
    ax2.grid(alpha=0.3)
    
    # 3. 거래별 수익 분포
    ax3 = plt.subplot(2, 2, 3)
    pnls = [t.pnl for t in best_result['trades']]
    colors_pnl = ['#2ecc71' if p > 0 else '#e74c3c' for p in pnls]
    ax3.bar(range(len(pnls)), pnls, color=colors_pnl, alpha=0.7)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax3.set_xlabel('Trade Number', fontsize=10)
    ax3.set_ylabel('P&L (KRW)', fontsize=10)
    ax3.set_title('Trade-by-Trade P&L', fontsize=12, fontweight='bold')
    ax3.grid(alpha=0.3)
    
    # 4. 수익률 분포 히스토그램
    ax4 = plt.subplot(2, 2, 4)
    pnl_pcts = [t.pnl_pct for t in best_result['trades']]
    ax4.hist(pnl_pcts, bins=30, alpha=0.7, color='#3498db', edgecolor='black')
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2)
    ax4.set_xlabel('Return (%)', fontsize=10)
    ax4.set_ylabel('Frequency', fontsize=10)
    ax4.set_title('Return Distribution', fontsize=12, fontweight='bold')
    ax4.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'/workspace/best_strategy_detail.png', dpi=150, bbox_inches='tight')
    print(f"  ✅ 상세 차트 저장: best_strategy_detail.png")


def monte_carlo_analysis(best_result):
    """몬테카를로 시뮬레이션"""
    
    if not best_result['trades'] or len(best_result['trades']) < 10:
        print("\n⚠️  거래 데이터 부족 - 몬테카를로 시뮬레이션 생략")
        return
    
    print(f"\n\n{'='*120}")
    print("🎲 몬테카를로 시뮬레이션 (최고 성과 전략)")
    print('='*120)
    
    simulator = MonteCarloSimulator(best_result['trades'], 10000000)
    simulator.print_simulation_report(num_simulations=1000)


if __name__ == "__main__":
    # 종합 백테스팅 실행
    all_results, df = run_comprehensive_backtest()
    
    # 결과 분석 및 시각화
    analyze_and_visualize(all_results)
    
    # 최고 성과 전략 상세 분석
    best_result = max(all_results, key=lambda x: x['total_return_pct'])
    
    print(f"\n\n{'='*120}")
    print("🏆 최고 성과 전략 종합 분석")
    print('='*120)
    print(f"\n전략: {best_result['strategy_name']}")
    print()
    
    if best_result['trades']:
        analyzer = PerformanceAnalyzer(best_result['trades'], 10000000)
        analyzer.print_report()
        
        # 리스크 분석
        print("\n")
        RiskAnalyzer.print_risk_report(best_result['trades'], 10000000)
        
        # 몬테카를로 시뮬레이션
        monte_carlo_analysis(best_result)
    
    print(f"\n\n{'='*120}")
    print("✅ 종합 분석 완료!")
    print('='*120)
    print()
    print("📁 생성된 파일:")
    print("  - strategy_comparison.png (전략 비교 차트)")
    print("  - best_strategy_detail.png (최고 전략 상세 차트)")
    print()
    print("💡 다음 단계:")
    print("  1. 차트 확인 및 분석")
    print("  2. 최적 전략 선택")
    print("  3. 실제 데이터로 검증")
    print("  4. 소액 실전 테스트")
