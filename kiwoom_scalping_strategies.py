"""
키움 스캘핑 전략 구현
- 다양한 시간프레임 (1분, 3분, 5분, 10분)
- 최적화된 기술적 지표 조합
- 백테스팅 가능한 구조
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import talib


@dataclass
class Signal:
    """매매 신호 데이터 클래스"""
    timestamp: pd.Timestamp
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    confidence: float  # 0.0 ~ 1.0
    stop_loss: float
    take_profit: float
    reason: str


@dataclass
class Trade:
    """거래 기록 데이터 클래스"""
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp]
    entry_price: float
    exit_price: Optional[float]
    position_size: int
    direction: str  # 'LONG', 'SHORT'
    pnl: Optional[float]
    pnl_pct: Optional[float]


class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        return talib.RSI(close.values, timeperiod=period)
    
    @staticmethod
    def calculate_bollinger_bands(close: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """볼린저 밴드 계산"""
        upper, middle, lower = talib.BBANDS(
            close.values, 
            timeperiod=period, 
            nbdevup=std, 
            nbdevdn=std, 
            matype=0
        )
        return pd.Series(upper, index=close.index), pd.Series(middle, index=close.index), pd.Series(lower, index=close.index)
    
    @staticmethod
    def calculate_macd(close: pd.Series, fast: int = 5, slow: int = 13, signal: int = 5) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD 계산 (스캘핑용 단기 설정)"""
        macd, signal_line, hist = talib.MACD(
            close.values, 
            fastperiod=fast, 
            slowperiod=slow, 
            signalperiod=signal
        )
        return pd.Series(macd, index=close.index), pd.Series(signal_line, index=close.index), pd.Series(hist, index=close.index)
    
    @staticmethod
    def calculate_ema(close: pd.Series, period: int) -> pd.Series:
        """지수이동평균 계산"""
        return talib.EMA(close.values, timeperiod=period)
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ATR 계산"""
        return talib.ATR(high.values, low.values, close.values, timeperiod=period)
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """VWAP 계산"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()


class ScalpingStrategy(ABC):
    """스캘핑 전략 추상 클래스"""
    
    def __init__(self, name: str, timeframe: str):
        self.name = name
        self.timeframe = timeframe
        self.indicators = TechnicalIndicators()
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """매매 신호 생성 (서브클래스에서 구현)"""
        pass
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표를 데이터프레임에 추가"""
        return df


class RSIMeanReversionStrategy(ScalpingStrategy):
    """전략 A: RSI 평균회귀 전략 (3분봉)"""
    
    def __init__(self):
        super().__init__("RSI Mean Reversion", "3min")
        self.rsi_oversold = 30
        self.rsi_exit = 50
        self.volume_multiplier = 1.5
        self.take_profit_pct = 1.5
        self.stop_loss_pct = 0.5
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요한 지표 추가"""
        df = df.copy()
        df['rsi'] = self.indicators.calculate_rsi(df['close'], 14)
        df['ema5'] = self.indicators.calculate_ema(df['close'], 5)
        df['ema20'] = self.indicators.calculate_ema(df['close'], 20)
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """매매 신호 생성"""
        df = self.add_indicators(df)
        last_row = df.iloc[-1]
        
        # 진입 조건
        if (last_row['rsi'] < self.rsi_oversold and
            last_row['volume'] > last_row['volume_ma20'] * self.volume_multiplier and
            last_row['ema5'] > last_row['ema20']):
            
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=last_row['close'],
                confidence=0.7,
                stop_loss=last_row['close'] * (1 - self.stop_loss_pct / 100),
                take_profit=last_row['close'] * (1 + self.take_profit_pct / 100),
                reason=f"RSI={last_row['rsi']:.1f} (과매도), 거래량 증가, EMA5 > EMA20"
            )
        
        # 청산 조건
        if last_row['rsi'] > self.rsi_exit:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=0.6,
                stop_loss=0,
                take_profit=0,
                reason=f"RSI={last_row['rsi']:.1f} (중립 복귀)"
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


