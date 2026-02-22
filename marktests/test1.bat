goto doo
..\.\dist\netwalker.exe --version
waitkey 30
if %ERRORLEVEL% == 113 goto bye
:doo
..\dist\netwalker.exe  --seed-devices KARE-CORE-A --max-depth 0 --config .\netwalker.ini
waitkey 120
:bye
