#include "pch.h"
#include "Resource.h"
#include "MainDlg.h"
#include "Config.h"
#include "Util.h"
#ifndef LINUX_SYNTAX_CHECK
#include <shellapi.h>
#endif

static const UINT_PTR TIMER_NEXT = 1;

CMainDlg::CMainDlg(CWnd* pParent)
    : CDialogEx(IDD_MAIN_DIALOG, pParent)
    , m_job(NULL), m_connected(false)
    , m_waitMs(Config::REQUEST_INTERVAL_MS), m_startTick(0)
{
}

void CMainDlg::DoDataExchange(CDataExchange* pDX)
{
    CDialogEx::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_LIST_LOG, m_log);
    DDX_Control(pDX, IDC_EDIT_PROBECODE, m_probeCode);
}

BEGIN_MESSAGE_MAP(CMainDlg, CDialogEx)
    ON_BN_CLICKED(IDC_BTN_LOGIN,   &CMainDlg::OnBnClickedLogin)
    ON_BN_CLICKED(IDC_BTN_PROBE,   &CMainDlg::OnBnClickedProbe)
    ON_BN_CLICKED(IDC_BTN_STEP1,   &CMainDlg::OnBnClickedStep1)
    ON_BN_CLICKED(IDC_BTN_STEP2,   &CMainDlg::OnBnClickedStep2)
    ON_BN_CLICKED(IDC_BTN_STOP,    &CMainDlg::OnBnClickedStop)
    ON_BN_CLICKED(IDC_BTN_OPENDIR, &CMainDlg::OnBnClickedOpenDir)
    ON_WM_TIMER()
    ON_WM_DESTROY()
END_MESSAGE_MAP()

// ---------------------------------------------------------------------
// OCX 이벤트 연결.
//
// 앞의 숫자는 이벤트 번호입니다. 키움 OCX 는 보통 아래 순서입니다.
//   1 OnReceiveTrData   2 OnReceiveRealData   3 OnReceiveMsg
//   4 OnReceiveChejanData   5 OnEventConnect
//
// 만약 이벤트가 안 들어오면 Visual Studio 에서 OCX 를 고른 뒤
// 속성 창의 번개 모양(이벤트)에서 핸들러를 추가해 보세요.
// 그러면 아래와 같은 줄이 자동으로 만들어지는데, 번호가 다르면
// 자동으로 만들어진 쪽이 맞습니다.
// ---------------------------------------------------------------------
BEGIN_EVENTSINK_MAP(CMainDlg, CDialogEx)
    ON_EVENT(CMainDlg, IDC_KHOPENAPI, 1, CMainDlg::OnReceiveTrDataKh,
             VTS_BSTR VTS_BSTR VTS_BSTR VTS_BSTR VTS_BSTR VTS_I4 VTS_BSTR VTS_BSTR VTS_BSTR)
    ON_EVENT(CMainDlg, IDC_KHOPENAPI, 3, CMainDlg::OnReceiveMsgKh,
             VTS_BSTR VTS_BSTR VTS_BSTR VTS_BSTR)
    ON_EVENT(CMainDlg, IDC_KHOPENAPI, 5, CMainDlg::OnEventConnectKh, VTS_I4)
END_EVENTSINK_MAP()

BOOL CMainDlg::OnInitDialog()
{
    CDialogEx::OnInitDialog();

    Log::Init(this);

    EnsureDir(PathUnder(Config::DATA_DIR));
    EnsureDir(PathUnder(Config::DAILY_DIR));
    EnsureDir(PathUnder(Config::BARS_DIR));
    EnsureDir(PathUnder(Config::LOG_DIR));

    // OCX 를 코드로 만듭니다. 대화상자 리소스에 넣지 않아도 됩니다.
    if (!m_kh.CreateControl(_T("KHOPENAPI.KHOpenAPICtrl.1"), NULL,
                            WS_CHILD, CRect(0, 0, 0, 0), this, IDC_KHOPENAPI))
    {
        AfxMessageBox(_T("키움 OpenAPI 컨트롤을 만들지 못했습니다.\n\n")
                      _T("확인할 것\n")
                      _T(" 1. 영웅문과 OpenAPI 모듈이 설치돼 있는지\n")
                      _T(" 2. 이 프로그램이 32비트(x86)로 빌드됐는지\n")
                      _T(" 3. OpenAPI 사용 신청이 돼 있는지"));
    }

    m_api.Attach(&m_kh, this);
    m_probeCode.SetWindowText(_T("005930"));

    SetStatus(_T("로그인을 먼저 하세요."));
    EnableButtons(true);

    Log::Write(_T("요청 간격 %d ms 로 설정돼 있습니다. (Config.h)"), Config::REQUEST_INTERVAL_MS);
    return TRUE;
}

