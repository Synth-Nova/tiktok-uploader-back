"""
Video Editor API - Main Flask Application
Video Editor Pro - Объединённый модуль монтажа видео

Подмодули:
1. Montage Pro (Quick + Advanced) - Единый API монтажа
2. Uniquifier - Уникализация видео для обхода детекции
3. Voice & Subtitles Generator (ElevenLabs + Whisper)
4. Avatar Generator (HeyGen)

Legacy (для обратной совместимости):
- Montage V1
- Montage V2
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Импорт новых подмодулей
from api.montage_pro import montage_pro_bp
from api.uniquifier_api import uniquifier_bp

# Импорт legacy подмодулей (для обратной совместимости)
from api.montage import montage_bp
from api.montage_v2 import montage_v2_bp
from api.voice_subtitles import voice_subtitles_bp
from api.avatar import avatar_bp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)
CORS(app)

# Конфигурация
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'outputs')

# API Keys (из environment variables для безопасности)
app.config['ELEVENLABS_API_KEY'] = os.getenv(
    'ELEVENLABS_API_KEY',
    'sk_9537f51db5a1bbf57f6ef774e4fe1c23de43617d0123a177'
)
app.config['HEYGEN_API_KEY'] = os.getenv(
    'HEYGEN_API_KEY',
    'sk_V2_hgu_kqlUGXHp4ZH_9KpXEW7bSJtfoy4tXvhvcgm1no0xFPtN'
)

# Создание необходимых директорий
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Регистрация новых blueprints (Video Editor Pro)
app.register_blueprint(montage_pro_bp, url_prefix='/api/video-editor')
app.register_blueprint(uniquifier_bp, url_prefix='/api/uniquifier')

# Регистрация legacy blueprints (для обратной совместимости)
app.register_blueprint(montage_bp, url_prefix='/api/montage')
app.register_blueprint(montage_v2_bp, url_prefix='/api/montage-v2')
app.register_blueprint(voice_subtitles_bp, url_prefix='/api/voice-subtitles')
app.register_blueprint(avatar_bp, url_prefix='/api/avatar')

# Главная страница API
@app.route('/')
def index():
    return jsonify({
        'service': 'Video Editor Pro API',
        'version': '2.0.0',
        'status': 'running',
        'modules': {
            'video_editor_pro': {
                'name': 'Video Editor Pro',
                'description': 'Объединённый модуль монтажа (Quick + Advanced)',
                'endpoint': '/api/video-editor',
                'features': ['analyze-shots', 'create', 'storage-info', 'projects']
            },
            'uniquifier': {
                'name': 'Video Uniquifier',
                'description': 'Уникализация видео для обхода детекции',
                'endpoint': '/api/uniquifier',
                'features': ['presets', 'single', 'batch', 'compare', 'info']
            },
            'voice_subtitles': {
                'name': 'Voice & Subtitles Generator',
                'description': 'Генерация голоса (ElevenLabs) и субтитров (Whisper)',
                'endpoint': '/api/voice-subtitles'
            },
            'avatar': {
                'name': 'Avatar Generator',
                'description': 'Создание аватаров (HeyGen)',
                'endpoint': '/api/avatar'
            }
        },
        'legacy': {
            'montage_v1': '/api/montage',
            'montage_v2': '/api/montage-v2'
        },
        'timestamp': datetime.utcnow().isoformat()
    })

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

# Endpoint для проверки API ключей
@app.route('/api/check-keys')
def check_keys():
    return jsonify({
        'elevenlabs': 'configured' if app.config['ELEVENLABS_API_KEY'] else 'missing',
        'heygen': 'configured' if app.config['HEYGEN_API_KEY'] else 'missing'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large (max 500MB)'}), 413

if __name__ == '__main__':
    logger.info("Starting Video Editor API on port 8081...")
    app.run(host='0.0.0.0', port=8081, debug=True)
