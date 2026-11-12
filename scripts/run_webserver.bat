@echo off
setlocal

rem Runs the Via Ludus web service and serves the frontend (Windows).
rem Extra arguments are passed through to the web service, for example:
rem     scripts\run_webserver.bat --port 9000

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"

cd /d "%REPO_ROOT%\backend-python" || exit /b 1

if defined PYTHONPATH set "PYTHONPATH=src;%PYTHONPATH%"
if not defined PYTHONPATH set "PYTHONPATH=src"

python -m web_service.main ^
	--frontend "%REPO_ROOT%\frontend" ^
	--host 0.0.0.0 ^
	--cors-origins http://localhost:8080 http://127.0.0.1:8080 ^
	%*
