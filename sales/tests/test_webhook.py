"""
Тесты для Webhook и вспомогательных функций.
"""
from decimal import Decimal

from django.test import TestCase

from sales.models import CashReceipt, SaleItem, SaleOrder
from sales.webhooks import CLUB_NAME_MAP, PAYMENT_TYPE_MAP, detect_category
from users.models import Club


class DetectCategoryTest(TestCase):
    """Тесты функции detect_category()"""

    def test_detect_entrance(self):
        """Входной билет → entrance"""
        self.assertEqual(detect_category('Входной билет'), 'entrance')
        self.assertEqual(detect_category('Билет на вход'), 'entrance')
        self.assertEqual(detect_category('Гость'), 'entrance')

    def test_detect_party(self):
        """Праздник → party"""
        self.assertEqual(detect_category('Праздник'), 'party')
        self.assertEqual(detect_category('День рождения'), 'party')

    def test_detect_masterclass(self):
        """Мастер-класс → masterclass"""
        self.assertEqual(detect_category('Мастер-класс "Слайм"'), 'masterclass')
        self.assertEqual(detect_category('МК "Рисование"'), 'masterclass')

    def test_detect_face_painting(self):
        """Аквагрим → face_painting"""
        self.assertEqual(detect_category('Аквагрим'), 'face_painting')
        self.assertEqual(detect_category('Аквагрим "Тигр"'), 'face_painting')

    def test_detect_cafe(self):
        """Кафе → cafe"""
        self.assertEqual(detect_category('Капучино'), 'cafe')
        self.assertEqual(detect_category('Пицца'), 'cafe')

    def test_detect_toys(self):
        """Игрушки → toys"""
        self.assertEqual(detect_category('Мягкая игрушка'), 'toys')
        self.assertEqual(detect_category('Набор LEGO'), 'toys')

    def test_default_category(self):
        """Неизвестное название → entrance (по умолчанию)"""
        self.assertEqual(detect_category('Что-то непонятное'), 'entrance')
        self.assertEqual(detect_category(''), 'entrance')
        self.assertEqual(detect_category(None), 'entrance')


class PaymentTypeMapTest(TestCase):
    """Тесты маппинга способов оплаты"""

    def test_payment_types(self):
        self.assertEqual(PAYMENT_TYPE_MAP[1], 'cash')
        self.assertEqual(PAYMENT_TYPE_MAP[2], 'card')
        self.assertEqual(PAYMENT_TYPE_MAP[3], 'qr')
        self.assertEqual(PAYMENT_TYPE_MAP['cash'], 'cash')


class ClubNameMapTest(TestCase):
    """Тесты маппинга клубов"""

    def test_club_names(self):
        self.assertEqual(CLUB_NAME_MAP['Космоклуб'], 'Космоклуб')
        self.assertEqual(CLUB_NAME_MAP['ЛокоМотив Парк'], 'ЛокоМотив Парк')


class OFDWebhookTests(TestCase):
    """Интеграционные тесты эндпоинта POST /api/webhooks/ofd/"""

    def setUp(self):
        """Создаём клуб, к которому будет привязан чек"""
        self.club = Club.objects.create(
            name='Космоклуб',
            address='ул. Космическая, 1',
        )
        self.url = '/api/webhooks/ofd/'

    def _make_payload(self, **overrides):
        """
        Хелпер: возвращает валидный payload чека ОФД.
        Можно переопределить любое поле через именованный аргумент.
        """
        payload = {
            'receipt_id': 'OFD-TEST-0001',
            'shop_name': 'Космоклуб',
            'total': 5000,
            'payment_method': 2,  # 2 = card
            'guests_count': 5,
            'items': [
                {'name': 'Входной билет', 'quantity': 3, 'price': 500},
                {'name': 'Капучино', 'quantity': 2, 'price': 250},
            ],
            'date': '2026-10-11T14:00:00+03;00',
        }
        payload.update(overrides)
        return payload

    def test_webhook_creates_order_and_items(self):
        """Успешный чек → создаётся SaleOrder + SaleItem, чек processed"""
        payload = self._make_payload()

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json',
        )

        # 1. HTTP-ответ
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

        # 2. CashReceipt создан и обработан
        receipt = CashReceipt.objects.get(receipt_id='OFD-TEST-0001')
        self.assertEqual(receipt.status, 'processed')
        self.assertIsNotNone(receipt.processed_at)

        # 3. SaleOrder создан
        self.assertEqual(SaleOrder.objects.count(), 1)
        order = SaleOrder.objects.first()
        self.assertEqual(order.club, self.club)
        self.assertEqual(order.total_amount, Decimal('5000'))
        self.assertEqual(order.payment_type, 'card')
        self.assertEqual(order.guests_count, 5)

        # 4. SaleItem созданы — по одному на каждый item
        self.assertEqual(SaleItem.objects.count(), 2)

        # 5. Категории определены правильно (через detect_category)
        ticket = SaleItem.objects.get(name='Входной билет')
        self.assertEqual(ticket.category, 'entrance')

        coffee = SaleItem.objects.get(name='Капучино')
        self.assertEqual(coffee.category, 'cafe')

    def test_webhook_duplicate_receipt_does_not_create_second_order(self):
        """Повторная отправка того же чека не создаёт дубль в БД"""
        payload = self._make_payload(receipt_id='OFD-DUPLICATE-001')

        # 1. Первый POST — создаёт заказ
        response1 = self.client.post(
            self.url,
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()['status'], 'ok')
        self.assertEqual(SaleOrder.objects.count(), 1)
        self.assertEqual(SaleItem.objects.count(), 2)
        self.assertEqual(CashReceipt.objects.count(), 1)

        # 2. Второй POST — тот же чек
        response2 = self.client.post(
            self.url,
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['status'], 'duplicate')

        # 3. Проверяем, что дублей НЕТ
        self.assertEqual(SaleOrder.objects.count(), 1)  # не 2!
        self.assertEqual(SaleItem.objects.count(), 2)   # не 4!
        self.assertEqual(CashReceipt.objects.count(), 1)  # не 2!

    def test_webhook_invalid_json_returns_400(self):
        """Битый JSON → 400 Bad Request, ничего не создаётся"""
        response = self.client.post(
            self.url,
            data='{not a valid json',
            content_type='application/json',
        )

        # 1. HTTP-ответ — 400
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

        # 2. В БД ничего не создалось
        self.assertEqual(SaleOrder.objects.count(), 0)
        self.assertEqual(CashReceipt.objects.count(), 0)

    def test_webhook_missing_required_fields_returns_400(self):
        """Отсутствие обязательного поля → 400, ничего не создаётся"""
        required_fields = ['receipt_id', 'shop_name', 'total']

        for field in required_fields:
            with self.subTest(missing_field=field):
                # Сбрасываем БД между подтестами
                CashReceipt.objects.all().delete()
                SaleOrder.objects.all().delete()
                SaleItem.objects.all().delete()

                payload = self._make_payload()
                del payload[field]

                response = self.client.post(
                    self.url,
                    data=payload,
                    content_type='application/json',
                )

                # 1. HTTP-ответ — 400
                self.assertEqual(
                    response.status_code, 400,
                    f'Ожидался 400 при отсутствии поля "{field}", получен {response.status_code}',
                )
                self.assertIn('error', response.json())

                # 2. В БД ничего не создалось
                self.assertEqual(
                    SaleOrder.objects.count(), 0,
                    f'При отсутствии поля "{field}" создался SaleOrder',
                )
                self.assertEqual(
                    CashReceipt.objects.count(), 0,
                    f'При отсутствии поля "{field}" создался CashReceipt',
                )
