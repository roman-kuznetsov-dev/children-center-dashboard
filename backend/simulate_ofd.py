import os
import sys
import time
import random
import requests
from datetime import datetime
from decimal import Decimal

# URL нашего Webhook
WEBHOOK_URL = 'http://127.0.0.1:8000/api/webhooks/ofd/'

# Названия клубов (должны совпадать с базой)
CLUBS = ['Космоклуб', 'ЛокоМотив Парк', 'ЛокоМотив', 'Айдахар']

# Способы оплаты (как в ОФД): 1 — нал, 2 — безнал, 3 — QR
PAYMENT_METHODS = [1, 2, 3]

# Категории товаров и их цены (реалистичные)
GOODS = {
    'entrance': {'names': ['Входной билет', 'Билет на вход', 'Гость'], 'price': (200, 800), 'weight': 50},
    'cafe': {'names': ['Капучино', 'Чизкейк', 'Сок', 'Пицца', 'Мороженое'], 'price': (150, 600), 'weight': 30},
    'toys': {'names': ['Мягкая игрушка', 'Набор LEGO', 'Кукла'], 'price': (300, 1500), 'weight': 15},
    'masterclass': {'names': ['Мастер-класс "Слайм"', 'Мастер-класс "Рисование"', 'МК "Кулинария"'], 'price': (500, 2000), 'weight': 10},
    'face_painting': {'names': ['Аквагрим', 'Аквагрим "Тигр"', 'Аквагрим "Бабочка"'], 'price': (300, 800), 'weight': 10},
    'party': {'names': ['День рождения', 'Праздник "Пираты"', 'Выпускной'], 'price': (5000, 20000), 'weight': 5},
}


def pick_good():
    """Выбираем случайный товар с учётом веса"""
    categories = list(GOODS.keys())
    weights = [GOODS[c]['weight'] for c in categories]
    category = random.choices(categories, weights=weights, k=1)[0]
    good_info = GOODS[category]
    name = random.choice(good_info['names'])
    price = random.randint(good_info['price'][0], good_info['price'][1])
    return name, price


def generate_receipt():
    """Генерируем случайный чек"""
    receipt_id = f"OFD-{int(time.time())}-{random.randint(1000, 9999)}"
    club = random.choice(CLUBS)
    payment_method = random.choice(PAYMENT_METHODS)

    # Генерируем 1-3 позиции
    items_count = random.randint(1, 3)
    items = []
    total = 0

    for _ in range(items_count):
        name, price = pick_good()
        quantity = random.randint(1, 5)
        items.append({
            'name': name,
            'quantity': quantity,
            'price': price,
        })
        total += price * quantity

    # Гости (только для входных билетов, иначе 1)
    has_entrance = any('билет' in item['name'].lower() or 'гость' in item['name'].lower() for item in items)
    guests_count = sum(item['quantity'] for item in items if 'билет' in item['name'].lower() or 'гость' in item['name'].lower()) if has_entrance else 1

    return {
        'receipt_id': receipt_id,
        'shop_name': club,
        'total': total,
        'payment_method': payment_method,
        'guests_count': guests_count,
        'items': items,
        'date': datetime.now().isoformat(),
    }


def send_receipt(receipt):
    """Отправляем чек на Webhook"""
    try:
        response = requests.post(WEBHOOK_URL, json=receipt, timeout=5)
        if response.status_code == 200:
            data = response.json()
            payment_names = {1: 'нал', 2: 'безнал', 3: 'QR'}
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] {receipt['shop_name']}: {receipt['total']} ₽ ({payment_names.get(receipt['payment_method'], '?')}) → Заказ #{data.get('order_id')}")
        else:
            print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Ошибка {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")


def run():
    """Основной цикл: каждые 10-30 секунд отправляем новый чек"""
    print("🚀 Запуск имитатора касс ОФД...")
    print(f"📡 Webhook: {WEBHOOK_URL}")
    print("⏱️  Интервал: 10-30 секунд между чеками")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("-" * 60)

    try:
        while True:
            receipt = generate_receipt()
            send_receipt(receipt)
            delay = random.randint(10, 30)
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\n🛑 Имитатор остановлен.")


if __name__ == '__main__':
    run()