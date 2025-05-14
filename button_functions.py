from PyQt6.QtWidgets import QMessageBox, QApplication, QDialog
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
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
    
    possible_exes = ["HD-Player.exe", "MSIAppPlayer.exe", "Bluestacks.exe", "MEmu.exe"]
    
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

class MemoryCleanerWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(int, list)
    error = pyqtSignal(str)

    def run(self):
        temp_dirs = [r"C:\Windows\Temp", r"C:\Users\AHMADA~1\AppData\Local\Temp"]
        total_files = 0
        for temp_dir in temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    for root, _, files in os.walk(temp_dir):
                        total_files += len(files)
            except Exception:
                pass

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
                            self.progress.emit(files_deleted)
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

        self.finished.emit(files_deleted, errors)

def clean_memory(parent):
    dialog = CleaningDialog(parent)
    
    temp_dirs = [r"C:\Windows\Temp", r"C:\Users\AHMADA~1\AppData\Local\Temp"]
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

    worker = MemoryCleanerWorker()
    thread = QThread(parent=dialog)  # Set dialog as parent to manage lifecycle
    dialog.thread = thread  # Store thread in dialog to prevent garbage collection
    worker.moveToThread(thread)
    worker.progress.connect(lambda value: dialog.progress_bar.setValue(value))
    worker.finished.connect(lambda files_deleted, errors: on_cleaning_finished(dialog, files_deleted, errors))
    worker.error.connect(lambda error: on_cleaning_error(dialog, error))
    dialog.finished.connect(lambda: stop_thread(thread))  # Handle dialog closure
    thread.started.connect(worker.run)
    thread.start()

def stop_thread(thread):
    if thread.isRunning():
        thread.quit()
        thread.wait()
    print("Thread stopped")

def on_cleaning_finished(dialog, files_deleted, errors):
    dialog.title_label.setText("Cleaned")
    dialog.progress_bar.setVisible(False)
    message = f"Successfully cleaned memory\nDeleted {files_deleted} files"
    if errors:
        message += f"\n{len(errors)} errors occurred"
    dialog.result_label.setText(message)
    dialog.result_label.setVisible(True)
    dialog.ok_button.setVisible(True)
    stop_thread(dialog.thread)
    print(f"Clean memory: {files_deleted} files deleted, {len(errors)} errors")

def on_cleaning_error(dialog, error):
    dialog.title_label.setText("Error")
    dialog.progress_bar.setVisible(False)
    dialog.result_label.setText(f"Error: {error}")
    dialog.result_label.setVisible(True)
    dialog.ok_button.setVisible(True)
    stop_thread(dialog.thread)
    print(f"Cleaning error: {error}")

class DiskCleanerWorker(QObject):
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            subprocess.run(["cleanmgr.exe", "/d", "C:", "/sagerun:1"], check=True)
            self.finished.emit(True, "Disk cleanup completed for C: drive.")
        except subprocess.CalledProcessError as e:
            self.finished.emit(False, f"Failed to run disk cleanup: {str(e)}")
        except Exception as e:
            self.finished.emit(False, f"Unexpected error during disk cleanup: {str(e)}")

def clean_disk():
    dialog = CustomMessageDialog("Disk Cleanup", "Starting disk cleanup...")
    dialog.show()
    worker = DiskCleanerWorker()
    thread = QThread(parent=dialog)
    dialog.thread = thread
    worker.moveToThread(thread)
    worker.finished.connect(lambda success, message: on_disk_cleaning_finished(dialog, success, message))
    dialog.finished.connect(lambda: stop_thread(thread))
    thread.started.connect(worker.run)
    thread.start()

def on_disk_cleaning_finished(dialog, success, message):
    dialog.setWindowTitle("Disk Cleanup")
    dialog.message_label.setText(message)
    dialog.ok_button.setVisible(True)
    stop_thread(dialog.thread)
    print(message)

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

class PowerModeWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, value):
        super().__init__()
        self.value = value

    def run(self):
        try:
            mode = None
            if self.value == 0:
                subprocess.run('powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a', check=True, shell=True)
                mode = "Power Saver"
            elif self.value == 1:
                subprocess.run('powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e', check=True, shell=True)
                mode = "Balanced"
            elif self.value == 2:
                success = activate_ultimate_performance()
                if not success:
                    raise subprocess.CalledProcessError(1, "powercfg", "Failed to set Ultimate Performance plan.")
                mode = "Ultimate Performance"
            self.finished.emit(True, f"Power mode set to {mode}.")
        except subprocess.CalledProcessError as e:
            self.finished.emit(False, f"Failed to set power mode: {str(e)}.\nPlease run the application as administrator.")
        except Exception as e:
            self.finished.emit(False, f"Unexpected error setting power mode: {str(e)}")

