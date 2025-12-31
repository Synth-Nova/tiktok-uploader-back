"""
Подмодуль: Uniquifier API
HTTP обёртка для VideoUniquifier
Возможности:
- Уникализация одного видео
- Batch-уникализация (несколько версий)
- Сравнение видео
- Информация о видео
"""

from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
import sys
import json
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

uniquifier_bp = Blueprint('uniquifier', __name__)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# Добавляем путь к VideoUniquifier
UNIQUIFIER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'instagram-reels-bot', 'src', 'tools'
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def get_uniquifier():
    """Получить экземпляр VideoUniquifier"""
    sys.path.insert(0, UNIQUIFIER_PATH)
    from video_uniquifier import VideoUniquifier
    return VideoUniquifier()


# =====================================================
# PRESETS INFO - Информация о пресетах
# =====================================================
@uniquifier_bp.route('/presets', methods=['GET'])
def get_presets():
    """Получить информацию о доступных пресетах"""
    return jsonify({
        'success': True,
        'presets': {
            'minimal': {
                'name': 'Минимальный',
                'description': 'Почти незаметные изменения. Для аккаунтов с хорошей репутацией.',
                'effects': [
                    'Crop 0.5-1%',
                    'Яркость ±2%',
                    'Контраст ±1%',
                    'Невидимый водяной знак'
                ],
                'recommended_for': 'Аккаунты с хорошей репутацией'
            },
            'balanced': {
                'name': 'Сбалансированный',
                'description': 'Оптимальный баланс между качеством и уникальностью. Рекомендуется.',
                'effects': [
                    'Crop 0.5-2%',
                    'Яркость ±5%',
                    'Контраст ±3%',
                    'Насыщенность ±5%',
                    'Сдвиг тона ±3°',
                    'Скорость ±2%',
                    'Pitch ±0.5 полутона',
                    'Микро-поворот ±0.5°',
                    'Обрезка кадров ±100мс',
                    'Сдвиг цвета ±2%',
                    'Невидимый водяной знак'
                ],
                'recommended_for': 'Большинство случаев'
            },
            'aggressive': {
                'name': 'Агрессивный',
                'description': 'Максимальная уникальность. Для новых аккаунтов или после бана.',
                'effects': [
                    'Crop 0.5-3%',
                    'Яркость ±8%',
                    'Контраст ±5%',
                    'Насыщенность ±5%',
                    'Сдвиг тона ±5°',
                    'Gamma ±5%',
                    'Скорость ±4%',
                    'Pitch ±1 полутон',
                    'Микро-поворот ±1°',
                    'Обрезка кадров ±200мс',
                    'Сдвиг цвета ±3%',
                    'Шум 0.5%',
                    'Невидимый водяной знак'
                ],
                'recommended_for': 'Новые аккаунты или после бана'
            }
        }
    })