void CMainDlg::OnDestroy()
{
    KillTimer(TIMER_NEXT);
    if (m_job) { delete m_job; m_job = NULL; }
    Log::Close();
    CDialogEx::OnDestroy();
}

void CMainDlg::OnCancel()
{
    if (m_job)
    {
        if (AfxMessageBox(_T("작업이 돌고 있습니다. 정말 닫을까요?"),
                          MB_YESNO | MB_ICONQUESTION) != IDYES) return;
    }
    CDialogEx::OnCancel();
}

// ------------------------------------------------------------- 로그 출력
void CMainDlg::OnLogLine(const CString& line)
{
    if (!::IsWindow(m_log.GetSafeHwnd())) return;

    int n = m_log.AddString(line);
    m_log.SetTopIndex(n);

    // 너무 쌓이면 앞쪽을 지웁니다. 파일에는 다 남아 있습니다.
    while (m_log.GetCount() > 2000) m_log.DeleteString(0);
}

void CMainDlg::SetStatus(LPCTSTR text)
{
    SetDlgItemText(IDC_STATIC_STATUS, text);
}

void CMainDlg::EnableButtons(bool idle)
{
    GetDlgItem(IDC_BTN_LOGIN)->EnableWindow(idle ? TRUE : FALSE);
    GetDlgItem(IDC_BTN_PROBE)->EnableWindow(idle && m_connected);
    GetDlgItem(IDC_BTN_STEP1)->EnableWindow(idle && m_connected);
    GetDlgItem(IDC_BTN_STEP2)->EnableWindow(idle && m_connected);
    GetDlgItem(IDC_BTN_STOP)->EnableWindow(idle ? FALSE : TRUE);
}

// ------------------------------------------------------------- 버튼
void CMainDlg::OnBnClickedLogin()
{
    SetStatus(_T("로그인 창을 띄웠습니다."));
    m_api.Login();
}

void CMainDlg::OnBnClickedProbe()
{
    CString code;
    m_probeCode.GetWindowText(code);
    code.Trim();
    if (code.GetLength() != 6) { AfxMessageBox(_T("종목코드 6자리를 넣어 주세요.")); return; }

    StartJob(new CProbeJob(&m_api, code));
}

void CMainDlg::OnBnClickedStep1()
{
    if (AfxMessageBox(_T("1단계를 시작합니다.\n\n")
                      _T("전 종목의 일봉을 받아서 분봉 받을 목록을 만듭니다.\n")
                      _T("종목 수가 많아 시간이 꽤 걸립니다. 계속할까요?"),
                      MB_YESNO | MB_ICONINFORMATION) != IDYES) return;

    StartJob(new CUniverseJob(&m_api));
}

void CMainDlg::OnBnClickedStep2()
{
    if (AfxMessageBox(_T("2단계를 시작합니다.\n\n")
                      _T("symbols.csv 의 종목들 1분봉을 받을 수 있는 데까지 받습니다.\n")
                      _T("중간에 멈춰도 다시 누르면 이어서 합니다. 계속할까요?"),
                      MB_YESNO | MB_ICONINFORMATION) != IDYES) return;

    StartJob(new CMinuteJob(&m_api));
}

void CMainDlg::OnBnClickedStop()
{
    StopJob(_T("사용자가 중지했습니다."));
}

void CMainDlg::OnBnClickedOpenDir()
{
    ::ShellExecute(NULL, _T("open"), PathUnder(Config::DATA_DIR), NULL, NULL, SW_SHOWNORMAL);
}

// ------------------------------------------------------------- 작업 흐름
void CMainDlg::StartJob(IJob* job)
{
    if (m_job) { AfxMessageBox(_T("이미 도는 작업이 있습니다.")); delete job; return; }
    if (!m_connected) { AfxMessageBox(_T("로그인을 먼저 하세요.")); delete job; return; }

    m_job      = job;
    m_waitMs   = Config::REQUEST_INTERVAL_MS;
    m_startTick = ::GetTickCount64();

    Log::Write(_T("===== %s 시작 ====="), (LPCTSTR)job->Name());

    if (!m_job->Begin())
    {
        Log::Error(_T("시작하지 못했습니다."));
        delete m_job;
        m_job = NULL;
        EnableButtons(true);
        return;
    }

    int planned = m_job->PlannedRequests();
    if (planned > 0)
    {
        double hours = (double)planned * Config::REQUEST_INTERVAL_MS / 1000.0 / 3600.0;
        Log::Write(_T("예상 요청 %d 회, 대략 %.1f 시간 걸립니다."), planned, hours);
        if (hours > 6.0)
            Log::Warn(_T("오래 걸립니다. Config.h 의 MAX_SYMBOLS_FOR_BARS 를 줄이면 짧아집니다."));
    }

    EnableButtons(false);
    SetStatus(m_job->Name());
    m_job->SendNext();
}

