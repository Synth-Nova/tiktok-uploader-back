import { exec } from "child_process";
import { promisify } from "util";
import { log } from "../utils";

const execAsync = promisify(exec);

async function killChromeProcesses() {
  const isWindows = process.platform === "win32";

  try {
    log("🔍 Поиск Chrome процессов...");

    let command: string;
    let killCommand: string;

    if (isWindows) {
      // Windows команды - ищем процессы отдельно
      try {
        let chromeCount = 0;
        let chromedriverCount = 0;

        // Ищем chrome.exe
        try {
          const { stdout: chromeOut } = await execAsync('tasklist /FI "IMAGENAME eq chrome.exe"');
          chromeCount = (chromeOut.match(/chrome\.exe/gi) || []).length;
        } catch (e) {
          // Процессы не найдены
        }

        // Ищем chromedriver.exe
        try {
          const { stdout: driverOut } = await execAsync('tasklist /FI "IMAGENAME eq chromedriver.exe"');
          chromedriverCount = (driverOut.match(/chromedriver\.exe/gi) || []).length;
        } catch (e) {
          // Процессы не найдены
        }

        const total = chromeCount + chromedriverCount;

        log(`📊 Найдено процессов:`);
        log(`   - Chrome: ${chromeCount}`);
        log(`   - ChromeDriver: ${chromedriverCount}`);
        log(`   - Всего: ${total}`);

        if (total === 0) {
          log("✅ Chrome процессы не найдены");
          return;
        }

        log("🗑️ Принудительное завершение всех Chrome процессов...");

        // Убиваем все процессы
        let killedChrome = false;
        let killedDriver = false;

        if (chromeCount > 0) {
          try {
            await execAsync("taskkill /F /IM chrome.exe /T");
            killedChrome = true;
            log(`✅ Завершено ${chromeCount} процессов chrome.exe`);
          } catch (e: any) {
            log(`⚠️ Ошибка при завершении chrome.exe: ${e.message}`);
          }
        }

        if (chromedriverCount > 0) {
          try {
            await execAsync("taskkill /F /IM chromedriver.exe /T");
            killedDriver = true;
            log(`✅ Завершено ${chromedriverCount} процессов chromedriver.exe`);
          } catch (e: any) {
            log(`⚠️ Ошибка при завершении chromedriver.exe: ${e.message}`);
          }
        }

        if (killedChrome || killedDriver) {
          log(`✅ Все Chrome процессы (${total}) успешно завершены`);
        }
      } catch (error: any) {
        log(`⚠️ Ошибка: ${error.message}`);
      }
    } else {
      // macOS/Linux команды
      try {
        const { stdout: chromePs } = await execAsync(
          "ps aux | grep -i chrome | grep -v grep || true"
        );
        const { stdout: driverPs } = await execAsync(
          "ps aux | grep -i chromedriver | grep -v grep || true"
        );

        const chromeLines = chromePs
          .trim()
          .split("\n")
          .filter((l) => l.length > 0);
        const driverLines = driverPs
          .trim()
          .split("\n")
          .filter((l) => l.length > 0);
        const total = chromeLines.length + driverLines.length;

        log(`📊 Найдено процессов:`);
        log(`   - Chrome: ${chromeLines.length}`);
        log(`   - ChromeDriver: ${driverLines.length}`);
        log(`   - Всего: ${total}`);

        if (total === 0) {
          log("✅ Chrome процессы не найдены");
          return;
        }

        log("🗑️ Принудительное завершение всех Chrome процессов...");

        await execAsync("pkill -9 -i chrome || true");
        await execAsync("pkill -9 -i chromedriver || true");

        log(`✅ Все Chrome процессы (${total}) успешно завершены`);
      } catch (error: any) {
        log(`⚠️ Ошибка: ${error.message}`);
      }
    }
  } catch (error: any) {
    log(`❌ Ошибка при завершении Chrome процессов: ${error.message}`);
    process.exit(1);
  }
}

// Запуск
log("🧹 Утилита для очистки Chrome процессов");
log("⚠️  ВНИМАНИЕ: Эта команда завершит ВСЕ Chrome процессы на системе!");
log("⚠️  Используйте только если worker'ы зависли и не отвечают.");
log("");

killChromeProcesses()
  .then(() => process.exit(0))
  .catch((err) => {
    log(`❌ Критическая ошибка: ${err.message}`);
    process.exit(1);
  });
