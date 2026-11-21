@echo off
rem Stratified classification (scheduled task "kt-p2-classify", hourly).
rem Resumes where it stopped; exits at once when all strata are finished.
set PATH=C:\Users\17yuv\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe;%PATH%
cd /d C:\workplace\JiraAndLogs\AGENTS-WORKSHOP
echo === start %date% %time% >> data\p2_classify\run.log
.venv\Scripts\python.exe -I analysis\p2_classify.py run 3 >> data\p2_classify\run.log 2>&1
echo === end %date% %time% >> data\p2_classify\run.log
