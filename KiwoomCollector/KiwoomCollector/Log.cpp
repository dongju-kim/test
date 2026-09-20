#include "pch.h"
#include "Log.h"
#include "Util.h"
#include "Config.h"
#include <stdarg.h>

namespace
{
    CLogSink*  g_sink = NULL;
    CStdioFile g_file;
    bool       g_open = false;
    CCriticalSection g_lock;

    void Emit(LPCTSTR level, LPCTSTR body)
    {
        SYSTEMTIME st;
        ::GetLocalTime(&st);

        CString line;
        line.Format(_T("%02d:%02d:%02d [%s] %s"),
                    st.wHour, st.wMinute, st.wSecond, level, body);

        CSingleLock guard(&g_lock, TRUE);

        if (g_open)
        {
            try
            {
                g_file.WriteString(line);
                g_file.WriteString(_T("\n"));
                g_file.Flush();
            }
            catch (CFileException* e) { e->Delete(); }
        }
        if (g_sink) g_sink->OnLogLine(line);
    }

    void EmitV(LPCTSTR level, LPCTSTR fmt, va_list args)
    {
        CString body;
        body.FormatV(fmt, args);
        Emit(level, body);
    }
}

void Log::Init(CLogSink* sink)
{
    g_sink = sink;

    EnsureDir(PathUnder(Config::LOG_DIR));

    CString path;
    path.Format(_T("%s\\run_%s.log"), (LPCTSTR)PathUnder(Config::LOG_DIR), (LPCTSTR)TodayYmd());

    try
    {
        // 이어쓰기. 하루치를 한 파일에 모읍니다.
        if (g_file.Open(path, CFile::modeCreate | CFile::modeNoTruncate |
                              CFile::modeWrite | CFile::typeText))
        {
            g_file.SeekToEnd();
            g_open = true;
        }
    }
    catch (CFileException* e) { e->Delete(); g_open = false; }

    Write(_T("---- 시작 ----"));
}

void Log::Close()
{
    CSingleLock guard(&g_lock, TRUE);
    if (g_open) { try { g_file.Close(); } catch (CFileException* e) { e->Delete(); } g_open = false; }
    g_sink = NULL;
}

void Log::Write(LPCTSTR fmt, ...) { va_list a; va_start(a, fmt); EmitV(_T("정보"), fmt, a); va_end(a); }
void Log::Warn (LPCTSTR fmt, ...) { va_list a; va_start(a, fmt); EmitV(_T("주의"), fmt, a); va_end(a); }
void Log::Error(LPCTSTR fmt, ...) { va_list a; va_start(a, fmt); EmitV(_T("실패"), fmt, a); va_end(a); }
