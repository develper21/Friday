#!/usr/bin/env python3
"""
HTTP Server for Phone Tracking
Receives location data from external sources (e.g., Termux script on phone)
and forwards it to the PhoneTrackingController.
"""

import json
import logging
import threading
from typing import Optional, Callable, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from core.security.ssl_server import SecureHTTPServer
    from core.security.auth import AuthManager, SecurityError
    from core.security.rate_limiter import RateLimiter
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False
    logging.warning("Security modules not available, running in insecure mode")


class LocationRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for location data"""
    
    # Class-level storage for the controller reference
    controller = None
    logger = logging
    auth_manager = None
    rate_limiter = None
    
    def _set_response(self, status_code: int = 200, content_type: str = 'application/json'):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def _check_auth(self) -> bool:
        """Check authentication"""
        if self.auth_manager is None:
            return True  # Allow if auth not configured
        
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self._send_error_response('Missing or invalid authorization header', 401)
            return False
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        try:
            user_id = self.auth_manager.verify_token(token)
            return user_id is not None
        except SecurityError as e:
            self._send_error_response(str(e), 401)
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check rate limiting"""
        if self.rate_limiter is None:
            return True  # Allow if rate limiting not configured
        
        client_ip = self.client_address[0]
        if not self.rate_limiter.is_allowed(client_ip):
            self._send_error_response('Rate limit exceeded', 429)
            return False
        
        return True
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        self._set_response(status_code)
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error_response(self, message: str, status_code: int = 400):
        """Send error response"""
        self._send_json_response({
            'success': False,
            'error': message
        }, status_code)
    
    def _send_success_response(self, data: Optional[Dict[str, Any]] = None):
        """Send success response"""
        response = {'success': True}
        if data:
            response.update(data)
        self._send_json_response(response)
    
    def do_GET(self):
        """Handle GET requests"""
        # Check rate limit
        if not self._check_rate_limit():
            return
        
        # Health endpoint doesn't require auth
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self._send_success_response({
                'status': 'healthy',
                'service': 'phone_tracking_http_server'
            })
        elif parsed_path.path == '/status':
            # Check auth for status endpoint
            if not self._check_auth():
                return
            if self.controller:
                summary = self.controller.get_location_summary()
                self._send_success_response(summary)
            else:
                self._send_error_response('Controller not initialized', 503)
        else:
            self._send_error_response('Endpoint not found', 404)
    
    def do_POST(self):
        """Handle POST requests"""
        # Check rate limit
        if not self._check_rate_limit():
            return
        
        # Check auth for all POST endpoints
        if not self._check_auth():
            return
        
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/location':
            self._handle_location_post()
        elif parsed_path.path == '/track/start':
            self._handle_start_tracking()
        elif parsed_path.path == '/track/stop':
            self._handle_stop_tracking()
        else:
            self._send_error_response('Endpoint not found', 404)
    
    def _handle_location_post(self):
        """Handle location data POST request"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length == 0:
                self._send_error_response('No data provided')
                return
            
            # Read and parse JSON data
            post_data = self.rfile.read(content_length)
            location_data = json.loads(post_data.decode('utf-8'))
            
            # Validate required fields
            required_fields = ['latitude', 'longitude']
            for field in required_fields:
                if field not in location_data:
                    self._send_error_response(f'Missing required field: {field}')
                    return
            
            # Validate data types
            try:
                lat = float(location_data['latitude'])
                lon = float(location_data['longitude'])
                
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    self._send_error_response('Invalid coordinates')
                    return
                    
            except (ValueError, TypeError):
                self._send_error_response('Invalid coordinate format')
                return
            
            # Forward to controller
            if self.controller:
                success = self.controller.receive_location(location_data)
                
                if success:
                    self.logger.info(f"Location received via HTTP: {lat}, {lon}")
                    self._send_success_response({
                        'message': 'Location received successfully',
                        'latitude': lat,
                        'longitude': lon
                    })
                else:
                    self._send_error_response('Failed to process location', 500)
            else:
                self._send_error_response('Controller not initialized', 503)
                
        except json.JSONDecodeError:
            self._send_error_response('Invalid JSON data')
        except Exception as e:
            self.logger.error(f"Error handling location POST: {e}")
            self._send_error_response('Internal server error', 500)
    
    def _handle_start_tracking(self):
        """Handle start tracking request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            request_data = json.loads(post_data.decode('utf-8')) if content_length > 0 else {}
            
            mode = request_data.get('mode', 'active')
            
            if self.controller:
                from assistance.controllers.phone_tracking_controller import TrackingMode
                
                tracking_mode = TrackingMode.PASSIVE
                if mode == 'active':
                    tracking_mode = TrackingMode.ACTIVE
                elif mode == 'continuous':
                    tracking_mode = TrackingMode.CONTINUOUS
                
                success = self.controller.start_tracking(tracking_mode)
                
                if success:
                    self._send_success_response({
                        'message': f'Tracking started in {mode} mode'
                    })
                else:
                    self._send_error_response('Failed to start tracking', 500)
            else:
                self._send_error_response('Controller not initialized', 503)
                
        except Exception as e:
            self.logger.error(f"Error handling start tracking: {e}")
            self._send_error_response('Internal server error', 500)
    
    def _handle_stop_tracking(self):
        """Handle stop tracking request"""
        try:
            if self.controller:
                success = self.controller.stop_tracking()
                
                if success:
                    self._send_success_response({
                        'message': 'Tracking stopped'
                    })
                else:
                    self._send_error_response('Failed to stop tracking', 500)
            else:
                self._send_error_response('Controller not initialized', 503)
                
        except Exception as e:
            self.logger.error(f"Error handling stop tracking: {e}")
            self._send_error_response('Internal server error', 500)
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS"""
        self._set_response(200)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log message handler"""
        self.logger.info(f"HTTP Request: {format % args}")


