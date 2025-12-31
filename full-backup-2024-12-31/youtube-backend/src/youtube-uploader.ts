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
} from "./utils";

export interface YouTubeVideoConfig {
  videoPath: string;
  title: string;
  description: string;
  tags: string[];
  visibility?: "public" | "unlisted" | "private";
  isShort?: boolean;
}

export class YouTubeUploader {
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
    this.sessionId = `yt-${Date.now()}-${Math.random().toString(36).substring(2)}`;
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
    log("🚀 [YouTube] Инициализация браузера...");

    const options = new ChromeOptions();

    log(`🔍 Headless режим: ${this.headless}`);

    const uniqueId = `${process.pid}-${Date.now()}-${Math.random()
      .toString(36)
      .substring(2)}`;
    this.userDataDir = path.join(os.tmpdir(), `chrome-yt-profile-${uniqueId}`);
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

    log("✅ [YouTube] Браузер успешно инициализирован");

    // Добавляем куки для YouTube/Google (если есть cookies)
    if (this.credentials.cookies && this.credentials.cookies.length > 0) {
      log("🍪 [YouTube] Добавляем куки в браузер...");

      // Сначала открываем YouTube для установки кук
      await this.driver.get("https://www.youtube.com/");
      await randomDelay(2000, 3000);

      let cookiesAdded = 0;
      for (const cookie of this.credentials.cookies) {
        try {
          // Определяем домен для куки
          let domain = cookie.domain || ".youtube.com";
          
          // Нормализуем домен
          if (domain.includes("google.com")) {
            // Для Google кук нужно сначала посетить google.com
            continue; // Пропускаем Google куки, добавим их позже
          }
          
          if (!domain.startsWith(".")) {
            domain = "." + domain;
          }

          const cleanCookie: any = {
            name: cookie.name,
            value: cookie.value,
            domain: domain.includes("youtube") ? ".youtube.com" : domain,
            path: cookie.path || "/",
            secure: cookie.secure !== false,
            httpOnly: cookie.httpOnly || false,
          };

          if (cookie.expirationDate) {
            cleanCookie.expiry = Math.floor(cookie.expirationDate);
          }

          await this.driver.manage().addCookie(cleanCookie);
          cookiesAdded++;
          log(`✅ Кука ${cookie.name} добавлена`);
        } catch (e: any) {
          log(`⚠️ Не удалось добавить куку ${cookie.name}: ${e.message || e}`);
        }
      }

      // Теперь добавляем Google куки
      await this.driver.get("https://accounts.google.com/");
      await randomDelay(1000, 2000);

      for (const cookie of this.credentials.cookies) {
        try {
          if (cookie.domain && cookie.domain.includes("google.com")) {
            const cleanCookie: any = {
              name: cookie.name,
              value: cookie.value,
              domain: ".google.com",
              path: cookie.path || "/",
              secure: cookie.secure !== false,
              httpOnly: cookie.httpOnly || false,
            };

            if (cookie.expirationDate) {
              cleanCookie.expiry = Math.floor(cookie.expirationDate);
            }

            await this.driver.manage().addCookie(cleanCookie);
            cookiesAdded++;
            log(`✅ Google кука ${cookie.name} добавлена`);
          }
        } catch (e: any) {
          log(`⚠️ Не удалось добавить Google куку ${cookie.name}: ${e.message}`);
        }
      }

      log(`✅ Добавлено ${cookiesAdded} кук из ${this.credentials.cookies.length}`);

      // Возвращаемся на YouTube и обновляем
      await this.driver.get("https://www.youtube.com/");
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

  async login(): Promise<void> {
    if (!this.driver) {
      throw new Error("Браузер не инициализирован");
    }

    log("🔐 [YouTube] Начинаем процесс авторизации...");

    try {
      // Проверяем авторизацию через куки (если есть)
      if (this.credentials.cookies && this.credentials.cookies.length > 0) {
        log("🍪 [YouTube] Проверяем авторизацию через куки...");

        // Переходим в YouTube Studio для проверки авторизации
        await this.driver.get("https://studio.youtube.com/");
        await randomDelay(3000, 5000);

        await this.takeScreenshot("01-studio-check");

        const currentUrl = await this.driver.getCurrentUrl();
        log(`📍 Текущий URL: ${currentUrl}`);

        // Проверяем авторизованы ли мы
        if (
          currentUrl.includes("studio.youtube.com") &&
          !currentUrl.includes("accounts.google.com")
        ) {
          log("✅ [YouTube] Успешная авторизация через куки!");
          this.isLoggedIn = true;
          
          // Проверяем и создаем канал если нужно
          await this.ensureChannelExists();
          return;
        }

        // Если перенаправило на логин Google - пробуем email/password
        if (currentUrl.includes("accounts.google.com")) {
          log("⚠️ [YouTube] Куки недействительны, пробуем email/password...");
        }
      }

      // Авторизация через email/пароль
      if (this.credentials.username && this.credentials.password) {
        await this.loginWithEmailPassword();
        return;
      }
      
      // Если есть email и password (альтернативные поля)
      if (this.credentials.email && this.credentials.email_password) {
        this.credentials.username = this.credentials.email;
        this.credentials.password = this.credentials.email_password;
        await this.loginWithEmailPassword();
        return;
      }

      throw new Error("Не удалось авторизоваться: нет валидных credentials (cookies или email/password)");
    } catch (error) {
      log(`❌ [YouTube] Ошибка при авторизации: ${error}`);
      await this.takeScreenshot("error-login");
      throw error;
    }
  }

  private async loginWithEmailPassword(): Promise<void> {
    if (!this.driver) {
      throw new Error("Браузер не инициализирован");
    }

    log("🔐 [YouTube] Авторизация через email и пароль...");

    try {
      // Переходим на YouTube
      await this.driver.get("https://www.youtube.com/");
      await randomDelay(2000, 3000);

      await this.takeScreenshot("02-youtube-home");

      // Ищем кнопку "Sign in" / "Войти"
      let signInButton: WebElement | null = null;

      // Проверяем наличие consent popup
      try {
        const consentButtons = await this.driver.findElements(
          By.css('ytd-button-renderer[class*="signin"]')
        );
        if (consentButtons.length > 0) {
          await humanLikeClick(this.driver, consentButtons[0]);
          log("✅ Нажата кнопка Sign in в consent popup");
          await randomDelay(2000, 3000);
        }
      } catch (e) {
        // Consent popup не найден
      }

      // Ищем стандартную кнопку Sign in
      if (!signInButton) {
        try {
          const buttonsContainer = await this.driver.findElement(By.id("buttons"));
          signInButton = await buttonsContainer.findElement(By.css("ytd-button-renderer"));
        } catch (e) {
          // Пробуем другие селекторы
        }
      }

      if (!signInButton) {
        try {
          signInButton = await this.driver.findElement(
            By.css('a[href*="accounts.google.com/ServiceLogin"], tp-yt-paper-button[aria-label*="Sign in"]')
          );
        } catch (e) {
          // Пробуем перейти напрямую
          log("⚠️ Кнопка Sign in не найдена, переходим напрямую на страницу входа");
          await this.driver.get("https://accounts.google.com/signin");
          await randomDelay(3000, 5000);
        }
      }

      if (signInButton) {
        await humanLikeClick(this.driver, signInButton);
        log("✅ Нажата кнопка Sign in");
        await randomDelay(3000, 5000);
      }

      await this.takeScreenshot("03-google-signin");

      // Вводим email
      const emailInput = await this.driver.wait(
        until.elementLocated(By.css('input[type="email"], #identifierId')),
        10000
      );
      await humanLikeTyping(emailInput, this.credentials.username);
      log("✅ Email введен");
      await randomDelay(500, 1000);

      // Нажимаем "Далее"
      const nextButton = await this.driver.findElement(
        By.css('#identifierNext, button[type="button"]')
      );
      await humanLikeClick(this.driver, nextButton);
      log("✅ Нажата кнопка Next");
      await randomDelay(3000, 5000);

      await this.takeScreenshot("04-password-page");

      // Вводим пароль
      const passwordInput = await this.driver.wait(
        until.elementLocated(By.css('input[type="password"], input[name="Passwd"]')),
        10000
      );
      await humanLikeTyping(passwordInput, this.credentials.password);
      log("✅ Пароль введен");
      await randomDelay(500, 1000);

      // Нажимаем "Войти"
      const signInSubmit = await this.driver.findElement(
        By.css('#passwordNext, button[type="button"]')
      );
      await humanLikeClick(this.driver, signInSubmit);
      log("✅ Нажата кнопка Sign in");
      await randomDelay(5000, 8000);

      await this.takeScreenshot("05-after-signin");

      // Проверяем наличие "Not now" кнопки (2FA или другие prompts)
      try {
        const notNowButton = await this.driver.wait(
          until.elementLocated(
            By.xpath("//button[.//span[normalize-space()='Not now']]")
          ),
          5000
        );
        await humanLikeClick(this.driver, notNowButton);
        log("✅ Нажата кнопка 'Not now'");
        await randomDelay(2000, 3000);
      } catch (e) {
        // Кнопка Not now не найдена - это нормально
      }

      // Проверяем успешность авторизации
      await this.driver.get("https://studio.youtube.com/");
      await randomDelay(3000, 5000);

      await this.takeScreenshot("06-studio-after-login");

      const finalUrl = await this.driver.getCurrentUrl();
      if (finalUrl.includes("studio.youtube.com") && !finalUrl.includes("accounts.google.com")) {
        log("✅ [YouTube] Успешная авторизация через email/password!");
        this.isLoggedIn = true;
        
        // Проверяем и создаем канал если нужно
        await this.ensureChannelExists();
        return;
      }

      throw new Error("Не удалось авторизоваться в YouTube");
    } catch (error) {
      log(`❌ [YouTube] Ошибка при авторизации через email/password: ${error}`);
      await this.takeScreenshot("error-email-login");
      throw error;
    }
  }

  private async ensureChannelExists(): Promise<void> {
    if (!this.driver) return;

    log("🔍 [YouTube] Проверяем наличие канала...");

    try {
      await this.driver.get("https://www.youtube.com/");
      await randomDelay(2000, 3000);

      await this.takeScreenshot("07-channel-check");

      // Проверяем диалог создания канала
      const channelDialogs = await this.driver.findElements(
        By.css("ytd-channel-creation-dialog-renderer")
      );

      if (channelDialogs.length > 0) {
        log("📺 [YouTube] Обнаружен диалог создания канала, создаем...");
        await this.createChannel();
        return;
      }

      // Кликаем на аватар профиля
      const avatarButtons = await this.driver.findElements(By.id("avatar-btn"));
      
      if (avatarButtons.length > 0) {
        await humanLikeClick(this.driver, avatarButtons[0]);
        await randomDelay(2000, 3000);

        await this.takeScreenshot("08-profile-menu");

        // Проверяем ссылку на канал
        const manageAccount = await this.driver.findElements(By.id("manage-account"));
        
        if (manageAccount.length > 0) {
          const links = await manageAccount[0].findElements(By.css("a"));
          
          if (links.length > 0) {
            const href = await links[0].getAttribute("href");
            
            if (href && href.includes("create_channel")) {
              log("📺 [YouTube] Канал не создан, создаем...");
              await this.createChannel(href);
              return;
            }
          }
        }

        // Закрываем меню профиля
        await this.driver.findElement(By.css("body")).click();
        await randomDelay(500, 1000);
      }

      log("✅ [YouTube] Канал уже существует");
    } catch (error) {
      log(`⚠️ [YouTube] Ошибка при проверке канала: ${error}`);
      // Продолжаем работу, возможно канал уже есть
    }
  }

  private async createChannel(href?: string): Promise<void> {
    if (!this.driver) return;

    log("📺 [YouTube] Создаем YouTube канал...");

    try {
      if (href) {
        await this.driver.get(href);
        await randomDelay(3000, 5000);
      }

      await this.takeScreenshot("09-create-channel");

      // Ищем кнопку создания канала разными способами
      let createButton: WebElement | null = null;

      // По aria-label
      try {
        createButton = await this.driver.findElement(
          By.xpath("//button[contains(@aria-label, 'канал') or contains(@aria-label, 'channel')]")
        );
        log("✅ Кнопка найдена по aria-label");
      } catch (e) {
        // Пробуем другой способ
      }

      // По тексту
      if (!createButton) {
        try {
          createButton = await this.driver.findElement(
            By.xpath("//button[.//span[contains(text(), 'Создать канал') or contains(text(), 'Create channel')]]")
          );
          log("✅ Кнопка найдена по тексту");
        } catch (e) {
          // Пробуем другой способ
        }
      }

      // По классу
      if (!createButton) {
        try {
          createButton = await this.driver.findElement(
            By.css("button.yt-spec-button-shape-next--call-to-action, #create-channel-button")
          );
          log("✅ Кнопка найдена по классу");
        } catch (e) {
          // Пробуем другой способ
        }
      }

      // В диалоге
      if (!createButton) {
        try {
          const dialog = await this.driver.findElement(
            By.css("ytd-channel-creation-dialog-renderer")
          );
          await humanLikeClick(this.driver, dialog);
          await randomDelay(1000, 2000);

          createButton = await this.driver.findElement(By.id("create-channel-button"));
          log("✅ Кнопка найдена в диалоге");
        } catch (e) {
          log("⚠️ Кнопка создания канала не найдена");
        }
      }

      if (createButton) {
        await humanLikeClick(this.driver, createButton);
        log("✅ Нажата кнопка создания канала");
        await randomDelay(3000, 5000);

        await this.takeScreenshot("10-after-create-channel");
        log("✅ [YouTube] Канал успешно создан!");
      }
    } catch (error) {
      log(`⚠️ [YouTube] Ошибка при создании канала: ${error}`);
    }
  }

  async uploadVideo(videoConfig: YouTubeVideoConfig): Promise<string> {
    if (!this.driver || !this.isLoggedIn) {
      throw new Error("Необходимо сначала авторизоваться");
    }

    const { videoPath, title, description, tags, visibility = "public", isShort = false } = videoConfig;

    log(`📹 [YouTube] Начинаем загрузку видео: ${videoPath}`);

    try {
      const absVideoPath = path.resolve(videoPath);
      if (!fs.existsSync(absVideoPath)) {
        throw new Error(`Видео файл не найден: ${absVideoPath}`);
      }

      // Переходим на страницу загрузки напрямую
      log("🌐 [YouTube] Переходим на страницу загрузки...");
      await this.driver.get("https://www.youtube.com/upload");
      await randomDelay(3000, 5000);

      await this.takeScreenshot("11-upload-page");

      // Ищем input для файла
      log("📤 [YouTube] Загружаем видео файл...");
      
      const fileInput = await this.driver.wait(
        until.elementLocated(By.css('input[type="file"]')),
        15000
      );

      await fileInput.sendKeys(absVideoPath);
      log("✅ Файл отправлен, ожидаем обработку...");

      // Ждем появления формы с деталями
      await this.driver.wait(
        until.elementLocated(By.id("title-textbox-container")),
        30000
      );
      await randomDelay(3000, 5000);

      await this.takeScreenshot("12-upload-started");

      // Заполняем название
      log("✍️ [YouTube] Заполняем детали видео...");
      
      const titleContainer = await this.driver.findElement(By.id("title-textbox-container"));
      const titleInput = await titleContainer.findElement(By.id("textbox"));

      await humanLikeClick(this.driver, titleInput);
      await randomDelay(300, 500);

      // Очищаем существующий текст
      const existingText = await titleInput.getAttribute("innerText");
      if (existingText && existingText.length > 0) {
        for (let i = 0; i < existingText.length; i++) {
          await titleInput.sendKeys(Key.BACK_SPACE);
          if (i % 10 === 0) await randomDelay(10, 50);
        }
        await randomDelay(300, 500);
      }

      await humanLikeTyping(titleInput, title);
      log(`✅ Название добавлено: ${title.substring(0, 50)}...`);

      await randomDelay(1000, 1500);

      // Заполняем описание
      const descriptionContainer = await this.driver.findElement(By.id("description-container"));
      const descriptionInput = await descriptionContainer.findElement(By.id("textbox"));

      await humanLikeClick(this.driver, descriptionInput);
      await randomDelay(300, 500);

      // Очищаем
      const existingDesc = await descriptionInput.getAttribute("innerText");
      if (existingDesc && existingDesc.length > 0) {
        for (let i = 0; i < existingDesc.length; i++) {
          await descriptionInput.sendKeys(Key.BACK_SPACE);
          if (i % 10 === 0) await randomDelay(10, 50);
        }
        await randomDelay(300, 500);
      }

      await humanLikeTyping(descriptionInput, description);
      log(`✅ Описание добавлено: ${description.substring(0, 50)}...`);

      await randomDelay(1000, 1500);
      await this.takeScreenshot("13-details-filled");

      // Пробуем получить ссылку на видео до публикации (для shorts)
      let videoUrl = "";
      try {
        const linkElement = await this.driver.findElement(
          By.xpath("//a[contains(@href, 'https://youtube.com/shorts/') or contains(@href, 'https://youtu.be/')]")
        );
        videoUrl = await linkElement.getAttribute("href");
        log(`🔗 Предварительная ссылка: ${videoUrl}`);
      } catch (e) {
        // Ссылка пока недоступна
      }

      // Устанавливаем "Not made for kids" / "Made for kids"
      try {
        const notForKidsRadio = await this.driver.findElement(
          By.name("VIDEO_MADE_FOR_KIDS_NOT_MFK")
        );
        await humanLikeClick(this.driver, notForKidsRadio);
        log("✅ Установлено: Not made for kids");
      } catch (e) {
        try {
          // Пробуем альтернативный вариант
          const forKidsRadio = await this.driver.findElement(
            By.name("VIDEO_MADE_FOR_KIDS_MFK")
          );
          await humanLikeClick(this.driver, forKidsRadio);
          log("✅ Установлено: Made for kids");
        } catch (e2) {
          log("⚠️ Не удалось найти опцию 'Made for kids'");
        }
      }

      await randomDelay(1000, 1500);

      // Нажимаем "Next" три раза (Details -> Video elements -> Checks -> Visibility)
      for (let i = 0; i < 3; i++) {
        try {
          const nextButton = await this.driver.findElement(By.id("next-button"));
          await humanLikeClick(this.driver, nextButton);
          log(`✅ Нажата кнопка Next (${i + 1}/3)`);
          await randomDelay(2000, 3000);
        } catch (e) {
          log(`⚠️ Кнопка Next не найдена на шаге ${i + 1}`);
        }
      }

      await this.takeScreenshot("14-visibility-page");

      // Устанавливаем видимость
      log(`🔓 [YouTube] Устанавливаем видимость: ${visibility}`);
      
      const visibilityMap: { [key: string]: string } = {
        public: "PUBLIC",
        unlisted: "UNLISTED",
        private: "PRIVATE",
      };

      try {
        const visibilityRadio = await this.driver.findElement(
          By.name(visibilityMap[visibility])
        );
        await humanLikeClick(this.driver, visibilityRadio);
        log(`✅ Видимость установлена: ${visibility}`);
      } catch (e) {
        log(`⚠️ Не удалось установить видимость: ${e}`);
      }

      await randomDelay(1500, 2500);

      // Ждем завершения обработки видео
      log("⏳ [YouTube] Ожидаем завершения обработки видео...");
      
      let processingComplete = false;
      const maxWaitTime = 10 * 60 * 1000; // 10 минут максимум
      const startTime = Date.now();

      while (!processingComplete && (Date.now() - startTime) < maxWaitTime) {
        try {
          // Проверяем статус обработки
          const progressText = await this.driver.executeScript(`
            const progress = document.querySelector('.progress-label, .ytcp-video-upload-progress');
            return progress ? progress.textContent : '';
          `);

          if (typeof progressText === "string") {
            if (progressText.includes("100%") || 
                progressText.toLowerCase().includes("complete") ||
                progressText.toLowerCase().includes("готово")) {
              processingComplete = true;
              log("✅ Обработка видео завершена");
            } else if (progressText) {
              log(`⏳ Обработка: ${progressText}`);
            }
          }

          // Также проверяем, активна ли кнопка публикации
          const publishButton = await this.driver.findElements(
            By.css('#done-button:not([disabled])')
          );
          if (publishButton.length > 0) {
            processingComplete = true;
            log("✅ Кнопка публикации активна");
          }
        } catch (e) {
          // Кнопка еще не активна
        }

        if (!processingComplete) {
          await randomDelay(5000, 8000);
        }
      }

      await this.takeScreenshot("15-before-publish");

      // Нажимаем "Done" / "Готово" для публикации
      log("🚀 [YouTube] Публикуем видео...");

      try {
        const doneButton = await this.driver.wait(
          until.elementLocated(By.id("done-button")),
          10000
        );
        
        // Ждем пока кнопка станет кликабельной
        await this.driver.wait(until.elementIsEnabled(doneButton), 30000);
        
        await humanLikeClick(this.driver, doneButton);
        log("✅ Кнопка публикации нажата");
      } catch (e) {
        log(`⚠️ Ошибка при нажатии кнопки публикации: ${e}`);
        throw new Error("Не удалось опубликовать видео");
      }

      await randomDelay(5000, 8000);

      await this.takeScreenshot("16-after-publish");

      // Получаем URL видео если еще не получили
      if (!videoUrl) {
        try {
          // Ищем ссылку на видео в диалоге успешной загрузки
          const linkElement = await this.driver.findElement(
            By.css('a.ytcp-video-info, a[href*="youtube.com/video"], a[href*="youtu.be"], a[href*="youtube.com/shorts"]')
          );
          videoUrl = await linkElement.getAttribute("href");
          log(`🔗 URL видео: ${videoUrl}`);
        } catch (e) {
          // Пробуем получить из текста
          try {
            const videoIdElement = await this.driver.findElement(
              By.css('.video-url-fadeable, [class*="video-url"]')
            );
            const urlText = await videoIdElement.getText();
            if (urlText.includes("youtube.com") || urlText.includes("youtu.be")) {
              videoUrl = urlText;
            }
          } catch (e2) {
            log(`⚠️ Не удалось получить URL видео`);
          }
        }
      }

      log(`✅ [YouTube] Видео успешно загружено: ${videoPath}`);
      return videoUrl;
    } catch (error) {
      log(`❌ [YouTube] Ошибка при загрузке видео: ${error}`);
      await this.takeScreenshot("error-upload");
      throw error;
    }
  }

  async getChannelStats(): Promise<{
    channelName: string;
    subscribers: number;
    totalViews: number;
    videoCount: number;
  }> {
    if (!this.driver || !this.isLoggedIn) {
      log("⚠️ Браузер не инициализирован или не авторизован");
      return { channelName: "", subscribers: 0, totalViews: 0, videoCount: 0 };
    }

    try {
      log("📊 [YouTube] Получаем статистику канала...");

      await this.driver.get("https://studio.youtube.com/");
      await randomDelay(3000, 5000);

      const stats = await this.driver.executeScript(`
        const result = { channelName: '', subscribers: 0, totalViews: 0, videoCount: 0 };
        
        // Название канала
        const channelName = document.querySelector('.channel-name, #channel-name');
        if (channelName) result.channelName = channelName.textContent.trim();
        
        // Подписчики
        const subsEl = document.querySelector('[class*="subscriber"]');
        if (subsEl) {
          const text = subsEl.textContent || '';
          const match = text.match(/([\\d,.]+)\\s*(K|M|B)?/i);
          if (match) {
            let num = parseFloat(match[1].replace(/,/g, ''));
            if (match[2]) {
              if (match[2].toUpperCase() === 'K') num *= 1000;
              if (match[2].toUpperCase() === 'M') num *= 1000000;
              if (match[2].toUpperCase() === 'B') num *= 1000000000;
            }
            result.subscribers = Math.round(num);
          }
        }
        
        return result;
      `);

      log(`✅ Статистика канала: ${JSON.stringify(stats)}`);
      return stats as any;
    } catch (error) {
      log(`❌ Ошибка при получении статистики: ${error}`);
      return { channelName: "", subscribers: 0, totalViews: 0, videoCount: 0 };
    }
  }

  async close(): Promise<void> {
    if (this.driver) {
      try {
        log("🔒 [YouTube] Закрываем браузер...");
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

    // Очистка временных файлов
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

    log(`🔌 [YouTube] Настройка прокси: ${this.proxy}`);

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
        `chrome-yt-proxy-ext-${uniqueId}`
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
