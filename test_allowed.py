from simple_agent import SimpleTaara

def test_allowed():
    print("\n🧪 Testing ALLOWED action...")
    agent = SimpleTaara()
    action, params = agent.parse_input("Schedule a meeting tomorrow at 2pm")
    allowed, reason = agent.check_policies(action, params)
    
    if allowed:
        result = agent.execute_action(action, params)
        print(f"✅ ALLOWED: {result['message']}")
    else:
        print(f"❌ BLOCKED: {reason}")
    
    return allowed

if __name__ == "__main__":
    test_allowed()
