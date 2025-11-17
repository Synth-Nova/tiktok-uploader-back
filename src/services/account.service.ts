import prisma from "../prisma";
import { Cookie, getAccountInfoFromCookies, log } from "../utils";

export class AccountService {
  /**
   * Находит или создает аккаунт по cookies
   * Если аккаунт существует - обновляет lastUsedAt и возвращает существующий User-Agent
   * Если новый - создает с новым User-Agent
   */
  async findOrCreateAccount(
    cookies: Cookie[] | string,
    profileStats?: { followers: number; following: number; likes: number; views?: number },
    proxy?: string
  ): Promise<{
    id: string;
    sessionId: string;
    userAgent: string;
    tiktokUid: string | null;
    proxy: string | null;
    isNew: boolean;
  }> {
    const accountInfo = getAccountInfoFromCookies(cookies);

    if (!accountInfo.sessionId) {
      throw new Error("Не удалось извлечь sessionId из cookies");
    }

    if (!accountInfo.userAgent) {
      throw new Error("Не удалось сгенерировать User-Agent");
    }

    // Нормализуем cookies в JSON
    let cookiesJson: string;
    if (typeof cookies === "string") {
      try {
        JSON.parse(cookies);
        cookiesJson = cookies;
      } catch (e) {
        const parsedCookies = getAccountInfoFromCookies(cookies);
        cookiesJson = JSON.stringify(parsedCookies);
      }
    } else {
      cookiesJson = JSON.stringify(cookies);
    }

    // Ищем существующий аккаунт
    let account = await prisma.account.findUnique({
      where: { sessionId: accountInfo.sessionId },
    });

    if (account) {
      // Аккаунт существует - обновляем lastUsedAt и прокси если изменился
      account = await prisma.account.update({
        where: { id: account.id },
        data: {
          lastUsedAt: new Date(),
          cookies: cookiesJson, // Обновляем cookies на случай если изменились
          proxy: proxy || account.proxy, // Обновляем прокси если передан новый
        },
      });

      log(
        `✅ Найден существующий аккаунт ${account.sessionId.substring(
          0,
          8
        )}... с User-Agent: ${account.userAgent.substring(0, 50)}...`
      );

      return {
        id: account.id,
        sessionId: account.sessionId,
        userAgent: account.userAgent,
        tiktokUid: account.tiktokUid,
        proxy: account.proxy,
        isNew: false,
      };
    } else {
      // Создаем новый аккаунт
      account = await prisma.account.create({
        data: {
          sessionId: accountInfo.sessionId,
          tiktokUid: accountInfo.tiktokUid,
          userAgent: accountInfo.userAgent,
          cookies: cookiesJson,
          proxy: proxy || null,
          lastUsedAt: new Date(),
          followers: profileStats?.followers || 0,
          following: profileStats?.following || 0,
          likes: profileStats?.likes || 0,
          views: profileStats?.views || 0,
        },
      });

      log(
        `🆕 Создан новый аккаунт ${account.sessionId.substring(
          0,
          8
        )}... с User-Agent: ${account.userAgent.substring(0, 50)}...`
      );
      log(
        `📊 Статистика: Подписчиков: ${account.followers}, Подписок: ${account.following}, Лайков: ${account.likes}, Просмотров: ${account.views}`
      );

      return {
        id: account.id,
        sessionId: account.sessionId,
        userAgent: account.userAgent,
        tiktokUid: account.tiktokUid,
        proxy: account.proxy,
        isNew: true,
      };
    }
  }

  /**
   * Добавляет запись статистики для аккаунта
   */
  async addAccountStats(
    accountId: string,
    stats: { followers: number; following: number; likes: number; views?: number },
    source: 'initial' | 'manual' | 'auto' = 'initial'
  ): Promise<void> {
    // Создаем запись в истории
    await prisma.accountStats.create({
      data: {
        accountId: accountId,
        followers: stats.followers,
        following: stats.following,
        likes: stats.likes,
        views: stats.views || 0,
        source: source,
      },
    });

    // Обновляем последнюю статистику в аккаунте
    await prisma.account.update({
      where: { id: accountId },
      data: {
        followers: stats.followers,
        following: stats.following,
        likes: stats.likes,
        views: stats.views || 0,
      },
    });

    log(`✅ Добавлена статистика для аккаунта ${accountId} (${source}): ${JSON.stringify(stats)}`);
  }