class BollingerBandBounceStrategy(ScalpingStrategy):
    """전략 B: 볼린저밴드 반등 전략 (3분봉) - 최우선 추천"""
    
    def __init__(self):
        super().__init__("Bollinger Band Bounce", "3min")
        self.bb_period = 20
        self.bb_std = 2.0
        self.rsi_oversold = 35
        self.volume_multiplier = 2.0
        self.take_profit_pct = 2.0
        self.stop_loss_pct = 0.7
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요한 지표 추가"""
        df = df.copy()
        df['rsi'] = self.indicators.calculate_rsi(df['close'], 9)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.indicators.calculate_bollinger_bands(
            df['close'], self.bb_period, self.bb_std
        )
        macd, signal_line, hist = self.indicators.calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal_line
        df['macd_hist'] = hist
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """매매 신호 생성"""
        df = self.add_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        
        # 진입 조건
        price_touch_lower = last_row['close'] <= last_row['bb_lower']
        rsi_oversold = last_row['rsi'] < self.rsi_oversold
        macd_turning_up = last_row['macd_hist'] > prev_row['macd_hist']
        volume_surge = last_row['volume'] > last_row['volume_ma20'] * self.volume_multiplier
        
        if price_touch_lower and rsi_oversold and macd_turning_up and volume_surge:
            confidence = 0.85  # 높은 신뢰도
            
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=last_row['close'],
                confidence=confidence,
                stop_loss=last_row['close'] * (1 - self.stop_loss_pct / 100),
                take_profit=last_row['close'] * (1 + self.take_profit_pct / 100),
                reason=f"BB 하단 터치, RSI={last_row['rsi']:.1f}, MACD 상승전환, 거래량 급증"
            )
        
        # 청산 조건
        if last_row['close'] >= last_row['bb_middle']:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=0.7,
                stop_loss=0,
                take_profit=0,
                reason="BB 중심선 도달"
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


class MomentumBreakoutStrategy(ScalpingStrategy):
    """전략 C: 모멘텀 브레이크아웃 전략 (1분봉)"""
    
    def __init__(self):
        super().__init__("Momentum Breakout", "1min")
        self.lookback_period = 5
        self.rsi_min = 60
        self.rsi_max = 80
        self.volume_multiplier = 3.0
        self.take_profit_pct = 1.0
        self.stop_loss_pct = 0.3
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요한 지표 추가"""
        df = df.copy()
        df['rsi'] = self.indicators.calculate_rsi(df['close'], 7)
        df['atr'] = self.indicators.calculate_atr(df['high'], df['low'], df['close'], 14)
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['high_5min'] = df['high'].rolling(window=self.lookback_period).max()
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """매매 신호 생성"""
        df = self.add_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        
        # 진입 조건: 최근 5분간 최고가 돌파
        price_breakout = last_row['close'] > prev_row['high_5min']
        rsi_in_range = self.rsi_min < last_row['rsi'] < self.rsi_max
        volume_surge = last_row['volume'] > last_row['volume_ma20'] * self.volume_multiplier
        atr_expanding = last_row['atr'] > prev_row['atr']
        
        if price_breakout and rsi_in_range and volume_surge and atr_expanding:
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=last_row['close'],
                confidence=0.75,
                stop_loss=last_row['close'] * (1 - self.stop_loss_pct / 100),
                take_profit=last_row['close'] * (1 + self.take_profit_pct / 100),
                reason=f"5분 고가 돌파, RSI={last_row['rsi']:.1f}, 거래량 3배, ATR 확대"
            )
        
        # 청산 조건
        if last_row['rsi'] < 50:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=0.6,
                stop_loss=0,
                take_profit=0,
                reason=f"RSI={last_row['rsi']:.1f} 하락"
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


