#pragma once
// 리눅스 문법 검사용 가짜 OCX 래퍼. Windows 에서는 Visual Studio 가 진짜를 만들어 줍니다.
#include "mfc_stub.h"
class CKHOpenAPICtrl : public CWnd
{
public:
    long    CommConnect() { return 0; }
    long    GetConnectState() { return 1; }
    CString GetCodeListByMarket(LPCTSTR) { return CString(""); }
    CString GetMasterCodeName(LPCTSTR)   { return CString(""); }
    CString GetMasterStockState(LPCTSTR) { return CString(""); }
    void    SetInputValue(LPCTSTR, LPCTSTR) {}
    long    CommRqData(LPCTSTR, LPCTSTR, long, LPCTSTR) { return 0; }
    long    GetRepeatCnt(LPCTSTR, LPCTSTR) { return 0; }
    CString GetCommData(LPCTSTR, LPCTSTR, long, LPCTSTR) { return CString(""); }
    void    DisconnectRealData(LPCTSTR) {}
};
