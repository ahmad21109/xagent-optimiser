from PyQt6.QtWidgets import QMessageBox, QApplication, QDialog
from PyQt6.QtCore import Qt
import os
import shutil
import subprocess
import ctypes
import sys
import tempfile
import winreg
import webbrowser
import requests
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from packaging import version
from dialogs import UpdateDialog, CleaningDialog, RestartDialog, DownloadDialog, CustomMessageDialog, CustomErrorDialog
import win32com.client

CURRENT_VERSION = "1.0.4"

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()

run_as_admin()

def is_program_installed(program_name):
    """
    Check if a program is installed by searching the Windows Uninstall registry and Start menu shortcuts.
    Args:
        program_name (str): Name or partial name of the program to search for (e.g., 'MSI App Player').
    Returns:
        tuple: (is_installed: bool, exe_path: str or None)
    """
    print(f"Searching for program: {program_name}")
    
    # Possible executable names for MSI App Player
    possible_exes = ["HD-Player.exe", "MSIAppPlayer.exe", "Bluestacks.exe"]
    
    # Check registry (HKEY_LOCAL_MACHINE and HKEY_CURRENT_USER)
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hive, path in registry_paths:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                try:
                    display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                    print(f"Found registry DisplayName: {display_name}")
                    if program_name.lower() in display_name.lower():
                        # Try DisplayIcon
                        try:
                            display_icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                            print(f"DisplayIcon: {display_icon}")
                            if display_icon.lower().endswith(".exe") and os.path.isfile(display_icon):
                                winreg.CloseKey(subkey)
                                winreg.CloseKey(key)
                                print(f"Found executable via DisplayIcon: {display_icon}")
                                return True, display_icon
                        except FileNotFoundError:
                            pass
                        
                        # Try InstallLocation with possible executables
                        try:
                            install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                            print(f"InstallLocation: {install_location}")
                            if install_location and os.path.isdir(install_location):
                                for exe in possible_exes:
                                    exe_path = os.path.join(install_location, exe)
                                    if os.path.isfile(exe_path):
                                        winreg.CloseKey(subkey)
                                        winreg.CloseKey(key)
                                        print(f"Found executable via InstallLocation: {exe_path}")
                                        return True, exe_path
                        except FileNotFoundError:
                            pass
                        
                        # Fallback: Parse UninstallString
                        try:
                            uninstall_string, _ = winreg.QueryValueEx(subkey, "UninstallString")
                            print(f"UninstallString: {uninstall_string}")
                            uninstall_string = uninstall_string.strip().strip('"')
                            if uninstall_string.lower().endswith(".exe"):
                                exe_dir = os.path.dirname(uninstall_string)
                                for exe in possible_exes:
                                    exe_path = os.path.join(exe_dir, exe)
                                    if os.path.isfile(exe_path):
                                        winreg.CloseKey(subkey)
                                        winreg.CloseKey(key)
                                        print(f"Found executable via UninstallString: {exe_path}")
                                        return True, exe_path
                        except FileNotFoundError:
                            pass
                except FileNotFoundError:
                    pass
                finally:
                    winreg.CloseKey(subkey)
            winreg.CloseKey(key)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Error checking registry {path}: {str(e)}")

    # Check Start menu shortcuts
    shortcut_dirs = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
    ]
    shell = win32com.client.Dispatch("WScript.Shell")
    
    for shortcut_dir in shortcut_dirs:
        try:
            for root, _, files in os.walk(shortcut_dir):
                for file in files:
                    if file.endswith(".lnk") and program_name.lower() in file.lower():
                        shortcut_path = os.path.join(root, file)
                        print(f"Found shortcut: {shortcut_path}")
                        shortcut = shell.CreateShortCut(shortcut_path)
                        target_path = shortcut.TargetPath
                        print(f"Shortcut TargetPath: {target_path}")
                        if target_path.lower().endswith(".exe") and os.path.isfile(target_path):
                            print(f"Found executable via shortcut: {target_path}")
                            return True, target_path
        except Exception as e:
            print(f"Error checking shortcuts in {shortcut_dir}: {str(e)}")

    print(f"No matching program found for {program_name}")
    return False, None

