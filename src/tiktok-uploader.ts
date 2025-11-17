import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  Builder,
  WebDriver,
  By,
  until,
  Key,
  WebElement,
} from "selenium-webdriver";
import { Options as ChromeOptions } from "selenium-webdriver/chrome";
import {
  Credentials,
  randomDelay,
  humanLikeTyping,
  humanLikeClick,
  log,
  hoursToSeconds,
} from "./utils";

export interface VideoConfig {
  videoPath: string;
  caption: string;
  hashtags: string[];
}

export class TikTokUploader {
  private credentials: Credentials;
  private headless: boolean;
  private driver: WebDriver | null = null;
  private isLoggedIn: boolean = false;
  private proxy: string | null = null;
  private proxyExtensionPath: string | null = null;
  private userDataDir: string | null = null;
  private screenshotDir: string;
  private sessionId: string;
  private userAgent: string | null = null;

  constructor(
    credentials: Credentials,
    headless: boolean = false,
    proxy?: string,
    userAgent?: string
  ) {
    this.credentials = credentials;
    this.headless = headless;
    this.proxy = proxy || null;
    this.userAgent = userAgent || null;

    // Уникальная директория для скриншотов этой сессии
    this.sessionId = `${Date.now()}-${Math.random().toString(36).substring(2)}`;
    this.screenshotDir = path.join(
      __dirname,
      "..",
      "screenshots",
      this.sessionId
    );

    // Создаем директорию для скриншотов
    if (!fs.existsSync(this.screenshotDir)) {
      fs.mkdirSync(this.screenshotDir, { recursive: true });
    }
  }

  async initialize(): Promise<void> {
    log("🚀 Инициализация браузера...");

    const options = new ChromeOptions();

    log(`🔍 Headless режим: ${this.headless}`);

    const uniqueId = `${process.pid}-${Date.now()}-${Math.random()
      .toString(36)
      .substring(2)}`;
    this.userDataDir = path.join(os.tmpdir(), `chrome-profile-${uniqueId}`);
    fs.mkdirSync(this.userDataDir, { recursive: true, mode: 0o755 });
    options.addArguments(`--user-data-dir=${this.userDataDir}`);
    log(`📁 Создан временный профиль: ${this.userDataDir}`);

    if (this.headless) {
      options.addArguments("--headless=new");
    }

    options.addArguments("--disable-software-rasterizer");

    options.addArguments(
      "--disable-features=ExtensionManifestV2Unsupported,ExtensionManifestV2Disabled"
    );

    options.addArguments("--no-sandbox");
    options.addArguments("--disable-setuid-sandbox");
    options.addArguments("--disable-blink-features=AutomationControlled");
    options.addArguments("--disable-infobars");
    options.addArguments("--disable-dev-shm-usage");
    options.addArguments("--disable-gpu");
    options.addArguments("--window-size=1920,1080");
    options.addArguments("--window-position=0,0");
    options.addArguments("--lang=en");

    options.addArguments("--disable-features=IsolateOrigins,site-per-process");
    options.addArguments("--allow-running-insecure-content");

    const userAgent =
      this.userAgent ||
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

    options.addArguments(`--user-agent=${userAgent}`);
    log(`🌐 User-Agent: ${userAgent.substring(0, 50)}...`);

    options.excludeSwitches("enable-automation", "enable-logging");
    options.addArguments("--disable-blink-features=AutomationControlled");

    if (this.proxy) {
      await this.setupProxy(options);
    }

    this.driver = await new Builder()
      .forBrowser("chrome")
      .setChromeOptions(options)
      .build();

    await this.driver.executeScript(`
      // Скрываем webdriver
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
      });
      
      // Эмулируем плагины
      Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
      });
      
      // Устанавливаем языки
      Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
      });
      
      // Скрываем headless
      Object.defineProperty(navigator, 'maxTouchPoints', {
        get: () => 1
      });
      
      // Переопределяем chrome для скрытия автоматизации
      if (!window.chrome) {
        window.chrome = {};
      }
      window.chrome.runtime = {};
      
      // Удаляем признаки автоматизации из свойств
      delete navigator.__proto__.webdriver;
      
      // Переопределяем permissions
      const originalQuery = window.navigator.permissions.query;
      window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
          Promise.resolve({ state: Notification.permission }) :
          originalQuery(parameters)
      );
    `);

    log("✅ Браузер успешно инициализирован");

    if (this.credentials.cookies && this.credentials.cookies.length > 0) {
      log("🍪 Добавляем куки в браузер...");

      await this.driver.get("https://www.tiktok.com/");
      await randomDelay(2000, 3000);

      let cookiesAdded = 0;
      for (const cookie of this.credentials.cookies) {
        try {
          log(`🔍 Исходная кука ${cookie.name}: домен="${cookie.domain}"`);

          const cleanCookie: any = {
            name: cookie.name,
            value: cookie.value,
            domain: ".tiktok.com",
            path: "/",
            secure: true,
            httpOnly: false,
          };

          log(
            `✅ Нормализованная кука ${cookie.name}: домен="${cleanCookie.domain}"`
          );

          await this.driver.manage().addCookie(cleanCookie);
          cookiesAdded++;
          log(`✅ Кука ${cookie.name} успешно добавлена`);
        } catch (e: any) {
          log(`⚠️ Не удалось добавить куку ${cookie.name}: ${e.message || e}`);
        }
      }

      log(
        `✅ Добавлено ${cookiesAdded} кук из ${this.credentials.cookies.length}`
      );

      if (cookiesAdded === 0) {
        throw new Error(
          "❌ Ни одна кука не была добавлена! " +
            "Куки невалидны или несовместимы с текущим доменом. " +
            "Проверьте формат кук в БД."
        );
      }

      await this.driver.navigate().refresh();
      await randomDelay(2000, 3000);
    }
  }

