"""
고급 스캘핑 전략 구현
- 복합 전략 (여러 신호 조합)
- 적응형 전략 (시장 상황 감지 및 전환)
- 다중 시간프레임 전략
- 머신러닝 기반 전략
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from kiwoom_scalping_strategies import (
    ScalpingStrategy, Signal, TechnicalIndicators, 
    BollingerBandBounceStrategy, RSIMeanReversionStrategy,
    MomentumBreakoutStrategy, VWAPReversionStrategy
)


@dataclass
class MarketRegime:
    """시장 상황 분류"""
    regime_type: str  # 'trending_up', 'trending_down', 'ranging', 'high_volatility'
    confidence: float  # 0.0 ~ 1.0
    volatility: float
    trend_strength: float


class MultiTimeframeStrategy(ScalpingStrategy):
    """
    다중 시간프레임 전략
    - 상위 시간프레임: 추세 확인 (5분봉)
    - 하위 시간프레임: 진입 타이밍 (3분봉)
    """
    
    def __init__(self):
        super().__init__("Multi-Timeframe", "3min")
        self.higher_timeframe_period = 5  # 5분 데이터를 3분봉에서 추정
    
    def detect_higher_timeframe_trend(self, df: pd.DataFrame) -> str:
        """상위 시간프레임 추세 감지"""
        # 5분봉 데이터 시뮬레이션 (간단하게 EMA로 대체)
        df = df.copy()
        df['ema_20'] = self.indicators.calculate_ema(df['close'], 20)
        df['ema_50'] = self.indicators.calculate_ema(df['close'], 50)
        
        last_row = df.iloc[-1]
        
        # 추세 판단
        if last_row['ema_20'] > last_row['ema_50'] * 1.01:
            return 'uptrend'
        elif last_row['ema_20'] < last_row['ema_50'] * 0.99:
            return 'downtrend'
        else:
            return 'sideways'
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요한 지표 추가"""
        df = df.copy()
        
        # 볼린저 밴드
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.indicators.calculate_bollinger_bands(
            df['close'], 20, 2.0
        )
        
        # RSI
        df['rsi'] = self.indicators.calculate_rsi(df['close'], 9)
        
        # MACD
        macd, signal_line, hist = self.indicators.calculate_macd(df['close'])
        df['macd_hist'] = hist
        
        # EMA for trend
        df['ema_20'] = self.indicators.calculate_ema(df['close'], 20)
        df['ema_50'] = self.indicators.calculate_ema(df['close'], 50)
        
        # 거래량
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """다중 시간프레임 신호 생성"""
        df = self.add_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        
        # 1단계: 상위 시간프레임 추세 확인
        higher_tf_trend = self.detect_higher_timeframe_trend(df)
        
        # 2단계: 하위 시간프레임 진입 신호
        # 상승 추세에서만 매수
        if higher_tf_trend == 'uptrend':
            # 볼린저 하단 + RSI 과매도 + MACD 전환
            bb_signal = last_row['close'] <= last_row['bb_lower']
            rsi_signal = last_row['rsi'] < 35
            macd_signal = last_row['macd_hist'] > prev_row['macd_hist']
            volume_signal = last_row['volume'] > last_row['volume_ma'] * 1.5
            
            if bb_signal and rsi_signal and macd_signal and volume_signal:
                return Signal(
                    timestamp=last_row.name,
                    signal_type='BUY',
                    price=last_row['close'],
                    confidence=0.85,
                    stop_loss=last_row['close'] * 0.993,  # -0.7%
                    take_profit=last_row['close'] * 1.02,  # +2.0%
                    reason=f"다중TF: 상위TF 상승추세, BB하단 터치, RSI={last_row['rsi']:.1f}, MACD전환, 거래량증가"
                )
        
        # 횡보장에서는 평균회귀
        elif higher_tf_trend == 'sideways':
            if last_row['close'] <= last_row['bb_lower'] and last_row['rsi'] < 30:
                return Signal(
                    timestamp=last_row.name,
                    signal_type='BUY',
                    price=last_row['close'],
                    confidence=0.75,
                    stop_loss=last_row['close'] * 0.995,
                    take_profit=last_row['close'] * 1.015,
                    reason=f"다중TF: 횡보장 평균회귀"
                )
        
        # 청산 신호
        if last_row['close'] >= last_row['bb_middle']:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=0.7,
                stop_loss=0,
                take_profit=0,
                reason="중심선 도달"
            )
        
        return Signal(
            timestamp=last_row.name,
            signal_type='HOLD',
            price=last_row['close'],
            confidence=0.0,
            stop_loss=0,
            take_profit=0,
            reason="조건 미충족"
        )