class VWAPReversionStrategy(ScalpingStrategy):
    """전략 D: VWAP 회귀 전략 (5분봉)"""
    
    def __init__(self):
        super().__init__("VWAP Reversion", "5min")
        self.vwap_deviation_pct = 1.5
        self.rsi_oversold = 40
        self.take_profit_pct = 1.0
        self.stop_loss_pct = 0.5
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """필요한 지표 추가"""
        df = df.copy()
        df['rsi'] = self.indicators.calculate_rsi(df['close'], 14)
        df['vwap'] = self.indicators.calculate_vwap(df)
        df['vwap_deviation'] = ((df['close'] - df['vwap']) / df['vwap']) * 100
        df['volume_trend'] = df['volume'].rolling(window=3).mean()
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """매매 신호 생성"""
        df = self.add_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        
        # 진입 조건: VWAP에서 1.5% 이상 괴리
        vwap_oversold = last_row['vwap_deviation'] < -self.vwap_deviation_pct
        rsi_oversold = last_row['rsi'] < self.rsi_oversold
        volume_increasing = last_row['volume_trend'] > prev_row['volume_trend']
        
        if vwap_oversold and rsi_oversold and volume_increasing:
            return Signal(
                timestamp=last_row.name,
                signal_type='BUY',
                price=last_row['close'],
                confidence=0.8,
                stop_loss=last_row['close'] * (1 - self.stop_loss_pct / 100),
                take_profit=last_row['close'] * (1 + self.take_profit_pct / 100),
                reason=f"VWAP 괴리 {last_row['vwap_deviation']:.1f}%, RSI={last_row['rsi']:.1f}, 거래량 증가"
            )
        
        # 청산 조건: VWAP 복귀
        if abs(last_row['vwap_deviation']) < 0.3:
            return Signal(
                timestamp=last_row.name,
                signal_type='SELL',
                price=last_row['close'],
                confidence=0.7,
                stop_loss=0,
                take_profit=0,
                reason="VWAP 복귀"
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


class StrategyManager:
    """전략 관리 및 실행 클래스"""
    
    def __init__(self):
        self.strategies: Dict[str, ScalpingStrategy] = {
            'strategy_a': RSIMeanReversionStrategy(),
            'strategy_b': BollingerBandBounceStrategy(),
            'strategy_c': MomentumBreakoutStrategy(),
            'strategy_d': VWAPReversionStrategy(),
        }
        self.active_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
    
    def get_strategy(self, strategy_name: str) -> Optional[ScalpingStrategy]:
        """전략 가져오기"""
        return self.strategies.get(strategy_name)
    
    def execute_strategy(self, strategy_name: str, df: pd.DataFrame) -> Signal:
        """전략 실행"""
        strategy = self.get_strategy(strategy_name)
        if strategy is None:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        return strategy.generate_signal(df)
    
    def backtest(self, strategy_name: str, df: pd.DataFrame, initial_capital: float = 10000000) -> Dict:
        """백테스팅 실행"""
        strategy = self.get_strategy(strategy_name)
        if strategy is None:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        capital = initial_capital
        position = None
        trades = []
        
        for i in range(len(df)):
            current_df = df.iloc[:i+1]
            if len(current_df) < 30:  # 최소 데이터 요구
                continue
            
            signal = strategy.generate_signal(current_df)
            current_row = current_df.iloc[-1]
            
            # 포지션 없을 때 매수 신호
            if position is None and signal.signal_type == 'BUY':
                position_size = int((capital * 0.95) / signal.price)  # 자금의 95% 사용
                position = {
                    'entry_time': signal.timestamp,
                    'entry_price': signal.price,
                    'size': position_size,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                }
            
            # 포지션 있을 때 청산 조건 체크
            elif position is not None:
                should_exit = False
                exit_reason = ""
                
                # 손절/익절 체크
                if current_row['close'] <= position['stop_loss']:
                    should_exit = True
                    exit_reason = "손절"
                elif current_row['close'] >= position['take_profit']:
                    should_exit = True
                    exit_reason = "익절"
                elif signal.signal_type == 'SELL':
                    should_exit = True
                    exit_reason = signal.reason
                
                if should_exit:
                    pnl = (current_row['close'] - position['entry_price']) * position['size']
                    pnl_pct = ((current_row['close'] - position['entry_price']) / position['entry_price']) * 100
                    
                    trade = Trade(
                        entry_time=position['entry_time'],
                        exit_time=signal.timestamp,
                        entry_price=position['entry_price'],
                        exit_price=current_row['close'],
                        position_size=position['size'],
                        direction='LONG',
                        pnl=pnl,
                        pnl_pct=pnl_pct
                    )
                    trades.append(trade)
                    capital += pnl
                    position = None
        
        # 백테스팅 결과 분석
        if not trades:
            return {
                'strategy': strategy_name,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return_pct': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
            }
        
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in trades)
        total_return_pct = ((capital - initial_capital) / initial_capital) * 100
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        return {
            'strategy': strategy_name,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) * 100 if trades else 0,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_capital': capital,
            'trades': trades,
        }


if __name__ == "__main__":
    # 샘플 데이터로 테스트
    print("=" * 80)
    print("키움 스캘핑 전략 시스템")
    print("=" * 80)
    print()
    print("구현된 전략:")
    print("  - Strategy A: RSI 평균회귀 (3분봉)")
    print("  - Strategy B: 볼린저밴드 반등 (3분봉) ⭐ 최우선 추천")
    print("  - Strategy C: 모멘텀 브레이크아웃 (1분봉)")
    print("  - Strategy D: VWAP 회귀 (5분봉)")
    print()
    print("사용법:")
    print("  manager = StrategyManager()")
    print("  signal = manager.execute_strategy('strategy_b', df)")
    print("  results = manager.backtest('strategy_b', df, initial_capital=10000000)")
