import { WebDriver, WebElement } from "selenium-webdriver";

export interface Credentials {
  username: string;
  password: string;
  email: string;
  email_password: string;
  cookies_string: string;
  cookies: Cookie[];
}

export interface Cookie {
  name: string;
  value: string;
  domain: string;
  path?: string;
  expirationDate?: number;
  secure?: boolean;
  httpOnly?: boolean;
}

export async function randomDelay(
  minMs: number = 1000,
  maxMs: number = 3000
): Promise<void> {
  const delay = Math.random() * (maxMs - minMs) + minMs;
  await new Promise((resolve) => setTimeout(resolve, delay));
}

export async function humanLikeTyping(
  element: WebElement,
  text: string,
  minDelay: number = 80,
  maxDelay: number = 250
): Promise<void> {
  await element.click();
  await randomDelay(500, 1200);

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    await element.sendKeys(char);

    let delay: number;
    if (i > 0 && Math.random() < 0.1) {
      delay = Math.random() * (600 - 300) + 300;
    } else {
      delay = Math.random() * (maxDelay - minDelay) + minDelay;
    }
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  await randomDelay(800, 1500);
}

export async function humanLikeClick(
  driver: WebDriver,
  element: WebElement
): Promise<void> {
  await randomDelay(500, 1500);

  const actions = driver.actions({ async: true });
  await actions.move({ origin: element }).perform();

  await randomDelay(200, 500);

  await element.click();

  await randomDelay(300, 800);
}

export function normalizeCookie(cookie: any): Cookie {
  const normalized: Cookie = {
    name: cookie.name,
    value: cookie.value,
    domain: cookie.domain || ".youtube.com",
  };

  if (cookie.path) {
    normalized.path = cookie.path;
  }

  if (cookie.expirationDate) {
    normalized.expirationDate = Math.floor(cookie.expirationDate);
  } else if (cookie.expiry) {
    normalized.expirationDate = Math.floor(cookie.expiry);
  }

  if (cookie.secure !== undefined) {
    normalized.secure = cookie.secure;
  }

  if (cookie.httpOnly !== undefined) {
    normalized.httpOnly = cookie.httpOnly;
  }

  return normalized;
}

export function parseCookies(cookieString: string): Cookie[] {
  if (!cookieString || !cookieString.trim()) {
    return [];
  }

  // Пробуем распарсить как JSON массив
  try {
    const parsed = JSON.parse(cookieString);
    if (Array.isArray(parsed)) {
      return parsed.map(item => normalizeCookie(item));
    }
  } catch (e) {
    // Не JSON, продолжаем
  }

  const cookies: Cookie[] = [];
  const cookiePairs = cookieString.split(/;\s*/);

  for (const pair of cookiePairs) {
    if (!pair.includes("=")) {
      continue;
    }

    const firstEqualIndex = pair.indexOf("=");
    const name = pair.substring(0, firstEqualIndex).trim();
    const value = pair.substring(firstEqualIndex + 1).trim();

    if (!name || !value) {
      continue;
    }

    const cookie: Cookie = {
      name,
      value,
      domain: ".youtube.com",
    };
    cookies.push(cookie);
  }

  return cookies;
}

export function parseCredentials(credString: string): Credentials {
  const trimmed = credString.trim();
  
  if (!trimmed) {
    throw new Error("Пустая строка учетных данных");
  }

  // Если это просто JSON с куками
  if (trimmed.startsWith("[")) {
    return {
      username: "",
      password: "",
      email: "",
      email_password: "",
      cookies_string: trimmed,
      cookies: parseCookies(trimmed),
    };
  }

  // Проверяем формат email:password (может содержать : в пароле)
  if (trimmed.includes(":") && !trimmed.includes("|")) {
    const firstColonIndex = trimmed.indexOf(":");
    const email = trimmed.substring(0, firstColonIndex).trim();
    const password = trimmed.substring(firstColonIndex + 1).trim();
    
    return {
      username: email,
      password: password,
      email: email,
      email_password: password,
      cookies_string: "",
      cookies: [],
    };
  }

  // Формат с разделителем |
  const parts = credString.split("|");

  if (parts.length < 1) {
    throw new Error(
      "Неверный формат учетных данных. Ожидается: email:password или username|password|email|email_password|cookies или просто cookies в JSON"
    );
  }

  const credentials: Credentials = {
    username: parts[0] || "",
    password: parts[1] || "",
    email: parts[2] || parts[0] || "",
    email_password: parts.length > 3 ? parts[3] : parts[1] || "",
    cookies_string: parts.length > 4 ? parts[4] : "",
    cookies: [],
  };

  credentials.cookies = parseCookies(credentials.cookies_string);

  return credentials;
}

export function log(message: string): void {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

export function hoursToMs(hours: number): number {
  return Math.floor(hours * 60 * 60 * 1000);
}

export function hoursToSeconds(hours: number): number {
  return Math.floor(hours * 60 * 60);
}

/**
 * Извлекает уникальный идентификатор аккаунта из cookies
 */
export function extractSessionId(cookies: Cookie[] | string): string | null {
  let cookieArray: Cookie[];
  
  if (typeof cookies === 'string') {
    try {
      cookieArray = JSON.parse(cookies);
    } catch (e) {
      cookieArray = parseCookies(cookies);
    }
  } else {
    cookieArray = cookies;
  }
  
  // Для YouTube/Google ищем специфичные куки
  const sessionCookieNames = [
    'SSID', 'SID', 'HSID', 'APISID', 'SAPISID', // Google auth cookies
    '__Secure-1PSID', '__Secure-3PSID', // Secure Google cookies
    'LOGIN_INFO', // YouTube login info
  ];
  
  for (const name of sessionCookieNames) {
    const cookie = cookieArray.find(c => c.name === name);
    if (cookie) return cookie.value;
  }
  
  // Если ничего не нашли, генерируем ID из всех cookies
  if (cookieArray.length > 0) {
    const combinedValue = cookieArray
      .map(c => `${c.name}=${c.value}`)
      .sort()
      .join('|');
    return combinedValue.substring(0, 100);
  }
  
  return null;
}

/**
 * Генерирует уникальный User-Agent на основе sessionId
 */
export function generateUserAgent(sessionId: string): string {
  let hash = 0;
  for (let i = 0; i < sessionId.length; i++) {
    hash = ((hash << 5) - hash) + sessionId.charCodeAt(i);
    hash = hash & hash;
  }
  
  const absHash = Math.abs(hash);
  
  const chromeVersions = ['120.0.6099.109', '121.0.6167.85', '122.0.6261.94', '123.0.6312.58', '124.0.6367.60'];
  const chromeVersion = chromeVersions[absHash % chromeVersions.length];
  
  const windowsVersions = [
    'Windows NT 10.0; Win64; x64',
    'Windows NT 11.0; Win64; x64',
  ];
  const windowsVersion = windowsVersions[absHash % windowsVersions.length];
  
  return `Mozilla/5.0 (${windowsVersion}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${chromeVersion} Safari/537.36`;
}

/**
 * Получает информацию об аккаунте из cookies
 */
export function getAccountInfoFromCookies(cookies: Cookie[] | string): {
  sessionId: string | null;
  userAgent: string | null;
} {
  const sessionId = extractSessionId(cookies);
  const userAgent = sessionId ? generateUserAgent(sessionId) : null;
  
  return {
    sessionId,
    userAgent,
  };
}
