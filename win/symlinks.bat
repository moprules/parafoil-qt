@echo off 
goto :check_Permissions 

:check_Permissions 
REM Проверяем права пользователя
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system" 
REM Если пользователь не является администратором, тогда повторяем выполнение скрипта с правами администратора
if '%errorlevel%' NEQ '0' (
    echo Administrator required!!!
    powershell -command "Start-Process '%0' -Verb runAs" 
    goto :EOF
) else (
    goto :start
) 

:start 
rem переходим в родительский каталог
cd %~dp0..\

rem Создаём символьную ссылку на какталог data
if not exist data\ (
  if exist data (del data)
  MKLINK /D .\data  .\submodules\parafoil\data
) else (
  echo data exist yet 
)

rem Создаём символьную ссылку на пакет parafoil
if not exist parafoil\ (
  if exist parafoil (del parafoil)
  MKLINK /D .\parafoil  .\submodules\parafoil\parafoil
) else (
  echo parafoil exist yet 
)

rem Создаём символьную ссылку на пакет flyplot
if not exist flyplot\ (
  if exist flyplot (del flyplot)
  MKLINK /D .\flyplot  .\submodules\flyplot\flyplot
) else (
  echo flyplot exist yet 
)

rem пауза
pause