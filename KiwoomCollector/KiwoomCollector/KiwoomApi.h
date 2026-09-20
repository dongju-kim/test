#pragma once
#include <vector>

// =====================================================================
// KiwoomApi.h - 키움 OCX 를 감싸는 얇은 층.
//   OCX 호출은 전부 KiwoomApi.cpp 안에만 있습니다.
//   다른 파일은 이 헤더만 보면 되고, OCX 래퍼 클래스 이름을 몰라도 됩니다.
// =====================================================================

// TR 응답이 왔을 때 넘어오는 정보
struct TrContext
{
    CString screenNo;
    CString rqName;      // 우리가 요청할 때 붙인 이름
    CString trCode;      // opt10081 / opt10080
    CString recordName;
    CString prevNext;    // "2" 이면 뒤에 더 있음 (연속조회 가능)
};

class IKiwoomListener
{
public:
    virtual ~IKiwoomListener() {}
    virtual void OnLoginResult(long errCode) = 0;
    virtual void OnTrReceived(const TrContext& ctx) = 0;
    virtual void OnServerMsg(const CString& rqName, const CString& msg) = 0;
};

class CKiwoomApi
{
public:
    CKiwoomApi();
    ~CKiwoomApi();

    // 대화상자가 시작할 때 한 번 불러 줍니다.
    // ctrl 은 IDE 가 만들어 준 OCX 래퍼 객체의 주소입니다.
    void Attach(void* ocxControl, IKiwoomListener* listener);

    bool Login();                 // 로그인 창을 띄웁니다
    bool IsConnected();

    // 종목 목록 (TR 아니라서 바로 돌아옵니다)
    std::vector<CString> GetCodeList(LPCTSTR market);   // "0"=코스피 "10"=코스닥
    CString GetName(LPCTSTR code);
    CString GetStockState(LPCTSTR code);                // 관리종목 등

    // TR 요청
    void  SetInput(LPCTSTR id, LPCTSTR value);
    long  Request(LPCTSTR rqName, LPCTSTR trCode, long prevNext, LPCTSTR screenNo);

    // TR 응답 읽기 (OnTrReceived 안에서만 씁니다)
    long    RepeatCount(LPCTSTR trCode, LPCTSTR recordName);
    CString Data(LPCTSTR trCode, LPCTSTR recordName, long index, LPCTSTR itemName);

    void DisconnectScreen(LPCTSTR screenNo);

    // 대화상자의 OCX 이벤트 핸들러가 이 셋을 그대로 불러 줍니다.
    void RaiseLogin(long errCode);
    void RaiseTr(LPCTSTR scrNo, LPCTSTR rqName, LPCTSTR trCode,
                 LPCTSTR recordName, LPCTSTR prevNext);
    void RaiseMsg(LPCTSTR rqName, LPCTSTR msg);

private:
    void*             m_ocx;
    IKiwoomListener*  m_listener;
};
