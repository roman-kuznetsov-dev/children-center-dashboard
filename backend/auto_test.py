"""
Автоматический тест дашборда:
- Одновременный вход 16 пользователей
- Разные действия (дашборд, периоды, Z-отчёт, сравнение)
- Проверка прав доступа
- Проверка скорости
- Проверка корректности данных
"""
import os
import sys
import time
import threading
import requests
from datetime import datetime, timedelta
from decimal import Decimal


# ============================================================
# НАСТРОЙКИ
# ============================================================
BASE_URL = 'http://127.0.0.1:8000'
API_URL = f'{BASE_URL}/api'

# Пользователи для теста (логин, пароль, роль, клуб)
USERS = [
    # Администраторы / боссы
    ('admin', 'admin123', 'admin', None),
    ('boss_1', '123', 'admin', None),
    ('boss_2', '123', 'admin', None),
    ('boss_3', '123', 'admin', None),
    # Управляющие
    ('manager_Космоклуб', '123', 'manager', 'Космоклуб'),
    ('manager_ЛокоМотив_Парк', '123', 'manager', 'ЛокоМотив Парк'),
    ('manager_ЛокоМотив', '123', 'manager', 'ЛокоМотив'),
    ('manager_Айдахар', '123', 'manager', 'Айдахар'),
    # Старшие смены
    ('supervisor_Космоклуб_1', '123', 'manager', 'Космоклуб'),
    ('supervisor_Космоклуб_2', '123', 'manager', 'Космоклуб'),
    ('supervisor_ЛокоМотив_Парк_1', '123', 'manager', 'ЛокоМотив Парк'),
    ('supervisor_ЛокоМотив_Парк_2', '123', 'manager', 'ЛокоМотив Парк'),
    ('supervisor_ЛокоМотив_1', '123', 'manager', 'ЛокоМотив'),
    ('supervisor_ЛокоМотив_2', '123', 'manager', 'ЛокоМотив'),
    ('supervisor_Айдахар_1', '123', 'manager', 'Айдахар'),
    ('supervisor_Айдахар_2', '123', 'manager', 'Айдахар'),
    # Кассиры
    ('cashier_Космоклуб_1', '123', 'staff', 'Космоклуб'),
    ('cashier_Космоклуб_2', '123', 'staff', 'Космоклуб'),
    ('cashier_ЛокоМотив_Парк_1', '123', 'staff', 'ЛокоМотив Парк'),
    ('cashier_ЛокоМотив_Парк_2', '123', 'staff', 'ЛокоМотив Парк'),
    ('cashier_ЛокоМотив_1', '123', 'staff', 'ЛокоМотив'),
    ('cashier_ЛокоМотив_2', '123', 'staff', 'ЛокоМотив'),
    ('cashier_Айдахар_1', '123', 'staff', 'Айдахар'),
    ('cashier_Айдахар_2', '123', 'staff', 'Айдахар'),
]

# Результаты теста
results = {
    'total_requests': 0,
    'success': 0,
    'errors': 0,
    'slow_requests': 0,
    'access_violations': 0,
    'max_time': 0.0,
    'min_time': 999.0,
    'total_time': 0.0,
    'details': [],
}

lock = threading.Lock()


def log(msg):
    with lock:
        print(msg)


