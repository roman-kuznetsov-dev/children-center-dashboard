import { test, expect } from '@playwright/test';
import { mockApiWithDateFilter } from '../helpers/mocks';
import { login } from '../helpers/login';

test.describe('Сценарий: фильтр по датам на дашборде', () => {
  test('переключение периода меняет KPI на дашборде', async ({ page }) => {
    // 1. Устанавливаем моки (разные данные для дня и для диапазона)
    await mockApiWithDateFilter(page);

    // 2. Логинимся
    await login(page);

    // 3. Проверяем, что на старте показан период «Сегодня»
    // и KPI соответствует моку для одного дня (79435)
    await expect(page.getByText('79 435 ₽').first()).toBeVisible();

    // 4. Переключаемся на «Прошлый месяц»
    await page.getByRole('button', { name: '📆 Прошлый месяц' }).click();

    // 5. Ждём, что данные обновились — новое значение из мока (1 234 567 ₽)
    await expect(page.getByText('1 234 567 ₽').first()).toBeVisible({
      timeout: 5000,
    });

    // 6. Старое значение больше не видно (проверяем, что данные реально заменились)
    await expect(page.getByText('79 435 ₽')).toHaveCount(0);

    // 7. Переключаемся на «Прошлую неделю»
    await page.getByRole('button', { name: '📅 Прошлая неделя' }).click();

    // 8. Данные остаются за диапазон (1 234 567 ₽)
    await expect(page.getByText('1 234 567 ₽').first()).toBeVisible();

    // 9. Возвращаемся на «Сегодня»
    await page.getByRole('button', { name: '📅 Сегодня' }).click();

    // 10. Данные снова соответствуют одному дню (79 435 ₽)
    await expect(page.getByText('79 435 ₽').first()).toBeVisible();
  });
});