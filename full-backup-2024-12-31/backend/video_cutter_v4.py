"""
Video Cutter V4 API
Full-featured video cutting with folder management, montage creation, and S3 upload
"""

import os
import re
import json
import shutil
import subprocess
import threading
import random
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
CUTS_DIR = os.path.join(OUTPUT_DIR, 'cuts')
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, 'archive')
MONTAGES_DIR = os.path.join(OUTPUT_DIR, 'montages')

# S3 Configuration
S3_PUBLIC_URL = os.environ.get('S3_PUBLIC_URL', 'https://video-editor-files.s3.ru-3.storage.selcloud.ru')

# Ensure directories exist
for d in [UPLOAD_DIR, OUTPUT_DIR, CUTS_DIR, ARCHIVE_DIR, MONTAGES_DIR]:
    os.makedirs(d, exist_ok=True)

# Active jobs storage
active_jobs = {}
job_lock = threading.Lock()


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
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0


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


def cut_video_worker(job_id, source_path, folder_path, segment_duration, upload_to_s3_flag):
    """Background worker for video cutting"""
    global active_jobs
    
    try:
        # Get video duration
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
            # Check if cancelled
            with job_lock:
                if active_jobs[job_id].get('cancelled'):
                    active_jobs[job_id]['status'] = 'cancelled'
                    active_jobs[job_id]['message'] = f'Отменено. Создано {len(cuts)} кусков'
                    active_jobs[job_id]['cuts'] = cuts
                    return
            
            start_time = i * segment_duration
            output_filename = f"{base_name}_cut_{i+1:03d}.mp4"
            output_path = os.path.join(folder_path, output_filename)
            
            # FFmpeg command (copy codec for speed)
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
                
                # Get file size
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                
                cut_info = {
                    'index': i,
                    'filename': output_filename,
                    'size_mb': round(size_mb, 2),
                    'start_time': start_time,
                    'start_time_formatted': format_time(start_time),
                    'download_url': f'/video-outputs/cuts/{job_id}/{output_filename}'
                }
                
                # Upload to S3
                if upload_to_s3_flag:
                    s3_key = f"outputs/cuts/{job_id}/{output_filename}"
                    s3_url = upload_to_s3(output_path, s3_key)
                    if s3_url:
                        cut_info['s3_url'] = s3_url
                
                cuts.append(cut_info)
                
                # Update progress
                with job_lock:
                    progress = ((i + 1) / total_cuts) * 100
                    active_jobs[job_id]['current_cut'] = i + 1
                    active_jobs[job_id]['progress'] = round(progress, 1)
                    active_jobs[job_id]['message'] = f'Кусок {i+1} из {total_cuts}'
                    active_jobs[job_id]['cuts'] = cuts
                    
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error for cut {i+1}: {e}")
                continue
        
        # Complete
        with job_lock:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['cuts'] = cuts
            active_jobs[job_id]['message'] = f'Готово! Создано {len(cuts)} кусков'
            
    except Exception as e:
        with job_lock:
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['error'] = str(e)


# ====== API ENDPOINTS ======

