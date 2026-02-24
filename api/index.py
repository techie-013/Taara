import sys
import os
import json
from http.server import BaseHTTPRequestHandler

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from simple_agent import SimpleTaara
except ImportError as e:
    print(f"Import error: {e}")

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Taara API is running",
            "endpoints": {
                "GET /": "This message",
                "GET /api/health": "Health check",
                "POST /api/process": "Process a command"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/process':
            try:
                # Get content length
                content_length = int(self.headers.get('Content-Length', 0))
                
                # Read POST data
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    command = data.get('text', '')
                else:
                    command = ''
                
                # Process command
                try:
                    agent = SimpleTaara()
                    action, params = agent.parse_input(command)
                    allowed, reason = agent.check_policies(action, params)
                    
                    if allowed:
                        result = agent.execute_action(action, params)
                        response = {
                            "allowed": True,
                            "message": result.get('message', 'Command executed'),
                            "action": action
                        }
                    else:
                        response = {
                            "allowed": False,
                            "reason": reason,
                            "action": action
                        }
                except Exception as e:
                    response = {
                        "allowed": False,
                        "reason": f"Error processing command: {str(e)}"
                    }
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                # Send error response
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": str(e)
                }).encode())
            
            return
        
        # Handle unknown paths
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "Not found"
        }).encode())
