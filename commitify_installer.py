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
        self.fetch_releases()
        self.home_dir = os.path.expanduser("~")
        self.install_dir = os.path.join(self.home_dir, "bin")
        os.makedirs(self.install_dir, exist_ok=True)

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
        self.download_btn.setEnabled(len(releases) > 0)
        
        if latest_release:
            index = self.release_dropdown.findText(latest_release)
            if index >= 0:
                self.release_dropdown.setCurrentIndex(index)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.release_dropdown.setPlaceholderText("Failed to load releases")

    def handle_download(self):
        selected_release = self.release_dropdown.currentText()
        if not selected_release:
            return

        try:
            release_url = f"https://api.github.com/repos/kokofixcomputers/Commitify/releases/tags/{selected_release}"
            response = requests.get(release_url)
            response.raise_for_status()
            release_data = response.json()
            
            # Find platform-specific asset
            asset = self.find_platform_asset(release_data['assets'])
            if not asset:
                QMessageBox.critical(self, "Error", "No compatible binary found for your system")
                return

            binary_name = "commitify"  # Final installed name
            download_path = os.path.join(self.install_dir, binary_name)
            self.download_file(asset['browser_download_url'], download_path)
            os.chmod(download_path, 0o755)  # Make executable
            
            self.update_shell_profile()
            
            QMessageBox.information(
                self, 
                "Success", 
                f"""Commitify has been installed successfully! You may need to restart your terminal to use it.""",
                QMessageBox.Ok
            )
            
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
            "linux": ["linux", "ubuntu", "debian"]
        }
        
        current_system = sys.platform.lower()
        target_keywords = system_map.get(current_system, [])
        
        for asset in assets:
            if any(keyword in asset['name'].lower() for keyword in target_keywords):
                return asset
        return None

    def download_file(self, url, save_path):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def update_shell_profile(self):
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
