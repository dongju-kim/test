#pragma once
// =====================================================================
// mfc_stub.h - 리눅스에서 문법 검사와 단위 테스트를 하려고 만든 가짜 MFC.
//              Windows 빌드에는 절대 들어가지 않습니다.
//              (pch.h 에서 LINUX_SYNTAX_CHECK 일 때만 포함합니다)
// =====================================================================
#include <string>
#include <vector>
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <cmath>
#include <algorithm>
#include <sys/stat.h>
#include <unistd.h>

typedef char            TCHAR;
typedef const char*     LPCTSTR;
typedef char*           LPTSTR;
typedef int             BOOL;
typedef unsigned int    UINT;
typedef unsigned int    DWORD;   // 윈도우 DWORD 는 32비트입니다. unsigned long 이면 리눅스에서 8바이트라 어긋납니다.
typedef long            LONG;
typedef unsigned short  WORD;
typedef unsigned long long ULONGLONG;
typedef unsigned long   UINT_PTR;
#define TRUE  1
#define FALSE 0
#define _T(x) x
#define _countof(a) (sizeof(a)/sizeof((a)[0]))
#define UNREFERENCED_PARAMETER(p) (void)(p)

inline int    _ttoi(LPCTSTR s)  { return atoi(s); }
inline double _tstof(LPCTSTR s) { return atof(s); }

// ---------------------------------------------------------------- CString
class CString
{
public:
    std::string s;
    CString() {}
    CString(const char* p) : s(p ? p : "") {}
    CString(const std::string& v) : s(v) {}

    operator LPCTSTR() const { return s.c_str(); }
    int  GetLength() const   { return (int)s.size(); }
    bool IsEmpty() const     { return s.empty(); }
    void Empty()             { s.clear(); }
    char operator[](int i) const { return s[(size_t)i]; }

    CString& operator+=(const CString& o) { s += o.s; return *this; }
    CString& operator+=(const char* o)    { s += o;   return *this; }
    CString& operator+=(char c)           { s += c;   return *this; }

    CString& Trim()
    {
        size_t b = s.find_first_not_of(" \t\r\n");
        size_t e = s.find_last_not_of(" \t\r\n");
        s = (b == std::string::npos) ? "" : s.substr(b, e - b + 1);
        return *this;
    }
    CString Left(int n) const  { return CString(s.substr(0, (size_t)std::min<int>(n, (int)s.size()))); }
    CString Right(int n) const
    {
        int k = std::min<int>(n, (int)s.size());
        return CString(s.substr(s.size() - (size_t)k));
    }
    CString Mid(int i) const { return (i >= (int)s.size()) ? CString() : CString(s.substr((size_t)i)); }
    CString Mid(int i, int n) const
    {
        if (i >= (int)s.size()) return CString();
        return CString(s.substr((size_t)i, (size_t)n));
    }
    int Find(const char* sub) const  { size_t p = s.find(sub); return p == std::string::npos ? -1 : (int)p; }
    int Find(char c) const           { size_t p = s.find(c);   return p == std::string::npos ? -1 : (int)p; }
    int ReverseFind(char c) const    { size_t p = s.rfind(c);  return p == std::string::npos ? -1 : (int)p; }
    int CompareNoCase(const char* o) const { return strcasecmp(s.c_str(), o); }

    void Replace(const char* a, const char* b)
    {
        std::string out; size_t i = 0, la = strlen(a);
        while (i < s.size())
        {
            size_t p = s.find(a, i);
            if (p == std::string::npos) { out += s.substr(i); break; }
            out += s.substr(i, p - i); out += b; i = p + la;
        }
        s = out;
    }
    void Remove(char c) { s.erase(std::remove(s.begin(), s.end(), c), s.end()); }

    CString Tokenize(const char* delims, int& iStart) const
    {
        if (iStart < 0) return CString();
        size_t b = s.find_first_not_of(delims, (size_t)iStart);
        if (b == std::string::npos) { iStart = -1; return CString(); }
        size_t e = s.find_first_of(delims, b);
        if (e == std::string::npos) { iStart = (int)s.size(); return CString(s.substr(b)); }
        iStart = (int)e + 1;
        return CString(s.substr(b, e - b));
    }

    void Format(const char* fmt, ...)
    { va_list a; va_start(a, fmt); FormatV(fmt, a); va_end(a); }

    void FormatV(const char* fmt, va_list a)
    {
        va_list c; va_copy(c, a);
        int n = vsnprintf(NULL, 0, fmt, c); va_end(c);
        if (n < 0) { s.clear(); return; }
        std::vector<char> buf((size_t)n + 1);
        vsnprintf(buf.data(), buf.size(), fmt, a);
        s.assign(buf.data(), (size_t)n);
    }
};
inline CString operator+(const CString& a, const CString& b) { return CString(a.s + b.s); }
inline CString operator+(const CString& a, const char* b)    { return CString(a.s + b); }
inline bool operator==(const CString& a, const CString& b) { return a.s == b.s; }
inline bool operator!=(const CString& a, const CString& b) { return a.s != b.s; }
inline bool operator==(const CString& a, const char* b)    { return a.s == b; }
inline bool operator!=(const CString& a, const char* b)    { return a.s != b; }
inline bool operator> (const CString& a, const CString& b) { return a.s >  b.s; }
inline bool operator< (const CString& a, const CString& b) { return a.s <  b.s; }

