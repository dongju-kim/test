"""
키움 OpenAPI 연동 모듈
실시간 데이터 수신 및 자동매매 실행
"""

from PyQt5.QtCore import QEventLoop
from PyQt5.QAxContainer import QAxWidget
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class KiwoomAPI:
    """키움 OpenAPI 래퍼 클래스"""
    
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.account = None
        self.tr_event_loop = QEventLoop()
        
        # 이벤트 연결
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        
        # 데이터 저장
        self.tr_data = {}
        self.real_data = {}
        
    def comm_connect(self):
        """로그인"""
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()
        
    def _on_event_connect(self, err_code):
        """로그인 이벤트"""
        if err_code == 0:
            print("✅ 키움 로그인 성공")
            # 계좌 정보 가져오기
            account_list = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            self.account = account_list.split(';')[0]
            print(f"계좌번호: {self.account}")
        else:
            print(f"❌ 로그인 실패: {err_code}")
        
        self.login_event_loop.exit()
    
    def get_candle_data(self, code: str, timeframe: str, count: int = 500) -> pd.DataFrame:
        """
        분봉 데이터 조회
        
        Args:
            code: 종목코드 (예: '005930')
            timeframe: '1', '3', '5', '10', '30', '60'
            count: 조회할 데이터 개수
        """
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "틱범위", timeframe)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                            "분봉조회", "opt10080", 0, "0101")
        
        self.tr_event_loop.exec_()
        
        # 데이터 가공
        df = pd.DataFrame(self.tr_data['opt10080'])
        
        if len(df) > 0:
            df['체결시간'] = pd.to_datetime(df['체결시간'], format='%Y%m%d%H%M%S')
            df = df.set_index('체결시간')
            df = df.rename(columns={
                '현재가': 'close',
                '시가': 'open',
                '고가': 'high',
                '저가': 'low',
                '거래량': 'volume'
            })
            
            # 숫자 변환
            for col in ['close', 'open', 'high', 'low']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
        return df
    
    def _on_receive_tr_data(self, screen_no, rqname, trcode, recordname, prev_next):
        """TR 데이터 수신 이벤트"""
        if rqname == "분봉조회":
            cnt = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            
            data = []
            for i in range(cnt):
                row = {
                    '체결시간': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                    trcode, rqname, i, "체결시간").strip(),
                    '현재가': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                  trcode, rqname, i, "현재가").strip(),
                    '시가': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                trcode, rqname, i, "시가").strip(),
                    '고가': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                trcode, rqname, i, "고가").strip(),
                    '저가': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                trcode, rqname, i, "저가").strip(),
                    '거래량': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                  trcode, rqname, i, "거래량").strip(),
                }
                data.append(row)
            
            self.tr_data[trcode] = data
        
        self.tr_event_loop.exit()
    
    def _on_receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신 이벤트"""
        if real_type == "주식체결":
            # 실시간 체결 데이터 처리
            current_price = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 10)
            volume = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 15)
            
            self.real_data[code] = {
                'price': int(current_price),
                'volume': int(volume),
                'time': datetime.now()
            }
    
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신 이벤트"""
        # 주문 체결 시 처리
        pass
    
    def send_order(self, order_type: str, code: str, qty: int, price: int = 0):
        """
        주문 전송
        
        Args:
            order_type: '1' 매수, '2' 매도
            code: 종목코드
            qty: 수량
            price: 가격 (0이면 시장가)
        """
        order_type_name = "매수" if order_type == "1" else "매도"
        hoga_type = "03" if price == 0 else "00"  # 03: 시장가, 00: 지정가
        
        result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [order_type_name, "0101", self.account, order_type, code, qty, price, hoga_type, ""]
        )
        
        if result == 0:
            print(f"✅ 주문 전송 성공: {order_type_name} {code} {qty}주")
        else:
            print(f"❌ 주문 전송 실패: {result}")
        
        return result


class AutoTradingSystem:
    """자동매매 시스템"""
    
    def __init__(self, kiwoom: KiwoomAPI, strategy_manager):
        self.kiwoom = kiwoom
        self.strategy_manager = strategy_manager
        self.positions = {}  # 현재 포지션
        self.target_stocks = []  # 대상 종목 리스트
        
    def add_target_stock(self, code: str, name: str, strategy: str, timeframe: str):
        """거래 대상 종목 추가"""
        self.target_stocks.append({
            'code': code,
            'name': name,
            'strategy': strategy,
            'timeframe': timeframe
        })
        print(f"종목 추가: {name} ({code}) - {strategy} 전략, {timeframe}분봉")
    
    def run(self):
        """자동매매 실행"""
        print("\n" + "=" * 80)
        print("🤖 자동매매 시스템 시작")
        print("=" * 80)
        
        for stock in self.target_stocks:
            print(f"\n📊 {stock['name']} 분석 중...")
            
            # 분봉 데이터 조회
            df = self.kiwoom.get_candle_data(
                stock['code'], 
                stock['timeframe'], 
                count=100
            )
            
            if len(df) == 0:
                print(f"  ⚠️  데이터 없음")
                continue
            
            # 전략 실행
            signal = self.strategy_manager.execute_strategy(stock['strategy'], df)
            
            print(f"  신호: {signal.signal_type}")
            print(f"  현재가: {signal.price:,}원")
            print(f"  신뢰도: {signal.confidence:.0%}")
            print(f"  사유: {signal.reason}")
            
            # 매매 실행
            if signal.signal_type == 'BUY' and signal.confidence >= 0.7:
                if stock['code'] not in self.positions:
                    print(f"  🔵 매수 주문 실행!")
                    # 여기에 실제 주문 로직
                    # self.kiwoom.send_order('1', stock['code'], qty, 0)
                    
            elif signal.signal_type == 'SELL':
                if stock['code'] in self.positions:
                    print(f"  🔴 매도 주문 실행!")
                    # 여기에 실제 주문 로직
                    # self.kiwoom.send_order('2', stock['code'], qty, 0)


if __name__ == "__main__":
    print("""
    키움 OpenAPI 연동 모듈
    
    사용 예시:
    
    from kiwoom_api_connector import KiwoomAPI, AutoTradingSystem
    from kiwoom_scalping_strategies import StrategyManager
    
    # 1. 키움 API 초기화
    kiwoom = KiwoomAPI()
    kiwoom.comm_connect()
    
    # 2. 전략 매니저 초기화
    strategy_manager = StrategyManager()
    
    # 3. 자동매매 시스템 설정
    auto_trading = AutoTradingSystem(kiwoom, strategy_manager)
    auto_trading.add_target_stock('005930', '삼성전자', 'strategy_b', '3')
    auto_trading.add_target_stock('000660', 'SK하이닉스', 'strategy_b', '3')
    
    # 4. 실행
    auto_trading.run()
    """)
