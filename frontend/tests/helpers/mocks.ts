import { Page } from '@playwright/test';

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

// Функция для создания мока dashboard с заданными значениями
export function makeDashboardMock(overrides: {
  total_revenue?: number;
  total_orders?: number;
  total_guests?: number;
  avg_check?: number;
} = {}) {
  return {
    kpi: {
      total_revenue: overrides.total_revenue ?? 79435,
      total_orders: overrides.total_orders ?? 7,
      total_guests: overrides.total_guests ?? 28,
      avg_check: overrides.avg_check ?? 11348,
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
}

// Ответ для страницы сравнения
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
export async function mockApi(page: Page): Promise<void> {
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
      body: JSON.stringify(makeDashboardMock()),
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
  // GET /api/orders/export_z_report/ — скачивание Excel
  await page.route('**/api/orders/export_z_report/**', async (route) => {
  // Возвращаем минимальный Excel-файл (xlsx — это ZIP, начинается с PK)
  // Несколько байт достаточно — тест проверяет только факт скачивания.
  const fakeXlsx = Buffer.from([0x50, 0x4b, 0x03, 0x04]); // 'PK\x03\x04'
  await route.fulfill({
    status: 200,
    contentType:
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    headers: {
      'Content-Disposition': 'attachment; filename="z_report.xlsx"',
    },
    body: fakeXlsx,
  });
});
}

// Специальный мок для сценария с фильтром дат:
// возвращает разные KPI в зависимости от start_date
export async function mockApiWithDateFilter(page: Page): Promise<void> {
  // Логин
  await page.route('**/api/token/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_LOGIN_RESPONSE),
    });
  });

  // Dashboard с разными данными в зависимости от периода
  await page.route('**/api/orders/dashboard_summary/**', async (route) => {
    const url = new URL(route.request().url());
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');

    // Для «сегодня» — одни цифры
    // Для прошлого месяца / недели — другие
    // Логика простая: смотрим, за какой период запрос

    const today = new Date().toISOString().split('T')[0];

    let dashboard;
    if (startDate === endDate) {
      // Один день — «Сегодня» или «Выбрать дату»
      dashboard = makeDashboardMock({
        total_revenue: 79435,
        total_orders: 7,
        total_guests: 28,
        avg_check: 11348,
      });
    } else {
      // Диапазон — «Прошлый месяц», «Прошлая неделя», «Текущий месяц»
      dashboard = makeDashboardMock({
        total_revenue: 1234567,
        total_orders: 150,
        total_guests: 480,
        avg_check: 8230,
      });
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(dashboard),
    });
  });

  // Сравнение — на всякий случай, вдруг тест зайдёт
  await page.route('**/api/orders/clubs_comparison/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_CLUBS_COMPARISON_RESPONSE),
    });
  });
}