@echo off
REM Elite Intel installer shim.
REM Double-click this file to run install.sh through Git Bash.
REM install.sh is the real installer; this file only launches it.

setlocal

set "SCRIPT_DIR=%~dp0"

REM Refuse to run from a network/UNC path (for example \\wsl.localhost\...).
REM The build needs a local Windows folder such as C:\elite-intel.
if "%SCRIPT_DIR:~0,2%"=="\\" (
    echo This installer cannot run from a network path:
    echo   %SCRIPT_DIR%
    echo.
    echo Clone or copy the project to a local Windows folder first, e.g.:
    echo   git clone https://github.com/macreat/elite-intel.git C:\elite-intel
    echo then double-click install.bat inside that folder.
    pause
    exit /b 1
)

REM Locate Git Bash explicitly. Never use plain "bash" from PATH: on PCs
REM with WSL installed that resolves to C:\Windows\System32\bash.exe
REM (WSL bash), which cannot run this installer.
set "BASH_EXE="
if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LocalAppData%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LocalAppData%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE (
    for /f "delims=" %%G in ('where git 2^>nul') do (
        if not defined BASH_EXE if exist "%%~dpG..\bin\bash.exe" set "BASH_EXE=%%~dpG..\bin\bash.exe"
    )
)
if not defined BASH_EXE (
    echo Git Bash was not found on this PC.
    echo Please install Git for Windows from https://git-scm.com/download/win
    echo then double-click install.bat again.
    pause
    exit /b 1
)

REM Run from the script's own folder so install.sh gets a plain relative
REM path and no Windows-to-bash path conversion is needed.
pushd "%SCRIPT_DIR%"
"%BASH_EXE%" install.sh
popd
pause
