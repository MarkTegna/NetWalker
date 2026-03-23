rem goto doo
..\.\dist\netwalker.exe --version
waitkey 30
if %ERRORLEVEL% == 113 goto bye
:doo
..\dist\netwalker.exe  --seed-devices KREM-CORE-A --max-depth 9 --config .\netwalker.ini
rem ..\dist\netwalker.exe  --seed-devices KUSA-CORE-A --max-depth 9 --config .\netwalker.ini
waitkey 120
:bye
