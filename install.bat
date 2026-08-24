@echo off
REM Elite Intel installer shim.
REM Double-click this file to run install.sh through Git Bash.
REM install.sh is the real installer; this file only launches it.

setlocal

set "SCRIPT_DIR=%~dp0"
set "BASH_EXE="

where bash >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "BASH_EXE=bash"
) else if exist "%ProgramFiles%\Git\bin\bash.exe" (
    set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
) else if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" (
    set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
) else (
    echo Git Bash was not found on this PC.
    echo Please install Git for Windows from https://git-scm.com/download/win
    echo then double-click install.bat again.
    pause
    exit /b 1
)

"%BASH_EXE%" "%SCRIPT_DIR%install.sh"
pause
