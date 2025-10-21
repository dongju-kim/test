"""
자동매매 실행 시스템
실제 거래를 자동으로 실행하는 핵심 엔진
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

from kiwoom_scalping_strategies import (
    BollingerBandBounceStrategy,
    VWAPReversionStrategy,
    Signal
)


@dataclass
class Position:
    """보유 포지션"""
    code: str
    name: str
    entry_time: datetime
    entry_price: float
    quantity: int
    stop_loss: float
    take_profit1: float
    take_profit2: float
    strategy: str
    

@dataclass
class Order:
    """주문 정보"""
    code: str
    name: str
    order_type: str  # 'BUY', 'SELL'
    price: float
    quantity: int
    timestamp: datetime
    reason: str


class AutoTradingExecutor:
    """자동매매 실행 엔진"""
    
    def __init__(self, initial_capital: float = 10000000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.daily_pnl = 0.0
        self.daily_trades = 0
        
        # 리스크 관리
        self.max_position_risk = 0.01  # 1%
        self.daily_loss_limit = 0.02   # 2%
        self.max_positions = 3
        
        # 전략
        self.strategies = {
            'bollinger': BollingerBandBounceStrategy(),
            'vwap': VWAPReversionStrategy(),
        }
        
        # 거래 가능 시간
        self.trading_start = "09:30"
        self.trading_end = "15:15"
        
        print("=" * 80)
        print("🤖 자동매매 시스템 초기화")
        print("=" * 80)
        print(f"  초기 자금: {self.initial_capital:,}원")
        print(f"  일일 손실 한도: {self.initial_capital * self.daily_loss_limit:,}원 ({self.daily_loss_limit*100}%)")
        print(f"  최대 포지션: {self.max_positions}개")
        print("=" * 80)
        print()
    
    def is_trading_time(self) -> bool:
        """거래 가능 시간 확인"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 장 시작 전 또는 장 마감 후
        if current_time < self.trading_start or current_time > self.trading_end:
            return False
        
        # 주말
        if now.weekday() >= 5:
            return False
        
        return True
    
    def can_trade(self) -> bool:
        """거래 가능 여부 확인"""
        # 시간 체크
        if not self.is_trading_time():
            return False
        
        # 일일 손실 한도 체크
        if self.daily_pnl <= -self.initial_capital * self.daily_loss_limit:
            print(f"⛔ 일일 손실 한도 도달: {self.daily_pnl:,}원")
            return False
        
        # 최대 포지션 수 체크
        if len(self.positions) >= self.max_positions:
            return False
        
        return True
    
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> int:
        """
        포지션 크기 계산 (리스크 기반)
        
        허용 손실 = 총 자금의 1%
        수량 = 허용 손실 / (진입가 - 손절가)
        """
        risk_amount = self.initial_capital * self.max_position_risk
        loss_per_share = abs(entry_price - stop_loss)
        
        if loss_per_share == 0:
            return 0
        
        quantity = int(risk_amount / loss_per_share)
        
        # 최대 투자금 제한 (총 자금의 30%)
        max_investment = self.current_capital * 0.3
        max_quantity = int(max_investment / entry_price)
        
        return min(quantity, max_quantity)
    
    def check_buy_signal(self, code: str, name: str, df: pd.DataFrame, strategy_name: str) -> Optional[Signal]:
        """
        매수 신호 확인
        
        Args:
            code: 종목코드
            name: 종목명
            df: 가격 데이터
            strategy_name: 전략명
        """
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return None
        
        # 신호 생성
        signal = strategy.generate_signal(df)
        
        # 매수 신호이고 신뢰도 70% 이상
        if signal.signal_type == 'BUY' and signal.confidence >= 0.7:
            return signal
        
        return None
    
    def execute_buy(self, code: str, name: str, signal: Signal, strategy_name: str) -> bool:
        """
        매수 실행
        
        Args:
            code: 종목코드
            name: 종목명
            signal: 매수 신호
            strategy_name: 전략명
        """
        # 거래 가능 여부 확인
        if not self.can_trade():
            return False
        
        # 이미 보유 중
        if code in self.positions:
            return False
        
        # 포지션 크기 계산
        quantity = self.calculate_position_size(signal.price, signal.stop_loss)
        
        if quantity == 0:
            print(f"⚠️  {name}: 포지션 크기 0 (진입 불가)")
            return False
        
        # 매수 실행
        entry_price = signal.price
        investment = entry_price * quantity
        
        # 자금 확인
        if investment > self.current_capital:
            print(f"⚠️  {name}: 자금 부족 ({investment:,}원 필요, {self.current_capital:,}원 보유)")
            return False
        
        # 포지션 생성
        position = Position(
            code=code,
            name=name,
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=signal.stop_loss,
            take_profit1=entry_price * 1.015,  # +1.5%
            take_profit2=signal.take_profit,   # +2.0%
            strategy=strategy_name
        )
        
        self.positions[code] = position
        self.current_capital -= investment
        self.daily_trades += 1
        
        # 주문 기록
        order = Order(
            code=code,
            name=name,
            order_type='BUY',
            price=entry_price,
            quantity=quantity,
            timestamp=datetime.now(),
            reason=signal.reason
        )
        self.orders.append(order)
        
        # 출력
        print(f"\n{'='*80}")
        print(f"✅ 매수 체결: {name} ({code})")
        print(f"{'='*80}")
        print(f"  진입가:     {entry_price:>12,}원")
        print(f"  수량:       {quantity:>12,}주")
        print(f"  투자금:     {investment:>12,}원")
        print(f"  손절가:     {signal.stop_loss:>12,.0f}원 ({(signal.stop_loss/entry_price-1)*100:+.2f}%)")
        print(f"  익절가1:    {position.take_profit1:>12,.0f}원 (+1.5%)")
        print(f"  익절가2:    {position.take_profit2:>12,.0f}원 (+2.0%)")
        print(f"  전략:       {strategy_name}")
        print(f"  이유:       {signal.reason}")
        print(f"  잔여 자금:  {self.current_capital:>12,}원")
        print(f"{'='*80}\n")
        
        return True
    
    def check_sell_conditions(self, code: str, current_price: float, current_rsi: float = None) -> Tuple[bool, str, int]:
        """
        매도 조건 확인
        
        Returns:
            (매도여부, 이유, 수량)
        """
        position = self.positions.get(code)
        if not position:
            return False, "", 0
        
        # 보유 시간
        holding_time = (datetime.now() - position.entry_time).total_seconds() / 60
        
        # 조건 1: 손절가 도달 (최우선)
        if current_price <= position.stop_loss:
            return True, "손절", position.quantity
        
        # 조건 2: 익절가1 도달 (50% 매도)
        if current_price >= position.take_profit1 and position.quantity > 1:
            return True, "익절1단계", position.quantity // 2
        
        # 조건 3: 익절가2 도달 (전량 매도)
        if current_price >= position.take_profit2:
            return True, "익절2단계", position.quantity
        
        # 조건 4: RSI 과열
        if current_rsi and current_rsi >= 65:
            return True, "RSI과열", position.quantity
        
        # 조건 5: 시간 경과 (30분)
        if holding_time >= 30:
            return True, "시간경과", position.quantity
        
        # 조건 6: 장 마감 임박
        if datetime.now().strftime("%H:%M") >= "15:15":
            return True, "장마감", position.quantity
        
        return False, "", 0
    
    def execute_sell(self, code: str, price: float, quantity: int, reason: str) -> bool:
        """
        매도 실행
        
        Args:
            code: 종목코드
            price: 매도가
            quantity: 수량
            reason: 매도 이유
        """
        position = self.positions.get(code)
        if not position:
            return False
        
        # 매도 금액
        proceeds = price * quantity
        
        # 손익 계산
        cost = position.entry_price * quantity
        pnl = proceeds - cost
        pnl_pct = (price / position.entry_price - 1) * 100
        
        # 자금 업데이트
        self.current_capital += proceeds
        self.daily_pnl += pnl
        
        # 포지션 업데이트
        position.quantity -= quantity
        if position.quantity <= 0:
            del self.positions[code]
        
        # 주문 기록
        order = Order(
            code=code,
            name=position.name,
            order_type='SELL',
            price=price,
            quantity=quantity,
            timestamp=datetime.now(),
            reason=reason
        )
        self.orders.append(order)
        
        # 보유 시간
        holding_time = (datetime.now() - position.entry_time).total_seconds() / 60
        
        # 출력
        emoji = "💰" if pnl > 0 else "💸"
        print(f"\n{'='*80}")
        print(f"{emoji} 매도 체결: {position.name} ({code})")
        print(f"{'='*80}")
        print(f"  매도가:     {price:>12,}원")
        print(f"  수량:       {quantity:>12,}주")
        print(f"  매도금:     {proceeds:>12,}원")
        print(f"  손익:       {pnl:>12,}원 ({pnl_pct:+.2f}%)")
        print(f"  이유:       {reason}")
        print(f"  보유시간:   {holding_time:>12.1f}분")
        print(f"  잔여 자금:  {self.current_capital:>12,}원")
        print(f"  일일 손익:  {self.daily_pnl:>12,}원")
        print(f"{'='*80}\n")
        
        return True
    
    def run_trading_cycle(self, market_data: Dict[str, pd.DataFrame], target_stocks: Dict[str, List[str]]):
        """
        1회 거래 사이클 실행
        
        Args:
            market_data: {종목코드: 가격 데이터}
            target_stocks: {전략명: [종목코드 리스트]}
        """
        if not self.is_trading_time():
            return
        
        # 1. 기존 포지션 청산 확인
        for code in list(self.positions.keys()):
            position = self.positions[code]
            df = market_data.get(code)
            
            if df is None or len(df) == 0:
                continue
            
            current_price = df['close'].iloc[-1]
            current_rsi = None
            
            # RSI 계산 (간단히)
            if len(df) >= 9:
                from kiwoom_scalping_strategies import TechnicalIndicators
                indicators = TechnicalIndicators()
                rsi_series = indicators.calculate_rsi(df['close'], 9)
                current_rsi = rsi_series.iloc[-1]
            
            # 매도 조건 확인
            should_sell, reason, quantity = self.check_sell_conditions(code, current_price, current_rsi)
            
            if should_sell:
                self.execute_sell(code, current_price, quantity, reason)
        
        # 2. 신규 진입 확인 (거래 가능한 경우에만)
        if not self.can_trade():
            return
        
        for strategy_name, stock_codes in target_stocks.items():
            for code in stock_codes:
                # 이미 보유 중이면 스킵
                if code in self.positions:
                    continue
                
                # 데이터 확인
                df = market_data.get(code)
                if df is None or len(df) < 30:
                    continue
                
                # 매수 신호 확인
                signal = self.check_buy_signal(code, f"종목{code}", df, strategy_name)
                
                if signal:
                    self.execute_buy(code, f"종목{code}", signal, strategy_name)
                    
                    # 한 사이클에 1개만 진입
                    break
            
            # 포지션 가득 차면 중단
            if len(self.positions) >= self.max_positions:
                break
    
    def print_daily_summary(self):
        """일일 성과 요약"""
        print("\n" + "=" * 80)
        print("📊 일일 거래 성과 요약")
        print("=" * 80)
        print(f"  초기 자금:   {self.initial_capital:>15,}원")
        print(f"  현재 자금:   {self.current_capital:>15,}원")
        print(f"  일일 손익:   {self.daily_pnl:>15,}원 ({self.daily_pnl/self.initial_capital*100:+.2f}%)")
        print(f"  총 거래:     {self.daily_trades:>15}회")
        print(f"  보유 포지션: {len(self.positions):>15}개")
        print("=" * 80)
        
        if self.positions:
            print("\n보유 중인 포지션:")
            print("-" * 80)
            for code, pos in self.positions.items():
                holding_time = (datetime.now() - pos.entry_time).total_seconds() / 60
                print(f"  {pos.name} | 진입: {pos.entry_price:,}원 | 수량: {pos.quantity}주 | 보유: {holding_time:.0f}분")
        
        print()


