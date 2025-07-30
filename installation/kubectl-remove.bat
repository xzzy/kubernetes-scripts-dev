@echo off
@REM echo %USERNAME%
echo "Removing %userprofile%\AppData\Local\Microsoft\WindowsApps\kubectl.exe"
cd %userprofile%\AppData\Local\Microsoft\WindowsApps
del kubectl.exe
