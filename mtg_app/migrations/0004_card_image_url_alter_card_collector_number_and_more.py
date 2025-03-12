# Generated by Django 5.1.1 on 2025-03-05 17:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mtg_app', '0003_deck'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='image_url',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Ссылка на изображение'),
        ),
        migrations.AlterField(
            model_name='card',
            name='collector_number',
            field=models.CharField(max_length=20, verbose_name='Коллекционный номер'),
        ),
        migrations.AlterField(
            model_name='card',
            name='condition',
            field=models.CharField(max_length=50, verbose_name='Состояние'),
        ),
        migrations.AlterField(
            model_name='card',
            name='foil',
            field=models.BooleanField(default=False, verbose_name='Фоил'),
        ),
        migrations.AlterField(
            model_name='card',
            name='language',
            field=models.CharField(max_length=50, verbose_name='Язык'),
        ),
        migrations.AlterField(
            model_name='card',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='card',
            name='purchase_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Цена покупки'),
        ),
        migrations.AlterField(
            model_name='card',
            name='quantity',
            field=models.IntegerField(default=1, verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='card',
            name='rarity',
            field=models.CharField(max_length=50, verbose_name='Редкость'),
        ),
        migrations.AlterField(
            model_name='card',
            name='scryfall_id',
            field=models.CharField(max_length=100, unique=True, verbose_name='Scryfall ID'),
        ),
        migrations.AlterField(
            model_name='card',
            name='set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtg_app.set', verbose_name='Сет'),
        ),
    ]
