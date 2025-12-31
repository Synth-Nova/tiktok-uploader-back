/**
 * Dark.Shopping API v2 Service
 * Покупка TikTok аккаунтов с cookies
 * 
 * API: https://dark.shopping/api/v1/
 * Документация: https://dark.shopping/developer/index
 * Rate Limit: 2 requests per second
 */

import axios, { AxiosInstance } from 'axios';

interface DarkShopConfig {
  apiKey: string;
  baseUrl?: string;
}

interface Product {
  id: number;
  name: string;
  price: string;
  quantity: number;
  minimum_order: number;
  description?: string;
  category?: {
    id: number;
    name: string;
  };
  attributes?: Array<{
    attribute_id: number;
    name: string;
    value: string;
  }>;
}

interface OrderItem {
  // Формат: логин:пароль:почта:пароль_почты:2FA или с cookies
  raw: string;
  login?: string;
  password?: string;
  email?: string;
  emailPassword?: string;
  twoFA?: string;
  cookies?: string;
}

interface BuyResult {
  success: boolean;
  orderId?: number;
  items?: OrderItem[];
  total?: number;
  error?: string;
}

interface BalanceResult {
  balance: number;
  currency: string;
}

export class DarkShopV2Service {
  private client: AxiosInstance;
  private apiKey: string;
  private lastRequestTime: number = 0;
  private minRequestInterval: number = 500; // 500ms between requests

