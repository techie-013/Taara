#!/usr/bin/env python3
"""
Taara - AI Agent with ARMORIQ Security Integration
"""

import os
import yaml
import json
from datetime import datetime, timedelta
import re
from colorama import init, Fore, Style

# Import ARMORIQ client
try:
    from armoriq_integration.armoriq_client import ArmoriqClient
    armoriq_available = True
except ImportError:
    armoriq_available = False
    print(f"{Fore.YELLOW}⚠ ARMORIQ integration not available{Style.RESET_ALL}")

init()

class SimpleTaara:
    def __init__(self):
        self.name = "Taara"
        self.load_policies()
        self.calendar_file = os.path.join(os.path.expanduser("~"), "taara_calendar.json")
        
        # Initialize ARMORIQ if available
        self.armoriq = None
        if armoriq_available:
            try:
                self.armoriq = ArmoriqClient()
                print(f"{Fore.GREEN}✓ ARMORIQ security initialized{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠ ARMORIQ init failed: {e}{Style.RESET_ALL}")
    
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
        """Execute the action with ARMORIQ audit"""
        result = None
        
        if action == "schedule":
            result = self.schedule_meeting(params)
        elif action == "remind":
            result = self.set_reminder(params)
        elif action == "task":
            result = self.create_task(params)
        else:
            result = {"status": "error", "message": f"Unknown action: {action}"}
        
        # Log to ARMORIQ if available
        if self.armoriq and result.get('status') == 'success':
            self.armoriq.create_audit_log(
                action=action,
                result=result,
                user=params.get('user_id', 'anonymous')
            )
        
        return result
    
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
            "id": len(calendar["events"]) + 1,
            "title": params.get('title', 'Meeting'),
            "time": params.get('time', '12:00'),
            "date": params.get('date', datetime.now().strftime('%Y-%m-%d')),
            "created": datetime.now().isoformat(),
            "verified": params.get('verified', False)
        }
        calendar["events"].append(event)
        
        # Save
        with open(self.calendar_file, 'w') as f:
            json.dump(calendar, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Scheduled: {event['title']} at {event['time']} on {event['date']}",
            "event": event
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
    
    def parse_input(self, text, verify_with_armoriq=True):
        """Parse input with optional ARMORIQ verification"""
        text = text.lower().strip()
        
        # Create intent data for ARMORIQ
        intent_data = {
            'raw_input': text,
            'type': self._classify_intent(text),
            'parameters': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check for dangerous commands first
        if "delete everything" in text or "clear all" in text:
            intent_data['type'] = 'dangerous'
            action = "delete_all"
            params = {"scope": "all"}
            
            # Verify with ARMORIQ
            if self.armoriq and verify_with_armoriq:
                verification = self.armoriq.verify_intent(intent_data)
                if verification.get('risk_score', 0) > 0.7:
                    return action, params, verification
            return action, params, None
        
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
            
            intent_data['type'] = 'schedule'
            intent_data['parameters'] = params
            
            action = "schedule"
        
        # Reminder
        elif "remind" in text:
            msg = text.replace("remind", "").replace("me", "").replace("to", "").strip()
            params = {"text": msg}
            intent_data['type'] = 'remind'
            intent_data['parameters'] = params
            action = "remind"
        
        # Task
        elif "task" in text or "todo" in text:
            task = text.replace("task", "").replace("todo", "").replace("add", "").strip()
            params = {"text": task}
            intent_data['type'] = 'task'
            intent_data['parameters'] = params
            action = "task"
        
        else:
            intent_data['type'] = 'unknown'
            action = "unknown"
            params = {}
        
        # Verify with ARMORIQ
        verification = None
        if self.armoriq and verify_with_armoriq and action != "unknown":
            verification = self.armoriq.verify_intent(intent_data)
            if verification and verification.get('verified'):
                params['verified'] = True
                params['verification_id'] = verification.get('verification_id')
        
        return action, params, verification
    
    def _classify_intent(self, text):
        """Classify intent type"""
        if any(word in text for word in ['schedule', 'meeting', 'appointment']):
            return 'schedule'
        elif 'remind' in text:
            return 'remind'
        elif any(word in text for word in ['task', 'todo']):
            return 'task'
        elif any(word in text for word in ['delete', 'remove', 'clear']):
            return 'dangerous'
        else:
            return 'query'
    
    def run(self):
        """Main loop with ARMORIQ integration"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌟 Taara AI Agent with ARMORIQ Security{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⚡ ARMORIQ x OPENCLAW HACKATHON 2026{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        if self.armoriq:
            print(f"{Fore.GREEN}✓ ARMORIQ Security: ENABLED{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ ARMORIQ Security: DISABLED (using local fallback){Style.RESET_ALL}")
        
        print("\n📋 Try these commands:")
        print("  ✅ Schedule a meeting tomorrow at 2pm")
        print("  ✅ Remind me to call John at 5pm")
        print("  ✅ Add task: Buy groceries")
        print("  ❌ Delete everything from my calendar")
        print("  📅 What meetings do I have tomorrow?")
        print("\n  Type 'quit' to exit\n")
        
        while True:
            try:
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                    break
                
                if not user_input:
                    continue
                
                # Parse with ARMORIQ verification
                print(f"{Fore.BLUE}📝 Parsing with ARMORIQ...{Style.RESET_ALL}")
                action, params, verification = self.parse_input(user_input)
                
                # Show ARMORIQ verification result
                if verification:
                    print(f"   ARMORIQ Risk Score: {verification.get('risk_score', 0):.2f}")
                    if verification.get('mode') == 'fallback':
                        print(f"   Mode: Local Fallback")
                
                print(f"   Action: {action}")
                
                # Check policies
                print(f"{Fore.BLUE}🔒 Checking policies...{Style.RESET_ALL}")
                allowed, reason = self.check_policies(action, params)
                
                if not allowed:
                    print(f"{Fore.RED}❌ BLOCKED: {reason}{Style.RESET_ALL}")
                    print(f"{Fore.RED}⛔ No changes made{Style.RESET_ALL}")
                    
                    # Log blocked action
                    if self.armoriq:
                        self.armoriq.create_audit_log(
                            action=action,
                            result={'reason': reason, 'blocked': True},
                            user='anonymous'
                        )
                    continue
                
                print(f"{Fore.GREEN}✓ Policy check passed{Style.RESET_ALL}")
                
                # Execute
                print(f"{Fore.BLUE}⚡ Executing...{Style.RESET_ALL}")
                result = self.execute_action(action, params)
                
                if result['status'] == 'success':
                    print(f"{Fore.GREEN}✅ {result['message']}{Style.RESET_ALL}")
                    
                    # Show verification badge if available
                    if params.get('verified'):
                        print(f"   🔐 ARMORIQ Verified: {params.get('verification_id', '')[:8]}...")
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
