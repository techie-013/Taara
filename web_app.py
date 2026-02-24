from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from simple_agent import SimpleTaara
import uvicorn
import json
import os

app = FastAPI(title="Taara AI Agent", description="Simple scheduler with policy enforcement")
agent = SimpleTaara()

class Command(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Taara AI Agent</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .container { border: 2px solid #333; padding: 20px; border-radius: 10px; }
            .allowed { color: green; font-weight: bold; }
            .blocked { color: red; font-weight: bold; }
            input, button { padding: 10px; margin: 10px 0; width: 100%; }
            #result { margin-top: 20px; padding: 10px; border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌟 Taara AI Agent</h1>
            <p>Try these commands:</p>
            <ul>
                <li>Schedule a meeting tomorrow at 2pm</li>
                <li>Remind me to call John</li>
                <li>Add task: Buy groceries</li>
                <li>Delete everything from my calendar (should be blocked)</li>
            </ul>
            
            <input type="text" id="command" placeholder="Enter your command...">
            <button onclick="sendCommand()">Send</button>
            
            <div id="result"></div>
        </div>

        <script>
        async function sendCommand() {
            const command = document.getElementById('command').value;
            const resultDiv = document.getElementById('result');
            
            resultDiv.innerHTML = 'Processing...';
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: command})
                });
                
                const data = await response.json();
                
                if (data.allowed) {
                    resultDiv.innerHTML = '<div class="allowed">✅ ' + data.message + '</div>';
                } else {
                    resultDiv.innerHTML = '<div class="blocked">❌ ' + data.reason + '</div>';
                }
            } catch (error) {
                resultDiv.innerHTML = '<div class="blocked">Error: ' + error + '</div>';
            }
        }
        </script>
    </body>
    </html>
    """

@app.post("/api/process")
async def process_command(command: Command):
    try:
        # Parse
        action, params = agent.parse_input(command.text)
        
        # Check policies
        allowed, reason = agent.check_policies(action, params)
        
        if not allowed:
            return {
                "allowed": False,
                "reason": reason,
                "action": action
            }
        
        # Execute
        result = agent.execute_action(action, params)
        
        # Read calendar to show
        calendar_data = {}
        if os.path.exists(agent.calendar_file):
            with open(agent.calendar_file, 'r') as f:
                calendar_data = json.load(f)
        
        return {
            "allowed": True,
            "message": result['message'],
            "action": action,
            "calendar": calendar_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/calendar")
async def get_calendar():
    if os.path.exists(agent.calendar_file):
        with open(agent.calendar_file, 'r') as f:
            return json.load(f)
    return {"events": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
