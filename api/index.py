import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
import json
from simple_agent import SimpleTaara
from urllib.parse import parse_qs
import json

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/api/calendar':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            agent = SimpleTaara()
            if os.path.exists(agent.calendar_file):
                with open(agent.calendar_file, 'r') as f:
                    calendar = json.load(f)
                self.wfile.write(json.dumps(calendar).encode())
            else:
                self.wfile.write(json.dumps({"events": []}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Taara API is running')
        
    def do_POST(self):
        if self.path == '/api/process':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            agent = SimpleTaara()
            command = data.get('text', '')
            
            # Parse
            action, params = agent.parse_input(command)
            
            # Check policies
            allowed, reason = agent.check_policies(action, params)
            
            response = {
                "command": command,
                "action": action,
                "allowed": allowed
            }
            
            if allowed:
                result = agent.execute_action(action, params)
                response["message"] = result['message']
                response["status"] = "success"
            else:
                response["reason"] = reason
                response["status"] = "blocked"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
            return
        
        self.send_response(404)
        self.end_headers()
