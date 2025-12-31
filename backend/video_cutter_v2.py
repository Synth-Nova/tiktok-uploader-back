"""
Video Cutter V2 - с прогресс-баром и управлением папками
"""
import os
import json
import subprocess
import shutil
import zipfile
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

cutter_bp = Blueprint('cutter', __name__)

# Directories
UPLOADS_DIR = '/opt/video-editor/uploads'
OUTPUTS_DIR = '/opt/video-editor/outputs'
CUTS_DIR = os.path.join(OUTPUTS_DIR, 'cuts')

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CUTS_DIR, exist_ok=True)

# Job tracking for progress
active_jobs = {}  # job_id -> {status, progress, total_cuts, current_cut, message, result}

def get_video_info(filepath):
    """Get video duration, fps, resolution using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration',
            '-show_entries', 'format=duration',
            '-of', 'json',
            filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        
        # Get duration from format or stream
        duration = 0
        if 'format' in data and 'duration' in data['format']:
            duration = float(data['format']['duration'])
        elif 'streams' in data and len(data['streams']) > 0:
            if 'duration' in data['streams'][0]:
                duration = float(data['streams'][0]['duration'])
        
        # Get resolution
        width = height = 0
        fps = 30.0
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            width = stream.get('width', 0)
            height = stream.get('height', 0)
            if 'r_frame_rate' in stream:
                fps_parts = stream['r_frame_rate'].split('/')
                if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                    fps = float(fps_parts[0]) / float(fps_parts[1])
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'fps': round(fps, 2)
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {'duration': 0, 'width': 0, 'height': 0, 'fps': 30.0}

def format_duration(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def cut_video_thread(job_id, filepath, segment_duration, output_folder, upload_to_s3=True):
    """Background thread for cutting video with progress tracking"""
    global active_jobs
    
    try:
        active_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'total_cuts': 0,
            'current_cut': 0,
            'message': 'Анализ видео...',
            'result': None
        }
        
        # Get video info
        video_info = get_video_info(filepath)
        duration = video_info['duration']
        
        if duration == 0:
            active_jobs[job_id] = {
                'status': 'error',
                'error': 'Не удалось определить длительность видео'
            }
            return
        
        total_cuts = int(duration // segment_duration)
        if duration % segment_duration > 1:  # Add partial segment if > 1 sec
            total_cuts += 1
        
        active_jobs[job_id]['total_cuts'] = total_cuts
        active_jobs[job_id]['message'] = f'Нарезка на {total_cuts} кусков...'
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        cuts = []
        source_name = os.path.splitext(os.path.basename(filepath))[0]
        
        for i in range(total_cuts):
            start_time = i * segment_duration
            
            # Update progress
            active_jobs[job_id]['current_cut'] = i + 1
            active_jobs[job_id]['progress'] = ((i + 1) / total_cuts) * 100
            active_jobs[job_id]['message'] = f'Кусок {i + 1} из {total_cuts}'
            
            output_filename = f"{source_name}_cut_{i+1:03d}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            # FFmpeg command for fast cutting without re-encoding
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', filepath,
                '-t', str(segment_duration),
                '-c', 'copy',  # Copy without re-encoding
                '-avoid_negative_ts', 'make_zero',
                output_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, timeout=120)
                
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    
                    cut_info = {
                        'index': i,
                        'filename': output_filename,
                        'size_mb': round(file_size, 2),
                        'start_time': start_time,
                        'start_time_formatted': format_duration(start_time),
                        'download_url': f'/video-outputs/cuts/{job_id}/{output_filename}'
                    }
                    
                    # Upload to S3 if enabled
                    if upload_to_s3:
                        try:
                            from api.s3_storage import get_s3_storage
                            s3 = get_s3_storage()
                            if s3:
                                s3_key = f"cuts/{job_id}/{output_filename}"
                                result = s3.upload_file(output_path, s3_key)
                                if result.get('success'):
                                    cut_info['s3_url'] = result.get('url')
                        except Exception as e:
                            print(f"S3 upload error: {e}")
                    
                    cuts.append(cut_info)
            except subprocess.TimeoutExpired:
                print(f"Timeout cutting segment {i + 1}")
            except Exception as e:
                print(f"Error cutting segment {i + 1}: {e}")
        
        # Complete
        active_jobs[job_id] = {
            'status': 'completed',
            'progress': 100,
            'total_cuts': total_cuts,
            'current_cut': total_cuts,
            'message': 'Готово!',
            'success': True,
            'job_id': job_id,
            'source_file': os.path.basename(filepath),
            'total_cuts': len(cuts),
            'output_folder': output_folder,
            'cuts': cuts
        }
        
    except Exception as e:
        active_jobs[job_id] = {
            'status': 'error',
            'error': str(e)
        }

@cutter_bp.route('/api/cutter/list-videos', methods=['GET'])
def list_videos():
    """List all uploaded videos available for cutting"""
    try:
        videos = []
        
        if os.path.exists(UPLOADS_DIR):
            for filename in os.listdir(UPLOADS_DIR):
                filepath = os.path.join(UPLOADS_DIR, filename)
                
                if os.path.isfile(filepath):
                    # Get video info
                    video_info = get_video_info(filepath)
                    file_stat = os.stat(filepath)
                    
                    videos.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size_mb': round(file_stat.st_size / (1024 * 1024), 1),
                        'duration': video_info['duration'],
                        'duration_formatted': format_duration(video_info['duration']),
                        'width': video_info['width'],
                        'height': video_info['height'],
                        'fps': video_info['fps'],
                        'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                    })
        
        # Sort by creation date, newest first
        videos.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'total': len(videos),
            'videos': videos
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cutter_bp.route('/api/cutter/cut', methods=['POST'])
def cut_video():
    """Start video cutting job"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        segment_duration = data.get('segment_duration', 15)
        upload_to_s3 = data.get('upload_to_s3', True)
        folder_name = data.get('folder_name')
        
        if not filename:
            return jsonify({'success': False, 'error': 'filename is required'}), 400
        
        filepath = os.path.join(UPLOADS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Generate job ID / folder name
        if folder_name:
            job_id = folder_name
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            source_name = os.path.splitext(filename)[0][:20]
            job_id = f"cuts_{source_name}_{segment_duration}s_{timestamp}"
        
        output_folder = os.path.join(CUTS_DIR, job_id)
        
        # Start cutting in background thread
        thread = threading.Thread(
            target=cut_video_thread,
            args=(job_id, filepath, segment_duration, output_folder, upload_to_s3)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Нарезка запущена'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cutter_bp.route('/api/cutter/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job progress/result"""
    if job_id in active_jobs:
        return jsonify(active_jobs[job_id])
    
    # Check if job folder exists (completed job that was restarted)
    job_folder = os.path.join(CUTS_DIR, job_id)
    if os.path.exists(job_folder):
        files = [f for f in os.listdir(job_folder) if f.endswith('.mp4')]
        return jsonify({
            'status': 'completed',
            'progress': 100,
            'total_cuts': len(files),
            'job_id': job_id,
            'output_folder': job_folder,
            'message': 'Загружено ранее'
        })
    
    return jsonify({'success': False, 'error': 'Job not found'}), 404

@cutter_bp.route('/api/cutter/jobs', methods=['GET'])
def list_jobs():
    """List all cutting jobs"""
    jobs = []
    
    # Active jobs
    for job_id, job_data in active_jobs.items():
        jobs.append({
            'job_id': job_id,
            **job_data
        })
    
    return jsonify({
        'success': True,
        'jobs': jobs
    })

@cutter_bp.route('/api/cutter/folders', methods=['GET'])
def list_folders():
    """List all saved cut folders"""
    try:
        folders = []
        
        if os.path.exists(CUTS_DIR):
            for folder_name in os.listdir(CUTS_DIR):
                folder_path = os.path.join(CUTS_DIR, folder_name)
                
                if os.path.isdir(folder_path):
                    files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
                    total_size = sum(
                        os.path.getsize(os.path.join(folder_path, f)) 
                        for f in files
                    )
                    
                    folder_stat = os.stat(folder_path)
                    
                    folders.append({
                        'name': folder_name,
                        'path': folder_path,
                        'files_count': len(files),
                        'total_size_mb': round(total_size / (1024 * 1024), 1),
                        'created': datetime.fromtimestamp(folder_stat.st_ctime).isoformat()
                    })
        
        # Sort by creation date, newest first
        folders.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'total': len(folders),
            'folders': folders
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cutter_bp.route('/api/cutter/download-folder/<folder_name>', methods=['GET'])
def download_folder_zip(folder_name):
    """Create and return ZIP archive of folder"""
    try:
        folder_path = os.path.join(CUTS_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'}), 404
        
        # Create ZIP file
        zip_filename = f"{folder_name}.zip"
        zip_path = os.path.join(OUTPUTS_DIR, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    zipf.write(file_path, file)
        
        # Upload ZIP to S3
        try:
            from api.s3_storage import get_s3_storage
            s3 = get_s3_storage()
            if s3:
                s3_key = f"archives/{zip_filename}"
                result = s3.upload_file(zip_path, s3_key)
                if result.get('success'):
                    return jsonify({
                        'success': True,
                        'zip_url': result.get('url'),
                        'filename': zip_filename
                    })
        except Exception as e:
            print(f"S3 upload error: {e}")
        
        # Fallback to local URL
        return jsonify({
            'success': True,
            'zip_url': f'/video-outputs/{zip_filename}',
            'filename': zip_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cutter_bp.route('/api/cutter/delete-folder/<folder_name>', methods=['DELETE'])
def delete_folder(folder_name):
    """Delete a cuts folder"""
    try:
        folder_path = os.path.join(CUTS_DIR, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'}), 404
        
        shutil.rmtree(folder_path)
        
        # Remove from active jobs if present
        if folder_name in active_jobs:
            del active_jobs[folder_name]
        
        return jsonify({
            'success': True,
            'message': f'Folder {folder_name} deleted'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cutter_bp.route('/api/cutter/delete-job/<job_name>', methods=['DELETE'])
def delete_job(job_name):
    """Delete a job (alias for delete-folder)"""
    return delete_folder(job_name)