  /**
   * Создает хэштеги заранее, чтобы избежать race condition
   * Вызывается ДО параллельной обработки аккаунтов
   */
  async ensureHashtagsExist(hashtags: string[]): Promise<void> {
    if (!hashtags || hashtags.length === 0) {
      return;
    }

    for (const tag of hashtags) {
      const cleanTag = tag.replace("#", "").trim().toLowerCase();
      if (!cleanTag) continue;

      try {
        // Пробуем найти хэштег
        const existing = await prisma.hashtag.findUnique({
          where: { tag: cleanTag },
        });

        if (!existing) {
          // Создаем только если не существует
          try {
            await prisma.hashtag.create({
              data: { tag: cleanTag },
            });
            log(`✅ Создан хэштег: #${cleanTag}`);
          } catch (error: any) {
            // Если ошибка unique constraint - значит кто-то создал параллельно, это ок
            if (error.code === 'P2002') {
              log(`ℹ️ Хэштег #${cleanTag} уже существует (создан параллельно)`);
            } else {
              throw error;
            }
          }
        } else {
          log(`ℹ️ Хэштег #${cleanTag} уже существует`);
        }
      } catch (error: any) {
        log(`⚠️ Ошибка при создании хэштега #${cleanTag}: ${error.message}`);
        // Не бросаем ошибку, продолжаем с остальными
      }
    }
  }

  /**
   * Добавляет хэштеги к аккаунту
   */
  async addHashtagsToAccount(
    accountId: string,
    hashtags: string[]
  ): Promise<void> {
    if (!hashtags || hashtags.length === 0) {
      return;
    }

    log(`🏷️ Добавляем хэштеги к аккаунту ${accountId.substring(0, 8)}...: ${hashtags.join(", ")}`);

    const errors: string[] = [];

    for (const tag of hashtags) {
      // Очищаем хэштег от символа # и пробелов
      const cleanTag = tag.replace("#", "").trim().toLowerCase();

      if (!cleanTag) continue;

      try {
        // Находим хэштег (он уже должен существовать после ensureHashtagsExist)
        const hashtag = await prisma.hashtag.findUnique({
          where: { tag: cleanTag },
        });

        if (!hashtag) {
          log(`⚠️ Хэштег #${cleanTag} не найден, пропускаем`);
          continue;
        }

        // Проверяем, существует ли уже связь
        const existingLink = await prisma.accountHashtag.findUnique({
          where: {
            accountId_hashtagId: {
              accountId: accountId,
              hashtagId: hashtag.id,
            },
          },
        });

        if (!existingLink) {
          // Создаем связь между аккаунтом и хэштегом
          await prisma.accountHashtag.create({
            data: {
              accountId: accountId,
              hashtagId: hashtag.id,
            },
          });
          log(`✅ Хэштег #${cleanTag} привязан к аккаунту ${accountId.substring(0, 8)}...`);
        } else {
          log(`ℹ️ Хэштег #${cleanTag} уже привязан к аккаунту ${accountId.substring(0, 8)}...`);
        }
      } catch (error: any) {
        const errorMsg = `Ошибка при добавлении хэштега #${cleanTag}: ${error.message}`;
        log(`⚠️ ${errorMsg}`);
        errors.push(errorMsg);
      }
    }

    // Если были ошибки, пробрасываем их наружу
    if (errors.length > 0) {
      throw new Error(`Не удалось добавить некоторые хэштеги: ${errors.join('; ')}`);
    }

    log(`✅ Все хэштеги успешно добавлены к аккаунту ${accountId.substring(0, 8)}...`);
  }

  /**
   * Находит аккаунты по хэштегу
   */
  async findAccountsByHashtag(hashtag: string) {
    const cleanTag = hashtag.replace("#", "").trim().toLowerCase();

    const hashtagRecord = await prisma.hashtag.findUnique({
      where: { tag: cleanTag },
      include: {
        accounts: {
          include: {
            account: {
              include: {
                _count: {
                  select: { videos: true },
                },
              },
            },
          },
        },
      },
    });

    if (!hashtagRecord) {
      return [];
    }

    return hashtagRecord.accounts.map((ah) => ({
      id: ah.account.id,
      sessionId: ah.account.sessionId.substring(0, 12) + "...",
      tiktokUid: ah.account.tiktokUid,
      userAgent: ah.account.userAgent,
      proxy: ah.account.proxy,
      cookies: ah.account.cookies,
      followers: ah.account.followers,
      following: ah.account.following,
      likes: ah.account.likes,
      videosCount: ah.account._count.videos,
      lastUsedAt: ah.account.lastUsedAt,
      createdAt: ah.account.createdAt,
    }));
  }

