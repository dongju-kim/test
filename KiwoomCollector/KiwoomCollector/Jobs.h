#pragma once
#include <vector>
#include "KiwoomApi.h"
#include "Util.h"

// =====================================================================
// Jobs.h - 오래 도는 작업 세 가지.
//
//   키움 TR 은 보내고 나서 나중에 답이 옵니다. 그래서 for 문으로
//   쭉 돌릴 수가 없습니다. 대신 이렇게 돌아갑니다.
//
//     Begin()  ->  SendNext()  ->  (답이 옴) OnTr()  ->  잠깐 쉬고
//                       ^                                    |
//                       +------------------------------------+
//
//   쉬는 시간은 Config::REQUEST_INTERVAL_MS 입니다.
// =====================================================================

class IJob
{
public:
    virtual ~IJob() {}
    virtual CString Name() const = 0;
    virtual bool    Begin() = 0;                  // 준비. 못 하면 false
    virtual void    SendNext() = 0;               // 요청 하나 보내기
    virtual void    OnTr(const TrContext& ctx) = 0;
    virtual bool    IsDone() const = 0;
    virtual CString Progress() const = 0;
    virtual void    Abort() = 0;
    virtual int     PlannedRequests() const = 0;  // 예상 요청 수
};

// ---------------------------------------------------------------------
// 프로그램 1 : 분봉 받을 종목 목록 만들기
//   전 종목 -> 이름과 코드로 거르기 -> 일봉 2년치 -> 거래대금과 호가비용
//   -> symbols.csv
// ---------------------------------------------------------------------
class CUniverseJob : public IJob
{
public:
    CUniverseJob(CKiwoomApi* api);

    CString Name() const override { return _T("1단계 · 종목 목록 만들기"); }
    bool    Begin() override;
    void    SendNext() override;
    void    OnTr(const TrContext& ctx) override;
    bool    IsDone() const override { return m_done; }
    CString Progress() const override;
    void    Abort() override { m_done = true; }
    int     PlannedRequests() const override { return (int)m_targets.size(); }

private:
    struct Target { CString code; CString name; };
    struct Result
    {
        CString code, name;
        double  turnover;   // 20일 평균 거래대금의 최댓값
        double  price;      // 그때 평균 종가
        double  tickCost;
        int     rows;
        bool    passed;
        CString reason;
    };

    void FinishSymbol();
    void WriteResults();

    CKiwoomApi*          m_api;
    std::vector<Target>  m_targets;
    std::vector<Result>  m_results;
    std::vector<DailyBar> m_bars;     // 지금 받는 중인 종목의 일봉
    size_t  m_index;
    long    m_prevNext;
    int     m_needRows;
    bool    m_done;
};

// ---------------------------------------------------------------------
// 프로그램 2 : 1분봉 받을 수 있는 최대치까지 받기
//   symbols.csv -> 종목마다 연속조회로 끝까지 -> data\bars\종목코드.csv
//   중간에 멈춰도 manifest.csv 를 보고 이어서 합니다.
// ---------------------------------------------------------------------
class CMinuteJob : public IJob
{
public:
    CMinuteJob(CKiwoomApi* api);

    CString Name() const override { return _T("2단계 · 1분봉 받기"); }
    bool    Begin() override;
    void    SendNext() override;
    void    OnTr(const TrContext& ctx) override;
    bool    IsDone() const override { return m_done; }
    CString Progress() const override;
    void    Abort() override { m_done = true; }
    int     PlannedRequests() const override;

private:
    struct Sym { CString code; CString name; };

    void FinishSymbol();
    void CheckIntegrity(const CString& code, const std::vector<MinuteBar>& bars);
    void AppendManifest(const CString& code, int rows,
                        const CString& from, const CString& to, const CString& note);
    bool AlreadyDone(const CString& code) const;

    CKiwoomApi*            m_api;
    std::vector<Sym>       m_symbols;
    std::vector<CString>   m_finished;    // manifest 에 이미 있는 종목
    std::vector<MinuteBar> m_bars;
    size_t  m_index;
    long    m_prevNext;
    int     m_pages;
    int     m_skipped;
    bool    m_done;
};

// ---------------------------------------------------------------------
// 한도 재보기 : 한 종목으로 분봉이 과거 어디까지 오는지 확인합니다.
//   본격적으로 받기 전에 이것부터 돌려 보세요. 10분이면 끝납니다.
// ---------------------------------------------------------------------
class CProbeJob : public IJob
{
public:
    CProbeJob(CKiwoomApi* api, LPCTSTR code);

    CString Name() const override { return _T("한도 재보기"); }
    bool    Begin() override;
    void    SendNext() override;
    void    OnTr(const TrContext& ctx) override;
    bool    IsDone() const override { return m_done; }
    CString Progress() const override;
    void    Abort() override { m_done = true; }
    int     PlannedRequests() const override { return Config_MaxPages(); }

private:
    static int Config_MaxPages();

    CKiwoomApi* m_api;
    CString     m_code;
    CString     m_oldest;
    CString     m_newest;
    long        m_prevNext;
    int         m_pages;
    int         m_rows;
    bool        m_done;
};
