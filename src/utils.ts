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
      // 10% шанс
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

/**
 * Нормализует cookie объект - оставляет только поля понятные Selenium
 * Убирает лишние поля из браузерных расширений (hostOnly, storeId, id, etc)
 */
export function normalizeCookie(cookie: any): Cookie {
  const normalized: Cookie = {
    name: cookie.name,
    value: cookie.value,
    domain: cookie.domain || ".tiktok.com",
  };

  // Добавляем path если есть
  if (cookie.path) {
    (normalized as any).path = cookie.path;
  }

  // Добавляем expiry если есть (expirationDate или expiry)
  if (cookie.expirationDate) {
    (normalized as any).expiry = Math.floor(cookie.expirationDate);
  } else if (cookie.expiry) {
    (normalized as any).expiry = Math.floor(cookie.expiry);
  }

  return normalized;
}

export function parseCookies(cookieString: string): Cookie[] {
  if (!cookieString || !cookieString.trim()) {
    return [];
  }

  // Пробуем распарсить как JSON массив (формат из браузерных расширений)
  try {
    const parsed = JSON.parse(cookieString);
    if (Array.isArray(parsed)) {
      // Формат: [{name, value, domain, ...}, ...]
      // Нормализуем каждую cookie - убираем лишние поля
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
      domain: ".tiktok.com",
    };
    cookies.push(cookie);
  }

  return cookies;
}

export function parseCredentials(credString: string): Credentials {
  const parts = credString.split("|");

  if (parts.length < 3) {
    throw new Error(
      "Неверный формат учетных данных. Ожидается: username|password|email|email_password|cookies"
    );
  }

  const credentials: Credentials = {
    username: parts[0],
    password: parts[1],
    email: parts[2],
    email_password: parts.length > 3 ? parts[3] : "",
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
 * Вычисляет следующий доступный 10-минутный слот
 * Добавляет 2 часа к текущему времени, затем округляет к БЛИЖАЙШЕМУ 10-минутному интервалу
 * 
 * Примеры:
 * - 14:31 + 2ч = 16:31 → 16:30 (ближайший)
 * - 14:55 + 2ч = 16:55 → 17:00 (ближайший)
 * - 14:44 + 2ч = 16:44 → 16:40 (ближайший)
 * 
 * Гарантирует задержку ~2 часа
 */
export function getNext10MinSlot(fromTime: Date = new Date()): Date {
  // Добавляем 2 часа
  const timeAfter2Hours = new Date(fromTime.getTime() + 2 * 60 * 60 * 1000);
  
  // Округляем к ближайшему 10-минутному интервалу
  const minutes = timeAfter2Hours.getMinutes();
  const remainder = minutes % 10;
  
  if (remainder === 0) {
    // Уже на 10-минутном интервале
    return timeAfter2Hours;
  } else if (remainder < 5) {
    // Округляем вниз (1-4 минуты остаток → вниз)
    const minutesToSubtract = remainder;
    return new Date(timeAfter2Hours.getTime() - minutesToSubtract * 60 * 1000);
  } else {
    // Округляем вверх (5-9 минут остаток → вверх)
    const minutesToAdd = 10 - remainder;
    return new Date(timeAfter2Hours.getTime() + minutesToAdd * 60 * 1000);
  }
}

/**
 * Генерирует массив временных слотов для батча видео
 * Каждое следующее видео планируется через ~2 часа на ближайший 10-минутный слот
 * 
 * @param videoCount - количество видео
 * @param startTime - время начала (по умолчанию текущее время)
 * @returns массив объектов Date для каждого видео
 */
export function generate10MinSlots(videoCount: number, startTime: Date = new Date()): Date[] {
  const slots: Date[] = [];
  let currentTime = startTime;
  
  for (let i = 0; i < videoCount; i++) {
    const nextSlot = getNext10MinSlot(currentTime);
    slots.push(nextSlot);
    currentTime = nextSlot;
  }
  
  return slots;
}

/**
 * Извлекает уникальный идентификатор аккаунта из cookies
 * Приоритет: sessionid -> sid_guard -> uid_tt -> msToken
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
  
  // Пробуем sessionid (основной)
  let sessionCookie = cookieArray.find(c => c.name === 'sessionid' || c.name === 'sessionid_ss');
  if (sessionCookie) return sessionCookie.value;
  
  // Пробуем sid_guard (альтернативный идентификатор сессии)
  sessionCookie = cookieArray.find(c => c.name === 'sid_guard');
  if (sessionCookie) return sessionCookie.value;
  
  // Пробуем uid_tt (User ID)
  sessionCookie = cookieArray.find(c => c.name === 'uid_tt' || c.name === 'uid_tt_ss');
  if (sessionCookie) return sessionCookie.value;
  
  // Пробуем msToken (токен сессии)
  sessionCookie = cookieArray.find(c => c.name === 'msToken');
  if (sessionCookie) return sessionCookie.value;
  
  // Если ничего не нашли, генерируем ID из всех cookies
  if (cookieArray.length > 0) {
    const combinedValue = cookieArray
      .map(c => `${c.name}=${c.value}`)
      .sort()
      .join('|');
    return combinedValue.substring(0, 100); // Ограничиваем длину
  }
  
  return null;
}

/**
 * Извлекает TikTok UID из cookies
 */
export function extractTikTokUid(cookies: Cookie[] | string): string | null {
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
  
  const uidCookie = cookieArray.find(c => c.name === 'uid_tt' || c.name === 'uid_tt_ss');
  return uidCookie ? uidCookie.value : null;
}

/**
 * Генерирует уникальный реалистичный User-Agent на основе sessionId
 * Использует детерминированную генерацию - один и тот же sessionId всегда дает один User-Agent
 */
export function generateUserAgent(sessionId: string): string {
  // Создаем hash из sessionId для детерминированного выбора параметров
  let hash = 0;
  for (let i = 0; i < sessionId.length; i++) {
    hash = ((hash << 5) - hash) + sessionId.charCodeAt(i);
    hash = hash & hash; // Convert to 32bit integer
  }
  
  const absHash = Math.abs(hash);
  
  // Варианты Chrome версий (последние стабильные)
  const chromeVersions = ['120.0.6099.109', '121.0.6167.85', '122.0.6261.94', '123.0.6312.58', '124.0.6367.60'];
  const chromeVersion = chromeVersions[absHash % chromeVersions.length];
  
  // Варианты Windows версий
  const windowsVersions = [
    'Windows NT 10.0; Win64; x64',
    'Windows NT 11.0; Win64; x64',
  ];
  const windowsVersion = windowsVersions[absHash % windowsVersions.length];
  
  // Варианты разрешений экрана (для WebGL fingerprint)
  const screenResolutions = [
    '1920x1080',
    '2560x1440',
    '1366x768',
    '1536x864',
    '1440x900',
  ];
  const resolution = screenResolutions[(absHash >> 2) % screenResolutions.length];
  
  return `Mozilla/5.0 (${windowsVersion}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${chromeVersion} Safari/537.36`;
}

/**
 * Получает информацию об аккаунте из cookies
 */
export function getAccountInfoFromCookies(cookies: Cookie[] | string): {
  sessionId: string | null;
  tiktokUid: string | null;
  userAgent: string | null;
} {
  const sessionId = extractSessionId(cookies);
  const tiktokUid = extractTikTokUid(cookies);
  const userAgent = sessionId ? generateUserAgent(sessionId) : null;
  
  return {
    sessionId,
    tiktokUid,
    userAgent,
  };
}
