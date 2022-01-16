from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField('адрес', max_length=500, unique=True)
    longitude = models.FloatField(verbose_name='долгота', blank=True, null=True)
    latitude = models.FloatField(verbose_name='широта', blank=True, null=True)
    updated = models.DateTimeField('дата обновления', default=timezone.now)

    def __str__(self):
        return f'№{self.id} - {self.address[:50]}'

    class Meta():
        verbose_name = 'место'
        verbose_name_plural = 'места'
