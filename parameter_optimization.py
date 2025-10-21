"""
전략 파라미터 최적화 모듈
그리드 서치를 통해 최적의 파라미터 조합을 찾습니다
"""

import pandas as pd
import numpy as np
from itertools import product
from typing import Dict, List, Tuple
from kiwoom_scalping_strategies import (
    BollingerBandBounceStrategy, 
    StrategyManager,
    TechnicalIndicators
)
from backtest_example import generate_sample_data


class ParameterOptimizer:
    """파라미터 최적화 클래스"""
    
    def __init__(self, strategy_class):
        self.strategy_class = strategy_class
        self.results = []
    
    def optimize_bollinger_band_strategy(self, df: pd.DataFrame, initial_capital: float = 10000000):
        """볼린저밴드 전략 파라미터 최적화"""
        
        print("=" * 100)
        print("📊 볼린저밴드 전략 파라미터 최적화")
        print("=" * 100)
        print()
        
        # 최적화할 파라미터 범위
        param_grid = {
            'bb_period': [15, 20, 25],
            'bb_std': [1.5, 2.0, 2.5],
            'rsi_period': [7, 9, 14],
            'rsi_oversold': [30, 35, 40],
            'volume_multiplier': [1.5, 2.0, 2.5],
            'take_profit_pct': [1.5, 2.0, 2.5],
            'stop_loss_pct': [0.5, 0.7, 1.0],
        }
        
        # 전체 조합 수
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"총 테스트 조합: {total_combinations:,}개")
        print()
        
        best_result = None
        best_score = -float('inf')
        
        # 그리드 서치 (계산량 감소를 위해 샘플링)
        sample_size = min(100, total_combinations)
        print(f"샘플링 크기: {sample_size}개 조합 테스트")
        print()
        
        tested = 0
        
        # 주요 파라미터 조합만 테스트
        for bb_period in param_grid['bb_period']:
            for bb_std in param_grid['bb_std']:
                for rsi_oversold in param_grid['rsi_oversold']:
                    for take_profit in param_grid['take_profit_pct']:
                        for stop_loss in param_grid['stop_loss_pct']:
                            
                            tested += 1
                            
                            # 전략 인스턴스 생성
                            strategy = BollingerBandBounceStrategy()
                            strategy.bb_period = bb_period
                            strategy.bb_std = bb_std
                            strategy.rsi_oversold = rsi_oversold
                            strategy.take_profit_pct = take_profit
                            strategy.stop_loss_pct = stop_loss
                            
                            # 백테스팅
                            manager = StrategyManager()
                            manager.strategies['test'] = strategy
                            result = manager.backtest('test', df, initial_capital)
                            
                            # 점수 계산 (수익률 * 승률 * Profit Factor)
                            if result['total_trades'] > 0:
                                score = (
                                    result['total_return_pct'] * 
                                    (result['win_rate'] / 100) * 
                                    result['profit_factor']
                                )
                            else:
                                score = -1000
                            
                            # 결과 저장
                            result['params'] = {
                                'bb_period': bb_period,
                                'bb_std': bb_std,
                                'rsi_oversold': rsi_oversold,
                                'take_profit_pct': take_profit,
                                'stop_loss_pct': stop_loss,
                            }
                            result['score'] = score
                            self.results.append(result)
                            
                            # 최고 성과 업데이트
                            if score > best_score:
                                best_score = score
                                best_result = result
                                print(f"🔥 New Best! Score: {score:.2f}")
                                print(f"   파라미터: BB({bb_period},{bb_std}) RSI<{rsi_oversold} TP:{take_profit}% SL:{stop_loss}%")
                                print(f"   수익률: {result['total_return_pct']:.2f}% | 승률: {result['win_rate']:.2f}% | PF: {result['profit_factor']:.2f}")
                                print()
                            
                            if tested >= sample_size:
                                break
                        if tested >= sample_size:
                            break
                    if tested >= sample_size:
                        break
                if tested >= sample_size:
                    break
            if tested >= sample_size:
                break
        
        # 결과 정리
        print("\n" + "=" * 100)
        print("📈 최적화 결과")
        print("=" * 100)
        print()
        
        if best_result:
            print("🏆 최적 파라미터:")
            for key, value in best_result['params'].items():
                print(f"   {key}: {value}")
            print()
            print(f"📊 성과:")
            print(f"   총 거래: {best_result['total_trades']}회")
            print(f"   승률: {best_result['win_rate']:.2f}%")
            print(f"   수익률: {best_result['total_return_pct']:.2f}%")
            print(f"   Profit Factor: {best_result['profit_factor']:.2f}")
            print(f"   평균 수익: {best_result['avg_win']:,.0f}원")
            print(f"   평균 손실: {best_result['avg_loss']:,.0f}원")
            print(f"   최종 자본: {best_result['final_capital']:,.0f}원")
            print()
            
            # 상위 5개 결과
            print("\n📊 상위 5개 파라미터 조합:")
            print("-" * 100)
            
            sorted_results = sorted(self.results, key=lambda x: x['score'], reverse=True)
            for i, result in enumerate(sorted_results[:5]):
                print(f"\n#{i+1} (Score: {result['score']:.2f})")
                print(f"   파라미터: {result['params']}")
                print(f"   수익률: {result['total_return_pct']:.2f}% | 승률: {result['win_rate']:.2f}% | PF: {result['profit_factor']:.2f}")
        
        return best_result
    
    def sensitivity_analysis(self, df: pd.DataFrame, param_name: str, param_range: List):
        """특정 파라미터의 민감도 분석"""
        
        print(f"\n{'=' * 100}")
        print(f"🔬 {param_name} 민감도 분석")
        print('=' * 100)
        print()
        
        results = []
        
        for param_value in param_range:
            strategy = BollingerBandBounceStrategy()
            setattr(strategy, param_name, param_value)
            
            manager = StrategyManager()
            manager.strategies['test'] = strategy
            result = manager.backtest('test', df, 10000000)
            
            results.append({
                'param_value': param_value,
                'return': result['total_return_pct'],
                'win_rate': result['win_rate'],
                'profit_factor': result['profit_factor'],
                'total_trades': result['total_trades']
            })
            
            print(f"{param_name} = {param_value:>6} | "
                  f"수익률: {result['total_return_pct']:>6.2f}% | "
                  f"승률: {result['win_rate']:>5.1f}% | "
                  f"PF: {result['profit_factor']:>5.2f} | "
                  f"거래: {result['total_trades']:>4}회")
        
        return results