def set_power_mode(value):
    dialog = CustomMessageDialog("Power Mode", "Setting power mode...")
    dialog.show()
    worker = PowerModeWorker(value)
    thread = QThread(parent=dialog)
    dialog.thread = thread
    worker.moveToThread(thread)
    worker.finished.connect(lambda success, message: on_power_mode_finished(dialog, success, message))
    dialog.finished.connect(lambda: stop_thread(thread))
    thread.started.connect(worker.run)
    thread.start()

def on_power_mode_finished(dialog, success, message):
    dialog.setWindowTitle("Power Mode")
    dialog.message_label.setText(message)
    dialog.ok_button.setVisible(True)
    stop_thread(dialog.thread)
    print(message)

class MouseOptimizerWorker(QObject):
    finished = pyqtSignal(bool, str)

    def run(self):
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
            self.finished.emit(True, "Mouse settings optimized successfully.")
        except PermissionError:
            self.finished.emit(False, "Permission denied: Run the application as administrator to modify mouse settings.")
        except Exception as e:
            self.finished.emit(False, f"Failed to optimize mouse settings: {str(e)}")

def optimize_mouse():
    dialog = CustomMessageDialog("Mouse Optimization", "Optimizing mouse settings...")
    dialog.show()
    worker = MouseOptimizerWorker()
    thread = QThread(parent=dialog)
    dialog.thread = thread
    worker.moveToThread(thread)
    worker.finished.connect(lambda success, message: on_mouse_optimization_finished(dialog, success, message))
    dialog.finished.connect(lambda: stop_thread(thread))
    thread.started.connect(worker.run)
    thread.start()

def on_mouse_optimization_finished(dialog, success, message):
    dialog.close()
    if success:
        restart_dialog = RestartDialog()
        result = restart_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            try:
                subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
                confirm_dialog = CustomMessageDialog("Restart", "System will restart in 60 seconds. Please save your work.")
                confirm_dialog.exec()
                print("System restart initiated")
            except subprocess.CalledProcessError as e:
                error_dialog = CustomErrorDialog("Error", f"Failed to initiate restart: {str(e)}")
                error_dialog.exec()
                print(f"Error initiating restart: {str(e)}")
        else:
            print("User chose to restart later")
    else:
        error_dialog = CustomErrorDialog("Error", message)
        error_dialog.exec()
    stop_thread(dialog.thread)
    print(message)

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

def open_msi_emulator():
    try:
        is_installed, exe_path = is_program_installed("MSI App Player")
        if is_installed and exe_path:
            subprocess.Popen([exe_path])
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
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error with MSI Emulator: {str(e)}")
        dialog.exec()
        print(f"Unexpected error with MSI Emulator: {str(e)}")

def open_bluestacks_emulator():
    try:
        is_installed, exe_path = is_program_installed("BlueStacks")
        if is_installed and exe_path:
            subprocess.Popen([exe_path])
            dialog = CustomMessageDialog("Success", "BlueStacks Emulator launched successfully.")
            dialog.exec()
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
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error with BlueStacks Emulator: {str(e)}")
        dialog.exec()
        print(f"Unexpected error with BlueStacks Emulator: {str(e)}")

def open_memu_emulator():
    try:
        is_installed, exe_path = is_program_installed("MEmu")
        if is_installed and exe_path:
            subprocess.Popen([exe_path])
            dialog = CustomMessageDialog("Success", "MEmu Emulator launched successfully.")
            dialog.exec()
            print("MEmu Emulator launched")
        else:
            message = "MEmu Emulator not found or executable missing."
            if is_installed:
                message += "\nTry reinstalling MEmu to fix registry settings."
            dialog = DownloadDialog("MEmu Emulator")
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                webbrowser.open("https://www.memuplay.com/download-memu-on-pc.html?from=online2_installer")
                print("Redirected to download MEmu Emulator")
            else:
                print("User chose to download MEmu Emulator later")
    except Exception as e:
        dialog = CustomErrorDialog("Error", f"Unexpected error with MEmu Emulator: {str(e)}")
        dialog.exec()
        print(f"Unexpected error with MEmu Emulator: {str(e)}")

def download_emu_hud():
    dialog = CustomMessageDialog("Action", "Downloading emulator HUD...")
    dialog.exec()
    print("Simulating emulator HUD download")

