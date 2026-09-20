#pragma once
#include <vector>

// =====================================================================
// Util.h - 계산과 파일 처리. 키움과 무관한 순수 기능만 모읍니다.
//          이 파일의 함수들은 키움 없이도 테스트할 수 있습니다.
// =====================================================================

// ---------------- 호가 단위 ----------------
// 가격대마다 한 호가의 크기가 다릅니다.
// 주의: 거래소 규정이 바뀌면 이 표도 고쳐야 합니다.
long   TickSize(double price);

// 한 호가가 가격의 몇 퍼센트인가. 작을수록 매매 비용이 쌉니다.
double TickCost(double price);

// ---------------- 종목 거르기 ----------------
// 우선주 / ETF / ETN / 스팩 / 리츠 이면 true (= 빼야 할 종목)
bool IsExcludedSymbol(LPCTSTR code, LPCTSTR name);

// ---------------- 일봉 한 줄 ----------------
struct DailyBar
{
    CString date;      // YYYYMMDD
    double  open;
    double  high;
    double  low;
    double  close;
    double  volume;    // 주
    double  turnover;  // 거래대금 (원)

    DailyBar() : open(0), high(0), low(0), close(0), volume(0), turnover(0) {}
};

// ---------------- 분봉 한 줄 ----------------
struct MinuteBar
{
    CString stamp;     // YYYYMMDDHHMMSS
    double  open;
    double  high;
    double  low;
    double  close;
    double  volume;

    MinuteBar() : open(0), high(0), low(0), close(0), volume(0) {}
};

// ---------------- 거래대금 계산 ----------------
// 20일 이동평균 거래대금의 최댓값. 2년 중 가장 활발했던 시기를 봅니다.
// 봉이 window 보다 적으면 0 을 돌려줍니다.
double MaxRollingTurnover(const std::vector<DailyBar>& bars, int window);

// 위 최댓값이 나온 구간의 평균 종가. 호가 비용을 그 시점 가격으로 재려고요.
double AvgCloseAtPeakTurnover(const std::vector<DailyBar>& bars, int window);

// ---------------- 문자열 ----------------
CString TrimAll(const CString& s);          // 앞뒤 공백 제거
double  ParseNum(const CString& s);         // 부호와 콤마가 섞인 키움 숫자 문자열
CString CsvEscape(const CString& s);
std::vector<CString> SplitCsvLine(const CString& line);

// ---------------- 파일 ----------------
bool EnsureDir(LPCTSTR path);               // 없으면 만듭니다 (중간 경로 포함)
CString ExeDir();                           // 실행 파일이 있는 폴더
CString PathUnder(LPCTSTR relative);        // 실행 폴더 기준 전체 경로
bool FileExistsAt(LPCTSTR path);

// ---------------- 날짜 ----------------
CString TodayYmd();                         // YYYYMMDD
CString YmdMinusDays(LPCTSTR ymd, int days);
