/**
 * SynthNova - Accounts Management API Routes V2
 * Управление аккаунтами TikTok, YouTube, Instagram
 * 
 * Endpoints:
 * - GET    /api/managed-accounts           - Список аккаунтов с фильтрацией
 * - GET    /api/managed-accounts/stats     - Статистика по аккаунтам
 * - GET    /api/managed-accounts/:id       - Детали аккаунта
 * - POST   /api/managed-accounts/import    - Импорт аккаунтов (массовый)
 * - PUT    /api/managed-accounts/:id       - Обновление аккаунта
 * - PUT    /api/managed-accounts/:id/status - Обновление статуса
 * - DELETE /api/managed-accounts/:id       - Удаление аккаунта
 * - POST   /api/managed-accounts/bulk-delete - Массовое удаление
 * - POST   /api/managed-accounts/bulk-status - Массовое обновление статуса
 * - POST   /api/managed-accounts/verify    - Массовая верификация (Cookie/Login)
 * - POST   /api/managed-accounts/verify/:id - Верификация одного аккаунта
 * - POST   /api/managed-accounts/warm      - Массовый прогрев
 * - GET    /api/managed-accounts/verifier/status - Статус верификатора
 * 
 * Verification Types:
 * - Cookie: проверка cookies через API платформы
 * - Login: вход по email/password + IMAP
 * 
 * Platforms: tiktok, youtube, instagram
 */

import { Router, Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AccountVerifierService, parseCookies, buildCookieString } from './account-verifier.service';

const router = Router();
const prisma = new PrismaClient();
const verifierService = new AccountVerifierService();

// Типы аккаунтов
type AccountType = 'cookie' | 'login' | 'autoreg';
type AccountStatus = 'new' | 'verifying' | 'verified' | 'warming' | 'ready' | 'working' | 'dead' | 'banned';
type Platform = 'tiktok' | 'youtube' | 'instagram';

interface ImportAccount {
  email?: string;
  password?: string;
  emailPassword?: string;
  backupCode?: string;
  cookies?: string;
  username?: string;
}

interface ImportRequest {
  platform: Platform;
  type: AccountType;
  country: string;
  accounts: ImportAccount[];
}