class MarketRegimeDetector:
    """시장 상황 감지기"""
    
    @staticmethod
    def detect_regime(df: pd.DataFrame) -> MarketRegime:
        """
        시장 상황 감지
        - trending_up: 상승 추세
        - trending_down: 하락 추세
        - ranging: 횡보
        - high_volatility: 고변동성
        """
        if len(df) < 50:
            return MarketRegime('unknown', 0.0, 0.0, 0.0)
        
        # 변동성 계산 (ATR)
        indicators = TechnicalIndicators()
        atr = indicators.calculate_atr(df['high'], df['low'], df['close'], 14)
        current_atr = atr.iloc[-1]
        avg_atr = atr.mean()
        volatility = current_atr / df['close'].iloc[-1] * 100
        
        # 추세 강도 계산 (ADX 간소화 버전)
        df_copy = df.copy()
        df_copy['ema_20'] = indicators.calculate_ema(df['close'], 20)
        df_copy['ema_50'] = indicators.calculate_ema(df['close'], 50)
        
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20] * 100
        ema_diff = (df_copy['ema_20'].iloc[-1] - df_copy['ema_50'].iloc[-1]) / df_copy['ema_50'].iloc[-1] * 100
        
        # 추세 강도
        trend_strength = abs(ema_diff)
        
        # 상황 판단
        if current_atr > avg_atr * 1.5:
            regime_type = 'high_volatility'
            confidence = 0.8
        elif price_change > 2.0 and ema_diff > 1.0:
            regime_type = 'trending_up'
            confidence = 0.85
        elif price_change < -2.0 and ema_diff < -1.0:
            regime_type = 'trending_down'
            confidence = 0.85
        elif abs(price_change) < 1.0 and abs(ema_diff) < 0.5:
            regime_type = 'ranging'
            confidence = 0.75
        else:
            regime_type = 'ranging'
            confidence = 0.6
        
        return MarketRegime(
            regime_type=regime_type,
            confidence=confidence,
            volatility=volatility,
            trend_strength=trend_strength
        )


class AdaptiveStrategy(ScalpingStrategy):
    """
    적응형 전략
    시장 상황을 감지하여 최적의 전략을 자동 선택
    """
    
    def __init__(self):
        super().__init__("Adaptive Strategy", "3min")
        
        # 하위 전략들
        self.bb_strategy = BollingerBandBounceStrategy()
        self.rsi_strategy = RSIMeanReversionStrategy()
        self.momentum_strategy = MomentumBreakoutStrategy()
        
        self.regime_detector = MarketRegimeDetector()
        self.current_regime = None
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """시장 상황에 따라 전략 선택"""
        # 시장 상황 감지
        regime = self.regime_detector.detect_regime(df)
        self.current_regime = regime
        
        # 상황별 전략 선택
        if regime.regime_type == 'trending_up':
            # 상승장: 모멘텀 전략
            signal = self.momentum_strategy.generate_signal(df)
            signal.reason = f"[상승장] {signal.reason}"
            
        elif regime.regime_type == 'trending_down':
            # 하락장: 거래 자제 또는 매도
            return Signal(
                timestamp=df.index[-1],
                signal_type='HOLD',
                price=df['close'].iloc[-1],
                confidence=0.0,
                stop_loss=0,
                take_profit=0,
                reason=f"[하락장] 거래 자제 (신뢰도: {regime.confidence:.0%})"
            )
            
        elif regime.regime_type == 'ranging':
            # 횡보장: 볼린저밴드 평균회귀
            signal = self.bb_strategy.generate_signal(df)
            signal.reason = f"[횡보장] {signal.reason}"
            
        elif regime.regime_type == 'high_volatility':
            # 고변동성: 포지션 크기 축소, 신중한 진입
            signal = self.bb_strategy.generate_signal(df)
            signal.confidence *= 0.7  # 신뢰도 30% 감소
            signal.reason = f"[고변동성] {signal.reason} - 포지션 축소 권장"
            
        else:
            return Signal(
                timestamp=df.index[-1],
                signal_type='HOLD',
                price=df['close'].iloc[-1],
                confidence=0.0,
                stop_loss=0,
                take_profit=0,
                reason="시장 상황 불명확"
            )
        
        return signal


