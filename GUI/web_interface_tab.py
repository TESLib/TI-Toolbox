#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TI-CSC-2.0 Web Interface Tab
This module provides a GUI interface for accessing the TI-CSC web interface.
Launches browsers in app mode for a focused user experience.
"""

import subprocess
import urllib.request
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer


class WebInterfaceTab(QtWidgets.QWidget):
    """Tab for accessing the TI-CSC web interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface for the web interface tab."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Title and description
        title_label = QtWidgets.QLabel("TI-CSC Web Interface")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        
        description_label = QtWidgets.QLabel(
            "Access the modern web-based interface for TI-CSC operations. "
            "The web interface provides an intuitive dashboard for monitoring, "
            "controlling, and interacting with your toolbox processes."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px; color: #34495e; margin-bottom: 20px;")
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addSpacing(20)
        
        # Web Interface Status Card
        status_group = QtWidgets.QGroupBox("Interface Status")
        status_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        status_layout = QtWidgets.QVBoxLayout(status_group)
        
        # Status indicators
        status_row = QtWidgets.QHBoxLayout()
        
        # Web service status
        web_status_label = QtWidgets.QLabel("Web Service:")
        web_status_label.setStyleSheet("font-weight: bold;")
        self.web_status = QtWidgets.QLabel("Checking...")
        self.web_status.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        status_row.addWidget(web_status_label)
        status_row.addWidget(self.web_status)
        status_row.addStretch()
        
        # Last check time
        self.last_check_label = QtWidgets.QLabel("Last checked: Never")
        self.last_check_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        status_layout.addLayout(status_row)
        status_layout.addWidget(self.last_check_label)
        
        main_layout.addWidget(status_group)
        
        # Web Interface Access Card
        access_group = QtWidgets.QGroupBox("Access Web Interface")
        access_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        access_layout = QtWidgets.QVBoxLayout(access_group)
        
        # URL display
        url_layout = QtWidgets.QHBoxLayout()
        url_label = QtWidgets.QLabel("Interface URL:")
        url_label.setStyleSheet("font-weight: bold;")
        self.url_display = QtWidgets.QLabel("http://webapp:3000")
        self.url_display.setStyleSheet("color: #3498db; font-family: monospace; background: #ecf0f1; padding: 5px; border-radius: 3px;")
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_display)
        url_layout.addStretch()
        
        access_layout.addLayout(url_layout)
        access_layout.addSpacing(10)
        
        # Main launch button
        self.launch_button = QtWidgets.QPushButton("🌐 Open Web Interface")
        self.launch_button.clicked.connect(self.open_web_interface)
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        self.launch_button.setToolTip("Launch the TI-CSC web interface in a dedicated browser window")
        
        access_layout.addWidget(self.launch_button)
        
        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.check_status_btn = QtWidgets.QPushButton("🔍 Check Status")
        self.check_status_btn.clicked.connect(self.check_web_service)
        self.check_status_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px 16px; border-radius: 4px;")
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.refresh_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 8px 16px; border-radius: 4px;")
        
        button_layout.addWidget(self.check_status_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        access_layout.addLayout(button_layout)
        
        main_layout.addWidget(access_group)
        
        # Information Card
        info_group = QtWidgets.QGroupBox("Features")
        info_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        info_layout = QtWidgets.QVBoxLayout(info_group)
        
        features_text = """
        ✅ Real-time communication with PyQt GUI
        ✅ Modern responsive web interface
        ✅ Process monitoring and control
        ✅ Analysis triggering and results viewing
        ✅ Interactive dashboard with status updates
        ✅ Tab creation prevention for focused workflow
        ✅ Professional app-style window (no browser UI)
        """
        
        features_label = QtWidgets.QLabel(features_text)
        features_label.setStyleSheet("color: #2c3e50; line-height: 1.6;")
        info_layout.addWidget(features_label)
        
        main_layout.addWidget(info_group)
        
        # Status message at bottom
        self.status_message = QtWidgets.QLabel("Ready to launch web interface")
        self.status_message.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px; background: #d5f4e6; border-radius: 4px;")
        main_layout.addWidget(self.status_message)
        
        main_layout.addStretch()
        
        # Auto-check status on startup
        QTimer.singleShot(1000, self.check_web_service)
    
    def open_web_interface(self):
        """Open the TI-CSC web interface in a dedicated browser window."""
        web_url = "http://webapp:3000"
        
        try:
            # Check if the web service is available
            try:
                response = urllib.request.urlopen(web_url, timeout=3)
                if response.getcode() == 200:
                    # Web service is available, try to open with available browser
                    browser_opened = self.launch_browser(web_url)
                    if browser_opened:
                        self.status_message.setText("✅ Web interface opened successfully")
                        self.status_message.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px; background: #d5f4e6; border-radius: 4px;")
                        
                        # Show success message
                        QtWidgets.QMessageBox.information(
                            self, 
                            "Web Interface Launched", 
                            f"TI-CSC web interface opened successfully!\n\n"
                            f"URL: {web_url}\n\n"
                            f"The interface opens in app mode with:\n"
                            f"• No address bar or tabs\n"
                            f"• Tab creation prevention\n"
                            f"• Focused workflow environment\n\n"
                            f"You can close the window normally when finished."
                        )
                    else:
                        self.status_message.setText("❌ No browser available - install Google Chrome")
                        self.status_message.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px; background: #fadbd8; border-radius: 4px;")
                        
                        QtWidgets.QMessageBox.warning(
                            self, 
                            "Browser Not Available", 
                            f"Web interface is running at: {web_url}\n\n"
                            f"No browser found in container. Install one with:\n"
                            f"• apt update && apt install -y google-chrome-stable\n\n"
                            f"Then try again to open the interface."
                        )
                else:
                    raise Exception(f"HTTP {response.getcode()}")
                    
            except Exception:
                # Web service not available, show instructions
                self.status_message.setText("❌ Web service not available")
                self.status_message.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px; background: #fadbd8; border-radius: 4px;")
                
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Web Interface Not Available",
                    f"The TI-CSC web interface is not currently running.\n\n"
                    f"Expected URL: {web_url}\n\n"
                    f"To start the web interface:\n"
                    f"1. Make sure Docker services are running\n"
                    f"2. The webapp container should be active\n"
                    f"3. Check docker logs for any errors\n\n"
                    f"Would you like to try opening the URL anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    self.launch_browser(web_url)
                    
        except Exception as e:
            self.status_message.setText(f"❌ Error: {str(e)}")
            self.status_message.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px; background: #fadbd8; border-radius: 4px;")
            
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to open web interface:\n{str(e)}\n\n"
                f"URL: {web_url}"
            )
    
    def launch_browser(self, url):
        """Try to launch a browser with the given URL. Returns True if successful."""
        # KIOSK MODE: Complete lockdown (uncomment to use instead of app mode)
        kiosk_browsers = [
            ['google-chrome-stable', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--kiosk', '--disable-infobars', '--disable-notifications', '--disable-default-apps', '--test-type', '--disable-logging', '--silent-debugger-extension-api', '--disable-breakpad', url],
            ['google-chrome', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--kiosk', '--disable-infobars', '--disable-notifications', '--disable-default-apps', '--test-type', '--disable-logging', '--silent-debugger-extension-api', '--disable-breakpad', url],
        ]
        
        # APP MODE: Less restrictive (current mode)
        app_browsers = [
            ['google-chrome-stable', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--app=' + url, '--disable-web-security', '--disable-features=VizDisplayCompositor', '--disable-infobars', '--disable-notifications', '--disable-default-apps', '--disable-session-crashed-bubble', '--disable-restore-session-state', '--no-first-run', '--no-default-browser-check', '--disable-component-extensions-with-background-pages', '--disable-extensions', '--disable-translate', '--disable-background-timer-throttling', '--test-type', '--disable-logging', '--silent-debugger-extension-api', '--disable-breakpad', '--disable-new-tab-first-run', '--disable-background-mode', '--disable-sync', '--disable-client-side-phishing-detection', '--overscroll-history-navigation=0', '--disable-pinch'],
            ['google-chrome', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--app=' + url, '--disable-web-security', '--disable-features=VizDisplayCompositor', '--disable-infobars', '--disable-notifications', '--disable-default-apps', '--disable-session-crashed-bubble', '--disable-restore-session-state', '--no-first-run', '--no-default-browser-check', '--disable-component-extensions-with-background-pages', '--disable-extensions', '--disable-translate', '--disable-background-timer-throttling', '--test-type', '--disable-logging', '--silent-debugger-extension-api', '--disable-breakpad', '--disable-new-tab-first-run', '--disable-background-mode', '--disable-sync', '--disable-client-side-phishing-detection', '--overscroll-history-navigation=0', '--disable-pinch'],
            ['chromium', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-extensions', '--disable-plugins', '--new-window', url],
            ['firefox', '--new-window', url],
            ['firefox-esr', '--new-window', url],
            ['links2', '-g', url]
        ]
        
        # Use app mode with enhanced tab prevention (windowed, can quit, but no new tabs)
        browsers = app_browsers
        
        for browser_cmd in browsers:
            try:
                subprocess.Popen(browser_cmd, 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL)
                print(f"✅ Launched browser: {browser_cmd[0]}")
                return True
            except FileNotFoundError:
                print(f"❌ Browser not found: {browser_cmd[0]}")
                continue
            except Exception as e:
                print(f"❌ Error launching {browser_cmd[0]}: {e}")
                continue
        
        print("❌ No suitable browser found. Install one with:")
        print("   apt update && apt install -y google-chrome-stable")
        print("   or: apt update && apt install -y chromium-browser")
        return False
    
    def check_web_service(self):
        """Check if the web service is available."""
        web_url = "http://webapp:3000"
        
        try:
            response = urllib.request.urlopen(web_url, timeout=2)
            if response.getcode() == 200:
                self.web_status.setText("🟢 Online")
                self.web_status.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.status_message.setText("✅ Web service is online and ready")
                self.status_message.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px; background: #d5f4e6; border-radius: 4px;")
            else:
                raise Exception(f"HTTP {response.getcode()}")
                
        except Exception as e:
            self.web_status.setText("🔴 Offline")
            self.web_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.status_message.setText("❌ Web service is not available")
            self.status_message.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px; background: #fadbd8; border-radius: 4px;")
        
        from datetime import datetime
        self.last_check_label.setText(f"Last checked: {datetime.now().strftime('%H:%M:%S')}")
    
    def refresh_status(self):
        """Refresh the web service status."""
        self.web_status.setText("Checking...")
        self.web_status.setStyleSheet("color: #f39c12; font-weight: bold;")
        self.status_message.setText("🔄 Refreshing status...")
        self.status_message.setStyleSheet("color: #f39c12; font-weight: bold; padding: 10px; background: #fdeaa7; border-radius: 4px;")
        
        # Delay check to show loading state
        QTimer.singleShot(500, self.check_web_service) 