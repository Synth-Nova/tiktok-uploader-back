#!/usr/bin/env python3
"""
Web Interface for Video Uniquifier v2.0
Веб-интерфейс для уникализатора видео
"""

import os
import sys
import json
import shutil
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.video_uniquifier import VideoUniquifier, UniquifySettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Directories
BASE_DIR = Path(__file__).parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_DIR = BASE_DIR / "data" / "uniquified"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# Progress tracking
processing_status = {
    'active': False,
    'current': 0,
    'total': 0,
    'message': '',
    'results': []
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 Video Uniquifier v2.0</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            margin-bottom: 20px;
            color: #4fc3f7;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .upload-zone {
            border: 3px dashed #4fc3f7;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-zone:hover {
            background: rgba(79, 195, 247, 0.1);
            border-color: #81d4fa;
        }
        
        .upload-zone.dragover {
            background: rgba(79, 195, 247, 0.2);
        }
        
        .upload-zone input {
            display: none;
        }
        
        .upload-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            padding-bottom: 10px;
        }
        
        .tab {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: #888;
            cursor: pointer;
            font-size: 14px;
            border-radius: 8px 8px 0 0;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #4fc3f7;
            background: rgba(79, 195, 247, 0.1);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .settings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .setting-item {
            background: rgba(0, 0, 0, 0.2);
            padding: 16px;
            border-radius: 8px;
        }
        
        .setting-item label {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .setting-item input[type="checkbox"] {
            width: 20px;
            height: 20px;
            accent-color: #4fc3f7;
        }
        
        .setting-item input[type="range"] {
            width: 100%;
            margin-top: 8px;
            accent-color: #4fc3f7;
        }
        
        .setting-item .value {
            color: #4fc3f7;
            font-weight: bold;
        }
        
        .setting-item small {
            color: #888;
            display: block;
            margin-top: 5px;
        }
        
        .preset-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .preset-btn {
            flex: 1;
            padding: 16px;
            border: 2px solid #4fc3f7;
            background: transparent;
            color: #fff;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .preset-btn:hover, .preset-btn.active {
            background: #4fc3f7;
            color: #1a1a2e;
        }
        
        .preset-btn .icon {
            font-size: 24px;
            display: block;
            margin-bottom: 8px;
        }
        
        .btn {
            background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
            color: #1a1a2e;
            border: none;
            padding: 16px 32px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(79, 195, 247, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .batch-settings {
            display: flex;
            gap: 20px;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .batch-settings input {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #4fc3f7;
            padding: 10px;
            border-radius: 8px;
            color: #fff;
            width: 100px;
            font-size: 16px;
        }
        
        .progress {
            display: none;
            margin-top: 20px;
        }
        
        .progress-bar {
            height: 24px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4fc3f7, #29b6f6);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            color: #1a1a2e;
        }
        
        .progress-text {
            text-align: center;
            margin-top: 10px;
        }
        
        .results {
            display: none;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .result-item .name {
            flex: 1;
        }
        
        .result-item .hash {
            color: #888;
            font-family: monospace;
            font-size: 11px;
            margin-top: 4px;
        }
        
        .result-item .mods {
            font-size: 11px;
            color: #4fc3f7;
            margin-top: 2px;
        }
        
        .download-btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
        }
        
        .download-btn:hover {
            background: #43a047;
        }
        
        .file-info {
            display: none;
            padding: 16px;
            background: rgba(76, 175, 80, 0.2);
            border-radius: 8px;
            margin-top: 16px;
        }
        
        .file-info.show {
            display: block;
        }
        
        .error {
            background: rgba(244, 67, 54, 0.2);
            color: #ff8a80;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            display: none;
        }
        
        .video-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .video-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .video-item:hover {
            background: rgba(0, 0, 0, 0.3);
        }
        
        .video-item.selected {
            background: rgba(79, 195, 247, 0.2);
            border: 1px solid #4fc3f7;
        }
        
        .info-box {
            background: rgba(79, 195, 247, 0.1);
            border-left: 4px solid #4fc3f7;
            padding: 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 20px;
        }
        
        .info-box h4 {
            margin-bottom: 8px;
        }
        
        .info-box ul {
            margin-left: 20px;
            color: #ccc;
        }
        
        .info-box li {
            margin-bottom: 4px;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .processing {
            animation: pulse 1.5s infinite;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-item {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-item .number {
            font-size: 24px;
            font-weight: bold;
            color: #4fc3f7;
        }
        
        .stat-item .label {
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Video Uniquifier v2.0</h1>
        <p class="subtitle">Создание уникальных версий видео для обхода детекции дубликатов</p>
        
        <!-- Info Box -->
        <div class="info-box">
            <h4>ℹ️ Как это работает</h4>
            <ul>
                <li>Загрузите видео или выберите существующее</li>
                <li>Выберите пресет или настройте параметры вручную</li>
                <li>Укажите количество уникальных версий</li>
                <li>Каждая версия будет иметь уникальный хэш и незаметные визуальные отличия</li>
            </ul>
        </div>
        
        <!-- Upload Section -->
        <div class="card">
            <h2>📤 Выбор видео</h2>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('upload')">📁 Загрузить</button>
                <button class="tab" onclick="switchTab('existing')">📂 Существующие</button>
            </div>
            
            <div id="upload-tab" class="tab-content active">
                <div class="upload-zone" id="uploadZone">
                    <div class="upload-icon">📁</div>
                    <p>Перетащите видео сюда или нажмите для выбора</p>
                    <p style="color: #888; margin-top: 8px;">MP4, MOV, AVI, MKV, WebM (до 500MB)</p>
                    <input type="file" id="fileInput" accept=".mp4,.mov,.avi,.mkv,.webm">
                </div>
            </div>
            
            <div id="existing-tab" class="tab-content">
                <div class="video-list" id="videoList">
                    {% for video in videos %}
                    <div class="video-item" onclick="selectVideo('{{ video.path }}', this)">
                        <span>📹 {{ video.name }} <small style="color: #888">({{ video.size_mb }} MB)</small></span>
                    </div>
                    {% endfor %}
                    {% if not videos %}
                    <p style="color: #888; text-align: center; padding: 20px;">Нет загруженных видео</p>
                    {% endif %}
                </div>
            </div>
            
            <div class="file-info" id="fileInfo">
                <strong>✅ Выбрано:</strong> <span id="fileName"></span>
                <br><small id="fileSize"></small>
            </div>
            <div class="error" id="uploadError"></div>
        </div>
        
        <!-- Settings -->
        <div class="card">
            <h2>⚙️ Настройки уникализации</h2>
            
            <div class="preset-buttons">
                <button class="preset-btn" data-preset="minimal" onclick="setPreset('minimal')">
                    <span class="icon">🔹</span>
                    <strong>Минимальные</strong>
                    <small>Почти незаметны</small>
                </button>
                <button class="preset-btn active" data-preset="balanced" onclick="setPreset('balanced')">
                    <span class="icon">⚖️</span>
                    <strong>Сбалансированные</strong>
                    <small>Рекомендуется</small>
                </button>
                <button class="preset-btn" data-preset="aggressive" onclick="setPreset('aggressive')">
                    <span class="icon">🔥</span>
                    <strong>Агрессивные</strong>
                    <small>Макс. уникальность</small>
                </button>
            </div>
            
            <div class="settings-grid">
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="cropEnabled" checked>
                        📐 Обрезка краёв
                    </label>
                    <input type="range" id="cropMax" min="0.5" max="5" step="0.5" value="2">
                    <span class="value" id="cropValue">0-2%</span>
                    <small>Случайная обрезка с масштабированием</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="brightnessEnabled" checked>
                        ☀️ Яркость/Контраст
                    </label>
                    <input type="range" id="brightnessMax" min="1" max="10" step="1" value="5">
                    <span class="value" id="brightnessValue">±5%</span>
                    <small>Случайное изменение яркости</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="saturationEnabled" checked>
                        🎨 Насыщенность
                    </label>
                    <input type="range" id="saturationMax" min="1" max="10" step="1" value="5">
                    <span class="value" id="saturationValue">±5%</span>
                    <small>Изменение насыщенности цветов</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="hueEnabled" checked>
                        🌈 Сдвиг цвета
                    </label>
                    <input type="range" id="hueMax" min="1" max="10" step="1" value="3">
                    <span class="value" id="hueValue">±3°</span>
                    <small>Сдвиг цветового тона</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="speedEnabled" checked>
                        ⏱️ Скорость
                    </label>
                    <input type="range" id="speedMax" min="1" max="5" step="0.5" value="2">
                    <span class="value" id="speedValue">±2%</span>
                    <small>Изменение скорости воспроизведения</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="pitchEnabled" checked>
                        🎵 Pitch аудио
                    </label>
                    <input type="range" id="pitchMax" min="0.1" max="2" step="0.1" value="0.5">
                    <span class="value" id="pitchValue">±0.5 semitones</span>
                    <small>Сдвиг тона аудио</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="noiseEnabled" checked>
                        📊 Шум
                    </label>
                    <input type="range" id="noiseAmount" min="0.001" max="0.01" step="0.001" value="0.002">
                    <span class="value" id="noiseValue">0.002</span>
                    <small>Невидимый шум на изображении</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="rotationEnabled" checked>
                        🔄 Микро-поворот
                    </label>
                    <input type="range" id="rotationMax" min="0.1" max="2" step="0.1" value="0.5">
                    <span class="value" id="rotationValue">±0.5°</span>
                    <small>Незаметный поворот изображения</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="trimEnabled" checked>
                        ✂️ Обрезка кадров
                    </label>
                    <input type="range" id="trimMax" min="50" max="300" step="50" value="100">
                    <span class="value" id="trimValue">±100 мс</span>
                    <small>Обрезка начала/конца</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="colorShiftEnabled" checked>
                        🎨 Color shift
                    </label>
                    <input type="range" id="colorShiftAmount" min="0.01" max="0.05" step="0.005" value="0.02">
                    <span class="value" id="colorShiftValue">2%</span>
                    <small>Сдвиг цветовых каналов RGB</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="gammaEnabled" checked>
                        🌗 Gamma
                    </label>
                    <input type="range" id="gammaMax" min="1" max="5" step="0.5" value="3">
                    <span class="value" id="gammaValue">±3%</span>
                    <small>Гамма-коррекция</small>
                </div>
                
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="watermarkEnabled" checked>
                        💧 Водяной знак
                    </label>
                    <input type="range" id="watermarkOpacity" min="0.005" max="0.02" step="0.005" value="0.01">
                    <span class="value" id="watermarkValue">1%</span>
                    <small>Невидимый уникальный паттерн</small>
                </div>
            </div>
        </div>
        
        <!-- Process -->
        <div class="card">
            <h2>🚀 Обработка</h2>
            
            <div class="batch-settings">
                <label>Количество версий:</label>
                <input type="number" id="versionCount" value="10" min="1" max="100">
                <small style="color: #888;">Каждая версия будет уникальной</small>
            </div>
            
            <button class="btn" id="processBtn" onclick="startProcessing()">
                🎬 Создать уникальные версии
            </button>
            
            <div class="progress" id="progress">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">Подготовка...</div>
            </div>
            
            <div class="error" id="processError"></div>
        </div>
        
        <!-- Results -->
        <div class="card results" id="results">
            <h2>✅ Результаты</h2>
            
            <div class="stats" id="stats"></div>
            
            <div id="resultsList" style="margin-top: 20px;"></div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn" style="flex: 1; background: #4caf50;" onclick="downloadAll()">
                    📥 Скачать все (ZIP)
                </button>
                <button class="btn" style="flex: 1; background: #ff9800;" onclick="location.reload()">
                    🔄 Новая партия
                </button>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let selectedVideoPath = null;
        let currentPreset = 'balanced';
        
        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            
            document.querySelector(`.tab[onclick*="${tabName}"]`).classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        }
        
        // Upload zone handlers
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        
        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) handleFile(files[0]);
        });
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });
        
        function handleFile(file) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (!['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(ext)) {
                showError('uploadError', 'Неподдерживаемый формат файла');
                return;
            }
            
            selectedFile = file;
            selectedVideoPath = null;
            
            // Clear existing selection
            document.querySelectorAll('.video-item').forEach(v => v.classList.remove('selected'));
            
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileSize').textContent = 
                `${(file.size / 1024 / 1024).toFixed(2)} MB`;
            document.getElementById('fileInfo').classList.add('show');
            hideError('uploadError');
        }
        
        function selectVideo(path, element) {
            selectedVideoPath = path;
            selectedFile = null;
            
            // Update selection UI
            document.querySelectorAll('.video-item').forEach(v => v.classList.remove('selected'));
            element.classList.add('selected');
            
            const name = path.split('/').pop();
            document.getElementById('fileName').textContent = name;
            document.getElementById('fileSize').textContent = 'Существующий файл';
            document.getElementById('fileInfo').classList.add('show');
        }
        
        function setPreset(preset) {
            currentPreset = preset;
            document.querySelectorAll('.preset-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.preset === preset);
            });
            
            // Update sliders based on preset
            if (preset === 'minimal') {
                document.getElementById('cropMax').value = 1;
                document.getElementById('brightnessMax').value = 2;
                document.getElementById('saturationMax').value = 2;
                document.getElementById('hueMax').value = 0;
                document.getElementById('speedMax').value = 0;
                document.getElementById('pitchMax').value = 0;
                document.getElementById('noiseAmount').value = 0.001;
                document.getElementById('rotationMax').value = 0;
                document.getElementById('trimMax').value = 0;
                document.getElementById('colorShiftAmount').value = 0;
                document.getElementById('gammaMax').value = 0;
                document.getElementById('watermarkOpacity').value = 0.01;
                
                document.getElementById('speedEnabled').checked = false;
                document.getElementById('pitchEnabled').checked = false;
                document.getElementById('hueEnabled').checked = false;
                document.getElementById('rotationEnabled').checked = false;
                document.getElementById('trimEnabled').checked = false;
                document.getElementById('colorShiftEnabled').checked = false;
                document.getElementById('gammaEnabled').checked = false;
                
            } else if (preset === 'balanced') {
                document.getElementById('cropMax').value = 2;
                document.getElementById('brightnessMax').value = 5;
                document.getElementById('saturationMax').value = 5;
                document.getElementById('hueMax').value = 3;
                document.getElementById('speedMax').value = 2;
                document.getElementById('pitchMax').value = 0.5;
                document.getElementById('noiseAmount').value = 0.002;
                document.getElementById('rotationMax').value = 0.5;
                document.getElementById('trimMax').value = 100;
                document.getElementById('colorShiftAmount').value = 0.02;
                document.getElementById('gammaMax').value = 3;
                document.getElementById('watermarkOpacity').value = 0.01;
                
                document.querySelectorAll('.setting-item input[type="checkbox"]').forEach(cb => {
                    cb.checked = true;
                });
                
            } else if (preset === 'aggressive') {
                document.getElementById('cropMax').value = 3;
                document.getElementById('brightnessMax').value = 8;
                document.getElementById('saturationMax').value = 8;
                document.getElementById('hueMax').value = 5;
                document.getElementById('speedMax').value = 4;
                document.getElementById('pitchMax').value = 1;
                document.getElementById('noiseAmount').value = 0.005;
                document.getElementById('rotationMax').value = 1;
                document.getElementById('trimMax').value = 200;
                document.getElementById('colorShiftAmount').value = 0.03;
                document.getElementById('gammaMax').value = 5;
                document.getElementById('watermarkOpacity').value = 0.01;
                
                document.querySelectorAll('.setting-item input[type="checkbox"]').forEach(cb => {
                    cb.checked = true;
                });
            }
            updateSliderValues();
        }
        
        function updateSliderValues() {
            document.getElementById('cropValue').textContent = 
                '0-' + document.getElementById('cropMax').value + '%';
            document.getElementById('brightnessValue').textContent = 
                '±' + document.getElementById('brightnessMax').value + '%';
            document.getElementById('saturationValue').textContent = 
                '±' + document.getElementById('saturationMax').value + '%';
            document.getElementById('hueValue').textContent = 
                '±' + document.getElementById('hueMax').value + '°';
            document.getElementById('speedValue').textContent = 
                '±' + document.getElementById('speedMax').value + '%';
            document.getElementById('pitchValue').textContent = 
                '±' + document.getElementById('pitchMax').value + ' semitones';
            document.getElementById('noiseValue').textContent = 
                document.getElementById('noiseAmount').value;
            document.getElementById('rotationValue').textContent = 
                '±' + document.getElementById('rotationMax').value + '°';
            document.getElementById('trimValue').textContent = 
                '±' + document.getElementById('trimMax').value + ' мс';
            document.getElementById('colorShiftValue').textContent = 
                (parseFloat(document.getElementById('colorShiftAmount').value) * 100).toFixed(0) + '%';
            document.getElementById('gammaValue').textContent = 
                '±' + document.getElementById('gammaMax').value + '%';
            document.getElementById('watermarkValue').textContent = 
                (parseFloat(document.getElementById('watermarkOpacity').value) * 100).toFixed(1) + '%';
        }
        
        // Update values on slider change
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.addEventListener('input', updateSliderValues);
        });
        
        async function startProcessing() {
            if (!selectedFile && !selectedVideoPath) {
                showError('processError', 'Сначала выберите видео');
                return;
            }
            
            const btn = document.getElementById('processBtn');
            btn.disabled = true;
            btn.innerHTML = '⏳ Обработка...';
            btn.classList.add('processing');
            
            const progress = document.getElementById('progress');
            progress.style.display = 'block';
            
            hideError('processError');
            document.getElementById('results').style.display = 'none';
            
            try {
                const formData = new FormData();
                
                if (selectedFile) {
                    formData.append('video', selectedFile);
                } else {
                    formData.append('video_path', selectedVideoPath);
                }
                
                formData.append('count', document.getElementById('versionCount').value);
                formData.append('preset', currentPreset);
                formData.append('settings', JSON.stringify(getSettings()));
                
                // Start processing
                const response = await fetch('/api/uniquify', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Poll for progress
                if (data.task_id) {
                    await pollProgress(data.task_id);
                } else {
                    showResults(data.results);
                }
                
            } catch (error) {
                showError('processError', error.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🎬 Создать уникальные версии';
                btn.classList.remove('processing');
            }
        }
        
        async function pollProgress(taskId) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            while (true) {
                try {
                    const response = await fetch(`/api/progress/${taskId}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    const percent = (data.current / data.total * 100).toFixed(0);
                    progressFill.style.width = percent + '%';
                    progressFill.textContent = percent + '%';
                    progressText.textContent = data.message || `Обработка: ${data.current}/${data.total}`;
                    
                    if (!data.active && data.results) {
                        showResults(data.results);
                        break;
                    }
                    
                    await new Promise(r => setTimeout(r, 1000));
                    
                } catch (error) {
                    throw error;
                }
            }
        }
        
        function getSettings() {
            return {
                crop_enabled: document.getElementById('cropEnabled').checked,
                crop_percent_max: parseFloat(document.getElementById('cropMax').value),
                brightness_enabled: document.getElementById('brightnessEnabled').checked,
                brightness_max: parseFloat(document.getElementById('brightnessMax').value) / 100,
                saturation_enabled: document.getElementById('saturationEnabled').checked,
                saturation_max: 1 + parseFloat(document.getElementById('saturationMax').value) / 100,
                hue_enabled: document.getElementById('hueEnabled').checked,
                hue_shift_max: parseFloat(document.getElementById('hueMax').value),
                speed_enabled: document.getElementById('speedEnabled').checked,
                speed_max: 1 + parseFloat(document.getElementById('speedMax').value) / 100,
                pitch_enabled: document.getElementById('pitchEnabled').checked,
                pitch_semitones_max: parseFloat(document.getElementById('pitchMax').value),
                noise_enabled: document.getElementById('noiseEnabled').checked,
                noise_amount: parseFloat(document.getElementById('noiseAmount').value),
                rotation_enabled: document.getElementById('rotationEnabled').checked,
                rotation_degrees_max: parseFloat(document.getElementById('rotationMax').value),
                frame_manipulation_enabled: document.getElementById('trimEnabled').checked,
                trim_start_ms_max: parseInt(document.getElementById('trimMax').value),
                color_shift_enabled: document.getElementById('colorShiftEnabled').checked,
                color_shift_amount: parseFloat(document.getElementById('colorShiftAmount').value),
                gamma_enabled: document.getElementById('gammaEnabled').checked,
                gamma_max: 1 + parseFloat(document.getElementById('gammaMax').value) / 100,
                watermark_enabled: document.getElementById('watermarkEnabled').checked,
                watermark_opacity: parseFloat(document.getElementById('watermarkOpacity').value)
            };
        }
        
        function showResults(results) {
            const container = document.getElementById('resultsList');
            const statsContainer = document.getElementById('stats');
            const progressEl = document.getElementById('progress');
            
            progressEl.style.display = 'none';
            
            // Calculate stats
            const successful = results.filter(r => !r.error);
            const failed = results.filter(r => r.error);
            const totalSize = successful.reduce((acc, r) => acc + (r.output_size || 0), 0);
            const avgSize = successful.length > 0 ? totalSize / successful.length : 0;
            
            statsContainer.innerHTML = `
                <div class="stat-item">
                    <div class="number">${successful.length}</div>
                    <div class="label">Успешно создано</div>
                </div>
                <div class="stat-item">
                    <div class="number">${failed.length}</div>
                    <div class="label">Ошибок</div>
                </div>
                <div class="stat-item">
                    <div class="number">${(totalSize / 1024 / 1024).toFixed(1)} MB</div>
                    <div class="label">Общий размер</div>
                </div>
                <div class="stat-item">
                    <div class="number">${successful.length}</div>
                    <div class="label">Уникальных хэшей</div>
                </div>
            `;
            
            container.innerHTML = '';
            
            results.forEach(result => {
                if (result.error) {
                    container.innerHTML += `
                        <div class="result-item" style="background: rgba(244,67,54,0.2);">
                            <span>❌ Версия ${result.version}: ${result.error}</span>
                        </div>
                    `;
                } else {
                    const filename = result.output_path.split('/').pop();
                    const mods = result.modifications || {};
                    const modsList = Object.keys(mods).slice(0, 5).join(', ');
                    
                    container.innerHTML += `
                        <div class="result-item">
                            <div class="name">
                                ✅ ${filename}
                                <div class="hash">🔑 ${result.output_hash}</div>
                                <div class="mods">🔧 ${modsList}...</div>
                            </div>
                            <a href="/download/${encodeURIComponent(filename)}" class="download-btn">
                                📥 Скачать
                            </a>
                        </div>
                    `;
                }
            });
            
            document.getElementById('results').style.display = 'block';
        }
        
        function showError(id, message) {
            const el = document.getElementById(id);
            el.textContent = '❌ ' + message;
            el.style.display = 'block';
        }
        
        function hideError(id) {
            document.getElementById(id).style.display = 'none';
        }
        
        async function downloadAll() {
            window.location.href = '/download-all';
        }
        
        // Initialize slider values
        updateSliderValues();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main page"""
    # Get list of existing videos
    videos = []
    
    # Check videos in data/videos
    videos_dir = BASE_DIR / "data" / "videos"
    if videos_dir.exists():
        for f in videos_dir.glob("*.mp4"):
            videos.append({
                'name': f.name,
                'path': str(f),
                'size_mb': round(f.stat().st_size / 1024 / 1024, 2)
            })
    
    # Check uploaded videos
    for f in UPLOAD_DIR.glob("*"):
        if f.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            videos.append({
                'name': f.name,
                'path': str(f),
                'size_mb': round(f.stat().st_size / 1024 / 1024, 2)
            })
    
    return render_template_string(HTML_TEMPLATE, videos=videos)


@app.route('/api/uniquify', methods=['POST'])
def api_uniquify():
    """API endpoint for video uniquification"""
    global processing_status
    
    try:
        # Get video file
        video_path = None
        
        if 'video' in request.files:
            file = request.files['video']
            if file.filename:
                # Generate unique filename
                from werkzeug.utils import secure_filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                original_name = secure_filename(file.filename)
                filename = f"{timestamp}_{original_name}"
                video_path = str(UPLOAD_DIR / filename)
                file.save(video_path)
                logger.info(f"Uploaded: {video_path}")
        
        elif 'video_path' in request.form:
            video_path = request.form['video_path']
            if not os.path.exists(video_path):
                return jsonify({'error': f'Video not found: {video_path}'})
        
        if not video_path:
            return jsonify({'error': 'No video provided'})
        
        # Get settings
        count = int(request.form.get('count', 10))
        preset = request.form.get('preset', 'balanced')
        
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = OUTPUT_DIR / f"batch_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process in background
        def process_videos():
            global processing_status
            processing_status = {
                'active': True,
                'current': 0,
                'total': count,
                'message': 'Инициализация...',
                'results': []
            }
            
            try:
                uniquifier = VideoUniquifier()
                
                input_name = Path(video_path).stem
                input_ext = Path(video_path).suffix
                
                for i in range(count):
                    processing_status['current'] = i
                    processing_status['message'] = f'Создание версии {i+1}/{count}...'
                    
                    output_filename = f"{input_name}_v{i+1:03d}_{uniquifier._generate_random_string(4)}{input_ext}"
                    output_path = str(output_dir / output_filename)
                    
                    try:
                        _, result_info = uniquifier.uniquify(
                            input_path=video_path,
                            output_path=output_path,
                            preset=preset
                        )
                        result_info['version'] = i + 1
                        processing_status['results'].append(result_info)
                    except Exception as e:
                        processing_status['results'].append({
                            'version': i + 1,
                            'error': str(e)
                        })
                
                processing_status['current'] = count
                processing_status['message'] = 'Готово!'
                
            finally:
                processing_status['active'] = False
        
        # Start processing in background
        thread = threading.Thread(target=process_videos)
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': 'current',
            'message': 'Processing started'
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)})


@app.route('/api/progress/<task_id>')
def api_progress(task_id):
    """Get processing progress"""
    global processing_status
    return jsonify(processing_status)


@app.route('/download/<filename>')
def download_file(filename):
    """Download a uniquified video"""
    # Search in all output directories
    for batch_dir in OUTPUT_DIR.glob("batch_*"):
        file_path = batch_dir / filename
        if file_path.exists():
            return send_file(
                str(file_path),
                as_attachment=True,
                download_name=filename
            )
    
    return "File not found", 404


@app.route('/download-all')
def download_all():
    """Download all uniquified videos as ZIP"""
    import zipfile
    
    # Find latest batch
    batch_dirs = sorted(OUTPUT_DIR.glob("batch_*"), reverse=True)
    if not batch_dirs:
        return "No files to download", 404
    
    latest_batch = batch_dirs[0]
    
    # Create ZIP
    zip_path = OUTPUT_DIR / f"{latest_batch.name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in latest_batch.glob("*"):
            if file.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.json']:
                zipf.write(file, file.name)
    
    return send_file(
        str(zip_path),
        as_attachment=True,
        download_name=f"uniquified_videos_{latest_batch.name}.zip"
    )


def run_server(host='0.0.0.0', port=8080):
    """Run the web server"""
    print("\n" + "="*60)
    print("🎬 VIDEO UNIQUIFIER WEB INTERFACE v2.0")
    print("="*60)
    print(f"\n📁 Upload dir: {UPLOAD_DIR}")
    print(f"📂 Output dir: {OUTPUT_DIR}")
    print(f"\n🌐 Starting server on http://{host}:{port}")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    run_server()
