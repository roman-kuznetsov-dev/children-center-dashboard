import { test, expect } from '@playwright/test';
import { mockApi } from '../helpers/mocks';
import { login } from '../helpers/login';

test.describe('Сценарий: скачивание Z-отчёта', () => {
  test('Z-отчёт скачивается как xlsx', async ({ page }) => {
    // 1. Моки
    await mockApi(page);

    // 2. Готовим обработчик для prompt с датой.
    // По умолчанию prompt блокирует test, поэтому мы его принимаем
    // и вводим фиксированную дату.
    page.on('dialog', async (dialog) => {
      expect(dialog.type()).toBe('prompt');
      await dialog.accept('2026-10-11');
    });

    // 3. Логинимся
    await login(page);

    // 4. Начинаем ждать события download (до клика!)
    const downloadPromise = page.waitForEvent('download');

    // 5. Кликаем по кнопке «Z-отчёт» — откроется prompt, мы введём дату
    await page.getByRole('button', { name: '📥 Z-отчёт' }).click();

    // 6. Ждём, что скачивание произошло
    const download = await downloadPromise;

    // 7. Проверяем имя файла
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/z_report.*\.xlsx$/);

    // 8. Сохраняем файл и проверяем, что он реально существует
    const path = await download.path();
    expect(path).toBeTruthy();
  });
});