def simulate_auto_trading():
    """자동매매 시뮬레이션"""
    
    print("\n" + "=" * 100)
    print("🚀 자동매매 시스템 시뮬레이션")
    print("=" * 100)
    print()
    
    # 시스템 초기화
    executor = AutoTradingExecutor(initial_capital=10000000)
    
    # 대상 종목
    target_stocks = {
        'bollinger': ['005930', '000660', '035420'],  # 삼성전자, SK하이닉스, NAVER
        'vwap': ['005930', '000660'],
    }
    
    print("대상 종목:")
    print("  볼린저밴드: 005930(삼성전자), 000660(SK하이닉스), 035420(NAVER)")
    print("  VWAP: 005930(삼성전자), 000660(SK하이닉스)")
    print()
    
    # 샘플 데이터 생성 (실제로는 API에서 실시간 수신)
    from backtest_example import generate_sample_data
    
    print("=" * 100)
    print("거래 시작 (시뮬레이션)")
    print("=" * 100)
    print()
    
    # 10사이클 시뮬레이션
    for cycle in range(10):
        print(f"\n--- 사이클 {cycle + 1} ---")
        
        # 시장 데이터 (실제로는 실시간 데이터)
        market_data = {
            '005930': generate_sample_data('3min', days=1),
            '000660': generate_sample_data('3min', days=1),
            '035420': generate_sample_data('3min', days=1),
        }
        
        # 거래 사이클 실행
        executor.run_trading_cycle(market_data, target_stocks)
        
        # 대기 (실제로는 10초~1분)
        time.sleep(0.1)
    
    # 모든 포지션 청산 (장 마감)
    print("\n" + "=" * 100)
    print("🔔 장 마감 - 모든 포지션 청산")
    print("=" * 100)
    
    for code in list(executor.positions.keys()):
        position = executor.positions[code]
        # 시장가로 청산 (시뮬레이션)
        executor.execute_sell(code, position.entry_price * 1.01, position.quantity, "장마감")
    
    # 일일 요약
    executor.print_daily_summary()
    
    print("\n✅ 시뮬레이션 완료!")
    print()
    print("실전 적용 시:")
    print("  1. 키움 OpenAPI 연동")
    print("  2. 실시간 데이터 수신")
    print("  3. 자동매매 시스템 시작")
    print("  4. 모니터링 및 기록")
    

if __name__ == "__main__":
    simulate_auto_trading()
