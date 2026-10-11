import { test, expect } from '@playwright/test';
import { mockApi } from '../helpers/mocks';
import { login } from '../helpers/login';

test.describe('Сценарий: выход из системы', () => {
  test('выход очищает токены и возвращает на /login', async ({ page }) => {
    // 1. Моки
    await mockApi(page);

    // 2. Логинимся
    await login(page);

    // 3. Проверяем, что токены сохранены в localStorage
    const accessToken = await page.evaluate(() =>
      localStorage.getItem('access_token'),
    );
    const refreshToken = await page.evaluate(() =>
      localStorage.getItem('refresh_token'),
    );
    const username = await page.evaluate(() => localStorage.getItem('username'));

    expect(accessToken).toBeTruthy();
    expect(refreshToken).toBeTruthy();
    expect(username).toBe('admin');

    // 4. Кликаем «Выйти»
    await page.getByRole('button', { name: '🚪 Выйти' }).click();

    // 5. Проверяем редирект на /login
    await expect(page).toHaveURL(/\/login/);

    // 6. Проверяем, что localStorage очищен
    const accessTokenAfter = await page.evaluate(() =>
      localStorage.getItem('access_token'),
    );
    const refreshTokenAfter = await page.evaluate(() =>
      localStorage.getItem('refresh_token'),
    );
    const usernameAfter = await page.evaluate(() =>
      localStorage.getItem('username'),
    );

    expect(accessTokenAfter).toBeNull();
    expect(refreshTokenAfter).toBeNull();
    expect(usernameAfter).toBeNull();

    // 7. Пытаемся зайти на /dashboard напрямую — редирект на /login
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});