  private async takeScreenshot(name: string): Promise<void> {
    if (!this.driver) return;

    try {
      const screenshot = await this.driver.takeScreenshot();
      const screenshotPath = path.join(this.screenshotDir, `${name}.png`);
      fs.writeFileSync(screenshotPath, screenshot, "base64");
      log(`📸 Скриншот: ${this.sessionId}/${name}.png`);
    } catch (e) {
      log(`⚠️ Ошибка скриншота ${name}: ${e}`);
    }
  }

  private async removeCookieBanner(): Promise<void> {
    if (!this.driver) return;

    try {
      log("🍪 Удаляем cookie banner...");

      try {
        await this.driver.executeScript(`
          const banner = document.querySelector('tiktok-cookie-banner');
          if (banner && banner.shadowRoot) {
            const button = banner.shadowRoot.querySelector('button');
            if (button) button.click();
          }
        `);
        await randomDelay(1000, 1500);
      } catch (e) {}

      await this.driver.executeScript(`
        const banner = document.querySelector('tiktok-cookie-banner');
        if (banner) {
          banner.remove();
          console.log('Cookie banner removed');
        }
      `);

      log("✅ Cookie banner удален");
      await randomDelay(1000, 1500);
    } catch (e) {
      log(`⚠️ Cookie banner не найден или уже удален: ${e}`);
    }
  }

  private async closeAllModalsAggressively(): Promise<void> {
    if (!this.driver) return;

    try {
      log("🧹 Агрессивная очистка модальных окон...");

      await this.driver.executeScript(`
        const modals = document.querySelectorAll('.TUXModal, .common-modal, [role="dialog"]');
        modals.forEach(m => m.remove());
        
        const overlays = document.querySelectorAll('.TUXModal-overlay, .modal-overlay, [class*="overlay"]');
        overlays.forEach(o => o.remove());
        
        const cookieBanner = document.querySelector('tiktok-cookie-banner');
        if (cookieBanner) {
          cookieBanner.remove();
        }
        
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
      `);

      await randomDelay(500, 1000);
      log("✅ Модальные окна очищены");
    } catch (e) {
      log(`⚠️ Ошибка агрессивной очистки: ${e}`);
    }
  }

  async login(): Promise<void> {
    if (!this.driver) {
      throw new Error("Браузер не инициализирован");
    }

    log("🔐 Начинаем процесс авторизации...");

    try {
      if (this.credentials.cookies && this.credentials.cookies.length > 0) {
        log("🍪 Авторизация через куки...");

        await this.driver.get("https://www.tiktok.com/");
        await randomDelay(3000, 5000);

        await this.driver.get("https://www.tiktok.com/creator-center/upload");
        await randomDelay(3000, 5000);

        const currentUrl = await this.driver.getCurrentUrl();
        log(currentUrl);

        if (
          !currentUrl.includes("/login") &&
          (currentUrl.includes("creator-center") ||
            currentUrl.includes("tiktokstudio"))
        ) {
          log("✅ Успешная авторизация через куки!");
          this.isLoggedIn = true;
          return;
        } else {
          throw new Error(
            "❌ Не удалось авторизоваться через куки. " +
              "Куки недействительны или истекли."
          );
        }
      }

      log("🔐 Авторизация через логин и пароль...");

      log("🌐 Открываем главную страницу TikTok...");
      await this.driver.get("https://www.tiktok.com/");
      await randomDelay(5000, 8000);

      await this.driver.executeScript("window.scrollTo(0, 500);");
      await randomDelay(2000, 3000);
      await this.driver.executeScript("window.scrollTo(0, 0);");
      await randomDelay(2000, 3000);

      log("🔐 Переходим на страницу входа...");
      await this.driver.get(
        "https://www.tiktok.com/login/phone-or-email/email"
      );
      await randomDelay(3000, 5000);

      let currentUrl = await this.driver.getCurrentUrl();
      if (!currentUrl.includes("/login")) {
        log("✅ Уже авторизованы");
        this.isLoggedIn = true;
        return;
      }

      log(`📧 Вводим email: ${this.credentials.email}`);

      const emailInput = await this.driver.wait(
        until.elementLocated(By.name("username")),
        10000
      );

      await humanLikeTyping(emailInput, this.credentials.username);

      log("🔑 Вводим пароль...");

      const passwordInput = await this.driver.wait(
        until.elementLocated(By.css('input[type="password"]')),
        10000
      );

      await humanLikeTyping(passwordInput, this.credentials.password);

      await randomDelay(1000, 2000);

      log("👆 Нажимаем кнопку входа...");

      const loginButtonSelectors = [
        'button[type="submit"]',
        'button[data-e2e="login-button"]',
        "button.tiktok-btn",
      ];

      let buttonFound = false;
      for (const selector of loginButtonSelectors) {
        try {
          const button = await this.driver.findElement(By.css(selector));
          await humanLikeClick(this.driver, button);
          buttonFound = true;
          break;
        } catch (e) {
          continue;
        }
      }

      if (!buttonFound) {
        await passwordInput.sendKeys(Key.RETURN);
      }

      await randomDelay(3000, 5000);

      log("⏳ Ожидаем завершения входа...");

      try {
        await this.driver.wait(async () => {
          const url = await this.driver!.getCurrentUrl();
          return !url.includes("/login") && !url.includes("/passport");
        }, 30000);
      } catch (e) {}

      const finalUrl = await this.driver.getCurrentUrl();

      if (finalUrl.includes("/login") || finalUrl.includes("/passport")) {
        log("⚠️ Возможно требуется ручное подтверждение (капча/2FA)");
        log("⏳ Ожидаем 60 секунд для ручного решения...");
        await new Promise((resolve) => setTimeout(resolve, 60000));
      }

      const checkUrl = await this.driver.getCurrentUrl();
      if (checkUrl.includes("/login")) {
        throw new Error(
          "Не удалось войти в аккаунт. Проверьте учетные данные."
        );
      }

      log("✅ Успешная авторизация!");
      this.isLoggedIn = true;

      await randomDelay(3000, 5000);
    } catch (error) {
      log(`❌ Ошибка при авторизации: ${error}`);
      throw error;
    }
  }

