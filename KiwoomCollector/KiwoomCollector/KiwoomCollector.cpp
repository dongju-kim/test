#include "pch.h"
#include "KiwoomCollector.h"
#include "MainDlg.h"
#include <locale.h>

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

    // 유니코드 빌드에서 CStdioFile 이 한글을 파일에 쓰려면 로캘이 잡혀 있어야 합니다.
    // 안 잡으면 종목명이 물음표로 깨집니다. 결과 CSV 는 CP949(한국어 윈도우 기본) 입니다.
    _tsetlocale(LC_ALL, _T(""));
    SetRegistryKey(_T("NullimCollector"));

    CMainDlg dlg;
    m_pMainWnd = &dlg;
    dlg.DoModal();

    return FALSE;
}
