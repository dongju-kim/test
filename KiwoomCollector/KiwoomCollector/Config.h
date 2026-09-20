#pragma once
// =====================================================================
// Config.h - 모든 설정값을 여기 한 곳에 모읍니다.
//            값을 바꾸려면 이 파일만 고치면 됩니다.
// =====================================================================

namespace Config
{
    // ---------------- 저장 위치 ----------------
    // 실행 파일이 있는 폴더 아래에 만들어집니다.
    static LPCTSTR DATA_DIR     = _T("data");          // 최상위
    static LPCTSTR DAILY_DIR    = _T("data\\daily");   // 일봉 (프로그램 1)
    static LPCTSTR BARS_DIR     = _T("data\\bars");    // 1분봉 (프로그램 2)
    static LPCTSTR LOG_DIR      = _T("data\\log");
    static LPCTSTR SYMBOLS_CSV  = _T("data\\symbols.csv");      // 프로그램 1 결과
    static LPCTSTR ALLCODES_CSV = _T("data\\all_codes.csv");    // 전 종목 원본
    static LPCTSTR MANIFEST_CSV = _T("data\\manifest.csv");     // 어디까지 받았나

    // ---------------- 요청 속도 ----------------
    // 키움 조회 제한은 공식 문서에 또렷하게 안 나와 있습니다.
    // 널리 쓰이는 값: 1초 5회 / 1분 100회 / 1시간 1000회.
    // 시간당 1000회가 가장 빡빡해서 3600ms 가 안전합니다.
    // 빠르게 받고 싶으면 줄이되, "조회제한" 메시지가 뜨면 다시 늘리세요.
    static const int REQUEST_INTERVAL_MS = 3600;   // 요청 사이 간격
    static const int RETRY_WAIT_MS       = 60000;  // 조회제한 걸렸을 때 쉬는 시간
    static const int MAX_RETRY           = 3;      // 한 요청당 재시도 횟수

    // ---------------- 프로그램 1 : 종목 고르기 ----------------
    static const int   DAILY_YEARS          = 2;        // 일봉 몇 년치
    static const int   LIQUIDITY_WINDOW     = 20;       // 거래대금 평균 낼 일수
    static const double MIN_TURNOVER_WON    = 5.0e9;    // 50억. 20일 평균의 최댓값 기준
    static const double MAX_TICK_COST       = 0.0015;   // 0.15%. 한 호가 / 가격
    static const int   MIN_DAILY_ROWS       = 60;       // 상장 60거래일 이상

    // 프로그램 2 에서 실제로 분봉 받을 종목 수 상한.
    // 거래대금 큰 순서로 자릅니다. 0 이면 제한 없음.
    // 700종목 전부 받으면 이틀 걸립니다. 처음엔 150 정도로 시작하세요.
    static const int   MAX_SYMBOLS_FOR_BARS = 150;

    // ---------------- 프로그램 2 : 분봉 받기 ----------------
    static const int   MINUTE_TICK_RANGE    = 1;     // 1분봉
    static const int   MAX_PAGES_PER_SYMBOL = 200;   // 한 종목당 연속조회 상한 (안전장치)

    // ---------------- 무결성 검사 ----------------
    static const int   EXPECTED_BARS_PER_DAY = 390;   // 09:00~15:30
    static const double GAP_WARN_RATIO       = 0.30;  // 전일 종가 대비 30% 넘게 튀면 경고

    // ---------------- TR 코드 ----------------
    static LPCTSTR TR_DAILY   = _T("opt10081");  // 주식일봉차트조회요청
    static LPCTSTR TR_MINUTE  = _T("opt10080");  // 주식분봉차트조회요청
    static LPCTSTR SCREEN_NO  = _T("1000");
}
