import { test, expect } from '@playwright/test';

test.describe('Smoke tests', () => {
  test('страница входа открывается', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Вход в систему' })).toBeVisible();
    await expect(page.getByPlaceholder('Введите логин')).toBeVisible();
    await expect(page.getByPlaceholder('Введите пароль')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();
  });

  test('вход под админом работает', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Введите логин').fill('admin');
    await page.getByPlaceholder('Введите пароль').fill('admin123');
    await page.getByRole('button', { name: 'Войти' }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: '🏠 Дашборд' })).toBeVisible();
  });

  test('дашборд показывает KPI карточки', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Введите логин').fill('admin');
    await page.getByPlaceholder('Введите пароль').fill('admin123');
    await page.getByRole('button', { name: 'Войти' }).click();

    await expect(page).toHaveURL(/\/dashboard/);

    await expect(page.getByText('Выручка', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Продаж', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Гости (входные билеты)', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Ср. чек', { exact: true }).first()).toBeVisible();
  });

  test('страница сравнения открывается', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Введите логин').fill('admin');
    await page.getByPlaceholder('Введите пароль').fill('admin123');
    await page.getByRole('button', { name: 'Войти' }).click();

    await expect(page).toHaveURL(/\/dashboard/);

    await page.getByRole('link', { name: '📊 Сравнить' }).click();

    await expect(page).toHaveURL(/\/comparison/);
    await expect(page.getByRole('heading', { name: /Сравнение/ })).toBeVisible();
  });
});