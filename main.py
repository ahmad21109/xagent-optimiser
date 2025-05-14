import sys
import warnings
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic
import os
from dialogs import CleaningDialog 
from button_functions import (  
    clean_memory, clean_disk, optimize_mouse, custom_hud,
    open_external_aimbot, close_external_aimbot, buy_external_aimbot,
    inject_internal_aimbot, close_internal_aimbot, buy_internal_aimbot,
    open_msi_emulator, open_bluestacks_emulator, open_memu_emulator,
    download_emu_hud, check_for_updates, set_power_mode
)

warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller sets this up
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class OptimizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(resource_path('OPTI_UI.ui'), self)
            self.setWindowTitle("XAGENT OPTIMISER")
            
            # Configure the slider for power modes
            try:
                self.horizontalSlider.setMinimum(0)
                self.horizontalSlider.setMaximum(2)
                self.horizontalSlider.setTickInterval(1)
                self.horizontalSlider.setSingleStep(1)
                self.horizontalSlider.setValue(1)  # Default to Balanced
            except AttributeError:
                print("Slider not found in UI")

            self.connect_buttons()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load UI: {str(e)}")
    
    def connect_buttons(self):
        try:
            self.pushButton.clicked.connect(lambda: clean_memory(self))
            self.pushButton_2.clicked.connect(clean_disk)
        except AttributeError:
            print("Performance tab buttons not found")
        
        try:
            self.horizontalSlider.valueChanged.connect(set_power_mode)
        except AttributeError:
            print("Slider not found")
        
        try:
            self.pushButton_3.clicked.connect(optimize_mouse)
            self.pushButton_4.clicked.connect(custom_hud)
        except AttributeError:
            print("Sensi tab buttons not found")
        
        try:
            self.pushButton_5.clicked.connect(open_external_aimbot)
            self.pushButton_6.clicked.connect(close_external_aimbot)
            self.pushButton_7.clicked.connect(buy_external_aimbot)
        except AttributeError:
            print("External aimbot buttons not found")

        try:
            self.pushButton_8.clicked.connect(inject_internal_aimbot)
            self.pushButton_9.clicked.connect(close_internal_aimbot)
            self.pushButton_10.clicked.connect(buy_internal_aimbot)
        except AttributeError:
            print("Internal aimbot buttons not found")
        
        try:
            self.pushButton_11.clicked.connect(open_msi_emulator)
            self.pushButton_12.clicked.connect(open_bluestacks_emulator)
            self.pushButton_13.clicked.connect(open_memu_emulator)
        except AttributeError:
            print("Emulator buttons not found")
        
        try:
            self.pushButton_14.clicked.connect(download_emu_hud)
        except AttributeError:
            print("EMU HUD button not found")
        
        try:
            self.pushButton_15.clicked.connect(check_for_updates)
        except AttributeError:
            print("Settings button not found")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OptimizerWindow()
    window.show()
    sys.exit(app.exec())