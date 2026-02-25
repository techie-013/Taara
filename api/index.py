from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from simple_agent import SimpleTaara
except ImportError as e:
    print(f"Import error: {e}")

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
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
                "GET /api/health": "Health check",
                "POST /api/process": "Process a command"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/process':
            try:
                # Get content length
                content_length = int(self.headers.get('Content-Length', 0))
                
                # Read POST data
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('text', '')
                
                # Process command
                agent = SimpleTaara()
                action, params = agent.parse_input(command)
                allowed, reason = agent.check_policies(action, params)
                
                response = {
                    "allowed": allowed,
                    "command": command,
                    "action": action
                }
                
                if allowed:
                    result = agent.execute_action(action, params)
                    response["message"] = result.get('message', 'Command executed')
                else:
                    response["reason"] = reason
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        # Handle unknown paths
        self.send_response(404)
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()