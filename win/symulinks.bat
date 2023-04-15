@echo off
rem переходим в родительский каталог
cd %~dp0..\

rem Создаём символьную ссылку на какталог data
if not exist data\ (
  del data
  MKLINK /D .\data  .\submodules\parafoil\data
) else (
  echo data exist yet 
)

rem Создаём символьную ссылку на пакет parafoil
if not exist parafoil\ (
  del parafoil
  MKLINK /D .\parafoil  .\submodules\parafoil\parafoil
) else (
  echo parafoil exist yet 
)

rem Создаём символьную ссылку на пакет flyplot
if not exist flyplot\ (
  del flyplot
  MKLINK /D .\flyplot  .\submodules\flyplot\flyplot
) else (
  echo flyplot exist yet 
)

rem пауза
pause