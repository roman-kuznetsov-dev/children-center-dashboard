from django.db import models
from users.models import Club, User


class SaleOrder(models.Model):
    PAYMENT_CHOICES = (
        ('cash', 'Наличные'),
        ('card', 'Безнал'),
        ('qr', 'QR-код'),
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    guests_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Заказ #{self.id} - {self.club.name} - {self.date.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-date']


class SaleItem(models.Model):
    CATEGORY_CHOICES = (
        ('party', 'Праздник'),
        ('masterclass', 'Мастер-класс'),
        ('face_painting', 'Аквагрим'),
        ('cafe', 'Кафе'),
        ('toys', 'Игрушки'),
        ('entrance', 'Гости (входные билеты)'),
    )

    order = models.ForeignKey(SaleOrder, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if self.quantity and self.price:
            self.total = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.quantity} шт.) - {self.total} ₽"

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'


class CashReceipt(models.Model):
    """
    Модель для хранения чеков, полученных от ОФД (как будто с кассы).
    В реальности сюда падают данные из ОФД через Webhook.
    """
    STATUS_CHOICES = (
        ('pending', 'В обработке'),
        ('processed', 'Обработан'),
        ('failed', 'Ошибка'),
    )

    receipt_id = models.CharField(max_length=100, unique=True, verbose_name='ID чека')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name='Клуб')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    payment_type = models.CharField(max_length=20, verbose_name='Способ оплаты')
    guests_count = models.IntegerField(default=1, verbose_name='Гостей')
    raw_data = models.JSONField(default=dict, verbose_name='Сырые данные ОФД')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Получен')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Обработан')

    def __str__(self):
        return f'Чек {self.receipt_id} — {self.club.name} — {self.total_amount} ₽'

    class Meta:
        verbose_name = 'Чек ОФД'
        verbose_name_plural = 'Чеки ОФД'
        ordering = ['-created_at']