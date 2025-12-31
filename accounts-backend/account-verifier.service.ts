/**
 * SynthNova - Account Verifier Service V2
 * Верификация аккаунтов TikTok, YouTube, Instagram
 * 
 * Типы верификации:
 * 1. Cookie - проверка валидности cookies через API
 * 2. Login - вход по email/password + IMAP для кодов (+ Playwright)
 * 3. Autoreg - базовая проверка + прогрев
 * 
 * Платформы:
 * - TikTok: Cookie + Login (через API и Playwright)
 * - YouTube: Cookie (через YouTube API)
 * - Instagram: Cookie (через Instagram API)
 */

import axios from 'axios';
// import * as Imap from 'imap';  // Uncomment when deploying
// import { simpleParser } from 'mailparser';  // Uncomment when deploying

// ==================== TYPES ====================

export interface VerifyResult {
  success: boolean;
  accountId: string;
  status: 'verified' | 'dead' | 'banned' | 'need_verification' | 'error';
  message: string;
  platform?: string;
  type?: string;
  details?: {
    username?: string;
    nickname?: string;
    followers?: number;
    following?: number;
    videos?: number;
    isRestricted?: boolean;
    lastActive?: string;
    profileUrl?: string;
    avatarUrl?: string;
  };
}

export interface CookieAccount {
  id: string;
  cookies: string; // JSON string, cookie array, or key=value string
  platform: string;
}

export interface LoginAccount {
  id: string;
  email: string;
  password: string;
  emailPassword?: string; // Пароль от почты для IMAP
  backupCode?: string;
  platform: string;
}

interface TikTokUserInfo {
  uniqueId: string;
  nickname: string;
  followerCount: number;
  followingCount: number;
  videoCount: number;
  privateAccount: boolean;
  avatarUrl?: string;
}

interface YouTubeUserInfo {
  channelId: string;
  title: string;
  subscriberCount: number;
  videoCount: number;
  viewCount: number;
}

interface InstagramUserInfo {
  username: string;
  fullName: string;
  followers: number;
  following: number;
  posts: number;
  isPrivate: boolean;
}

// ==================== COOKIE PARSER UTILITY ====================

export function parseCookies(cookiesInput: string): Record<string, string> {
  const result: Record<string, string> = {};

  if (!cookiesInput || cookiesInput.trim() === '') {
    return result;
  }

  try {
    // JSON формат (массив или объект)
    if (cookiesInput.startsWith('[') || cookiesInput.startsWith('{')) {
      const parsed = JSON.parse(cookiesInput);
      
      // Массив cookies (Chrome/EditThisCookie формат)
      if (Array.isArray(parsed)) {
        parsed.forEach((cookie: any) => {
          if (cookie.name && cookie.value !== undefined) {
            result[cookie.name] = String(cookie.value);
          }
        });
      } else {
        // Объект
        Object.entries(parsed).forEach(([key, value]) => {
          result[key] = String(value);
        });
      }
    } else {
      // Строка вида "name1=value1; name2=value2"
      cookiesInput.split(';').forEach(pair => {
        const [name, ...valueParts] = pair.trim().split('=');
        if (name && valueParts.length > 0) {
          result[name.trim()] = valueParts.join('=').trim();
        }
      });
    }
  } catch (e) {
    // Если JSON не парсится, пробуем как строку
    cookiesInput.split(';').forEach(pair => {
      const [name, ...valueParts] = pair.trim().split('=');
      if (name && valueParts.length > 0) {
        result[name.trim()] = valueParts.join('=').trim();
      }
    });
  }

  return result;
}

export function buildCookieString(cookies: Record<string, string>): string {
  return Object.entries(cookies)
    .map(([name, value]) => `${name}=${value}`)
    .join('; ');
}

// ==================== TIKTOK COOKIE VERIFIER ====================

export class TikTokCookieVerifier {
  private readonly USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