  async uploadVideo(videoConfig: VideoConfig): Promise<string> {
    if (!this.driver || !this.isLoggedIn) {
      throw new Error("Необходимо сначала авторизоваться");
    }

    const { videoPath, caption, hashtags } = videoConfig;

    log(`📹 Начинаем загрузку видео: ${videoPath}`);

    try {
      const absVideoPath = path.resolve(videoPath);
      if (!fs.existsSync(absVideoPath)) {
        throw new Error(`Видео файл не найден: ${absVideoPath}`);
      }

      log("🌐 Переходим на страницу загрузки...");
      await this.driver.get("https://www.tiktok.com/creator-center/upload");
      await randomDelay(3000, 5000);

      await this.removeCookieBanner();

      log("📤 Загружаем видео файл...");

      const fileInputSelectors = [
        'input[type="file"]',
        'input[accept*="video"]',
        '[data-e2e="upload-input"]',
      ];

      let fileInput: WebElement | null = null;
      for (const selector of fileInputSelectors) {
        try {
          fileInput = await this.driver.findElement(By.css(selector));
          if (fileInput) {
            break;
          }
        } catch (e) {
          continue;
        }
      }

      if (!fileInput) {
        throw new Error("Не найден элемент для загрузки файла");
      }

      await fileInput.sendKeys(absVideoPath);
      log("✅ Файл отправлен, ожидаем обработку видео...");

      await randomDelay(3000, 5000);

      try {
        const errorElement = await this.driver.findElement(
          By.xpath(
            "//*[contains(text(), \"Couldn't upload\") or contains(text(), 'Upload failed') or contains(text(), 'Try again later')]"
          )
        );

        if (await errorElement.isDisplayed()) {
          const errorText = await errorElement.getText();
          log(`❌ TikTok отклонил видео: ${errorText}`);
          throw new Error(
            `TikTok отклонил видео при загрузке: "${errorText}". ` +
              `Возможные причины: 1) Headless режим детектируется - попробуйте headless=false, ` +
              `2) Формат/кодек видео не поддерживается, 3) Антибот защита TikTok`
          );
        }
      } catch (e: any) {
        if (e.message && e.message.includes("TikTok отклонил")) {
          throw e;
        }
      }

      log("⏳ Ожидаем подтверждение обработки видео...");
      await randomDelay(10000, 15000);

      await this.closeAllModalsAggressively();

      log("✍️ Добавляем описание и хештеги...");

      await this.closeAllModalsAggressively();

      const captionSelectors = [
        'div[contenteditable="true"]',
        'textarea[placeholder*="description"]',
        '[data-e2e="caption-input"]',
        "div.DraftEditor-editorContainer",
      ];

      let captionFound = false;
      for (const selector of captionSelectors) {
        try {
          const captionElement = await this.driver.wait(
            until.elementLocated(By.css(selector)),
            10000
          );

          await this.driver.executeScript(
            'arguments[0].scrollIntoView({behavior: "smooth", block: "center"});',
            captionElement
          );
          await randomDelay(1000, 1500);

          try {
            await humanLikeClick(this.driver, captionElement);
          } catch (e) {
            log("⚠️ Обычный клик не сработал, используем JavaScript...");
            await this.driver.executeScript(
              "arguments[0].click();",
              captionElement
            );
          }

          await randomDelay(500, 1000);

          let currentText = "";
          try {
            currentText = (await this.driver.executeScript(
              `
              const element = arguments[0];
              if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
                return element.value || '';
              } else {
                return element.textContent || element.innerText || '';
              }
            `,
              captionElement
            )) as string;

            currentText = currentText.trim();
            log(
              `📝 Текущий текст в поле: "${currentText}" (длина: ${currentText.length})`
            );
          } catch (e) {
            log(`⚠️ Ошибка при получении текста: ${e}`);
          }

          if (currentText.length > 0) {
            log(`🧹 Удаляем ${currentText.length} символов через Backspace...`);
            let counter = 0;
            while (counter < currentText.length) {
              await captionElement.sendKeys(Key.BACK_SPACE);
              counter++;

              if (counter % 10 === 0) {
                await randomDelay(10, 50);
              }
            }
            log("✅ Поле полностью очищено");
            await randomDelay(300, 500);
          }

          await captionElement.sendKeys(caption);
          log(`✅ Описание добавлено: ${caption.substring(0, 50)}...`);
          await randomDelay(500, 1000);

          for (const tag of hashtags) {
            const cleanTag = tag.replace("#", "");

            log(`🏷️ Добавляем хэштег: #${cleanTag}`);

            await captionElement.sendKeys(` #${cleanTag}`);
            await randomDelay(800, 1500);

            try {
              await randomDelay(300, 600);

              const hashtagSelectors = [
                'div[data-e2e="search-hashtag-item"]',
                'div[role="option"]',
                'div[class*="hashtag-item"]',
                'div[class*="HashtagSuggestion"]',
                '[data-e2e="search-hashtag"] div[role="option"]',
              ];

              let hashtagSelected = false;
              for (const hashtagSelector of hashtagSelectors) {
                try {
                  const hashtagSuggestion = await this.driver.wait(
                    until.elementLocated(By.css(hashtagSelector)),
                    3000
                  );

                  if (await hashtagSuggestion.isDisplayed()) {
                    await randomDelay(300, 600);

                    try {
                      await hashtagSuggestion.click();
                      hashtagSelected = true;
                      log(
                        `✅ Хэштег #${cleanTag} выбран из списка (обычный клик)`
                      );
                    } catch (e) {
                      await this.driver.executeScript(
                        "arguments[0].click();",
                        hashtagSuggestion
                      );
                      hashtagSelected = true;
                      log(
                        `✅ Хэштег #${cleanTag} выбран из списка (JavaScript клик)`
                      );
                    }

                    await randomDelay(500, 1000);
                    break;
                  }
                } catch (e) {
                  continue;
                }
              }

              if (!hashtagSelected) {
                log(`⚠️ Автодополнение для #${cleanTag} не найдено`);
                await captionElement.sendKeys(" ");
                await randomDelay(300, 500);
              }
            } catch (e) {
              log(`⚠️ Ошибка при выборе хэштега #${cleanTag}: ${e}`);
              await captionElement.sendKeys(" ");
              await randomDelay(300, 500);
            }
          }

          captionFound = true;
          break;
        } catch (e) {
          log(`⚠️ Ошибка при работе с описанием: ${e}`);
          continue;
        }
      }

      if (!captionFound) {
        log("⚠️ Не удалось найти поле для описания");
      }

      await randomDelay(2000, 3000);

      log("🔓 Устанавливаем настройки публикации...");

      await randomDelay(2000, 3000);

      await this.closeAllModalsAggressively();

      log("🚀 Публикуем видео...");

      try {
        const publishButton = await this.driver.wait(
          until.elementLocated(By.css('button[data-e2e="post_video_button"]')),
          10000
        );

        await this.driver.executeScript(
          'arguments[0].scrollIntoView({behavior: "smooth", block: "center"});',
          publishButton
        );
        await randomDelay(1000, 1500);

        try {
          await humanLikeClick(this.driver, publishButton);
          log("✅ Кнопка публикации нажата (обычный клик)");
        } catch (e) {
          log("⚠️ Обычный клик не сработал, используем JavaScript...");
          await this.driver.executeScript(
            "arguments[0].click();",
            publishButton
          );
          log("✅ Кнопка публикации нажата (JavaScript)");
        }
      } catch (e) {
        log(`⚠️ Не удалось найти кнопку публикации: ${e}`);
        throw new Error("Не удалось найти кнопку публикации автоматически");
      }

      log("⏳ Ожидаем подтверждение публикации...");
      await randomDelay(10000, 15000);

      await this.driver.navigate().refresh();

      this.takeScreenshot(`after-publish`);

      let videoUrl = "";
      try {
        const currentUrl = await this.driver.getCurrentUrl();

        if (currentUrl.includes("tiktok.com/video/")) {
          videoUrl = currentUrl;
        } else {
          const linkSelectors = [
            'a[href*="/video/"]',
            '[data-e2e="video-link"]',
            'a[href*="/@"]',
          ];

          for (const selector of linkSelectors) {
            try {
              const linkElement = await this.driver.findElement(
                By.css(selector)
              );
              videoUrl = await linkElement.getAttribute("href");
              if (videoUrl && videoUrl.includes("tiktok.com")) {
                break;
              }
            } catch (e) {
              continue;
            }
          }
        }

        this.takeScreenshot(`after-get-video-url`);

        if (videoUrl) {
          log(`🔗 URL видео: ${videoUrl}`);
        }
      } catch (e) {
        log(`⚠️ Не удалось получить URL видео: ${e}`);
      }

      log(`✅ Видео успешно загружено: ${videoPath}`);
      return videoUrl;
    } catch (error) {
      log(`❌ Ошибка при загрузке видео: ${error}`);
      throw error;
    }
  }

