@echo off
rem Resume the 2,000-PR pilot classification (scheduled task "kt-pilot-classify").
rem Finished PRs are skipped; the runner stops itself after 10 failures in a row.
set PATH=C:\Users\17yuv\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe;%PATH%
cd /d C:\workplace\JiraAndLogs\AGENTS-WORKSHOP
echo === scheduled start %date% %time% >> data\p1_classify\cc_run.log
.venv\Scripts\python.exe -I analysis\p1_classify_cc.py run 2000 3 >> data\p1_classify\cc_run.log 2>&1
.venv\Scripts\python.exe -I analysis\p1_classify_cc.py collect >> data\p1_classify\cc_run.log 2>&1
echo === finished %date% %time% >> data\p1_classify\cc_run.log
