@echo off
rem Full Haiku classification of all 108,708 candidates (scheduled task "kt-p4-full", hourly).
rem Resumes where it stopped; a lock keeps a second copy out; exits when everything is labelled.
set PATH=C:\Users\17yuv\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe;%PATH%
cd /d C:\workplace\JiraAndLogs\AGENTS-WORKSHOP
echo === start %date% %time% >> data\p4_full\run.log
.venv\Scripts\python.exe -I analysis\p4_full.py run 4 >> data\p4_full\run.log 2>&1
echo === end %date% %time% >> data\p4_full\run.log
