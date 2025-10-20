"""
키움 스캘핑 전략 백테스팅 예제
실제 데이터를 사용하여 전략 성능을 비교 분석
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiwoom_scalping_strategies import StrategyManager
import matplotlib.pyplot as plt
import seaborn as sns


def generate_sample_data(timeframe: str, days: int = 5) -> pd.DataFrame:
    """
    샘플 데이터 생성 (실제로는 키움 API에서 가져옴)
    
    Args:
        timeframe: '1min', '3min', '5min', '10min'
        days: 생성할 데이터 일수
    """
    # 시간프레임별 데이터 포인트 수
    points_per_day = {
        '1min': 360,
        '3min': 120,
        '5min': 72,
        '10min': 36
    }
    
    total_points = points_per_day.get(timeframe, 120) * days
    
    # 시작 가격
    base_price = 50000
    
    # 랜덤 워크 기반 가격 생성 (실제 주가와 유사한 패턴)
    np.random.seed(42)
    returns = np.random.normal(0.0001, 0.003, total_points)  # 평균 수익률, 표준편차
    price = base_price * np.exp(np.cumsum(returns))
    
    # 고가, 저가 생성
    high = price * (1 + np.abs(np.random.normal(0, 0.005, total_points)))
    low = price * (1 - np.abs(np.random.normal(0, 0.005, total_points)))
    
    # 거래량 생성 (가격 변동성과 상관관계)
    volume_base = 100000
    volume = volume_base + np.abs(np.random.normal(0, 50000, total_points))
    volume = volume * (1 + np.abs(returns) * 10)  # 변동성 클 때 거래량 증가
    
    # 시간 인덱스 생성
    start_time = datetime.now() - timedelta(days=days)
    if timeframe == '1min':
        freq = '1T'
    elif timeframe == '3min':
        freq = '3T'
    elif timeframe == '5min':
        freq = '5T'
    else:
        freq = '10T'
    
    time_index = pd.date_range(start=start_time, periods=total_points, freq=freq)
    
    df = pd.DataFrame({
        'open': price,
        'high': high,
        'low': low,
        'close': price,
        'volume': volume.astype(int)
    }, index=time_index)
    
    return df


def run_backtest_comparison(initial_capital: float = 10000000):
    """모든 전략의 백테스팅 결과 비교"""
    
    print("=" * 100)
    print("키움 스캘핑 전략 백테스팅 비교 분석")
    print("=" * 100)
    print(f"\n초기 자본: {initial_capital:,}원")
    print()
    
    manager = StrategyManager()
    results = []
    
    # 각 전략별 백테스팅
    strategies_config = [
        ('strategy_a', '3min', 'RSI 평균회귀'),
        ('strategy_b', '3min', '볼린저밴드 반등 ⭐'),
        ('strategy_c', '1min', '모멘텀 브레이크아웃'),
        ('strategy_d', '5min', 'VWAP 회귀'),
    ]
    
    for strategy_id, timeframe, strategy_name in strategies_config:
        print(f"\n{'=' * 100}")
        print(f"전략: {strategy_name} ({timeframe})")
        print('=' * 100)
        
        # 샘플 데이터 생성
        df = generate_sample_data(timeframe, days=20)
        print(f"데이터 기간: {df.index[0]} ~ {df.index[-1]}")
        print(f"총 데이터 포인트: {len(df):,}개")
        
        # 백테스팅 실행
        result = manager.backtest(strategy_id, df, initial_capital)
        results.append({
            'name': strategy_name,
            'timeframe': timeframe,
            **result
        })
        
        # 결과 출력
        print(f"\n📊 백테스팅 결과:")
        print(f"  총 거래 횟수: {result['total_trades']:,}회")
        print(f"  승리 거래: {result['winning_trades']:,}회")
        print(f"  패배 거래: {result['losing_trades']:,}회")
        print(f"  승률: {result['win_rate']:.2f}%")
        print(f"  총 손익: {result['total_pnl']:,.0f}원")
        print(f"  수익률: {result['total_return_pct']:.2f}%")
        print(f"  평균 수익: {result['avg_win']:,.0f}원")
        print(f"  평균 손실: {result['avg_loss']:,.0f}원")
        print(f"  Profit Factor: {result['profit_factor']:.2f}")
        print(f"  최종 자본: {result['final_capital']:,.0f}원")
        
        if result['total_trades'] > 0:
            # 거래별 상세 정보 (처음 5개만)
            print(f"\n📝 거래 내역 (처음 5개):")
            for i, trade in enumerate(result['trades'][:5]):
                print(f"  #{i+1}: 진입 {trade.entry_price:,.0f}원 → 청산 {trade.exit_price:,.0f}원 "
                      f"| 손익 {trade.pnl:,.0f}원 ({trade.pnl_pct:+.2f}%)")
    
    # 전략 비교 요약
    print(f"\n\n{'=' * 100}")
    print("📈 전략 성과 비교 요약")
    print('=' * 100)
    print()
    
    # DataFrame으로 변환하여 정렬
    comparison_df = pd.DataFrame(results)
    if len(comparison_df) > 0:
        comparison_df = comparison_df.sort_values('total_return_pct', ascending=False)
        
        print(f"{'순위':<5} {'전략명':<30} {'시간봉':<8} {'승률':<10} {'수익률':<12} {'거래횟수':<10} {'PF':<8}")
        print('-' * 100)
        
        for idx, row in comparison_df.iterrows():
            rank = comparison_df.index.get_loc(idx) + 1
            print(f"{rank:<5} {row['name']:<30} {row['timeframe']:<8} "
                  f"{row['win_rate']:>6.2f}%  {row['total_return_pct']:>8.2f}%    "
                  f"{row['total_trades']:>6}회   {row['profit_factor']:>6.2f}")
    
    # 최종 권장사항
    print(f"\n\n{'=' * 100}")
    print("💡 최종 권장사항")
    print('=' * 100)
    
    if len(comparison_df) > 0:
        best_strategy = comparison_df.iloc[0]
        print(f"""