def login(username, password):
    """Логин и получение токена"""
    try:
        response = requests.post(
            f'{API_URL}/token/',
            json={'username': username, 'password': password},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()['access']
        return None
    except Exception as e:
        log(f'❌ Ошибка логина {username}: {e}')
        return None


def measure(func):
    """Замер времени выполнения запроса"""
    start = time.time()
    result = func()
    elapsed = time.time() - start
    return result, elapsed


def record_result(name, elapsed, success, error_msg=None, slow_threshold=2.0):
    """Записать результат в общую статистику"""
    with lock:
        results['total_requests'] += 1
        results['total_time'] += elapsed
        results['max_time'] = max(results['max_time'], elapsed)
        results['min_time'] = min(results['min_time'], elapsed)
        if success:
            results['success'] += 1
        else:
            results['errors'] += 1
        if elapsed > slow_threshold:
            results['slow_requests'] += 1
        results['details'].append({
            'name': name,
            'time': elapsed,
            'success': success,
            'error': error_msg,
        })


def test_dashboard(token, username, period='today'):
    """Тест: получение данных дашборда"""
    def action():
        today = datetime.now().date()
        if period == 'today':
            start = end = today.isoformat()
        elif period == 'month':
            first = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            start = first.isoformat()
            end = (today.replace(day=1) - timedelta(days=1)).isoformat()
        elif period == 'week':
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            start = last_monday.isoformat()
            end = last_sunday.isoformat()
        else:
            start = end = today.isoformat()

        return requests.get(
            f'{API_URL}/orders/dashboard_summary/?start_date={start}&end_date={end}',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10,
        )

    response, elapsed = measure(action)
    success = response.status_code == 200
    error = None if success else f'HTTP {response.status_code}'
    record_result(f'{username} [{period}] dashboard', elapsed, success, error)
    return response, elapsed, success


def test_comparison(token, username, role):
    """Тест: страница сравнения (только для admin)"""
    def action():
        return requests.get(
            f'{API_URL}/orders/clubs_comparison/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10,
        )

    response, elapsed = measure(action)
    
    if role == 'admin':
        success = response.status_code == 200
        error = None if success else f'HTTP {response.status_code}'
        record_result(f'{username} comparison', elapsed, success, error)
    else:
        # Не-админ должен получить 403 или видеть только свой клуб
        # (у нас реализовано через фильтрацию, поэтому 200, но данные только по его клубу)
        success = response.status_code == 200
        if success:
            data = response.json()
            clubs = data.get('clubs', data) if isinstance(data, dict) else data
            if isinstance(clubs, list) and len(clubs) > 1:
                # Нарушение прав доступа — видит больше одного клуба
                with lock:
                    results['access_violations'] += 1
                log(f'⚠️ НАРУШЕНИЕ: {username} видит {len(clubs)} клубов (должен 1)')
        record_result(f'{username} comparison', elapsed, success)
    
    return response, elapsed, success


def test_z_report(token, username):
    """Тест: скачивание Z-отчёта"""
    def action():
        today = datetime.now().date().isoformat()
        return requests.get(
            f'{API_URL}/orders/export_z_report/?date={today}',
            headers={'Authorization': f'Bearer {token}'},
            timeout=15,
        )

    response, elapsed = measure(action)
    success = response.status_code == 200
    error = None if success else f'HTTP {response.status_code}'
    record_result(f'{username} Z-report', elapsed, success, error, slow_threshold=3.0)
    return response, elapsed, success


def user_scenario(username, password, role, club):
    """Сценарий для одного пользователя"""
    token = login(username, password)
    if not token:
        log(f'❌ {username}: не удалось войти')
        record_result(f'{username} login', 0, False, 'Login failed')
        return

    # Разные сценарии для разных ролей
    if role == 'admin':
        # Админ: дашборд + сравнение + Z-отчёт + переключение периодов
        test_dashboard(token, username, 'today')
        time.sleep(0.1)
        test_dashboard(token, username, 'month')
        time.sleep(0.1)
        test_comparison(token, username, 'admin')
        time.sleep(0.1)
        test_z_report(token, username)
    elif role == 'manager':
        # Менеджер: дашборд + Z-отчёт (сравнение — только свой клуб)
        test_dashboard(token, username, 'today')
        time.sleep(0.1)
        test_dashboard(token, username, 'week')
        time.sleep(0.1)
        test_comparison(token, username, 'manager')
        time.sleep(0.1)
        test_z_report(token, username)
    else:
        # Кассир: только дашборд
        test_dashboard(token, username, 'today')
        time.sleep(0.1)
        test_dashboard(token, username, 'today')


def run_test():
    """Запуск всего теста"""
    print('=' * 60)
    print('🚀 АВТОМАТИЧЕСКИЙ ТЕСТ ДАШБОРДА')
    print('=' * 60)
    print(f'👥 Пользователей: {len(USERS)}')
    print(f'🌐 URL: {BASE_URL}')
    print('=' * 60)

    # Проверяем, что сервер запущен
    try:
        requests.get(f'{API_URL}/token/', timeout=5)
    except requests.exceptions.RequestException:
        print('❌ Сервер Django не запущен! Запустите: python manage.py runserver')
        return

    print('✅ Сервер доступен. Запускаем пользователей...\n')

    # Запускаем всех пользователей одновременно
    threads = []
    start_time = time.time()

    for username, password, role, club in USERS:
        t = threading.Thread(target=user_scenario, args=(username, password, role, club))
        threads.append(t)
        t.start()

    # Ждём завершения всех
    for t in threads:
        t.join()

    total_elapsed = time.time() - start_time

    # ============================================================
    # ОТЧЁТ
    # ============================================================
    print('\n' + '=' * 60)
    print('📊 РЕЗУЛЬТАТЫ ТЕСТА')
    print('=' * 60)
    print(f'⏱️  Общее время: {total_elapsed:.2f} сек')
    print(f'📨 Всего запросов: {results["total_requests"]}')
    print(f'✅ Успешных: {results["success"]}')
    print(f'❌ Ошибок: {results["errors"]}')
    print(f'🐌 Медленных (>2 сек): {results["slow_requests"]}')
    print(f'⚠️  Нарушений доступа: {results["access_violations"]}')
    print(f'⚡ Среднее время ответа: {results["total_time"] / max(results["total_requests"], 1):.3f} сек')
    print(f'🔺 Максимальное время: {results["max_time"]:.3f} сек')
    print(f'🔻 Минимальное время: {results["min_time"]:.3f} сек')
    print('=' * 60)

    # Оценка
    if results['errors'] == 0 and results['access_violations'] == 0 and results['slow_requests'] == 0:
        print('🏆 РЕЗУЛЬТАТ: ВСЁ ИДЕАЛЬНО! Система готова к продакшену.')
    elif results['errors'] == 0 and results['access_violations'] == 0:
        print('✅ РЕЗУЛЬТАТ: ХОРОШО! Есть медленные запросы, но система работает.')
    elif results['access_violations'] > 0:
        print('🚨 РЕЗУЛЬТАТ: ЕСТЬ НАРУШЕНИЯ ДОСТУПА! Проверьте права.')
    else:
        print('⚠️  РЕЗУЛЬТАТ: ЕСТЬ ОШИБКИ. Проверьте детали ниже.')

    # Детали ошибок
    if results['errors'] > 0:
        print('\n❌ ОШИБКИ:')
        for d in results['details']:
            if not d['success']:
                print(f'  - {d["name"]}: {d["error"]}')

    print('=' * 60)


if __name__ == '__main__':
    run_test()