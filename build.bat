@echo off
pyinstaller --noconsole --onefile --uac-admin --name "xagent_optimiser_v1.0.4" --icon "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\ppg.ico" --add-data "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\version.json:." --add-data "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\OPTI_UI.ui:." "D:\AHMAD ABDULLAH\Desktop\Important files\OPTIMISER\main.py"
pause
