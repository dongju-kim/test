@echo off
setlocal
rem ---------------------------------------------------------------
rem  build.bat - double-click to build with Visual Studio 2015
rem  Result goes to build.log in this folder. Send that file to Claude.
rem ---------------------------------------------------------------
set "VS=C:\Program Files (x86)\Microsoft Visual Studio 14.0\Common7\IDE\devenv.exe"
set "SLN=%~dp0KiwoomCollector.sln"
set "LOG=%~dp0build.log"

if not exist "%VS%" (
    echo devenv.exe not found:
    echo   %VS%
    echo Open Visual Studio manually instead.
    pause
    exit /b 1
)

echo Building Release ^| Win32 ...  (takes a minute)
"%VS%" "%SLN%" /Rebuild "Release|Win32" /Out "%LOG%"

echo.
echo ================= build.log =================
type "%LOG%"
echo =============================================
echo.
if exist "%~dp0KiwoomCollector\Release\KiwoomCollector.exe" (
    echo SUCCESS:  KiwoomCollector\Release\KiwoomCollector.exe
) else if exist "%~dp0Release\KiwoomCollector.exe" (
    echo SUCCESS:  Release\KiwoomCollector.exe
) else (
    echo FAILED.  Send build.log to Claude.
)
start notepad "%LOG%"
pause