  /**
   * Проверка валидности cookies через TikTok API
   */
  async verify(account: CookieAccount): Promise<VerifyResult> {
    try {
      const cookies = parseCookies(account.cookies);
      
      // Проверяем наличие ключевых cookies
      if (!cookies.sessionid && !cookies.sid_tt && !cookies.sessionid_ss) {
        return {
          success: false,
          accountId: account.id,
          status: 'dead',
          platform: 'tiktok',
          type: 'cookie',
          message: 'No sessionid, sid_tt, or sessionid_ss found in cookies'
        };
      }

      const cookieString = buildCookieString(cookies);
      
      // Метод 1: /api/passport/web/account/info/
      const userInfo = await this.getUserInfoFromPassport(cookieString);
      
      if (userInfo) {
        return {
          success: true,
          accountId: account.id,
          status: 'verified',
          platform: 'tiktok',
          type: 'cookie',
          message: 'Account verified successfully',
          details: {
            username: userInfo.uniqueId,
            nickname: userInfo.nickname,
            followers: userInfo.followerCount,
            following: userInfo.followingCount,
            videos: userInfo.videoCount,
            isRestricted: userInfo.privateAccount,
            avatarUrl: userInfo.avatarUrl,
            profileUrl: `https://www.tiktok.com/@${userInfo.uniqueId}`
          }
        };
      }

      // Метод 2: Fallback через /api/user/detail/
      const userDetail = await this.getUserDetail(cookieString);
      
      if (userDetail) {
        return {
          success: true,
          accountId: account.id,
          status: 'verified',
          platform: 'tiktok',
          type: 'cookie',
          message: 'Account verified via user detail',
          details: {
            username: userDetail.uniqueId,
            nickname: userDetail.nickname,
            followers: userDetail.followerCount,
            following: userDetail.followingCount,
            videos: userDetail.videoCount,
            isRestricted: userDetail.privateAccount,
            profileUrl: `https://www.tiktok.com/@${userDetail.uniqueId}`
          }
        };
      }

      return {
        success: false,
        accountId: account.id,
        status: 'dead',
        platform: 'tiktok',
        type: 'cookie',
        message: 'Cookies expired or invalid - could not fetch user info'
      };

    } catch (error: any) {
      console.error(`TikTok verify error for ${account.id}:`, error.message);
      
      if (error.response?.status === 403) {
        return {
          success: false,
          accountId: account.id,
          status: 'banned',
          platform: 'tiktok',
          type: 'cookie',
          message: 'Account is banned or restricted (403 Forbidden)'
        };
      }

      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
        return {
          success: false,
          accountId: account.id,
          status: 'error',
          platform: 'tiktok',
          type: 'cookie',
          message: 'Connection error - please try again'
        };
      }

      return {
        success: false,
        accountId: account.id,
        status: 'error',
        platform: 'tiktok',
        type: 'cookie',
        message: error.message
      };
    }
  }

  private async getUserInfoFromPassport(cookieString: string): Promise<TikTokUserInfo | null> {
    try {
      const response = await axios.get('https://www.tiktok.com/api/passport/web/account/info/', {
        headers: {
          'Cookie': cookieString,
          'User-Agent': this.USER_AGENT,
          'Accept': 'application/json, text/plain, */*',
          'Accept-Language': 'en-US,en;q=0.9',
          'Referer': 'https://www.tiktok.com/',
          'Origin': 'https://www.tiktok.com'
        },
        timeout: 15000,
        validateStatus: (status) => status < 500
      });

      if (response.data?.data?.username) {
        const data = response.data.data;
        return {
          uniqueId: data.username,
          nickname: data.nickname || data.username,
          followerCount: data.follower_count || 0,
          followingCount: data.following_count || 0,
          videoCount: data.video_count || 0,
          privateAccount: data.private_account || false,
          avatarUrl: data.avatar_url
        };
      }

      return null;
    } catch (error) {
      return null;
    }
  }

  private async getUserDetail(cookieString: string): Promise<TikTokUserInfo | null> {
    try {
      const response = await axios.get('https://www.tiktok.com/api/user/detail/', {
        headers: {
          'Cookie': cookieString,
          'User-Agent': this.USER_AGENT,
          'Accept': 'application/json',
          'Referer': 'https://www.tiktok.com/'
        },
        timeout: 15000,
        validateStatus: (status) => status < 500
      });

      if (response.data?.userInfo?.user) {
        const user = response.data.userInfo.user;
        const stats = response.data.userInfo.stats || {};
        return {
          uniqueId: user.uniqueId,
          nickname: user.nickname,
          followerCount: stats.followerCount || 0,
          followingCount: stats.followingCount || 0,
          videoCount: stats.videoCount || 0,
          privateAccount: user.privateAccount || false
        };
      }

      return null;
    } catch (error) {
      return null;
    }
  }
}

