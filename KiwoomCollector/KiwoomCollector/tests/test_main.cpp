// 리눅스에서 돌리는 단위 테스트. Windows 빌드에는 들어가지 않습니다.
//   g++ -std=c++17 -DLINUX_SYNTAX_CHECK -I. -Itests tests/test_main.cpp Util.cpp -o /tmp/t && /tmp/t
#include "pch.h"
#include "Util.h"
#include <cstdio>

static int g_fail = 0, g_pass = 0;

static void Check(bool ok, const char* what)
{
    if (ok) { ++g_pass; }
    else    { ++g_fail; printf("  실패: %s\n", what); }
}
static void CheckNear(double got, double want, double tol, const char* what)
{
    bool ok = fabs(got - want) <= tol;
    if (ok) ++g_pass;
    else { ++g_fail; printf("  실패: %s  (받은값 %.6f, 기대값 %.6f)\n", what, got, want); }
}

int main()
{
    printf("== 호가 단위 ==\n");
    Check(TickSize(1500)   == 1,    "1,500원 -> 1원");
    Check(TickSize(1999)   == 1,    "1,999원 -> 1원");
    Check(TickSize(2000)   == 5,    "2,000원 -> 5원 (경계)");
    Check(TickSize(4999)   == 5,    "4,999원 -> 5원");
    Check(TickSize(5000)   == 10,   "5,000원 -> 10원 (경계)");
    Check(TickSize(19999)  == 10,   "19,999원 -> 10원");
    Check(TickSize(20000)  == 50,   "20,000원 -> 50원 (경계)");
    Check(TickSize(49999)  == 50,   "49,999원 -> 50원");
    Check(TickSize(50000)  == 100,  "50,000원 -> 100원 (경계)");
    Check(TickSize(199999) == 100,  "199,999원 -> 100원");
    Check(TickSize(200000) == 500,  "200,000원 -> 500원 (경계)");
    Check(TickSize(500000) == 1000, "500,000원 -> 1000원 (경계)");

    printf("== 호가 비용 ==\n");
    // 설계서에 적은 값과 맞는지
    CheckNear(TickCost(2100)   * 100, 0.238, 0.01, "2,100원 -> 0.24%");
    CheckNear(TickCost(19900)  * 100, 0.050, 0.01, "19,900원 -> 0.05%");
    CheckNear(TickCost(21000)  * 100, 0.238, 0.01, "21,000원 -> 0.24%");
    CheckNear(TickCost(199000) * 100, 0.050, 0.01, "199,000원 -> 0.05%");
    Check(TickCost(0) >= 1.0, "0원이면 최악으로 취급");
    // 단위가 바뀌는 구간 바로 위가 더 불리하다는 성질
    Check(TickCost(21000) > TickCost(19900), "21,000원이 19,900원보다 불리");

    printf("== 종목 거르기 ==\n");
    Check(!IsExcludedSymbol("005930", "삼성전자"),        "삼성전자는 통과");
    Check( IsExcludedSymbol("005935", "삼성전자우"),      "우선주는 제외");
    Check( IsExcludedSymbol("051915", "LG화학우"),        "우선주는 제외 2");
    Check( IsExcludedSymbol("005387", "현대차2우B"),      "2우B 는 제외");
    Check( IsExcludedSymbol("069500", "KODEX 200"),       "ETF 는 제외");
    Check( IsExcludedSymbol("102110", "TIGER 200"),       "ETF 는 제외 2");
    Check( IsExcludedSymbol("123456", "교보14호스팩"),    "스팩은 제외");
    Check( IsExcludedSymbol("330590", "롯데리츠"),        "리츠는 제외");
    Check( IsExcludedSymbol("12345",  "코드짧음"),        "코드 6자리 아니면 제외");
    Check(!IsExcludedSymbol("000660", "SK하이닉스"),      "하이닉스는 통과");

    printf("== 거래대금 계산 ==\n");
    {
        std::vector<DailyBar> bars;
        // 20일 * 3 구간. 가운데 구간만 거래대금이 큽니다.
        for (int i = 0; i < 60; ++i)
        {
            DailyBar b;
            b.close    = 10000 + i;
            b.turnover = (i >= 20 && i < 40) ? 300.0 : 100.0;
            bars.push_back(b);
        }
        CheckNear(MaxRollingTurnover(bars, 20), 300.0, 0.001, "가장 활발한 20일 평균은 300");
        // 그 구간의 평균 종가는 10020..10039 의 평균
        CheckNear(AvgCloseAtPeakTurnover(bars, 20), 10029.5, 0.001, "최대 구간의 평균 종가");
    }
    {
        std::vector<DailyBar> few(5);
        CheckNear(MaxRollingTurnover(few, 20), 0.0, 0.001, "봉이 모자라면 0");
    }

    printf("== 키움 숫자 읽기 ==\n");
    CheckNear(ParseNum("+1,234"),  1234.0, 0.001, "+1,234");
    CheckNear(ParseNum("-560"),    -560.0, 0.001, "-560");
    CheckNear(ParseNum("  7890 "), 7890.0, 0.001, "앞뒤 공백");
    CheckNear(ParseNum(""),           0.0, 0.001, "빈 문자열");
    CheckNear(ParseNum("-"),          0.0, 0.001, "부호만");
    CheckNear(ParseNum("1,234,567"), 1234567.0, 0.001, "콤마 여러 개");

    printf("== CSV ==\n");
    {
        std::vector<CString> c = SplitCsvLine("1,005930,삼성전자,123,456");
        Check(c.size() == 5,          "칸 5개");
        Check(c[1] == "005930",       "두 번째 칸이 종목코드");
        Check(c[2] == "삼성전자",     "세 번째 칸이 종목명");
    }
    {
        std::vector<CString> c = SplitCsvLine("1,\"가,나\",3");
        Check(c.size() == 3,      "따옴표 안의 콤마는 안 쪼갬");
        Check(c[1] == "가,나",    "따옴표 벗기기");
    }
    Check(CsvEscape("보통이름") == "보통이름",     "특수문자 없으면 그대로");
    Check(CsvEscape("가,나") == "\"가,나\"",       "콤마 있으면 감싸기");

    printf("== 날짜 ==\n");
    Check(YmdMinusDays("20260301", 1)  == "20260228", "2026-03-01 하루 전");
    Check(YmdMinusDays("20260101", 1)  == "20251231", "해 넘기기");
    Check(YmdMinusDays("20240301", 1)  == "20240229", "윤년");

    printf("\n결과: 통과 %d, 실패 %d\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