@cutter_bp.route('/list-videos', methods=['GET'])
def list_videos():
    """List available videos for cutting"""
    videos = []
    
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            # Skip directories and non-video files
            if os.path.isdir(filepath):
                continue
            if not filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                continue
            
            try:
                duration = get_video_duration(filepath)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # Get video dimensions
                cmd = [
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height',
                    '-of', 'json', filepath
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                data = json.loads(result.stdout)
                streams = data.get('streams', [{}])
                width = streams[0].get('width', 0) if streams else 0
                height = streams[0].get('height', 0) if streams else 0
                
                videos.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size_mb': round(size_mb, 1),
                    'duration': duration,
                    'duration_formatted': format_time(duration),
                    'width': width,
                    'height': height,
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
    
    videos.sort(key=lambda x: x['created'], reverse=True)
    
    return jsonify({
        'success': True,
        'videos': videos,
        'total': len(videos)
    })


@cutter_bp.route('/cut', methods=['POST'])
def start_cut():
    """Start video cutting job"""
    data = request.get_json()
    
    filename = data.get('filename')
    segment_duration = data.get('segment_duration', 15)
    folder_name = data.get('folder_name', '')
    upload_to_s3_flag = data.get('upload_to_s3', True)
    
    if not filename:
        return jsonify({'success': False, 'error': 'filename required'})
    
    # Find source file
    source_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(source_path):
        return jsonify({'success': False, 'error': 'Video file not found'})
    
    # Create job ID and folder
    if folder_name:
        job_id = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(filename)[0][:20]
        job_id = f"cuts_{base_name}_{segment_duration}s"
    
    folder_path = os.path.join(CUTS_DIR, job_id)
    os.makedirs(folder_path, exist_ok=True)
    
    # Initialize job
    with job_lock:
        active_jobs[job_id] = {
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
    
    # Start background worker
    thread = threading.Thread(
        target=cut_video_worker,
        args=(job_id, source_path, folder_path, segment_duration, upload_to_s3_flag)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Cutting started'
    })


@cutter_bp.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and progress"""
    with job_lock:
        if job_id not in active_jobs:
            return jsonify({'success': False, 'error': 'Job not found'})
        
        job = active_jobs[job_id].copy()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        **job
    })


@cutter_bp.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel running job"""
    with job_lock:
        if job_id not in active_jobs:
            return jsonify({'success': False, 'error': 'Job not found'})
        
        if active_jobs[job_id]['status'] not in ['pending', 'processing']:
            return jsonify({'success': False, 'error': 'Job is not running'})
        
        active_jobs[job_id]['cancelled'] = True
    
    return jsonify({'success': True, 'message': 'Cancellation requested'})


@cutter_bp.route('/folders', methods=['GET'])
def list_folders():
    """List all cut folders (active and archived)"""
    folders = []
    
    # Active folders
    if os.path.exists(CUTS_DIR):
        for name in os.listdir(CUTS_DIR):
            path = os.path.join(CUTS_DIR, name)
            if os.path.isdir(path):
                files = [f for f in os.listdir(path) if f.endswith('.mp4')]
                total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files) / (1024*1024)
                folders.append({
                    'name': name,
                    'path': path,
                    'files_count': len(files),
                    'total_size_mb': round(total_size, 1),
                    'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
                    'archived': False
                })
    
    # Archived folders
    if os.path.exists(ARCHIVE_DIR):
        for name in os.listdir(ARCHIVE_DIR):
            path = os.path.join(ARCHIVE_DIR, name)
            if os.path.isdir(path):
                files = [f for f in os.listdir(path) if f.endswith('.mp4')]
                total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files) / (1024*1024)
                folders.append({
                    'name': name,
                    'path': path,
                    'files_count': len(files),
                    'total_size_mb': round(total_size, 1),
                    'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
                    'archived': True
                })
    
    folders.sort(key=lambda x: x['created'], reverse=True)
    
    return jsonify({
        'success': True,
        'folders': folders,
        'total': len(folders)
    })


@cutter_bp.route('/folder-files/<folder_name>', methods=['GET'])
def get_folder_files(folder_name):
    """Get list of files in a folder"""
    try:
        # Check both cuts and archive directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        files = []
        for f in sorted(os.listdir(folder_path)):
            if f.endswith('.mp4'):
                file_path = os.path.join(folder_path, f)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                files.append({
                    'filename': f,
                    'size_mb': round(size_mb, 2),
                    'download_url': f'/video-outputs/cuts/{folder_name}/{f}',
                    's3_url': f'{S3_PUBLIC_URL}/outputs/cuts/{folder_name}/{f}' if S3_PUBLIC_URL else None
                })
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'files': files,
            'total': len(files)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/rename-folder', methods=['POST'])