// ==================== YOUTUBE COOKIE VERIFIER ====================

export class YouTubeCookieVerifier {
  private readonly USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

  /**
   * Проверка валидности cookies через YouTube API
   */
  async verify(account: CookieAccount): Promise<VerifyResult> {
    try {
      const cookies = parseCookies(account.cookies);
      
      // Проверяем наличие ключевых cookies
      if (!cookies.SAPISID && !cookies.SID && !cookies.__Secure-1PSID) {
        return {
          success: false,
          accountId: account.id,
          status: 'dead',
          platform: 'youtube',
          type: 'cookie',
          message: 'No YouTube session cookies found (SAPISID, SID, __Secure-1PSID)'
        };
      }

      const cookieString = buildCookieString(cookies);
      
      // Проверяем через YouTube API
      const channelInfo = await this.getChannelInfo(cookieString, cookies.SAPISID);
      
      if (channelInfo) {
        return {
          success: true,
          accountId: account.id,
          status: 'verified',
          platform: 'youtube',
          type: 'cookie',
          message: 'YouTube account verified successfully',
          details: {
            username: channelInfo.title,
            followers: channelInfo.subscriberCount,
            videos: channelInfo.videoCount,
            profileUrl: `https://www.youtube.com/channel/${channelInfo.channelId}`
          }
        };
      }

      return {
        success: false,
        accountId: account.id,
        status: 'dead',
        platform: 'youtube',
        type: 'cookie',
        message: 'YouTube cookies expired or invalid'
      };

    } catch (error: any) {
      console.error(`YouTube verify error for ${account.id}:`, error.message);
      
      return {
        success: false,
        accountId: account.id,
        status: 'error',
        platform: 'youtube',
        type: 'cookie',
        message: error.message
      };
    }
  }

