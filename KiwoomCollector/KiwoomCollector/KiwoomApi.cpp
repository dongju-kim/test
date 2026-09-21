#include "pch.h"
#include "KiwoomApi.h"
#include "Log.h"

// ---------------------------------------------------------------------
// 아래 한 줄이 이 파일의 유일한 준비물입니다.
//
// Visual Studio 에서
//   [프로젝트] > [클래스 추가] > [ActiveX 컨트롤에서 MFC 클래스]
//   에서 "KHOpenAPI Control" 을 고르면 래퍼 클래스가 만들어집니다.
// 이미 다른 프로젝트에 있으면 그 두 파일을 복사해 오면 됩니다.
// 클래스 이름이 다르면 아래 두 줄만 고치세요.
// ---------------------------------------------------------------------
#include "khopenapictrl.h"
typedef CKhopenapictrl KiwoomCtrl;

static KiwoomCtrl* Ctrl(void* p) { return reinterpret_cast<KiwoomCtrl*>(p); }

CKiwoomApi::CKiwoomApi() : m_ocx(NULL), m_listener(NULL) {}
CKiwoomApi::~CKiwoomApi() {}

void CKiwoomApi::Attach(void* ocxControl, IKiwoomListener* listener)
{
    m_ocx      = ocxControl;
    m_listener = listener;
}

bool CKiwoomApi::Login()
{
    if (!m_ocx) { Log::Error(_T("OCX 가 붙어 있지 않습니다.")); return false; }
    long r = Ctrl(m_ocx)->CommConnect();
    Log::Write(_T("로그인 창을 띄웠습니다. 반환값 %ld"), r);
    return r == 0;
}

bool CKiwoomApi::IsConnected()
{
    if (!m_ocx) return false;
    return Ctrl(m_ocx)->GetConnectState() == 1;
}

std::vector<CString> CKiwoomApi::GetCodeList(LPCTSTR market)
{
    std::vector<CString> out;
    if (!m_ocx) return out;

    // 여섯 자리씩 ';' 로 이어진 한 덩어리로 옵니다.
    CString all = Ctrl(m_ocx)->GetCodeListByMarket(market);

    int pos = 0;
    while (pos < all.GetLength())
    {
        CString tok = all.Tokenize(_T(";"), pos);
        tok.Trim();
        if (tok.GetLength() == 6) out.push_back(tok);
        if (pos < 0) break;
    }
    return out;
}

CString CKiwoomApi::GetName(LPCTSTR code)
{
    if (!m_ocx) return _T("");
    CString n = Ctrl(m_ocx)->GetMasterCodeName(code);
    n.Trim();
    return n;
}

CString CKiwoomApi::GetStockState(LPCTSTR code)
{
    if (!m_ocx) return _T("");
    CString s = Ctrl(m_ocx)->GetMasterStockState(code);
    s.Trim();
    return s;
}

void CKiwoomApi::SetInput(LPCTSTR id, LPCTSTR value)
{
    if (!m_ocx) return;
    Ctrl(m_ocx)->SetInputValue(id, value);
}

long CKiwoomApi::Request(LPCTSTR rqName, LPCTSTR trCode, long prevNext, LPCTSTR screenNo)
{
    if (!m_ocx) return -1;
    return Ctrl(m_ocx)->CommRqData(rqName, trCode, prevNext, screenNo);
}

long CKiwoomApi::RepeatCount(LPCTSTR trCode, LPCTSTR recordName)
{
    if (!m_ocx) return 0;
    return Ctrl(m_ocx)->GetRepeatCnt(trCode, recordName);
}

CString CKiwoomApi::Data(LPCTSTR trCode, LPCTSTR recordName, long index, LPCTSTR itemName)
{
    if (!m_ocx) return _T("");
    CString v = Ctrl(m_ocx)->GetCommData(trCode, recordName, index, itemName);
    v.Trim();
    return v;
}

void CKiwoomApi::DisconnectScreen(LPCTSTR screenNo)
{
    if (!m_ocx) return;
    Ctrl(m_ocx)->DisconnectRealData(screenNo);
}

void CKiwoomApi::RaiseLogin(long errCode)
{
    if (m_listener) m_listener->OnLoginResult(errCode);
}

void CKiwoomApi::RaiseTr(LPCTSTR scrNo, LPCTSTR rqName, LPCTSTR trCode,
                         LPCTSTR recordName, LPCTSTR prevNext)
{
    if (!m_listener) return;

    TrContext ctx;
    ctx.screenNo   = scrNo;
    ctx.rqName     = rqName;
    ctx.trCode     = trCode;
    ctx.recordName = recordName;
    ctx.prevNext   = CString(prevNext).Trim();
    m_listener->OnTrReceived(ctx);
}

void CKiwoomApi::RaiseMsg(LPCTSTR rqName, LPCTSTR msg)
{
    if (m_listener) m_listener->OnServerMsg(rqName, msg);
}
