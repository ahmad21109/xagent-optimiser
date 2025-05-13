from PyQt6.QtWidgets import QMessageBox, QApplication, QDialog
from PyQt6.QtCore import Qt
import os
import shutil
import subprocess
import ctypes
import sys
import winreg
import webbrowser
import requests
from packaging import version
from dialogs import CleaningDialog, RestartDialog, DownloadDialog, UpdateDialog  # Import dialogs

# Define the current version of your application
CURRENT_VERSION = "1.0.0"  # Update this with your app's version

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()

run_as_admin()

def clean_memory(parent):
    temp_dirs = [r"C:\Windows\Temp", r"C:\Users\AHMADA~1\AppData\Local\Temp"]

    dialog = CleaningDialog(parent)
    total_files = 0
    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                for root, _, files in os.walk(temp_dir):
                    total_files += len(files)
        except Exception:
            pass
    
    dialog.progress_bar.setMaximum(total_files if total_files > 0 else 1)
    dialog.show()
    QApplication.processEvents()    
    files_deleted = 0
    errors = []    
    for temp_dir in temp_dirs:
        try:
            if not os.path.exists(temp_dir):
                errors.append(f"Directory not found: {temp_dir}")
                continue            
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                        dialog.progress_bar.setValue(dialog.progress_bar.value() + 1)
                        QApplication.processEvents()
                    except (PermissionError, OSError) as e:
                        errors.append(f"Failed to delete {file_path}: {str(e)}")               
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        shutil.rmtree(dir_path, ignore_errors=True)
                    except (PermissionError, OSError) as e:
                        errors.append(f"Failed to delete {dir_path}: {str(e)}")        
        except Exception as e:
            errors.append(f"Error accessing {temp_dir}: {str(e)}")

    dialog.title_label.setText("Cleaned")
    dialog.progress_bar.setVisible(False)
    message = f"Successfully cleaned memory"
    dialog.result_label.setText(message)
    dialog.result_label.setVisible(True)
    dialog.ok_button.setVisible(True)
    dialog.exec()   
    print(f"Clean memory: {files_deleted} files deleted, {len(errors)} errors")

def clean_disk():
    try:
        # Run Windows Disk Cleanup (cleanmgr.exe) for C: drive with preset options
        subprocess.run(["cleanmgr.exe", "/d", "C:", "/sagerun:1"], check=True)
        QMessageBox.information(None, "Success", "Disk cleanup completed for C: drive.")
        print("Disk cleanup executed for C: drive")
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Error", f"Failed to run disk cleanup: {str(e)}")
        print(f"Error during disk cleanup: {str(e)}")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Unexpected error during disk cleanup: {str(e)}")
        print(f"Unexpected error during disk cleanup: {str(e)}")