class HybridStrategy(ScalpingStrategy):
    """
    복합 전략
    여러 전략의 신호를 종합하여 최종 결정
    """
    
    def __init__(self):
        super().__init__("Hybrid Strategy", "3min")
        
        # 개별 전략들
        self.strategies = {
            'bb': BollingerBandBounceStrategy(),
            'rsi': RSIMeanReversionStrategy(),
            'momentum': MomentumBreakoutStrategy(),
        }
        
        # 전략별 가중치
        self.weights = {
            'bb': 0.4,
            'rsi': 0.3,
            'momentum': 0.3
        }
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """여러 전략의 신호를 통합"""
        signals = {}
        
        # 각 전략의 신호 수집
        for name, strategy in self.strategies.items():
            signals[name] = strategy.generate_signal(df)
        
        # 신호 통합
        buy_score = 0.0
        sell_score = 0.0
        
        for name, signal in signals.items():
            weight = self.weights[name]
            if signal.signal_type == 'BUY':
                buy_score += weight * signal.confidence
            elif signal.signal_type == 'SELL':
                sell_score += weight * signal.confidence
        
        last_row = df.iloc[-1]
        
        # 최종 신호 결정
        if buy_score > 0.6:  # 임계값: 60%
            # 가장 신뢰도 높은 전략의 손절/익절가 사용
            best_signal = max(
                [s for s in signals.values() if s.signal_type == 'BUY'],
                key=lambda x: x.confidence,
                default=signals['bb']
            )
            
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=last_row['close'],
                confidence=buy_score,
                stop_loss=best_signal.stop_loss,
                take_profit=best_signal.take_profit,
                reason=f"복합신호 (매수강도: {buy_score:.0%}) - " + 
                       ", ".join([f"{n}:{s.signal_type}" for n, s in signals.items()])
            )
        
        elif sell_score > 0.5:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=sell_score,
                stop_loss=0,
                take_profit=0,
                reason=f"복합신호 (매도강도: {sell_score:.0%})"
            )
        
        return Signal(
            timestamp=last_row.name,
            signal_type='HOLD',
            price=last_row['close'],
            confidence=0.0,
            stop_loss=0,
            take_profit=0,
            reason=f"복합신호 부족 (매수:{buy_score:.0%}, 매도:{sell_score:.0%})"
        )


