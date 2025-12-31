#!/usr/bin/env python3
"""
TikTok Batch Uploader with Sound Support
Handles batch uploads with accounts, proxies, and sounds
"""

import sys
import json
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tiktokautouploader import upload_tiktok
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "tiktokautouploader not installed"
    }))
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class UploadTask:
    """Single upload task configuration"""
    video_path: str
    account_cookies: str  # Cookie string or session file
    account_name: str
    proxy: Optional[str] = None
    description: str = ""
    hashtags: List[str] = None
    sound_name: Optional[str] = None
    sound_aud_vol: str = "mix"


def parse_accounts_file(file_path: str) -> List[str]:
    """Parse accounts file (one cookie/session per line)"""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def parse_proxies_file(file_path: str) -> List[str]:
    """Parse proxies file (one proxy per line: ip:port:user:pass or ip:port)"""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def get_videos_from_folder(folder_path: str) -> List[str]:
    """Get all video files from folder"""
    video_extensions = ['.mp4', '.mov', '.avi', '.webm']
    videos = []
    
    folder = Path(folder_path)
    for ext in video_extensions:
        videos.extend(folder.glob(f"*{ext}"))
    
    return sorted([str(v) for v in videos])


def upload_single_video(task: UploadTask, task_id: int, total: int) -> Dict:
    """
    Upload a single video with the given configuration
    """
    logger.info(f"[{task_id}/{total}] Starting upload: {Path(task.video_path).name}")
    logger.info(f"  Account: {task.account_name}")
    logger.info(f"  Proxy: {task.proxy or 'None'}")
    logger.info(f"  Sound: {task.sound_name or 'Original'}")
    
    try:
        # Build upload kwargs
        upload_kwargs = {
            "video": task.video_path,
            "description": task.description,
            "accountname": task.account_name,
            "headless": True,  # Always headless for batch
        }
        
        if task.hashtags:
            upload_kwargs["hashtags"] = [f"#{h.lstrip('#')}" for h in task.hashtags]
        
        if task.sound_name:
            upload_kwargs["sound_name"] = task.sound_name
            upload_kwargs["sound_aud_vol"] = task.sound_aud_vol
        
        if task.proxy:
            upload_kwargs["proxy"] = task.proxy
        
        # Perform upload
        start_time = time.time()
        result = upload_tiktok(**upload_kwargs)
        elapsed = time.time() - start_time
        
        logger.info(f"[{task_id}/{total}] ✅ Upload completed in {elapsed:.1f}s")
        
        return {
            "success": True,
            "task_id": task_id,
            "video": task.video_path,
            "account": task.account_name,
            "elapsed_seconds": elapsed
        }
        
    except Exception as e:
        logger.error(f"[{task_id}/{total}] ❌ Upload failed: {str(e)}")
        return {
            "success": False,
            "task_id": task_id,
            "video": task.video_path,
            "account": task.account_name,
            "error": str(e)
        }


def batch_upload(
    videos_folder: str,
    accounts_file: str,
    proxies_file: str,
    description: str = "",
    hashtags: List[str] = None,
    sound_name: Optional[str] = None,
    sound_aud_vol: str = "mix",
    max_workers: int = 1,  # Sequential by default (safer)
    delay_between: int = 30  # Delay between uploads in seconds
) -> Dict:
    """
    Batch upload videos to TikTok
    
    Distribution strategy: Round-robin videos across accounts
    Each account gets paired with corresponding proxy
    """
    
    # Load data
    videos = get_videos_from_folder(videos_folder)
    accounts = parse_accounts_file(accounts_file)
    proxies = parse_proxies_file(proxies_file)
    
    if not videos:
        return {"success": False, "error": "No videos found in folder"}
    
    if not accounts:
        return {"success": False, "error": "No accounts found in file"}
    
    if len(accounts) != len(proxies):
        return {
            "success": False, 
            "error": f"Account count ({len(accounts)}) != Proxy count ({len(proxies)})"
        }
    
    logger.info(f"📹 Videos: {len(videos)}")
    logger.info(f"👤 Accounts: {len(accounts)}")
    logger.info(f"🌐 Proxies: {len(proxies)}")
    logger.info(f"🎵 Sound: {sound_name or 'Original'}")
    
    # Create tasks - distribute videos across accounts
    tasks = []
    for i, video in enumerate(videos):
        account_idx = i % len(accounts)
        
        task = UploadTask(
            video_path=video,
            account_cookies=accounts[account_idx],
            account_name=f"account_{account_idx + 1}",
            proxy=proxies[account_idx],
            description=description,
            hashtags=hashtags or [],
            sound_name=sound_name,
            sound_aud_vol=sound_aud_vol
        )
        tasks.append(task)
    
    logger.info(f"📋 Created {len(tasks)} upload tasks")
    
    # Execute uploads
    results = []
    successful = 0
    failed = 0
    
    for i, task in enumerate(tasks, 1):
        result = upload_single_video(task, i, len(tasks))
        results.append(result)
        
        if result["success"]:
            successful += 1
        else:
            failed += 1
        
        # Delay between uploads (except for last one)
        if i < len(tasks) and delay_between > 0:
            logger.info(f"⏳ Waiting {delay_between}s before next upload...")
            time.sleep(delay_between)
    
    return {
        "success": True,
        "summary": {
            "total": len(tasks),
            "successful": successful,
            "failed": failed,
            "videos_folder": videos_folder
        },
        "results": results
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TikTok Batch Uploader with Sound")
    
    parser.add_argument("--videos-folder", required=True, help="Folder with videos")
    parser.add_argument("--accounts-file", required=True, help="File with accounts (cookies)")
    parser.add_argument("--proxies-file", required=True, help="File with proxies")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--hashtags", default="", help="Comma-separated hashtags")
    parser.add_argument("--sound", default=None, help="TikTok sound name")
    parser.add_argument("--sound-vol", default="mix", choices=["main", "background", "mix"])
    parser.add_argument("--delay", type=int, default=30, help="Delay between uploads (seconds)")
    parser.add_argument("--json-config", default=None, help="JSON config file")
    
    args = parser.parse_args()
    
    if args.json_config:
        with open(args.json_config, 'r') as f:
            config = json.load(f)
        result = batch_upload(**config)
    else:
        hashtags = [h.strip() for h in args.hashtags.split(",") if h.strip()] if args.hashtags else None
        
        result = batch_upload(
            videos_folder=args.videos_folder,
            accounts_file=args.accounts_file,
            proxies_file=args.proxies_file,
            description=args.description,
            hashtags=hashtags,
            sound_name=args.sound,
            sound_aud_vol=args.sound_vol,
            delay_between=args.delay
        )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
