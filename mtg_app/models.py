from django.db import models

# Create your models here.

class Set (models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    
    def card_count(self):
        return self.card_set.count()()
    
    def __str__(self):
        return self.name

class Card(models.Model):
    scryfall_id = models.CharField(max_length=100, unique=True, verbose_name="Scryfall ID")
    name = models.CharField(max_length=200, verbose_name="Название")
    set = models.ForeignKey('Set', on_delete=models.CASCADE, verbose_name="Сет",related_name='cards')
    collector_number = models.CharField(max_length=20, verbose_name="Коллекционный номер")
    foil = models.BooleanField(default=False, verbose_name="Фоил")
    rarity = models.CharField(max_length=50, verbose_name="Редкость")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2,default=0, verbose_name="Цена покупки")
    language = models.CharField(max_length=50, verbose_name="Язык")
    condition = models.CharField(max_length=50, verbose_name="Состояние")
    image_url = models.CharField(max_length=200, blank=True, null=True, verbose_name="Ссылка на изображение")

    def __str__(self):
        return self.name
    
class Deck(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название колоды")
    description = models.TextField(blank=True, verbose_name="Описание")
    cards = models.ManyToManyField(Card, verbose_name="Карты в колоде")

    def __str__(self):
        return self.name