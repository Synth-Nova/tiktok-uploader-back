"""
Video Cutter V5 API
Full-featured video cutting with folder management, montage creation, 
uniquification, and clear video type separation
"""

import os
import re
import json
import shutil
import subprocess
import threading
import random
import hashlib
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

# Try to import S3 storage
try:
    from api.s3_storage import get_s3_storage
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    print("Warning: S3 storage not available")

cutter_bp = Blueprint('cutter', __name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

# Clear folder structure
CUTS_DIR = os.path.join(OUTPUT_DIR, 'cuts')           # Нарезки
MONTAGES_DIR = os.path.join(OUTPUT_DIR, 'montages')   # Комбинированные
UNIQUIFIED_DIR = os.path.join(OUTPUT_DIR, 'uniquified')  # Уникализированные
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, 'archive')     # Архив

# S3 Configuration
S3_PUBLIC_URL = os.environ.get('S3_PUBLIC_URL', 'https://video-editor-files.s3.ru-3.storage.selcloud.ru')

# Bright Data Configuration
BRIGHTDATA_API_TOKEN = os.environ.get('BRIGHTDATA_API_TOKEN', '')
BRIGHTDATA_ZONE = os.environ.get('BRIGHTDATA_ZONE', 'web_unlocker1')
BRIGHTDATA_API_BASE = 'https://api.brightdata.com'

