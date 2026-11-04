@echo off
rem Startet den exportierten Windows-Build von Ashes of Empires: The Last Winter.
if exist "%~dp0builds\windows\AshesOfEmpires.exe" (
  start "" "%~dp0builds\windows\AshesOfEmpires.exe"
) else (
  echo Kein Build gefunden. Bitte zuerst exportieren: siehe README.md
  pause
)