class UpdateCheckerWorker(QObject):
    finished = pyqtSignal(bool, str, str, str, str)
    error = pyqtSignal(str)

    def run(self):
        try:
            VERSION_URL = "https://github.com/ahmad21109/xagent-optimiser/raw/main/version.json"
            response = requests.get(VERSION_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get("version")
            download_url = data.get("download_url", "")
            release_notes = data.get("release_notes", "No release notes available.")
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                self.finished.emit(True, "Update available.", latest_version, release_notes, download_url)
            else:
                self.finished.emit(False, f"You are using the latest version ({CURRENT_VERSION}).", latest_version, release_notes, download_url)
        except requests.RequestException as e:
            self.error.emit(f"Failed to check for updates: Unable to connect to the server.\n{str(e)}")
        except ValueError as e:
            self.error.emit(f"Failed to parse version information: {str(e)}")
        except Exception as e:
            self.error.emit(f"Unexpected error while checking for updates: {str(e)}")

class UpdateDownloaderWorker(QObject):
    finished = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        try:
            response = requests.get(self.download_url, timeout=10, stream=True)
            response.raise_for_status()
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            temp_dir = tempfile.gettempdir()
            temp_exe = os.path.join(temp_dir, "xagent_optimiser_temp.exe")
            with open(temp_exe, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            batch_file = os.path.join(temp_dir, "update_xagent.bat")
            with open(batch_file, "w") as f:
                f.write("@echo off\n")
                f.write("timeout /t 2 /nobreak >nul\n")
                f.write(f"copy /Y \"{temp_exe}\" \"{current_exe}\"\n")
                f.write(f"del \"{temp_exe}\"\n")
                f.write(f"start \"\" \"{current_exe}\"\n")
                f.write(f"del \"{batch_file}\"\n")
            subprocess.Popen(batch_file, shell=True)
            self.finished.emit(True, "Update downloaded. Application will restart.")
        except requests.RequestException as e:
            self.error.emit(f"Failed to download update: {str(e)}")
        except Exception as e:
            self.error.emit(f"Unexpected error during update download: {str(e)}")

def check_for_updates():
    dialog = CustomMessageDialog("Checking Updates", "Checking for updates...")
    dialog.show()
    worker = UpdateCheckerWorker()
    thread = QThread(parent=dialog)
    dialog.thread = thread
    worker.moveToThread(thread)
    worker.finished.connect(lambda success, message, latest_version, release_notes, download_url: on_update_check_finished(dialog, success, message, latest_version, release_notes, download_url))
    worker.error.connect(lambda error: on_update_check_error(dialog, error))
    dialog.finished.connect(lambda: stop_thread(thread))
    thread.started.connect(worker.run)
    thread.start()

def on_update_check_finished(dialog, success, message, latest_version, release_notes, download_url):
    dialog.close()
    if success:
        update_dialog = UpdateDialog(CURRENT_VERSION, latest_version, release_notes, download_url)
        if update_dialog.exec() == QDialog.DialogCode.Accepted:
            download_dialog = CustomMessageDialog("Downloading Update", "Downloading update...")
            download_dialog.show()
            worker = UpdateDownloaderWorker(download_url)
            thread = QThread(parent=download_dialog)
            download_dialog.thread = thread
            worker.moveToThread(thread)
            worker.finished.connect(lambda success, msg: on_update_download_finished(download_dialog, success, msg))
            worker.error.connect(lambda error: on_update_download_error(download_dialog, error))
            download_dialog.finished.connect(lambda: stop_thread(thread))
            thread.started.connect(worker.run)
            thread.start()
        else:
            print("User chose to update later")
    else:
        dialog = CustomMessageDialog("No Updates", message)
        dialog.exec()
    stop_thread(dialog.thread)
    print(message)

def on_update_download_finished(dialog, success, message):
    dialog.close()
    if success:
        dialog = CustomMessageDialog("Update", message)
        dialog.exec()
        QCoreApplication.quit()
    else:
        dialog = CustomErrorDialog("Error", message)
        dialog.exec()
    stop_thread(dialog.thread)
    print(message)

def on_update_download_error(dialog, error):
    dialog.close()
    error_dialog = CustomErrorDialog("Error", error)
    error_dialog.exec()
    stop_thread(dialog.thread)
    print(error)

def on_update_check_error(dialog, error):
    dialog.close()
    error_dialog = CustomErrorDialog("Error", error)
    error_dialog.exec()
    stop_thread(dialog.thread)
    print(error)