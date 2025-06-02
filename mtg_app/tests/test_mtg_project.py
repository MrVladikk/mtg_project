import pytest
from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.core.management import call_command
from mtg_app.models import Card, Deck, Set
import pandas as pd # Убедитесь, что pandas установлен в вашем окружении для тестов
from unittest import mock # Для мокирования


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_card_creation():
    """
    Тестирует создание объекта Card с правильной связью на Set.
    """
    test_set = Set.objects.create(code="LEA", name="Alpha")
    card = Card.objects.create(
        name="Black Lotus",
        set=test_set,
        rarity="Rare",
        image_url="http://example.com/black_lotus.jpg"
    )
    assert Card.objects.count() == 1
    assert Card.objects.first().name == "Black Lotus"


@pytest.mark.django_db
def test_deck_creation():
    """
    Тестирует создание объекта Deck.
    """
    deck = Deck.objects.create(name="Vintage Deck")
    assert Deck.objects.count() == 1
    assert Deck.objects.first().name == "Vintage Deck"


@pytest.mark.django_db
def test_set_creation():
    """
    Тестирует создание объекта Set.
    """
    mtg_set = Set.objects.create(code="LEA", name="Alpha")
    assert Set.objects.count() == 1
    assert mtg_set.name == "Alpha"


@pytest.mark.django_db
def test_card_list_view(client):
    """
    Тестирует доступность представления списка карточек.
    """
    url_name_to_try = 'card_list'
    try:
        url = reverse(f'mtg_app:{url_name_to_try}')
    except NoReverseMatch:
        try:
            url = reverse(url_name_to_try)
        except NoReverseMatch as e:
            pytest.fail(f"NoReverseMatch for '{url_name_to_try}' with and without 'mtg_app' namespace: {e}")
            return
        
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_deck_list_view(client):
    """
    Тестирует доступность представления списка колод.
    """
    url_name_to_try = 'deck_list'
    try:
        url = reverse(f'mtg_app:{url_name_to_try}')
    except NoReverseMatch:
        try:
            url = reverse(url_name_to_try)
        except NoReverseMatch as e:
            pytest.fail(f"NoReverseMatch for '{url_name_to_try}' with and without 'mtg_app' namespace: {e}")
            return

    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('pandas.read_csv') # Мокируем pandas.read_csv
def test_import_cards_command(mock_read_csv, tmp_path):
    """
    Тестирует выполнение команды импорта карточек из CSV.
    Команда 'import_cards' использует жестко заданный путь к файлу.
    Мы мокируем pd.read_csv, чтобы подменить данные для импорта.
    Команда вызывается без аргументов, так как она не принимает их.
    """
    # Создаем данные для DataFrame, который вернет мок pd.read_csv
    csv_data = {
        "Set code": ["LEA"],
        "Set name": ["Limited Edition Alpha"],
        "Name": ["Test Card From Mock"],
        "Collector number": ["123"],
        "Foil": ["false"], # или "foil" для True
        "Rarity": ["Common"],
        "Quantity": [1],
        "Purchase price": ["1.00"],
        "Language": ["English"],
        "Condition": ["Near Mint"],
        "Scryfall ID": ["some-unique-scryfall-id-for-mock"] # Убедитесь, что это ID уникален
    }
    mock_df = pd.DataFrame(csv_data)
    mock_read_csv.return_value = mock_df

    # Команда import_cards не принимает аргументы пути, она использует жестко заданный.
    # Мы мокировали pd.read_csv, поэтому содержимое жестко заданного файла не будет читаться.
    call_command('import_cards')

    # Проверяем, что карта была создана на основе мокированных данных
    assert Card.objects.filter(name="Test Card From Mock").exists()
    created_card = Card.objects.get(name="Test Card From Mock")
    assert created_card.set.code == "LEA"
    assert not created_card.foil # так как "false"

    # Убедитесь, что mock_read_csv был вызван с жестко заданным путем из команды import_cards.py
    # Это необязательно, но полезно для уверенности, что мок сработал там, где ожидалось.
    # Однако, поскольку мы не можем легко получить доступ к переменной file_path внутри handle извне,
    # просто убедимся, что он был вызван хотя бы один раз.
    mock_read_csv.assert_called_once() 


@pytest.mark.django_db
@mock.patch('mtg_app.management.commands.update_image_urls.os.path.exists') # Мокируем os.path.exists
def test_update_images_command(mock_os_path_exists):
    """
    Тестирует выполнение команды обновления изображений карточек.
    Имя команды было исправлено на 'update_image_urls'.
    Мокируем os.path.exists, чтобы команда думала, что файл изображения существует.
    """
    mock_os_path_exists.return_value = True # Заставляем команду думать, что все файлы изображений существуют

    test_set = Set.objects.create(code="LEA", name="Alpha")
    # Используем уникальный collector_number для формирования пути, если он используется в имени файла
    card = Card.objects.create(
        name="Test Image Card", # Используем имя, которое не конфликтует с другими тестами
        collector_number="imgtst", 
        set=test_set,
        rarity="Rare",
        image_url=""  # Изначально пустое изображение
    )

    # Исправлено имя команды
    call_command('update_image_urls')

    card.refresh_from_db()
    # Утверждение проверяет, что URL изображения был обновлен (не пустой),
    # так как мы замокировали os.path.exists=True
    assert card.image_url != "", "Image URL should have been updated by the command"
    
    # Опционально: Проверить, что image_url соответствует ожидаемому формату, если он предсказуем
    # Например: expected_image_path = f"mtg_app/images/cards/Test_Image_Card__imgtst.jpg" 
    # (зависит от логики формирования имени в команде)
    # assert card.image_url == expected_image_path
    
    # Проверяем, что os.path.exists был вызван
    mock_os_path_exists.assert_called()


@pytest.mark.django_db
def test_add_deck_command(tmp_path):
    """
    Тестирует добавление колоды через команду.
    Команда должна принимать deck_file и deck_name как аргументы.
    """
    deck_file = tmp_path / "deck.txt"
    deck_file.write_text("1 Black Lotus\n")

    test_set, _ = Set.objects.get_or_create(code="LEA", defaults={"name": "Alpha"})
    Card.objects.get_or_create(
        name="Black Lotus", # Это имя должно совпадать с тем, что в deck_file
        set=test_set,
        defaults={
            "rarity": "Rare",
            "image_url": "http://example.com/image.jpg",
            # Убедитесь, что scryfall_id уникален или не используется для get_or_create без него
            "scryfall_id": "unique-scryfall-id-for-black-lotus-in-deck-test" 
        }
    )

    call_command('add_deck', '--deck_file', str(deck_file), '--deck_name', 'Test Deck')

    assert Deck.objects.filter(name='Test Deck').exists()