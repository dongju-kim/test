#pragma once

// =====================================================================
// Log.h - 화면과 파일에 동시에 기록합니다.
//         오래 도는 작업이라 로그가 없으면 무슨 일이 있었는지 모릅니다.
// =====================================================================

class CLogSink
{
public:
    virtual ~CLogSink() {}
    virtual void OnLogLine(const CString& line) = 0;   // 화면에 한 줄
};

namespace Log
{
    void Init(CLogSink* sink);          // 프로그램 시작 때 한 번
    void Close();
    void Write(LPCTSTR fmt, ...);       // 보통 기록
    void Warn(LPCTSTR fmt, ...);        // 주의
    void Error(LPCTSTR fmt, ...);       // 실패
}
