"""
Video Editor API - Main Flask Application
Модуль монтажа видео с 3 подмодулями:
1. Smart Video Montage (перемешивание шотов)
2. Voice & Subtitles Generator (ElevenLabs + Whisper)
3. Avatar Generator (HeyGen)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Импорт подмодулей
from api.montage import montage_bp
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

# Регистрация blueprints (подмодулей)
app.register_blueprint(montage_bp, url_prefix='/api/montage')
app.register_blueprint(voice_subtitles_bp, url_prefix='/api/voice-subtitles')
app.register_blueprint(avatar_bp, url_prefix='/api/avatar')

# Главная страница API
@app.route('/')
def index():
    return jsonify({
        'service': 'Video Editor API',
        'version': '1.0.0',
        'status': 'running',
        'modules': {
            'montage': {
                'name': 'Smart Video Montage',
                'description': 'Перемешивание шотов с Hook и CTA',
                'endpoint': '/api/montage'
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
