@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0overseer-up.ps1" %*