  constructor(config: DarkShopConfig) {
    this.apiKey = config.apiKey;
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://dark.shopping/api/v1',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      // Игнорируем SSL ошибки (некоторые серверы имеют проблемы)
      httpsAgent: new (require('https').Agent)({ rejectUnauthorized: false })
    });
  }

  private async rateLimit(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < this.minRequestInterval) {
      await new Promise(resolve => 
        setTimeout(resolve, this.minRequestInterval - timeSinceLastRequest)
      );
    }
    
    this.lastRequestTime = Date.now();
  }

  private async get<T>(endpoint: string, params: Record<string, any> = {}): Promise<T> {
    await this.rateLimit();
    
    try {
      const response = await this.client.get(endpoint, {
        params: {
          key: this.apiKey,
          ...params
        }
      });
      
      return response.data;
    } catch (error: any) {
      console.error(`[DarkShop] GET ${endpoint} error:`, error.response?.data || error.message);
      throw error;
    }
  }

  private async post<T>(endpoint: string, data: Record<string, any> = {}): Promise<T> {
    await this.rateLimit();
    
    try {
      const response = await this.client.post(endpoint, {
        key: this.apiKey,
        ...data
      });
      
      return response.data;
    } catch (error: any) {
      console.error(`[DarkShop] POST ${endpoint} error:`, error.response?.data || error.message);
      throw error;
    }
  }

  // ==================== Balance ====================

  async getBalance(): Promise<BalanceResult> {
    try {
      // Прямой запрос как curl - без лишних заголовков
      await this.rateLimit();
      
      const https = require('https');
      const url = `https://dark.shopping/api/v1/user/balance?key=${this.apiKey}`;
      
      return new Promise((resolve, reject) => {
        const req = https.get(url, { 
          rejectUnauthorized: false,
          headers: {
            'User-Agent': 'curl/7.88.1',
            'Accept': '*/*'
          }
        }, (res: any) => {
          let data = '';
          res.on('data', (chunk: any) => data += chunk);
          res.on('end', () => {
            try {
              const json = JSON.parse(data);
              if (json.success && json.data) {
                resolve({
                  balance: parseFloat(json.data.balance) || 0,
                  currency: json.data.currency || 'RUB'
                });
              } else {
                reject(new Error('Invalid response'));
              }
            } catch (e) {
              console.error('[DarkShop] Parse error:', data.substring(0, 200));
              reject(new Error('Failed to parse response'));
            }
          });
        });
        
        req.on('error', (e: any) => {
          console.error('[DarkShop] Request error:', e.message);
          reject(e);
        });
        
        req.end();
      });
    } catch (error: any) {
      console.error('[DarkShop] Balance error:', error.message);
      throw new Error(error.message || 'Failed to get balance');
    }
  }

  // ==================== Categories ====================

  async getCategories(): Promise<any[]> {
    const response = await this.get<any>('category/list');
    return response.success ? response.data.items || [] : [];
  }

  // ==================== Products ====================

  /**
   * Нативный GET запрос (работает как curl)
   */
  private nativeGet(url: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const https = require('https');
      const req = https.get(url, { 
        rejectUnauthorized: false,
        headers: {
          'User-Agent': 'curl/7.88.1',
          'Accept': '*/*'
        }
      }, (res: any) => {
        let data = '';
        res.on('data', (chunk: any) => data += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            console.error('[DarkShop] Parse error:', data.substring(0, 200));
            reject(new Error('Failed to parse response'));
          }
        });
      });
      
      req.on('error', (e: any) => reject(e));
      req.end();
    });
  }

  /**
   * Поиск TikTok аккаунтов с cookies
   */
  async getTikTokWithCookies(options: {
    country?: string;
    maxPrice?: number;
    minQuantity?: number;
  } = {}): Promise<Product[]> {
    await this.rateLimit();
    
    // TikTok category_id = 33, используем GET запрос
    const url = `https://dark.shopping/api/v1/product/list?key=${this.apiKey}&category_id=33&only_in_stock=1&per_page=100&name=cookie`;
    
    const response = await this.nativeGet(url);

    if (!response.success || !response.data?.items) {
      return [];
    }

    let products = response.data.items as Product[];

    // Фильтр по цене
    if (options.maxPrice) {
      products = products.filter(p => parseFloat(p.price) <= options.maxPrice!);
    }

    // Фильтр по количеству
    if (options.minQuantity) {
      products = products.filter(p => p.quantity >= options.minQuantity!);
    }

    // Фильтр по стране (в названии)
    if (options.country) {
      const countryLower = options.country.toLowerCase();
      products = products.filter(p => 
        p.name.toLowerCase().includes(countryLower) ||
        p.name.toLowerCase().includes(this.countryToRussian(countryLower))
      );
    }

    // Сортировка по цене
    products.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));

    return products;
  }

  /**
   * Все TikTok товары (с cookies и без)
   */
  async searchTikTokProducts(options: {
    name?: string;
    withCookies?: boolean;
    maxPrice?: number;
    country?: string;
  } = {}): Promise<Product[]> {
    await this.rateLimit();
    
    // Формируем URL для GET запроса
    let url = `https://dark.shopping/api/v1/product/list?key=${this.apiKey}&category_id=33&only_in_stock=1&per_page=100`;
    
    if (options.name) {
      url += `&name=${encodeURIComponent(options.name)}`;
    }
    
    if (options.withCookies) {
      url += `&name=cookie`;
    }

    const response = await this.nativeGet(url);

    if (!response.success || !response.data?.items) {
      return [];
    }

    let products = response.data.items as Product[];

    // Фильтр по цене
    if (options.maxPrice) {
      products = products.filter(p => parseFloat(p.price) <= options.maxPrice!);
    }

    // Фильтр по стране
    if (options.country) {
      const countryLower = options.country.toLowerCase();
      products = products.filter(p => 
        p.name.toLowerCase().includes(countryLower)
      );
    }

    return products;
  }

  /**
   * Получить товар по ID
   */
  async getProduct(productId: number): Promise<Product | null> {
    await this.rateLimit();
    
    const url = `https://dark.shopping/api/v1/product/view?key=${this.apiKey}&id=${productId}`;
    const response = await this.nativeGet(url);
    
    if (response.success && response.data) {
      return response.data as Product;
    }
    
    return null;
  }

  // ==================== Purchase ====================

  /**
   * Купить товар
   */
  async buyProduct(productId: number, quantity: number): Promise<BuyResult> {
    try {
      // Проверяем товар
      const product = await this.getProduct(productId);
      if (!product) {
        return { success: false, error: 'Product not found' };
      }

      // Проверяем наличие
      if (product.quantity < quantity) {
        return { 
          success: false, 
          error: `Not enough items. Available: ${product.quantity}, requested: ${quantity}` 
        };
      }

      // Проверяем минимальный заказ
      if (quantity < (product.minimum_order || 1)) {
        return { 
          success: false, 
          error: `Minimum order: ${product.minimum_order}` 
        };
      }

      // Проверяем баланс
      const balance = await this.getBalance();
      const total = parseFloat(product.price) * quantity;
      
      if (balance.balance < total) {
        return { 
          success: false, 
          error: `Insufficient balance. Required: ${total}₽, available: ${balance.balance}₽` 
        };
      }

      // Создаём заказ через GET (как работает API)
      // Параметр называется "product", не "product_id"!
      await this.rateLimit();
      const orderUrl = `https://dark.shopping/api/v1/order/create?key=${this.apiKey}&product=${productId}&quantity=${quantity}`;
      const response = await this.nativeGet(orderUrl);

      if (response.success) {
        const items = this.parseOrderItems(response.data?.items || []);
        
        return {
          success: true,
          orderId: response.data?.order_id || response.data?.id,
          items: items,
          total: total
        };
      }

      return {
        success: false,
        error: response.message || response.error || 'Order failed'
      };

    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message
      };
    }
  }

  /**
   * Парсинг купленных аккаунтов
   * Форматы:
   * - логин:пароль:почта:пароль_почты:2FA
   * - логин:пароль:почта:пароль_почты:cookies
   * - email:password:cookies (JSON)
   */
  private parseOrderItems(items: any[]): OrderItem[] {
    return items.map(item => {
      const raw = typeof item === 'string' ? item : (item.content || item.data || JSON.stringify(item));
      
      // Пробуем разные форматы
      const parts = raw.split(/[:|]/);
      
      // Проверяем есть ли JSON cookies в конце
      let cookies: string | undefined;
      const cookieMatch = raw.match(/(\{.*"sessionid".*\}|\[.*"sessionid".*\])/i);
      if (cookieMatch) {
        cookies = cookieMatch[1];
      }

      return {
        raw: raw,
        login: parts[0] || undefined,
        password: parts[1] || undefined,
        email: parts[2] || undefined,
        emailPassword: parts[3] || undefined,
        twoFA: parts[4] || undefined,
        cookies: cookies
      };
    });
  }

  /**
   * Быстрая покупка TikTok аккаунтов с cookies
   */
  async buyTikTokWithCookies(options: {
    quantity: number;
    country?: string;
    maxPricePerItem?: number;
  }): Promise<BuyResult> {
    // Находим подходящие товары
    const products = await this.getTikTokWithCookies({
      country: options.country,
      maxPrice: options.maxPricePerItem,
      minQuantity: options.quantity
    });

    if (products.length === 0) {
      return {
        success: false,
        error: `No TikTok accounts with cookies found for country: ${options.country || 'any'}`
      };
    }

    // Берём самый дешёвый
    const cheapest = products[0];
    
    console.log(`[DarkShop] Found: ${cheapest.name}`);
    console.log(`[DarkShop] Price: ${cheapest.price}₽ × ${options.quantity} = ${parseFloat(cheapest.price) * options.quantity}₽`);

    return this.buyProduct(cheapest.id, options.quantity);
  }

  // ==================== Helpers ====================

  private countryToRussian(country: string): string {
    const map: Record<string, string> = {
      'usa': 'сша',
      'us': 'сша',
      'uk': 'великобритания',
      'united kingdom': 'великобритания',
      'germany': 'германия',
      'france': 'франция',
      'canada': 'канада',
      'australia': 'австралия',
      'europe': 'европа',
      'asia': 'азия'
    };
    return map[country] || country;
  }
}

// Export singleton factory
export function createDarkShopV2Service(apiKey: string): DarkShopV2Service {
  return new DarkShopV2Service({ apiKey });
}

export default DarkShopV2Service;
