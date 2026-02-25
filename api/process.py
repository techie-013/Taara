import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from simple_agent import SimpleTaara
    agent = SimpleTaara()
except Exception as e:
    agent = None
    print(f"Agent import error: {e}")

def handler(event, context):
    """Vercel Python serverless function with ARMORIQ"""
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-ARMORIQ-SIGNATURE, X-VERCEL-BYPASS'
    }
    
    # Handle OPTIONS request (CORS preflight)
    if event['requestContext']['http']['method'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Handle GET request
    if event['requestContext']['http']['method'] == 'GET':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'ok',
                'message': 'Taara API with ARMORIQ is running',
                'armoriq': 'connected',
                'endpoints': {
                    'POST /api/process': 'Send commands with ARMORIQ verification'
                }
            })
        }
    
    # Handle POST request
    if event['requestContext']['http']['method'] == 'POST':
        try:
            # Parse body
            body = json.loads(event.get('body', '{}'))
            command = body.get('text', '')
            
            response = {
                'command': command,
                'allowed': False,
                'armoriq_verified': False
            }
            
            # Process with agent if available
            if agent:
                # Parse with ARMORIQ verification
                action, params, verification = agent.parse_input(command)
                
                # Add ARMORIQ info to response
                if verification:
                    response['armoriq_verified'] = verification.get('verified', False)
                    response['risk_score'] = verification.get('risk_score', 0)
                    response['verification_id'] = verification.get('verification_id', '')
                
                # Check policies
                allowed, reason = agent.check_policies(action, params)
                response['allowed'] = allowed
                response['action'] = action
                
                if allowed:
                    result = agent.execute_action(action, params)
                    response['message'] = result.get('message', 'Command executed')
                    response['result'] = result
                else:
                    response['message'] = f"Blocked: {reason}"
                    response['reason'] = reason
            else:
                response['message'] = 'Agent not available'
                response['error'] = 'Agent initialization failed'
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'error': str(e),
                    'allowed': False,
                    'message': f'Server error: {str(e)}'
                })
            }
    
    # Handle other methods
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps({'error': 'Method not allowed'})
    }
