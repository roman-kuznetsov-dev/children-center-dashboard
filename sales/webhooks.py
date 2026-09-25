import json
from decimal import Decimal
from datetime import datetime

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import CashReceipt, SaleOrder, SaleItem
from users.models import Club


# Маппинг названий клубов (из ОФД) на объекты Club в базе
CLUB_NAME_MAP = {
    'Космоклуб': 'Космоклуб',
    'ЛокоМотив Парк': 'ЛокоМотив Парк',
    'ЛокоМотив': 'ЛокоМотив',
    'Айдахар': 'Айдахар',
}


# Маппинг способов оплаты из ОФД (числа) в наши строки
PAYMENT_TYPE_MAP = {
    1: 'cash',   # наличные
    2: 'card',   # безнал
    3: 'qr',     # QR / СБП
    'cash': 'cash',
    'card': 'card',
    'qr': 'qr',
}


# Маппинг категорий товаров из ОФД в наши категории
CATEGORY_MAP = {
    # Входные билеты / гости
    'входной билет': 'entrance',
    'билет': 'entrance',
    'гость': 'entrance',
    'вход': 'entrance',
    'входной': 'entrance',

    # Праздники
    'праздник': 'party',
    'день рождения': 'party',
    'днюха': 'party',
    'выпускной': 'party',
    'утренник': 'party',

    # Мастер-классы
    'мастер-класс': 'masterclass',
    'мастер класс': 'masterclass',
    'мк': 'masterclass',
    'слайм': 'masterclass',
    'рисование': 'masterclass',
    'кулинария': 'masterclass',
    'лепка': 'masterclass',

    # Аквагрим
    'аквагрим': 'face_painting',
    'грим': 'face_painting',
    'тату': 'face_painting',
    'блеск-тату': 'face_painting',

    # Кафе
    'кафе': 'cafe',
    'капучино': 'cafe',
    'латте': 'cafe',
    'чай': 'cafe',
    'кофе': 'cafe',
    'сок': 'cafe',
    'вода': 'cafe',
    'пицца': 'cafe',
    'чизкейк': 'cafe',
    'мороженое': 'cafe',
    'торт': 'cafe',
    'пирожное': 'cafe',
    'булочка': 'cafe',
    'еда': 'cafe',
    'напиток': 'cafe',

    # Игрушки
    'игрушка': 'toys',
    'игрушки': 'toys',
    'мягкая игрушка': 'toys',
    'lego': 'toys',
    'лего': 'toys',
    'конструктор': 'toys',
    'кукла': 'toys',
    'машинка': 'toys',
    'набор': 'toys',
}


def detect_category(item_name):
    """Определяем категорию по названию товара"""
    if not item_name:
        return 'entrance'  # по умолчанию — входной билет
    name_lower = item_name.lower()
    for key, category in CATEGORY_MAP.items():
        if key in name_lower:
            return category
    return 'entrance'  # по умолчанию


@csrf_exempt
@require_POST
def ofd_webhook(request):
    """
    Webhook для приёма чеков от ОФД.
    В реальности сюда приходит POST от ОФД с данными чека.

    Пример входящего JSON (упрощённый):
    {
        "receipt_id": "OFD-123456789",
        "shop_name": "Космоклуб",
        "total": 5000,
        "payment_method": 2,
        "guests_count": 1,
        "items": [
            {"name": "Входной билет", "quantity": 3, "price": 500},
            {"name": "Кафе", "quantity": 1, "price": 3500}
        ],
        "date": "2026-09-21T14:30:00"
    }
    """
    try:
        # Парсим JSON
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Неверный JSON'}, status=400)

        # Извлекаем данные
        receipt_id = payload.get('receipt_id')
        shop_name = payload.get('shop_name')
        total = payload.get('total')
        payment_method = payload.get('payment_method')
        guests_count = payload.get('guests_count', 1)
        items = payload.get('items', [])
        date_str = payload.get('date')

        # Валидация
        if not receipt_id or not shop_name or total is None:
            return JsonResponse(
                {'error': 'Не хватает обязательных полей: receipt_id, shop_name, total'},
                status=400
            )

        # Ищем клуб
        club_name = CLUB_NAME_MAP.get(shop_name, shop_name)
        try:
            club = Club.objects.get(name=club_name)
        except Club.DoesNotExist:
            return JsonResponse({'error': f'Клуб "{shop_name}" не найден в системе'}, status=404)

        # Определяем способ оплаты
        payment_type = PAYMENT_TYPE_MAP.get(payment_method, 'card')

        # Парсим дату
        if date_str:
            try:
                order_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                order_date = timezone.now()
        else:
            order_date = timezone.now()

        # Создаём чек в CashReceipt
        receipt, created = CashReceipt.objects.get_or_create(
            receipt_id=receipt_id,
            defaults={
                'club': club,
                'total_amount': Decimal(str(total)),
                'payment_type': payment_type,
                'guests_count': guests_count,
                'raw_data': payload,
                'status': 'pending',
            }
        )

        if not created:
            return JsonResponse({'status': 'duplicate', 'message': 'Чек уже существует'})

        # Создаём SaleOrder
        order = SaleOrder.objects.create(
            club=club,
            manager=None,
            date=order_date,
            total_amount=Decimal(str(total)),
            payment_type=payment_type,
            guests_count=guests_count,
        )

        # Создаём SaleItem для каждой позиции
        if items:
            for item in items:
                item_name = item.get('name', '')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)

                SaleItem.objects.create(
                    order=order,
                    category=detect_category(item_name),
                    name=item_name or 'Позиция',
                    quantity=quantity,
                    price=Decimal(str(price)),
                    total=Decimal(str(price)) * quantity,
                )
        else:
            # Если позиций нет — создаём одну позицию "Входной билет"
            SaleItem.objects.create(
                order=order,
                category='entrance',
                name='Входной билет',
                quantity=guests_count,
                price=Decimal(str(total)) / guests_count if guests_count > 0 else Decimal(str(total)),
                total=Decimal(str(total)),
            )

        # Обновляем статус чека
        receipt.status = 'processed'
        receipt.processed_at = timezone.now()
        receipt.save()

        return JsonResponse({
            'status': 'ok',
            'receipt_id': receipt.receipt_id,
            'order_id': order.id,
            'message': 'Чек успешно обработан',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)