// ---------------------------------------------------------------- 파일
class CFileException { public: void Delete() { delete this; } };

class CFile
{
public:
    enum { modeRead = 1, modeWrite = 2, modeCreate = 4,
           modeNoTruncate = 8, typeText = 16 };
};

class CStdioFile : public CFile
{
public:
    FILE* f;
    CStdioFile() : f(NULL) {}
    ~CStdioFile() { if (f) fclose(f); }

    BOOL Open(LPCTSTR path, UINT flags)
    {
        const char* m = "r";
        if (flags & modeCreate) m = (flags & modeNoTruncate) ? "a+" : "w";
        else if (flags & modeWrite) m = "a+";
        f = fopen(path, m);
        return f != NULL;
    }
    BOOL ReadString(CString& line)
    {
        if (!f) return FALSE;
        char buf[8192];
        if (!fgets(buf, sizeof(buf), f)) return FALSE;
        size_t n = strlen(buf);
        while (n && (buf[n-1] == '\n' || buf[n-1] == '\r')) buf[--n] = 0;
        line = CString(buf);
        return TRUE;
    }
    void WriteString(LPCTSTR t) { if (f) fputs(t, f); }
    void SeekToEnd()            { if (f) fseek(f, 0, SEEK_END); }
    void Flush()                { if (f) fflush(f); }
    void Close()                { if (f) { fclose(f); f = NULL; } }
};

// ---------------------------------------------------------------- 동기화
class CCriticalSection { public: void Lock() {} void Unlock() {} };
class CSingleLock
{
public:
    CSingleLock(CCriticalSection*, BOOL) {}
};

// ---------------------------------------------------------------- Win32 흉내
struct SYSTEMTIME { WORD wYear, wMonth, wDayOfWeek, wDay, wHour, wMinute, wSecond, wMilliseconds; };
struct FILETIME   { DWORD dwLowDateTime, dwHighDateTime; };
union  ULARGE_INTEGER { struct { DWORD LowPart, HighPart; }; ULONGLONG QuadPart; };

inline void GetLocalTime(SYSTEMTIME* st)
{
    time_t t = time(NULL); struct tm lt; localtime_r(&t, &lt);
    st->wYear = (WORD)(lt.tm_year + 1900); st->wMonth = (WORD)(lt.tm_mon + 1);
    st->wDay = (WORD)lt.tm_mday; st->wHour = (WORD)lt.tm_hour;
    st->wMinute = (WORD)lt.tm_min; st->wSecond = (WORD)lt.tm_sec;
    st->wDayOfWeek = (WORD)lt.tm_wday; st->wMilliseconds = 0;
}
inline BOOL SystemTimeToFileTime(const SYSTEMTIME* st, FILETIME* ft)
{
    struct tm t = {}; t.tm_year = st->wYear - 1900; t.tm_mon = st->wMonth - 1;
    t.tm_mday = st->wDay; t.tm_isdst = -1;
    time_t s = timegm(&t);
    ULONGLONG v = ((ULONGLONG)s + 11644473600ULL) * 10000000ULL;
    ft->dwLowDateTime = (DWORD)(v & 0xFFFFFFFFULL);
    ft->dwHighDateTime = (DWORD)(v >> 32);
    return TRUE;
}
inline BOOL FileTimeToSystemTime(const FILETIME* ft, SYSTEMTIME* st)
{
    ULONGLONG v = ((ULONGLONG)ft->dwHighDateTime << 32) | ft->dwLowDateTime;
    time_t s = (time_t)(v / 10000000ULL - 11644473600ULL);
    struct tm t; gmtime_r(&s, &t);
    st->wYear = (WORD)(t.tm_year + 1900); st->wMonth = (WORD)(t.tm_mon + 1);
    st->wDay = (WORD)t.tm_mday; st->wHour = (WORD)t.tm_hour;
    st->wMinute = (WORD)t.tm_min; st->wSecond = (WORD)t.tm_sec;
    return TRUE;
}
inline DWORD GetModuleFileName(void*, LPTSTR buf, DWORD n)
{ snprintf(buf, n, "%s", "/tmp/KiwoomCollector.exe"); return (DWORD)strlen(buf); }
inline BOOL PathIsDirectory(LPCTSTR p) { struct stat st; return stat(p,&st)==0 && S_ISDIR(st.st_mode); }
inline BOOL CreateDirectory(LPCTSTR p, void*) { return mkdir(p, 0755) == 0; }
#define INVALID_FILE_ATTRIBUTES ((DWORD)-1)
#define FILE_ATTRIBUTE_DIRECTORY 0x10
inline DWORD GetFileAttributes(LPCTSTR p)
{
    struct stat st;
    if (stat(p, &st) != 0) return INVALID_FILE_ATTRIBUTES;
    return S_ISDIR(st.st_mode) ? FILE_ATTRIBUTE_DIRECTORY : 0;
}
#define MAX_PATH 260

