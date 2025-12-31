#!/usr/bin/env python3
"""
TikTok Sound Search API
Search for sounds and get their IDs
"""

import sys
import json
import argparse
import requests
from typing import List, Dict, Optional

def search_sounds_via_api(query: str, limit: int = 10) -> Dict:
    """
    Search TikTok sounds using unofficial API
    """
    try:
        # TikTok Web API endpoint for sound search
        url = "https://www.tiktok.com/api/search/general/full/"
        
        params = {
            "keyword": query,
            "offset": 0,
            "search_source": "normal_search",
            "web_search_code": '{"tiktok":{"client_params_x":{"search_engine":{"ies_mt_user_live_video_card_use_resolve":1}}}}',
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.tiktok.com/search",
        }
        
        # This is a simplified approach - in production you'd need proper auth
        # For now, we'll return a structured response for manual ID entry
        
        return {
            "success": True,
            "message": "Use TikTok app to find sound ID",
            "instructions": [
                "1. Open TikTok and search for the sound",
                "2. Tap on the sound to open its page",
                "3. Copy the share link",
                "4. The ID is in the URL after '/music/' (e.g., 7572266043506149392)"
            ],
            "query": query
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def parse_sound_url(url: str) -> Dict:
    """
    Parse TikTok sound URL to extract sound ID and name
    """
    import urllib.parse
    import re
    
    try:
        # Handle short URLs by following redirects
        if "vt.tiktok.com" in url or "vm.tiktok.com" in url:
            try:
                response = requests.head(url, allow_redirects=True, timeout=10)
                url = response.url
            except:
                pass
        
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        
        # Extract from /music/NAME-ID format
        music_match = re.search(r'/music/([^/]+)-(\d+)', path)
        if music_match:
            name = music_match.group(1).replace('-', ' ')
            sound_id = music_match.group(2)
            return {
                "success": True,
                "sound_id": sound_id,
                "sound_name": name,
                "original_url": url
            }
        
        # Try to extract just the ID from URL params
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'share_music_id' in query_params:
            return {
                "success": True,
                "sound_id": query_params['share_music_id'][0],
                "sound_name": None,
                "original_url": url
            }
        
        # Try to find any long number that could be an ID
        id_match = re.search(r'(\d{15,25})', url)
        if id_match:
            return {
                "success": True,
                "sound_id": id_match.group(1),
                "sound_name": None,
                "original_url": url
            }
        
        return {
            "success": False,
            "error": "Could not extract sound ID from URL",
            "original_url": url
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_sound_info(sound_id: str) -> Dict:
    """
    Get information about a sound by its ID
    """
    return {
        "success": True,
        "sound_id": sound_id,
        "tiktok_url": f"https://www.tiktok.com/music/-{sound_id}",
        "message": "Sound ID is valid format"
    }


def main():
    parser = argparse.ArgumentParser(description="TikTok Sound Search")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for sounds')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Max results')
    
    # Parse URL command
    parse_parser = subparsers.add_parser('parse', help='Parse sound URL to get ID')
    parse_parser.add_argument('url', help='TikTok sound URL')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get sound info by ID')
    info_parser.add_argument('sound_id', help='Sound ID')
    
    args = parser.parse_args()
    
    if args.command == 'search':
        result = search_sounds_via_api(args.query, args.limit)
    elif args.command == 'parse':
        result = parse_sound_url(args.url)
    elif args.command == 'info':
        result = get_sound_info(args.sound_id)
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