def rename_folder():
    """Rename a folder"""
    try:
        data = request.get_json()
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        
        if not old_name or not new_name:
            return jsonify({'success': False, 'error': 'old_name and new_name required'})
        
        # Sanitize new name
        new_name = re.sub(r'[^a-zA-Z0-9_-]', '_', new_name)
        
        # Check both directories
        old_path = os.path.join(CUTS_DIR, old_name)
        is_archived = False
        if not os.path.exists(old_path):
            old_path = os.path.join(ARCHIVE_DIR, old_name)
            is_archived = True
        
        if not os.path.exists(old_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        base_dir = ARCHIVE_DIR if is_archived else CUTS_DIR
        new_path = os.path.join(base_dir, new_name)
        
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': 'Folder with this name already exists'})
        
        os.rename(old_path, new_path)
        
        return jsonify({
            'success': True,
            'old_name': old_name,
            'new_name': new_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/archive-folder/<folder_name>', methods=['POST'])
def archive_folder(folder_name):
    """Move folder to archive"""
    try:
        src_path = os.path.join(CUTS_DIR, folder_name)
        dst_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(src_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        if os.path.exists(dst_path):
            return jsonify({'success': False, 'error': 'Folder already in archive'})
        
        shutil.move(src_path, dst_path)
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'archived': True
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/unarchive-folder/<folder_name>', methods=['POST'])
def unarchive_folder(folder_name):
    """Restore folder from archive"""
    try:
        src_path = os.path.join(ARCHIVE_DIR, folder_name)
        dst_path = os.path.join(CUTS_DIR, folder_name)
        
        if not os.path.exists(src_path):
            return jsonify({'success': False, 'error': 'Folder not found in archive'})
        
        if os.path.exists(dst_path):
            return jsonify({'success': False, 'error': 'Folder already exists in cuts'})
        
        shutil.move(src_path, dst_path)
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'archived': False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/delete-folder/<folder_name>', methods=['DELETE'])
def delete_folder(folder_name):
    """Delete a folder and all its files"""
    try:
        # Check both directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        shutil.rmtree(folder_path)
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'deleted': True
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/delete-files', methods=['POST'])
def delete_files():
    """Delete specific files from folder"""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')
        filenames = data.get('filenames', [])
        
        if not folder_name or not filenames:
            return jsonify({'success': False, 'error': 'folder_name and filenames required'})
        
        # Check both directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        deleted = []
        errors = []
        
        for filename in filenames:
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted.append(filename)
                except Exception as e:
                    errors.append({'filename': filename, 'error': str(e)})
            else:
                errors.append({'filename': filename, 'error': 'File not found'})
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'deleted_count': len(deleted),
            'errors': errors if errors else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/s3-urls/<folder_name>', methods=['GET'])
def get_s3_urls(folder_name):
    """Get S3 URLs for all files in folder"""
    try:
        # Check both directories
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        urls = []
        for f in sorted(os.listdir(folder_path)):
            if f.endswith('.mp4'):
                urls.append({
                    'filename': f,
                    's3_url': f'{S3_PUBLIC_URL}/outputs/cuts/{folder_name}/{f}' if S3_PUBLIC_URL else None,
                    'download_url': f'/video-outputs/cuts/{folder_name}/{f}'
                })
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'urls': urls,
            'total': len(urls)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ====== MONTAGE ENDPOINTS ======

@cutter_bp.route('/combine-montage', methods=['POST'])
def combine_montage():
    """Combine cuts into a montage video"""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')
        middle_count = data.get('middle_count', 10)
        variants = data.get('variants', 1)
        shuffle = data.get('shuffle', True)
        hook_url = data.get('hook_url')
        cta_url = data.get('cta_url')
        
        if not folder_name:
            return jsonify({'success': False, 'error': 'folder_name required'})
        
        # Find folder
        folder_path = os.path.join(CUTS_DIR, folder_name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(ARCHIVE_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'})
        
        # Get all video files
        all_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])
        
        if len(all_files) < 1:
            return jsonify({'success': False, 'error': 'No video files in folder'})
        
        # Clamp middle_count
        middle_count = min(middle_count, len(all_files))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results = []
        
        for v in range(variants):
            # Select and optionally shuffle files
            selected_files = all_files.copy()
            if shuffle:
                random.shuffle(selected_files)
            selected_files = selected_files[:middle_count]
            
            # Create concat file
            concat_file = os.path.join(MONTAGES_DIR, f'concat_{folder_name}_{timestamp}_v{v:02d}.txt')
            with open(concat_file, 'w') as f:
                for filename in selected_files:
                    file_path = os.path.join(folder_path, filename)
                    f.write(f"file '{file_path}'\n")
            
            # Output file
            output_filename = f"combined_{folder_name}_{timestamp}_v{v:02d}.mp4"
            output_path = os.path.join(MONTAGES_DIR, output_filename)
            
            # FFmpeg concat
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                
                # Get output info
                duration = get_video_duration(output_path)
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                
                result = {
                    'variant': v,
                    'filename': output_filename,
                    'download_url': f'/video-outputs/montages/{output_filename}',
                    'duration': round(duration, 2),
                    'size_mb': round(size_mb, 2),
                    'shots_used': len(selected_files)
                }
                
                # Upload to S3
                s3_key = f"outputs/montages/{output_filename}"
                s3_url = upload_to_s3(output_path, s3_key)
                if s3_url:
                    result['s3_url'] = s3_url
                
                results.append(result)
                
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error for variant {v}: {e}")
                continue
            finally:
                # Cleanup concat file
                if os.path.exists(concat_file):
                    os.remove(concat_file)
        
        return jsonify({
            'success': True,
            'folder': folder_name,
            'variants': results,
            'total_variants': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cutter_bp.route('/send-to-uniquify', methods=['POST'])
def send_to_uniquify():
    """Send video to uniquification"""
    try:
        data = request.get_json()
        video_path = data.get('video_path')
        video_filename = data.get('video_filename')
        effects = data.get('effects', ['speed', 'mirror', 'color'])
        
        # Find video
        if video_filename:
            # Check in montages first
            video_path = os.path.join(MONTAGES_DIR, video_filename)
            if not os.path.exists(video_path):
                # Check in outputs
                video_path = os.path.join(OUTPUT_DIR, video_filename)
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video file not found'})
        
        try:
            from api.uniquifier_api import uniquify_video
            result = uniquify_video(video_path, effects)
            return jsonify(result)
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Uniquifier not available',
                'video_path': video_path
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
