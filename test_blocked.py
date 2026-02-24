from simple_agent import SimpleTaara

def test_blocked():
    print("\n🧪 Testing BLOCKED action...")
    agent = SimpleTaara()
    action, params = agent.parse_input("Delete everything from my calendar")
    allowed, reason = agent.check_policies(action, params)
    
    if allowed:
        print("❌ TEST FAILED: Dangerous action was allowed")
    else:
        print(f"✅ BLOCKED correctly: {reason}")
    
    return not allowed

if __name__ == "__main__":
    test_blocked()
