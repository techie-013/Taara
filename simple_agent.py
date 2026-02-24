#!/usr/bin/env python3
"""
Taara - Simple OpenClaw Agent
"""

import os
import yaml
import json
from datetime import datetime, timedelta
import re
from colorama import init, Fore, Style

# Initialize colorama
init()

class SimpleTaara:
    def __init__(self):
        self.name = "Taara"
        self.load_policies()
        self.calendar_file = os.path.join(os.path.expanduser("~"), "taara_calendar.json")
        
    def load_policies(self):
        """Load simple policies"""
        try:
            with open('policies.yaml', 'r') as f:
                self.policies = yaml.safe_load(f)
            print(f"{Fore.GREEN}✓ Policies loaded{Style.RESET_ALL}")
        except Exception as e:
            self.policies = []
            print(f"{Fore.YELLOW}⚠ No policies file found: {e}{Style.RESET_ALL}")
    
    def check_policies(self, action, params):
        """Simple policy check"""
        current_hour = datetime.now().hour
        
        for policy in self.policies:
            if policy.get('type') == 'time_restriction':
                if current_hour not in policy.get('allowed_hours', []):
                    return False, f"Not allowed at {current_hour}:00"
            
            if policy.get('type') == 'operation_restriction':
                if action in policy.get('blocked_ops', []):
                    return False, f"Operation '{action}' is blocked"
        
        return True, "Allowed"
    
    def execute_action(self, action, params):
        """Execute the action"""
        if action == "schedule":
            return self.schedule_meeting(params)
        elif action == "remind":
            return self.set_reminder(params)
        elif action == "task":
            return self.create_task(params)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    
    def schedule_meeting(self, params):
        """Simple meeting scheduling"""
        # Load or create calendar
        calendar = {"events": []}
        if os.path.exists(self.calendar_file):
            try:
                with open(self.calendar_file, 'r') as f:
                    calendar = json.load(f)
            except:
                calendar = {"events": []}
        
        # Add new event
        event = {
            "title": params.get('title', 'Meeting'),
            "time": params.get('time', '12:00'),
            "date": params.get('date', datetime.now().strftime('%Y-%m-%d')),
            "created": datetime.now().isoformat()
        }
        calendar["events"].append(event)
        
        # Save
        with open(self.calendar_file, 'w') as f:
            json.dump(calendar, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Scheduled: {event['title']} at {event['time']} on {event['date']}"
        }
    
    def set_reminder(self, params):
        """Simple reminder"""
        return {
            "status": "success",
            "message": f"Reminder set: {params.get('text', '')}"
        }
    
    def create_task(self, params):
        """Simple task creation"""
        return {
            "status": "success",
            "message": f"Task created: {params.get('text', '')}"
        }
    
    def parse_input(self, text):
        """Simple parsing"""
        text = text.lower().strip()
        
        # Check for dangerous commands
        if "delete everything" in text or "clear all" in text:
            return "delete_all", {}
        
        # Schedule meeting
        if "schedule" in text or "meeting" in text:
            params = {"title": "Meeting"}
            
            if "tomorrow" in text:
                tomorrow = datetime.now() + timedelta(days=1)
                params['date'] = tomorrow.strftime('%Y-%m-%d')
            
            # Extract time
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = time_match.group(2) if time_match.group(2) else "00"
                meridiem = time_match.group(3)
                
                if meridiem == 'pm' and hour < 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0
                    
                params['time'] = f"{hour}:{minute}"
            
            return "schedule", params
        
        # Reminder
        elif "remind" in text:
            msg = text.replace("remind", "").replace("me", "").replace("to", "").strip()
            return "remind", {"text": msg}
        
        # Task
        elif "task" in text or "todo" in text:
            task = text.replace("task", "").replace("todo", "").replace("add", "").strip()
            return "task", {"text": task}
        
        return "unknown", {}
    
    def run(self):
        """Main loop"""
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌟 Taara - Simple Agent{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print("\nCommands:")
        print("  • Schedule a meeting tomorrow at 2pm")
        print("  • Remind me to call John")
        print("  • Add task: Buy groceries")
        print("  • Delete everything (will be blocked)")
        print("  • quit\n")
        
        while True:
            try:
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                    break
                
                if not user_input:
                    continue
                
                print(f"{Fore.BLUE}📝 Parsing...{Style.RESET_ALL}")
                action, params = self.parse_input(user_input)
                print(f"   Action: {action}")
                
                print(f"{Fore.BLUE}🔒 Checking policies...{Style.RESET_ALL}")
                allowed, reason = self.check_policies(action, params)
                
                if not allowed:
                    print(f"{Fore.RED}❌ BLOCKED: {reason}{Style.RESET_ALL}")
                    print(f"{Fore.RED}⛔ No changes made{Style.RESET_ALL}")
                    continue
                
                print(f"{Fore.GREEN}✓ Policy check passed{Style.RESET_ALL}")
                
                print(f"{Fore.BLUE}⚡ Executing...{Style.RESET_ALL}")
                result = self.execute_action(action, params)
                
                if result['status'] == 'success':
                    print(f"{Fore.GREEN}✅ {result['message']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ {result['message']}{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    agent = SimpleTaara()
    agent.run()
