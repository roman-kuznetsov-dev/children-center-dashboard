import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from users.models import Club, User
from sales.models import SaleOrder, SaleItem

# Настройки генерации
DAYS_BACK = 90
CLUBS_NAMES = ['Космоклуб', 'ЛокоМотив Парк', 'ЛокоМотив', 'Айдахар']

# Категории и их характеристики (вероятность, диапазон цены)
CATEGORIES = {
    'party':         {'weight': 20, 'min': 5000,  'max': 25000},  # Праздники
    'masterclass':   {'weight': 40, 'min': 500,   'max': 3000},   # Мастер-классы
    'face_painting': {'weight': 30, 'min': 300,   'max': 1500},   # Аквагрим
    'cafe':          {'weight': 50, 'min': 200,   'max': 2000},   # Кафе
    'toys':          {'weight': 25, 'min': 100,   'max': 800},    # Игрушки
    'entrance':      {'weight': 60, 'min': 200, 'max': 1000},     # Входные билеты - самые частые
}

PAYMENT_TYPES = ['cash', 'card', 'qr']
PAYMENT_WEIGHTS = [30, 50, 20]  # 30% нал, 50% безнал, 20% QR


def pick_category():
    categories = list(CATEGORIES.keys())
    weights = [CATEGORIES[c]['weight'] for c in categories]
    return random.choices(categories, weights=weights, k=1)[0]


def pick_payment():
    return random.choices(PAYMENT_TYPES, weights=PAYMENT_WEIGHTS, k=1)[0]


def run():
    print("🚀 Начинаем генерацию реалистичных данных...")
    
    # Проверяем клубы
    clubs = list(Club.objects.filter(name__in=CLUBS_NAMES))
    if not clubs:
        print("❌ Нет клубов. Сначала создайте клубы через админку.")
        return
    
    print(f"✅ Найдено клубов: {len(clubs)}")
    
    # Проверяем менеджеров
    managers = list(User.objects.filter(role='manager'))
    if not managers:
        print("❌ Нет менеджеров. Сначала создайте менеджеров.")
        return
    
    # Очищаем старые данные за последние 90 дней
    cutoff = datetime.now() - timedelta(days=DAYS_BACK)
    old_count = SaleOrder.objects.filter(date__gte=cutoff).count()
    if old_count > 0:
        print(f"🗑️ Удаляем {old_count} старых заказов за последние {DAYS_BACK} дней...")
        SaleOrder.objects.filter(date__gte=cutoff).delete()
    
    total_sales = 0
    total_items = 0
    
    for day_offset in range(DAYS_BACK):
        current_date = datetime.now() - timedelta(days=day_offset)
        weekday = current_date.weekday()
        is_weekend = weekday >= 4  # Пт, Сб, Вс
        month = current_date.month
        
        if is_weekend:
            daily_orders = random.randint(12, 25)
        else:
            daily_orders = random.randint(5, 15)
        
        if month in [6, 7, 8]:
            daily_orders = int(daily_orders * 1.4)
        elif month in [12, 1, 2]:
            daily_orders = int(daily_orders * 0.7)
        
        for _ in range(daily_orders):
            club = random.choice(clubs)
            club_managers = [m for m in managers if m.club_id == club.id]
            manager = random.choice(club_managers) if club_managers else random.choice(managers)
            
            guests = random.randint(3, 40)
            
            order_time = current_date.replace(
                hour=random.randint(10, 20),
                minute=random.choice([0, 15, 30, 45]),
                second=0,
                microsecond=0
            )
            
            order = SaleOrder.objects.create(
                club=club,
                manager=manager,
                date=order_time,
                total_amount=Decimal(0),
                payment_type=pick_payment(),
                guests_count=guests,
            )
            
            items_count = random.randint(1, 3)
            order_total = Decimal(0)
            
            for _ in range(items_count):
                category = pick_category()
                cat_info = CATEGORIES[category]
                
                quantity = random.randint(1, 5)
                price = Decimal(random.randint(cat_info['min'], cat_info['max']))
                item_total = price * quantity
                
                SaleItem.objects.create(
                    order=order,
                    category=category,
                    name=f"{dict(SaleItem.CATEGORY_CHOICES)[category]}",
                    quantity=quantity,
                    price=price,
                    total=item_total,
                )
                
                order_total += item_total
                total_items += 1
            
            order.total_amount = order_total
            order.save()
            total_sales += 1
    
    print(f"✅ Создано заказов: {total_sales}")
    print(f"✅ Создано позиций: {total_items}")
    print("🎉 Готово!")


if __name__ == '__main__':
    run()