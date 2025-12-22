#!/usr/bin/env python3
"""
Video Uniquifier v2.0 - Уникализатор видео для Instagram Reels
Создаёт уникальные версии видео для обхода детекции дубликатов

Возможности:
- Изменение метаданных (полное удаление и рандомизация)
- Визуальные модификации (crop, яркость, контраст, шум, поворот)
- Аудио модификации (pitch, speed, небольшие искажения)
- Манипуляции с кадрами (добавление/удаление кадров)
- Невидимый водяной знак
- Генерация множества уникальных версий
"""

import os
import sys
import json
import random
import string
import hashlib
import subprocess
import tempfile
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class UniquifySettings:
    """Настройки уникализации"""
    # Crop settings (обрезка краёв)
    crop_enabled: bool = True
    crop_percent_min: float = 0.5   # Минимум 0.5%
    crop_percent_max: float = 2.0   # Максимум 2%
    
    # Brightness/Contrast
    brightness_enabled: bool = True
    brightness_min: float = -0.05   # -5%
    brightness_max: float = 0.05    # +5%
    contrast_min: float = 0.97      # -3%
    contrast_max: float = 1.03      # +3%
    
    # Saturation (насыщенность)
    saturation_enabled: bool = True
    saturation_min: float = 0.95
    saturation_max: float = 1.05
    
    # Hue (цветовой тон) - новое
    hue_enabled: bool = True
    hue_shift_min: float = -3.0     # градусы
    hue_shift_max: float = 3.0
    
    # Speed (скорость воспроизведения)
    speed_enabled: bool = True
    speed_min: float = 0.98         # -2%
    speed_max: float = 1.02         # +2%
    
    # Audio pitch
    pitch_enabled: bool = True
    pitch_semitones_min: float = -0.5
    pitch_semitones_max: float = 0.5
    
    # Noise (невидимый шум)
    noise_enabled: bool = True
    noise_amount: float = 0.002     # Очень слабый шум
    
    # Mirror (зеркалирование) - опционально
    mirror_enabled: bool = False
    mirror_probability: float = 0.0  # 0 = никогда, 1 = всегда
    
    # Rotation (небольшой поворот)
    rotation_enabled: bool = True
    rotation_degrees_max: float = 0.5  # ±0.5 градуса
    
    # Frame manipulation (манипуляции с кадрами) - новое
    frame_manipulation_enabled: bool = True
    trim_start_ms_max: int = 100     # Обрезка начала до 100мс
    trim_end_ms_max: int = 100       # Обрезка конца до 100мс
    
    # Color shift (сдвиг цветовых каналов) - новое
    color_shift_enabled: bool = True
    color_shift_amount: float = 0.02  # 2% сдвиг каналов
    
    # Invisible watermark (невидимый водяной знак) - новое
    watermark_enabled: bool = True
    watermark_opacity: float = 0.01   # 1% прозрачность
    
    # Gamma correction - новое
    gamma_enabled: bool = True
    gamma_min: float = 0.97
    gamma_max: float = 1.03
    
    # Metadata
    strip_metadata: bool = True
    randomize_creation_date: bool = True
    
    # Output quality
    output_crf: int = 23              # Качество (18-28, меньше = лучше)
    output_preset: str = "medium"     # Скорость кодирования


