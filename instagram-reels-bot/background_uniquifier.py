#!/usr/bin/env python3
"""
Background Video Uniquifier for Multiple Speakers
Создаёт СИЛЬНО отличающиеся версии фонового видео для каждого спикера

Решает проблему:
- 1 базовое фоновое видео
- 8 спикеров (аккаунтов)
- Нужно, чтобы фон у каждого был РАЗНЫЙ

Метод:
- Для каждого спикера генерируем уникальный "сид"
- Применяем разные комбинации эффектов
- Добавляем уникальные оверлеи
- Изменяем цветовую схему
"""

import os
import sys
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.video_uniquifier import VideoUniquifier, UniquifySettings


class BackgroundUniquifier:
    """
    Создаёт уникальные фоновые видео для каждого спикера
    """
    
    def __init__(self):
        self.uniquifier = VideoUniquifier()
    
    def create_speaker_preset(self, speaker_name: str, speaker_index: int) -> UniquifySettings:
        """
        Создать уникальный пресет для спикера на основе его имени
        
        Каждый спикер получает уникальные параметры:
        - Разный crop
        - Разная цветокоррекция
        - Разный hue shift
        - Разный gamma
        - Разная скорость
        """
        # Генерируем сид из имени спикера
        speaker_seed = int(hashlib.md5(speaker_name.encode()).hexdigest()[:8], 16)
        random.seed(speaker_seed)
        
        settings = UniquifySettings()
        
        # Для каждого спикера - уникальный диапазон модификаций
        # Базируется на индексе спикера (0-7 для 8 спикеров)
        
        # Crop (разный для каждого) - REDUCED to avoid rotation issues
        settings.crop_enabled = True
        settings.crop_percent_min = 0.3
        settings.crop_percent_max = 0.8  # Max 0.8% to be safe
        
        # Brightness (разный диапазон)
        settings.brightness_enabled = True
        base_brightness = (speaker_index - 4) * 0.02  # От -0.08 до +0.06
        settings.brightness_min = base_brightness - 0.03
        settings.brightness_max = base_brightness + 0.03
        
        # Contrast
        settings.contrast_min = 0.95 + (speaker_index * 0.01)
        settings.contrast_max = 1.00 + (speaker_index * 0.01)
        
        # Saturation (каждый спикер - своя насыщенность)
        settings.saturation_enabled = True
        settings.saturation_min = 0.90 + (speaker_index * 0.02)
        settings.saturation_max = 0.95 + (speaker_index * 0.02)
        
        # Hue shift (КРИТИЧНО - разный цветовой тон для каждого)
        settings.hue_enabled = True
        hue_base = speaker_index * 45  # 0, 45, 90, 135, 180, 225, 270, 315 градусов
        settings.hue_shift_min = hue_base - 10
        settings.hue_shift_max = hue_base + 10
        
        # Gamma
        settings.gamma_enabled = True
        settings.gamma_min = 0.95 + (speaker_index * 0.01)
        settings.gamma_max = 1.00 + (speaker_index * 0.01)
        
        # Speed (разная для каждого)
        settings.speed_enabled = True
        if speaker_index % 2 == 0:
            settings.speed_min = 0.96
            settings.speed_max = 0.99
        else:
            settings.speed_min = 1.01
            settings.speed_max = 1.04
        
        # Pitch
        settings.pitch_enabled = True
        settings.pitch_semitones_min = -0.5 * (1 + speaker_index * 0.1)
        settings.pitch_semitones_max = 0.5 * (1 + speaker_index * 0.1)
        
        # Rotation (разный угол)
        settings.rotation_enabled = True
        settings.rotation_degrees_max = 0.3 + (speaker_index * 0.1)
        
        # Frame manipulation
        settings.frame_manipulation_enabled = True
        settings.trim_start_ms_max = 50 + (speaker_index * 20)
        settings.trim_end_ms_max = 50 + (speaker_index * 20)
        
        # Color shift (ВАЖНО - разный для каждого)
        settings.color_shift_enabled = True
        settings.color_shift_amount = 0.02 + (speaker_index * 0.005)
        
        # Watermark
        settings.watermark_enabled = True
        settings.watermark_opacity = 0.01 + (speaker_index * 0.002)
        
        # Noise
        settings.noise_enabled = True
        settings.noise_amount = 0.002 + (speaker_index * 0.0005)
        
        # Качество
        settings.output_crf = 23
        settings.output_preset = "medium"
        
        # Metadata
        settings.strip_metadata = True
        settings.randomize_creation_date = True
        
        random.seed()  # Reset seed
        
        return settings
    
    def create_backgrounds_for_speakers(
        self,
        base_video_path: str,
        speakers: List[str],
        output_dir: str,
        extra_variations: int = 0
    ) -> List[Dict]:
        """
        Создать уникальные фоновые видео для каждого спикера
        
        Args:
            base_video_path: Путь к базовому фоновому видео
            speakers: Список имён спикеров (например: ["Маша", "Саша", "Петя", ...])
            output_dir: Директория для сохранения
            extra_variations: Дополнительные вариации для каждого (0 = только 1 версия)
        
        Returns:
            List of result dicts with info about each generated video
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        print("\n" + "="*70)
        print("🎬 BACKGROUND UNIQUIFIER FOR SPEAKERS v1.0")
        print("="*70)
        print(f"📁 Base video: {base_video_path}")
        print(f"👥 Speakers: {len(speakers)}")
        print(f"📂 Output: {output_dir}")
        print(f"🔢 Variations per speaker: {1 + extra_variations}")
        print(f"📊 Total videos to generate: {len(speakers) * (1 + extra_variations)}")
        print("="*70)
        
        for idx, speaker in enumerate(speakers):
            print(f"\n\n{'='*70}")
            print(f"👤 [{idx+1}/{len(speakers)}] SPEAKER: {speaker}")
            print(f"{'='*70}")
            
            # Создаём базовую настройку для спикера
            base_settings = self.create_speaker_preset(speaker, idx)
            
            # Генерируем основную версию + вариации
            for var_idx in range(1 + extra_variations):
                print(f"\n  📹 Variation {var_idx + 1}/{1 + extra_variations}...")
                
                # Применяем настройки
                self.uniquifier.settings = base_settings
                
                # Генерируем имя файла
                if extra_variations > 0:
                    output_filename = f"{speaker}_background_v{var_idx+1}.mp4"
                else:
                    output_filename = f"{speaker}_background.mp4"
                
                output_path = os.path.join(output_dir, output_filename)
                
                try:
                    # Уникализируем
                    result_path, info = self.uniquifier.uniquify(
                        input_path=base_video_path,
                        output_path=output_path,
                        preset="custom"  # Используем наши кастомные настройки
                    )
                    
                    results.append({
                        'speaker': speaker,
                        'variation': var_idx + 1,
                        'path': result_path,
                        'success': True,
                        'info': info
                    })
                    
                    print(f"  ✅ Saved: {output_filename}")
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    results.append({
                        'speaker': speaker,
                        'variation': var_idx + 1,
                        'success': False,
                        'error': str(e)
                    })
        
        # Итоговая статистика
        successful = len([r for r in results if r.get('success')])
        failed = len(results) - successful
        
        print("\n\n" + "="*70)
        print("📊 GENERATION COMPLETE")
        print("="*70)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📂 Output directory: {output_dir}")
        print("="*70 + "\n")
        
        return results
    
    def analyze_differences(self, video_paths: List[str]) -> None:
        """
        Проанализировать различия между сгенерированными видео
        """
        print("\n" + "="*70)
        print("🔍 ANALYZING DIFFERENCES")
        print("="*70)
        
        if len(video_paths) < 2:
            print("Need at least 2 videos to compare")
            return
        
        # Сравниваем первое видео со всеми остальными
        base_video = video_paths[0]
        
        for i, video in enumerate(video_paths[1:], 1):
            result = self.uniquifier.compare_videos(base_video, video)
            
            print(f"\n📊 Comparison {i}: {Path(base_video).name} vs {Path(video).name}")
            print(f"  Hashes different: {'✅ Yes' if result['hashes_different'] else '❌ No'}")
            print(f"  Size ratio: {result['size_ratio']:.2%}")
            print(f"  Size diff: {result['size_difference']:+,} bytes")


def main():
    """
    Пример использования
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Background Video Uniquifier for Multiple Speakers'
    )
    
    parser.add_argument('input', help='Path to base background video')
    parser.add_argument('-s', '--speakers', nargs='+', required=True,
                        help='List of speaker names (e.g., Маша Саша Петя)')
    parser.add_argument('-o', '--output-dir', required=True,
                        help='Output directory')
    parser.add_argument('-v', '--variations', type=int, default=0,
                        help='Extra variations per speaker (default: 0)')
    parser.add_argument('--analyze', action='store_true',
                        help='Analyze differences between generated videos')
    
    args = parser.parse_args()
    
    # Создаём уникализатор
    bg_uniquifier = BackgroundUniquifier()
    
    # Генерируем фоны для спикеров
    results = bg_uniquifier.create_backgrounds_for_speakers(
        base_video_path=args.input,
        speakers=args.speakers,
        output_dir=args.output_dir,
        extra_variations=args.variations
    )
    
    # Анализ различий
    if args.analyze:
        successful_paths = [r['path'] for r in results if r.get('success')]
        if successful_paths:
            bg_uniquifier.analyze_differences(successful_paths)


if __name__ == "__main__":
    main()