  async getProfileStats(): Promise<{
    username: string;
    followers: number;
    following: number;
    likes: number;
    views: number;
  }> {
    if (!this.driver || !this.isLoggedIn) {
      log("⚠️ Браузер не инициализирован или не авторизован, возвращаем 0");
      return { username: "", followers: 0, following: 0, likes: 0, views: 0 };
    }

    try {
      log("📊 Получаем статистику профиля...");

      // Получаем username для перехода в профиль
      await this.driver.get("https://www.tiktok.com/");
      await randomDelay(3000, 5000);

      let username = "";
      const profileSelectors = [
        'a[data-e2e="nav-profile"]',
        'a[href*="/@"]',
        '[data-e2e="profile-link"]',
      ];

      for (const selector of profileSelectors) {
        try {
          const profileLink = await this.driver.findElement(By.css(selector));
          const href = await profileLink.getAttribute("href");

          if (href && href.includes("/@")) {
            const match = href.match(/@([^/?]+)/);
            if (match && match[1]) {
              username = match[1];
              log(`✅ Найден username: ${username}`);
              break;
            }
          }
        } catch (e) {
          continue;
        }
      }

      if (!username) {
        log("⚠️ Username не найден, невозможно получить статистику профиля");
        return { username: "", followers: 0, following: 0, likes: 0, views: 0 };
      }

      // Переходим в профиль
      const profileUrl = `https://www.tiktok.com/@${username}`;
      log(`🌐 Переходим на профиль: ${profileUrl}`);

      await this.driver.get(profileUrl);
      await randomDelay(3000, 5000);

      // Собираем статистику используя новые селекторы
      const stats = await this.driver.executeScript(`
        const stats = { followers: 0, following: 0, likes: 0, views: 0 };
        
        // Ищем элементы по data-e2e атрибутам
        const followingElement = document.querySelector('strong[data-e2e="following-count"]');
        const followersElement = document.querySelector('strong[data-e2e="followers-count"]');
        const likesElement = document.querySelector('strong[data-e2e="likes-count"]');
        
        if (followingElement) {
          const value = followingElement.textContent || '0';
          stats.following = parseInt(value.replace(/[^0-9]/g, ''), 10) || 0;
        }
        
        if (followersElement) {
          const value = followersElement.textContent || '0';
          stats.followers = parseInt(value.replace(/[^0-9]/g, ''), 10) || 0;
        }
        
        if (likesElement) {
          const value = likesElement.textContent || '0';
          stats.likes = parseInt(value.replace(/[^0-9]/g, ''), 10) || 0;
        }
        
        // views пока оставляем 0, так как они не отображаются на странице профиля
        stats.views = 0;
        
        return stats;
      `);

      log(`✅ Статистика профиля: ${JSON.stringify(stats)}`);

      // Возвращаем статистику с username для дальнейшего сбора просмотров
      const result = stats as {
        username: string;
        followers: number;
        following: number;
        likes: number;
        views: number;
      };

      // Добавляем username в результат (будет использован в stats.worker)
      result.username = username as string;

      return result;
    } catch (error) {
      log(`❌ Ошибка при получении статистики профиля: ${error}`);
      return { username: "", followers: 0, following: 0, likes: 0, views: 0 };
    }
  }