# Ensure directories exist
for d in [UPLOAD_DIR, OUTPUT_DIR, CUTS_DIR, MONTAGES_DIR, UNIQUIFIED_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

# Active jobs storage
active_jobs = {}
job_lock = threading.Lock()

# ==================== HELPERS ====================

def get_video_duration(filepath):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except:
        return 0

def get_video_info(filepath):
    """Get video info (duration, width, height)"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-show_entries', 'format=duration',
            '-of', 'json', filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        streams = data.get('streams', [{}])
        fmt = data.get('format', {})
        
        return {
            'width': streams[0].get('width', 0) if streams else 0,
            'height': streams[0].get('height', 0) if streams else 0,
            'duration': float(streams[0].get('duration') or fmt.get('duration') or 0)
        }
    except:
        return {'width': 0, 'height': 0, 'duration': 0}

def format_time(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def upload_to_s3(filepath, s3_key):
    """Upload file to S3"""
    if not S3_AVAILABLE:
        return None
    try:
        s3 = get_s3_storage()
        if s3 and s3.upload_file(filepath, s3_key):
            return f"{S3_PUBLIC_URL}/{s3_key}"
    except Exception as e:
        print(f"S3 upload error: {e}")
    return None

# ==================== UNIQUIFIER ====================

UNIQUIFIER_PRESETS = {
    'minimal': {
        'crop_percent': (0.3, 0.8),
        'brightness': (-0.02, 0.02),
        'contrast': (-0.01, 0.01),
        'saturation': (0, 0),
        'speed': (1.0, 1.0),
        'hue': (0, 0),
    },
    'balanced': {
        'crop_percent': (0.5, 2.0),
        'brightness': (-0.05, 0.05),
        'contrast': (-0.03, 0.03),
        'saturation': (-0.05, 0.05),
        'speed': (0.97, 1.03),
        'hue': (-3, 3),
    },
    'aggressive': {
        'crop_percent': (1.0, 3.0),
        'brightness': (-0.08, 0.08),
        'contrast': (-0.05, 0.05),
        'saturation': (-0.10, 0.10),
        'speed': (0.95, 1.05),
        'hue': (-5, 5),
    }
}

def generate_unique_params(preset='balanced'):
    """Generate random uniquification parameters"""
    p = UNIQUIFIER_PRESETS.get(preset, UNIQUIFIER_PRESETS['balanced'])
    return {
        'crop_percent': random.uniform(*p['crop_percent']),
        'brightness': random.uniform(*p['brightness']),
        'contrast': 1.0 + random.uniform(*p['contrast']),
        'saturation': 1.0 + random.uniform(*p['saturation']),
        'speed': random.uniform(*p['speed']),
        'hue': random.uniform(*p['hue']),
        'bitrate_variation': random.uniform(0.95, 1.05),
    }

def uniquify_video(input_path, output_path, preset='balanced'):
    """Apply uniquification effects to video"""
    info = get_video_info(input_path)
    width, height = info['width'] or 1920, info['height'] or 1080
    params = generate_unique_params(preset)
    
    # Build filters
    filters = []
    
    # Crop
    crop_px = int(min(width, height) * params['crop_percent'] / 100)
    if crop_px > 0:
        new_w = width - (crop_px * 2)
        new_h = height - (crop_px * 2)
        filters.append(f"crop={new_w}:{new_h}:{crop_px}:{crop_px}")
        filters.append(f"scale={width}:{height}")
    
    # Color adjustments
    eq_parts = []
    if abs(params['brightness']) > 0.001:
        eq_parts.append(f"brightness={params['brightness']:.3f}")
    if abs(params['contrast'] - 1.0) > 0.001:
        eq_parts.append(f"contrast={params['contrast']:.3f}")
    if abs(params['saturation'] - 1.0) > 0.001:
        eq_parts.append(f"saturation={params['saturation']:.3f}")
    if eq_parts:
        filters.append(f"eq={':'.join(eq_parts)}")
    
    # Hue
    if abs(params['hue']) > 0.5:
        filters.append(f"hue=h={params['hue']:.1f}")
    
    # Speed
    if abs(params['speed'] - 1.0) > 0.001:
        pts_speed = 1.0 / params['speed']
        filters.append(f"setpts={pts_speed:.4f}*PTS")
    
    # Build command
    cmd = ['ffmpeg', '-y', '-i', input_path]
    
    if filters:
        cmd.extend(['-vf', ','.join(filters)])
    
    # Audio speed
    if abs(params['speed'] - 1.0) > 0.001:
        atempo = params['speed']
        if 0.5 <= atempo <= 2.0:
            cmd.extend(['-af', f"atempo={atempo:.4f}"])
    
    # Output settings
    bitrate = int(5000 * params['bitrate_variation'])
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
            return {'error': result.stderr[:300]}
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        return {
            'success': True,
            'output_path': output_path,
            'size_mb': round(size_mb, 2),
            'params': params
        }
    except Exception as e:
        return {'error': str(e)}

def uniquify_worker(job_id, input_path, output_folder, count, preset, upload_s3):
    """Background worker for batch uniquification"""
    global active_jobs
    
    try:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with job_lock:
            active_jobs[job_id]['total'] = count
            active_jobs[job_id]['status'] = 'processing'
        
        results = []
        
        for i in range(count):
            # Check cancelled
            with job_lock:
                if active_jobs[job_id].get('cancelled'):
                    active_jobs[job_id]['status'] = 'cancelled'
                    active_jobs[job_id]['results'] = results
                    return
            
            rand_id = hashlib.md5(f"{random.random()}{i}".encode()).hexdigest()[:6]
            output_filename = f"{base_name}_u{i+1:02d}_{timestamp}_{rand_id}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            result = uniquify_video(input_path, output_path, preset)
            
            if result.get('success'):
                item = {
                    'version': i + 1,
                    'filename': output_filename,
                    'size_mb': result['size_mb'],
                    'download_url': f'/video-outputs/uniquified/{job_id}/{output_filename}'
                }
                
                # Upload to S3
                if upload_s3:
                    s3_key = f"outputs/uniquified/{job_id}/{output_filename}"
                    s3_url = upload_to_s3(output_path, s3_key)
                    if s3_url:
                        item['s3_url'] = s3_url
                
                results.append(item)
            
            # Update progress
            with job_lock:
                active_jobs[job_id]['current'] = i + 1
                active_jobs[job_id]['progress'] = round(((i + 1) / count) * 100, 1)
                active_jobs[job_id]['results'] = results
                active_jobs[job_id]['message'] = f'Версия {i+1} из {count}'
        
        # Complete
        with job_lock:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['results'] = results
            
    except Exception as e:
        with job_lock:
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['error'] = str(e)

# ==================== CUT WORKER ====================

def cut_video_worker(job_id, source_path, folder_path, segment_duration, upload_to_s3_flag):
    """Background worker for video cutting"""
    global active_jobs
    
    try:
        duration = get_video_duration(source_path)
        if duration <= 0:
            with job_lock:
                active_jobs[job_id]['status'] = 'error'
                active_jobs[job_id]['error'] = 'Could not get video duration'
            return
        
        total_cuts = int(duration // segment_duration) + (1 if duration % segment_duration > 0 else 0)
        source_filename = os.path.basename(source_path)
        base_name = os.path.splitext(source_filename)[0]
        
        with job_lock:
            active_jobs[job_id]['total_cuts'] = total_cuts
            active_jobs[job_id]['status'] = 'processing'
        
        cuts = []
        
        for i in range(total_cuts):
            with job_lock:
                if active_jobs[job_id].get('cancelled'):
                    active_jobs[job_id]['status'] = 'cancelled'
                    active_jobs[job_id]['cuts'] = cuts
                    return
            
            start_time = i * segment_duration
            output_filename = f"{base_name}_cut_{i+1:03d}.mp4"
            output_path = os.path.join(folder_path, output_filename)
            
            cmd = [
                'ffmpeg', '-y', '-ss', str(start_time),
                '-i', source_path,
                '-t', str(segment_duration),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                output_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                
                cut_info = {
                    'index': i,
                    'filename': output_filename,
                    'size_mb': round(size_mb, 2),
                    'start_time': start_time,
                    'start_time_formatted': format_time(start_time),
                    'download_url': f'/video-outputs/cuts/{job_id}/{output_filename}'
                }
                
                if upload_to_s3_flag:
                    s3_key = f"outputs/cuts/{job_id}/{output_filename}"
                    s3_url = upload_to_s3(output_path, s3_key)
                    if s3_url:
                        cut_info['s3_url'] = s3_url
                
                cuts.append(cut_info)
                
                with job_lock:
                    progress = ((i + 1) / total_cuts) * 100
                    active_jobs[job_id]['current_cut'] = i + 1
                    active_jobs[job_id]['progress'] = round(progress, 1)
                    active_jobs[job_id]['message'] = f'Кусок {i+1} из {total_cuts}'
                    active_jobs[job_id]['cuts'] = cuts
                    
            except subprocess.CalledProcessError:
                continue
        
        with job_lock:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['cuts'] = cuts
            
    except Exception as e:
        with job_lock:
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['error'] = str(e)

# ==================== API ENDPOINTS ====================

@cutter_bp.route('/list-videos', methods=['GET'])
def list_videos():
    """List available master videos"""
    videos = []
    
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.isdir(filepath):
                continue
            if not filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                continue
            
            try:
                info = get_video_info(filepath)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                videos.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size_mb': round(size_mb, 1),
                    'duration': info['duration'],
                    'duration_formatted': format_time(info['duration']),
                    'width': info['width'],
                    'height': info['height'],
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    'type': 'master'
                })
            except:
                continue
    
    videos.sort(key=lambda x: x['created'], reverse=True)
    return jsonify({'success': True, 'videos': videos, 'total': len(videos)})


@cutter_bp.route('/cut', methods=['POST'])
def start_cut():
    """Start video cutting job"""
    data = request.get_json()
    filename = data.get('filename')
    segment_duration = data.get('segment_duration', 15)
    folder_name = data.get('folder_name', '')
    upload_s3 = data.get('upload_to_s3', True)
    
    if not filename:
        return jsonify({'success': False, 'error': 'filename required'})
    
    source_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(source_path):
        return jsonify({'success': False, 'error': 'Video file not found'})
    
    if folder_name:
        job_id = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name)
    else:
        base_name = os.path.splitext(filename)[0][:20]
        job_id = f"cuts_{base_name}_{segment_duration}s"
    
    folder_path = os.path.join(CUTS_DIR, job_id)
    os.makedirs(folder_path, exist_ok=True)
    
    with job_lock:
        active_jobs[job_id] = {
            'type': 'cut',
            'status': 'pending',
            'progress': 0,
            'current_cut': 0,
            'total_cuts': 0,
            'source_file': filename,
            'output_folder': folder_path,
            'cuts': [],
            'message': 'Запуск...',
            'cancelled': False
        }
    
    thread = threading.Thread(
        target=cut_video_worker,
        args=(job_id, source_path, folder_path, segment_duration, upload_s3)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'job_id': job_id})


@cutter_bp.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status"""
    with job_lock:
        if job_id not in active_jobs:
            return jsonify({'success': False, 'error': 'Job not found'})
        job = active_jobs[job_id].copy()
    return jsonify({'success': True, 'job_id': job_id, **job})


@cutter_bp.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel running job"""
    with job_lock:
        if job_id not in active_jobs:
            return jsonify({'success': False, 'error': 'Job not found'})
        active_jobs[job_id]['cancelled'] = True
    return jsonify({'success': True})


# ==================== FOLDERS ====================

@cutter_bp.route('/folders', methods=['GET'])
def list_folders():
    """List all folders by type"""
    video_type = request.args.get('type', 'all')  # cuts, montages, uniquified, all
    
    folders = []
    
    def scan_dir(base_dir, folder_type):
        if not os.path.exists(base_dir):
            return
        for name in os.listdir(base_dir):
            path = os.path.join(base_dir, name)
            if os.path.isdir(path):
                files = [f for f in os.listdir(path) if f.endswith('.mp4')]
                total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files) / (1024*1024)
                folders.append({
                    'name': name,
                    'path': path,
                    'type': folder_type,
                    'files_count': len(files),
                    'total_size_mb': round(total_size, 1),
                    'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
                    'archived': False
                })
    
    if video_type in ['cuts', 'all']:
        scan_dir(CUTS_DIR, 'cuts')
    if video_type in ['montages', 'all']:
        scan_dir(MONTAGES_DIR, 'montages')
    if video_type in ['uniquified', 'all']:
        scan_dir(UNIQUIFIED_DIR, 'uniquified')
    if video_type == 'all':
        scan_dir(ARCHIVE_DIR, 'archived')
    
    folders.sort(key=lambda x: x['created'], reverse=True)
    return jsonify({'success': True, 'folders': folders, 'total': len(folders)})


@cutter_bp.route('/folder-files/<folder_name>', methods=['GET'])
def get_folder_files(folder_name):
    """Get files in folder"""
    # Search in all directories
    for base_dir, folder_type in [
        (CUTS_DIR, 'cuts'),
        (MONTAGES_DIR, 'montages'),
        (UNIQUIFIED_DIR, 'uniquified'),
        (ARCHIVE_DIR, 'archived')
    ]:
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.exists(folder_path):
            files = []
            for f in sorted(os.listdir(folder_path)):
                if f.endswith('.mp4'):
                    file_path = os.path.join(folder_path, f)
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    files.append({
                        'filename': f,
                        'size_mb': round(size_mb, 2),
                        'download_url': f'/video-outputs/{folder_type}/{folder_name}/{f}',
                        's3_url': f'{S3_PUBLIC_URL}/outputs/{folder_type}/{folder_name}/{f}' if S3_PUBLIC_URL else None
                    })
            
            return jsonify({
                'success': True,
                'folder': folder_name,
                'type': folder_type,
                'files': files,
                'total': len(files)
            })
    
    return jsonify({'success': False, 'error': 'Folder not found'})


@cutter_bp.route('/delete-folder/<folder_name>', methods=['DELETE'])
def delete_folder(folder_name):
    """Delete folder"""
    for base_dir in [CUTS_DIR, MONTAGES_DIR, UNIQUIFIED_DIR, ARCHIVE_DIR]:
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Folder not found'})


@cutter_bp.route('/s3-urls/<folder_name>', methods=['GET'])
def get_s3_urls(folder_name):
    """Get S3/download URLs for folder"""
    for base_dir, folder_type in [
        (CUTS_DIR, 'cuts'),
        (MONTAGES_DIR, 'montages'),
        (UNIQUIFIED_DIR, 'uniquified')
    ]:
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.exists(folder_path):
            urls = []
            for f in sorted(os.listdir(folder_path)):
                if f.endswith('.mp4'):
                    urls.append({
                        'filename': f,
                        'download_url': f'/video-outputs/{folder_type}/{folder_name}/{f}',
                        's3_url': f'{S3_PUBLIC_URL}/outputs/{folder_type}/{folder_name}/{f}'
                    })
            return jsonify({'success': True, 'urls': urls, 'total': len(urls)})
    
    return jsonify({'success': False, 'error': 'Folder not found'})


# ==================== MONTAGE ====================

@cutter_bp.route('/combine-montage', methods=['POST'])
def combine_montage():
    """Create montage from cuts"""
    data = request.get_json()
    folder_name = data.get('folder_name')
    middle_count = data.get('middle_count', 10)
    variants = data.get('variants', 1)
    shuffle = data.get('shuffle', True)
    
    if not folder_name:
        return jsonify({'success': False, 'error': 'folder_name required'})
    
    # Find source folder
    folder_path = os.path.join(CUTS_DIR, folder_name)
    if not os.path.exists(folder_path):
        return jsonify({'success': False, 'error': 'Folder not found'})
    
    all_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
    if not all_files:
        return jsonify({'success': False, 'error': 'No videos in folder'})
    
    middle_count = min(middle_count, len(all_files))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create montage output folder
    montage_folder = os.path.join(MONTAGES_DIR, f"montage_{folder_name}_{timestamp}")
    os.makedirs(montage_folder, exist_ok=True)
    
    results = []
    
    for v in range(variants):
        selected = all_files.copy()
        if shuffle:
            random.shuffle(selected)
        selected = selected[:middle_count]
        
        # Concat file
        concat_file = os.path.join(montage_folder, f'concat_v{v:02d}.txt')
        with open(concat_file, 'w') as f:
            for filename in selected:
                f.write(f"file '{os.path.join(folder_path, filename)}'\n")
        
        output_filename = f"combined_{folder_name}_{timestamp}_v{v:02d}.mp4"
        output_path = os.path.join(montage_folder, output_filename)
        
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file, '-c', 'copy', output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            duration = get_video_duration(output_path)
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            results.append({
                'variant': v,
                'filename': output_filename,
                'download_url': f'/video-outputs/montages/montage_{folder_name}_{timestamp}/{output_filename}',
                'duration': round(duration, 2),
                'size_mb': round(size_mb, 2),
                'shots_used': len(selected)
            })
        except:
            continue
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
    
    return jsonify({
        'success': True,
        'folder': folder_name,
        'output_folder': f"montage_{folder_name}_{timestamp}",
        'variants': results,
        'total_variants': len(results)
    })


# ==================== UNIQUIFICATION ====================

@cutter_bp.route('/uniquify', methods=['POST'])
def start_uniquify():
    """Start uniquification job"""
    data = request.get_json()
    source_folder = data.get('source_folder')  # montage folder name
    source_file = data.get('source_file')      # specific file
    count = min(50, max(1, data.get('count', 5)))
    preset = data.get('preset', 'balanced')
    upload_s3 = data.get('upload_to_s3', False)
    
    # Find source
    input_path = None
    
    if source_file:
        # Direct file path
        for base_dir in [MONTAGES_DIR, CUTS_DIR, OUTPUT_DIR]:
            for root, dirs, files in os.walk(base_dir):
                if source_file in files:
                    input_path = os.path.join(root, source_file)
                    break
            if input_path:
                break
    elif source_folder:
        # First file from folder
        for base_dir in [MONTAGES_DIR, CUTS_DIR]:
            folder_path = os.path.join(base_dir, source_folder)
            if os.path.exists(folder_path):
                files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
                if files:
                    input_path = os.path.join(folder_path, files[0])
                break
    
    if not input_path or not os.path.exists(input_path):
        return jsonify({'success': False, 'error': 'Source video not found'})
    
    # Create job
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(os.path.basename(input_path))[0][:20]
    job_id = f"unique_{base_name}_{timestamp}"
    
    output_folder = os.path.join(UNIQUIFIED_DIR, job_id)
    os.makedirs(output_folder, exist_ok=True)
    
    with job_lock:
        active_jobs[job_id] = {
            'type': 'uniquify',
            'status': 'pending',
            'progress': 0,
            'current': 0,
            'total': count,
            'source_file': os.path.basename(input_path),
            'preset': preset,
            'results': [],
            'message': 'Запуск...',
            'cancelled': False
        }
    
    thread = threading.Thread(
        target=uniquify_worker,
        args=(job_id, input_path, output_folder, count, preset, upload_s3)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'job_id': job_id})


@cutter_bp.route('/uniquify-presets', methods=['GET'])
def get_uniquify_presets():
    """Get available uniquification presets"""
    return jsonify({
        'success': True,
        'presets': {
            'minimal': {
                'name': 'Минимальный',
                'description': 'Почти незаметные изменения',
                'effects': ['Crop 0.3-0.8%', 'Яркость ±2%', 'Контраст ±1%']
            },
            'balanced': {
                'name': 'Сбалансированный',
                'description': 'Оптимальный баланс (рекомендуется)',
                'effects': ['Crop 0.5-2%', 'Яркость ±5%', 'Контраст ±3%', 'Насыщенность ±5%', 'Скорость ±3%', 'Сдвиг цвета ±3°']
            },
            'aggressive': {
                'name': 'Агрессивный',
                'description': 'Максимальная уникальность',
                'effects': ['Crop 1-3%', 'Яркость ±8%', 'Контраст ±5%', 'Насыщенность ±10%', 'Скорость ±5%', 'Сдвиг цвета ±5°']
            }
        }
    })


# ==================== ZIP & TIKTOK INTEGRATION ====================

@cutter_bp.route('/create-zip/<folder_name>', methods=['POST'])
def create_zip(folder_name):
    """Create ZIP archive from folder for TikTok upload"""
    import zipfile
    
    # Find folder
    folder_path = None
    folder_type = None
    
    for base_dir, ftype in [
        (UNIQUIFIED_DIR, 'uniquified'),
        (MONTAGES_DIR, 'montages'),
        (CUTS_DIR, 'cuts')
    ]:
        path = os.path.join(base_dir, folder_name)
        if os.path.exists(path):
            folder_path = path
            folder_type = ftype
            break
    
    if not folder_path:
        return jsonify({'success': False, 'error': 'Folder not found'})
    
    # Get MP4 files
    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
    if not files:
        return jsonify({'success': False, 'error': 'No videos in folder'})
    
    # Create ZIP
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"{folder_name}_{timestamp}.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                file_path = os.path.join(folder_path, f)
                zf.write(file_path, f)
        
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'zip_filename': zip_filename,
            'zip_path': zip_path,
            'download_url': f'/video-outputs/{zip_filename}',
            'size_mb': round(size_mb, 2),
            'files_count': len(files),
            'source_folder': folder_name,
            'source_type': folder_type
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/prepare-tiktok-upload', methods=['POST'])
def prepare_tiktok_upload():
    """Prepare data for TikTok batch upload - returns info about what will be sent"""
    data = request.get_json()
    folder_name = data.get('folder_name')
    
    if not folder_name:
        return jsonify({'success': False, 'error': 'folder_name required'})
    
    # Find folder
    folder_path = None
    folder_type = None
    
    for base_dir, ftype in [
        (UNIQUIFIED_DIR, 'uniquified'),
        (MONTAGES_DIR, 'montages'),
        (CUTS_DIR, 'cuts')
    ]:
        path = os.path.join(base_dir, folder_name)
        if os.path.exists(path):
            folder_path = path
            folder_type = ftype
            break
    
    if not folder_path:
        return jsonify({'success': False, 'error': 'Folder not found'})
    
    # Get videos info
    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
    total_size = sum(os.path.getsize(os.path.join(folder_path, f)) for f in files) / (1024*1024)
    
    return jsonify({
        'success': True,
        'folder_name': folder_name,
        'folder_type': folder_type,
        'videos_count': len(files),
        'total_size_mb': round(total_size, 2),
        'videos': [{'filename': f, 'size_mb': round(os.path.getsize(os.path.join(folder_path, f)) / (1024*1024), 2)} for f in files],
        'ready_for_upload': True,
        'instructions': {
            'step1': 'Создать ZIP с видео (POST /create-zip/{folder_name})',
            'step2': 'Отправить на /api/batch-upload с файлами: videos (zip), accounts (txt), proxies (txt)',
            'accounts_format': 'username:password (по строке)',
            'proxies_format': 'ip:port:user:pass (по строке)',
            'note': 'Количество аккаунтов должно совпадать с количеством прокси'
        }
    })


@cutter_bp.route('/list-zips', methods=['GET'])
def list_zips():
    """List available ZIP files for upload"""
    zips = []
    
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.zip'):
                filepath = os.path.join(OUTPUT_DIR, filename)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                created = datetime.fromtimestamp(os.path.getctime(filepath))
                
                zips.append({
                    'filename': filename,
                    'size_mb': round(size_mb, 2),
                    'download_url': f'/video-outputs/{filename}',
                    'created': created.isoformat()
                })
    
    zips.sort(key=lambda x: x['created'], reverse=True)
    return jsonify({'success': True, 'zips': zips, 'total': len(zips)})


@cutter_bp.route('/delete-zip/<filename>', methods=['DELETE'])
def delete_zip(filename):
    """Delete a ZIP file"""
    if not filename.endswith('.zip'):
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'File not found'})


# ==================== STATS ====================

@cutter_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    def count_folder(base_dir):
        if not os.path.exists(base_dir):
            return {'folders': 0, 'files': 0, 'size_mb': 0}
        
        folders = 0
        files = 0
        size = 0
        
        for name in os.listdir(base_dir):
            path = os.path.join(base_dir, name)
            if os.path.isdir(path):
                folders += 1
                for f in os.listdir(path):
                    if f.endswith('.mp4'):
                        files += 1
                        size += os.path.getsize(os.path.join(path, f))
        
        return {'folders': folders, 'files': files, 'size_mb': round(size / (1024*1024), 1)}
    
    return jsonify({
        'success': True,
        'masters': count_folder(UPLOAD_DIR),
        'cuts': count_folder(CUTS_DIR),
        'montages': count_folder(MONTAGES_DIR),
        'uniquified': count_folder(UNIQUIFIED_DIR),
        'archived': count_folder(ARCHIVE_DIR)
    })


# ==================== BRIGHT DATA PROXY ====================

@cutter_bp.route('/proxy/config', methods=['GET'])
def get_proxy_config():
    """Get Bright Data proxy configuration"""
    return jsonify({
        'success': True,
        'configured': bool(BRIGHTDATA_API_TOKEN),
        'zone': BRIGHTDATA_ZONE,
        'provider': 'Bright Data'
    })


@cutter_bp.route('/proxy/save-config', methods=['POST'])
def save_proxy_config():
    """Save Bright Data API token"""
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
        'configured': bool(BRIGHTDATA_API_TOKEN)
    })


@cutter_bp.route('/proxy/test', methods=['POST'])
def test_proxy():
    """Test Bright Data connection"""
    if not BRIGHTDATA_API_TOKEN:
        return jsonify({'success': False, 'error': 'API Token not configured'})
    
    try:
        response = requests.post(
            f'{BRIGHTDATA_API_BASE}/request',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {BRIGHTDATA_API_TOKEN}'
            },
            json={
                'zone': BRIGHTDATA_ZONE,
                'url': 'https://geo.brdtest.com/welcome.txt',
                'format': 'raw'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Connection successful!',
                'response': response.text[:200],
                'ip_info': response.text
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API error: {response.status_code}',
                'details': response.text[:300]
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/proxy/generate', methods=['POST'])
def generate_proxies():
    """
    Generate proxy list using Bright Data Web Unlocker API
    For TikTok upload - generates session-based proxies
    """
    if not BRIGHTDATA_API_TOKEN:
        return jsonify({'success': False, 'error': 'API Token not configured. Go to Settings to add your Bright Data API token.'})
    
    data = request.get_json() or {}
    count = min(100, max(1, data.get('count', 10)))
    country = data.get('country', 'us').lower()
    
    # For Web Unlocker API, we use the API endpoint format
    # Each request gets a new IP automatically
    
    # Generate proxy configuration for TikTok uploader
    # Format expected by the system: ip:port:user:pass
    
    proxies = []
    
    # Bright Data Web Unlocker uses API calls, not traditional proxy format
    # We'll generate session IDs for sticky sessions if needed
    
    for i in range(count):
        # Create unique session for each proxy
        session_id = f'tiktok_{datetime.now().strftime("%Y%m%d%H%M%S")}_{i}_{random.randint(1000, 9999)}'
        
        # For Web Unlocker API format
        # The actual proxy call will use the API
        proxy_entry = {
            'session_id': session_id,
            'country': country,
            'index': i + 1
        }
        
        # Generate traditional proxy string format
        # Using Bright Data super proxy with session
        proxy_string = f'brd.superproxy.io:22225:brd-customer-hl_xxxxxxxx-zone-{BRIGHTDATA_ZONE}-country-{country}-session-{session_id}:{BRIGHTDATA_API_TOKEN}'
        
        proxies.append(proxy_string)
    
    # Create downloadable text
    proxy_text = '\n'.join(proxies)
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'proxies_{country}_{count}_{timestamp}.txt'
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w') as f:
        f.write(proxy_text)
    
    return jsonify({
        'success': True,
        'count': count,
        'country': country,
        'filename': filename,
        'download_url': f'/video-outputs/{filename}',
        'proxies': proxies,
        'proxy_text': proxy_text,
        'format': 'host:port:username:password',
        'note': 'Proxies ready for TikTok upload'
    })


@cutter_bp.route('/proxy/countries', methods=['GET'])
def get_proxy_countries():
    """Get available proxy countries"""
    countries = [
        {'code': 'us', 'name': 'United States'},
        {'code': 'gb', 'name': 'United Kingdom'},
        {'code': 'de', 'name': 'Germany'},
        {'code': 'fr', 'name': 'France'},
        {'code': 'ru', 'name': 'Russia'},
        {'code': 'ua', 'name': 'Ukraine'},
        {'code': 'pl', 'name': 'Poland'},
        {'code': 'nl', 'name': 'Netherlands'},
        {'code': 'it', 'name': 'Italy'},
        {'code': 'es', 'name': 'Spain'},
        {'code': 'br', 'name': 'Brazil'},
        {'code': 'mx', 'name': 'Mexico'},
        {'code': 'ca', 'name': 'Canada'},
        {'code': 'au', 'name': 'Australia'},
        {'code': 'jp', 'name': 'Japan'},
        {'code': 'kr', 'name': 'South Korea'},
        {'code': 'in', 'name': 'India'},
        {'code': 'id', 'name': 'Indonesia'},
        {'code': 'th', 'name': 'Thailand'},
        {'code': 'vn', 'name': 'Vietnam'},
    ]
    return jsonify({'success': True, 'countries': countries})


@cutter_bp.route('/parse-sound-url', methods=['POST'])
def parse_sound_url():
    """Parse TikTok sound URL to extract sound ID and name"""
    import urllib.parse
    
    data = request.get_json() or {}
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    try:
        original_url = url
        
        # Handle short URLs by following redirects
        if 'vt.tiktok.com' in url or 'vm.tiktok.com' in url:
            try:
                response = requests.head(url, allow_redirects=True, timeout=10)
                url = response.url
            except Exception as e:
                # Try GET if HEAD fails
                try:
                    response = requests.get(url, allow_redirects=True, timeout=10)
                    url = response.url
                except:
                    pass
        
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        
        # Extract from /music/NAME-ID format
        music_match = re.search(r'/music/([^/]+)-(\d{15,25})', path)
        if music_match:
            name = music_match.group(1).replace('-', ' ')
            sound_id = music_match.group(2)
            return jsonify({
                'success': True,
                'sound_id': sound_id,
                'sound_name': name,
                'original_url': original_url,
                'resolved_url': url
            })
        
        # Try to extract from query params
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'share_music_id' in query_params:
            return jsonify({
                'success': True,
                'sound_id': query_params['share_music_id'][0],
                'sound_name': None,
                'original_url': original_url,
                'resolved_url': url
            })
        
        # Try to find any long number that could be an ID
        id_match = re.search(r'(\d{15,25})', url)
        if id_match:
            return jsonify({
                'success': True,
                'sound_id': id_match.group(1),
                'sound_name': None,
                'original_url': original_url,
                'resolved_url': url
            })
        
        return jsonify({
            'success': False,
            'error': 'Could not extract sound ID from URL',
            'original_url': original_url,
            'resolved_url': url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# ==================== TIKTOK SOUND ====================

SOUNDS_DIR = os.path.join(OUTPUT_DIR, 'sounds')
os.makedirs(SOUNDS_DIR, exist_ok=True)

def download_sound(url, output_path):
    """Download sound from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return {'success': True, 'path': output_path}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def extract_audio_from_video(video_path, output_path):
    """Extract audio track from video file"""
    try:
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_path):
            return {'success': True, 'path': output_path}
        return {'success': False, 'error': result.stderr[:300]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_audio_duration(filepath):
    """Get audio duration in seconds"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except:
        return 0


@cutter_bp.route('/sounds', methods=['GET'])
def list_sounds():
    """List available sounds in library"""
    sounds = []
    
    if os.path.exists(SOUNDS_DIR):
        for filename in os.listdir(SOUNDS_DIR):
            if filename.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg')):
                filepath = os.path.join(SOUNDS_DIR, filename)
                try:
                    duration = get_audio_duration(filepath)
                    size_kb = os.path.getsize(filepath) / 1024
                    sounds.append({
                        'filename': filename,
                        'duration': round(duration, 2),
                        'duration_formatted': format_time(duration),
                        'size_kb': round(size_kb, 1),
                        'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                    })
                except:
                    continue
    
    sounds.sort(key=lambda x: x['created'], reverse=True)
    return jsonify({'success': True, 'sounds': sounds, 'total': len(sounds)})


@cutter_bp.route('/upload-sound', methods=['POST'])
def upload_sound():
    """Upload sound file to library"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Validate extension
    allowed_ext = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        return jsonify({'success': False, 'error': f'Invalid format. Allowed: {", ".join(allowed_ext)}'})
    
    # Save file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    filename = f"{timestamp}_{safe_name}"
    filepath = os.path.join(SOUNDS_DIR, filename)
    
    file.save(filepath)
    
    duration = get_audio_duration(filepath)
    size_kb = os.path.getsize(filepath) / 1024
    
    return jsonify({
        'success': True,
        'filename': filename,
        'duration': round(duration, 2),
        'size_kb': round(size_kb, 1)
    })


@cutter_bp.route('/download-tiktok-sound', methods=['POST'])
def download_tiktok_sound():
    """
    Download TikTok sound by URL
    Note: TikTok doesn't provide direct sound download API
    This attempts to extract from video or use third-party services
    """
    data = request.get_json() or {}
    sound_url = data.get('url', '')
    sound_name = data.get('name', '')
    
    if not sound_url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # First, parse the URL to get sound ID
    try:
        # Handle short URLs
        if 'vt.tiktok.com' in sound_url or 'vm.tiktok.com' in sound_url:
            try:
                response = requests.head(sound_url, allow_redirects=True, timeout=10)
                sound_url = response.url
            except:
                pass
        
        # Extract sound ID
        sound_id = None
        music_match = re.search(r'/music/[^/]+-(\d{15,25})', sound_url)
        if music_match:
            sound_id = music_match.group(1)
        else:
            id_match = re.search(r'(\d{15,25})', sound_url)
            if id_match:
                sound_id = id_match.group(1)
        
        if not sound_id:
            return jsonify({
                'success': False,
                'error': 'Could not extract sound ID from URL',
                'hint': 'You can manually download the sound and upload it via /upload-sound'
            })
        
        # TikTok sound API endpoint (unofficial)
        # Note: This may not work as TikTok blocks direct access
        # Alternative: Use yt-dlp or similar tools
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', sound_name or f'tiktok_{sound_id}')
        filename = f"{safe_name}_{timestamp}.mp3"
        filepath = os.path.join(SOUNDS_DIR, filename)
        
        # Try using yt-dlp if available
        try:
            ytdlp_cmd = [
                'yt-dlp', '-x', '--audio-format', 'mp3',
                '-o', filepath.replace('.mp3', '.%(ext)s'),
                f'https://www.tiktok.com/music/-{sound_id}'
            ]
            result = subprocess.run(ytdlp_cmd, capture_output=True, text=True, timeout=60)
            
            # Check if file was created (yt-dlp may change extension)
            possible_files = [
                filepath,
                filepath.replace('.mp3', '.m4a'),
                filepath.replace('.mp3', '.webm')
            ]
            
            for pf in possible_files:
                if os.path.exists(pf):
                    # Convert to mp3 if needed
                    if not pf.endswith('.mp3'):
                        mp3_path = pf.rsplit('.', 1)[0] + '.mp3'
                        convert_cmd = ['ffmpeg', '-y', '-i', pf, '-acodec', 'libmp3lame', '-q:a', '2', mp3_path]
                        subprocess.run(convert_cmd, capture_output=True, timeout=60)
                        os.remove(pf)
                        pf = mp3_path
                    
                    duration = get_audio_duration(pf)
                    return jsonify({
                        'success': True,
                        'filename': os.path.basename(pf),
                        'sound_id': sound_id,
                        'duration': round(duration, 2),
                        'method': 'yt-dlp'
                    })
        except FileNotFoundError:
            pass  # yt-dlp not installed
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"yt-dlp error: {e}")
        
        # If yt-dlp failed, return instructions for manual download
        return jsonify({
            'success': False,
            'sound_id': sound_id,
            'error': 'Automatic download not available',
            'instructions': {
                'option1': 'Install yt-dlp: pip install yt-dlp',
                'option2': 'Download manually from TikTok and upload via /upload-sound',
                'option3': 'Use a TikTok sound downloader website and upload the file'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/add-sound', methods=['POST'])
def add_sound_to_video():
    """
    Add sound to video with customizable settings
    
    Parameters:
    - video_file: filename of video in cuts/montages/uniquified folder
    - video_folder: folder containing the video (optional, will search)
    - sound_file: filename of sound in sounds library
    - sound_url: URL to download sound from (alternative to sound_file)
    - sound_start: start time in sound file (seconds), default 0
    - video_start: where to start adding sound in video (seconds), default 0
    - duration: how long the sound should play (seconds), default: video length
    - volume: sound volume 0.0-2.0, default 1.0
    - mix_mode: 'replace' (remove original audio) or 'mix' (combine), default 'mix'
    - mix_ratio: ratio of original:new audio when mixing (0.0-1.0), default 0.3
    - output_folder: folder name for output, default auto-generated
    """
    data = request.get_json() or {}
    
    video_file = data.get('video_file')
    video_folder = data.get('video_folder')
    sound_file = data.get('sound_file')
    sound_url = data.get('sound_url')
    sound_start = float(data.get('sound_start', 0))
    video_start = float(data.get('video_start', 0))
    duration = data.get('duration')  # None = full video
    volume = float(data.get('volume', 1.0))
    mix_mode = data.get('mix_mode', 'mix')  # 'replace' or 'mix'
    mix_ratio = float(data.get('mix_ratio', 0.3))  # original audio ratio
    output_folder = data.get('output_folder')
    
    # Validate inputs
    if not video_file:
        return jsonify({'success': False, 'error': 'video_file is required'})
    
    if not sound_file and not sound_url:
        return jsonify({'success': False, 'error': 'sound_file or sound_url is required'})
    
    # Find video file
    video_path = None
    video_type = None
    
    search_dirs = [
        (CUTS_DIR, 'cuts'),
        (MONTAGES_DIR, 'montages'),
        (UNIQUIFIED_DIR, 'uniquified'),
        (UPLOAD_DIR, 'uploads')
    ]
    
    if video_folder:
        # Search in specific folder
        for base_dir, vtype in search_dirs:
            folder_path = os.path.join(base_dir, video_folder)
            if os.path.exists(folder_path):
                file_path = os.path.join(folder_path, video_file)
                if os.path.exists(file_path):
                    video_path = file_path
                    video_type = vtype
                    break
    else:
        # Search everywhere
        for base_dir, vtype in search_dirs:
            # Check in base dir
            file_path = os.path.join(base_dir, video_file)
            if os.path.exists(file_path):
                video_path = file_path
                video_type = vtype
                break
            
            # Check in subdirs
            if os.path.exists(base_dir):
                for subdir in os.listdir(base_dir):
                    subdir_path = os.path.join(base_dir, subdir)
                    if os.path.isdir(subdir_path):
                        file_path = os.path.join(subdir_path, video_file)
                        if os.path.exists(file_path):
                            video_path = file_path
                            video_type = vtype
                            video_folder = subdir
                            break
                if video_path:
                    break
    
    if not video_path:
        return jsonify({'success': False, 'error': f'Video file not found: {video_file}'})
    
    # Get/download sound file
    sound_path = None
    
    if sound_file:
        sound_path = os.path.join(SOUNDS_DIR, sound_file)
        if not os.path.exists(sound_path):
            return jsonify({'success': False, 'error': f'Sound file not found: {sound_file}'})
    elif sound_url:
        # Download sound
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_sound = os.path.join(SOUNDS_DIR, f'temp_sound_{timestamp}.mp3')
        download_result = download_sound(sound_url, temp_sound)
        if not download_result.get('success'):
            return jsonify({'success': False, 'error': f'Failed to download sound: {download_result.get("error")}'})
        sound_path = temp_sound
    
    # Get video info
    video_info = get_video_info(video_path)
    video_duration = video_info['duration']
    
    if video_duration <= 0:
        return jsonify({'success': False, 'error': 'Could not get video duration'})
    
    # Calculate actual duration
    actual_duration = duration if duration else (video_duration - video_start)
    actual_duration = min(actual_duration, video_duration - video_start)
    
    # Get sound info
    sound_duration = get_audio_duration(sound_path)
    
    # Create output folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if not output_folder:
        base_name = os.path.splitext(video_file)[0][:15]
        output_folder = f"with_sound_{base_name}_{timestamp}"
    
    output_dir = os.path.join(OUTPUT_DIR, 'with_sound', output_folder)
    os.makedirs(output_dir, exist_ok=True)
    
    # Build output filename
    sound_name = os.path.splitext(os.path.basename(sound_path))[0][:10]
    output_filename = f"{os.path.splitext(video_file)[0]}_sound_{sound_name}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    # Build FFmpeg command
    try:
        if mix_mode == 'replace':
            # Replace original audio completely
            filter_complex = []
            
            # Trim sound to start at specified position
            if sound_start > 0:
                filter_complex.append(f"[1:a]atrim=start={sound_start},asetpts=PTS-STARTPTS[snd]")
                sound_input = "[snd]"
            else:
                sound_input = "[1:a]"
            
            # Adjust volume
            if volume != 1.0:
                filter_complex.append(f"{sound_input}volume={volume}[volsnd]")
                sound_input = "[volsnd]"
            
            # Add delay if video_start > 0
            if video_start > 0:
                delay_ms = int(video_start * 1000)
                filter_complex.append(f"{sound_input}adelay={delay_ms}|{delay_ms}[delayed]")
                sound_input = "[delayed]"
            
            # Trim to video duration
            filter_complex.append(f"{sound_input}atrim=0:{actual_duration}[final]")
            
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', sound_path,
                '-filter_complex', ';'.join(filter_complex),
                '-map', '0:v',
                '-map', '[final]',
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest',
                output_path
            ]
        else:
            # Mix with original audio
            filter_parts = []
            
            # Process new sound
            if sound_start > 0:
                filter_parts.append(f"[1:a]atrim=start={sound_start},asetpts=PTS-STARTPTS[snd]")
                new_sound = "[snd]"
            else:
                new_sound = "[1:a]"
            
            # Adjust new sound volume
            new_volume = volume * (1 - mix_ratio)
            filter_parts.append(f"{new_sound}volume={new_volume}[newsnd]")
            
            # Adjust original audio volume
            orig_volume = mix_ratio
            filter_parts.append(f"[0:a]volume={orig_volume}[origsnd]")
            
            # Add delay to new sound if needed
            if video_start > 0:
                delay_ms = int(video_start * 1000)
                filter_parts.append(f"[newsnd]adelay={delay_ms}|{delay_ms}[delayedsnd]")
                new_sound_final = "[delayedsnd]"
            else:
                new_sound_final = "[newsnd]"
            
            # Mix both audio streams
            filter_parts.append(f"[origsnd]{new_sound_final}amix=inputs=2:duration=first:dropout_transition=2[mixed]")
            
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', sound_path,
                '-filter_complex', ';'.join(filter_parts),
                '-map', '0:v',
                '-map', '[mixed]',
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest',
                output_path
            ]
        
        # Execute FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': 'FFmpeg error',
                'details': result.stderr[:500]
            })
        
        # Get output info
        output_info = get_video_info(output_path)
        output_size = os.path.getsize(output_path) / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'output': {
                'filename': output_filename,
                'folder': output_folder,
                'path': output_path,
                'download_url': f'/video-outputs/with_sound/{output_folder}/{output_filename}',
                'duration': round(output_info['duration'], 2),
                'size_mb': round(output_size, 2)
            },
            'settings': {
                'video_file': video_file,
                'sound_file': sound_file or 'downloaded',
                'sound_start': sound_start,
                'video_start': video_start,
                'volume': volume,
                'mix_mode': mix_mode,
                'mix_ratio': mix_ratio if mix_mode == 'mix' else None
            }
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Processing timeout (5 minutes)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/add-sound-batch', methods=['POST'])
def add_sound_to_batch():
    """
    Add sound to multiple videos in a folder
    
    Parameters:
    - source_folder: folder containing videos
    - sound_file: sound filename from library
    - sound_start: start time in sound (seconds)
    - volume: sound volume 0.0-2.0
    - mix_mode: 'replace' or 'mix'
    - mix_ratio: ratio when mixing
    """
    data = request.get_json() or {}
    
    source_folder = data.get('source_folder')
    sound_file = data.get('sound_file')
    sound_start = float(data.get('sound_start', 0))
    volume = float(data.get('volume', 1.0))
    mix_mode = data.get('mix_mode', 'mix')
    mix_ratio = float(data.get('mix_ratio', 0.3))
    
    if not source_folder:
        return jsonify({'success': False, 'error': 'source_folder is required'})
    if not sound_file:
        return jsonify({'success': False, 'error': 'sound_file is required'})
    
    # Find source folder
    folder_path = None
    folder_type = None
    
    for base_dir, ftype in [
        (CUTS_DIR, 'cuts'),
        (MONTAGES_DIR, 'montages'),
        (UNIQUIFIED_DIR, 'uniquified')
    ]:
        path = os.path.join(base_dir, source_folder)
        if os.path.exists(path):
            folder_path = path
            folder_type = ftype
            break
    
    if not folder_path:
        return jsonify({'success': False, 'error': f'Folder not found: {source_folder}'})
    
    # Check sound file
    sound_path = os.path.join(SOUNDS_DIR, sound_file)
    if not os.path.exists(sound_path):
        return jsonify({'success': False, 'error': f'Sound file not found: {sound_file}'})
    
    # Get video files
    video_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.mp4')])
    if not video_files:
        return jsonify({'success': False, 'error': 'No videos in folder'})
    
    # Create job
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    job_id = f"sound_batch_{source_folder[:15]}_{timestamp}"
    
    output_dir = os.path.join(OUTPUT_DIR, 'with_sound', job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize job
    with job_lock:
        active_jobs[job_id] = {
            'type': 'add_sound_batch',
            'status': 'processing',
            'progress': 0,
            'current': 0,
            'total': len(video_files),
            'source_folder': source_folder,
            'sound_file': sound_file,
            'results': [],
            'errors': [],
            'message': 'Starting...',
            'cancelled': False
        }
    
    # Process in background
    def process_batch():
        results = []
        errors = []
        
        sound_name = os.path.splitext(sound_file)[0][:10]
        
        for i, video_file in enumerate(video_files):
            # Check cancelled
            with job_lock:
                if active_jobs[job_id].get('cancelled'):
                    active_jobs[job_id]['status'] = 'cancelled'
                    return
            
            video_path = os.path.join(folder_path, video_file)
            output_filename = f"{os.path.splitext(video_file)[0]}_s{sound_name}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                # Build FFmpeg command (simplified for batch)
                if mix_mode == 'replace':
                    filter_complex = f"[1:a]atrim=start={sound_start},asetpts=PTS-STARTPTS,volume={volume}[snd]"
                    cmd = [
                        'ffmpeg', '-y', '-i', video_path, '-i', sound_path,
                        '-filter_complex', filter_complex,
                        '-map', '0:v', '-map', '[snd]',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                        '-shortest', output_path
                    ]
                else:
                    new_vol = volume * (1 - mix_ratio)
                    orig_vol = mix_ratio
                    filter_complex = f"[1:a]atrim=start={sound_start},asetpts=PTS-STARTPTS,volume={new_vol}[snd];[0:a]volume={orig_vol}[orig];[orig][snd]amix=inputs=2:duration=first[mix]"
                    cmd = [
                        'ffmpeg', '-y', '-i', video_path, '-i', sound_path,
                        '-filter_complex', filter_complex,
                        '-map', '0:v', '-map', '[mix]',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                        '-shortest', output_path
                    ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    results.append({
                        'filename': output_filename,
                        'size_mb': round(size_mb, 2),
                        'download_url': f'/video-outputs/with_sound/{job_id}/{output_filename}'
                    })
                else:
                    errors.append({'file': video_file, 'error': 'FFmpeg failed'})
                    
            except Exception as e:
                errors.append({'file': video_file, 'error': str(e)})
            
            # Update progress
            with job_lock:
                progress = ((i + 1) / len(video_files)) * 100
                active_jobs[job_id]['current'] = i + 1
                active_jobs[job_id]['progress'] = round(progress, 1)
                active_jobs[job_id]['results'] = results
                active_jobs[job_id]['errors'] = errors
                active_jobs[job_id]['message'] = f'Processing {i+1}/{len(video_files)}'
        
        # Complete
        with job_lock:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['output_folder'] = job_id
    
    thread = threading.Thread(target=process_batch)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'total_videos': len(video_files),
        'message': 'Processing started'
    })


@cutter_bp.route('/delete-sound/<filename>', methods=['DELETE'])
def delete_sound(filename):
    """Delete a sound from library"""
    filepath = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Sound not found'})
