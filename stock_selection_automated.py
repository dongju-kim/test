"""
자동 종목 선정 시스템
매일 아침 최적의 종목을 자동으로 선정
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class StockInfo:
    """종목 정보"""
    code: str
    name: str
    price: float
    market_cap: float  # 시가총액 (억원)
    volume_value: float  # 거래대금 (억원)
    foreign_ratio: float  # 외국인 보유율 (%)
    institution_net: float  # 기관 순매수 (억원)
    spread_pct: float  # 호가 스프레드 (%)
    week_change_pct: float  # 주간 변동률 (%)
    avg_volume_ratio: float  # 평균 거래량 대비
    has_disclosure: bool  # 당일 공시 여부
    is_managed: bool  # 관리종목 여부
    is_suspended: bool  # 거래정지 여부
    score: float = 0.0  # 종합 점수


class StockSelector:
    """종목 선정 자동화"""
    
    def __init__(self):
        self.selected_stocks = []
        
    def filter_basic_requirements(self, stocks: List[StockInfo]) -> List[StockInfo]:
        """
        1단계: 필수 조건 필터링
        """
        print("=" * 80)
        print("📊 1단계: 필수 조건 필터링")
        print("=" * 80)
        print()
        
        filtered = []
        
        for stock in stocks:
            # 필수 조건 체크
            if (stock.market_cap >= 5000 and  # 5,000억 이상
                stock.volume_value >= 500 and  # 500억 이상
                stock.price >= 10000 and  # 10,000원 이상
                stock.spread_pct <= 0.1 and  # 스프레드 0.1% 이하
                not stock.is_managed and  # 관리종목 아님
                not stock.is_suspended):  # 거래정지 아님
                
                filtered.append(stock)
        
        print(f"전체 종목: {len(stocks)}개")
        print(f"필터링 후: {len(filtered)}개")
        print()
        
        return filtered
    
    def calculate_scores(self, stocks: List[StockInfo]) -> List[StockInfo]:
        """
        2단계: 점수 계산
        """
        print("=" * 80)
        print("📈 2단계: 종목별 점수 계산")
        print("=" * 80)
        print()
        
        # 시가총액 순위
        sorted_by_cap = sorted(stocks, key=lambda x: x.market_cap, reverse=True)
        cap_ranks = {s.code: i+1 for i, s in enumerate(sorted_by_cap)}
        
        # 거래대금 순위
        sorted_by_volume = sorted(stocks, key=lambda x: x.volume_value, reverse=True)
        volume_ranks = {s.code: i+1 for i, s in enumerate(sorted_by_volume)}
        
        for stock in stocks:
            score = 0
            reasons = []
            
            # 시가총액 TOP 50
            if cap_ranks[stock.code] <= 50:
                score += 3
                reasons.append("시총TOP50(+3)")
            
            # 거래대금 TOP 50
            if volume_ranks[stock.code] <= 50:
                score += 2
                reasons.append("거래TOP50(+2)")
            
            # 외국인 보유율 30% 이상
            if stock.foreign_ratio >= 30:
                score += 2
                reasons.append("외국인30%↑(+2)")
            
            # 기관 순매수
            if stock.institution_net > 0:
                score += 1
                reasons.append("기관순매수(+1)")
            
            # 거래량 증가
            if stock.avg_volume_ratio > 1.0:
                score += 1
                reasons.append("거래량↑(+1)")
            
            # 감점: 급등락
            if abs(stock.week_change_pct) > 10:
                score -= 5
                reasons.append("급등락(-5)")
            
            # 감점: 공시
            if stock.has_disclosure:
                score -= 3
                reasons.append("공시(-3)")
            
            stock.score = score
            
            print(f"{stock.name:15} | 점수: {score:>3} | {', '.join(reasons)}")
        
        print()
        return stocks
    
    def select_top_stocks(self, stocks: List[StockInfo], top_n: int = 10) -> List[StockInfo]:
        """
        3단계: 상위 종목 선정
        """
        print("=" * 80)
        print(f"🏆 3단계: 상위 {top_n}개 종목 선정")
        print("=" * 80)
        print()
        
        sorted_stocks = sorted(stocks, key=lambda x: x.score, reverse=True)
        top_stocks = sorted_stocks[:top_n]
        
        print(f"{'순위':<5} {'종목명':<15} {'점수':<6} {'시총(억)':<12} {'거래대금(억)':<12}")
        print("-" * 80)
        
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i:<5} {stock.name:<15} {stock.score:<6} {stock.market_cap:>10,.0f}  {stock.volume_value:>10,.0f}")
        
        print()
        return top_stocks
    
    def allocate_strategies(self, stocks: List[StockInfo]) -> Dict[str, List[StockInfo]]:
        """
        4단계: 전략별 종목 할당
        """
        print("=" * 80)
        print("🎯 4단계: 전략별 종목 할당")
        print("=" * 80)
        print()
        
        allocation = {
            'bollinger': [],  # 볼린저밴드 전략
            'momentum': [],   # 모멘텀 전략 (실시간 선정)
            'vwap': []        # VWAP 전략
        }
        
        # 볼린저밴드: 상위 5개
        allocation['bollinger'] = stocks[:5]
        print("📊 볼린저밴드 전략 (상위 5개):")
        for stock in allocation['bollinger']:
            print(f"  - {stock.name} ({stock.code})")
        print()
        
        # VWAP: 초대형주만 (시총 TOP 3)
        top_by_cap = sorted(stocks, key=lambda x: x.market_cap, reverse=True)[:3]
        allocation['vwap'] = top_by_cap
        print("📊 VWAP 전략 (초대형주):")
        for stock in allocation['vwap']:
            print(f"  - {stock.name} ({stock.code})")
        print()
        
        # 모멘텀: 실시간 선정
        print("📊 모멘텀 전략: 장 중 실시간 선정")
        print("  조건: 거래량 폭발 + 뉴스/테마 + 적정 상승률")
        print()
        
        return allocation
    
    def run_daily_selection(self, stocks: List[StockInfo]) -> Dict[str, List[StockInfo]]:
        """매일 종목 선정 실행"""
        
        print("\n" + "=" * 80)
        print(f"🌅 자동 종목 선정 시스템 (일자: {datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print("=" * 80)
        print()
        
        # 1단계: 필수 조건 필터링
        filtered = self.filter_basic_requirements(stocks)
        
        if len(filtered) == 0:
            print("⚠️  필수 조건을 만족하는 종목이 없습니다.")
            return {}
        
        # 2단계: 점수 계산
        scored = self.calculate_scores(filtered)
        
        # 3단계: 상위 선정
        top_stocks = self.select_top_stocks(scored, top_n=10)
        
        # 4단계: 전략별 할당
        allocation = self.allocate_strategies(top_stocks)
        
        self.selected_stocks = top_stocks
        
        return allocation


def get_recommended_stocks() -> List[str]:
    """
    추천 종목 리스트 (2025년 기준)
    실제로는 API에서 가져오지만, 여기서는 하드코딩
    """
    return [
        ('005930', '삼성전자', 'A'),
        ('000660', 'SK하이닉스', 'A'),
        ('035420', 'NAVER', 'A'),
        ('035720', '카카오', 'A'),
        ('005935', '삼성전자우', 'A'),
        ('005380', '현대차', 'B'),
        ('000270', '기아', 'B'),
        ('068270', '셀트리온', 'B'),
        ('005490', 'POSCO홀딩스', 'B'),
        ('051910', 'LG화학', 'B'),
        ('006400', '삼성SDI', 'C'),
        ('105560', 'KB금융', 'C'),
        ('055550', '신한지주', 'C'),
        ('207940', '삼성바이오로직스', 'C'),
        ('373220', 'LG에너지솔루션', 'C'),
    ]


def generate_sample_stock_data() -> List[StockInfo]:
    """샘플 종목 데이터 생성 (실제로는 API에서 가져옴)"""
    
    recommended = get_recommended_stocks()
    stocks = []
    
    base_prices = {
        '005930': 70000,    # 삼성전자
        '000660': 130000,   # SK하이닉스
        '035420': 200000,   # NAVER
        '035720': 50000,    # 카카오
        '005935': 60000,    # 삼성전자우
        '005380': 180000,   # 현대차
        '000270': 90000,    # 기아
        '068270': 150000,   # 셀트리온
        '005490': 350000,   # POSCO홀딩스
        '051910': 400000,   # LG화학
        '006400': 350000,   # 삼성SDI
        '105560': 60000,    # KB금융
        '055550': 40000,    # 신한지주
        '207940': 800000,   # 삼성바이오로직스
        '373220': 400000,   # LG에너지솔루션
    }
    
    for code, name, grade in recommended:
        # 등급별 기본 점수
        if grade == 'A':
            market_cap = np.random.uniform(300000, 600000)  # 30~60조
            volume_value = np.random.uniform(5000, 15000)  # 5,000~15,000억
            foreign_ratio = np.random.uniform(40, 60)
        elif grade == 'B':
            market_cap = np.random.uniform(100000, 300000)  # 10~30조
            volume_value = np.random.uniform(1000, 5000)
            foreign_ratio = np.random.uniform(25, 45)
        else:
            market_cap = np.random.uniform(50000, 100000)   # 5~10조
            volume_value = np.random.uniform(500, 2000)
            foreign_ratio = np.random.uniform(15, 35)
        
        stock = StockInfo(
            code=code,
            name=name,
            price=base_prices.get(code, 50000),
            market_cap=market_cap,
            volume_value=volume_value,
            foreign_ratio=foreign_ratio,
            institution_net=np.random.uniform(-100, 200),
            spread_pct=np.random.uniform(0.02, 0.08),
            week_change_pct=np.random.uniform(-5, 5),
            avg_volume_ratio=np.random.uniform(0.8, 1.5),
            has_disclosure=np.random.random() < 0.1,  # 10% 확률
            is_managed=False,
            is_suspended=False
        )
        stocks.append(stock)
    
    return stocks


def print_strategy_guide(allocation: Dict[str, List[StockInfo]]):
    """전략별 실행 가이드 출력"""
    
    print("\n" + "=" * 80)
    print("📋 오늘의 자동매매 전략 가이드")
    print("=" * 80)
    print()
    
    print("🎯 전략 1: 볼린저밴드 반등 (3분봉)")
    print("-" * 80)
    print("대상 종목:")
    for stock in allocation.get('bollinger', []):
        print(f"  ✅ {stock.name} ({stock.code}) - 현재가: {stock.price:,}원")
    print()
    print("매수 조건:")
    print("  1. 현재가 <= 볼린저 하단")
    print("  2. RSI(9) < 35")
    print("  3. MACD 히스토그램 상승 전환")
    print("  4. 거래량 > 평균 × 2.0")
    print("  5. 코스피 -1.5% 이상 아님")
    print()
    print("매도 조건:")
    print("  - 손절: -0.7%")
    print("  - 익절: +1.5% (50%), +2.0% (50%)")
    print("  - 시간: 30분 경과")
    print()
    
    print("🎯 전략 2: VWAP 회귀 (5분봉)")
    print("-" * 80)
    print("대상 종목:")
    for stock in allocation.get('vwap', []):
        print(f"  ✅ {stock.name} ({stock.code}) - 현재가: {stock.price:,}원")
    print()
    print("매수 조건:")
    print("  1. 현재가 < VWAP × 0.985 (-1.5% 괴리)")
    print("  2. RSI(14) < 40")
    print("  3. 거래량 증가 추세")
    print()
    print("매도 조건:")
    print("  - 익절: VWAP 도달")
    print("  - 손절: -0.5%")
    print("  - 시간: 1시간")
    print()
    
    print("🎯 전략 3: 모멘텀 브레이크아웃 (1분봉)")
    print("-" * 80)
    print("실시간 선정 (장 중 조건 충족 시)")
    print()
    print("선정 조건:")
    print("  - 거래량 평균의 3배 이상")
    print("  - 당일 +2% ~ +5% 상승")
    print("  - 뉴스/테마 있음")
    print()
    print("매수 조건:")
    print("  - 5분간 고가 돌파")
    print("  - 60 < RSI(7) < 80")
    print()
    print("매도 조건:")
    print("  - 익절: +1.0%")
    print("  - 손절: -0.3%")
    print("  - 시간: 5분")
    print()
    
    print("=" * 80)
    print("⚠️  리스크 관리")
    print("=" * 80)
    print("  - 1회 최대 리스크: 총 자금의 1%")
    print("  - 일일 손실 한도: 총 자금의 2%")
    print("  - 최대 동시 포지션: 3개")
    print("  - 거래 시간: 09:30 ~ 15:15")
    print("=" * 80)
    print()


if __name__ == "__main__":
    # 샘플 데이터 생성
    stocks = generate_sample_stock_data()
    
    # 종목 선정 실행
    selector = StockSelector()
    allocation = selector.run_daily_selection(stocks)
    
    # 전략 가이드 출력
    if allocation:
        print_strategy_guide(allocation)
        
        print("✅ 종목 선정 완료!")
        print()
        print("다음 단계:")
        print("  1. 자동매매 시스템 시작")
        print("  2. 실시간 데이터 모니터링")
        print("  3. 조건 충족 시 자동 진입")
        print("  4. 손절/익절 자동 실행")
        print()
        print("행운을 빕니다! 🚀")
