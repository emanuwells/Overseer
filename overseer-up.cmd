@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\overseer-up.ps1" %*
