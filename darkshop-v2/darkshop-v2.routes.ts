/**
 * Dark.Shopping API v2 Routes
 * Покупка TikTok аккаунтов с cookies
 */

import { Router, Request, Response } from 'express';
import { DarkShopV2Service } from '../services/darkshop-v2.service';
import { PrismaClient } from '@prisma/client';

const router = Router();
const prisma = new PrismaClient();

let darkShopService: DarkShopV2Service | null = null;

function getService(): DarkShopV2Service {
  const apiKey = process.env.DARKSHOP_API_KEY;
  
  if (!apiKey) {
    throw new Error('DARKSHOP_API_KEY not configured');
  }
  
  if (!darkShopService) {
    darkShopService = new DarkShopV2Service({ apiKey });
  }
  
  return darkShopService;
}

/**
 * GET /api/darkshop/status
 * Статус подключения и баланс
 */
router.get('/status', async (req: Request, res: Response) => {
  try {
    const service = getService();
    const balance = await service.getBalance();
    
    res.json({
      success: true,
      data: {
        connected: true,
        balance: balance.balance,
        currency: balance.currency,
        apiUrl: 'https://dark.shopping'
      }
    });
  } catch (error: any) {
    res.json({
      success: true,
      data: {
        connected: false,
        error: error.message
      }
    });
  }
});

/**
 * GET /api/darkshop/products
 * Список TikTok товаров
 */
