#include "pch.h"
#include "Jobs.h"
#include "Config.h"
#include "Log.h"
#include <algorithm>
#include <math.h>

// 키움이 돌려주는 항목 이름들.
// 개발가이드와 다르면 여기만 고치면 됩니다.
static LPCTSTR REC_DAILY   = _T("주식일봉차트조회");
static LPCTSTR REC_MINUTE  = _T("주식분봉차트조회");

static LPCTSTR F_DATE      = _T("일자");
static LPCTSTR F_STAMP     = _T("체결시간");
static LPCTSTR F_OPEN      = _T("시가");
static LPCTSTR F_HIGH      = _T("고가");
static LPCTSTR F_LOW       = _T("저가");
static LPCTSTR F_CLOSE     = _T("현재가");
static LPCTSTR F_VOLUME    = _T("거래량");
static LPCTSTR F_TURNOVER  = _T("거래대금");

// 키움 일봉의 거래대금은 백만원 단위로 오는 경우가 있습니다.
// 받아 보고 자릿수가 이상하면 이 값을 1.0 이나 1000000.0 으로 바꾸세요.
static const double TURNOVER_UNIT = 1000000.0;

// =====================================================================
//  프로그램 1 : 종목 목록 만들기
// =====================================================================

CUniverseJob::CUniverseJob(CKiwoomApi* api)
    : m_api(api), m_index(0), m_prevNext(0), m_needRows(0), m_done(false)
{
    m_needRows = Config::DAILY_YEARS * 250;   // 1년 약 250거래일
}

bool CUniverseJob::Begin()
{
    m_targets.clear();
    m_results.clear();
    m_bars.clear();
    m_index    = 0;
    m_prevNext = 0;
    m_done     = false;

    EnsureDir(PathUnder(Config::DATA_DIR));

    std::vector<CString> kospi  = m_api->GetCodeList(_T("0"));
    std::vector<CString> kosdaq = m_api->GetCodeList(_T("10"));

    Log::Write(_T("전 종목: 코스피 %d, 코스닥 %d"), (int)kospi.size(), (int)kosdaq.size());
    if (kospi.empty() && kosdaq.empty())
    {
        Log::Error(_T("종목 목록이 비어 있습니다. 로그인 상태를 확인하세요."));
        return false;
    }

    std::vector<CString> all;
    all.insert(all.end(), kospi.begin(), kospi.end());
    all.insert(all.end(), kosdaq.begin(), kosdaq.end());

    // 전 종목 원본을 남겨 둡니다. 왜 빠졌는지 나중에 확인하려고요.
    CStdioFile fAll;
    bool allOpen = false;
    try
    {
        if (fAll.Open(PathUnder(Config::ALLCODES_CSV),
                      CFile::modeCreate | CFile::modeWrite | CFile::typeText))
        {
            fAll.WriteString(_T("code,name,state,excluded\n"));
            allOpen = true;
        }
    }
    catch (CFileException* e) { e->Delete(); }

    int excluded = 0;
    for (size_t i = 0; i < all.size(); ++i)
    {
        CString code  = all[i];
        CString name  = m_api->GetName(code);
        CString state = m_api->GetStockState(code);

        bool drop = IsExcludedSymbol(code, name);

        // 관리종목 / 거래정지 는 빼 둡니다.
        if (!drop && (state.Find(_T("관리")) >= 0 || state.Find(_T("거래정지")) >= 0))
            drop = true;

        if (allOpen)
        {
            CString line;
            line.Format(_T("%s,%s,%s,%d\n"),
                        (LPCTSTR)code, (LPCTSTR)CsvEscape(name),
                        (LPCTSTR)CsvEscape(state), drop ? 1 : 0);
            try { fAll.WriteString(line); } catch (CFileException* e) { e->Delete(); }
        }

        if (drop) { ++excluded; continue; }

        Target t;
        t.code = code;
        t.name = name;
        m_targets.push_back(t);
    }

    if (allOpen) { try { fAll.Close(); } catch (CFileException* e) { e->Delete(); } }

    Log::Write(_T("이름과 코드로 거른 결과: %d 개 제외, %d 개 남음"),
               excluded, (int)m_targets.size());
    Log::Write(_T("이제 종목마다 일봉 %d 년치를 받습니다. 요청 %d 회 예정."),
               Config::DAILY_YEARS, (int)m_targets.size());

    return !m_targets.empty();
}