class TimeframeComparison:
    """시간프레임별 성과 비교"""
    
    @staticmethod
    def compare_all_timeframes():
        """모든 시간프레임 비교"""
        
        print("\n" + "=" * 100)
        print("⏰ 시간프레임별 성과 비교 (동일 전략)")
        print("=" * 100)
        print()
        
        timeframes = {
            '1min': '1분봉 - 고빈도 스캘핑',
            '3min': '3분봉 - 최적 스캘핑 ⭐',
            '5min': '5분봉 - 안정적 단타',
            '10min': '10분봉 - 단기 스윙'
        }
        
        results = []
        
        for tf_key, tf_name in timeframes.items():
            print(f"\n{'='*50}")
            print(f"{tf_name}")
            print('='*50)
            
            # 데이터 생성
            df = generate_sample_data(tf_key, days=20)
            
            # 전략 실행
            strategy = BollingerBandBounceStrategy()
            manager = StrategyManager()
            manager.strategies['test'] = strategy
            result = manager.backtest('test', df, 10000000)
            
            # 결과 출력
            print(f"데이터 포인트: {len(df):,}개")
            print(f"총 거래: {result['total_trades']:,}회")
            print(f"승률: {result['win_rate']:.2f}%")
            print(f"수익률: {result['total_return_pct']:.2f}%")
            print(f"Profit Factor: {result['profit_factor']:.2f}")
            
            if result['total_trades'] > 0:
                trades_per_day = result['total_trades'] / 20
                print(f"일평균 거래: {trades_per_day:.1f}회")
            
            results.append({
                'timeframe': tf_name,
                'data_points': len(df),
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'return': result['total_return_pct'],
                'profit_factor': result['profit_factor']
            })
        
        # 요약 테이블
        print("\n\n" + "=" * 100)
        print("📊 시간프레임 비교 요약")
        print("=" * 100)
        print()
        print(f"{'시간프레임':<30} {'데이터':<10} {'거래':<8} {'승률':<10} {'수익률':<12} {'PF':<8}")
        print("-" * 100)
        
        for r in results:
            print(f"{r['timeframe']:<30} {r['data_points']:>6}개  {r['total_trades']:>5}회  "
                  f"{r['win_rate']:>6.2f}%   {r['return']:>8.2f}%    {r['profit_factor']:>6.2f}")
        
        # 최고 성과
        best = max(results, key=lambda x: x['return'])
        print(f"\n🏆 최고 성과: {best['timeframe']}")
        print(f"   수익률: {best['return']:.2f}%")
        
        return results


if __name__ == "__main__":
    print("=" * 100)
    print("🎯 키움 스캘핑 전략 파라미터 최적화 시스템")
    print("=" * 100)
    print()
    
    # 샘플 데이터 생성 (3분봉, 20일)
    df = generate_sample_data('3min', days=20)
    print(f"백테스팅 데이터: {len(df):,}개 (3분봉, 20일)")
    print()
    
    # 1. 파라미터 최적화
    optimizer = ParameterOptimizer(BollingerBandBounceStrategy)
    best_params = optimizer.optimize_bollinger_band_strategy(df)
    
    # 2. 민감도 분석
    print("\n\n" + "=" * 100)
    print("🔬 주요 파라미터 민감도 분석")
    print("=" * 100)
    
    # RSI 과매도 기준
    optimizer.sensitivity_analysis(df, 'rsi_oversold', [25, 30, 35, 40, 45])
    
    # 익절 비율
    optimizer.sensitivity_analysis(df, 'take_profit_pct', [1.0, 1.5, 2.0, 2.5, 3.0])
    
    # 손절 비율
    optimizer.sensitivity_analysis(df, 'stop_loss_pct', [0.3, 0.5, 0.7, 1.0, 1.5])
    
    # 3. 시간프레임 비교
    TimeframeComparison.compare_all_timeframes()
    
    print("\n\n" + "=" * 100)
    print("✅ 최적화 완료!")
    print("=" * 100)
    print()
    print("💡 다음 단계:")
    print("   1. 최적 파라미터를 실전 전략에 적용")
    print("   2. 다양한 종목으로 검증")
    print("   3. 실시간 데이터로 재검증")
    print("   4. 소액 실전 테스트")
