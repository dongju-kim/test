#include "pch.h"
#include "Util.h"
#include <algorithm>
#ifndef LINUX_SYNTAX_CHECK
#include <shlwapi.h>
#pragma comment(lib, "shlwapi.lib")
#endif

// ---------------------------------------------------------------- 호가 단위
long TickSize(double price)
{
    if (price <   2000.0) return 1;
    if (price <   5000.0) return 5;
    if (price <  20000.0) return 10;
    if (price <  50000.0) return 50;
    if (price < 200000.0) return 100;
    if (price < 500000.0) return 500;
    return 1000;
}

double TickCost(double price)
{
    if (price <= 0.0) return 1.0;               // 말이 안 되는 값이면 최악으로 취급
    return (double)TickSize(price) / price;
}

// ------------------------------------------------------------- 종목 거르기
bool IsExcludedSymbol(LPCTSTR code, LPCTSTR name)
{
    CString c(code), n(name);
    c.Trim();
    n.Trim();

    if (c.GetLength() != 6) return true;

    // 우선주: 보통주는 끝자리가 0 입니다.
    if (c.Right(1) != _T("0")) return true;

    // 이름으로 거르기
    static LPCTSTR kWords[] = {
        _T("스팩"), _T("리츠"),
        _T("KODEX"), _T("TIGER"), _T("KBSTAR"), _T("ARIRANG"),
        _T("ACE "), _T("SOL "), _T("HANARO"), _T("PLUS "),
        _T("KOSEF"), _T("TIMEFOLIO"), _T("WOORI "), _T("RISE "),
        _T("ETN"), _T("선물"), _T("레버리지"), _T("인버스")
    };
    for (int i = 0; i < (int)_countof(kWords); ++i)
    {
        if (n.Find(kWords[i]) >= 0) return true;
    }

    // 이름 끝이 우선주 표기인 경우 (예: 삼성전자우, LG화학우, 현대차2우B)
    if (n.Right(1) == _T("우")) return true;
    if (n.GetLength() >= 2 && n.Right(2) == _T("우B")) return true;

    return false;
}

// ------------------------------------------------------------- 거래대금
double MaxRollingTurnover(const std::vector<DailyBar>& bars, int window)
{
    if (window <= 0) return 0.0;
    if ((int)bars.size() < window) return 0.0;

    double sum = 0.0;
    for (int i = 0; i < window; ++i) sum += bars[i].turnover;

    double best = sum / window;
    for (size_t i = window; i < bars.size(); ++i)
    {
        sum += bars[i].turnover;
        sum -= bars[i - window].turnover;
        double avg = sum / window;
        if (avg > best) best = avg;
    }
    return best;
}

double AvgCloseAtPeakTurnover(const std::vector<DailyBar>& bars, int window)
{
    if (window <= 0) return 0.0;
    if ((int)bars.size() < window) return 0.0;

    double sum = 0.0;
    for (int i = 0; i < window; ++i) sum += bars[i].turnover;

    double best     = sum / window;
    size_t bestEnd  = window - 1;

    for (size_t i = window; i < bars.size(); ++i)
    {
        sum += bars[i].turnover;
        sum -= bars[i - window].turnover;
        double avg = sum / window;
        if (avg > best) { best = avg; bestEnd = i; }
    }

    double csum = 0.0;
    for (size_t i = bestEnd + 1 - window; i <= bestEnd; ++i) csum += bars[i].close;
    return csum / window;
}

// ------------------------------------------------------------- 문자열
CString TrimAll(const CString& s)
{
    CString t(s);
    t.Trim();
    return t;
}

double ParseNum(const CString& s)
{
    // 키움은 "+1,234", "-560", " 0" 같이 부호와 콤마를 섞어서 줍니다.
    CString t(s);
    t.Trim();
    t.Remove(_T(','));
    t.Remove(_T('+'));
    if (t.IsEmpty()) return 0.0;

    bool minus = (t[0] == _T('-'));
    if (minus) t = t.Mid(1);
    if (t.IsEmpty()) return 0.0;

    double v = _tstof(t);
    // 분봉의 고가/저가는 음수로 오는 경우가 있어 절댓값을 씁니다.
    return minus ? -v : v;
}