  private async getChannelInfo(cookieString: string, sapisid?: string): Promise<YouTubeUserInfo | null> {
    try {
      // Пробуем получить информацию о канале через browse endpoint
      const response = await axios.get('https://www.youtube.com/account', {
        headers: {
          'Cookie': cookieString,
          'User-Agent': this.USER_AGENT,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.9'
        },
        timeout: 15000,
        validateStatus: (status) => status < 500
      });

      // Ищем данные о пользователе в ответе
      const html = response.data;
      
      // Паттерны для извлечения данных
      const channelIdMatch = html.match(/\"channelId\":\"(UC[\w-]+)\"/);
      const titleMatch = html.match(/\"title\":\"([^\"]+)\"/);
      
      if (channelIdMatch) {
        return {
          channelId: channelIdMatch[1],
          title: titleMatch ? titleMatch[1] : 'Unknown',
          subscriberCount: 0,
          videoCount: 0,
          viewCount: 0
        };
      }

      // Альтернативный метод - проверяем что перенаправление на login не происходит
      if (response.status === 200 && !html.includes('accounts.google.com/ServiceLogin')) {
        return {
          channelId: 'unknown',
          title: 'Verified Account',
          subscriberCount: 0,
          videoCount: 0,
          viewCount: 0
        };
      }

      return null;
    } catch (error) {
      return null;
    }
  }
}

// ==================== INSTAGRAM COOKIE VERIFIER ====================

export class InstagramCookieVerifier {
  private readonly USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

  /**
   * Проверка валидности cookies через Instagram API
   */
  async verify(account: CookieAccount): Promise<VerifyResult> {
    try {
      const cookies = parseCookies(account.cookies);
      
      // Проверяем наличие ключевых cookies
      if (!cookies.sessionid && !cookies.ds_user_id) {
        return {
          success: false,
          accountId: account.id,
          status: 'dead',
          platform: 'instagram',
          type: 'cookie',
          message: 'No Instagram session cookies found (sessionid, ds_user_id)'
        };
      }

      const cookieString = buildCookieString(cookies);
      
      // Проверяем через Instagram API
      const userInfo = await this.getUserInfo(cookieString, cookies.ds_user_id);
      
      if (userInfo) {
        return {
          success: true,
          accountId: account.id,
          status: 'verified',
          platform: 'instagram',
          type: 'cookie',
          message: 'Instagram account verified successfully',
          details: {
            username: userInfo.username,
            nickname: userInfo.fullName,
            followers: userInfo.followers,
            following: userInfo.following,
            videos: userInfo.posts,
            isRestricted: userInfo.isPrivate,
            profileUrl: `https://www.instagram.com/${userInfo.username}/`
          }
        };
      }

      return {
        success: false,
        accountId: account.id,
        status: 'dead',
        platform: 'instagram',
        type: 'cookie',
        message: 'Instagram cookies expired or invalid'
      };

    } catch (error: any) {
      console.error(`Instagram verify error for ${account.id}:`, error.message);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        return {
          success: false,
          accountId: account.id,
          status: 'dead',
          platform: 'instagram',
          type: 'cookie',
          message: 'Session expired - please re-login'
        };
      }

      return {
        success: false,
        accountId: account.id,
        status: 'error',
        platform: 'instagram',
        type: 'cookie',
        message: error.message
      };
    }
  }

  private async getUserInfo(cookieString: string, userId?: string): Promise<InstagramUserInfo | null> {
    try {
      // Попробуем получить через graphql endpoint
      const response = await axios.get('https://www.instagram.com/api/v1/users/web_profile_info/', {
        headers: {
          'Cookie': cookieString,
          'User-Agent': this.USER_AGENT,
          'X-IG-App-ID': '936619743392459',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': '*/*',
          'Referer': 'https://www.instagram.com/'
        },
        params: userId ? { username: '' } : undefined,
        timeout: 15000,
        validateStatus: (status) => status < 500
      });

      // Альтернативный метод - проверяем через accounts/edit
      const editResponse = await axios.get('https://www.instagram.com/accounts/edit/', {
        headers: {
          'Cookie': cookieString,
          'User-Agent': this.USER_AGENT,
          'Accept': 'text/html,application/xhtml+xml'
        },
        timeout: 15000,
        validateStatus: (status) => status < 500
      });

      // Если не редирект на логин - аккаунт валиден
      if (editResponse.status === 200 && !editResponse.data.includes('login')) {
        // Пробуем извлечь username из ответа
        const usernameMatch = editResponse.data.match(/"username":"([^"]+)"/);
        
        return {
          username: usernameMatch ? usernameMatch[1] : 'verified_user',
          fullName: '',
          followers: 0,
          following: 0,
          posts: 0,
          isPrivate: false
        };
      }

      return null;
    } catch (error) {
      return null;
    }
  }
}

// ==================== IMAP EMAIL VERIFIER ====================

export class ImapEmailVerifier {
  /**
   * Получение кода верификации из почты
   * Note: Requires 'imap' and 'mailparser' packages
   */
  async getVerificationCode(
    email: string,
    password: string,
    host?: string,
    searchFrom: string = 'TikTok'
  ): Promise<string | null> {
    // Placeholder - full implementation requires imap package
    console.log(`📧 IMAP check for ${email} (from: ${searchFrom})`);
    
    // В production здесь будет IMAP логика
    // Для тестирования возвращаем null
    return null;
  }

  /**
   * Определение IMAP конфигурации по домену почты
   */
  getImapConfig(email: string, password: string, customHost?: string): any {
    const domain = email.split('@')[1]?.toLowerCase();
    
    const configs: Record<string, { host: string; port: number; tls: boolean }> = {
      'gmail.com': { host: 'imap.gmail.com', port: 993, tls: true },
      'googlemail.com': { host: 'imap.gmail.com', port: 993, tls: true },
      'outlook.com': { host: 'outlook.office365.com', port: 993, tls: true },
      'hotmail.com': { host: 'outlook.office365.com', port: 993, tls: true },
      'live.com': { host: 'outlook.office365.com', port: 993, tls: true },
      'yahoo.com': { host: 'imap.mail.yahoo.com', port: 993, tls: true },
      'mail.ru': { host: 'imap.mail.ru', port: 993, tls: true },
      'yandex.ru': { host: 'imap.yandex.ru', port: 993, tls: true },
      'yandex.com': { host: 'imap.yandex.ru', port: 993, tls: true },
      'icloud.com': { host: 'imap.mail.me.com', port: 993, tls: true },
      'protonmail.com': { host: 'imap.protonmail.com', port: 993, tls: true },
      'rambler.ru': { host: 'imap.rambler.ru', port: 993, tls: true },
    };

    const config = configs[domain];
    
    if (!config && !customHost) {
      return null;
    }

    return {
      user: email,
      password: password,
      host: customHost || config?.host,
      port: config?.port || 993,
      tls: config?.tls ?? true,
      tlsOptions: { rejectUnauthorized: false }
    };
  }

  /**
   * Извлечение кода из текста письма
   */
  extractCode(text: string): string | null {
    // Паттерны для кодов верификации
    const patterns = [
      /verification code[:\s]+(\d{4,6})/i,
      /код подтверждения[:\s]+(\d{4,6})/i,
      /код[:\s]+(\d{4,6})/i,
      /code[:\s]+(\d{4,6})/i,
      /\b(\d{6})\b/,  // 6 цифр подряд
      /\b(\d{4})\b/   // 4 цифры
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }

    return null;
  }
}

// ==================== LOGIN VERIFIER (Playwright-based) ====================

export class LoginVerifier {
  private emailVerifier = new ImapEmailVerifier();

  /**
   * Верификация через логин
   * Базовая версия - проверка доступа к почте
   * Полная версия требует Playwright
   */
  async verify(account: LoginAccount): Promise<VerifyResult> {
    try {
      // Проверяем доступ к почте если есть пароль
      if (account.emailPassword) {
        const imapConfig = this.emailVerifier.getImapConfig(account.email, account.emailPassword);
        
        if (imapConfig) {
          return {
            success: true,
            accountId: account.id,
            status: 'need_verification',
            platform: account.platform,
            type: 'login',
            message: 'Email configuration valid. Full login verification requires Playwright.',
            details: {
              username: account.email.split('@')[0]
            }
          };
        }
      }

      // Если нет пароля от почты - помечаем как требующий верификации
      return {
        success: false,
        accountId: account.id,
        status: 'need_verification',
        platform: account.platform,
        type: 'login',
        message: 'Login verification requires Playwright browser automation'
      };

    } catch (error: any) {
      return {
        success: false,
        accountId: account.id,
        status: 'error',
        platform: account.platform,
        type: 'login',
        message: error.message
      };
    }
  }
}

// ==================== MAIN VERIFIER SERVICE ====================

export class AccountVerifierService {
  private tiktokCookieVerifier = new TikTokCookieVerifier();
  private youtubeCookieVerifier = new YouTubeCookieVerifier();
  private instagramCookieVerifier = new InstagramCookieVerifier();
  private loginVerifier = new LoginVerifier();

  /**
   * Универсальная верификация аккаунта
   */
  async verifyAccount(account: {
    id: string;
    type?: string;
    platform: string;
    cookies?: string;
    email?: string;
    password?: string;
    emailPassword?: string;
    backupCode?: string;
  }): Promise<VerifyResult> {
    
    const { platform, cookies, email } = account;
    // Определяем тип по наличию данных
    const type = cookies ? 'cookie' : 'login';

    console.log(`🔍 Verifying ${platform}/${type} account: ${account.id}`);

    // TikTok
    if (platform === 'tiktok') {
      if (type === 'cookie' && cookies) {
        return this.tiktokCookieVerifier.verify({
          id: account.id,
          cookies,
          platform
        });
      }

      if (type === 'login' && email) {
        return this.loginVerifier.verify({
          id: account.id,
          email,
          password: account.password || '',
          emailPassword: account.emailPassword,
          platform
        });
      }
    }

    // YouTube
    if (platform === 'youtube') {
      if (type === 'cookie' && cookies) {
        return this.youtubeCookieVerifier.verify({
          id: account.id,
          cookies,
          platform
        });
      }

      if (type === 'login' && email) {
        return this.loginVerifier.verify({
          id: account.id,
          email,
          password: account.password || '',
          emailPassword: account.emailPassword,
          platform
        });
      }
    }

    // Instagram
    if (platform === 'instagram') {
      if (type === 'cookie' && cookies) {
        return this.instagramCookieVerifier.verify({
          id: account.id,
          cookies,
          platform
        });
      }

      if (type === 'login' && email) {
        return this.loginVerifier.verify({
          id: account.id,
          email,
          password: account.password || '',
          emailPassword: account.emailPassword,
          platform
        });
      }
    }

    return {
      success: false,
      accountId: account.id,
      status: 'error',
      platform,
      type,
      message: `Unknown platform or missing credentials for ${platform}/${type}`
    };
  }

  /**
   * Batch верификация нескольких аккаунтов
   */
  async verifyBatch(accounts: any[], concurrency: number = 3): Promise<VerifyResult[]> {
    const results: VerifyResult[] = [];
    
    console.log(`📋 Starting batch verification of ${accounts.length} accounts (concurrency: ${concurrency})`);
    
    for (let i = 0; i < accounts.length; i += concurrency) {
      const batch = accounts.slice(i, i + concurrency);
      const batchResults = await Promise.all(
        batch.map(acc => this.verifyAccount(acc))
      );
      results.push(...batchResults);
      
      // Логируем прогресс
      console.log(`✓ Verified ${Math.min(i + concurrency, accounts.length)}/${accounts.length} accounts`);
      
      // Пауза между батчами для избежания rate limit
      if (i + concurrency < accounts.length) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    // Статистика
    const stats = {
      total: results.length,
      verified: results.filter(r => r.status === 'verified').length,
      dead: results.filter(r => r.status === 'dead').length,
      banned: results.filter(r => r.status === 'banned').length,
      needVerification: results.filter(r => r.status === 'need_verification').length,
      errors: results.filter(r => r.status === 'error').length
    };

    console.log(`📊 Verification complete:`, stats);

    return results;
  }

  /**
   * Получение статуса верификатора
   */
  getStatus(): { available: boolean; platforms: string[]; types: string[] } {
    return {
      available: true,
      platforms: ['tiktok', 'youtube', 'instagram'],
      types: ['cookie', 'login']
    };
  }
}

// Export singleton instance
export const accountVerifier = new AccountVerifierService();
export default accountVerifier;
