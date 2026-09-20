#!/bin/sh
# 리눅스에서 문법 검사 + 단위 테스트.
# Windows 빌드와는 무관합니다. 가짜 MFC 헤더(mfc_stub.h)에 대고 컴파일합니다.
#   사용법:  sh tests/check.sh
set -e
cd "$(dirname "$0")/.."
FLAGS="-std=c++17 -Wall -Wextra -DLINUX_SYNTAX_CHECK -I. -Itests"

echo "== 문법 검사 =="
for f in Util.cpp Log.cpp KiwoomApi.cpp Jobs.cpp MainDlg.cpp KiwoomCollector.cpp; do
    printf "  %-24s" "$f"
    g++ $FLAGS -fsyntax-only "$f" && echo "통과"
done

echo
echo "== 단위 테스트 =="
g++ $FLAGS tests/test_main.cpp Util.cpp -o /tmp/kc_test
/tmp/kc_test
