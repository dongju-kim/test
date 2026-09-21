#pragma once
#include "Resource.h"
#include "KiwoomApi.h"
#include "Jobs.h"
#include "Log.h"

// ---------------------------------------------------------------------
// IDE 가 만들어 준 OCX 래퍼 헤더. 이름이 다르면 이 줄을 고치세요.
// ---------------------------------------------------------------------
#include "khopenapictrl.h"

class CMainDlg : public CDialogEx, public IKiwoomListener, public CLogSink
{
public:
    CMainDlg(CWnd* pParent = NULL);
    enum { IDD = IDD_MAIN_DIALOG };

protected:
    void DoDataExchange(CDataExchange* pDX) override;
    BOOL OnInitDialog() override;
    void OnCancel() override;

    // IKiwoomListener
    void OnLoginResult(long errCode) override;
    void OnTrReceived(const TrContext& ctx) override;
    void OnServerMsg(const CString& rqName, const CString& msg) override;

    // CLogSink
    void OnLogLine(const CString& line) override;

    afx_msg void OnBnClickedLogin();
    afx_msg void OnBnClickedProbe();
    afx_msg void OnBnClickedStep1();
    afx_msg void OnBnClickedStep2();
    afx_msg void OnBnClickedStop();
    afx_msg void OnBnClickedOpenDir();
    afx_msg void OnTimer(UINT_PTR nIDEvent);
    afx_msg void OnDestroy();

    // OCX 이벤트
    void OnEventConnectKh(long nErrCode);
    void OnReceiveTrDataKh(LPCTSTR sScrNo, LPCTSTR sRQName, LPCTSTR sTrCode,
                           LPCTSTR sRecordName, LPCTSTR sPrevNext, long nDataLength,
                           LPCTSTR sErrorCode, LPCTSTR sMessage, LPCTSTR sSplmMsg);
    void OnReceiveMsgKh(LPCTSTR sScrNo, LPCTSTR sRQName,
                        LPCTSTR sTrCode, LPCTSTR sMsg);

    DECLARE_MESSAGE_MAP()
    DECLARE_EVENTSINK_MAP()

private:
    void StartJob(IJob* job);
    void StopJob(LPCTSTR why);
    void ScheduleNext(int delayMs);
    void SetStatus(LPCTSTR text);
    void EnableButtons(bool idle);

    CKhopenapictrl m_kh;
    CKiwoomApi     m_api;
    CListBox       m_log;
    CEdit          m_probeCode;

    IJob* m_job;
    bool  m_connected;
    int   m_waitMs;        // 다음 요청까지 쉴 시간
    ULONGLONG m_startTick;
};
