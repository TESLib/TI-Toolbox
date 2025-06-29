#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple HTTP API Server for PyQt5 GUI
Provides REST API endpoints for web app communication.
"""

import json
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from PyQt5.QtCore import QObject, pyqtSignal


class APIRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the API server."""
    
    def __init__(self, *args, gui_bridge=None, **kwargs):
        self.gui_bridge = gui_bridge
        super().__init__(*args, **kwargs)
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Set common HTTP headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response."""
        self._set_headers(status_code)
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error_response(self, message, status_code=500):
        """Send error response."""
        self._send_json_response({
            'error': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }, status_code)
    
    def _get_request_body(self):
        """Get and parse request body."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except Exception as e:
            return None
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            path = self.path.split('?')[0]  # Remove query parameters
            
            if path == '/api/status':
                self._handle_status()
            elif path == '/api/info':
                self._handle_info()
            elif path == '/api/ping':
                self._handle_ping()
            elif path == '/api/results':
                self._handle_get_results()
            else:
                self._send_error_response(f'Endpoint not found: {path}', 404)
                
        except Exception as e:
            print(f"API GET Error: {e}")
            self._send_error_response(str(e))
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            path = self.path.split('?')[0]  # Remove query parameters
            body = self._get_request_body()
            
            if body is None:
                self._send_error_response('Invalid JSON in request body', 400)
                return
            
            if path == '/api/ping':
                self._handle_ping(body)
            elif path == '/api/message':
                self._handle_message(body)
            elif path == '/api/analysis':
                self._handle_analysis(body)
            else:
                self._send_error_response(f'Endpoint not found: {path}', 404)
                
        except Exception as e:
            print(f"API POST Error: {e}")
            self._send_error_response(str(e))
    
    def _handle_status(self):
        """Handle status endpoint."""
        status = {
            'status': 'ok',
            'service': 'TI-CSC PyQt GUI API',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - getattr(self.gui_bridge, 'start_time', time.time()),
            'gui_active': True
        }
        self._send_json_response(status)
    
    def _handle_info(self):
        """Handle info endpoint."""
        info = {
            'service': 'TI-CSC PyQt GUI API',
            'version': '1.0.0',
            'description': 'HTTP API for TI-CSC PyQt5 GUI communication',
            'endpoints': [
                'GET /api/status - Service status',
                'GET /api/info - Service information',
                'GET /api/ping - Ping test',
                'POST /api/ping - Ping with data',
                'POST /api/message - Send message to GUI',
                'POST /api/analysis - Trigger analysis',
                'GET /api/results - Get analysis results'
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # Add GUI-specific info if available
        if self.gui_bridge:
            info['gui_info'] = self.gui_bridge.get_gui_info()
        
        self._send_json_response(info)
    
    def _handle_ping(self, data=None):
        """Handle ping endpoint."""
        response = {
            'pong': True,
            'timestamp': datetime.now().isoformat(),
            'server': 'TI-CSC PyQt GUI API'
        }
        
        if data:
            response['received_data'] = data
            response['echo'] = data.get('message', 'No message')
        
        # Notify GUI if bridge is available
        if self.gui_bridge:
            self.gui_bridge.on_web_ping(data or {})
        
        self._send_json_response(response)
    
    def _handle_message(self, data):
        """Handle message endpoint."""
        message = data.get('message', '')
        sender = data.get('from', 'unknown')
        
        # Send to GUI if bridge is available
        if self.gui_bridge:
            gui_response = self.gui_bridge.on_web_message(message, sender)
        else:
            gui_response = "GUI bridge not available"
        
        response = {
            'received': True,
            'message': message,
            'from': sender,
            'gui_response': gui_response,
            'timestamp': datetime.now().isoformat()
        }
        
        self._send_json_response(response)
    
    def _handle_analysis(self, data):
        """Handle analysis endpoint."""
        analysis_type = data.get('type', 'unknown')
        parameters = data.get('parameters', {})
        
        # Send to GUI if bridge is available
        if self.gui_bridge:
            result = self.gui_bridge.on_web_analysis_request(analysis_type, parameters)
        else:
            result = {
                'status': 'error',
                'message': 'GUI bridge not available'
            }
        
        response = {
            'analysis_triggered': True,
            'type': analysis_type,
            'parameters': parameters,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        self._send_json_response(response)
    
    def _handle_get_results(self):
        """Handle get results endpoint."""
        if self.gui_bridge:
            results = self.gui_bridge.get_analysis_results()
        else:
            results = {
                'status': 'error',
                'message': 'GUI bridge not available'
            }
        
        response = {
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        self._send_json_response(response)
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        # Uncomment to see all requests:
        # print(f"[API] {format % args}")
        pass


class GUIBridge(QObject):
    """Bridge between HTTP API and PyQt GUI."""
    
    # Signals for GUI communication
    web_message_received = pyqtSignal(str, str)  # message, sender
    web_ping_received = pyqtSignal(dict)  # ping data
    web_analysis_requested = pyqtSignal(str, dict)  # type, parameters
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.start_time = time.time()
        self.analysis_results = []
        
    def get_gui_info(self):
        """Get information about the GUI state."""
        info = {
            'window_title': 'TI-CSC Toolbox',
            'tabs_available': [],
            'current_tab': 'unknown',
            'status': 'active'
        }
        
        if self.main_window:
            try:
                info['window_title'] = self.main_window.windowTitle()
                # Add more GUI-specific info here
                if hasattr(self.main_window, 'tab_widget'):
                    tab_count = self.main_window.tab_widget.count()
                    info['tab_count'] = tab_count
                    info['current_tab_index'] = self.main_window.tab_widget.currentIndex()
                    
                    # Get tab names
                    for i in range(tab_count):
                        tab_name = self.main_window.tab_widget.tabText(i)
                        info['tabs_available'].append(tab_name)
                        
            except Exception as e:
                info['error'] = str(e)
        
        return info
    
    def on_web_ping(self, data):
        """Handle ping from web interface."""
        print(f"🏓 Web ping received: {data}")
        self.web_ping_received.emit(data)
        
    def on_web_message(self, message, sender):
        """Handle message from web interface."""
        print(f"📨 Web message from {sender}: {message}")
        self.web_message_received.emit(message, sender)
        return f"Message '{message}' received by GUI"
    
    def on_web_analysis_request(self, analysis_type, parameters):
        """Handle analysis request from web interface."""
        print(f"🧪 Web analysis request: {analysis_type} with {parameters}")
        self.web_analysis_requested.emit(analysis_type, parameters)
        
        # Simulate analysis result
        result = {
            'status': 'started',
            'id': f'analysis_{int(time.time())}',
            'type': analysis_type,
            'message': f'{analysis_type} analysis started successfully'
        }
        
        # Store result
        self.analysis_results.append({
            'id': result['id'],
            'type': analysis_type,
            'parameters': parameters,
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'result': f'Mock result for {analysis_type} analysis'
        })
        
        return result
    
    def get_analysis_results(self):
        """Get stored analysis results."""
        return {
            'count': len(self.analysis_results),
            'results': self.analysis_results[-5:],  # Return last 5 results
            'status': 'success'
        }


class APIServer:
    """HTTP API Server for PyQt GUI."""
    
    def __init__(self, port=8080, main_window=None):
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        self.gui_bridge = GUIBridge(main_window)
        
    def create_handler(self):
        """Create request handler with GUI bridge."""
        def handler(*args, **kwargs):
            return APIRequestHandler(*args, gui_bridge=self.gui_bridge, **kwargs)
        return handler
    
    def start(self):
        """Start the API server in a separate thread."""
        if self.running:
            return False
        
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), self.create_handler())
            self.running = True
            
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            print(f"🚀 API Server started on port {self.port}")
            print(f"📡 API Base URL: http://localhost:{self.port}/api/")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return False
    
    def stop(self):
        """Stop the API server."""
        if not self.running:
            return
            
        self.running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        print("🛑 API Server stopped")
    
    def _run_server(self):
        """Run the server loop."""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:  # Only log if not intentionally stopped
                print(f"❌ API Server error: {e}")
        finally:
            self.running = False
    
    def is_running(self):
        """Check if server is running."""
        return self.running
    
    def get_bridge(self):
        """Get the GUI bridge for signal connections."""
        return self.gui_bridge 