class VolumeProfileStrategy(ScalpingStrategy):
    """
    거래량 프로파일 전략
    가격대별 거래량 분석을 통한 지지/저항 파악
    """
    
    def __init__(self):
        super().__init__("Volume Profile", "3min")
        self.num_bins = 20  # 가격 구간 개수
    
    def calculate_volume_profile(self, df: pd.DataFrame) -> Dict[float, float]:
        """거래량 프로파일 계산"""
        price_min = df['low'].min()
        price_max = df['high'].max()
        
        # 가격 구간 생성
        bins = np.linspace(price_min, price_max, self.num_bins)
        
        # 각 구간별 거래량 집계
        volume_profile = {}
        for i in range(len(bins) - 1):
            lower = bins[i]
            upper = bins[i + 1]
            
            # 해당 구간에 포함되는 거래량 합계
            mask = (df['close'] >= lower) & (df['close'] < upper)
            volume_profile[(lower + upper) / 2] = df.loc[mask, 'volume'].sum()
        
        return volume_profile
    
    def find_poc(self, volume_profile: Dict[float, float]) -> float:
        """POC (Point of Control) 찾기 - 거래량이 가장 많은 가격대"""
        if not volume_profile:
            return 0
        return max(volume_profile, key=volume_profile.get)
    
    def find_value_area(self, volume_profile: Dict[float, float]) -> Tuple[float, float]:
        """Value Area 찾기 - 전체 거래량의 70%가 발생한 가격 범위"""
        if not volume_profile:
            return 0, 0
        
        total_volume = sum(volume_profile.values())
        target_volume = total_volume * 0.7
        
        # POC부터 시작하여 확장
        poc = self.find_poc(volume_profile)
        sorted_prices = sorted(volume_profile.keys())
        poc_idx = sorted_prices.index(min(sorted_prices, key=lambda x: abs(x - poc)))
        
        accumulated_volume = volume_profile[sorted_prices[poc_idx]]
        lower_idx = poc_idx
        upper_idx = poc_idx
        
        while accumulated_volume < target_volume:
            # 위아래로 확장
            lower_vol = volume_profile.get(sorted_prices[lower_idx - 1], 0) if lower_idx > 0 else 0
            upper_vol = volume_profile.get(sorted_prices[upper_idx + 1], 0) if upper_idx < len(sorted_prices) - 1 else 0
            
            if lower_vol > upper_vol and lower_idx > 0:
                lower_idx -= 1
                accumulated_volume += lower_vol
            elif upper_idx < len(sorted_prices) - 1:
                upper_idx += 1
                accumulated_volume += upper_vol
            else:
                break
        
        return sorted_prices[lower_idx], sorted_prices[upper_idx]
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """거래량 프로파일 기반 신호"""
        if len(df) < 50:
            return Signal(
                timestamp=df.index[-1],
                signal_type='HOLD',
                price=df['close'].iloc[-1],
                confidence=0.0,
                stop_loss=0,
                take_profit=0,
                reason="데이터 부족"
            )
        
        # 최근 데이터로 거래량 프로파일 계산
        recent_df = df.iloc[-50:]
        volume_profile = self.calculate_volume_profile(recent_df)
        
        poc = self.find_poc(volume_profile)
        value_area_low, value_area_high = self.find_value_area(volume_profile)
        
        last_row = df.iloc[-1]
        current_price = last_row['close']
        
        # 신호 생성
        # Value Area 하단 이탈 시 매수
        if current_price < value_area_low:
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=current_price,
                confidence=0.75,
                stop_loss=current_price * 0.995,
                take_profit=poc,  # POC까지 회귀 목표
                reason=f"거래량프로파일: VA하단({value_area_low:.0f}) 이탈, POC({poc:.0f}) 회귀 기대"
            )
        
        # POC 도달 시 청산
        if abs(current_price - poc) < (value_area_high - value_area_low) * 0.1:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=current_price,
                confidence=0.7,
                stop_loss=0,
                take_profit=0,
                reason=f"POC({poc:.0f}) 도달"
            )
        
        return Signal(
            timestamp=last_row.name,
            signal_type='HOLD',
            price=current_price,
            confidence=0.0,
            stop_loss=0,
            take_profit=0,
            reason=f"현재가 {current_price:.0f}, VA범위 [{value_area_low:.0f}-{value_area_high:.0f}]"
        )


