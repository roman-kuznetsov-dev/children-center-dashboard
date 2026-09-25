"""
Тесты для Webhook и вспомогательных функций.
"""
from django.test import TestCase
from sales.webhooks import detect_category, PAYMENT_TYPE_MAP, CLUB_NAME_MAP


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