// ---------------------------------------------------------------- 창과 대화상자
struct RECT { int left, top, right, bottom; };
struct CRect : RECT { CRect(int a=0,int b=0,int c=0,int d=0){ left=a; top=b; right=c; bottom=d; } };
struct HWND__ {}; typedef HWND__* HWND;
class CDataExchange {};

typedef unsigned char BYTE;
typedef long   DISPID;
typedef unsigned short VARTYPE;
typedef wchar_t* BSTR;
struct GUID { unsigned int Data1; unsigned short Data2, Data3; unsigned char Data4[8]; };
typedef GUID CLSID;
struct VARIANT { int vt; long lVal; };
class CCreateContext {};
#define DISPATCH_METHOD 1
#define VT_EMPTY   0
#define VT_I4      3
#define VT_BSTR    8
#define VT_VARIANT 12
#define DECLARE_DYNCREATE(cls)
#define IMPLEMENT_DYNCREATE(cls, base)

class CWnd
{
public:
    virtual ~CWnd() {}
    void InvokeHelper(DISPID, unsigned short, VARTYPE, void*, const BYTE*, ...) {}
    BOOL CreateControl(const CLSID&, LPCTSTR, DWORD, const RECT&, CWnd*, UINT,
                       CFile* = 0, BOOL = 0, BSTR = 0) { return TRUE; }
    HWND GetSafeHwnd() const { return (HWND)0; }
    BOOL EnableWindow(BOOL) { return TRUE; }
    void SetWindowText(LPCTSTR) {}
    void GetWindowText(CString& s) { s = CString("005930"); }
    UINT_PTR SetTimer(UINT_PTR id, UINT, void*) { return id; }
    BOOL KillTimer(UINT_PTR) { return TRUE; }
    CWnd* GetDlgItem(int) { static CWnd w; return &w; }
    void  SetDlgItemText(int, LPCTSTR) {}
    BOOL  CreateControl(LPCTSTR, LPCTSTR, DWORD, const CRect&, CWnd*, UINT) { return TRUE; }
};
inline BOOL IsWindow(HWND) { return TRUE; }

class CListBox : public CWnd
{
public:
    int  AddString(const CString&) { return 0; }
    void SetTopIndex(int) {}
    int  GetCount() const { return 0; }
    int  DeleteString(int) { return 0; }
};
class CEdit : public CWnd {};

class CDialogEx : public CWnd
{
public:
    CDialogEx(UINT = 0, CWnd* = 0) {}
    virtual BOOL OnInitDialog() { return TRUE; }
    virtual void DoDataExchange(CDataExchange*) {}
    virtual void OnCancel() {}
    virtual void OnTimer(UINT_PTR) {}
    virtual void OnDestroy() {}
    int  DoModal() { return 0; }
};

class CWinApp
{
public:
    CWnd* m_pMainWnd = 0;
    virtual ~CWinApp() {}
    virtual BOOL InitInstance() { return TRUE; }
    void SetRegistryKey(LPCTSTR) {}
};

#define afx_msg
#define DECLARE_MESSAGE_MAP()
#define DECLARE_EVENTSINK_MAP()
#define BEGIN_MESSAGE_MAP(theClass, base)   static void theClass##_MsgMapStub() {
#define END_MESSAGE_MAP()                   }
#define BEGIN_EVENTSINK_MAP(theClass, base) static void theClass##_SinkStub() {
#define END_EVENTSINK_MAP()                 }
#define ON_BN_CLICKED(id, fn)
#define ON_WM_TIMER()
#define ON_WM_DESTROY()
#define ON_EVENT(cls, id, dispid, fn, vts)
#define VTS_I4      "\x03"
#define VTS_BSTR    "\x08"
#define VTS_VARIANT "\x0c"
#define WS_CHILD 0x40000000
#define WS_VISIBLE 0x10000000
#define MB_YESNO 4
#define MB_ICONQUESTION 32
#define MB_ICONINFORMATION 64
#define IDYES 6
#define SW_SHOWNORMAL 1
inline int  AfxMessageBox(LPCTSTR, UINT = 0, UINT = 0) { return IDYES; }
inline BOOL AfxOleInit() { return TRUE; }
inline void AfxEnableControlContainer() {}
inline void DDX_Control(CDataExchange*, int, CWnd&) {}
inline ULONGLONG GetTickCount64() { return 0; }
inline void ShellExecute(void*, LPCTSTR, LPCTSTR, LPCTSTR, LPCTSTR, int) {}