void CUniverseJob::SendNext()
{
    if (m_done) return;

    if (m_index >= m_targets.size())
    {
        WriteResults();
        m_done = true;
        return;
    }

    const Target& t = m_targets[m_index];

    m_api->SetInput(_T("종목코드"),     t.code);
    m_api->SetInput(_T("기준일자"),     TodayYmd());
    m_api->SetInput(_T("수정주가구분"), _T("1"));

    CString rq;
    rq.Format(_T("일봉_%s"), (LPCTSTR)t.code);
    m_api->Request(rq, Config::TR_DAILY, m_prevNext, Config::SCREEN_NO);
}

void CUniverseJob::OnTr(const TrContext& ctx)
{
    if (m_done) return;
    if (ctx.trCode.CompareNoCase(Config::TR_DAILY) != 0) return;

    long n = m_api->RepeatCount(ctx.trCode, REC_DAILY);
    for (long i = 0; i < n; ++i)
    {
        DailyBar b;
        b.date     = m_api->Data(ctx.trCode, REC_DAILY, i, F_DATE);
        b.open     = fabs(ParseNum(m_api->Data(ctx.trCode, REC_DAILY, i, F_OPEN)));
        b.high     = fabs(ParseNum(m_api->Data(ctx.trCode, REC_DAILY, i, F_HIGH)));
        b.low      = fabs(ParseNum(m_api->Data(ctx.trCode, REC_DAILY, i, F_LOW)));
        b.close    = fabs(ParseNum(m_api->Data(ctx.trCode, REC_DAILY, i, F_CLOSE)));
        b.volume   = fabs(ParseNum(m_api->Data(ctx.trCode, REC_DAILY, i, F_VOLUME)));
        b.turnover = fabs(ParseNum(m_api->Data(ctx.trCode, REC_DAILY, i, F_TURNOVER))) * TURNOVER_UNIT;

        if (b.date.GetLength() == 8) m_bars.push_back(b);
    }

    bool more = (ctx.prevNext == _T("2"));
    if (more && (int)m_bars.size() < m_needRows)
    {
        m_prevNext = 2;      // 같은 종목 다음 장
        return;
    }

    FinishSymbol();
}

void CUniverseJob::FinishSymbol()
{
    const Target& t = m_targets[m_index];

    // 키움은 최근 것부터 줍니다. 오래된 것부터로 뒤집습니다.
    std::reverse(m_bars.begin(), m_bars.end());

    Result r;
    r.code     = t.code;
    r.name     = t.name;
    r.rows     = (int)m_bars.size();
    r.turnover = MaxRollingTurnover(m_bars, Config::LIQUIDITY_WINDOW);
    r.price    = AvgCloseAtPeakTurnover(m_bars, Config::LIQUIDITY_WINDOW);
    r.tickCost = (r.price > 0.0) ? TickCost(r.price) : 1.0;
    r.passed   = true;
    r.reason   = _T("");

    if (r.rows < Config::MIN_DAILY_ROWS)
    {
        r.passed = false;
        r.reason = _T("상장 기간 부족");
    }
    else if (r.turnover < Config::MIN_TURNOVER_WON)
    {
        r.passed = false;
        r.reason = _T("거래대금 미달");
    }
    else if (r.tickCost > Config::MAX_TICK_COST)
    {
        r.passed = false;
        r.reason = _T("호가 비용 과다");
    }

    m_results.push_back(r);

    if ((m_index % 50) == 0 || r.passed)
    {
        Log::Write(_T("[%d/%d] %s %s  일봉 %d  거래대금 %.0f억  호가 %.3f%%  %s"),
                   (int)m_index + 1, (int)m_targets.size(),
                   (LPCTSTR)r.code, (LPCTSTR)r.name, r.rows,
                   r.turnover / 1.0e8, r.tickCost * 100.0,
                   r.passed ? _T("통과") : (LPCTSTR)r.reason);
    }

    m_bars.clear();
    m_prevNext = 0;
    ++m_index;
}

