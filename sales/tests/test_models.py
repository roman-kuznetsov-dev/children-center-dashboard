"""
Юнит-тесты для моделей.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from users.models import Club, User
from sales.models import SaleOrder, SaleItem, CashReceipt


class SaleItemModelTest(TestCase):
    """Тесты модели SaleItem"""

    def setUp(self):
        """Создаём тестовые данные перед каждым тестом"""
        self.club = Club.objects.create(name='Тестовый клуб', address='ул. Тестовая, 1')
        self.user = User.objects.create_user(
            username='test_manager',
            password='123',
            role='manager',
            club=self.club,
        )
        self.order = SaleOrder.objects.create(
            club=self.club,
            manager=self.user,
            date=timezone.now(),
            total_amount=Decimal('1000.00'),
            payment_type='card',
            guests_count=5,
        )

    def test_total_calculated_automatically(self):
        """При сохранении позиции total = quantity × price"""
        item = SaleItem.objects.create(
            order=self.order,
            category='masterclass',
            name='Мастер-класс',
            quantity=3,
            price=Decimal('500.00'),
        )
        self.assertEqual(item.total, Decimal('1500.00'))

    def test_total_updates_on_save(self):
        """При изменении quantity total пересчитывается"""
        item = SaleItem.objects.create(
            order=self.order,
            category='cafe',
            name='Капучино',
            quantity=2,
            price=Decimal('200.00'),
        )
        self.assertEqual(item.total, Decimal('400.00'))

        item.quantity = 5
        item.save()
        self.assertEqual(item.total, Decimal('1000.00'))

    def test_item_str_representation(self):
        """Строковое представление позиции"""
        item = SaleItem.objects.create(
            order=self.order,
            category='entrance',
            name='Входной билет',
            quantity=2,
            price=Decimal('300.00'),
        )
        self.assertIn('Входной билет', str(item))


class SaleOrderModelTest(TestCase):
    """Тесты модели SaleOrder"""

    def test_order_str_representation(self):
        club = Club.objects.create(name='Космоклуб', address='адрес')
        order = SaleOrder.objects.create(
            club=club,
            date=timezone.now(),
            total_amount=Decimal('5000.00'),
            payment_type='cash',
            guests_count=10,
        )
        self.assertIn('Космоклуб', str(order))


class CashReceiptModelTest(TestCase):
    """Тесты модели CashReceipt (чеки из ОФД)"""

    def test_receipt_created(self):
        club = Club.objects.create(name='Космоклуб', address='адрес')
        receipt = CashReceipt.objects.create(
            receipt_id='TEST-001',
            club=club,
            total_amount=Decimal('1500.00'),
            payment_type='card',
            guests_count=1,
            raw_data={'test': 'data'},
        )
        self.assertEqual(receipt.status, 'pending')
        self.assertIn('TEST-001', str(receipt))