def open_msi_emulator():
    try:
        is_installed, exe_path = is_program_installed("MSI App Player")
        if is_installed and exe_path:
            subprocess.run([exe_path], check=True)
            dialog = CustomMessageDialog("Success", "MSI Emulator launched successfully.")
            dialog.exec()
            print("MSI Emulator launched")
        else:
            message = "MSI App Player not found or executable missing."
            if is_installed:
                message += "\nTry reinstalling MSI App Player to fix registry settings."
            dialog = DownloadDialog("MSI Emulator")
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://download.msi.com/uti_exe/nb/MSI-APP-Player.zip")
                print("Redirected to download MSI Emulator")
            else:
                print("User chose to download MSI Emulator later")
    except subprocess.CalledProcessError as e:
        print(f"Error launching MSI Emulator: {str(e)}")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error with MSI Emulator: {str(e)}")
        dialog.exec()
        print(f"Unexpected error with MSI Emulator: {str(e)}")

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
        subprocess.run(["cleanmgr.exe", "/d", "C:", "/sagerun:1"], check=True)
        dialog = CustomMessageDialog("Success", "Disk cleanup completed for C: drive.")
        dialog.exec()
        print("Disk cleanup executed for C: drive")
    except subprocess.CalledProcessError as e:
        dialog = CustomErrorDialog("Error", f"Failed to run disk cleanup: {str(e)}")
        dialog.exec()
        print(f"Error during disk cleanup: {str(e)}")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error during disk cleanup: {str(e)}")
        dialog.exec()
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
            subprocess.run('powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a', check=True, shell=True)
            mode = "Power Saver"
        elif value == 1:
            subprocess.run('powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e', check=True, shell=True)
            mode = "Balanced"
        elif value == 2:
             success = activate_ultimate_performance()
             if not success:
                raise subprocess.CalledProcessError(1, "powercfg", "Failed to set Ultimate Performance plan.")
             mode = "Ultimate Performance"
        dialog = CustomMessageDialog("Success", f"Power mode set to {mode}.")
        dialog.exec()
        print(f"Power mode set to {mode}")
    except subprocess.CalledProcessError as e:
        dialog = CustomErrorDialog("Error", f"Failed to set power mode: {str(e)}.\nPlease run the application as administrator.")
        dialog.exec()
        print(f"Error setting power mode: {str(e)}")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error setting power mode: {str(e)}")
        dialog.exec()
        print(f"Unexpected error setting power mode: {str(e)}")

def optimize_mouse():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
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
        for name, (reg_type, value) in settings.items():
            winreg.SetValueEx(key, name, 0, reg_type, value)
        winreg.CloseKey(key)
        dialog = RestartDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
            dialog = CustomMessageDialog("Restart", "System will restart in 60 seconds. Please save your work.")
            dialog.exec()
            print("System restart initiated")
        else:
            print("User chose to restart later")
        print("Mouse settings optimized successfully")
    except PermissionError:
        dialog = CustomErrorDialog("Error", "Permission denied: Run the application as administrator to modify mouse settings.")
        dialog.exec()
        print("Permission error: Failed to modify registry")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Failed to optimize mouse settings: {str(e)}")
        dialog.exec()
        print(f"Error optimizing mouse settings: {str(e)}")

def custom_hud():
    dialog = CustomMessageDialog("Action", "Applying custom HUD...")
    dialog.exec()
    print("Simulating custom HUD application")

def open_external_aimbot():
    dialog = CustomMessageDialog("Action", "Opening external aimbot...")
    dialog.exec()
    print("Simulating external aimbot open")

def close_external_aimbot():
    dialog = CustomMessageDialog("Action", "Closing external aimbot...")
    dialog.exec()
    print("Simulating external aimbot close")

def buy_external_aimbot():
    dialog = CustomMessageDialog("Action", "Redirecting to purchase external aimbot...")
    dialog.exec()
    print("Simulating external aimbot purchase")

def inject_internal_aimbot():
    dialog = CustomMessageDialog("Action", "Injecting internal aimbot...")
    dialog.exec()
    print("Simulating internal aimbot injection")

def close_internal_aimbot():
    dialog = CustomMessageDialog("Action", "Closing internal aimbot...")
    dialog.exec()
    print("Simulating internal aimbot close")

def buy_internal_aimbot():
    dialog = CustomMessageDialog("Action", "Redirecting to purchase internal aimbot...")
    dialog.exec()
    print("Simulating internal aimbot purchase")

