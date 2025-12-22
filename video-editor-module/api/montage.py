"""
Подмодуль 1: Smart Video Montage
Функционал:
- Загрузка 8+ видео шотов
- Фиксация Hook (первый) и CTA (последний)
- Случайное перемешивание средних шотов
- Наложение аудио дорожки
- Генерация субтитров
- Опциональный аватар с прозрачным фоном
"""

from flask import Blueprint, request, jsonify, current_app, send_file
import os
import random
import subprocess
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

montage_bp = Blueprint('montage', __name__)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'm4a', 'ogg'}

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def get_video_duration(video_path):
    """Получить длительность видео через ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return 0

@montage_bp.route('/create', methods=['POST'])
def create_montage():
    """
    Создать монтаж видео из шотов
    
    Ожидаемые поля:
    - shots: список видео файлов (минимум 3: hook, середина, cta)
    - audio: аудио файл (опционально)
    - avatar: видео аватара с прозрачным фоном (опционально)
    - shuffle_count: количество вариантов перемешивания (по умолчанию 1)
    - add_subtitles: добавлять ли субтитры (true/false)
    """
    try:
        # Проверка наличия файлов
        if 'shots[]' not in request.files:
            return jsonify({'error': 'No video shots provided'}), 400
        
        shots = request.files.getlist('shots[]')
        
        if len(shots) < 3:
            return jsonify({'error': 'Minimum 3 shots required (hook, middle, cta)'}), 400
        
        # Параметры
        shuffle_count = int(request.form.get('shuffle_count', 1))
        add_subtitles = request.form.get('add_subtitles', 'false').lower() == 'true'
        
        # Сохранение загруженных шотов
        upload_folder = current_app.config['UPLOAD_FOLDER']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_folder = os.path.join(upload_folder, f'montage_{timestamp}')
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
        if 'audio' in request.files:
            audio = request.files['audio']
            if audio and allowed_file(audio.filename, ALLOWED_AUDIO_EXTENSIONS):
                audio_filename = secure_filename(f'audio_{audio.filename}')
                audio_path = os.path.join(project_folder, audio_filename)
                audio.save(audio_path)
                logger.info(f"Saved audio: {audio_filename}")
        
        # Сохранение аватара (если есть)
        avatar_path = None
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar and allowed_file(avatar.filename, ALLOWED_VIDEO_EXTENSIONS):
                avatar_filename = secure_filename(f'avatar_{avatar.filename}')
                avatar_path = os.path.join(project_folder, avatar_filename)
                avatar.save(avatar_path)
                logger.info(f"Saved avatar: {avatar_filename}")
        
        # Создание вариантов монтажа
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
            output_folder = current_app.config['OUTPUT_FOLDER']
            output_filename = f'montage_{timestamp}_v{variant:02d}.mp4'
            output_path = os.path.join(output_folder, output_filename)
            
            # Базовая команда ffmpeg для конкатенации
            ffmpeg_cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_file
            ]
            
            # Добавление аудио если есть
            if audio_path:
                ffmpeg_cmd.extend(['-i', audio_path])
                ffmpeg_cmd.extend(['-c:v', 'copy', '-c:a', 'aac', '-shortest'])
            else:
                ffmpeg_cmd.extend(['-c', 'copy'])
            
            ffmpeg_cmd.append(output_path)
            
            logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully created montage variant {variant}")
                
                # Наложение аватара (если есть)
                if avatar_path:
                    output_with_avatar = output_path.replace('.mp4', '_with_avatar.mp4')
                    overlay_cmd = [
                        'ffmpeg', '-i', output_path, '-i', avatar_path,
                        '-filter_complex', '[1:v]colorkey=0x00FF00:0.1:0.1[ckout];[0:v][ckout]overlay=x=10:y=10[out]',
                        '-map', '[out]', '-map', '0:a?',
                        '-c:a', 'copy',
                        output_with_avatar
                    ]
                    
                    overlay_result = subprocess.run(overlay_cmd, capture_output=True, text=True)
                    
                    if overlay_result.returncode == 0:
                        output_path = output_with_avatar
                        logger.info(f"Successfully added avatar to variant {variant}")
                
                output_videos.append({
                    'variant': variant,
                    'filename': os.path.basename(output_path),
                    'path': output_path,
                    'url': f'/api/montage/download/{os.path.basename(output_path)}',
                    'shots_order': [os.path.basename(p) for p in final_order]
                })
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
        
        return jsonify({
            'success': True,
            'project_id': timestamp,
            'variants_created': len(output_videos),
            'outputs': output_videos,
            'hook': os.path.basename(hook_shot),
            'cta': os.path.basename(cta_shot),
            'middle_shots_count': len(middle_shots)
        })
    
    except Exception as e:
        logger.error(f"Error creating montage: {e}")
        return jsonify({'error': str(e)}), 500

@montage_bp.route('/download/<filename>')
def download_video(filename):
    """Скачать готовое видео"""
    try:
        output_folder = current_app.config['OUTPUT_FOLDER']
        filepath = os.path.join(output_folder, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return jsonify({'error': str(e)}), 500

@montage_bp.route('/list', methods=['GET'])
def list_projects():
    """Список всех проектов монтажа"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        projects = []
        
        for folder in os.listdir(upload_folder):
            if folder.startswith('montage_'):
                project_path = os.path.join(upload_folder, folder)
                if os.path.isdir(project_path):
                    projects.append({
                        'id': folder,
                        'created': folder.replace('montage_', ''),
                        'path': project_path
                    })
        
        return jsonify({
            'success': True,
            'projects': projects
        })
    
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return jsonify({'error': str(e)}), 500
