"""
Тесты прав доступа.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import Club, User
from sales.models import SaleOrder


class PermissionsTest(TestCase):
    """Проверка прав доступа для разных ролей"""

    def setUp(self):
        self.client = APIClient()
        self.club1 = Club.objects.create(name='Космоклуб', address='адрес1')
        self.club2 = Club.objects.create(name='ЛокоМотив', address='адрес2')
        self.admin = User.objects.create_user(
            username='admin_test', password='123', role='admin'
        )
        self.manager1 = User.objects.create_user(
            username='manager1', password='123', role='manager', club=self.club1
        )
        self.manager2 = User.objects.create_user(
            username='manager2', password='123', role='manager', club=self.club2
        )

    def test_manager_does_not_see_other_club_data(self):
        """Manager1 не видит данные клуба Manager2"""
        SaleOrder.objects.create(
            club=self.club2,
            date=timezone.now(),
            total_amount=Decimal('10000.00'),
            payment_type='cash',
            guests_count=1,
        )

        self.client.force_authenticate(user=self.manager1)
        response = self.client.get('/api/orders/dashboard_summary/')

        # Manager1 должен видеть 0 (нет заказов в его клубе)
        self.assertEqual(response.data['kpi']['total_revenue'], 0)

    def test_manager_sees_own_club_data(self):
        """Manager1 видит данные своего клуба"""
        SaleOrder.objects.create(
            club=self.club1,
            date=timezone.now(),
            total_amount=Decimal('5000.00'),
            payment_type='cash',
            guests_count=1,
        )

        self.client.force_authenticate(user=self.manager1)
        response = self.client.get('/api/orders/dashboard_summary/')

        self.assertEqual(response.data['kpi']['total_revenue'], 5000.0)

    def test_no_token_returns_401(self):
        """Без токена → 401"""
        response = self.client.get('/api/orders/dashboard_summary/')
        self.assertEqual(response.status_code, 401)