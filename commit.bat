@echo off
REM Double-click this file to open TortoiseGit commit dialog
REM with an auto-generated commit message.
REM
REM It requires TortoiseGitProc.exe to be on your PATH.

powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0commit.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: Something went wrong. Make sure TortoiseGit is installed.
    echo.
)
pause