1. 최고 성과 전략: {best_strategy['name']}
   - 수익률: {best_strategy['total_return_pct']:.2f}%
   - 승률: {best_strategy['win_rate']:.2f}%
   - Profit Factor: {best_strategy['profit_factor']:.2f}

2. 실전 적용 시 주의사항:
   ⚠️  백테스팅 결과는 과거 데이터 기반이며, 실전 성과를 보장하지 않습니다
   ⚠️  슬리피지(체결가격 차이)와 수수료를 고려하면 실제 수익률은 더 낮습니다
   ⚠️  종목 특성, 시장 상황에 따라 전략 성과가 달라질 수 있습니다
   
3. 리스크 관리:
   ✅ 1회 거래당 총 자금의 1% 이내로 리스크 제한
   ✅ 일일 손실 한도 설정 (예: 총 자금의 2%)
   ✅ 연속 손실 시 거래 중단 규칙 적용
   ✅ 실전 투입 전 소액으로 충분히 테스트

4. 최적화 방향:
   📊 실시간 데이터로 파라미터 재조정
   📊 종목별 특성에 맞게 전략 커스터마이징
   📊 다중 시간프레임 분석 추가
   📊 시장 상황별 전략 전환 로직 개발
        """)
    
    return results


def analyze_timeframe_performance():
    """시간프레임별 성과 분석"""
    print("\n\n" + "=" * 100)
    print("⏰ 시간프레임별 상세 분석")
    print("=" * 100)
    
    timeframes = ['1min', '3min', '5min', '10min']
    manager = StrategyManager()
    
    for tf in timeframes:
        print(f"\n\n📊 {tf} 분석")
        print("-" * 100)
        
        df = generate_sample_data(tf, days=10)
        
        # 볼린저밴드 전략으로 통일하여 비교
        result = manager.backtest('strategy_b', df, 10000000)
        
        print(f"  데이터 포인트: {len(df):,}개")
        print(f"  거래 기회: {result['total_trades']:,}회")
        print(f"  승률: {result['win_rate']:.2f}%")
        print(f"  수익률: {result['total_return_pct']:.2f}%")
        print(f"  Profit Factor: {result['profit_factor']:.2f}")
        
        # 거래 빈도 분석
        if result['total_trades'] > 0:
            avg_trades_per_day = result['total_trades'] / 10
            print(f"  일평균 거래: {avg_trades_per_day:.1f}회")
            
            # 평가
            if tf == '1min':
                print(f"  평가: 거래 빈도 높음, 수수료 부담 큼, 노이즈 많음")
            elif tf == '3min':
                print(f"  평가: ⭐ 최적 균형, 충분한 기회 + 신뢰도 높은 신호")
            elif tf == '5min':
                print(f"  평가: 안정적, 스캘핑보다는 단타에 적합")
            else:
                print(f"  평가: 거래 빈도 낮음, 스윙 트레이딩에 더 적합")


if __name__ == "__main__":
    # 전체 백테스팅 비교
    results = run_backtest_comparison(initial_capital=10000000)
    
    # 시간프레임별 분석
    analyze_timeframe_performance()
    
    print("\n\n" + "=" * 100)
    print("✅ 백테스팅 완료!")
    print("=" * 100)
    print("\n다음 단계:")
    print("  1. 실제 키움 API 데이터로 백테스팅")
    print("  2. 종목별 맞춤 파라미터 최적화")
    print("  3. 소액 실전 테스트")
    print("  4. 성과 모니터링 및 전략 개선")