def open_bluestacks_emulator():
    try:
        is_installed, exe_path = is_program_installed("BlueStacks")
        if is_installed and exe_path:
            dialog = CustomMessageDialog("Success", "BlueStacks Emulator launched successfully.")
            dialog.exec()
            subprocess.run([exe_path], check=True)
            print("BlueStacks Emulator launched")
        else:
            message = "BlueStacks Emulator not found or executable missing."
            if is_installed:
                message += "\nTry reinstalling BlueStacks to fix registry settings."
            dialog = DownloadDialog("BlueStacks Emulator")
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://www.bluestacks.com/download.html")
                print("Redirected to download BlueStacks Emulator")
            else:
                print("User chose to download BlueStacks Emulator later")
    except subprocess.CalledProcessError as e:
        print(f"Error launching BlueStacks Emulator: {str(e)}")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error with BlueStacks Emulator: {str(e)}")
        dialog.exec()
        print(f"Unexpected error with BlueStacks Emulator: {str(e)}")

def open_memu_emulator():
    try:
        is_installed, exe_path = is_program_installed("MEmu")
        if is_installed and exe_path:
            dialog = CustomMessageDialog("Success", "BlueStacks Emulator launched successfully.")
            dialog.exec()
            subprocess.run([exe_path], check=True)
            print("MEMU Play Emulator launched")
        else:
            message = "MEMU Play Emulator not found or executable missing."
            if is_installed:
                message += "\nTry reinstalling MEmu to fix registry settings."
            dialog = DownloadDialog("MEMU Play Emulator")
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://www.memuplay.com/download-memu-on-pc.html?from=online2_installer")
                print("Redirected to download MEMU Play Emulator")
            else:
                print("User chose to download MEMU Play Emulator later")
    except subprocess.CalledProcessError as e:
        print(f"Error launching MEMU Play Emulator: {str(e)}")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error with MEMU Play Emulator: {str(e)}")
        dialog.exec()
        print(f"Unexpected error with MEMU Play Emulator: {str(e)}")

def download_emu_hud():
    dialog = CustomMessageDialog("Action", "Downloading emulator HUD...")
    dialog.exec()
    print("Simulating emulator HUD download")

def check_for_updates():
    try:
        VERSION_URL = "https://github.com/ahmad21109/xagent-optimiser/raw/main/version.json"
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        latest_version = data.get("version")
        download_url = data.get("download_url", "")
        release_notes = data.get("release_notes", "No release notes available.")
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            dialog = UpdateDialog(CURRENT_VERSION, latest_version, release_notes, download_url)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                print(f"Downloading update from {download_url}...")
                response = requests.get(download_url, timeout=10, stream=True)
                response.raise_for_status()
                current_exe = sys.executable
                current_dir = os.path.dirname(current_exe)
                temp_dir = tempfile.gettempdir()
                temp_exe = os.path.join(temp_dir, "xagent_optimiser_v1.0.1_temp.exe")
                with open(temp_exe, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"New executable downloaded to {temp_exe}")
                batch_file = os.path.join(temp_dir, "update_xagent.bat")
                with open(batch_file, "w") as f:
                    f.write("@echo off\n")
                    f.write("timeout /t 2 /nobreak >nul\n")
                    f.write(f"copy /Y \"{temp_exe}\" \"{current_exe}\"\n")
                    f.write(f"del \"{temp_exe}\"\n")
                    f.write(f"start \"\" \"{current_exe}\"\n")
                    f.write(f"del \"{batch_file}\"\n")
                subprocess.Popen(batch_file, shell=True)
                print("Initiating update process... Application will close.")
                QCoreApplication.quit()
        else:
            dialog = CustomMessageDialog("No Updates", f"You are using the latest version ({CURRENT_VERSION}).")
            dialog.exec()
            print("No updates available")
    except requests.RequestException as e:
        dialog = CustomErrorDialog("Error", f"Failed to check for updates: Unable to connect to the server.\n{str(e)}")
        dialog.exec()
        print(f"Error checking for updates: {str(e)}")
    except ValueError as e:
        dialog = CustomErrorDialog("Error", f"Failed to parse version information: {str(e)}")
        dialog.exec()
        print(f"Error parsing version: {str(e)}")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error while checking for updates: {str(e)}")
        dialog.exec()
        print(f"Unexpected error: {str(e)}")