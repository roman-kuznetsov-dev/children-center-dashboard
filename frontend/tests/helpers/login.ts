import { Page, expect } from '@playwright/test';

/**
 * Хелпер: выполняет логин через UI.
 * Предполагает, что mockApi(page) уже вызван.
 * После логина проверяет, что мы на /dashboard.
 */
export async function login(
  page: Page,
  username = 'admin',
  password = 'admin123',
): Promise<void> {
  await page.goto('/login');
  await page.getByPlaceholder('Введите логин').fill(username);
  await page.getByPlaceholder('Введите пароль').fill(password);
  await page.getByRole('button', { name: 'Войти' }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}