void CUniverseJob::WriteResults()
{
    // 거래대금 큰 순서로 정렬합니다. 2단계에서 위에서부터 자르려고요.
    std::vector<Result> passed;
    for (size_t i = 0; i < m_results.size(); ++i)
        if (m_results[i].passed) passed.push_back(m_results[i]);

    std::sort(passed.begin(), passed.end(),
              [](const Result& a, const Result& b) { return a.turnover > b.turnover; });

    CStdioFile f;
    try
    {
        if (!f.Open(PathUnder(Config::SYMBOLS_CSV),
                    CFile::modeCreate | CFile::modeWrite | CFile::typeText))
        {
            Log::Error(_T("symbols.csv 를 못 만들었습니다."));
            return;
        }
        f.WriteString(_T("rank,code,name,turnover_won,price,tick_cost_pct,daily_rows\n"));

        for (size_t i = 0; i < passed.size(); ++i)
        {
            const Result& r = passed[i];
            CString line;
            line.Format(_T("%d,%s,%s,%.0f,%.0f,%.4f,%d\n"),
                        (int)i + 1, (LPCTSTR)r.code, (LPCTSTR)CsvEscape(r.name),
                        r.turnover, r.price, r.tickCost * 100.0, r.rows);
            f.WriteString(line);
        }
        f.Close();
    }
    catch (CFileException* e) { e->Delete(); return; }

    Log::Write(_T("===== 1단계 끝 ====="));
    Log::Write(_T("살펴본 종목 %d, 통과 %d"), (int)m_results.size(), (int)passed.size());
    Log::Write(_T("결과 파일: %s"), (LPCTSTR)PathUnder(Config::SYMBOLS_CSV));

    if (Config::MAX_SYMBOLS_FOR_BARS > 0 &&
        (int)passed.size() > Config::MAX_SYMBOLS_FOR_BARS)
    {
        Log::Warn(_T("2단계는 위에서부터 %d 개만 받습니다. Config.h 의 MAX_SYMBOLS_FOR_BARS 값입니다."),
                  Config::MAX_SYMBOLS_FOR_BARS);
    }
}

CString CUniverseJob::Progress() const
{
    CString s;
    s.Format(_T("%d / %d"), (int)m_index, (int)m_targets.size());
    return s;
}


// =====================================================================
//  프로그램 2 : 1분봉을 받을 수 있는 최대치까지
// =====================================================================

CMinuteJob::CMinuteJob(CKiwoomApi* api)
    : m_api(api), m_index(0), m_prevNext(0), m_pages(0), m_skipped(0), m_done(false)
{
}

bool CMinuteJob::AlreadyDone(const CString& code) const
{
    for (size_t i = 0; i < m_finished.size(); ++i)
        if (m_finished[i] == code) return true;
    return false;
}

bool CMinuteJob::Begin()
{
    m_symbols.clear();
    m_finished.clear();
    m_bars.clear();
    m_index    = 0;
    m_prevNext = 0;
    m_pages    = 0;
    m_skipped  = 0;
    m_done     = false;

    EnsureDir(PathUnder(Config::BARS_DIR));

    // 1단계 결과 읽기
    CString symPath = PathUnder(Config::SYMBOLS_CSV);
    if (!FileExistsAt(symPath))
    {
        Log::Error(_T("symbols.csv 가 없습니다. 1단계를 먼저 돌리세요."));
        return false;
    }

    CStdioFile f;
    try
    {
        if (!f.Open(symPath, CFile::modeRead | CFile::typeText))
        {
            Log::Error(_T("symbols.csv 를 못 열었습니다."));
            return false;
        }

        CString line;
        f.ReadString(line);                       // 머리글 버리기
        while (f.ReadString(line))
        {
            line.Trim();
            if (line.IsEmpty()) continue;

            std::vector<CString> cols = SplitCsvLine(line);
            if (cols.size() < 3) continue;

            Sym s;
            s.code = TrimAll(cols[1]);
            s.name = TrimAll(cols[2]);
            if (s.code.GetLength() == 6) m_symbols.push_back(s);
        }
        f.Close();
    }
    catch (CFileException* e) { e->Delete(); return false; }

    if (Config::MAX_SYMBOLS_FOR_BARS > 0 &&
        (int)m_symbols.size() > Config::MAX_SYMBOLS_FOR_BARS)
    {
        m_symbols.resize(Config::MAX_SYMBOLS_FOR_BARS);
    }

    // 이미 받은 종목은 건너뜁니다. 중간에 멈췄어도 이어서 할 수 있게요.
    CString manPath = PathUnder(Config::MANIFEST_CSV);
    if (FileExistsAt(manPath))
    {
        CStdioFile mf;
        try
        {
            if (mf.Open(manPath, CFile::modeRead | CFile::typeText))
            {
                CString line;
                mf.ReadString(line);
                while (mf.ReadString(line))
                {
                    std::vector<CString> cols = SplitCsvLine(line);
                    if (!cols.empty())
                    {
                        CString c = TrimAll(cols[0]);
                        if (c.GetLength() == 6) m_finished.push_back(c);
                    }
                }
                mf.Close();
            }
        }
        catch (CFileException* e) { e->Delete(); }
    }

    int todo = 0;
    for (size_t i = 0; i < m_symbols.size(); ++i)
        if (!AlreadyDone(m_symbols[i].code)) ++todo;

    Log::Write(_T("2단계 준비 완료. 대상 %d 종목, 이미 받은 것 %d, 이번에 받을 것 %d"),
               (int)m_symbols.size(), (int)m_symbols.size() - todo, todo);

    if (todo == 0)
    {
        Log::Write(_T("받을 게 없습니다. 다시 받으려면 manifest.csv 를 지우세요."));
        m_done = true;
        return false;
    }
    return true;
}

