#!/usr/bin/env python3
"""
Video Uniquifier - Main Entry Point
Запуск уникализатора видео

Usage:
    python run_uniquifier.py web        # Запустить веб-интерфейс
    python run_uniquifier.py cli        # CLI режим
    python run_uniquifier.py test       # Тест системы
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'web':
        # Запуск веб-интерфейса
        from src.tools.uniquifier_web import run_server
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        run_server(port=port)
        
    elif command == 'cli':
        # CLI режим
        from src.tools.video_uniquifier import main as cli_main
        sys.argv = sys.argv[1:]  # Remove 'cli' from args
        cli_main()
        
    elif command == 'test':
        # Тест системы
        test_system()
        
    else:
        print_help()


def test_system():
    """Тестирование системы"""
    print("\n" + "="*60)
    print("🧪 VIDEO UNIQUIFIER - SYSTEM TEST")
    print("="*60)
    
    # Test FFmpeg
    print("\n1. Checking FFmpeg...")
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"   ✅ FFmpeg found: {version}")
        else:
            print("   ❌ FFmpeg error")
            return False
    except FileNotFoundError:
        print("   ❌ FFmpeg not installed!")
        print("   Install with: apt install ffmpeg")
        return False
    
    # Test ffprobe
    print("\n2. Checking ffprobe...")
    try:
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ ffprobe found")
        else:
            print("   ❌ ffprobe error")
    except FileNotFoundError:
        print("   ❌ ffprobe not installed!")
        return False
    
    # Test imports
    print("\n3. Testing imports...")
    try:
        from src.tools.video_uniquifier import VideoUniquifier, UniquifySettings
        print("   ✅ VideoUniquifier imported")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    try:
        from src.tools.uniquifier_web import app
        print("   ✅ Web interface imported")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    # Test VideoUniquifier initialization
    print("\n4. Testing VideoUniquifier...")
    try:
        uniquifier = VideoUniquifier()
        print("   ✅ VideoUniquifier initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Check directories
    print("\n5. Checking directories...")
    base_dir = Path(__file__).parent
    
    dirs_to_check = [
        base_dir / "data" / "uploads",
        base_dir / "data" / "uniquified",
        base_dir / "data" / "videos"
    ]
    
    for dir_path in dirs_to_check:
        dir_path.mkdir(parents=True, exist_ok=True)
        if dir_path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path}")
    
    # Check for sample videos
    print("\n6. Checking for sample videos...")
    videos_dir = base_dir / "data" / "videos"
    videos = list(videos_dir.glob("*.mp4"))
    if videos:
        print(f"   ✅ Found {len(videos)} video(s):")
        for v in videos[:5]:
            size_mb = v.stat().st_size / 1024 / 1024
            print(f"      - {v.name} ({size_mb:.2f} MB)")
    else:
        print("   ⚠️ No sample videos found")
        print("   Upload videos to: data/videos/")
    
    print("\n" + "="*60)
    print("✅ All tests passed! System is ready.")
    print("="*60)
    print("\nTo start web interface:")
    print("   python run_uniquifier.py web")
    print("\nTo use CLI:")
    print("   python run_uniquifier.py cli single input.mp4 -o output.mp4")
    print("   python run_uniquifier.py cli batch input.mp4 -d ./output -c 10")
    print("="*60 + "\n")
    
    return True


def print_help():
    print("""
🎬 VIDEO UNIQUIFIER v2.0
========================

Уникализатор видео для Instagram Reels.
Создаёт уникальные версии видео с разными хэшами.

Usage:
  python run_uniquifier.py web [port]   - Запустить веб-интерфейс (по умолчанию порт 8080)
  python run_uniquifier.py cli <args>   - CLI режим
  python run_uniquifier.py test         - Тест системы

CLI Examples:
  python run_uniquifier.py cli single input.mp4 -o output.mp4
  python run_uniquifier.py cli batch input.mp4 -d ./output -c 10
  python run_uniquifier.py cli compare video1.mp4 video2.mp4
  python run_uniquifier.py cli info input.mp4

Presets:
  minimal    - Минимальные изменения (почти незаметны)
  balanced   - Сбалансированные (рекомендуется)
  aggressive - Агрессивные (максимальная уникальность)

Modifications:
  ✅ Crop (обрезка краёв)
  ✅ Brightness/Contrast/Saturation
  ✅ Hue shift (сдвиг цветового тона)
  ✅ Gamma correction
  ✅ Speed change
  ✅ Audio pitch shift
  ✅ Noise injection
  ✅ Micro-rotation
  ✅ Frame trimming
  ✅ Color channel shift
  ✅ Invisible watermark
  ✅ Metadata stripping
""")


if __name__ == "__main__":
    main()