class PhoneTrackingHTTPServer:
    """
    HTTP Server for receiving phone location data
    Runs in a separate thread to avoid blocking the main application
    """
    
    def __init__(self, controller, port: int = 8080, host: str = '0.0.0.0',
                 enable_ssl: bool = True, enable_auth: bool = True,
                 enable_rate_limiting: bool = True):
        """
        Initialize HTTP server
        
        Args:
            controller: PhoneTrackingController instance
            port: Port to listen on
            host: Host to bind to
            enable_ssl: Enable SSL/TLS encryption
            enable_auth: Enable JWT authentication
            enable_rate_limiting: Enable rate limiting
        """
        self.controller = controller
        self.port = port
        self.host = host
        self.enable_ssl = enable_ssl and SSL_AVAILABLE
        self.enable_auth = enable_auth
        self.enable_rate_limiting = enable_rate_limiting
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize security modules
        if self.enable_auth:
            try:
                self.auth_manager = AuthManager()
                LocationRequestHandler.auth_manager = self.auth_manager
                self.logger.info("Authentication enabled")
            except Exception as e:
                self.logger.warning(f"Failed to enable authentication: {e}")
                self.enable_auth = False
        
        if self.enable_rate_limiting:
            try:
                self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
                LocationRequestHandler.rate_limiter = self.rate_limiter
                self.logger.info("Rate limiting enabled")
            except Exception as e:
                self.logger.warning(f"Failed to enable rate limiting: {e}")
                self.enable_rate_limiting = False
    
    def start(self) -> bool:
        """Start the HTTP server in a background thread"""
        if self.is_running:
            self.logger.warning("HTTP server is already running")
            return True
        
        try:
            # Set controller reference in request handler
            LocationRequestHandler.controller = self.controller
            LocationRequestHandler.logger = self.logger
            
            # Create server with or without SSL
            if self.enable_ssl:
                try:
                    self.server = SecureHTTPServer.create_server(
                        self.host, self.port, LocationRequestHandler
                    )
                    protocol = "HTTPS"
                except Exception as e:
                    self.logger.warning(f"Failed to create SSL server, falling back to HTTP: {e}")
                    self.server = HTTPServer((self.host, self.port), LocationRequestHandler)
                    protocol = "HTTP"
            else:
                self.server = HTTPServer((self.host, self.port), LocationRequestHandler)
                protocol = "HTTP"
            
            # Start server in background thread
            self.is_running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.logger.info(f"{protocol} server started on {self.host}:{self.port}")
            return True
            
        except OSError as e:
            if e.errno == 48:  # Address already in use
                self.logger.error(f"Port {self.port} is already in use")
            else:
                self.logger.error(f"Failed to start HTTP server: {e}")
            self.is_running = False
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error starting HTTP server: {e}")
            self.is_running = False
            return False
    
    def _run_server(self):
        """Run the HTTP server (called in background thread)"""
        try:
            self.logger.info("HTTP server thread started")
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"HTTP server error: {e}")
            self.is_running = False
    
    def stop(self) -> bool:
        """Stop the HTTP server"""
        if not self.is_running:
            self.logger.warning("HTTP server is not running")
            return True
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            if self.server_thread:
                self.server_thread.join(timeout=5)
            
            self.is_running = False
            self.logger.info("HTTP server stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping HTTP server: {e}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            'is_running': self.is_running,
            'host': self.host,
            'port': self.port,
            'url': f'http://{self.host}:{self.port}'
        }
    
    def get_available_port(self) -> int:
        """Find an available port if the default is in use"""
        if self.is_running:
            return self.port
        
        for test_port in range(self.port, self.port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, test_port))
                    return test_port
            except OSError:
                continue
        
        return self.port  # Fallback to original port