def set_brightness(level):
    try:
        subprocess.run(
            ['powershell', '-Command',
             f'(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})'],
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to set brightness: {e}")

def activate_ultimate_performance():
    try:
        plans = subprocess.check_output('powercfg /list', shell=True, text=True)
        lines = plans.splitlines()

        ultimate_guid = None
        for line in lines:
            if "ultimate" in line.lower():
                ultimate_guid = line.strip().split()[3]
                break

        if not ultimate_guid:
            subprocess.run('powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61', shell=True, check=True)
            return activate_ultimate_performance()

        subprocess.run(f'powercfg /setactive {ultimate_guid}', shell=True, check=True)

        # 🔆 Set brightness to 100%
        set_brightness(100)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed: {e}")
        return False

def set_power_mode(value):
    try:
        mode = None

        power_plans = subprocess.check_output(['powercfg', '/list'], shell=True, text=True)

        if value == 0:
            # Power Saver
            subprocess.run('powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a', check=True, shell=True)
            mode = "Power Saver"

        elif value == 1:
            # Balanced
            subprocess.run('powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e', check=True, shell=True)
            mode = "Balanced"

        elif value == 2:
             success = activate_ultimate_performance()
             if not success:
                raise subprocess.CalledProcessError(1, "powercfg", "Failed to set Ultimate Performance plan.")
             mode = "Ultimate Performance"

        QMessageBox.information(None, "Success", f"Power mode set to {mode}.")
        print(f"Power mode set to {mode}")

    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Error", f"Failed to set power mode: {str(e)}.\nPlease run the application as administrator.")
        print(f"Error setting power mode: {str(e)}")

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Unexpected error setting power mode: {str(e)}")
        print(f"Unexpected error setting power mode: {str(e)}")

def optimize_mouse():
    try:
        # Open the registry key for mouse settings
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
        
        # Define the mouse settings from the provided .reg file
        settings = {
            "ActiveWindowTracking": (winreg.REG_DWORD, 0),
            "Beep": (winreg.REG_SZ, "No"),
            "DoubleClickHeight": (winreg.REG_SZ, "2"),
            "DoubleClickSpeed": (winreg.REG_SZ, "400"),
            "DoubleClickWidth": (winreg.REG_SZ, "2"),
            "ExtendedSounds": (winreg.REG_SZ, "yes"),
            "MouseHoverHeight": (winreg.REG_SZ, "4"),
            "MouseHoverTime": (winreg.REG_SZ, "30"),
            "MouseHoverWidth": (winreg.REG_SZ, "4"),
            "MouseSensitivity": (winreg.REG_SZ, "4"),
            "MouseSpeed": (winreg.REG_SZ, "1"),
            "MouseThreshold1": (winreg.REG_SZ, "9"),
            "MouseThreshold2": (winreg.REG_SZ, "9"),
            "MouseTrails": (winreg.REG_SZ, "0"),
            "SmoothMouseXCurve": (winreg.REG_BINARY, bytes.fromhex("00 00 00 00 00 00 00 00 00 A0 00 00 00 00 00 00 00 40 01 00 00 00 00 00 00 80 02 00 00 00 00 00 00 00 05 00 00 00 00 00")),
            "SmoothMouseYCurve": (winreg.REG_BINARY, bytes.fromhex("00 00 00 00 00 00 00 00 66 A6 02 00 00 00 00 00 CD 4C 05 00 00 00 00 00 A0 99 0A 00 00 00 00 00 38 33 15 00 00 00 00 00")),
            "SnapToDefaultButton": (winreg.REG_SZ, "0"),
            "SwapMouseButtons": (winreg.REG_SZ, "0")
        }
        
        # Apply each setting to the registry
        for name, (reg_type, value) in settings.items():
            winreg.SetValueEx(key, name, 0, reg_type, value)
        
        winreg.CloseKey(key)
        
        # Show custom restart dialog
        dialog = RestartDialog()
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Initiate system restart (60-second delay to allow user to save work)
            subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
            QMessageBox.information(None, "Restart", "System will restart in 60 seconds. Please save your work.")
            print("System restart initiated")
        else:
            print("User chose to restart later")
        
        print("Mouse settings optimized successfully")
    
    except PermissionError:
        QMessageBox.critical(None, "Error", "Permission denied: Run the application as administrator to modify mouse settings.")
        print("Permission error: Failed to modify registry")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to optimize mouse settings: {str(e)}")
        print(f"Error optimizing mouse settings: {str(e)}")

def custom_hud():
    QMessageBox.information(None, "Action", "Applying custom HUD...")
    print("Simulating custom HUD application")

def open_external_aimbot():
    QMessageBox.information(None, "Action", "Opening external aimbot...")
    print("Simulating external aimbot open")

def close_external_aimbot():
    QMessageBox.information(None, "Action", "Closing external aimbot...")
    print("Simulating external aimbot close")

def buy_external_aimbot():
    QMessageBox.information(None, "Action", "Redirecting to purchase external aimbot...")
    print("Simulating external aimbot purchase")

# SENSI tab - INTERNAL AIMBOT functions
def inject_internal_aimbot():
    QMessageBox.information(None, "Action", "Injecting internal aimbot...")
    print("Simulating internal aimbot injection")

def close_internal_aimbot():
    QMessageBox.information(None, "Action", "Closing internal aimbot...")
    print("Simulating internal aimbot close")

def buy_internal_aimbot():
    QMessageBox.information(None, "Action", "Redirecting to purchase internal aimbot...")
    print("Simulating internal aimbot purchase")

# OTHER STUFF tab - EMULATORS functions
def open_msi_emulator():
    # Check if MSI Emulator (MSI App Player) is installed
    msi_path = r"C:\Program Files\BlueStacks_msi5"
    msi_exe = os.path.join(msi_path, "HD-Player.exe")
    try:
        if os.path.exists(msi_exe):
            subprocess.run([msi_exe], check=True)
            QMessageBox.information(None, "Success", "MSI Emulator launched successfully.")
            print("MSI Emulator launched")
        else:
            dialog = DownloadDialog("MSI Emulator")
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://www.google.com")
                print("Redirected to download MSI Emulator")
            else:
                print("User chose to download MSI Emulator later")
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Error", f"Failed to launch MSI Emulator: {str(e)}")
        print(f"Error launching MSI Emulator: {str(e)}")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to check or launch MSI Emulator: {str(e)}")
        print(f"Error checking MSI Emulator: {str(e)}")

def open_bluestacks_emulator():
    # Check if BlueStacks is installed
    bluestacks_path = r"C:\Program Files\BlueStacks"
    bluestacks_exe = os.path.join(bluestacks_path, "HD-Player.exe")
    try:
        if os.path.exists(bluestacks_exe):
            subprocess.run([bluestacks_exe], check=True)
            QMessageBox.information(None, "Success", "BlueStacks Emulator launched successfully.")
            print("BlueStacks Emulator launched")
        else:
            dialog = DownloadDialog("BlueStacks Emulator")
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://www.google.com")
                print("Redirected to download BlueStacks Emulator")
            else:
                print("User chose to download BlueStacks Emulator later")
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Error", f"Failed to launch BlueStacks Emulator: {str(e)}")
        print(f"Error launching BlueStacks Emulator: {str(e)}")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to check or launch BlueStacks Emulator: {str(e)}")
        print(f"Error checking BlueStacks Emulator: {str(e)}")

def open_memu_emulator():
    # Check if MEmu is installed
    memu_path = r"C:\Program Files\Microvirt\MEmu"
    memu_exe = os.path.join(memu_path, "MEmu.exe")
    try:
        if os.path.exists(memu_exe):
            subprocess.run([memu_exe], check=True)
            QMessageBox.information(None, "Success", "MEMU Play Emulator launched successfully.")
            print("MEMU Play Emulator launched")
        else:
            dialog = DownloadDialog("MEMU Play Emulator")
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://www.google.com")
                print("Redirected to download MEMU Play Emulator")
            else:
                print("User chose to download MEMU Play Emulator later")
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Error", f"Failed to launch MEMU Play Emulator: {str(e)}")
        print(f"Error launching MEMU Play Emulator: {str(e)}")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to check or launch MEMU Play Emulator: {str(e)}")
        print(f"Error checking MEMU Play Emulator: {str(e)}")

# OTHER STUFF tab - EMU HUDS function
def download_emu_hud():
    QMessageBox.information(None, "Action", "Downloading emulator HUD...")
    print("Simulating emulator HUD download")

# SETTINGS tab function
def check_for_updates():
    try:
        # URL to the version information JSON file
        VERSION_URL = "https://your-server.com/version.json"  # Replace with your actual URL

        # Make an HTTP request to fetch version information
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        data = response.json()
        latest_version = data.get("version")
        download_url = data.get("download_url", "")
        release_notes = data.get("release_notes", "No release notes available.")

        # Compare versions
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            # Update available, show custom dialog
            dialog = UpdateDialog(CURRENT_VERSION, latest_version, release_notes, download_url)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                webbrowser.open(download_url)
                print(f"Opened download URL: {download_url}")
        else:
            # No update available
            QMessageBox.information(
                None,
                "No Updates",
                f"You are using the latest version ({CURRENT_VERSION})."
            )
            print("No updates available")

    except requests.RequestException as e:
        QMessageBox.critical(
            None,
            "Error",
            f"Failed to check for updates: Unable to connect to the server.\n{str(e)}"
        )
        print(f"Error checking for updates: {str(e)}")
    except ValueError as e:
        QMessageBox.critical(
            None,
            "Error",
            f"Failed to parse version information: {str(e)}"
        )
        print(f"Error parsing version: {str(e)}")
    except Exception as e:
        QMessageBox.critical(
            None,
            "Error",
            f"Unexpected error while checking for updates: {str(e)}"
        )
        print(f"Unexpected error: {str(e)}")