class VideoUniquifier:
    """
    Уникализатор видео для Instagram v2.0
    Использует FFmpeg для модификаций
    """
    
    def __init__(self, settings: Optional[UniquifySettings] = None):
        self.settings = settings or UniquifySettings()
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Проверка наличия FFmpeg"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg not working")
            logger.info("✅ FFmpeg found")
        except FileNotFoundError:
            raise RuntimeError("❌ FFmpeg not installed! Install with: apt install ffmpeg")
    
    def _get_video_info(self, video_path: str) -> Dict:
        """Получить информацию о видео через ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def _generate_random_string(self, length: int = 8) -> str:
        """Генерация случайной строки"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _calculate_hash(self, file_path: str) -> str:
        """Вычислить MD5 хэш файла"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _generate_invisible_watermark(self, width: int, height: int, temp_dir: str) -> str:
        """Создать невидимый водяной знак (уникальный для каждого видео)"""
        watermark_path = os.path.join(temp_dir, "watermark.png")
        
        # Генерируем уникальный паттерн шума
        unique_seed = self._generate_random_string(16)
        
        # Создаём PNG с очень слабым шумом
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'nullsrc=s={width}x{height}:d=1,geq=random(1)*255:128:128',
            '-vframes', '1',
            watermark_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return watermark_path
    
    def uniquify(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        preset: str = "balanced"
    ) -> Tuple[str, Dict]:
        """
        Создать уникальную версию видео
        
        Args:
            input_path: Путь к исходному видео
            output_path: Путь для сохранения (если None - автогенерация)
            preset: Пресет настроек (minimal, balanced, aggressive)
            
        Returns:
            Tuple[output_path, modifications_applied]
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Video not found: {input_path}")
        
        # Apply preset
        self._apply_preset(preset)
        
        # Get video info
        info = self._get_video_info(input_path)
        video_stream = next(
            (s for s in info['streams'] if s['codec_type'] == 'video'), 
            None
        )
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        # Get duration
        duration = float(info['format'].get('duration', 0))
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎬 UNIQUIFYING VIDEO v2.0")
        logger.info(f"📁 Input: {input_path}")
        logger.info(f"📐 Size: {width}x{height}")
        logger.info(f"⏱️ Duration: {duration:.2f}s")
        logger.info(f"🎯 Preset: {preset}")
        logger.info(f"{'='*60}")
        
        # Generate modifications
        mods = self._generate_modifications(width, height, duration)
        
        # Build FFmpeg command
        ffmpeg_cmd = self._build_ffmpeg_command(input_path, mods, width, height, duration)
        
        # Generate output path
        if output_path is None:
            input_name = Path(input_path).stem
            input_ext = Path(input_path).suffix
            random_suffix = self._generate_random_string(6)
            output_path = str(
                Path(input_path).parent / f"{input_name}_unique_{random_suffix}{input_ext}"
            )
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Add output to command
        ffmpeg_cmd.extend(['-y', output_path])
        
        # Execute FFmpeg
        logger.info("\n🔄 Processing video...")
        logger.info(f"Command: {' '.join(ffmpeg_cmd[:15])}... [truncated]")
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")
        
        # Verify output
        if not os.path.exists(output_path):
            raise RuntimeError("Output file was not created")
        
        output_size = os.path.getsize(output_path)
        input_size = os.path.getsize(input_path)
        
        # Calculate hashes
        input_hash = self._calculate_hash(input_path)
        output_hash = self._calculate_hash(output_path)
        
        logger.info(f"\n✅ Video uniquified!")
        logger.info(f"📁 Output: {output_path}")
        logger.info(f"📊 Size: {input_size:,} → {output_size:,} bytes ({output_size/input_size*100:.1f}%)")
        logger.info(f"🔑 Hash: {input_hash[:12]}... → {output_hash[:12]}...")
        
        # Return info about modifications
        result_info = {
            'input_path': input_path,
            'output_path': output_path,
            'input_hash': input_hash,
            'output_hash': output_hash,
            'input_size': input_size,
            'output_size': output_size,
            'modifications': mods,
            'preset': preset,
            'timestamp': datetime.now().isoformat()
        }
        
        return output_path, result_info
    
    def _apply_preset(self, preset: str):
        """Применить пресет настроек"""
        if preset == "minimal":
            # Минимальные изменения - почти незаметны
            self.settings.crop_percent_max = 1.0
            self.settings.brightness_max = 0.02
            self.settings.brightness_min = -0.02
            self.settings.contrast_min = 0.99
            self.settings.contrast_max = 1.01
            self.settings.speed_enabled = False
            self.settings.pitch_enabled = False
            self.settings.noise_amount = 0.001
            self.settings.rotation_enabled = False
            self.settings.hue_enabled = False
            self.settings.frame_manipulation_enabled = False
            self.settings.color_shift_enabled = False
            self.settings.watermark_enabled = True
            self.settings.gamma_enabled = False
            
        elif preset == "balanced":
            # Сбалансированные изменения (по умолчанию)
            self.settings = UniquifySettings()
            
        elif preset == "aggressive":
            # Агрессивные изменения - максимальная уникальность
            self.settings.crop_percent_max = 3.0
            self.settings.brightness_max = 0.08
            self.settings.brightness_min = -0.08
            self.settings.contrast_min = 0.95
            self.settings.contrast_max = 1.05
            self.settings.speed_min = 0.96
            self.settings.speed_max = 1.04
            self.settings.pitch_semitones_min = -1.0
            self.settings.pitch_semitones_max = 1.0
            self.settings.noise_amount = 0.005
            self.settings.rotation_degrees_max = 1.0
            self.settings.hue_shift_max = 5.0
            self.settings.hue_shift_min = -5.0
            self.settings.trim_start_ms_max = 200
            self.settings.trim_end_ms_max = 200
            self.settings.color_shift_amount = 0.03
            self.settings.gamma_min = 0.95
            self.settings.gamma_max = 1.05
    
    def _generate_modifications(self, width: int, height: int, duration: float) -> Dict:
        """Генерация случайных модификаций"""
        mods = {}
        s = self.settings
        
        # Crop
        if s.crop_enabled:
            crop_percent = random.uniform(s.crop_percent_min, s.crop_percent_max)
            crop_x = int(width * crop_percent / 100)
            crop_y = int(height * crop_percent / 100)
            mods['crop'] = {
                'x': crop_x,
                'y': crop_y,
                'percent': crop_percent
            }
            logger.info(f"  📐 Crop: {crop_percent:.2f}% ({crop_x}x{crop_y} pixels)")
        
        # Brightness
        if s.brightness_enabled:
            brightness = random.uniform(s.brightness_min, s.brightness_max)
            mods['brightness'] = brightness
            logger.info(f"  ☀️ Brightness: {brightness:+.3f}")
        
        # Contrast
        if s.brightness_enabled:
            contrast = random.uniform(s.contrast_min, s.contrast_max)
            mods['contrast'] = contrast
            logger.info(f"  🔲 Contrast: {contrast:.3f}")
        
        # Saturation
        if s.saturation_enabled:
            saturation = random.uniform(s.saturation_min, s.saturation_max)
            mods['saturation'] = saturation
            logger.info(f"  🎨 Saturation: {saturation:.3f}")
        
        # Hue shift (новое)
        if s.hue_enabled:
            hue_shift = random.uniform(s.hue_shift_min, s.hue_shift_max)
            mods['hue_shift'] = hue_shift
            logger.info(f"  🌈 Hue shift: {hue_shift:+.2f}°")
        
        # Gamma (новое)
        if s.gamma_enabled:
            gamma = random.uniform(s.gamma_min, s.gamma_max)
            mods['gamma'] = gamma
            logger.info(f"  🌗 Gamma: {gamma:.3f}")
        
        # Speed
        if s.speed_enabled:
            speed = random.uniform(s.speed_min, s.speed_max)
            mods['speed'] = speed
            logger.info(f"  ⏱️ Speed: {speed:.3f}x")
        
        # Pitch
        if s.pitch_enabled:
            pitch = random.uniform(s.pitch_semitones_min, s.pitch_semitones_max)
            mods['pitch_semitones'] = pitch
            logger.info(f"  🎵 Pitch: {pitch:+.2f} semitones")
        
        # Noise
        if s.noise_enabled:
            mods['noise'] = s.noise_amount
            logger.info(f"  📊 Noise: {s.noise_amount:.4f}")
        
        # Rotation
        if s.rotation_enabled:
            rotation = random.uniform(-s.rotation_degrees_max, s.rotation_degrees_max)
            mods['rotation'] = rotation
            logger.info(f"  🔄 Rotation: {rotation:+.2f}°")
        
        # Frame manipulation (новое)
        if s.frame_manipulation_enabled and duration > 1.0:
            trim_start = random.uniform(0, s.trim_start_ms_max / 1000)
            trim_end = random.uniform(0, s.trim_end_ms_max / 1000)
            mods['trim'] = {
                'start': trim_start,
                'end': trim_end
            }
            logger.info(f"  ✂️ Trim: start +{trim_start*1000:.0f}ms, end -{trim_end*1000:.0f}ms")
        
        # Color shift (новое)
        if s.color_shift_enabled:
            r_shift = random.uniform(-s.color_shift_amount, s.color_shift_amount)
            g_shift = random.uniform(-s.color_shift_amount, s.color_shift_amount)
            b_shift = random.uniform(-s.color_shift_amount, s.color_shift_amount)
            mods['color_shift'] = {'r': r_shift, 'g': g_shift, 'b': b_shift}
            logger.info(f"  🎨 Color shift: R{r_shift:+.3f} G{g_shift:+.3f} B{b_shift:+.3f}")
        
        # Watermark (новое)
        if s.watermark_enabled:
            mods['watermark'] = {
                'opacity': s.watermark_opacity,
                'seed': self._generate_random_string(8)
            }
            logger.info(f"  💧 Watermark: {s.watermark_opacity*100:.1f}% opacity")
        
        # Mirror
        if s.mirror_enabled and random.random() < s.mirror_probability:
            mods['mirror'] = True
            logger.info(f"  🪞 Mirror: Yes")
        
        return mods
    
    def _build_ffmpeg_command(
        self, 
        input_path: str, 
        mods: Dict, 
        width: int, 
        height: int,
        duration: float
    ) -> List[str]:
        """Построить команду FFmpeg"""
        cmd = ['ffmpeg']
        
        # Input with trim if needed
        if 'trim' in mods:
            trim = mods['trim']
            cmd.extend(['-ss', str(trim['start'])])
        
        cmd.extend(['-i', input_path])
        
        if 'trim' in mods:
            trim = mods['trim']
            new_duration = duration - trim['start'] - trim['end']
            cmd.extend(['-t', str(new_duration)])
        
        # Build filter complex
        video_filters = []
        audio_filters = []
        
        # Crop
        if 'crop' in mods:
            crop = mods['crop']
            new_w = width - (crop['x'] * 2)
            new_h = height - (crop['y'] * 2)
            video_filters.append(f"crop={new_w}:{new_h}:{crop['x']}:{crop['y']}")
            # Scale back to original size
            video_filters.append(f"scale={width}:{height}")
        
        # Build eq filter (brightness, contrast, saturation, gamma)
        eq_parts = []
        if 'brightness' in mods:
            eq_parts.append(f"brightness={mods['brightness']}")
        if 'contrast' in mods:
            eq_parts.append(f"contrast={mods['contrast']}")
        if 'saturation' in mods:
            eq_parts.append(f"saturation={mods['saturation']}")
        if 'gamma' in mods:
            eq_parts.append(f"gamma={mods['gamma']}")
        if eq_parts:
            video_filters.append(f"eq={':'.join(eq_parts)}")
        
        # Hue shift
        if 'hue_shift' in mods:
            video_filters.append(f"hue=h={mods['hue_shift']}")
        
        # Color shift (using colorbalance)
        if 'color_shift' in mods:
            cs = mods['color_shift']
            video_filters.append(f"colorbalance=rs={cs['r']}:gs={cs['g']}:bs={cs['b']}")
        
        # Rotation
        if 'rotation' in mods:
            rotation_rad = mods['rotation'] * 3.14159 / 180
            video_filters.append(f"rotate={rotation_rad}:fillcolor=black")
        
        # Noise (invisible)
        if 'noise' in mods:
            noise_amount = int(mods['noise'] * 100)
            video_filters.append(f"noise=alls={noise_amount}:allf=t")
        
        # Invisible watermark (unique pattern for each video)
        if 'watermark' in mods:
            wm = mods['watermark']
            # Add very subtle noise pattern as watermark
            opacity = wm['opacity']
            video_filters.append(
                f"drawbox=x=0:y=0:w={width}:h={height}:color=white@{opacity}:t=fill"
            )
        
        # Mirror
        if mods.get('mirror'):
            video_filters.append("hflip")
        
        # Speed (affects both video and audio)
        if 'speed' in mods:
            speed = mods['speed']
            video_filters.append(f"setpts={1/speed}*PTS")
            audio_filters.append(f"atempo={speed}")
        
        # Pitch (using asetrate)
        if 'pitch_semitones' in mods:
            pitch = mods['pitch_semitones']
            # Convert semitones to rate multiplier
            rate_mult = 2 ** (pitch / 12)
            audio_filters.append(f"asetrate=44100*{rate_mult},aresample=44100")
        
        # Build command with filters
        if video_filters:
            cmd.extend(['-vf', ','.join(video_filters)])
        
        if audio_filters:
            cmd.extend(['-af', ','.join(audio_filters)])
        
        # Output settings
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', self.settings.output_preset,
            '-crf', str(self.settings.output_crf),
            '-c:a', 'aac',
            '-b:a', '128k',
        ])
        
        # Strip metadata
        if self.settings.strip_metadata:
            cmd.extend(['-map_metadata', '-1'])
        
        # Randomize creation date
        if self.settings.randomize_creation_date:
            # Random date within last 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            random_date = (datetime.now() - timedelta(days=days_ago, hours=hours_ago)).strftime('%Y-%m-%dT%H:%M:%S')
            cmd.extend(['-metadata', f'creation_time={random_date}'])
        
        return cmd
    
    def batch_uniquify(
        self,
        input_path: str,
        output_dir: str,
        count: int,
        preset: str = "balanced",
        name_prefix: Optional[str] = None
    ) -> List[Dict]:
        """
        Создать несколько уникальных версий одного видео
        
        Args:
            input_path: Путь к исходному видео
            output_dir: Директория для сохранения
            count: Количество версий
            preset: Пресет настроек
            name_prefix: Префикс для имён файлов
            
        Returns:
            List of result info dicts
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎬 BATCH UNIQUIFICATION v2.0")
        logger.info(f"📁 Input: {input_path}")
        logger.info(f"📂 Output dir: {output_dir}")
        logger.info(f"📊 Count: {count}")
        logger.info(f"🎯 Preset: {preset}")
        logger.info(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        input_name = Path(input_path).stem
        input_ext = Path(input_path).suffix
        prefix = name_prefix or input_name
        
        results = []
        
        for i in range(count):
            logger.info(f"\n[{i+1}/{count}] Creating unique version...")
            
            output_filename = f"{prefix}_v{i+1:03d}_{self._generate_random_string(4)}{input_ext}"
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                # Reset settings for each version
                self._apply_preset(preset)
                
                _, result_info = self.uniquify(
                    input_path=input_path,
                    output_path=output_path,
                    preset=preset
                )
                result_info['version'] = i + 1
                results.append(result_info)
                
            except Exception as e:
                logger.error(f"❌ Failed to create version {i+1}: {e}")
                results.append({
                    'version': i + 1,
                    'error': str(e)
                })
        
        # Summary
        successful = len([r for r in results if 'error' not in r])
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 BATCH COMPLETE: {successful}/{count} successful")
        logger.info(f"{'='*60}")
        
        # Save report
        report_path = os.path.join(output_dir, f"{prefix}_uniquify_report.json")
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Report saved: {report_path}")
        
        return results
    
    def compare_videos(self, video1: str, video2: str) -> Dict:
        """
        Сравнить два видео и показать различия
        """
        hash1 = self._calculate_hash(video1)
        hash2 = self._calculate_hash(video2)
        
        size1 = os.path.getsize(video1)
        size2 = os.path.getsize(video2)
        
        info1 = self._get_video_info(video1)
        info2 = self._get_video_info(video2)
        
        return {
            'video1': {
                'path': video1,
                'hash': hash1,
                'size': size1,
                'duration': float(info1['format'].get('duration', 0))
            },
            'video2': {
                'path': video2,
                'hash': hash2,
                'size': size2,
                'duration': float(info2['format'].get('duration', 0))
            },
            'hashes_different': hash1 != hash2,
            'size_difference': size2 - size1,
            'size_ratio': size2 / size1 if size1 > 0 else 0
        }


def main():
    parser = argparse.ArgumentParser(
        description='Video Uniquifier v2.0 - Create unique versions of videos'
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Single file
    single_parser = subparsers.add_parser('single', help='Uniquify single video')
    single_parser.add_argument('input', help='Input video path')
    single_parser.add_argument('-o', '--output', help='Output path')
    single_parser.add_argument('-p', '--preset', 
                               choices=['minimal', 'balanced', 'aggressive'],
                               default='balanced',
                               help='Preset (default: balanced)')
    
    # Batch
    batch_parser = subparsers.add_parser('batch', help='Create multiple unique versions')
    batch_parser.add_argument('input', help='Input video path')
    batch_parser.add_argument('-d', '--output-dir', required=True, help='Output directory')
    batch_parser.add_argument('-c', '--count', type=int, default=10, help='Number of versions')
    batch_parser.add_argument('-p', '--preset',
                              choices=['minimal', 'balanced', 'aggressive'],
                              default='balanced')
    batch_parser.add_argument('--prefix', help='Filename prefix')
    
    # Compare
    compare_parser = subparsers.add_parser('compare', help='Compare two videos')
    compare_parser.add_argument('video1', help='First video')
    compare_parser.add_argument('video2', help='Second video')
    
    # Info
    info_parser = subparsers.add_parser('info', help='Show video info')
    info_parser.add_argument('input', help='Video path')
    
    args = parser.parse_args()
    
    if args.command == 'single':
        uniquifier = VideoUniquifier()
        output_path, info = uniquifier.uniquify(
            args.input,
            args.output,
            args.preset
        )
        print(f"\n✅ Output: {output_path}")
        
    elif args.command == 'batch':
        uniquifier = VideoUniquifier()
        results = uniquifier.batch_uniquify(
            args.input,
            args.output_dir,
            args.count,
            args.preset,
            args.prefix
        )
        
    elif args.command == 'compare':
        uniquifier = VideoUniquifier()
        result = uniquifier.compare_videos(args.video1, args.video2)
        print("\n📊 COMPARISON RESULT:")
        print(f"  Video 1: {result['video1']['path']}")
        print(f"    Hash: {result['video1']['hash']}")
        print(f"    Size: {result['video1']['size']:,} bytes")
        print(f"  Video 2: {result['video2']['path']}")
        print(f"    Hash: {result['video2']['hash']}")
        print(f"    Size: {result['video2']['size']:,} bytes")
        print(f"  Hashes different: {'✅ Yes' if result['hashes_different'] else '❌ No'}")
        print(f"  Size ratio: {result['size_ratio']:.2%}")
        
    elif args.command == 'info':
        uniquifier = VideoUniquifier()
        info = uniquifier._get_video_info(args.input)
        print(json.dumps(info, indent=2))
        
    else:
        print("🎬 VIDEO UNIQUIFIER v2.0")
        print("="*50)
        print("\nУсовершенствованный уникализатор видео для Instagram")
        print("\nUsage:")
        print("  python video_uniquifier.py single input.mp4 -o output.mp4")
        print("  python video_uniquifier.py batch input.mp4 -d ./output -c 10")
        print("  python video_uniquifier.py compare video1.mp4 video2.mp4")
        print("  python video_uniquifier.py info input.mp4")
        print("\nPresets:")
        print("  minimal    - Незаметные изменения (для аккаунтов с репутацией)")
        print("  balanced   - Сбалансированные (рекомендуется)")
        print("  aggressive - Максимальная уникальность (для новых аккаунтов)")
        print("\nМодификации v2.0:")
        print("  ✅ Crop (обрезка краёв)")
        print("  ✅ Brightness/Contrast/Saturation")
        print("  ✅ Hue shift (сдвиг цветового тона)")
        print("  ✅ Gamma correction")
        print("  ✅ Speed change")
        print("  ✅ Audio pitch shift")
        print("  ✅ Noise injection")
        print("  ✅ Micro-rotation")
        print("  ✅ Frame trimming")
        print("  ✅ Color channel shift")
        print("  ✅ Invisible watermark")
        print("  ✅ Metadata stripping")


if __name__ == "__main__":
    main()
