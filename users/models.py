from django.db import models
from django.contrib.auth.models import AbstractUser

class Club(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор сети'),
        ('manager', 'Управляющий клубом'),
        ('staff', 'Сотрудник'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.username
        class Meta:
            db_table = 'users'