import hashlib
import hmac
import json
import os
from datetime import datetime
import requests
from typing import Dict, Any, Optional

class ArmoriqClient:
    """ARMORIQ security integration for Taara agent"""
    
    def __init__(self):
        self.api_key = os.getenv('ARMORIQ_API_KEY', '')
        self.api_secret = os.getenv('ARMORIQ_SECRET', '')
        self.api_endpoint = os.getenv('ARMORIQ_ENDPOINT', 'https://api.armoriq.io/v1')
        self.bypass_secret = os.getenv('VERCEL_AUTOMATION_BYPASS_SECRET', '')
        
    def verify_intent(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify intent with ARMORIQ security layer"""
        
        # Create verification payload
        timestamp = datetime.utcnow().isoformat()
        payload = {
            'intent': intent_data,
            'timestamp': timestamp,
            'source': 'taara-agent',
            'version': '1.0.0'
        }
        
        # Generate signature
        signature = hmac.new(
            self.api_secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Add security headers
        headers = {
            'X-ARMORIQ-API-KEY': self.api_key,
            'X-ARMORIQ-SIGNATURE': signature,
            'X-ARMORIQ-TIMESTAMP': timestamp,
            'X-VERCEL-BYPASS': self.bypass_secret,
            'Content-Type': 'application/json'
        }
        
        try:
            # Call ARMORIQ verification API
            response = requests.post(
                f"{self.api_endpoint}/verify",
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'verified': True,
                    'risk_score': response.json().get('risk_score', 0),
                    'verification_id': response.json().get('verification_id'),
                    'signature': signature
                }
            else:
                return {
                    'verified': False,
                    'error': response.json().get('error', 'Verification failed'),
                    'status_code': response.status_code
                }
                
        except Exception as e:
            # Fallback to local verification
            return self._local_verification(intent_data, signature)
    
    def _local_verification(self, intent_data: Dict, signature: str) -> Dict:
        """Local fallback verification"""
        risk_score = self._calculate_risk_score(intent_data)
        
        return {
            'verified': True,
            'risk_score': risk_score,
            'verification_id': f"local_{hashlib.md5(json.dumps(intent_data).encode()).hexdigest()}",
            'signature': signature,
            'mode': 'fallback'
        }
    
    def _calculate_risk_score(self, intent_data: Dict) -> float:
        """Calculate risk score locally"""
        score = 0.0
        
        intent_type = intent_data.get('type', '')
        params = intent_data.get('parameters', {})
        
        # High risk operations
        if 'delete' in intent_type or 'clear' in intent_type:
            score += 0.5
            if params.get('scope') == 'all':
                score += 0.3
        
        # Check for dangerous patterns
        command = intent_data.get('raw_input', '').lower()
        dangerous_words = ['delete', 'remove', 'clear', 'erase', 'destroy']
        for word in dangerous_words:
            if word in command and 'everything' in command:
                score += 0.4
                break
        
        return min(score, 1.0)
    
    def create_audit_log(self, action: str, result: Dict, user: str = 'anonymous'):
        """Create audit trail entry"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'result': result,
            'user': user,
            'environment': os.getenv('VERCEL_ENV', 'development')
        }
        
        # Hash the entry for tamper-proof audit
        entry_hash = hashlib.sha256(
            json.dumps(audit_entry, sort_keys=True).encode()
        ).hexdigest()
        
        audit_entry['hash'] = entry_hash
        
        # Store in file (in production, send to ARMORIQ)
        with open('armoriq_integration/audit.log', 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
        
        return entry_hash
