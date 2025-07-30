@echo off
for /f "delims=" %%i in ('curl.exe -Ls https://dl.k8s.io/release/stable.txt') do set output=%%i
@REM echo %output%
@REM echo %USERNAME%
echo "Installing to %userprofile%\AppData\Local\Microsoft\WindowsApps"
cd %userprofile%\AppData\Local\Microsoft\WindowsApps

curl.exe -LO "https://dl.k8s.io/release/%output%/bin/windows/amd64/kubectl.exe"
