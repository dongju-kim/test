#pragma once
#include "Resource.h"

class CKiwoomCollectorApp : public CWinApp
{
public:
    CKiwoomCollectorApp();
    BOOL InitInstance() override;
    DECLARE_MESSAGE_MAP()
};

extern CKiwoomCollectorApp theApp;