CString CsvEscape(const CString& s)
{
    if (s.Find(_T(',')) < 0 && s.Find(_T('"')) < 0 && s.Find(_T('\n')) < 0)
        return s;

    CString t(s);
    t.Replace(_T("\""), _T("\"\""));
    CString out;
    out.Format(_T("\"%s\""), (LPCTSTR)t);
    return out;
}

std::vector<CString> SplitCsvLine(const CString& line)
{
    std::vector<CString> out;
    CString cur;
    bool inQuote = false;

    for (int i = 0; i < line.GetLength(); ++i)
    {
        TCHAR ch = line[i];
        if (inQuote)
        {
            if (ch == _T('"'))
            {
                if (i + 1 < line.GetLength() && line[i + 1] == _T('"')) { cur += _T('"'); ++i; }
                else inQuote = false;
            }
            else cur += ch;
        }
        else
        {
            if (ch == _T('"'))      inQuote = true;
            else if (ch == _T(',')) { out.push_back(cur); cur.Empty(); }
            else                    cur += ch;
        }
    }
    out.push_back(cur);
    return out;
}

// ------------------------------------------------------------- 파일
CString ExeDir()
{
    TCHAR buf[MAX_PATH] = { 0 };
    ::GetModuleFileName(NULL, buf, MAX_PATH);
    CString p(buf);
    int pos = p.ReverseFind(_T('\\'));
    return (pos > 0) ? p.Left(pos) : CString(_T("."));
}

CString PathUnder(LPCTSTR relative)
{
    CString p = ExeDir();
    p += _T("\\");
    p += relative;
    return p;
}

bool EnsureDir(LPCTSTR path)
{
    CString p(path);
    if (p.IsEmpty()) return false;
    if (::PathIsDirectory(p)) return true;

    int pos = p.ReverseFind(_T('\\'));
    if (pos > 0)
    {
        CString parent = p.Left(pos);
        if (!::PathIsDirectory(parent)) EnsureDir(parent);
    }
    return ::CreateDirectory(p, NULL) != 0 || ::PathIsDirectory(p);
}

bool FileExistsAt(LPCTSTR path)
{
    DWORD a = ::GetFileAttributes(path);
    return (a != INVALID_FILE_ATTRIBUTES) && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

// ------------------------------------------------------------- 날짜
CString TodayYmd()
{
    SYSTEMTIME st;
    ::GetLocalTime(&st);
    CString s;
    s.Format(_T("%04d%02d%02d"), st.wYear, st.wMonth, st.wDay);
    return s;
}

CString YmdMinusDays(LPCTSTR ymd, int days)
{
    CString s(ymd);
    if (s.GetLength() != 8) return s;

    SYSTEMTIME st = {};
    st.wYear  = (WORD)_ttoi(s.Left(4));
    st.wMonth = (WORD)_ttoi(s.Mid(4, 2));
    st.wDay   = (WORD)_ttoi(s.Mid(6, 2));

    FILETIME ft;
    if (!::SystemTimeToFileTime(&st, &ft)) return s;

    ULARGE_INTEGER u;
    u.LowPart  = ft.dwLowDateTime;
    u.HighPart = ft.dwHighDateTime;
    u.QuadPart -= (ULONGLONG)days * 24ULL * 60ULL * 60ULL * 10000000ULL;
    ft.dwLowDateTime  = u.LowPart;
    ft.dwHighDateTime = u.HighPart;

    if (!::FileTimeToSystemTime(&ft, &st)) return s;

    CString out;
    out.Format(_T("%04d%02d%02d"), st.wYear, st.wMonth, st.wDay);
    return out;
}