  private parseViewCount(viewsText: string): number {
    const text = viewsText.trim().toLowerCase();

    if (text.includes("k")) {
      const number = parseFloat(text.replace(/[^0-9.]/g, ""));
      return Math.round(number * 1000);
    } else if (text.includes("m")) {
      const number = parseFloat(text.replace(/[^0-9.]/g, ""));
      return Math.round(number * 1000000);
    } else if (text.includes("b")) {
      const number = parseFloat(text.replace(/[^0-9.]/g, ""));
      return Math.round(number * 1000000000);
    } else {
      return parseInt(text.replace(/[^0-9]/g, ""), 10) || 0;
    }
  }

  async collectVideoViews(username: string): Promise<number> {
    if (!this.driver || !this.isLoggedIn) {
      throw new Error("Необходимо сначала авторизоваться");
    }

    try {
      log(`📊 Начинаем сбор просмотров со всех видео для @${username}`);

      const profileUrl = `https://www.tiktok.com/@${username}`;
      await this.driver.get(profileUrl);
      await randomDelay(3000, 5000);

      let totalViews = 0;
      let lastHeight = 0;
      let sameHeightCount = 0;
      const MAX_SAME_HEIGHT = 3; // Если высота не меняется 3 раза подряд - достигли низа

      log(`🔄 Начинаем листать вниз для загрузки всех видео`);

      // Листаем вниз пока не достигнем низа
      while (sameHeightCount < MAX_SAME_HEIGHT) {
        // Прокручиваем вниз
        await this.driver.executeScript(
          "window.scrollTo(0, document.body.scrollHeight);"
        );
        await randomDelay(2000, 3000);

        // Проверяем текущую высоту
        const currentHeight = (await this.driver.executeScript(
          "return document.body.scrollHeight;"
        )) as number;

        if (currentHeight === lastHeight) {
          sameHeightCount++;
          log(
            `⏸️ Высота не изменилась (попытка ${sameHeightCount}/${MAX_SAME_HEIGHT})`
          );
        } else {
          sameHeightCount = 0;
          lastHeight = currentHeight;
          log(`📏 Прокрутили, текущая высота: ${currentHeight}px`);
        }
      }

      log(`✅ Достигли низа страницы, собираем просмотры`);

      const viewsElements = await this.driver.findElements(
        By.css('strong[data-e2e="video-views"]')
      );

      log(`📹 Найдено видео: ${viewsElements.length}`);

      for (const element of viewsElements) {
        try {
          const viewsText = await element.getText();
          const views = this.parseViewCount(viewsText);
          totalViews += views;
          log(`  📊 ${viewsText} -> ${views}`);
        } catch (e) {
          continue;
        }
      }

      log(
        `✅ Собрано просмотров: ${totalViews} с ${viewsElements.length} видео`
      );

      return totalViews;
    } catch (error) {
      log(`❌ Ошибка при сборе просмотров видео: ${error}`);
      return 0;
    }
  }