  /**
   * Получает все хэштеги
   */
  async getAllHashtags() {
    const hashtags = await prisma.hashtag.findMany({
      include: {
        _count: {
          select: { accounts: true },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    return hashtags.map((h) => ({
      id: h.id,
      tag: h.tag,
      accountsCount: h._count.accounts,
      createdAt: h.createdAt,
    }));
  }

  /**
   * Добавляет задачи на обновление статистики для всех аккаунтов с указанным хэштегом в очередь
   */
  async updateStatsForHashtag(hashtag: string): Promise<{
    total: number;
    queued: number;
    message: string;
  }> {
    const cleanTag = hashtag.replace("#", "").trim().toLowerCase();
    
    log(`🔄 Начинаем добавление задач обновления статистики для хэштега #${cleanTag}`);

    const accounts = await this.findAccountsByHashtag(cleanTag);
    
    if (accounts.length === 0) {
      log(`⚠️ Аккаунтов с хэштегом #${cleanTag} не найдено`);
      return { 
        total: 0, 
        queued: 0, 
        message: `Аккаунтов с хэштегом #${cleanTag} не найдено` 
      };
    }

    log(`📊 Найдено ${accounts.length} аккаунтов для обновления статистики`);

    // Импортируем очередь статистики
    const { statsQueue } = await import("../queues/stats.queue");

    let queued = 0;

    for (const account of accounts) {
      try {
        // Добавляем задачу в очередь
        await statsQueue.add(
          {
            hashtag: cleanTag,
            accountId: account.id,
            accountCookies: account.cookies,
            proxy: account.proxy || undefined,
            userAgent: account.userAgent,
          },
          {
            attempts: 1,
            removeOnComplete: true,
            removeOnFail: false,
          }
        );

        log(`✅ Задача на обновление статистики для аккаунта ${account.sessionId} добавлена в очередь`);
        queued++;
      } catch (error: any) {
        log(`❌ Не удалось добавить задачу для аккаунта ${account.sessionId}: ${error.message}`);
      }
    }

    log(`✅ Добавлено ${queued} задач в очередь обновления статистики`);

    return {
      total: accounts.length,
      queued: queued,
      message: `Добавлено ${queued} из ${accounts.length} задач в очередь обновления статистики`,
    };
  }

  /**
   * Получает историю статистики для аккаунтов с хэштегом
   */
  async getStatsHistoryForHashtag(hashtag: string) {
    const cleanTag = hashtag.replace("#", "").trim().toLowerCase();

    const hashtagRecord = await prisma.hashtag.findUnique({
      where: { tag: cleanTag },
      include: {
        accounts: {
          include: {
            account: {
              include: {
                stats: {
                  orderBy: {
                    createdAt: 'asc',
                  },
                },
                _count: {
                  select: { videos: true },
                },
              },
            },
          },
        },
      },
    });

    if (!hashtagRecord) {
      return [];
    }

    return hashtagRecord.accounts.map((ah) => ({
      accountId: ah.account.id,
      sessionId: ah.account.sessionId.substring(0, 12) + "...",
      tiktokUid: ah.account.tiktokUid,
      username: ah.account.username || 'N/A',
      videosCount: ah.account._count.videos,
      createdAt: ah.account.createdAt,
      statsHistory: ah.account.stats.map((stat) => ({
        followers: stat.followers,
        following: stat.following,
        likes: stat.likes,
        views: stat.views,
        source: stat.source,
        date: stat.createdAt,
      })),
    }));
  }

  /**
   * Получает аккаунт по ID
   */
  async getAccountById(accountId: string) {
    return await prisma.account.findUnique({
      where: { id: accountId },
    });
  }

  /**
   * Получает статистику по аккаунтам
   */
  async getAccountsStats() {
    const totalAccounts = await prisma.account.count();

    const accountsWithVideos = await prisma.account.findMany({
      include: {
        _count: {
          select: { videos: true },
        },
      },
      orderBy: {
        lastUsedAt: "desc",
      },
      take: 10,
    });

    return {
      totalAccounts,
      recentAccounts: accountsWithVideos.map((acc) => ({
        id: acc.id,
        sessionId: acc.sessionId.substring(0, 8) + "...",
        tiktokUid: acc.tiktokUid,
        userAgent: acc.userAgent.substring(0, 50) + "...",
        videosCount: acc._count.videos,
        lastUsedAt: acc.lastUsedAt,
      })),
    };
  }

  /**
   * Получает все аккаунты
   */
  async getAllAccounts() {
    return await prisma.account.findMany({
      include: {
        _count: {
          select: { videos: true },
        },
      },
      orderBy: {
        lastUsedAt: "desc",
      },
    });
  }

  /**
   * Получает аккаунты с пагинацией
   */
  async getAccountsPaginated(page: number = 1, limit: number = 20) {
    const skip = (page - 1) * limit;

    const [accounts, total] = await Promise.all([
      prisma.account.findMany({
        skip,
        take: limit,
        include: {
          _count: {
            select: { videos: true, hashtags: true },
          },
          hashtags: {
            include: {
              hashtag: true,
            },
          },
        },
        orderBy: {
          lastUsedAt: "desc",
        },
      }),
      prisma.account.count(),
    ]);

    return {
      accounts: accounts.map((acc) => ({
        id: acc.id,
        sessionId: acc.sessionId.substring(0, 12) + "...",
        tiktokUid: acc.tiktokUid,
        userAgent: acc.userAgent,
        followers: acc.followers,
        following: acc.following,
        likes: acc.likes,
        videosCount: acc._count.videos,
        hashtagsCount: acc._count.hashtags,
        hashtags: acc.hashtags.map((ah) => ah.hashtag.tag),
        lastUsedAt: acc.lastUsedAt,
        createdAt: acc.createdAt,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }
}

