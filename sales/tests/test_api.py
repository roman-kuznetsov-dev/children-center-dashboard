"""
Тесты API-эндпоинтов.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import Club, User
from sales.models import SaleOrder, SaleItem


class DashboardSummaryAPITest(TestCase):
    """Тесты эндпоинта /api/orders/dashboard_summary/"""

    def setUp(self):
        self.client = APIClient()
        self.club = Club.objects.create(name='Космоклуб', address='адрес')
        self.admin = User.objects.create_user(
            username='admin_test',
            password='123',
            role='admin',
        )
        self.manager = User.objects.create_user(
            username='manager_test',
            password='123',
            role='manager',
            club=self.club,
        )
        # Создаём заказ на сегодня
        self.order = SaleOrder.objects.create(
            club=self.club,
            manager=self.manager,
            date=timezone.now(),
            total_amount=Decimal('1000.00'),
            payment_type='card',
            guests_count=5,
        )
        SaleItem.objects.create(
            order=self.order,
            category='entrance',
            name='Входной билет',
            quantity=3,
            price=Decimal('300.00'),
        )

    def test_unauthorized_returns_401(self):
        """Без токена → 401"""
        response = self.client.get('/api/orders/dashboard_summary/')
        self.assertEqual(response.status_code, 401)

    def test_admin_sees_data(self):
        """Admin получает данные"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/orders/dashboard_summary/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('kpi', response.data)
        self.assertIn('categories', response.data)
        self.assertEqual(response.data['kpi']['total_revenue'], 1000.0)

    def test_manager_sees_only_own_club(self):
        """Manager видит только свой клуб"""
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/orders/dashboard_summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['kpi']['total_revenue'], 1000.0)

    def test_date_filter(self):
        """Фильтр по датам работает"""
        self.client.force_authenticate(user=self.admin)
        today = timezone.now().date().isoformat()
        response = self.client.get(
            f'/api/orders/dashboard_summary/?start_date={today}&end_date={today}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['kpi']['total_revenue'], 1000.0)

    def test_guests_counted_as_entrance(self):
        """Гости = количество входных билетов"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/orders/dashboard_summary/')
        self.assertEqual(response.data['kpi']['total_guests'], 3)


class ClubsComparisonAPITest(TestCase):
    """Тесты эндпоинта /api/orders/clubs_comparison/"""

    def setUp(self):
        self.client = APIClient()
        self.club1 = Club.objects.create(name='Космоклуб', address='адрес1')
        self.club2 = Club.objects.create(name='ЛокоМотив', address='адрес2')
        self.admin = User.objects.create_user(
            username='admin_test',
            password='123',
            role='admin',
        )
        self.manager = User.objects.create_user(
            username='manager_test',
            password='123',
            role='manager',
            club=self.club1,
        )
        SaleOrder.objects.create(
            club=self.club1,
            date=timezone.now(),
            total_amount=Decimal('5000.00'),
            payment_type='cash',
            guests_count=1,
        )
        SaleOrder.objects.create(
            club=self.club2,
            date=timezone.now(),
            total_amount=Decimal('3000.00'),
            payment_type='card',
            guests_count=1,
        )

    def test_admin_sees_all_clubs(self):
        """Admin видит все клубы"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/orders/clubs_comparison/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # у нас 2 клуба в тесте

    def test_manager_sees_one_club(self):
        """Manager видит только свой клуб"""
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/orders/clubs_comparison/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['club_name'], 'Космоклуб')