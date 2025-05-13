@echo off
pyinstaller --noconsole --onefile --uac-admin --name "xagent_optimiser_v1.0.1" --icon "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\ppg.ico" --add-data "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\version.json:." "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\main.py"
pause
