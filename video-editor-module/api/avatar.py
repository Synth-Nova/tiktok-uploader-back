"""
Подмодуль 3: Avatar Generator (HeyGen API)
Функционал:
- Создание talking head видео через HeyGen API
- Поддержка различных аватаров
- Интеграция с текстом или аудио
"""

from flask import Blueprint, request, jsonify, current_app
import os
import requests
import json
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

avatar_bp = Blueprint('avatar', __name__)

HEYGEN_API_BASE = "https://api.heygen.com/v2"

@avatar_bp.route('/create', methods=['POST'])
def create_avatar_video():
    """
    Создать видео с аватаром через HeyGen API
    
    Ожидаемые поля:
    - text: текст для произнесения
    - avatar_id: ID аватара (опционально)
    - voice_id: ID голоса (опционально)
    - language: язык (опционально)
    - background: цвет или изображение фона (опционально)
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        avatar_id = data.get('avatar_id', 'default')
        voice_id = data.get('voice_id', 'default')
        language = data.get('language', 'en')
        background = data.get('background', '#FFFFFF')
        
        api_key = current_app.config['HEYGEN_API_KEY']
        
        # HeyGen API endpoint для создания видео
        url = f"{HEYGEN_API_BASE}/video/generate"
        
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
        
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": voice_id,
                    "language": language
                },
                "background": {
                    "type": "color",
                    "value": background
                }
            }],
            "dimension": {
                "width": 1920,
                "height": 1080
            },
            "aspect_ratio": "16:9"
        }
        
        logger.info(f"Creating HeyGen avatar video with text: {text[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            video_id = result.get('data', {}).get('video_id')
            
            if video_id:
                logger.info(f"HeyGen video generation started: {video_id}")
                
                return jsonify({
                    'success': True,
                    'video_id': video_id,
                    'status': 'processing',
                    'message': 'Video generation started. Use /api/avatar/status/<video_id> to check progress.',
                    'check_url': f'/api/avatar/status/{video_id}'
                })
            else:
                return jsonify({
                    'error': 'No video_id returned from HeyGen',
                    'response': result
                }), 500
        else:
            logger.error(f"HeyGen API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': f'HeyGen API error: {response.status_code}',
                'details': response.text
            }), response.status_code
    
    except Exception as e:
        logger.error(f"Error creating avatar video: {e}")
        return jsonify({'error': str(e)}), 500

@avatar_bp.route('/status/<video_id>', methods=['GET'])
def check_video_status(video_id):
    """
    Проверить статус генерации видео
    """
    try:
        api_key = current_app.config['HEYGEN_API_KEY']
        url = f"{HEYGEN_API_BASE}/video/{video_id}"
        
        headers = {
            "X-Api-Key": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            
            status = data.get('status', 'unknown')
            video_url = data.get('video_url')
            
            response_data = {
                'success': True,
                'video_id': video_id,
                'status': status,
                'video_url': video_url
            }
            
            if status == 'completed' and video_url:
                response_data['download_url'] = f'/api/avatar/download/{video_id}'
                logger.info(f"HeyGen video completed: {video_id}")
            elif status == 'failed':
                response_data['error'] = data.get('error', 'Video generation failed')
                logger.error(f"HeyGen video failed: {video_id}")
            
            return jsonify(response_data)
        else:
            logger.error(f"HeyGen API error: {response.status_code}")
            return jsonify({
                'error': f'HeyGen API error: {response.status_code}'
            }), response.status_code
    
    except Exception as e:
        logger.error(f"Error checking video status: {e}")
        return jsonify({'error': str(e)}), 500

@avatar_bp.route('/download/<video_id>', methods=['GET'])
def download_avatar_video(video_id):
    """
    Скачать готовое видео с аватаром
    """
    try:
        # Сначала получаем URL видео
        api_key = current_app.config['HEYGEN_API_KEY']
        url = f"{HEYGEN_API_BASE}/video/{video_id}"
        
        headers = {
            "X-Api-Key": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            video_url = result.get('data', {}).get('video_url')
            
            if video_url:
                # Скачиваем видео
                video_response = requests.get(video_url, stream=True, timeout=60)
                
                if video_response.status_code == 200:
                    # Сохраняем видео локально
                    output_folder = current_app.config['OUTPUT_FOLDER']
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    video_filename = f'avatar_{video_id}_{timestamp}.mp4'
                    video_path = os.path.join(output_folder, video_filename)
                    
                    with open(video_path, 'wb') as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    logger.info(f"Avatar video downloaded: {video_filename}")
                    
                    return jsonify({
                        'success': True,
                        'filename': video_filename,
                        'path': video_path,
                        'url': f'/api/montage/download/{video_filename}'
                    })
            
            return jsonify({'error': 'Video URL not available'}), 404
        else:
            return jsonify({'error': 'Failed to get video info'}), response.status_code
    
    except Exception as e:
        logger.error(f"Error downloading avatar video: {e}")
        return jsonify({'error': str(e)}), 500

@avatar_bp.route('/list-avatars', methods=['GET'])
def list_avatars():
    """
    Получить список доступных аватаров
    """
    try:
        api_key = current_app.config['HEYGEN_API_KEY']
        url = f"{HEYGEN_API_BASE}/avatars"
        
        headers = {
            "X-Api-Key": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            avatars = result.get('data', {}).get('avatars', [])
            
            # Форматирование списка аватаров
            formatted_avatars = []
            for avatar in avatars:
                formatted_avatars.append({
                    'avatar_id': avatar.get('avatar_id'),
                    'avatar_name': avatar.get('avatar_name'),
                    'gender': avatar.get('gender'),
                    'preview_image': avatar.get('preview_image_url'),
                    'preview_video': avatar.get('preview_video_url')
                })
            
            return jsonify({
                'success': True,
                'avatars': formatted_avatars,
                'count': len(formatted_avatars)
            })
        else:
            logger.error(f"HeyGen API error: {response.status_code}")
            return jsonify({
                'error': f'HeyGen API error: {response.status_code}'
            }), response.status_code
    
    except Exception as e:
        logger.error(f"Error listing avatars: {e}")
        return jsonify({'error': str(e)}), 500

@avatar_bp.route('/list-voices', methods=['GET'])
def list_voices():
    """
    Получить список доступных голосов для аватаров
    """
    try:
        api_key = current_app.config['HEYGEN_API_KEY']
        url = f"{HEYGEN_API_BASE}/voices"
        
        headers = {
            "X-Api-Key": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            voices = result.get('data', {}).get('voices', [])
            
            # Форматирование списка голосов
            formatted_voices = []
            for voice in voices:
                formatted_voices.append({
                    'voice_id': voice.get('voice_id'),
                    'voice_name': voice.get('voice_name'),
                    'language': voice.get('language'),
                    'gender': voice.get('gender'),
                    'preview_audio': voice.get('preview_audio_url')
                })
            
            return jsonify({
                'success': True,
                'voices': formatted_voices,
                'count': len(formatted_voices)
            })
        else:
            logger.error(f"HeyGen API error: {response.status_code}")
            return jsonify({
                'error': f'HeyGen API error: {response.status_code}'
            }), response.status_code
    
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        return jsonify({'error': str(e)}), 500
