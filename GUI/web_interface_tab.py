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
import os
import webbrowser


class WebInterfaceTab(QtWidgets.QWidget):
    """Tab for accessing the TI-CSC web interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface for the web interface tab."""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Title and description
        title_label = QtWidgets.QLabel("TI-CSC Net Viewer")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        
        description_label = QtWidgets.QLabel(
            "Access the interactive 3D network visualization interface for TI-CSC. "
            "The Net Viewer provides real-time 3D visualization of electrode networks, "
            "brain anatomy, and field distributions with advanced Three.js rendering."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px; color: #34495e; margin-bottom: 20px;")
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addSpacing(20)
        
        # Performance Mode Selection
        performance_frame = QtWidgets.QFrame()
        performance_frame.setFrameStyle(QtWidgets.QFrame.Box)
        performance_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        performance_layout = QtWidgets.QVBoxLayout(performance_frame)
        
        performance_title = QtWidgets.QLabel("🚀 Performance Mode Selection")
        performance_title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        performance_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # Host Browser option (recommended)
        self.host_radio = QtWidgets.QRadioButton("Host Browser (Recommended)")
        self.host_radio.setChecked(True)
        self.host_radio.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.host_radio.setStyleSheet("color: #27ae60; margin: 5px;")
        
        host_desc = QtWidgets.QLabel("✅ Launches your default browser on Windows host\n✅ Full native GPU acceleration and performance\n✅ Best experience for 3D visualization")
        host_desc.setStyleSheet("color: #27ae60; margin-left: 20px; font-size: 9pt;")
        host_desc.setWordWrap(True)
        
        # Docker Chrome option
        self.docker_radio = QtWidgets.QRadioButton("Docker Chrome (Fallback)")
        self.docker_radio.setFont(QtGui.QFont("Arial", 10))
        self.docker_radio.setStyleSheet("color: #e67e22; margin: 5px;")
        
        docker_desc = QtWidgets.QLabel("⚠️ Chrome inside Docker with X11 forwarding\n⚠️ Software rendering, limited performance\n💡 Use only if host browser fails to connect")
        docker_desc.setStyleSheet("color: #e67e22; margin-left: 20px; font-size: 9pt;")
        docker_desc.setWordWrap(True)
        
        performance_layout.addWidget(performance_title)
        performance_layout.addWidget(self.host_radio)
        performance_layout.addWidget(host_desc)
        performance_layout.addWidget(self.docker_radio)
        performance_layout.addWidget(docker_desc)
        
        main_layout.addWidget(performance_frame)
        
        # Status section
        status_frame = QtWidgets.QFrame()
        status_frame.setFrameStyle(QtWidgets.QFrame.Box)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        status_layout = QtWidgets.QVBoxLayout(status_frame)
        
        status_title = QtWidgets.QLabel("📊 Service Status")
        status_title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        status_title.setStyleSheet("color: #2c3e50;")
        
        # API Server status
        api_status_layout = QtWidgets.QHBoxLayout()
        self.api_status_label = QtWidgets.QLabel("API Server:")
        self.api_status_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.api_status_indicator = QtWidgets.QLabel("●")
        self.api_status_indicator.setFont(QtGui.QFont("Arial", 16))
        self.api_status_text = QtWidgets.QLabel("Checking...")
        api_status_layout.addWidget(self.api_status_label)
        api_status_layout.addWidget(self.api_status_indicator)
        api_status_layout.addWidget(self.api_status_text)
        api_status_layout.addStretch()
        
        # Net Viewer status
        viewer_status_layout = QtWidgets.QHBoxLayout()
        self.viewer_status_label = QtWidgets.QLabel("Net Viewer:")
        self.viewer_status_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.viewer_status_indicator = QtWidgets.QLabel("●")
        self.viewer_status_indicator.setFont(QtGui.QFont("Arial", 16))
        self.viewer_status_text = QtWidgets.QLabel("Checking...")
        viewer_status_layout.addWidget(self.viewer_status_label)
        viewer_status_layout.addWidget(self.viewer_status_indicator)
        viewer_status_layout.addWidget(self.viewer_status_text)
        viewer_status_layout.addStretch()
        
        status_layout.addWidget(status_title)
        status_layout.addLayout(api_status_layout)
        status_layout.addLayout(viewer_status_layout)
        
        main_layout.addWidget(status_frame)
        
        # Launch button
        self.launch_button = QtWidgets.QPushButton("🚀 Launch Net Viewer")
        self.launch_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.launch_button.setMinimumHeight(50)
        self.launch_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a569c7, stop:1 #9b59b6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.launch_button.clicked.connect(self.launch_net_viewer)
        
        main_layout.addWidget(self.launch_button)
        
        # Performance tips
        tips_frame = QtWidgets.QFrame()
        tips_frame.setFrameStyle(QtWidgets.QFrame.Box)
        tips_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e8;
                border: 2px solid #c3e6c3;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        tips_layout = QtWidgets.QVBoxLayout(tips_frame)
        
        tips_title = QtWidgets.QLabel("💡 Performance Tips")
        tips_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        tips_title.setStyleSheet("color: #2c3e50;")
        
        tips_text = QtWidgets.QLabel("""
• Host Browser: Launches your default Windows browser on host for maximum performance
• Docker Chrome: Fallback option that runs Chrome inside Docker with X11 forwarding
• Host Browser uses native GPU acceleration and Windows graphics pipeline
• Docker Chrome requires VcXsrv/X11 server and has limited performance
• Host Browser automatically detected when containers start
        """.strip())
        tips_text.setStyleSheet("color: #27ae60; font-size: 9pt;")
        tips_text.setWordWrap(True)
        
        tips_layout.addWidget(tips_title)
        tips_layout.addWidget(tips_text)
        
        main_layout.addWidget(tips_frame)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Auto-check status on startup
        QTimer.singleShot(1000, self.check_web_service)
    
    def launch_net_viewer(self):
        """Launch the net viewer based on selected mode"""
        # Check appropriate service based on mode
        if self.host_radio.isChecked():
            # For host browser, check if we can reach the service via host IP
            if not self.check_host_service():
                reply = QtWidgets.QMessageBox.question(
                    self, "Service Check", 
                    "Cannot reach the Net Viewer service from host\n\n"
                    "This could mean:\n"
                    "• Net viewer container is not running\n"
                    "• Host IP detection failed\n"
                    "• Port 3000 is not accessible\n\n"
                    "Would you like to try launching anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    return
            self.launch_host_browser()
        else:
            # For Docker Chrome, check internal Docker URL
            if not self.check_services():
                QtWidgets.QMessageBox.warning(self, "Service Error", 
                                              "Net Viewer service is not available. Please check that the Docker containers are running.")
                return
            self.launch_docker_chrome()
    
    def launch_host_browser(self):
        """Launch browser on Windows host using localhost (Docker port mapping)"""
        try:
            # Use localhost since we're launching on the host side
            url = "http://localhost:3000"
            print(f"🌐 Creating browser launch trigger for: {url}")
            print(f"🔧 Using localhost (Docker port mapping)")
            
            # Create a trigger file for the host to monitor
            self.create_browser_trigger(url)
            
            QtWidgets.QMessageBox.information(self, "Host Browser Opening", 
                                              f"🚀 Browser opening automatically on Windows host!\n\n"
                                              f"URL: {url}\n"
                                              f"Method: Host-side browser launch\n\n"
                                              f"The browser should open within 2-3 seconds...\n"
                                              f"If it doesn't open, try Docker Chrome fallback.")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Host Browser Error", 
                                          f"Failed to create browser trigger!\n\n"
                                          f"Error: {e}\n\n"
                                          f"Try the Docker Chrome fallback option instead.")
            print(f"❌ Failed to create host browser trigger: {e}")
    
    def create_browser_trigger(self, url):
        """Create a trigger file that the host can monitor to launch browser"""
        try:
            import os
            import json
            from datetime import datetime
            
            # Get the project directory path inside Docker
            project_dir_name = os.environ.get('PROJECT_DIR_NAME', '')
            if project_dir_name:
                trigger_dir = os.path.join('/mnt', project_dir_name, ".ti-csc-info")
            else:
                trigger_dir = "/mnt/.ti-csc-info"
            
            # Ensure directory exists
            os.makedirs(trigger_dir, exist_ok=True)
            
            # Create trigger file with browser launch request
            trigger_file = os.path.join(trigger_dir, "launch_browser_trigger.json")
            
            trigger_data = {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "action": "launch_browser",
                "source": "ti_csc_gui"
            }
            
            with open(trigger_file, 'w') as f:
                json.dump(trigger_data, f, indent=2)
            
            print(f"✅ Browser trigger file created: {trigger_file}")
            print(f"📄 Trigger data: {trigger_data}")
            print(f"🔄 Host monitor should automatically open browser...")
            
        except Exception as e:
            print(f"❌ Failed to create browser trigger file: {e}")
            raise




    
    def launch_docker_chrome(self):
        """Launch Chrome inside Docker container (compatibility mode)"""
        try:
            # Original Docker Chrome command
            url = "http://net_viewer:3000"
            
            chrome_flags = [
                "--new-window",
                f"--app={url}",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--enable-gpu",
                "--enable-gpu-rasterization",
                "--max_old_space_size=4096",
                "--process-per-site",
                "--max-gum-fps=60",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--test-type",
                "--disable-gpu-sandbox",
                "--user-data-dir=/tmp/chrome-ti-csc",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--disable-contextual-search",
                "--disable-tab-for-desktop-share",
                "--allow-running-insecure-content",
                "--kiosk-printing"
            ]
            
            # Build the Docker command
            chrome_cmd = " ".join([
                "nohup google-chrome",
                " ".join(chrome_flags),
                ">/dev/null 2>&1 &", 
                "disown"
            ])
            
            docker_cmd = [
                "docker", "exec", "-d", 
                "simnibs_container",
                "bash", "-c", chrome_cmd
            ]
            
            # Execute with complete detachment
            subprocess.Popen(docker_cmd, 
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            QtWidgets.QMessageBox.information(self, "Docker Chrome", 
                                          f"🐳 Docker Chrome launched in compatibility mode\n\n"
                                          f"URL: {url}\n"
                                          f"Mode: Software Rendering\n"
                                          f"Performance: Limited by X11 forwarding")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to launch Docker Chrome: {e}")
    
    def check_services(self):
        """Check if the net viewer service is available via Docker internal URL."""
        web_url = "http://net_viewer:3000"
        
        try:
            response = urllib.request.urlopen(web_url, timeout=2)
            if response.getcode() == 200:
                self.viewer_status_text.setText("🟢 Online")
                self.viewer_status_text.setStyleSheet("color: #27ae60; font-weight: bold;")
                return True
            else:
                raise Exception(f"HTTP {response.getcode()}")
                
        except Exception as e:
            self.viewer_status_text.setText("🔴 Offline")
            self.viewer_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
            return False

    def check_host_service(self):
        """Check if the net viewer service is available from host perspective."""
        # Since we use localhost:3000 for host browser, check if port 3000 is accessible
        try:
            # Test if port 3000 is accessible (this will work via Docker port mapping)
            docker_cmd = [
                "docker", "exec", 
                "simnibs_container",
                "bash", "-c", 
                "curl -s --connect-timeout 3 http://net_viewer:3000 >/dev/null 2>&1"
            ]
            
            result = subprocess.run(docker_cmd, 
                                  capture_output=True, 
                                  timeout=5)
            
            return result.returncode == 0
                
        except Exception as e:
            return False
    
    def check_web_service(self):
        """Check if the net viewer service is available."""
        web_url = "http://net_viewer:3000"
        
        try:
            response = urllib.request.urlopen(web_url, timeout=2)
            if response.getcode() == 200:
                self.viewer_status_text.setText("🟢 Online")
                self.viewer_status_text.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                raise Exception(f"HTTP {response.getcode()}")
                
        except Exception as e:
            self.viewer_status_text.setText("🔴 Offline")
            self.viewer_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        from datetime import datetime
        self.api_status_text.setText(f"Last checked: {datetime.now().strftime('%H:%M:%S')}")
    
    def refresh_status(self):
        """Refresh the web service status."""
        self.viewer_status_text.setText("Checking...")
        self.viewer_status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
        self.api_status_text.setText("Checking...")
        self.api_status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        # Delay check to show loading state
        QTimer.singleShot(500, self.check_web_service) 