// ==================== GET /api/managed-accounts ====================
// Список аккаунтов с фильтрацией и пагинацией
router.get('/', async (req: Request, res: Response) => {
  try {
    const {
      platform,
      type,
      status,
      country,
      search,
      page = '1',
      limit = '50'
    } = req.query;

    const where: any = {};
    
    if (platform && platform !== 'all') {
      where.platform = platform;
    }
    if (type && type !== 'all') {
      where.type = type;
    }
    if (status && status !== 'all') {
      where.status = status;
    }
    if (country && country !== 'all') {
      where.country = country;
    }
    if (search) {
      where.OR = [
        { email: { contains: search as string, mode: 'insensitive' } },
        { username: { contains: search as string, mode: 'insensitive' } }
      ];
    }

    const skip = (parseInt(page as string) - 1) * parseInt(limit as string);
    const take = parseInt(limit as string);

    const [accounts, total] = await Promise.all([
      prisma.managedAccount.findMany({
        where,
        skip,
        take,
        orderBy: { createdAt: 'desc' }
      }),
      prisma.managedAccount.count({ where })
    ]);

    res.json({
      success: true,
      data: accounts,
      pagination: {
        page: parseInt(page as string),
        limit: parseInt(limit as string),
        total,
        pages: Math.ceil(total / parseInt(limit as string))
      }
    });
  } catch (error: any) {
    console.error('Error fetching accounts:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== GET /api/managed-accounts/stats ====================
// Статистика по аккаунтам
router.get('/stats', async (req: Request, res: Response) => {
  try {
    const { platform } = req.query;
    
    const where: any = {};
    if (platform && platform !== 'all') {
      where.platform = platform;
    }

    // Общее количество
    const total = await prisma.managedAccount.count({ where });
    
    // Получаем все аккаунты и группируем вручную
    const accounts = await prisma.managedAccount.findMany({
      where,
      select: { status: true, platform: true }
    });
    
    // Группировка по статусам
    const byStatus: Record<string, number> = {};
    const byPlatform: Record<string, number> = {};
    
    accounts.forEach((acc: any) => {
      const status = acc.status || 'unknown';
      byStatus[status] = (byStatus[status] || 0) + 1;
      
      const platform = acc.platform || 'unknown';
      byPlatform[platform] = (byPlatform[platform] || 0) + 1;
    });

    res.json({
      success: true,
      data: {
        total,
        byStatus,
        byPlatform
      }
    });
  } catch (error: any) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== GET /api/managed-accounts/:id ====================
// Детали аккаунта
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    
    const account = await prisma.managedAccount.findUnique({
      where: { id }
    });

    if (!account) {
      return res.status(404).json({ success: false, error: 'Account not found' });
    }

    res.json({ success: true, data: account });
  } catch (error: any) {
    console.error('Error fetching account:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== POST /api/managed-accounts/import ====================
// Массовый импорт аккаунтов
router.post('/import', async (req: Request, res: Response) => {
  try {
    const { platform, type, country, accounts } = req.body as ImportRequest;

    if (!platform || !type || !accounts || !Array.isArray(accounts)) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: platform, type, accounts'
      });
    }

    if (accounts.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No accounts to import'
      });
    }

    console.log(`📥 Importing ${accounts.length} ${type} accounts for ${platform}`);

    const createdAccounts: any[] = [];
    const errors: string[] = [];

    for (const acc of accounts) {
      try {
        // Проверка на дубликаты по email
        if (acc.email) {
          const existing = await prisma.managedAccount.findFirst({
            where: {
              email: acc.email,
              platform
            }
          });
          
          if (existing) {
            errors.push(`Duplicate: ${acc.email}`);
            continue;
          }
        }

        // Парсинг cookies если строка
        let cookiesData = acc.cookies;
        if (typeof cookiesData === 'string' && cookiesData.startsWith('[')) {
          try {
            cookiesData = JSON.parse(cookiesData);
          } catch {
            // Оставляем как есть
          }
        }

        const created = await prisma.managedAccount.create({
          data: {
            email: acc.email || '',
            password: acc.password || '',
            username: acc.username || null,
            backupCode: acc.backupCode || acc.emailPassword || null,
            cookies: typeof cookiesData === 'object' ? JSON.stringify(cookiesData) : cookiesData,
            platform,
            type,
            country: country || 'US',
            status: 'new'
          }
        });

        createdAccounts.push(created);
      } catch (e: any) {
        errors.push(`Error importing ${acc.email || 'unknown'}: ${e.message}`);
      }
    }

    console.log(`✅ Imported ${createdAccounts.length}/${accounts.length} accounts`);

    res.json({
      success: true,
      data: {
        imported: createdAccounts.length,
        total: accounts.length,
        errors: errors.length > 0 ? errors : undefined
      }
    });
  } catch (error: any) {
    console.error('Error importing accounts:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== PUT /api/managed-accounts/:id ====================
// Обновление аккаунта
router.put('/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    // Убираем поля которые нельзя обновлять напрямую
    delete updateData.id;
    delete updateData.createdAt;

    const account = await prisma.managedAccount.update({
      where: { id },
      data: {
        ...updateData,
        updatedAt: new Date()
      }
    });

    res.json({ success: true, data: account });
  } catch (error: any) {
    console.error('Error updating account:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== PUT /api/managed-accounts/:id/status ====================
// Обновление статуса аккаунта
router.put('/:id/status', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    const validStatuses: AccountStatus[] = ['new', 'verifying', 'verified', 'warming', 'ready', 'working', 'dead', 'banned'];
    
    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        success: false,
        error: `Invalid status. Valid values: ${validStatuses.join(', ')}`
      });
    }

    const account = await prisma.managedAccount.update({
      where: { id },
      data: {
        status,
        lastActionAt: new Date(),
        updatedAt: new Date()
      }
    });

    res.json({ success: true, data: account });
  } catch (error: any) {
    console.error('Error updating account status:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== DELETE /api/managed-accounts/:id ====================
// Удаление аккаунта
router.delete('/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    await prisma.managedAccount.delete({
      where: { id }
    });

    res.json({ success: true, message: 'Account deleted' });
  } catch (error: any) {
    console.error('Error deleting account:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== POST /api/managed-accounts/bulk-delete ====================
// Массовое удаление аккаунтов
router.post('/bulk-delete', async (req: Request, res: Response) => {
  try {
    const { ids } = req.body;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing or empty ids array'
      });
    }

    const result = await prisma.managedAccount.deleteMany({
      where: {
        id: { in: ids }
      }
    });

    res.json({
      success: true,
      data: { deleted: result.count }
    });
  } catch (error: any) {
    console.error('Error bulk deleting accounts:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== POST /api/managed-accounts/bulk-status ====================
// Массовое обновление статуса
router.post('/bulk-status', async (req: Request, res: Response) => {
  try {
    const { ids, status } = req.body;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing or empty ids array'
      });
    }

    const validStatuses: AccountStatus[] = ['new', 'verifying', 'verified', 'warming', 'ready', 'working', 'dead', 'banned'];
    
    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        success: false,
        error: `Invalid status. Valid values: ${validStatuses.join(', ')}`
      });
    }

    const result = await prisma.managedAccount.updateMany({
      where: {
        id: { in: ids }
      },
      data: {
        status,
        lastActionAt: new Date()
      }
    });

    res.json({
      success: true,
      data: { updated: result.count }
    });
  } catch (error: any) {
    console.error('Error bulk updating status:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== POST /api/managed-accounts/verify ====================
// Верификация аккаунтов (синхронно для небольших batch, асинхронно для больших)
router.post('/verify', async (req: Request, res: Response) => {
  try {
    const { ids, async: asyncMode = false } = req.body;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing or empty ids array'
      });
    }

    // Получаем аккаунты для верификации
    const accounts = await prisma.managedAccount.findMany({
      where: { id: { in: ids } }
    });

    if (accounts.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No accounts found'
      });
    }

    // Обновляем статус на verifying
    await prisma.managedAccount.updateMany({
      where: { id: { in: ids } },
      data: { status: 'verifying', lastActionAt: new Date() }
    });

    console.log(`🔍 Starting verification for ${accounts.length} accounts`);

    // Для больших batch или asyncMode - запускаем в фоне
    if (asyncMode || accounts.length > 10) {
      // Запуск в фоне без ожидания
      verifyAccountsBatch(accounts).catch(err => {
        console.error('Background verification error:', err);
      });

      return res.json({
        success: true,
        message: `Verification started for ${accounts.length} accounts (background)`,
        data: { queued: accounts.length, mode: 'async' }
      });
    }

    // Синхронная верификация для небольших batch
    const results = await verifyAccountsBatch(accounts);

    res.json({
      success: true,
      message: `Verification completed for ${accounts.length} accounts`,
      data: {
        total: results.length,
        verified: results.filter(r => r.status === 'verified').length,
        dead: results.filter(r => r.status === 'dead').length,
        banned: results.filter(r => r.status === 'banned').length,
        errors: results.filter(r => r.status === 'error').length,
        results
      }
    });
  } catch (error: any) {
    console.error('Error in verification:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== POST /api/managed-accounts/verify/:id ====================
// Верификация одного аккаунта
router.post('/verify/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const account = await prisma.managedAccount.findUnique({
      where: { id }
    });

    if (!account) {
      return res.status(404).json({ success: false, error: 'Account not found' });
    }

    // Обновляем статус
    await prisma.managedAccount.update({
      where: { id },
      data: { status: 'verifying', lastActionAt: new Date() }
    });

    // Верифицируем
    const result = await verifySingleAccount(account);

    res.json({
      success: result.success,
      data: result
    });
  } catch (error: any) {
    console.error('Error verifying account:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== GET /api/managed-accounts/verifier/status ====================
// Статус верификатора
router.get('/verifier/status', async (req: Request, res: Response) => {
  try {
    const status = verifierService.getStatus();
    res.json({
      success: true,
      data: status
    });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ==================== Verification Helper Functions ====================

async function verifySingleAccount(account: any): Promise<any> {
  try {
    // Используем AccountVerifierService
    const result = await verifierService.verifyAccount({
      id: account.id,
      platform: account.platform,
      type: account.type,
      cookies: account.cookies,
      email: account.email,
      password: account.password,
      emailPassword: account.backupCode || account.emailPassword
    });

    // Обновляем статус в БД
    const updateData: any = {
      lastActionAt: new Date()
    };

    // Мапим статус (need_verification -> new)
    if (result.status === 'need_verification') {
      updateData.status = 'new';
    } else if (['verified', 'dead', 'banned'].includes(result.status)) {
      updateData.status = result.status;
    }

    // Обновляем username если получили
    if (result.details?.username) {
      updateData.username = result.details.username;
    }

    await prisma.managedAccount.update({
      where: { id: account.id },
      data: updateData
    });

    return result;

  } catch (error: any) {
    console.error(`Verification error for ${account.id}:`, error.message);
    
    return {
      success: false,
      accountId: account.id,
      status: 'error',
      message: error.message
    };
  }
}

async function verifyAccountsBatch(accounts: any[]): Promise<any[]> {
  const results: any[] = [];
  const concurrency = 3;

  console.log(`📋 Starting batch verification of ${accounts.length} accounts`);

  for (let i = 0; i < accounts.length; i += concurrency) {
    const batch = accounts.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(acc => verifySingleAccount(acc))
    );
    results.push(...batchResults);

    // Логируем прогресс
    console.log(`✓ Verified ${Math.min(i + concurrency, accounts.length)}/${accounts.length}`);

    // Пауза между батчами для избежания rate limit
    if (i + concurrency < accounts.length) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  return results;
}

// ==================== POST /api/managed-accounts/warm ====================
// Запуск прогрева аккаунтов (асинхронно)
router.post('/warm', async (req: Request, res: Response) => {
  try {
    const { ids } = req.body;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing or empty ids array'
      });
    }

    // Проверяем что аккаунты verified
    const accounts = await prisma.managedAccount.findMany({
      where: {
        id: { in: ids },
        status: { in: ['verified', 'ready'] }
      }
    });

    if (accounts.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No verified accounts found for warming'
      });
    }

    // Обновляем статус на warming
    await prisma.managedAccount.updateMany({
      where: {
        id: { in: accounts.map(a => a.id) }
      },
      data: {
        status: 'warming',
        lastActionAt: new Date()
      }
    });

    // TODO: Запуск фоновой задачи прогрева
    console.log(`🔥 Warming queued for ${accounts.length} accounts`);

    res.json({
      success: true,
      message: `Warming started for ${accounts.length} accounts`,
      data: { queued: accounts.length }
    });
  } catch (error: any) {
    console.error('Error starting warming:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

export default router;
