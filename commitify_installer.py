# commitify_installer.py
import sys
import os
import requests
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QLabel, QComboBox, QFrame, QMessageBox, QPushButton)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

class GitHubWorker(QThread):
    releases_loaded = pyqtSignal(list, str)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            url = "https://api.github.com/repos/kokofixcomputers/Commitify/releases"
            response = requests.get(url)
            response.raise_for_status()
            releases_data = response.json()
            releases = [release['tag_name'] for release in releases_data]
            latest = releases_data[0]['tag_name'] if releases else ""
            self.releases_loaded.emit(releases, latest)
        except Exception as e:
            self.error_occurred.emit(f"Failed to fetch releases: {str(e)}")

class CommitifyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.home_dir = os.path.expanduser("~")
        # Use different install directory on Windows
        if sys.platform.startswith("win"):
            self.install_dir = os.path.join(self.home_dir, "CommitifyBin")
        else:
            self.install_dir = os.path.join(self.home_dir, "bin")
        os.makedirs(self.install_dir, exist_ok=True)
        self.fetch_releases()

    def setup_ui(self):
        self.setWindowTitle("Commitify Installer")
        self.setMinimumSize(QSize(500, 350))
        
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(25, 35, 45))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 45, 55))
        dark_palette.setColor(QPalette.AlternateBase, QColor(25, 35, 45))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(25, 35, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Commitify Installer")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 24, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #61afef; margin-bottom: 30px;")
        layout.addWidget(title)

        self.release_container = QFrame()
        release_layout = QVBoxLayout(self.release_container)
        release_layout.setContentsMargins(0, 0, 0, 0)
        
        release_label = QLabel("Select version:")
        release_label.setStyleSheet("color: #abb2bf;")
        release_layout.addWidget(release_label)

        self.release_dropdown = QComboBox()
        self.release_dropdown.setStyleSheet(self.get_dropdown_style())
        release_layout.addWidget(self.release_dropdown)
        layout.addWidget(self.release_container)

        self.download_btn = QPushButton("Download & Install")
        self.download_btn.setStyleSheet(self.get_button_style())
        self.download_btn.clicked.connect(self.handle_download)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)

        self.update_btn = QPushButton("Update")
        self.update_btn.setStyleSheet(self.get_button_style())
        self.update_btn.clicked.connect(self.handle_download)
        self.update_btn.setVisible(False)  # hidden initially
        self.update_btn.setEnabled(False)
        layout.addWidget(self.update_btn)

        layout.addStretch()

    def get_dropdown_style(self):
        return """
            QComboBox {
                background: #282c34;
                color: white;
                padding: 8px;
                border: 1px solid #3e4451;
                border-radius: 6px;
                min-width: 200px;
            }
            QComboBox:hover {
                border: 1px solid #61afef;
                background: #2d313a;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #3e4451;
            }
            QComboBox QAbstractItemView {
                background: #282c34;
                color: white;
                selection-background-color: #61afef;
                border: 1px solid #3e4451;
                border-radius: 6px;
                padding: 8px;
            }
        """

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #61afef;
                color: #282c34;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #528bcc;
            }
            QPushButton:pressed {
                background-color: #3a6ea5;
            }
            QPushButton:disabled {
                background-color: #3e4451;
                color: #abb2bf;
            }
        """

    def fetch_releases(self):
        self.worker = GitHubWorker()
        self.worker.releases_loaded.connect(self.update_releases)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def update_releases(self, releases, latest_release):
        self.release_dropdown.clear()
        self.release_dropdown.addItems(releases)
        installed = self.is_installed()

        # Toggle buttons visibility based on install status
        self.download_btn.setVisible(not installed)
        self.update_btn.setVisible(installed)

        self.download_btn.setEnabled(len(releases) > 0)
        self.update_btn.setEnabled(len(releases) > 0)
        
        if latest_release:
            index = self.release_dropdown.findText(latest_release)
            if index >= 0:
                self.release_dropdown.setCurrentIndex(index)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.release_dropdown.setPlaceholderText("Failed to load releases")

    def is_installed(self):
        binary_name = self.get_binary_name()
        binary_path = os.path.join(self.install_dir, binary_name)
        return os.path.isfile(binary_path) and os.access(binary_path, os.X_OK)

    def get_binary_name(self):
        # Windows executables usually have .exe extension
        if sys.platform.startswith("win"):
            return "commitify.exe"
        else:
            return "commitify"

    def handle_download(self):
        selected_release = self.release_dropdown.currentText()
        if not selected_release:
            return

        sender = self.sender()
        action = "updated" if sender == self.update_btn else "installed"

        try:
            release_url = f"https://api.github.com/repos/kokofixcomputers/Commitify/releases/tags/{selected_release}"
            response = requests.get(release_url)
            response.raise_for_status()
            release_data = response.json()
            
            asset = self.find_platform_asset(release_data['assets'])
            if not asset:
                QMessageBox.critical(self, "Error", "No compatible binary found for your system")
                return

            binary_name = self.get_binary_name()
            download_path = os.path.join(self.install_dir, binary_name)
            self.download_file(asset['browser_download_url'], download_path)

            if not sys.platform.startswith("win"):
                os.chmod(download_path, 0o755)  # Make executable on Unix

            self.update_shell_profile()
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Commitify has been {action} successfully! You may need to restart your terminal or command prompt to use it.",
                QMessageBox.Ok
            )

            # Update button visibility after install/update
            installed = self.is_installed()
            self.download_btn.setVisible(not installed)
            self.update_btn.setVisible(installed)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Error: {str(e)}",
                QMessageBox.Ok
            )

    def find_platform_asset(self, assets):
        system_map = {
            "darwin": ["darwin", "macos"],
            "linux": ["linux", "ubuntu", "debian"],
            "win32": ["windows", "win", ".exe"]
        }
        
        current_system = sys.platform.lower()
        # Normalize Windows platform string
        if current_system.startswith("win"):
            current_system = "win32"

        target_keywords = system_map.get(current_system, [])
        
        for asset in assets:
            asset_name_lower = asset['name'].lower()
            if any(keyword in asset_name_lower for keyword in target_keywords):
                return asset
        return None

    def download_file(self, url, save_path):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def update_shell_profile(self):
        if sys.platform.startswith("win"):
            # On Windows, update PATH environment variable if needed
            self.update_windows_path()
        else:
            # On Unix-like systems, update shell profiles
            path_line = f'\nexport PATH="$HOME/bin:$PATH"\n'
            profiles = [".zshrc", ".bashrc", ".bash_profile"]
            
            for profile in profiles:
                profile_path = os.path.expanduser(f"~/{profile}")
                try:
                    with open(profile_path, "a+") as f:
                        f.seek(0)
                        if path_line.strip() not in f.read():
                            f.write(path_line)
                except Exception:
                    continue

    def update_windows_path(self):
        import winreg
        try:
            # Read current user PATH
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as key:
                try:
                    current_path, _ = winreg.QueryValueEx(key, "PATH")
                except FileNotFoundError:
                    current_path = ""
            
            install_dir = self.install_dir
            if install_dir.lower() not in current_path.lower():
                new_path = f"{current_path};{install_dir}" if current_path else install_dir
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                # Inform user to restart their session
                QMessageBox.information(
                    self,
                    "PATH Updated",
                    "The installation directory has been added to your user PATH environment variable.\n"
                    "Please restart your command prompt or log out and back in for changes to take effect.",
                    QMessageBox.Ok
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "PATH Update Failed",
                f"Failed to update PATH environment variable automatically.\n"
                f"Please add the following directory to your PATH manually:\n{self.install_dir}\n\nError: {e}",
                QMessageBox.Ok
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a2e32;
            border: 1px solid #3e4451;
        }
    """)
    window = CommitifyApp()
    window.show()
    sys.exit(app.exec_())
