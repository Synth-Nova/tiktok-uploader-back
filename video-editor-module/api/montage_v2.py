"""
Подмодуль 1: Smart Video Montage V2 (Расширенная версия)
Новые возможности:
- Анализ длительности каждого шота
- Точная обрезка по времени (start_time, end_time)
- Расчет итогового хронометража
- Случайное смещение по фрейму для уникализации
- Предпросмотр через Nginx /video-outputs/
- Система хранения с автоочисткой старых файлов
"""

from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
import random
import subprocess
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import logging
import shutil

logger = logging.getLogger(__name__)

montage_v2_bp = Blueprint('montage_v2', __name__)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'm4a', 'ogg'}

# Максимальный возраст файлов в outputs (7 дней)
MAX_FILE_AGE_DAYS = 7

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def get_video_info(video_path):
    """Получить полную информацию о видео через ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'format=duration:stream=width,height,r_frame_rate',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        duration = float(data['format']['duration'])
        stream = data['streams'][0]
        
        # Парсинг frame rate
        fps_parts = stream['r_frame_rate'].split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0
        
        return {
            'duration': duration,
            'width': stream['width'],
            'height': stream['height'],
            'fps': fps
        }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {'duration': 0, 'width': 0, 'height': 0, 'fps': 30.0}

def cleanup_old_files(output_folder, max_age_days=MAX_FILE_AGE_DAYS):
    """Удаление старых файлов из outputs"""
    try:
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        for filename in os.listdir(output_folder):
            filepath = os.path.join(output_folder, filename)
            if os.path.isfile(filepath):
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_modified < cutoff_time:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Deleted old file: {filename}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old files")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")
        return 0

@montage_v2_bp.route('/analyze-shots', methods=['POST'])
def analyze_shots():
    """
    Анализ загруженных шотов - возвращает длительность и мета-данные
    Параметры:
    - shots[]: видео файлы для анализа
    """
    try:
        if 'shots[]' not in request.files:
            return jsonify({'error': 'No video shots provided'}), 400
        
        shots = request.files.getlist('shots[]')
        
        # Временная папка для анализа
        upload_folder = current_app.config['UPLOAD_FOLDER']
        temp_folder = os.path.join(upload_folder, 'temp_analysis')
        os.makedirs(temp_folder, exist_ok=True)
        
        analyzed_shots = []
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        for idx, shot in enumerate(shots):
            if shot and allowed_file(shot.filename, ALLOWED_VIDEO_EXTENSIONS):
                filename = secure_filename(f'temp_{idx}_{shot.filename}')
                filepath = os.path.join(temp_folder, filename)
                shot.save(filepath)
                
                # Копируем в outputs для доступа через Nginx /video-outputs/
                output_preview_path = os.path.join(output_folder, f'preview_{filename}')
                shutil.copy2(filepath, output_preview_path)
                
                # Анализ видео
                info = get_video_info(filepath)
                
                analyzed_shots.append({
                    'index': idx,
                    'original_filename': shot.filename,
                    'duration': round(info['duration'], 2),
                    'width': info['width'],
                    'height': info['height'],
                    'fps': round(info['fps'], 2),
                    'temp_path': filename,
                    'preview_url': f'/video-outputs/preview_{filename}'
                })
                
                logger.info(f"Analyzed shot {idx}: {shot.filename} - {info['duration']:.2f}s")
        
        return jsonify({
            'success': True,
            'shots': analyzed_shots,
            'total_duration': sum(s['duration'] for s in analyzed_shots),
            'temp_folder': temp_folder
        })
    
    except Exception as e:
        logger.error(f"Error analyzing shots: {e}")
        return jsonify({'error': str(e)}), 500

@montage_v2_bp.route('/create-advanced', methods=['POST'])
def create_advanced_montage():
    """
    Создать расширенный монтаж с точным таймингом
    
    Параметры JSON:
    {
        "shots": [
            {
                "index": 0,
                "type": "hook",
                "start_time": 0,
                "end_time": 3.5,
                "random_offset": true
            },
            {
                "index": 1,
                "type": "middle",
                "start_time": 1.2,
                "end_time": 5.8,
                "random_offset": true
            },
            ...
        ],
        "audio_file": "optional",
        "target_duration": 30,
        "shuffle_count": 5,
        "enable_random_offsets": true
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'shots' not in data:
            return jsonify({'error': 'No shots configuration provided'}), 400
        
        shots_config = data['shots']
        shuffle_count = int(data.get('shuffle_count', 1))
        target_duration = float(data.get('target_duration', 0))
        enable_random_offsets = data.get('enable_random_offsets', False)
        
        # Очистка старых файлов
        output_folder = current_app.config['OUTPUT_FOLDER']
        cleanup_old_files(output_folder)
        
        # Получаем файлы из temp папки
        upload_folder = current_app.config['UPLOAD_FOLDER']
        temp_folder = os.path.join(upload_folder, 'temp_analysis')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_folder = os.path.join(upload_folder, f'montage_v2_{timestamp}')
        os.makedirs(project_folder, exist_ok=True)
        
        # Обработка каждого шота с точной обрезкой
        processed_shots = []
        
        for shot_cfg in shots_config:
            idx = shot_cfg['index']
            temp_path = shot_cfg.get('temp_path')
            start_time = shot_cfg.get('start_time', 0)
            end_time = shot_cfg.get('end_time')
            shot_type = shot_cfg.get('type', 'middle')
            random_offset = shot_cfg.get('random_offset', False) and enable_random_offsets
            
            if not temp_path:
                continue
            
            source_path = os.path.join(temp_folder, temp_path)
            if not os.path.exists(source_path):
                continue
            
            # Обрезка видео по времени
            output_filename = f'shot_{idx:02d}_{shot_type}.mp4'
            output_path = os.path.join(project_folder, output_filename)
            
            # Случайное смещение для уникализации
            if random_offset and end_time:
                video_info = get_video_info(source_path)
                max_offset = min(1.0, (video_info['duration'] - (end_time - start_time)) / 2)
                if max_offset > 0:
                    offset = random.uniform(0, max_offset)
                    start_time += offset
                    end_time += offset
                    logger.info(f"Applied random offset {offset:.2f}s to shot {idx}")
            
            # FFmpeg команда для обрезки
            trim_cmd = [
                'ffmpeg', '-i', source_path,
                '-ss', str(start_time),
            ]
            
            if end_time:
                duration = end_time - start_time
                trim_cmd.extend(['-t', str(duration)])
            
            trim_cmd.extend([
                '-c:v', 'libx264', '-preset', 'fast',
                '-c:a', 'aac', '-b:a', '128k',
                output_path
            ])
            
            logger.info(f"Trimming shot {idx}: {start_time}s to {end_time}s")
            
            result = subprocess.run(trim_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                processed_shots.append({
                    'index': idx,
                    'type': shot_type,
                    'path': output_path,
                    'start_time': start_time,
                    'end_time': end_time
                })
            else:
                logger.error(f"Error trimming shot {idx}: {result.stderr}")
        
        if len(processed_shots) < 3:
            return jsonify({'error': 'Failed to process minimum 3 shots'}), 500
        
        # Разделение на hook, middle, cta
        hook_shots = [s for s in processed_shots if s['type'] == 'hook']
        cta_shots = [s for s in processed_shots if s['type'] == 'cta']
        middle_shots = [s for s in processed_shots if s['type'] == 'middle']
        
        if not hook_shots or not cta_shots:
            return jsonify({'error': 'Hook and CTA shots are required'}), 400
        
        hook_shot = hook_shots[0]
        cta_shot = cta_shots[0]
        
        # Создание вариантов монтажа
        output_videos = []
        
        for variant in range(shuffle_count):
            # Случайное перемешивание middle шотов
            shuffled_middle = middle_shots.copy()
            random.shuffle(shuffled_middle)
            
            # Финальный порядок
            final_order = [hook_shot] + shuffled_middle + [cta_shot]
            
            # Создание concat файла
            concat_file = os.path.join(project_folder, f'concat_{variant}.txt')
            with open(concat_file, 'w') as f:
                for shot in final_order:
                    f.write(f"file '{shot['path']}'\n")
            
            # Монтаж
            output_filename = f'montage_v2_{timestamp}_v{variant:02d}.mp4'
            output_path = os.path.join(output_folder, output_filename)
            
            concat_cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]
            
            logger.info(f"Creating montage variant {variant}")
            
            result = subprocess.run(concat_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Получаем итоговую длительность
                final_info = get_video_info(output_path)
                
                output_videos.append({
                    'variant': variant,
                    'filename': output_filename,
                    'url': f'/video-outputs/{output_filename}',
                    'duration': round(final_info['duration'], 2),
                    'size': os.path.getsize(output_path),
                    'shots_count': len(final_order)
                })
                
                logger.info(f"Successfully created variant {variant}: {final_info['duration']:.2f}s")
            else:
                logger.error(f"Error creating variant {variant}: {result.stderr}")
        
        # Очистка temp папки
        try:
            shutil.rmtree(temp_folder)
        except:
            pass
        
        return jsonify({
            'success': True,
            'project_id': timestamp,
            'variants_created': len(output_videos),
            'outputs': output_videos,
            'total_shots': len(processed_shots),
            'hook_count': len(hook_shots),
            'middle_count': len(middle_shots),
            'cta_count': len(cta_shots)
        })
    
    except Exception as e:
        logger.error(f"Error creating advanced montage: {e}")
        return jsonify({'error': str(e)}), 500

@montage_v2_bp.route('/storage-info', methods=['GET'])
def get_storage_info():
    """Получить информацию о хранилище"""
    try:
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        # Подсчет файлов и размера
        total_size = 0
        file_count = 0
        files = []
        
        for filename in os.listdir(output_folder):
            filepath = os.path.join(output_folder, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                total_size += file_size
                file_count += 1
                
                files.append({
                    'filename': filename,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'modified': file_modified.isoformat(),
                    'url': f'/video-outputs/{filename}'
                })
        
        # Сортировка по дате (новые первыми)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        # Получаем место на диске
        statvfs = os.statvfs(output_folder)
        disk_free = statvfs.f_bavail * statvfs.f_frsize
        disk_total = statvfs.f_blocks * statvfs.f_frsize
        
        return jsonify({
            'success': True,
            'storage': {
                'total_files': file_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'disk_free_gb': round(disk_free / (1024 * 1024 * 1024), 2),
                'disk_total_gb': round(disk_total / (1024 * 1024 * 1024), 2),
                'disk_usage_percent': round((1 - disk_free / disk_total) * 100, 2)
            },
            'files': files
        })
    
    except Exception as e:
        logger.error(f"Error getting storage info: {e}")
        return jsonify({'error': str(e)}), 500

@montage_v2_bp.route('/cleanup', methods=['POST'])
def manual_cleanup():
    """Ручная очистка старых файлов"""
    try:
        data = request.get_json() or {}
        max_age_days = int(data.get('max_age_days', MAX_FILE_AGE_DAYS))
        
        output_folder = current_app.config['OUTPUT_FOLDER']
        deleted_count = cleanup_old_files(output_folder, max_age_days)
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} files older than {max_age_days} days'
        })
    
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        return jsonify({'error': str(e)}), 500

@montage_v2_bp.route('/preview/<filename>', methods=['GET'])
def preview_temp_shot(filename):
    """
    Раздача временных файлов для превью шотов
    """
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        temp_folder = os.path.join(upload_folder, 'temp_analysis')
        
        # Безопасность: проверяем, что файл находится в нужной папке
        safe_filename = secure_filename(filename)
        filepath = os.path.join(temp_folder, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(temp_folder, safe_filename)
    
    except Exception as e:
        logger.error(f"Error serving preview: {e}")
        return jsonify({'error': str(e)}), 500