int CMinuteJob::PlannedRequests() const
{
    int todo = 0;
    for (size_t i = 0; i < m_symbols.size(); ++i)
        if (!AlreadyDone(m_symbols[i].code)) ++todo;

    // 한 종목당 대략 몇 장이 올지는 받아 봐야 압니다.
    // 160일치 (약 62,000봉) 를 900개씩 나누면 70장쯤입니다.
    return todo * 70;
}

void CMinuteJob::SendNext()
{
    if (m_done) return;

    // 이미 받은 종목은 넘어갑니다.
    while (m_index < m_symbols.size() && AlreadyDone(m_symbols[m_index].code))
    {
        ++m_index;
        ++m_skipped;
    }

    if (m_index >= m_symbols.size())
    {
        Log::Write(_T("===== 2단계 끝 ====="));
        Log::Write(_T("건너뛴 종목 %d"), m_skipped);
        m_done = true;
        return;
    }

    const Sym& s = m_symbols[m_index];

    CString tick;
    tick.Format(_T("%d"), Config::MINUTE_TICK_RANGE);

    m_api->SetInput(_T("종목코드"),     s.code);
    m_api->SetInput(_T("틱범위"),       tick);
    m_api->SetInput(_T("수정주가구분"), _T("1"));

    CString rq;
    rq.Format(_T("분봉_%s"), (LPCTSTR)s.code);
    m_api->Request(rq, Config::TR_MINUTE, m_prevNext, Config::SCREEN_NO);
}

void CMinuteJob::OnTr(const TrContext& ctx)
{
    if (m_done) return;
    if (ctx.trCode.CompareNoCase(Config::TR_MINUTE) != 0) return;
    if (m_index >= m_symbols.size()) return;

    long n = m_api->RepeatCount(ctx.trCode, REC_MINUTE);
    for (long i = 0; i < n; ++i)
    {
        MinuteBar b;
        b.stamp  = m_api->Data(ctx.trCode, REC_MINUTE, i, F_STAMP);
        b.open   = fabs(ParseNum(m_api->Data(ctx.trCode, REC_MINUTE, i, F_OPEN)));
        b.high   = fabs(ParseNum(m_api->Data(ctx.trCode, REC_MINUTE, i, F_HIGH)));
        b.low    = fabs(ParseNum(m_api->Data(ctx.trCode, REC_MINUTE, i, F_LOW)));
        b.close  = fabs(ParseNum(m_api->Data(ctx.trCode, REC_MINUTE, i, F_CLOSE)));
        b.volume = fabs(ParseNum(m_api->Data(ctx.trCode, REC_MINUTE, i, F_VOLUME)));

        if (b.stamp.GetLength() >= 12) m_bars.push_back(b);
    }

    ++m_pages;

    bool more = (ctx.prevNext == _T("2"));
    if (more && n > 0 && m_pages < Config::MAX_PAGES_PER_SYMBOL)
    {
        m_prevNext = 2;       // 같은 종목 다음 장
        return;
    }

    FinishSymbol();
}

