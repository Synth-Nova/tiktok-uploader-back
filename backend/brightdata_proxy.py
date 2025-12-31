"""
Bright Data Proxy Integration
Автоматическое получение прокси для TikTok заливки
"""

import os
import requests
from flask import Blueprint, request, jsonify

brightdata_bp = Blueprint('brightdata', __name__)

# Configuration - в продакшене использовать переменные окружения!
BRIGHTDATA_API_TOKEN = os.environ.get('BRIGHTDATA_API_TOKEN', '')
BRIGHTDATA_ZONE = os.environ.get('BRIGHTDATA_ZONE', 'web_unlocker1')

# Bright Data API endpoints
API_BASE = 'https://api.brightdata.com'


def get_headers():
    """Get authorization headers"""
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {BRIGHTDATA_API_TOKEN}'
    }


@brightdata_bp.route('/proxy/status', methods=['GET'])
def get_status():
    """Check Bright Data connection and balance"""
    if not BRIGHTDATA_API_TOKEN:
        return jsonify({
            'success': False,
            'error': 'API Token not configured',
            'configured': False
        })
    
    try:
        # Get account info
        response = requests.get(
            f'{API_BASE}/zone/get_settings?zone={BRIGHTDATA_ZONE}',
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'configured': True,
                'zone': BRIGHTDATA_ZONE,
                'zone_info': data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API error: {response.status_code}',
                'configured': True
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'configured': bool(BRIGHTDATA_API_TOKEN)
        })


@brightdata_bp.route('/proxy/balance', methods=['GET'])
def get_balance():
    """Get account balance"""
    if not BRIGHTDATA_API_TOKEN:
        return jsonify({'success': False, 'error': 'API Token not configured'})
    
    try:
        response = requests.get(
            f'{API_BASE}/customer/balance',
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'balance': data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API error: {response.status_code}'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@brightdata_bp.route('/proxy/generate', methods=['POST'])
def generate_proxies():
    """
    Generate proxy list for TikTok upload
    
    Request body:
    {
        "count": 10,           // Number of proxies needed
        "country": "us",       // Country code (optional)
        "session_type": "rotating"  // rotating or sticky
    }
    """
    if not BRIGHTDATA_API_TOKEN:
        return jsonify({'success': False, 'error': 'API Token not configured'})
    
    data = request.get_json() or {}
    count = min(100, max(1, data.get('count', 10)))
    country = data.get('country', '')
    session_type = data.get('session_type', 'rotating')
    
    # Bright Data proxy format
    # For Web Unlocker API, we use the API endpoint directly
    # But for traditional proxy format, we generate session IDs
    
    proxies = []
    
    # Generate proxy strings
    # Format: host:port:username:password
    # For Bright Data residential: brd.superproxy.io:22225:user:pass
    
    base_host = 'brd.superproxy.io'
    base_port = '22225'
    
    # Customer ID from zone (you'll need to get this from settings)
    # For now, we'll use the API method instead
    
    for i in range(count):
        session_id = f'session_{i}_{os.urandom(4).hex()}'
        
        # Build username with options
        username_parts = [f'brd-customer-hl_xxxxxxxx-zone-{BRIGHTDATA_ZONE}']
        
        if country:
            username_parts.append(f'country-{country.lower()}')
        
        if session_type == 'sticky':
            username_parts.append(f'session-{session_id}')
        
        username = '-'.join(username_parts)
        
        # Password is the API token or zone password
        password = 'YOUR_ZONE_PASSWORD'  # This needs to be set
        
        proxy_string = f'{base_host}:{base_port}:{username}:{password}'
        proxies.append(proxy_string)
    
    # Return as downloadable format
    proxy_text = '\n'.join(proxies)
    
    return jsonify({
        'success': True,
        'count': count,
        'country': country or 'any',
        'session_type': session_type,
        'proxies': proxies,
        'proxy_text': proxy_text,
        'format': 'host:port:username:password',
        'note': 'Configure zone password in settings'
    })


@brightdata_bp.route('/proxy/test', methods=['POST'])
def test_proxy():
    """Test a single proxy request through Bright Data"""
    if not BRIGHTDATA_API_TOKEN:
        return jsonify({'success': False, 'error': 'API Token not configured'})
    
    data = request.get_json() or {}
    test_url = data.get('url', 'https://geo.brdtest.com/welcome.txt')
    
    try:
        response = requests.post(
            f'{API_BASE}/request',
            headers=get_headers(),
            json={
                'zone': BRIGHTDATA_ZONE,
                'url': test_url,
                'format': 'raw'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'response': response.text[:500],
                'status_code': response.status_code
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Request failed: {response.status_code}',
                'response': response.text[:500]
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@brightdata_bp.route('/proxy/config', methods=['GET'])
def get_config():
    """Get current proxy configuration"""
    return jsonify({
        'success': True,
        'configured': bool(BRIGHTDATA_API_TOKEN),
        'zone': BRIGHTDATA_ZONE,
        'api_base': API_BASE,
        'proxy_host': 'brd.superproxy.io',
        'proxy_port': 22225,
        'instructions': {
            'step1': 'Set BRIGHTDATA_API_TOKEN environment variable',
            'step2': 'Set BRIGHTDATA_ZONE if different from default',
            'step3': 'Use /proxy/generate to create proxy list',
            'step4': 'Use /proxy/test to verify connection'
        }
    })


@brightdata_bp.route('/proxy/save-config', methods=['POST'])
def save_config():
    """Save Bright Data configuration"""
    global BRIGHTDATA_API_TOKEN, BRIGHTDATA_ZONE
    
    data = request.get_json() or {}
    
    if 'api_token' in data:
        BRIGHTDATA_API_TOKEN = data['api_token']
        os.environ['BRIGHTDATA_API_TOKEN'] = data['api_token']
    
    if 'zone' in data:
        BRIGHTDATA_ZONE = data['zone']
        os.environ['BRIGHTDATA_ZONE'] = data['zone']
    
    return jsonify({
        'success': True,
        'message': 'Configuration saved',
        'zone': BRIGHTDATA_ZONE,
        'token_set': bool(BRIGHTDATA_API_TOKEN)
    })
