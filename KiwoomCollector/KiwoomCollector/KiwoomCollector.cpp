#include "pch.h"
#include "KiwoomCollector.h"
#include "MainDlg.h"

CKiwoomCollectorApp theApp;

BEGIN_MESSAGE_MAP(CKiwoomCollectorApp, CWinApp)
END_MESSAGE_MAP()

CKiwoomCollectorApp::CKiwoomCollectorApp() {}

BOOL CKiwoomCollectorApp::InitInstance()
{
    // OCX 를 쓰려면 반드시 필요합니다.
    if (!AfxOleInit())
    {
        AfxMessageBox(_T("OLE 를 초기화하지 못했습니다."));
        return FALSE;
    }
    AfxEnableControlContainer();

    CWinApp::InitInstance();
    SetRegistryKey(_T("NullimCollector"));

    CMainDlg dlg;
    m_pMainWnd = &dlg;
    dlg.DoModal();

    return FALSE;
}
