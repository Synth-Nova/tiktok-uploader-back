"""
Подмодуль 2: Voice & Subtitles Generator
Функционал:
- Генерация голоса из текста (ElevenLabs API)
- Генерация субтитров из аудио (Whisper API / Deepgram)
- Поддержка множества языков и голосов
"""

from flask import Blueprint, request, jsonify, current_app, send_file
import os
import requests
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
import subprocess

logger = logging.getLogger(__name__)

voice_subtitles_bp = Blueprint('voice_subtitles', __name__)

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'}

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

@voice_subtitles_bp.route('/generate-voice', methods=['POST'])
def generate_voice():
    """
    Генерация голоса из текста через ElevenLabs API
    
    Ожидаемые поля:
    - text: текст для озвучки
    - voice_id: ID голоса (опционально, по умолчанию используется Rachel)
    - language: язык (en, ru, etc.)
    - model_id: модель ElevenLabs (по умолчанию eleven_multilingual_v2)
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')  # Rachel voice
        language = data.get('language', 'en')
        model_id = data.get('model_id', 'eleven_multilingual_v2')
        
        # ElevenLabs API endpoint
        api_key = current_app.config['ELEVENLABS_API_KEY']
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        logger.info(f"Generating voice for text: {text[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            # Сохранение аудио файла
            output_folder = current_app.config['OUTPUT_FOLDER']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_filename = f'voice_{timestamp}.mp3'
            audio_path = os.path.join(output_folder, audio_filename)
            
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Voice generated successfully: {audio_filename}")
            
            return jsonify({
                'success': True,
                'filename': audio_filename,
                'path': audio_path,
                'url': f'/api/voice-subtitles/download/{audio_filename}',
                'text_length': len(text),
                'voice_id': voice_id,
                'language': language
            })
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': f'ElevenLabs API error: {response.status_code}',
                'details': response.text
            }), response.status_code
    
    except Exception as e:
        logger.error(f"Error generating voice: {e}")
        return jsonify({'error': str(e)}), 500

@voice_subtitles_bp.route('/generate-subtitles', methods=['POST'])
def generate_subtitles():
    """
    Генерация субтитров из аудио через Whisper (local) или Deepgram API
    
    Ожидаемые поля:
    - audio: аудио файл
    - language: язык (опционально, auto-detect)
    - format: формат субтитров (srt, vtt, json)
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        
        if not audio_file or not allowed_audio_file(audio_file.filename):
            return jsonify({'error': 'Invalid audio file format'}), 400
        
        # Параметры
        language = request.form.get('language', 'auto')
        subtitle_format = request.form.get('format', 'srt')
        
        # Сохранение аудио файла
        upload_folder = current_app.config['UPLOAD_FOLDER']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = secure_filename(f'audio_{timestamp}_{audio_file.filename}')
        audio_path = os.path.join(upload_folder, audio_filename)
        audio_file.save(audio_path)
        
        logger.info(f"Generating subtitles for: {audio_filename}")
        
        # Использование Whisper (через whisper-cli или whisper.cpp)
        # Альтернатива: можно использовать OpenAI Whisper API или Deepgram
        
        try:
            # Попытка использовать whisper CLI (если установлен)
            output_folder = current_app.config['OUTPUT_FOLDER']
            subtitle_base = os.path.join(output_folder, f'subtitles_{timestamp}')
            
            whisper_cmd = [
                'whisper', audio_path,
                '--model', 'base',
                '--output_format', subtitle_format,
                '--output_dir', output_folder
            ]
            
            if language != 'auto':
                whisper_cmd.extend(['--language', language])
            
            result = subprocess.run(
                whisper_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Найти сгенерированный файл субтитров
                subtitle_filename = f'{os.path.splitext(audio_filename)[0]}.{subtitle_format}'
                subtitle_path = os.path.join(output_folder, subtitle_filename)
                
                if os.path.exists(subtitle_path):
                    with open(subtitle_path, 'r', encoding='utf-8') as f:
                        subtitle_content = f.read()
                    
                    logger.info(f"Subtitles generated successfully: {subtitle_filename}")
                    
                    return jsonify({
                        'success': True,
                        'filename': subtitle_filename,
                        'path': subtitle_path,
                        'url': f'/api/voice-subtitles/download/{subtitle_filename}',
                        'format': subtitle_format,
                        'content': subtitle_content,
                        'method': 'whisper-local'
                    })
            
            # Если Whisper не сработал, пробуем альтернативный метод
            logger.warning("Whisper CLI not available, trying alternative method...")
            
        except Exception as whisper_error:
            logger.warning(f"Whisper error: {whisper_error}")
        
        # Альтернативный метод: использование ffmpeg для извлечения текста (если есть встроенные субтитры)
        # Или возврат ошибки с рекомендацией установить Whisper
        
        return jsonify({
            'error': 'Subtitle generation not available',
            'recommendation': 'Please install Whisper: pip install openai-whisper',
            'alternatives': [
                'Use OpenAI Whisper API',
                'Use Deepgram API',
                'Install whisper locally: pip install openai-whisper'
            ]
        }), 501
    
    except Exception as e:
        logger.error(f"Error generating subtitles: {e}")
        return jsonify({'error': str(e)}), 500

@voice_subtitles_bp.route('/list-voices', methods=['GET'])
def list_voices():
    """
    Получить список доступных голосов из ElevenLabs
    """
    try:
        api_key = current_app.config['ELEVENLABS_API_KEY']
        url = "https://api.elevenlabs.io/v1/voices"
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            voices_data = response.json()
            
            # Форматирование списка голосов
            voices = []
            for voice in voices_data.get('voices', []):
                voices.append({
                    'voice_id': voice.get('voice_id'),
                    'name': voice.get('name'),
                    'category': voice.get('category'),
                    'labels': voice.get('labels', {}),
                    'preview_url': voice.get('preview_url')
                })
            
            return jsonify({
                'success': True,
                'voices': voices,
                'count': len(voices)
            })
        else:
            logger.error(f"ElevenLabs API error: {response.status_code}")
            return jsonify({
                'error': f'ElevenLabs API error: {response.status_code}'
            }), response.status_code
    
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        return jsonify({'error': str(e)}), 500

@voice_subtitles_bp.route('/download/<filename>')
def download_file(filename):
    """Скачать аудио или субтитры"""
    try:
        # Проверка в output folder
        output_folder = current_app.config['OUTPUT_FOLDER']
        filepath = os.path.join(output_folder, secure_filename(filename))
        
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        
        # Проверка в upload folder
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, secure_filename(filename))
        
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        
        return jsonify({'error': 'File not found'}), 404
    
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500
