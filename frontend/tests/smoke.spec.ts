import { test, expect, Page } from '@playwright/test';

// ============================================================
// Моки API
// Playwright перехватывает запросы к бэкенду и возвращает
// заранее подготовленные ответы. Это позволяет тестам работать
// без реального API — важно для CI, где бэкенд не запущен.
// ============================================================

// Ответ на POST /api/token/ — как отдаёт Django SimpleJWT
const MOCK_LOGIN_RESPONSE = {
  access: 'fake-access-token-for-tests',
  refresh: 'fake-refresh-token-for-tests',
};

// Ответ на GET /api/orders/dashboard_summary/
// Формат точно совпадает с тем, что читает src/components/Dashboard.tsx
const MOCK_DASHBOARD_RESPONSE = {
  kpi: {
    total_revenue: 79435,
    total_orders: 7,
    total_guests: 28,
    avg_check: 11348,
    cash: 20000,
    card: 30000,
    qr: 29435,
  },
  categories: {
    party: { name: 'Праздники', total: 43365, count: 5 },
    masterclass: { name: 'Мастер-классы', total: 5972, count: 6 },
    face_painting: { name: 'Аквагрим', total: 4059, count: 3 },
    cafe: { name: 'Кафе', total: 7388, count: 4 },
    toys: { name: 'Игрушки', total: 1476, count: 7 },
    entrance: { name: 'Гости (входные билеты)', total: 17175, count: 28 },
  },
};

// Ответ на GET /api/orders/clubs_comparison/
// Формат из src/components/ClubsComparison.tsx
const MOCK_CLUBS_COMPARISON_RESPONSE = [
  {
    club_name: 'Клуб №1',
    total_revenue: 79435,
    cash: 20000,
    card: 30000,
    qr: 29435,
    total_guests: 28,
    categories: {
      party: 43365,
      masterclass: 5972,
      face_painting: 4059,
      cafe: 7388,
      toys: 1476,
      entrance: 17175,
    },
    categories_count: {
      party: 5,
      masterclass: 6,
      face_painting: 3,
      cafe: 4,
      toys: 7,
      entrance: 28,
    },
  },
];

// Устанавливаем моки на все API-запросы страницы.
// Вызывать ДО page.goto().
async function mockApi(page: Page) {
  // POST /api/token/ — логин
  await page.route('**/api/token/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_LOGIN_RESPONSE),
    });
  });

  // GET /api/orders/dashboard_summary/ — KPI дашборда
  await page.route('**/api/orders/dashboard_summary/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_DASHBOARD_RESPONSE),
    });
  });

  // GET /api/orders/clubs_comparison/ — страница сравнения
  await page.route('**/api/orders/clubs_comparison/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_CLUBS_COMPARISON_RESPONSE),
    });
  });
}

// ============================================================
// Тесты
// ============================================================

test.describe('Smoke tests', () => {
  test('страница входа открывается', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Вход в систему' })).toBeVisible();
    await expect(page.getByPlaceholder('Введите логин')).toBeVisible();
    await expect(page.getByPlaceholder('Введите пароль')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();
  });

  test('вход под админом работает', async ({ page }) => {
    await mockApi(page);

    await page.goto('/login');
    await page.getByPlaceholder('Введите логин').fill('admin');
    await page.getByPlaceholder('Введите пароль').fill('admin123');
    await page.getByRole('button', { name: 'Войти' }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: '🏠 Дашборд' })).toBeVisible();
  });

  test('дашборд показывает KPI карточки', async ({ page }) => {
    await mockApi(page);

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
    await mockApi(page);

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