void CMinuteJob::FinishSymbol()
{
    const Sym& s = m_symbols[m_index];

    std::reverse(m_bars.begin(), m_bars.end());   // 오래된 것부터

    CString path;
    path.Format(_T("%s\\%s.csv"), (LPCTSTR)PathUnder(Config::BARS_DIR), (LPCTSTR)s.code);

    CString from = m_bars.empty() ? CString(_T("")) : m_bars.front().stamp;
    CString to   = m_bars.empty() ? CString(_T("")) : m_bars.back().stamp;

    CStdioFile f;
    bool ok = false;
    try
    {
        if (f.Open(path, CFile::modeCreate | CFile::modeWrite | CFile::typeText))
        {
            f.WriteString(_T("stamp,open,high,low,close,volume\n"));
            for (size_t i = 0; i < m_bars.size(); ++i)
            {
                const MinuteBar& b = m_bars[i];
                CString line;
                line.Format(_T("%s,%.0f,%.0f,%.0f,%.0f,%.0f\n"),
                            (LPCTSTR)b.stamp, b.open, b.high, b.low, b.close, b.volume);
                f.WriteString(line);
            }
            f.Close();
            ok = true;
        }
    }
    catch (CFileException* e) { e->Delete(); }

    if (!ok) Log::Error(_T("%s 파일 쓰기 실패"), (LPCTSTR)s.code);

    CheckIntegrity(s.code, m_bars);
    AppendManifest(s.code, (int)m_bars.size(), from, to, ok ? _T("ok") : _T("write_fail"));

    Log::Write(_T("[%d/%d] %s %s  %d 봉  %s ~ %s  (%d 장)"),
               (int)m_index + 1, (int)m_symbols.size(),
               (LPCTSTR)s.code, (LPCTSTR)s.name,
               (int)m_bars.size(), (LPCTSTR)from, (LPCTSTR)to, m_pages);

    m_bars.clear();
    m_prevNext = 0;
    m_pages    = 0;
    ++m_index;
}

void CMinuteJob::CheckIntegrity(const CString& code, const std::vector<MinuteBar>& bars)
{
    if (bars.empty()) { Log::Warn(_T("%s : 받은 봉이 없습니다."), (LPCTSTR)code); return; }

    int badShape = 0;
    for (size_t i = 0; i < bars.size(); ++i)
    {
        const MinuteBar& b = bars[i];
        double hi = (b.open > b.close) ? b.open : b.close;
        double lo = (b.open < b.close) ? b.open : b.close;
        if (b.high < hi - 0.5 || b.low > lo + 0.5) ++badShape;
    }
    if (badShape > 0)
        Log::Warn(_T("%s : 고가/저가가 앞뒤 안 맞는 봉 %d 개"), (LPCTSTR)code, badShape);

    // 날짜별 봉 개수와 하루 사이 가격 점프를 봅니다.
    CString curDay;
    int     dayCount   = 0;
    int     shortDays  = 0;
    int     days       = 0;
    double  lastClose  = 0.0;
    int     bigGaps    = 0;

    for (size_t i = 0; i < bars.size(); ++i)
    {
        CString day = bars[i].stamp.Left(8);
        if (day != curDay)
        {
            if (!curDay.IsEmpty())
            {
                ++days;
                if (dayCount < Config::EXPECTED_BARS_PER_DAY - 10) ++shortDays;
            }
            if (lastClose > 0.0)
            {
                double ratio = fabs(bars[i].open - lastClose) / lastClose;
                if (ratio > Config::GAP_WARN_RATIO) ++bigGaps;
            }
            curDay   = day;
            dayCount = 0;
        }
        ++dayCount;
        lastClose = bars[i].close;
    }
    if (!curDay.IsEmpty()) ++days;

    if (shortDays > 0)
        Log::Warn(_T("%s : 봉이 모자란 날 %d / %d"), (LPCTSTR)code, shortDays, days);

    if (bigGaps > 0)
        Log::Warn(_T("%s : 전일 종가 대비 %.0f%% 넘게 튄 날 %d 곳. 액면분할일 수 있습니다."),
                  (LPCTSTR)code, Config::GAP_WARN_RATIO * 100.0, bigGaps);
}

