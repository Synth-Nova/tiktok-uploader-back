#!/usr/bin/env python3
"""
TikTok Uploader with Sound Support
Wrapper around tiktokautouploader library for Node.js integration
"""

import sys
import json
import argparse
from pathlib import Path

try:
    from tiktokautouploader import upload_tiktok
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "tiktokautouploader not installed. Run: pip install tiktokautouploader"
    }))
    sys.exit(1)


def upload_video_with_sound(
    video_path: str,
    account_name: str,
    description: str = "",
    hashtags: list = None,
    sound_name: str = None,
    sound_aud_vol: str = "mix",  # 'main', 'background', 'mix'
    schedule_time: str = None,  # Format: 'HH:MM'
    schedule_day: int = None,   # Day of month (1-31)
    copyright_check: bool = False,
    proxy: str = None,
    headless: bool = True
) -> dict:
    """
    Upload video to TikTok with optional sound
    
    Args:
        video_path: Path to video file
        account_name: TikTok account name (for session management)
        description: Video description/caption
        hashtags: List of hashtags (with or without #)
        sound_name: Name of TikTok sound to add (searches TikTok library)
        sound_aud_vol: Audio volume mode - 'main' (sound only), 'background' (video audio main), 'mix' (both)
        schedule_time: Time to post (HH:MM format)
        schedule_day: Day to post (1-31)
        copyright_check: Check for copyright before posting
        proxy: Proxy server (format: ip:port or ip:port:user:pass)
        headless: Run browser in headless mode
    
    Returns:
        dict with success status and details
    """
    
    # Validate video file
    if not Path(video_path).exists():
        return {
            "success": False,
            "error": f"Video file not found: {video_path}"
        }
    
    # Prepare hashtags
    if hashtags:
        # Ensure hashtags have # prefix
        hashtags = [f"#{tag.lstrip('#')}" for tag in hashtags]
    
    try:
        # Build upload arguments
        upload_kwargs = {
            "video": video_path,
            "description": description,
            "accountname": account_name,
        }
        
        if hashtags:
            upload_kwargs["hashtags"] = hashtags
        
        # Add sound if specified
        if sound_name:
            upload_kwargs["sound_name"] = sound_name
            upload_kwargs["sound_aud_vol"] = sound_aud_vol
        
        # Add scheduling if specified
        if schedule_time:
            upload_kwargs["schedule"] = schedule_time
            if schedule_day:
                upload_kwargs["day"] = schedule_day
        
        # Add copyright check
        if copyright_check:
            upload_kwargs["copyrightcheck"] = True
        
        # Add proxy if specified
        if proxy:
            upload_kwargs["proxy"] = proxy
        
        # Add headless mode
        upload_kwargs["headless"] = headless
        
        # Perform upload
        result = upload_tiktok(**upload_kwargs)
        
        return {
            "success": True,
            "message": "Video uploaded successfully",
            "data": {
                "video_path": video_path,
                "account": account_name,
                "sound": sound_name,
                "hashtags": hashtags,
                "scheduled": schedule_time is not None
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "video_path": video_path,
            "account": account_name
        }


def main():
    parser = argparse.ArgumentParser(description="TikTok Video Uploader with Sound Support")
    
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--account", required=True, help="TikTok account name")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--hashtags", default="", help="Comma-separated hashtags")
    parser.add_argument("--sound", default=None, help="TikTok sound name to add")
    parser.add_argument("--sound-vol", default="mix", choices=["main", "background", "mix"],
                        help="Sound volume mode")
    parser.add_argument("--schedule", default=None, help="Schedule time (HH:MM)")
    parser.add_argument("--schedule-day", type=int, default=None, help="Schedule day (1-31)")
    parser.add_argument("--copyright-check", action="store_true", help="Check copyright before upload")
    parser.add_argument("--proxy", default=None, help="Proxy server (ip:port or ip:port:user:pass)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Show browser")
    parser.add_argument("--json-input", default=None, help="JSON file with upload config")
    
    args = parser.parse_args()
    
    # If JSON input provided, use it
    if args.json_input:
        with open(args.json_input, 'r') as f:
            config = json.load(f)
        result = upload_video_with_sound(**config)
    else:
        # Parse hashtags
        hashtags = [h.strip() for h in args.hashtags.split(",") if h.strip()] if args.hashtags else None
        
        result = upload_video_with_sound(
            video_path=args.video,
            account_name=args.account,
            description=args.description,
            hashtags=hashtags,
            sound_name=args.sound,
            sound_aud_vol=args.sound_vol,
            schedule_time=args.schedule,
            schedule_day=args.schedule_day,
            copyright_check=args.copyright_check,
            proxy=args.proxy,
            headless=args.headless
        )
    
    # Output JSON result
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