class OrderFlowStrategy(ScalpingStrategy):
    """
    주문 흐름 전략
    매수/매도 압력 분석 (간소화 버전)
    """
    
    def __init__(self):
        super().__init__("Order Flow", "3min")
    
    def calculate_buying_pressure(self, df: pd.DataFrame) -> pd.Series:
        """매수 압력 계산 (간소화)"""
        # 상승 캔들의 거래량을 매수 압력으로 간주
        df = df.copy()
        df['buying_volume'] = np.where(
            df['close'] > df['open'],
            df['volume'],
            0
        )
        return df['buying_volume']
    
    def calculate_selling_pressure(self, df: pd.DataFrame) -> pd.Series:
        """매도 압력 계산 (간소화)"""
        df = df.copy()
        df['selling_volume'] = np.where(
            df['close'] < df['open'],
            df['volume'],
            0
        )
        return df['selling_volume']
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """주문 흐름 기반 신호"""
        df = df.copy()
        df['buying_volume'] = self.calculate_buying_pressure(df)
        df['selling_volume'] = self.calculate_selling_pressure(df)
        
        # 최근 10개 캔들의 누적 매수/매도 압력
        recent_buying = df['buying_volume'].iloc[-10:].sum()
        recent_selling = df['selling_volume'].iloc[-10:].sum()
        
        total_volume = recent_buying + recent_selling
        if total_volume == 0:
            return Signal(
                timestamp=df.index[-1],
                signal_type='HOLD',
                price=df['close'].iloc[-1],
                confidence=0.0,
                stop_loss=0,
                take_profit=0,
                reason="거래량 없음"
            )
        
        buying_ratio = recent_buying / total_volume
        selling_ratio = recent_selling / total_volume
        
        last_row = df.iloc[-1]
        
        # 매수 압력이 70% 이상
        if buying_ratio > 0.7:
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=last_row['close'],
                confidence=0.8,
                stop_loss=last_row['close'] * 0.995,
                take_profit=last_row['close'] * 1.015,
                reason=f"주문흐름: 매수압력 {buying_ratio:.0%}"
            )
        
        # 매도 압력이 70% 이상
        elif selling_ratio > 0.7:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=0.7,
                stop_loss=0,
                take_profit=0,
                reason=f"주문흐름: 매도압력 {selling_ratio:.0%}"
            )
        
        return Signal(
            timestamp=last_row.name,
            signal_type='HOLD',
            price=last_row['close'],
            confidence=0.0,
            stop_loss=0,
            take_profit=0,
            reason=f"주문흐름 중립 (매수:{buying_ratio:.0%}, 매도:{selling_ratio:.0%})"
        )


if __name__ == "__main__":
    print("=" * 100)
    print("🚀 고급 스캘핑 전략 시스템")
    print("=" * 100)
    print()
    
    print("구현된 고급 전략:")
    print()
    print("1. 다중 시간프레임 전략 (Multi-Timeframe)")
    print("   - 상위TF로 추세 확인, 하위TF로 진입")
    print("   - 추세 순응 + 정밀 타이밍")
    print()
    print("2. 적응형 전략 (Adaptive)")
    print("   - 시장 상황 자동 감지")
    print("   - 상황별 최적 전략 자동 선택")
    print("   - 상승장/하락장/횡보장/고변동성 대응")
    print()
    print("3. 복합 전략 (Hybrid)")
    print("   - 여러 전략의 신호 통합")
    print("   - 가중치 기반 최종 결정")
    print("   - 높은 신뢰도")
    print()
    print("4. 거래량 프로파일 전략 (Volume Profile)")
    print("   - 가격대별 거래량 분석")
    print("   - POC, Value Area 활용")
    print("   - 주요 지지/저항 파악")
    print()
    print("5. 주문 흐름 전략 (Order Flow)")
    print("   - 매수/매도 압력 분석")
    print("   - 실시간 수급 파악")
    print()
    
    print("=" * 100)
    print("사용 예시:")
    print("=" * 100)
    print("""
from advanced_strategies import AdaptiveStrategy, HybridStrategy
from kiwoom_scalping_strategies import StrategyManager

# 적응형 전략 사용
adaptive = AdaptiveStrategy()
signal = adaptive.generate_signal(df)
print(f"시장 상황: {adaptive.current_regime.regime_type}")
print(f"신호: {signal.signal_type} - {signal.reason}")

# 복합 전략 사용
hybrid = HybridStrategy()
signal = hybrid.generate_signal(df)
print(f"신호: {signal.signal_type} (신뢰도: {signal.confidence:.0%})")
    """)