router.get('/products', async (req: Request, res: Response) => {
  try {
    const service = getService();
    
    const withCookies = req.query.with_cookies === 'true';
    const country = req.query.country as string | undefined;
    const maxPrice = req.query.max_price ? parseFloat(req.query.max_price as string) : undefined;
    
    const products = await service.searchTikTokProducts({
      withCookies,
      country,
      maxPrice
    });

    // Форматируем для UI
    const formatted = products.map((p: any) => ({
      id: p.id,
      name: p.name,
      price: parseFloat(p.price as any),
      quantity: p.quantity,
      hasCookies: p.name.toLowerCase().includes('cookie')
    }));

    res.json({
      success: true,
      data: formatted,
      total: formatted.length
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/darkshop/products/cookies
 * Только товары с cookies
 */
router.get('/products/cookies', async (req: Request, res: Response) => {
  try {
    const service = getService();
    
    const country = req.query.country as string | undefined;
    const maxPrice = req.query.max_price ? parseFloat(req.query.max_price as string) : undefined;
    
    const products = await service.getTikTokWithCookies({
      country,
      maxPrice
    });

    const formatted = products.map((p: any) => ({
      id: p.id,
      name: p.name,
      price: parseFloat(p.price as any),
      quantity: p.quantity,
      priceFormatted: `${parseFloat(p.price as any).toFixed(2)}₽`
    }));

    res.json({
      success: true,
      data: formatted,
      total: formatted.length
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/darkshop/products/:id
 * Детали товара
 */
router.get('/products/:id', async (req: Request, res: Response) => {
  try {
    const service = getService();
    const productId = parseInt(req.params.id);
    
    const product = await service.getProduct(productId);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    res.json({
      success: true,
      data: product
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/darkshop/purchase
 * Покупка товара
 */
router.post('/purchase', async (req: Request, res: Response) => {
  try {
    const service = getService();
    const { productId, quantity } = req.body;
    
    if (!productId || !quantity) {
      return res.status(400).json({
        success: false,
        error: 'productId and quantity are required'
      });
    }

    const result = await service.buyProduct(productId, quantity);
    
    if (!result.success) {
      return res.status(400).json({
        success: false,
        error: result.error
      });
    }

    res.json({
      success: true,
      data: {
        orderId: result.orderId,
        total: result.total,
        itemsCount: result.items?.length || 0,
        items: result.items
      }
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/darkshop/buy-tiktok-cookies
 * Быстрая покупка TikTok с cookies + добавление в систему
 */
router.post('/buy-tiktok-cookies', async (req: Request, res: Response) => {
  try {
    const service = getService();
    const { 
      quantity = 1, 
      country,
      maxPricePerItem,
      addToSystem = true,
      autoAssignProxy = true
    } = req.body;
    
    console.log(`[DarkShop] Buying ${quantity} TikTok accounts with cookies for ${country || 'any country'}`);

    // Покупаем аккаунты
    const result = await service.buyTikTokWithCookies({
      quantity: parseInt(quantity),
      country,
      maxPricePerItem: maxPricePerItem ? parseFloat(maxPricePerItem) : undefined
    });
    
    if (!result.success) {
      return res.status(400).json({
        success: false,
        error: result.error
      });
    }

    let addedToSystem = 0;
    const addedAccounts: any[] = [];

    // Добавляем в систему
    if (addToSystem && result.items && result.items.length > 0) {
      for (const item of result.items) {
        try {
          // Создаём аккаунт в БД
          const account = await prisma.managedAccount.create({
            data: {
              email: item.email || item.login || `darkshop_${Date.now()}@temp.com`,
              password: item.password || '',
              username: item.login || '',
              backupCode: item.twoFA || item.emailPassword || '',
              platform: 'tiktok',
              country: country?.toUpperCase() || 'US',
              status: 'active',
              // Сохраняем cookies если есть
              ...(item.cookies && { cookies: item.cookies })
            }
          });

          addedAccounts.push({
            id: account.id,
            email: account.email,
            hasCookies: !!item.cookies
          });

          addedToSystem++;
        } catch (dbError: any) {
          console.error(`[DarkShop] Failed to add account to DB:`, dbError.message);
        }
      }

      // Автоматически назначаем прокси
      if (autoAssignProxy && addedAccounts.length > 0) {
        try {
          // Находим свободные прокси
          const freeProxies = await prisma.proxy.findMany({
            where: {
              status: { not: 'dead' }
            },
            take: addedAccounts.length
          });

          for (let i = 0; i < Math.min(addedAccounts.length, freeProxies.length); i++) {
            await prisma.managedAccount.update({
              where: { id: addedAccounts[i].id },
              data: { proxyId: freeProxies[i].id }
            });
            addedAccounts[i].proxyAssigned = true;
          }
        } catch (proxyError: any) {
          console.error(`[DarkShop] Failed to assign proxies:`, proxyError.message);
        }
      }
    }

    res.json({
      success: true,
      data: {
        orderId: result.orderId,
        purchased: result.items?.length || 0,
        total: result.total,
        addedToSystem,
        accounts: addedAccounts
      }
    });
  } catch (error: any) {
    console.error(`[DarkShop] Error:`, error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/darkshop/countries
 * Доступные страны для TikTok с cookies
 */
router.get('/countries', async (req: Request, res: Response) => {
  try {
    const service = getService();
    const products = await service.getTikTokWithCookies({});

    // Извлекаем страны из названий
    const countriesSet = new Set<string>();
    const countryPatterns = [
      /USA/i, /UK/i, /United Kingdom/i, /Germany/i, /France/i, /Canada/i,
      /Australia/i, /Europe/i, /Asia/i, /Oceania/i, /Latin America/i,
      /Mexico/i, /Brazil/i, /Italy/i, /Spain/i, /Portugal/i,
      /Philippines/i, /Vietnam/i, /Indonesia/i, /Thailand/i,
      /Saudi Arabia/i, /UAE/i, /Israel/i, /South Korea/i, /Japan/i
    ];

    for (const product of products) {
      for (const pattern of countryPatterns) {
        const match = product.name.match(pattern);
        if (match) {
          countriesSet.add(match[0]);
        }
      }
    }

    const countries = Array.from(countriesSet).map(name => ({
      name,
      code: name.toUpperCase().replace(/\s+/g, '_').substring(0, 2)
    }));

    res.json({
      success: true,
      data: countries
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;
