from django.core.management.base import BaseCommand, CommandError
from mtg_app.models import Card, Deck
import os

class Command(BaseCommand):
    help = 'Импортирует колоду из текстового файла и добавляет карты в базу данных.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--deck_file', '-f',
            type=str,
            required=True,
            help="Путь к текстовому файлу с описанием колоды (например, 'ashiok.txt')."
        )
        parser.add_argument(
            '--deck_name', '-n',
            type=str,
            required=True,
            help="Название колоды."
        )
        parser.add_argument(
            '--deck_description', '-d',
            type=str,
            default="",
            help="Описание колоды (необязательно)."
        )

    def handle(self, *args, **options):
        deck_file = options['deck_file']
        deck_name = options['deck_name']
        deck_description = options['deck_description']

        # Создаем колоду
        deck = Deck.objects.create(
            name=deck_name,
            description=deck_description
        )

        # Проверка наличия файла
        if not os.path.exists(deck_file):
            raise CommandError(f"Файл '{deck_file}' не найден.")

        try:
            with open(deck_file, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        # Если строка начинается с цифры, разделяем количество и название
                        if line[0].isdigit():
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                quantity, card_name = parts
                            else:
                                quantity, card_name = 1, parts[0]
                        else:
                            quantity, card_name = 1, line

                        # Убираем лишние символы (например, для foil-карт)
                        card_name = card_name.split(' (')[0]

                        # Ищем карту в базе данных
                        card = Card.objects.filter(name__icontains=card_name).first()
                        if card:
                            deck.cards.add(card)
                            self.stdout.write(self.style.SUCCESS(f"Добавлена карта: {card.name}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"Карта не найдена: {card_name}"))
            self.stdout.write(self.style.SUCCESS(f"Колода '{deck.name}' успешно создана!"))
        except Exception as e:
            raise CommandError(f"Ошибка при добавлении колоды: {e}")