void CMainDlg::StopJob(LPCTSTR why)
{
    KillTimer(TIMER_NEXT);
    if (m_job)
    {
        m_job->Abort();
        Log::Write(_T("%s"), why);

        ULONGLONG sec = (::GetTickCount64() - m_startTick) / 1000;
        Log::Write(_T("걸린 시간 %llu 분 %llu 초"), sec / 60, sec % 60);

        delete m_job;
        m_job = NULL;
    }
    m_api.DisconnectScreen(Config::SCREEN_NO);
    EnableButtons(true);
    SetStatus(_T("대기 중"));
}

void CMainDlg::ScheduleNext(int delayMs)
{
    KillTimer(TIMER_NEXT);
    SetTimer(TIMER_NEXT, delayMs, NULL);
}

void CMainDlg::OnTimer(UINT_PTR nIDEvent)
{
    if (nIDEvent == TIMER_NEXT)
    {
        KillTimer(TIMER_NEXT);
        if (m_job && !m_job->IsDone())
        {
            m_job->SendNext();
            if (m_job->IsDone()) StopJob(_T("작업이 끝났습니다."));
        }
        return;
    }
    CDialogEx::OnTimer(nIDEvent);
}

// ------------------------------------------------------------- 키움 이벤트
void CMainDlg::OnLoginResult(long errCode)
{
    if (errCode == 0)
    {
        m_connected = true;
        Log::Write(_T("로그인 성공"));
        SetStatus(_T("로그인됨. 먼저 [한도 재보기]를 돌려 보세요."));
    }
    else
    {
        m_connected = false;
        Log::Error(_T("로그인 실패. 오류코드 %ld"), errCode);
        SetStatus(_T("로그인 실패"));
    }
    EnableButtons(m_job == NULL);
}

void CMainDlg::OnTrReceived(const TrContext& ctx)
{
    if (!m_job) return;

    m_job->OnTr(ctx);
    SetStatus(m_job->Name() + _T("   ") + m_job->Progress());

    if (m_job->IsDone()) { StopJob(_T("작업이 끝났습니다.")); return; }

    ScheduleNext(m_waitMs);
    m_waitMs = Config::REQUEST_INTERVAL_MS;   // 한 번 늘렸던 건 원래대로
}

void CMainDlg::OnServerMsg(const CString& rqName, const CString& msg)
{
    Log::Write(_T("서버(%s): %s"), (LPCTSTR)rqName, (LPCTSTR)msg);

    // 조회 제한에 걸리면 한참 쉬었다 다시 합니다.
    if (msg.Find(_T("제한")) >= 0 || msg.Find(_T("초과")) >= 0)
    {
        m_waitMs = Config::RETRY_WAIT_MS;
        Log::Warn(_T("조회 제한 같습니다. %d 초 쉬었다 이어서 합니다."),
                  Config::RETRY_WAIT_MS / 1000);
    }
}

// ------------------------------------------------------------- OCX -> 우리
void CMainDlg::OnEventConnectKh(long nErrCode)
{
    m_api.RaiseLogin(nErrCode);
}

void CMainDlg::OnReceiveTrDataKh(LPCTSTR sScrNo, LPCTSTR sRQName, LPCTSTR sTrCode,
                                 LPCTSTR sRecordName, LPCTSTR sPrevNext, long nDataLength,
                                 LPCTSTR sErrorCode, LPCTSTR sMessage, LPCTSTR sSplmMsg)
{
    UNREFERENCED_PARAMETER(nDataLength);
    UNREFERENCED_PARAMETER(sErrorCode);
    UNREFERENCED_PARAMETER(sMessage);
    UNREFERENCED_PARAMETER(sSplmMsg);

    m_api.RaiseTr(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext);
}

void CMainDlg::OnReceiveMsgKh(LPCTSTR sScrNo, LPCTSTR sRQName,
                              LPCTSTR sTrCode, LPCTSTR sMsg)
{
    UNREFERENCED_PARAMETER(sScrNo);
    UNREFERENCED_PARAMETER(sTrCode);
    m_api.RaiseMsg(sRQName, sMsg);
}
