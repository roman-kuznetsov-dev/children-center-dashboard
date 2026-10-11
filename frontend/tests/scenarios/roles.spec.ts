import { test, expect } from '@playwright/test';
import { mockApi } from '../helpers/mocks';
import { login } from '../helpers/login';

// ============================================================
// Список ролей и пользователей
// См. Dashboard.tsx: allowedUsers = ['admin', 'boss_1', 'boss_2', 'boss_3']
// ============================================================

// Пользователи, которым кнопка «Сравнить» ДОСТУПНА (точный список)
const CAN_SEE_COMPARISON = ['admin', 'boss_1', 'boss_2', 'boss_3'];

// Список клубов (суффиксы в username)
const CLUBS = ['Айдахар', 'Космоклуб', 'ЛокоМотив', 'ЛокоМотив_Парк'];

// Пользователи, которым кнопка «Сравнить» НЕ доступна.
// Генерируется по шаблонам:
//   - manager_<club>             (по одному на клуб)
//   - supervisor_<club>_1, _2    (по два на клуб)
//   - cashier_<club>_1, _2       (по два на клуб)
const CANNOT_SEE_COMPARISON = [
  ...CLUBS.map((club) => `manager_${club}`),
  ...CLUBS.flatMap((club) => [
    `supervisor_${club}_1`,
    `supervisor_${club}_2`,
    `cashier_${club}_1`,
    `cashier_${club}_2`,
  ]),
];

// ============================================================
// Тесты
// ============================================================

test.describe('Сценарий: роли и доступ к кнопке «Сравнить»', () => {
  // ----- Роли, которым кнопка ДОСТУПНА -----
  for (const username of CAN_SEE_COMPARISON) {
    test(`"${username}" видит кнопку «Сравнить»`, async ({ page }) => {
      await mockApi(page);
      await login(page, username, 'test_pass');

      // На дашборде
      await expect(page).toHaveURL(/\/dashboard/);

      // Username сохранился правильно
      const stored = await page.evaluate(() => localStorage.getItem('username'));
      expect(stored).toBe(username);

      // Кнопка «Сравнить» видна
      await expect(
        page.getByRole('link', { name: '📊 Сравнить' }),
      ).toBeVisible();
    });
  }

  // ----- Роли, которым кнопка НЕ доступна -----
  for (const username of CANNOT_SEE_COMPARISON) {
    test(`"${username}" НЕ видит кнопку «Сравнить»`, async ({ page }) => {
      await mockApi(page);
      await login(page, username, 'test_pass');

      await expect(page).toHaveURL(/\/dashboard/);

      const stored = await page.evaluate(() => localStorage.getItem('username'));
      expect(stored).toBe(username);

      // Кнопки «Сравнить» НЕТ
      await expect(
        page.getByRole('link', { name: '📊 Сравнить' }),
      ).toHaveCount(0);

      // Но дашборд отрендерился (KPI видны)
      await expect(
        page.getByText('Выручка', { exact: true }).first(),
      ).toBeVisible();
    });
  }
});