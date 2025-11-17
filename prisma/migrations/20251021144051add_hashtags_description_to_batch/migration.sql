-- Миграция: добавление полей hashtags и description в таблицу upload_batches
-- Дата: 2025-10-21

ALTER TABLE "upload_batches" 
ADD COLUMN "hashtags" TEXT,
ADD COLUMN "description" TEXT;

-- Комментарии
COMMENT ON COLUMN "upload_batches"."hashtags" IS 'Хэштеги для всех видео в батче (через запятую)';
COMMENT ON COLUMN "upload_batches"."description" IS 'Описание для всех видео в батче';

