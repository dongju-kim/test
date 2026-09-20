#pragma once

// 이 프로젝트는 미리 컴파일된 헤더를 쓰지 않습니다.
// 버전마다 설정이 달라서 문제가 생기기 쉬워 일부러 껐습니다.
// (VS 2015 는 stdafx.h, 2017 부터는 pch.h 를 쓰는데 이러면 상관없습니다.)

#ifndef VC_EXTRALEAN
#define VC_EXTRALEAN
#endif

#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0601      // Windows 7 이상
#endif

#define _AFX_ALL_WARNINGS

#include <afxwin.h>
#include <afxext.h>
#include <afxdisp.h>
#include <afxdtctl.h>
#ifndef _AFX_NO_AFXCMN_SUPPORT
#include <afxcmn.h>
#endif
#include <afxcontrolbars.h>
#include <afxocc.h>
#include <afxdialogex.h>
