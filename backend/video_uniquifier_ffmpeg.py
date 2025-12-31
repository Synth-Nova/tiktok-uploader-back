"""
Video Uniquifier - FFmpeg based
Creates unique versions of videos using various effects
No external dependencies - pure FFmpeg
"""

import os
import subprocess
import random
import hashlib
import json
from datetime import datetime


class VideoUniquifier:
    """FFmpeg-based video uniquifier"""
    
    PRESETS = {
        'minimal': {
            'crop_percent': (0.3, 0.8),      # 0.3-0.8%
            'brightness': (-0.02, 0.02),      # ±2%
            'contrast': (-0.01, 0.01),        # ±1%
            'saturation': (0, 0),             # no change
            'speed': (1.0, 1.0),              # no change
            'rotation': (0, 0),               # no rotation
            'hue': (0, 0),                    # no hue shift
        },
        'balanced': {
            'crop_percent': (0.5, 2.0),       # 0.5-2%
            'brightness': (-0.05, 0.05),      # ±5%
            'contrast': (-0.03, 0.03),        # ±3%
            'saturation': (-0.05, 0.05),      # ±5%
            'speed': (0.97, 1.03),            # ±3%
            'rotation': (-0.5, 0.5),          # ±0.5°
            'hue': (-3, 3),                   # ±3°
        },
        'aggressive': {
            'crop_percent': (1.0, 3.0),       # 1-3%
            'brightness': (-0.08, 0.08),      # ±8%
            'contrast': (-0.05, 0.05),        # ±5%
            'saturation': (-0.10, 0.10),      # ±10%
            'speed': (0.95, 1.05),            # ±5%
            'rotation': (-1.0, 1.0),          # ±1°
            'hue': (-5, 5),                   # ±5°
        }
    }
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or '/opt/video-editor/outputs/uniquified'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_video_info(self, video_path):
        """Get video dimensions and duration"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-show_entries', 'format=duration',
            '-of', 'json', video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            streams = data.get('streams', [{}])
            fmt = data.get('format', {})
            
            width = streams[0].get('width', 1920) if streams else 1920
            height = streams[0].get('height', 1080) if streams else 1080
            duration = float(streams[0].get('duration') or fmt.get('duration') or 0)
            
            return {'width': width, 'height': height, 'duration': duration}
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {'width': 1920, 'height': 1080, 'duration': 0}
    
    def generate_random_params(self, preset='balanced'):
        """Generate random parameters based on preset"""
        p = self.PRESETS.get(preset, self.PRESETS['balanced'])
        
        return {
            'crop_percent': random.uniform(*p['crop_percent']),
            'brightness': random.uniform(*p['brightness']),
            'contrast': 1.0 + random.uniform(*p['contrast']),
            'saturation': 1.0 + random.uniform(*p['saturation']),
            'speed': random.uniform(*p['speed']),
            'rotation': random.uniform(*p['rotation']),
            'hue': random.uniform(*p['hue']),
            'bitrate_variation': random.uniform(0.95, 1.05),
        }
    
    def build_filter_complex(self, params, width, height):
        """Build FFmpeg filter_complex string"""
        filters = []
        
        # Crop (remove small edges)
        crop_px = int(min(width, height) * params['crop_percent'] / 100)
        if crop_px > 0:
            new_w = width - (crop_px * 2)
            new_h = height - (crop_px * 2)
            filters.append(f"crop={new_w}:{new_h}:{crop_px}:{crop_px}")
        
        # Scale back to original size
        if crop_px > 0:
            filters.append(f"scale={width}:{height}")
        
        # Rotation (small angle)
        if abs(params['rotation']) > 0.1:
            angle = params['rotation'] * 3.14159 / 180  # Convert to radians
            filters.append(f"rotate={angle}:fillcolor=black")
        
        # Color adjustments (eq filter)
        eq_parts = []
        if abs(params['brightness']) > 0.001:
            eq_parts.append(f"brightness={params['brightness']:.3f}")
        if abs(params['contrast'] - 1.0) > 0.001:
            eq_parts.append(f"contrast={params['contrast']:.3f}")
        if abs(params['saturation'] - 1.0) > 0.001:
            eq_parts.append(f"saturation={params['saturation']:.3f}")
        
        if eq_parts:
            filters.append(f"eq={':'.join(eq_parts)}")
        
        # Hue shift
        if abs(params['hue']) > 0.5:
            filters.append(f"hue=h={params['hue']:.1f}")
        
        # Speed change (setpts for video, atempo for audio)
        # This is handled separately
        
        return ','.join(filters) if filters else None
    
    def uniquify(self, input_path, output_path=None, preset='balanced', params=None):
        """
        Create a unique version of the video
        
        Args:
            input_path: Source video path
            output_path: Output path (auto-generated if None)
            preset: 'minimal', 'balanced', or 'aggressive'
            params: Custom parameters (overrides preset)
        
        Returns:
            dict with output_path, params, hash
        """
        if not os.path.exists(input_path):
            return {'error': f'Input file not found: {input_path}'}
        
        # Get video info
        info = self.get_video_info(input_path)
        width, height = info['width'], info['height']
        
        # Generate parameters
        if params is None:
            params = self.generate_random_params(preset)
        
        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            rand_id = hashlib.md5(str(random.random()).encode()).hexdigest()[:6]
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(
                self.output_dir, 
                f"{base_name}_unique_{timestamp}_{rand_id}.mp4"
            )
        
        # Build filter
        filter_complex = self.build_filter_complex(params, width, height)
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-y', '-i', input_path]
        
        # Video filters
        vf_parts = []
        if filter_complex:
            vf_parts.append(filter_complex)
        
        # Speed change
        if abs(params['speed'] - 1.0) > 0.001:
            pts_speed = 1.0 / params['speed']
            vf_parts.append(f"setpts={pts_speed:.4f}*PTS")
        
        if vf_parts:
            cmd.extend(['-vf', ','.join(vf_parts)])
        
        # Audio speed change
        if abs(params['speed'] - 1.0) > 0.001:
            # atempo only accepts 0.5-2.0, may need multiple
            atempo = params['speed']
            if 0.5 <= atempo <= 2.0:
                cmd.extend(['-af', f"atempo={atempo:.4f}"])
            else:
                cmd.extend(['-an'])  # Remove audio if speed too extreme
        
        # Output settings
        bitrate = int(5000 * params['bitrate_variation'])  # ~5Mbps base
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-b:v', f'{bitrate}k',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                return {
                    'error': f'FFmpeg error: {result.stderr[:500]}',
                    'command': ' '.join(cmd)
                }
            
            # Calculate output hash
            with open(output_path, 'rb') as f:
                output_hash = hashlib.md5(f.read(1024*1024)).hexdigest()  # First 1MB
            
            # Get output size
            output_size = os.path.getsize(output_path) / (1024 * 1024)
            
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'output_hash': output_hash,
                'size_mb': round(output_size, 2),
                'preset': preset,
                'params': {k: round(v, 4) if isinstance(v, float) else v 
                          for k, v in params.items()}
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'FFmpeg timeout (>10 min)'}
        except Exception as e:
            return {'error': str(e)}
    
    def batch_uniquify(self, input_path, output_dir=None, count=5, preset='balanced'):
        """
        Create multiple unique versions of a video
        
        Args:
            input_path: Source video path
            output_dir: Output directory (uses self.output_dir if None)
            count: Number of versions to create (1-50)
            preset: 'minimal', 'balanced', or 'aggressive'
        
        Returns:
            list of results
        """
        count = max(1, min(50, count))  # Limit 1-50
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = self.output_dir
        
        results = []
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for i in range(count):
            rand_id = hashlib.md5(f"{random.random()}{i}".encode()).hexdigest()[:6]
            output_path = os.path.join(
                output_dir,
                f"{base_name}_v{i+1:02d}_{timestamp}_{rand_id}.mp4"
            )
            
            result = self.uniquify(
                input_path=input_path,
                output_path=output_path,
                preset=preset
            )
            result['version'] = i + 1
            results.append(result)
        
        return results
    
    def get_file_hash(self, filepath):
        """Calculate file hash for comparison"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()


# Standalone test
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        uniquifier = VideoUniquifier()
        result = uniquifier.uniquify(sys.argv[1], preset='balanced')
        print(json.dumps(result, indent=2, ensure_ascii=False))