  async deleteAllVideos(): Promise<number> {
    if (!this.driver || !this.isLoggedIn) {
      throw new Error("Необходимо сначала авторизоваться");
    }

    try {
      log("🗑️ Начинаем удаление всех видео из профиля...");

      // Получаем username для перехода в профиль
      await this.driver.get("https://www.tiktok.com/");
      await randomDelay(3000, 5000);

      let username = "";
      const profileSelectors = [
        'a[data-e2e="nav-profile"]',
        'a[href*="/@"]',
        '[data-e2e="profile-link"]',
      ];

      for (const selector of profileSelectors) {
        try {
          const profileLink = await this.driver.findElement(By.css(selector));
          const href = await profileLink.getAttribute("href");

          if (href && href.includes("/@")) {
            const match = href.match(/@([^/?]+)/);
            if (match && match[1]) {
              username = match[1];
              log(`✅ Найден username: ${username}`);
              break;
            }
          }
        } catch (e) {
          continue;
        }
      }

      if (!username) {
        log("⚠️ Username не найден, не можем удалить видео");
        return 0;
      }

      // Переходим в профиль
      const profileUrl = `https://www.tiktok.com/@${username}`;
      log(`🌐 Переходим в профиль: ${profileUrl}`);

      await this.driver.get(profileUrl);
      await randomDelay(3000, 5000);

      await this.takeScreenshot("01-profile-page");

      let deletedCount = 0;
      let failedAttempts = 0;
      const MAX_FAILED_ATTEMPTS = 3;
      const MAX_VIDEOS_TO_DELETE = 100; // Защита от бесконечного цикла
      const seenVideos = new Set<string>(); // Отслеживаем уже обработанные видео
      let sameVideoAttempts = 0;
      let lastVideoUrl = "";

      this.closeAllModalsAggressively();
      await randomDelay(1000, 2000);

      // Удаляем видео в цикле, пока они есть
      while (deletedCount < MAX_VIDEOS_TO_DELETE) {
        try {
          // Ищем все контейнеры видео на странице профиля
          const videoContainers = await this.driver.findElements(
            By.css('a[href*="/video/"]')
          );

          if (videoContainers.length === 0) {
            log("✅ Видео не найдено, удаление завершено");
            break;
          }

          // Получаем URL первого видео для проверки зацикливания
          const firstVideoUrl = await videoContainers[0].getAttribute("href");

          // Проверяем, не застряли ли мы на одном видео
          if (firstVideoUrl === lastVideoUrl) {
            sameVideoAttempts++;
            log(
              `⚠️ То же самое видео (попытка ${sameVideoAttempts}/3): ${firstVideoUrl}`
            );

            if (sameVideoAttempts >= 3) {
              log(`❌ Застряли на видео ${firstVideoUrl}, пропускаем`);
              seenVideos.add(firstVideoUrl);
              sameVideoAttempts = 0;

              // Если уже пытались удалить все видео, выходим
              if (seenVideos.size >= videoContainers.length) {
                log(`❌ Все видео обработаны, но не удалены. Завершаем.`);
                break;
              }

              failedAttempts++;
              if (failedAttempts >= MAX_FAILED_ATTEMPTS) {
                break;
              }
              continue;
            }
          } else {
            sameVideoAttempts = 0;
            lastVideoUrl = firstVideoUrl;
          }

          log(
            `📹 Найдено видео: ${videoContainers.length}, удаляем: ${firstVideoUrl}`
          );

          // Прокручиваем к первому видео и ждем, пока оно станет кликабельным
          try {
            await this.driver.executeScript(
              "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
              videoContainers[0]
            );
            await randomDelay(1000, 1500);

            // Ждем, пока элемент станет кликабельным
            await this.driver.wait(
              until.elementIsVisible(videoContainers[0]),
              5000
            );
            await this.driver.wait(
              until.elementIsEnabled(videoContainers[0]),
              5000
            );

            log("✅ Элемент видео готов для клика");
          } catch (scrollError) {
            log(`⚠️ Ошибка при подготовке элемента: ${scrollError}`);
            // Пробуем продолжить даже если прокрутка не удалась
          }

          // Кликаем на первое видео, чтобы открыть его в модальном окне
          try {
            await humanLikeClick(this.driver, videoContainers[0]);
            await randomDelay(4000, 5000);
          } catch (clickError: any) {
            log(
              `⚠️ Обычный клик не сработал, пробуем JavaScript клик: ${clickError.message}`
            );
            try {
              await this.driver.executeScript(
                "arguments[0].click();",
                videoContainers[0]
              );
              await randomDelay(5000, 6000); // JS клику нужно больше времени
              log(`✅ JavaScript клик выполнен, ждем загрузку модалки`);
            } catch (jsClickError: any) {
              log(
                `❌ JavaScript клик тоже не сработал: ${jsClickError.message}`
              );
              // Если видео не открылось, переходим к следующей итерации
              throw new Error("Не удалось открыть видео для удаления");
            }
          }

          await this.takeScreenshot("02-video-opened");

          // Ищем кнопку с тремя точками (меню действий)
          let menuButton: WebElement | null = null;
          try {
            menuButton = await this.driver.wait(
              until.elementLocated(By.css('div[data-e2e="video-setting"]')),
              10000 // Увеличили с 5000 до 10000
            );
            log("✅ Найдена кнопка меню (три точки)");
          } catch (e) {
            log("⚠️ Кнопка меню не найдена, пробуем альтернативные селекторы");

            // Пробуем найти SVG с Ellipsis
            try {
              const svgElements = await this.driver.findElements(
                By.css('svg[class*="Ellipsis"]')
              );

              for (const svg of svgElements) {
                const parent = await svg.findElement(By.xpath(".."));
                const isDisplayed = await parent.isDisplayed();
                if (isDisplayed) {
                  menuButton = parent;
                  log("✅ Найдена кнопка меню через SVG");
                  break;
                }
              }
            } catch (e2) {
              log(`⚠️ Альтернативный поиск не удался: ${e2}`);
            }
          }

          if (!menuButton) {
            log(
              "⚠️ Кнопка меню не найдена, пытаемся закрыть видео и продолжить"
            );
            // Нажимаем Escape, чтобы закрыть видео
            await this.driver.actions().sendKeys(Key.ESCAPE).perform();
            await randomDelay(1000, 2000);
            continue;
          }

          // Кликаем на кнопку меню
          await humanLikeClick(this.driver, menuButton);
          await randomDelay(1500, 2500);

          await this.takeScreenshot("03-menu-opened");

          // Ищем кнопку Delete в выпадающем меню
          let deleteButton: WebElement | null = null;

          try {
            // Используем только data-e2e - работает для любого языка
            deleteButton = await this.driver.wait(
              until.elementLocated(
                By.css('li[data-e2e="video-delete"] button')
              ),
              5000
            );
            log("✅ Найдена кнопка Delete по data-e2e");
          } catch (e) {
            log("⚠️ Кнопка Delete не найдена, пробуем альтернативные способы");

            // Запасной вариант: ищем li с data-e2e и кнопку внутри
            try {
              const liElement = await this.driver.findElement(
                By.css('li[data-e2e="video-delete"]')
              );

              if (liElement) {
                const button = await liElement.findElement(By.css("button"));
                const isDisplayed = await button.isDisplayed();
                if (isDisplayed) {
                  deleteButton = button;
                  log("✅ Найдена кнопка Delete через li элемент");
                }
              }
            } catch (e3) {
              log(`⚠️ Поиск кнопки Delete не удался: ${e3}`);
            }
          }

          if (!deleteButton) {
            log("⚠️ Кнопка Delete не найдена, закрываем меню и продолжаем");
            await this.driver.actions().sendKeys(Key.ESCAPE).perform();
            await randomDelay(1000, 2000);
            continue;
          }

          // Кликаем на кнопку Delete
          await humanLikeClick(this.driver, deleteButton);
          await randomDelay(3000, 4000); // Увеличили задержку для загрузки модалки подтверждения

          await this.takeScreenshot("04-delete-modal-opened");

          // Подтверждаем удаление в модальном окне
          let confirmButton: WebElement | null = null;

          try {
            // Используем только data-e2e - работает для любого языка
            confirmButton = await this.driver.wait(
              until.elementLocated(
                By.css('button[data-e2e="video-modal-delete"]')
              ),
              10000
            );
            log("✅ Найдена кнопка подтверждения удаления");
          } catch (e) {
            log(
              "⚠️ Кнопка подтверждения не найдена по data-e2e, пробуем по классу"
            );

            // Запасной вариант: по классу ButtonConfirm (любой язык)
            try {
              const buttons = await this.driver.findElements(
                By.css('button[class*="ButtonConfirm"]')
              );

              for (const button of buttons) {
                try {
                  const isDisplayed = await button.isDisplayed();
                  if (isDisplayed) {
                    confirmButton = button;
                    const text = await button.getText();
                    log(`✅ Найдена кнопка подтверждения по классу: "${text}"`);
                    break;
                  }
                } catch (e2) {
                  continue;
                }
              }
            } catch (e3) {
              log(`⚠️ Поиск по классу не удался: ${e3}`);
            }
          }

          if (!confirmButton) {
            log("⚠️ Кнопка подтверждения не найдена, отменяем удаление");
            await this.driver.actions().sendKeys(Key.ESCAPE).perform();
            await randomDelay(1000, 2000);
            continue;
          }

          // Кликаем на кнопку подтверждения
          await humanLikeClick(this.driver, confirmButton);
          log("✅ Видео удалено");
          deletedCount++;
          failedAttempts = 0; // Сбрасываем счетчик неудач при успешном удалении

          await this.takeScreenshot("05-video-deleted");

          // Ждем 3 секунды перед следующим удалением
          await randomDelay(3000, 4000);

          // Возвращаемся в профиль (обновляем страницу)
          await this.driver.get(profileUrl);
          await randomDelay(3000, 5000);

          await this.takeScreenshot("06-back-to-profile");
        } catch (error) {
          failedAttempts++;
          log(
            `⚠️ Ошибка при удалении видео (попытка ${failedAttempts}/${MAX_FAILED_ATTEMPTS}): ${error}`
          );

          await this.takeScreenshot(`error-attempt-${failedAttempts}`);

          // Если слишком много неудачных попыток подряд, прекращаем удаление
          if (failedAttempts >= MAX_FAILED_ATTEMPTS) {
            log(
              `❌ Превышено максимальное количество неудачных попыток (${MAX_FAILED_ATTEMPTS}), прекращаем удаление`
            );
            break;
          }

          // Пытаемся вернуться в профиль
          try {
            await this.driver.get(profileUrl);
            await randomDelay(3000, 5000);
          } catch (e) {
            log(`❌ Не удалось вернуться в профиль: ${e}`);
            break;
          }
        }
      }

      log(`✅ Удаление завершено. Всего удалено видео: ${deletedCount}`);
      return deletedCount;
    } catch (error) {
      log(`❌ Ошибка при удалении видео: ${error}`);
      throw error;
    }
  }