# =====================================================
# UNIQUIFY SINGLE - Уникализация одного видео
# =====================================================
@uniquifier_bp.route('/single', methods=['POST'])
def uniquify_single():
    """
    Уникализация одного видео
    
    FormData:
    - video: видео файл
    - preset: minimal / balanced / aggressive (default: balanced)
    
    Returns:
    - Информация об уникализированном видео
    """
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        
        if not video or not allowed_file(video.filename):
            return jsonify({'error': 'Invalid video file'}), 400
        
        preset = request.form.get('preset', 'balanced')
        if preset not in ['minimal', 'balanced', 'aggressive']:
            preset = 'balanced'
        
        # Сохранение видео
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_folder = os.path.join(upload_folder, f'uniquify_{timestamp}')
        os.makedirs(temp_folder, exist_ok=True)
        
        filename = secure_filename(video.filename)
        input_path = os.path.join(temp_folder, filename)
        video.save(input_path)
        
        logger.info(f"Uniquifying video: {filename} with preset: {preset}")
        
        # Уникализация
        uniquifier = get_uniquifier()
        output_path, info = uniquifier.uniquify(
            input_path=input_path,
            output_path=None,
            preset=preset
        )
        
        # Перемещаем в output_folder
        final_filename = os.path.basename(output_path)
        final_path = os.path.join(output_folder, final_filename)
        shutil.move(output_path, final_path)
        
        # Очистка
        try:
            shutil.rmtree(temp_folder)
        except:
            pass
        
        # Формируем ответ
        return jsonify({
            'success': True,
            'original': {
                'filename': filename,
                'hash': info['input_hash'][:12] + '...',
                'size_mb': round(info['input_size'] / (1024 * 1024), 2)
            },
            'uniquified': {
                'filename': final_filename,
                'url': f'/video-outputs/{final_filename}',
                'hash': info['output_hash'][:12] + '...',
                'size_mb': round(info['output_size'] / (1024 * 1024), 2)
            },
            'preset': preset,
            'modifications': info['modifications'],
            'timestamp': info['timestamp']
        })
    
    except Exception as e:
        logger.error(f"Error uniquifying video: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# UNIQUIFY BATCH - Batch-уникализация
# =====================================================
@uniquifier_bp.route('/batch', methods=['POST'])
def uniquify_batch():
    """
    Создание нескольких уникальных версий видео
    
    FormData:
    - video: видео файл
    - count: количество версий (1-10, default: 5)
    - preset: minimal / balanced / aggressive (default: balanced)
    
    Returns:
    - Список уникализированных видео
    """
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        
        if not video or not allowed_file(video.filename):
            return jsonify({'error': 'Invalid video file'}), 400
        
        count = int(request.form.get('count', 5))
        count = max(1, min(10, count))  # Ограничение 1-10
        
        preset = request.form.get('preset', 'balanced')
        if preset not in ['minimal', 'balanced', 'aggressive']:
            preset = 'balanced'
        
        # Сохранение видео
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_folder = os.path.join(upload_folder, f'uniquify_batch_{timestamp}')
        os.makedirs(temp_folder, exist_ok=True)
        
        filename = secure_filename(video.filename)
        input_path = os.path.join(temp_folder, filename)
        video.save(input_path)
        
        logger.info(f"Batch uniquifying: {filename}, count={count}, preset={preset}")
        
        # Batch уникализация
        uniquifier = get_uniquifier()
        results = uniquifier.batch_uniquify(
            input_path=input_path,
            output_dir=temp_folder,
            count=count,
            preset=preset
        )
        
        # Перемещаем в output_folder
        outputs = []
        for result in results:
            if 'error' not in result:
                output_filename = os.path.basename(result['output_path'])
                final_path = os.path.join(output_folder, output_filename)
                
                if os.path.exists(result['output_path']):
                    shutil.move(result['output_path'], final_path)
                    
                    outputs.append({
                        'version': result['version'],
                        'filename': output_filename,
                        'url': f'/video-outputs/{output_filename}',
                        'hash': result['output_hash'][:12] + '...',
                        'size_mb': round(result['output_size'] / (1024 * 1024), 2),
                        'modifications': result['modifications']
                    })
            else:
                outputs.append({
                    'version': result['version'],
                    'error': result['error']
                })
        
        # Очистка
        try:
            shutil.rmtree(temp_folder)
        except:
            pass
        
        successful = len([o for o in outputs if 'error' not in o])
        
        return jsonify({
            'success': True,
            'original_filename': filename,
            'count_requested': count,
            'count_successful': successful,
            'preset': preset,
            'outputs': outputs
        })
    
    except Exception as e:
        logger.error(f"Error batch uniquifying: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# UNIQUIFY FROM URL - Уникализация по пути/URL
# =====================================================
@uniquifier_bp.route('/from-path', methods=['POST'])
def uniquify_from_path():
    """
    Уникализация видео по пути (для интеграции с монтажом)
    
    JSON:
    {
        "video_path": "/video-outputs/montage_xxx.mp4",
        "preset": "balanced",
        "count": 1
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'video_path' not in data:
            return jsonify({'error': 'video_path is required'}), 400
        
        video_path = data['video_path']
        preset = data.get('preset', 'balanced')
        count = int(data.get('count', 1))
        count = max(1, min(10, count))
        
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        # Определяем полный путь
        if video_path.startswith('/video-outputs/'):
            video_path = os.path.join(output_folder, video_path.replace('/video-outputs/', ''))
        elif not os.path.isabs(video_path):
            video_path = os.path.join(output_folder, video_path)
        
        if not os.path.exists(video_path):
            return jsonify({'error': f'Video not found: {video_path}'}), 404
        
        logger.info(f"Uniquifying from path: {video_path}, preset={preset}, count={count}")
        
        uniquifier = get_uniquifier()
        
        if count == 1:
            output_path, info = uniquifier.uniquify(
                input_path=video_path,
                output_path=None,
                preset=preset
            )
            
            # Перемещаем в output если нужно
            if os.path.dirname(output_path) != output_folder:
                final_path = os.path.join(output_folder, os.path.basename(output_path))
                shutil.move(output_path, final_path)
                output_path = final_path
            
            output_filename = os.path.basename(output_path)
            
            return jsonify({
                'success': True,
                'outputs': [{
                    'filename': output_filename,
                    'url': f'/video-outputs/{output_filename}',
                    'hash': info['output_hash'][:12] + '...',
                    'size_mb': round(info['output_size'] / (1024 * 1024), 2),
                    'modifications': info['modifications']
                }],
                'preset': preset
            })
        else:
            # Batch
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'uniquify_path_{timestamp}')
            os.makedirs(temp_folder, exist_ok=True)
            
            results = uniquifier.batch_uniquify(
                input_path=video_path,
                output_dir=temp_folder,
                count=count,
                preset=preset
            )
            
            outputs = []
            for result in results:
                if 'error' not in result:
                    output_filename = os.path.basename(result['output_path'])
                    final_path = os.path.join(output_folder, output_filename)
                    
                    if os.path.exists(result['output_path']):
                        shutil.move(result['output_path'], final_path)
                        
                        outputs.append({
                            'version': result['version'],
                            'filename': output_filename,
                            'url': f'/video-outputs/{output_filename}',
                            'hash': result['output_hash'][:12] + '...',
                            'size_mb': round(result['output_size'] / (1024 * 1024), 2),
                            'modifications': result['modifications']
                        })
            
            # Очистка
            try:
                shutil.rmtree(temp_folder)
            except:
                pass
            
            return jsonify({
                'success': True,
                'outputs': outputs,
                'preset': preset,
                'count_successful': len(outputs)
            })
    
    except Exception as e:
        logger.error(f"Error uniquifying from path: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# COMPARE - Сравнение видео
# =====================================================
@uniquifier_bp.route('/compare', methods=['POST'])
def compare_videos():
    """
    Сравнение двух видео
    
    FormData:
    - video1: первое видео
    - video2: второе видео
    
    или JSON:
    {
        "video1_path": "...",
        "video2_path": "..."
    }
    """
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_folder = os.path.join(upload_folder, f'compare_{timestamp}')
        os.makedirs(temp_folder, exist_ok=True)
        
        video1_path = None
        video2_path = None
        
        # Проверяем FormData
        if 'video1' in request.files and 'video2' in request.files:
            video1 = request.files['video1']
            video2 = request.files['video2']
            
            video1_path = os.path.join(temp_folder, secure_filename(video1.filename))
            video2_path = os.path.join(temp_folder, secure_filename(video2.filename))
            
            video1.save(video1_path)
            video2.save(video2_path)
        
        # Или JSON с путями
        elif request.is_json:
            data = request.get_json()
            video1_path = data.get('video1_path')
            video2_path = data.get('video2_path')
            
            # Преобразуем относительные пути
            for path in [video1_path, video2_path]:
                if path and path.startswith('/video-outputs/'):
                    path = os.path.join(output_folder, path.replace('/video-outputs/', ''))
        
        if not video1_path or not video2_path:
            return jsonify({'error': 'Two videos are required for comparison'}), 400
        
        if not os.path.exists(video1_path) or not os.path.exists(video2_path):
            return jsonify({'error': 'One or both videos not found'}), 404
        
        # Сравнение
        uniquifier = get_uniquifier()
        result = uniquifier.compare_videos(video1_path, video2_path)
        
        # Очистка если создавали temp файлы
        try:
            shutil.rmtree(temp_folder)
        except:
            pass
        
        return jsonify({
            'success': True,
            'video1': {
                'path': os.path.basename(video1_path),
                'hash': result['video1']['hash'][:12] + '...',
                'size_mb': round(result['video1']['size'] / (1024 * 1024), 2),
                'duration': round(result['video1']['duration'], 2)
            },
            'video2': {
                'path': os.path.basename(video2_path),
                'hash': result['video2']['hash'][:12] + '...',
                'size_mb': round(result['video2']['size'] / (1024 * 1024), 2),
                'duration': round(result['video2']['duration'], 2)
            },
            'comparison': {
                'hashes_different': result['hashes_different'],
                'size_difference_mb': round(result['size_difference'] / (1024 * 1024), 2),
                'size_ratio_percent': round(result['size_ratio'] * 100, 2)
            }
        })
    
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# VIDEO INFO - Информация о видео
# =====================================================
@uniquifier_bp.route('/info', methods=['POST'])
def video_info():
    """
    Получить информацию о видео
    
    FormData:
    - video: видео файл
    
    или JSON:
    {
        "video_path": "..."
    }
    """
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        video_path = None
        cleanup_after = False
        
        # FormData
        if 'video' in request.files:
            video = request.files['video']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_path = os.path.join(upload_folder, f'info_{timestamp}_{secure_filename(video.filename)}')
            video.save(temp_path)
            video_path = temp_path
            cleanup_after = True
        
        # JSON
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if video_path and video_path.startswith('/video-outputs/'):
                video_path = os.path.join(output_folder, video_path.replace('/video-outputs/', ''))
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Video not found'}), 404
        
        uniquifier = get_uniquifier()
        info = uniquifier._get_video_info(video_path)
        file_hash = uniquifier._calculate_hash(video_path)
        file_size = os.path.getsize(video_path)
        
        # Очистка
        if cleanup_after:
            try:
                os.remove(video_path)
            except:
                pass
        
        # Парсим информацию
        video_stream = next(
            (s for s in info.get('streams', []) if s.get('codec_type') == 'video'),
            {}
        )
        audio_stream = next(
            (s for s in info.get('streams', []) if s.get('codec_type') == 'audio'),
            {}
        )
        
        return jsonify({
            'success': True,
            'info': {
                'filename': os.path.basename(video_path),
                'hash': file_hash[:12] + '...',
                'size_mb': round(file_size / (1024 * 1024), 2),
                'duration': round(float(info.get('format', {}).get('duration', 0)), 2),
                'format': info.get('format', {}).get('format_name', 'unknown'),
                'bitrate_kbps': round(int(info.get('format', {}).get('bit_rate', 0)) / 1000),
                'video': {
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'width': video_stream.get('width', 0),
                    'height': video_stream.get('height', 0),
                    'fps': video_stream.get('r_frame_rate', '0/1')
                },
                'audio': {
                    'codec': audio_stream.get('codec_name', 'unknown'),
                    'channels': audio_stream.get('channels', 0),
                    'sample_rate': audio_stream.get('sample_rate', 0)
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return jsonify({'error': str(e)}), 500