void CMinuteJob::AppendManifest(const CString& code, int rows,
                                const CString& from, const CString& to, const CString& note)
{
    CString path = PathUnder(Config::MANIFEST_CSV);
    bool isNew = !FileExistsAt(path);

    CStdioFile f;
    try
    {
        if (!f.Open(path, CFile::modeCreate | CFile::modeNoTruncate |
                          CFile::modeWrite | CFile::typeText))
            return;

        f.SeekToEnd();
        if (isNew) f.WriteString(_T("code,rows,from,to,note,fetched_at\n"));

        CString line;
        line.Format(_T("%s,%d,%s,%s,%s,%s\n"),
                    (LPCTSTR)code, rows, (LPCTSTR)from, (LPCTSTR)to,
                    (LPCTSTR)note, (LPCTSTR)TodayYmd());
        f.WriteString(line);
        f.Close();
    }
    catch (CFileException* e) { e->Delete(); }
}

CString CMinuteJob::Progress() const
{
    CString s;
    s.Format(_T("%d / %d  (이번 종목 %d 장)"),
             (int)m_index, (int)m_symbols.size(), m_pages);
    return s;
}

// =====================================================================
//  한도 재보기
// =====================================================================

int CProbeJob::Config_MaxPages() { return Config::MAX_PAGES_PER_SYMBOL; }

CProbeJob::CProbeJob(CKiwoomApi* api, LPCTSTR code)
    : m_api(api), m_code(code), m_prevNext(0), m_pages(0), m_rows(0), m_done(false)
{
}

bool CProbeJob::Begin()
{
    m_prevNext = 0;
    m_pages    = 0;
    m_rows     = 0;
    m_oldest.Empty();
    m_newest.Empty();
    m_done     = false;

    Log::Write(_T("%s 한 종목으로 1분봉이 과거 어디까지 오는지 재봅니다."), (LPCTSTR)m_code);
    return true;
}

void CProbeJob::SendNext()
{
    if (m_done) return;

    CString tick;
    tick.Format(_T("%d"), Config::MINUTE_TICK_RANGE);

    m_api->SetInput(_T("종목코드"),     m_code);
    m_api->SetInput(_T("틱범위"),       tick);
    m_api->SetInput(_T("수정주가구분"), _T("1"));

    m_api->Request(_T("한도측정"), Config::TR_MINUTE, m_prevNext, Config::SCREEN_NO);
}

void CProbeJob::OnTr(const TrContext& ctx)
{
    if (m_done) return;
    if (ctx.trCode.CompareNoCase(Config::TR_MINUTE) != 0) return;

    long n = m_api->RepeatCount(ctx.trCode, REC_MINUTE);
    for (long i = 0; i < n; ++i)
    {
        CString stamp = m_api->Data(ctx.trCode, REC_MINUTE, i, F_STAMP);
        if (stamp.GetLength() < 12) continue;

        ++m_rows;
        if (m_newest.IsEmpty() || stamp > m_newest) m_newest = stamp;
        if (m_oldest.IsEmpty() || stamp < m_oldest) m_oldest = stamp;
    }

    ++m_pages;
    Log::Write(_T("%d 장째, 누적 %d 봉, 가장 오래된 시각 %s"),
               m_pages, m_rows, (LPCTSTR)m_oldest);

    bool more = (ctx.prevNext == _T("2"));
    if (more && n > 0 && m_pages < Config::MAX_PAGES_PER_SYMBOL)
    {
        m_prevNext = 2;
        return;
    }

    Log::Write(_T("===== 한도 측정 결과 ====="));
    Log::Write(_T("종목 %s"), (LPCTSTR)m_code);
    Log::Write(_T("받은 봉 %d 개, 연속조회 %d 장"), m_rows, m_pages);
    Log::Write(_T("기간 %s ~ %s"), (LPCTSTR)m_oldest, (LPCTSTR)m_newest);
    Log::Write(_T("하루 390봉으로 치면 약 %d 거래일입니다."),
               m_rows / Config::EXPECTED_BARS_PER_DAY);
    Log::Write(_T("이 값이 한 종목당 받을 수 있는 최대치입니다."));

    if (!more)
        Log::Write(_T("더 줄 데이터가 없다고 서버가 알려 왔습니다. 이게 진짜 한도입니다."));
    else
        Log::Warn(_T("안전장치(%d 장)에 걸려 멈췄습니다. Config.h 의 MAX_PAGES_PER_SYMBOL 을 늘리면 더 받힙니다."),
                  Config::MAX_PAGES_PER_SYMBOL);

    m_done = true;
}

CString CProbeJob::Progress() const
{
    CString s;
    s.Format(_T("%d 장 / %d 봉"), m_pages, m_rows);
    return s;
}
