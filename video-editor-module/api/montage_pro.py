"""
Подмодуль: Video Editor Pro - Unified Montage API
Объединяет функционал V1 и V2:
- Быстрый режим (Quick) - простая сборка шотов с аудио/аватаром
- Продвинутый режим (Advanced) - анализ, превью, обрезка, тайминги
- Интеграция уникализации
- Единое хранилище
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
import sys

logger = logging.getLogger(__name__)

montage_pro_bp = Blueprint('montage_pro', __name__)

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


# =====================================================
# ANALYZE SHOTS - Анализ загруженных видео
# =====================================================
@montage_pro_bp.route('/analyze-shots', methods=['POST'])
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
                file_size = os.path.getsize(filepath)
                
                analyzed_shots.append({
                    'index': idx,
                    'original_filename': shot.filename,
                    'duration': round(info['duration'], 2),
                    'width': info['width'],
                    'height': info['height'],
                    'fps': round(info['fps'], 2),
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'temp_path': filename,
                    'preview_url': f'/video-outputs/preview_{filename}'
                })
                
                logger.info(f"Analyzed shot {idx}: {shot.filename} - {info['duration']:.2f}s")
        
        return jsonify({
            'success': True,
            'shots': analyzed_shots,
            'total_duration': sum(s['duration'] for s in analyzed_shots),
            'total_count': len(analyzed_shots)
        })
    
    except Exception as e:
        logger.error(f"Error analyzing shots: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# CREATE - Единый endpoint создания монтажа
# =====================================================
@montage_pro_bp.route('/create', methods=['POST'])
def create_montage():
    """
    Единый endpoint создания монтажа (поддержка Quick и Advanced режимов)
    
    Quick Mode (FormData):
    - shots[]: видео файлы
    - audio: аудио файл (опционально)
    - avatar: видео аватара (опционально)
    - shuffle_count: количество вариантов
    - add_subtitles: добавлять субтитры
    
    Advanced Mode (JSON):
    {
        "mode": "advanced",
        "shots": [
            {
                "index": 0,
                "type": "hook",
                "start_time": 0,
                "end_time": 3.5,
                "random_offset": true,
                "temp_path": "temp_0_video.mp4"
            }
        ],
        "shuffle_count": 5,
        "enable_random_offsets": true,
        "target_duration": 30,
        "audio": {"file_path": "...", "source": "upload"},
        "avatar_overlay": {"file_path": "...", "position": "bottom-left"},
        "uniquify": {"enabled": true, "preset": "balanced"}
    }
    """
    try:
        # Определяем режим по Content-Type
        content_type = request.content_type or ''
        
        if 'application/json' in content_type:
            return _create_advanced_montage(request.get_json())
        else:
            return _create_quick_montage(request)
    
    except Exception as e:
        logger.error(f"Error creating montage: {e}")
        return jsonify({'error': str(e)}), 500


def _create_quick_montage(req):
    """Создание монтажа в быстром режиме (V1 логика)"""
    # Проверка наличия файлов
    if 'shots[]' not in req.files:
        return jsonify({'error': 'No video shots provided'}), 400
    
    shots = req.files.getlist('shots[]')
    
    if len(shots) < 3:
        return jsonify({'error': 'Minimum 3 shots required (hook, middle, cta)'}), 400
    
    # Параметры
    shuffle_count = int(req.form.get('shuffle_count', 1))
    add_subtitles = req.form.get('add_subtitles', 'false').lower() == 'true'
    
    # Сохранение загруженных шотов
    upload_folder = current_app.config['UPLOAD_FOLDER']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_folder = os.path.join(upload_folder, f'montage_pro_{timestamp}')
    os.makedirs(project_folder, exist_ok=True)
    
    shot_paths = []
    for idx, shot in enumerate(shots):
        if shot and allowed_file(shot.filename, ALLOWED_VIDEO_EXTENSIONS):
            filename = secure_filename(f'shot_{idx:02d}_{shot.filename}')
            filepath = os.path.join(project_folder, filename)
            shot.save(filepath)
            shot_paths.append(filepath)
            logger.info(f"Saved shot {idx}: {filename}")
    
    if len(shot_paths) < 3:
        return jsonify({'error': 'At least 3 valid video shots required'}), 400
    
    # Hook (первый) и CTA (последний) фиксируются
    hook_shot = shot_paths[0]
    cta_shot = shot_paths[-1]
    middle_shots = shot_paths[1:-1]
    
    # Сохранение аудио (если есть)
    audio_path = None
    if 'audio' in req.files:
        audio = req.files['audio']
        if audio and allowed_file(audio.filename, ALLOWED_AUDIO_EXTENSIONS):
            audio_filename = secure_filename(f'audio_{audio.filename}')
            audio_path = os.path.join(project_folder, audio_filename)
            audio.save(audio_path)
            logger.info(f"Saved audio: {audio_filename}")
    
    # Сохранение аватара (если есть)
    avatar_path = None
    if 'avatar' in req.files:
        avatar = req.files['avatar']
        if avatar and allowed_file(avatar.filename, ALLOWED_VIDEO_EXTENSIONS):
            avatar_filename = secure_filename(f'avatar_{avatar.filename}')
            avatar_path = os.path.join(project_folder, avatar_filename)
            avatar.save(avatar_path)
            logger.info(f"Saved avatar: {avatar_filename}")
    
    # Создание вариантов монтажа
    output_folder = current_app.config['OUTPUT_FOLDER']
    output_videos = []
    
    for variant in range(shuffle_count):
        # Случайное перемешивание средних шотов
        shuffled_middle = middle_shots.copy()
        random.shuffle(shuffled_middle)
        
        # Финальный порядок: Hook + shuffled middle + CTA
        final_order = [hook_shot] + shuffled_middle + [cta_shot]
        
        # Создание concat файла для ffmpeg
        concat_file = os.path.join(project_folder, f'concat_{variant}.txt')
        with open(concat_file, 'w') as f:
            for shot_path in final_order:
                f.write(f"file '{shot_path}'\n")
        
        # Монтаж видео через ffmpeg
        output_filename = f'montage_pro_{timestamp}_v{variant:02d}.mp4'
        output_path = os.path.join(output_folder, output_filename)
        
        # Базовая команда ffmpeg для конкатенации
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file
        ]
        
        # Добавление аудио если есть
        if audio_path:
            ffmpeg_cmd.extend(['-i', audio_path])
            ffmpeg_cmd.extend(['-c:v', 'copy', '-c:a', 'aac', '-shortest'])
        else:
            ffmpeg_cmd.extend(['-c', 'copy'])
        
        ffmpeg_cmd.append(output_path)
        
        logger.info(f"Running ffmpeg command for variant {variant}")
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully created montage variant {variant}")
            
            # Наложение аватара (если есть)
            if avatar_path:
                output_with_avatar = output_path.replace('.mp4', '_avatar.mp4')
                overlay_cmd = [
                    'ffmpeg', '-y', '-i', output_path, '-i', avatar_path,
                    '-filter_complex', '[1:v]colorkey=0x00FF00:0.1:0.1[ckout];[0:v][ckout]overlay=x=10:y=10[out]',
                    '-map', '[out]', '-map', '0:a?',
                    '-c:a', 'copy',
                    output_with_avatar
                ]
                
                overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                
                if overlay_result.returncode == 0:
                    # Удаляем промежуточный файл
                    os.remove(output_path)
                    output_path = output_with_avatar
                    output_filename = os.path.basename(output_with_avatar)
                    logger.info(f"Successfully added avatar to variant {variant}")
            
            # Получаем информацию о результате
            final_info = get_video_info(output_path)
            file_size = os.path.getsize(output_path)
            
            output_videos.append({
                'variant': variant,
                'filename': output_filename,
                'url': f'/video-outputs/{output_filename}',
                'duration': round(final_info['duration'], 2),
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'shots_count': len(final_order)
            })
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
    
    return jsonify({
        'success': True,
        'mode': 'quick',
        'project_id': timestamp,
        'variants_created': len(output_videos),
        'outputs': output_videos,
        'hook': os.path.basename(hook_shot),
        'cta': os.path.basename(cta_shot),
        'middle_shots_count': len(middle_shots)
    })


def _create_advanced_montage(data):
    """Создание монтажа в продвинутом режиме (V2 логика с обрезкой)"""
    if not data or 'shots' not in data:
        return jsonify({'error': 'No shots configuration provided'}), 400
    
    shots_config = data['shots']
    shuffle_count = int(data.get('shuffle_count', 1))
    target_duration = float(data.get('target_duration', 0))
    enable_random_offsets = data.get('enable_random_offsets', False)
    uniquify_config = data.get('uniquify', {})
    audio_config = data.get('audio', {})
    avatar_config = data.get('avatar_overlay', {})
    
    # Очистка старых файлов
    output_folder = current_app.config['OUTPUT_FOLDER']
    cleanup_old_files(output_folder)
    
    # Получаем файлы из temp папки
    upload_folder = current_app.config['UPLOAD_FOLDER']
    temp_folder = os.path.join(upload_folder, 'temp_analysis')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_folder = os.path.join(upload_folder, f'montage_pro_{timestamp}')
    os.makedirs(project_folder, exist_ok=True)
    
    # Обработка каждого шота с точной обрезкой
    processed_shots = []
    
    logger.info(f"=== ADVANCED MONTAGE: Processing {len(shots_config)} shots ===")
    
    for shot_cfg in shots_config:
        idx = shot_cfg['index']
        temp_path = shot_cfg.get('temp_path')
        start_time = float(shot_cfg.get('start_time', 0))
        end_time = float(shot_cfg.get('end_time')) if shot_cfg.get('end_time') is not None else None
        shot_type = shot_cfg.get('type', 'middle')
        random_offset = shot_cfg.get('random_offset', False) and enable_random_offsets
        
        if not temp_path:
            logger.warning(f"Shot {idx}: no temp_path, skipping")
            continue
        
        source_path = os.path.join(temp_folder, temp_path)
        if not os.path.exists(source_path):
            logger.warning(f"Shot {idx}: source not found at {source_path}")
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
                logger.info(f"Shot {idx}: applied random offset {offset:.2f}s")
        
        # FFmpeg команда для обрезки
        trim_cmd = [
            'ffmpeg', '-y', '-i', source_path,
            '-ss', str(start_time),
        ]
        
        if end_time is not None and end_time > start_time:
            duration = end_time - start_time
            trim_cmd.extend(['-t', str(duration)])
            logger.info(f"Shot {idx}: trimming {start_time:.2f}s -> {end_time:.2f}s (duration: {duration:.2f}s)")
        else:
            logger.info(f"Shot {idx}: no trimming applied")
        
        trim_cmd.extend([
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k',
            output_path
        ])
        
        result = subprocess.run(trim_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            trimmed_info = get_video_info(output_path)
            logger.info(f"Shot {idx}: trimmed successfully, duration: {trimmed_info['duration']:.2f}s")
            
            processed_shots.append({
                'index': idx,
                'type': shot_type,
                'path': output_path,
                'start_time': start_time,
                'end_time': end_time,
                'trimmed_duration': trimmed_info['duration']
            })
        else:
            logger.error(f"Shot {idx}: trim error: {result.stderr}")
    
    if len(processed_shots) < 3:
        return jsonify({'error': f'Failed to process minimum 3 shots, got {len(processed_shots)}'}), 500
    
    # Разделение на hook, middle, cta
    hook_shots = [s for s in processed_shots if s['type'] == 'hook']
    cta_shots = [s for s in processed_shots if s['type'] == 'cta']
    middle_shots = [s for s in processed_shots if s['type'] == 'middle']
    
    if not hook_shots or not cta_shots:
        return jsonify({'error': 'Hook and CTA shots are required'}), 400
    
    hook_shot = hook_shots[0]
    cta_shot = cta_shots[0]
    
    # Получаем аудио файл если указан
    audio_path = None
    if audio_config.get('file_path'):
        audio_path = audio_config['file_path']
        if audio_config.get('source') == 'generated':
            # Аудио из Voice модуля
            audio_path = os.path.join(output_folder, audio_path)
    
    # Получаем аватар файл если указан
    avatar_path = None
    avatar_position = 'bottom-left'
    if avatar_config.get('file_path'):
        avatar_path = avatar_config['file_path']
        avatar_position = avatar_config.get('position', 'bottom-left')
        if avatar_config.get('source') == 'heygen':
            avatar_path = os.path.join(output_folder, avatar_path)
    
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
        output_filename = f'montage_pro_{timestamp}_v{variant:02d}.mp4'
        output_path = os.path.join(output_folder, output_filename)
        
        # Базовая конкатенация
        concat_cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
        ]
        
        # Добавление аудио
        if audio_path and os.path.exists(audio_path):
            concat_cmd.extend(['-i', audio_path])
            concat_cmd.extend(['-c:v', 'copy', '-c:a', 'aac', '-shortest'])
        else:
            concat_cmd.extend(['-c', 'copy'])
        
        concat_cmd.append(output_path)
        
        logger.info(f"Creating montage variant {variant}")
        
        result = subprocess.run(concat_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Наложение аватара
            if avatar_path and os.path.exists(avatar_path):
                output_with_avatar = output_path.replace('.mp4', '_avatar.mp4')
                
                # Определяем позицию
                position_map = {
                    'bottom-left': 'x=10:y=H-h-10',
                    'bottom-right': 'x=W-w-10:y=H-h-10',
                    'top-left': 'x=10:y=10',
                    'top-right': 'x=W-w-10:y=10'
                }
                position = position_map.get(avatar_position, 'x=10:y=H-h-10')
                
                overlay_cmd = [
                    'ffmpeg', '-y', '-i', output_path, '-i', avatar_path,
                    '-filter_complex', f'[1:v]colorkey=0x00FF00:0.1:0.1[ckout];[0:v][ckout]overlay={position}[out]',
                    '-map', '[out]', '-map', '0:a?',
                    '-c:a', 'copy',
                    output_with_avatar
                ]
                
                overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                
                if overlay_result.returncode == 0:
                    os.remove(output_path)
                    output_path = output_with_avatar
                    output_filename = os.path.basename(output_with_avatar)
            
            # Уникализация
            if uniquify_config.get('enabled'):
                output_path, output_filename = _apply_uniquification(
                    output_path, 
                    uniquify_config.get('preset', 'balanced'),
                    output_folder
                )
            
            # Получаем итоговую длительность
            final_info = get_video_info(output_path)
            file_size = os.path.getsize(output_path)
            
            output_videos.append({
                'variant': variant,
                'filename': output_filename,
                'url': f'/video-outputs/{output_filename}',
                'duration': round(final_info['duration'], 2),
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'shots_count': len(final_order)
            })
            
            logger.info(f"Variant {variant} created: {final_info['duration']:.2f}s")
        else:
            logger.error(f"Error creating variant {variant}: {result.stderr}")
    
    # Очистка temp папки
    try:
        shutil.rmtree(temp_folder)
    except:
        pass
    
    return jsonify({
        'success': True,
        'mode': 'advanced',
        'project_id': timestamp,
        'variants_created': len(output_videos),
        'outputs': output_videos,
        'total_shots': len(processed_shots),
        'hook_count': len(hook_shots),
        'middle_count': len(middle_shots),
        'cta_count': len(cta_shots),
        'uniquified': uniquify_config.get('enabled', False)
    })


def _apply_uniquification(video_path, preset, output_folder):
    """Применить уникализацию к видео"""
    try:
        # Импортируем VideoUniquifier
        uniquifier_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'instagram-reels-bot', 'src', 'tools'
        )
        sys.path.insert(0, uniquifier_path)
        
        from video_uniquifier import VideoUniquifier
        
        uniquifier = VideoUniquifier()
        output_unique_path, info = uniquifier.uniquify(
            input_path=video_path,
            output_path=None,  # Автогенерация имени
            preset=preset
        )
        
        # Удаляем оригинал
        if output_unique_path != video_path:
            os.remove(video_path)
        
        # Перемещаем в output_folder если нужно
        if os.path.dirname(output_unique_path) != output_folder:
            final_path = os.path.join(output_folder, os.path.basename(output_unique_path))
            shutil.move(output_unique_path, final_path)
            output_unique_path = final_path
        
        return output_unique_path, os.path.basename(output_unique_path)
    
    except Exception as e:
        logger.error(f"Uniquification error: {e}")
        return video_path, os.path.basename(video_path)


# =====================================================
# STORAGE - Управление хранилищем
# =====================================================
@montage_pro_bp.route('/storage-info', methods=['GET'])
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


@montage_pro_bp.route('/cleanup', methods=['POST'])
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


@montage_pro_bp.route('/projects', methods=['GET'])
def list_projects():
    """Список всех проектов монтажа"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        projects = []
        
        # Получаем готовые видео из output_folder
        for filename in os.listdir(output_folder):
            if filename.startswith('montage_pro_') and filename.endswith('.mp4'):
                filepath = os.path.join(output_folder, filename)
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    # Извлекаем project_id из имени файла
                    parts = filename.replace('montage_pro_', '').split('_v')
                    project_id = parts[0] if parts else filename
                    
                    projects.append({
                        'id': project_id,
                        'filename': filename,
                        'url': f'/video-outputs/{filename}',
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'created': file_modified.isoformat()
                    })
        
        # Сортировка по дате
        projects.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'projects': projects,
            'total': len(projects)
        })
    
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return jsonify({'error': str(e)}), 500


@montage_pro_bp.route('/download/<filename>')
def download_video(filename):
    """Скачать готовое видео"""
    try:
        output_folder = current_app.config['OUTPUT_FOLDER']
        safe_filename = secure_filename(filename)
        
        return send_from_directory(output_folder, safe_filename, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return jsonify({'error': str(e)}), 500


@montage_pro_bp.route('/preview/<filename>', methods=['GET'])
def preview_temp_shot(filename):
    """Раздача временных файлов для превью шотов"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        temp_folder = os.path.join(upload_folder, 'temp_analysis')
        
        safe_filename = secure_filename(filename)
        filepath = os.path.join(temp_folder, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(temp_folder, safe_filename)
    
    except Exception as e:
        logger.error(f"Error serving preview: {e}")
        return jsonify({'error': str(e)}), 500