  async close(): Promise<void> {
    if (this.driver) {
      try {
        log("🔒 Закрываем браузер...");
        await this.driver.quit();
        this.driver = null;
        this.isLoggedIn = false;
        log("✅ Браузер закрыт");
      } catch (e) {
        log(`⚠️ Ошибка при закрытии браузера: ${e}`);
        this.driver = null;
        this.isLoggedIn = false;
      }
    }

    if (this.proxyExtensionPath && fs.existsSync(this.proxyExtensionPath)) {
      try {
        fs.rmSync(this.proxyExtensionPath, { recursive: true, force: true });
        log("🗑️ Расширение прокси удалено");
      } catch (e) {
        log(`⚠️ Ошибка при удалении расширения прокси: ${e}`);
      }
    }

    if (this.userDataDir && fs.existsSync(this.userDataDir)) {
      try {
        fs.rmSync(this.userDataDir, { recursive: true, force: true });
        log("🗑️ User data директория удалена");
      } catch (e) {
        log(`⚠️ Ошибка при удалении user data: ${e}`);
      }
    }
  }

  private async setupProxy(options: ChromeOptions): Promise<void> {
    if (!this.proxy) return;

    log(`🔌 Настройка прокси: ${this.proxy}`);

    const proxyParts = this.proxy.split(":");

    if (proxyParts.length === 4) {
      const [host, port, username, password] = proxyParts;

      const manifest = {
        version: "1.0.0",
        manifest_version: 2,
        name: "Chrome Proxy",
        permissions: [
          "proxy",
          "tabs",
          "unlimitedStorage",
          "storage",
          "<all_urls>",
          "webRequest",
          "webRequestBlocking",
        ],
        background: { scripts: ["background.js"] },
        minimum_chrome_version: "76.0.0",
      };

      const background = `
        var config = {
          mode: "fixed_servers",
          rules: {
            singleProxy: {
              scheme: "http",
              host: "${host}",
              port: ${port}
            },
            bypassList: ["localhost"]
          }
        };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
          return {
            authCredentials: {
              username: "${username}",
              password: "${password}"
            }
          };
        }

        chrome.webRequest.onAuthRequired.addListener(
          callbackFn,
          { urls: ["<all_urls>"] },
          ['blocking']
        );
      `;

      const uniqueId = `${process.pid}-${Date.now()}-${Math.random()
        .toString(36)
        .substring(2)}`;
      this.proxyExtensionPath = path.join(
        os.tmpdir(),
        `chrome-proxy-ext-${uniqueId}`
      );
      fs.mkdirSync(this.proxyExtensionPath, { recursive: true, mode: 0o755 });

      fs.writeFileSync(
        path.join(this.proxyExtensionPath, "manifest.json"),
        JSON.stringify(manifest)
      );
      fs.writeFileSync(
        path.join(this.proxyExtensionPath, "background.js"),
        background
      );

      options.addArguments(`--load-extension=${this.proxyExtensionPath}`);
      options.addArguments(`--proxy-server=http://${host}:${port}`);

      log(`✅ Прокси настроен: ${host}:${port} (${username})`);
    } else if (proxyParts.length === 2) {
      const [host, port] = proxyParts;
      options.addArguments(`--proxy-server=http://${host}:${port}`);
      log(`✅ Прокси настроен: ${host}:${port}`);
    } else {
      log(
        `⚠️ Неверный формат прокси: ${this.proxy}. Ожидается IP:PORT:LOGIN:PASSWORD или IP:PORT`
      );
    }
  }
}
