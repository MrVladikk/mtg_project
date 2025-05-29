from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
# from django.core.files.base import ContentFile # Не используется при сохранении в static напрямую
import csv
import os
import tempfile
import requests # Для скачивания изображений и запросов к API
import time # Для небольших задержек между API запросами (хорошая практика)
import re # Для очистки имен файлов

# --- ИМПОРТИРУЙТЕ ВАШИ МОДЕЛИ ---
try:
    from mtg_app.models import Card, Set
except ImportError:
    raise ImportError(
        "Не удалось импортировать модели 'Card' и/или 'Set' из 'mtg_app.models'. "
        "Убедитесь, что приложение 'mtg_app' существует, модели в нем определены, "
        "и 'mtg_app' добавлено в INSTALLED_APPS."
    )

def sanitize_filename(name):
    """Очищает имя файла от недопустимых символов."""
    name = name.replace('/', '_').replace('//', '__') # Как в update_image_urls.py
    name = re.sub(r'[<>:"/\\|?*]', '_', name) # Заменяем другие недопустимые символы
    name = name.strip()
    return name if name else "unknown_card"


class Command(BaseCommand):
    help = 'Обрабатывает CSV-файл с картами, скачивает изображения в статическую папку и сохраняет пути в базу данных.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к CSV-файлу для обработки.')

    def handle(self, *args, **options):
        file_path = options['file_path']
        self.stdout.write(self.style.SUCCESS(f'Начало обработки CSV-файла: {file_path}'))

        if not os.path.exists(file_path):
            raise CommandError(f'Ошибка: Файл не найден по пути "{file_path}"')
        if not os.path.isfile(file_path):
            raise CommandError(f'Ошибка: "{file_path}" не является файлом.')

        # Определение пути к папке с изображениями внутри статики приложения mtg_app
        try:
            app_static_dir = os.path.join(settings.BASE_DIR, 'mtg_app', 'static', 'mtg_app')
            IMAGE_SAVE_FOLDER_ABSOLUTE = os.path.join(app_static_dir, 'images', 'cards')
            IMAGE_DB_PATH_PREFIX = os.path.join('mtg_app', 'images', 'cards') # Относительный путь для БД
        except AttributeError:
            self.stderr.write(self.style.ERROR("settings.BASE_DIR не определен. Невозможно определить путь для сохранения изображений."))
            return

        os.makedirs(IMAGE_SAVE_FOLDER_ABSOLUTE, exist_ok=True)

        processed_count = 0
        created_count = 0
        updated_count = 0
        error_count = 0
        image_download_success = 0
        image_download_errors = 0
        image_skipped_count = 0
        scryfall_api_requests = 0

        expected_csv_headers_for_validation = [
            'Name', 'Set code', 'Set name', 'Collector number', 'Foil', 'Rarity',
            'Quantity', 'Scryfall ID', 'Purchase price', 'Condition', 'Language',
            'Image URL'
        ]

        try:
            with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                actual_headers = [header.strip() for header in reader.fieldnames] if reader.fieldnames else []
                
                has_image_url_column_csv = 'Image URL' in actual_headers
                if not has_image_url_column_csv:
                    self.stdout.write(self.style.WARNING(
                        f"В CSV-файле отсутствует колонка 'Image URL'. Будет предпринята попытка получить URL с Scryfall."
                    ))
                
                critical_missing_headers = [h for h in expected_csv_headers_for_validation if h not in ['Image URL'] and h not in actual_headers]
                if critical_missing_headers:
                     self.stdout.write(self.style.WARNING(
                        f"В CSV-файле отсутствуют некоторые ожидаемые колонки: {', '.join(critical_missing_headers)}. "
                        f"Обработка будет продолжена с доступными данными, но могут быть пропуски."
                    ))

                for i, row in enumerate(reader):
                    card_name_csv = row.get("Name", "Unknown Card Name").strip()
                    self.stdout.write(f'Обработка строки {i + 1}: {card_name_csv}')
                    processed_count += 1
                    
                    card_obj = None

                    try:
                        scryfall_id = row.get('Scryfall ID', '').strip()
                        # Scryfall ID все еще важен для уникальности записи в БД
                        if not scryfall_id:
                            self.stderr.write(self.style.ERROR(f'Строка {i + 1}: Отсутствует обязательный Scryfall ID для создания/обновления записи. Пропуск строки.'))
                            error_count +=1
                            continue

                        set_code_csv = row.get('Set code', '').strip()
                        set_name_csv = row.get('Set name', '').strip()
                        collector_number_csv = row.get('Collector number', '').strip()
                        set_instance = None

                        if set_code_csv:
                            set_instance, created_set = Set.objects.get_or_create(
                                code=set_code_csv,
                                defaults={'name': set_name_csv if set_name_csv else set_code_csv}
                            )
                            if created_set:
                                self.stdout.write(self.style.SUCCESS(f"  Создан новый сет: {set_instance.name} ({set_instance.code})"))
                        else:
                            self.stderr.write(self.style.ERROR(f'Строка {i + 1} ({card_name_csv}): Отсутствует "Set code". Пропуск.'))
                            error_count += 1
                            continue
                        
                        if not collector_number_csv:
                            self.stderr.write(self.style.ERROR(f'Строка {i + 1} ({card_name_csv}): Отсутствует "Collector number". Пропуск.'))
                            error_count += 1
                            continue


                        csv_foil_value = row.get('Foil', '').strip().lower()
                        is_foil_card = csv_foil_value not in ['normal', ''] 

                        purchase_price_str = row.get('Purchase price', '').strip()
                        purchase_price_val = float(purchase_price_str) if purchase_price_str else 0.0

                        defaults_data = {
                            'name': card_name_csv,
                            'set': set_instance,
                            'collector_number': collector_number_csv,
                            'foil': is_foil_card,
                            'rarity': row.get('Rarity', '').strip().lower(),
                            'quantity': int(row.get('Quantity', 1)) if row.get('Quantity', '').strip() else 1,
                            'purchase_price': purchase_price_val,
                            'language': row.get('Language', 'ru').strip(),
                            'condition': row.get('Condition', 'near_mint').strip(),
                        }
                        
                        card_obj, created = Card.objects.update_or_create(
                            scryfall_id=scryfall_id, # Scryfall ID используется для идентификации записи в БД
                            defaults=defaults_data
                        )

                        if created:
                            created_count += 1
                            self.stdout.write(self.style.SUCCESS(f"  Создана: {card_obj.name} ({card_obj.scryfall_id})"))
                        else:
                            updated_count += 1
                            self.stdout.write(self.style.NOTICE(f"  Обновлена: {card_obj.name} ({card_obj.scryfall_id})"))

                        # --- Логика получения URL изображения и его скачивания ---
                        image_url_to_download = row.get('Image URL', '').strip() if has_image_url_column_csv else None
                        final_image_db_path = None
                        
                        sanitized_card_name = sanitize_filename(card_obj.name)
                        image_filename_base = f"{sanitized_card_name}_{card_obj.collector_number}"
                        
                        potential_extensions = ['.jpg', '.png', '.jpeg', '.webp']
                        existing_image_physical_path = None
                        for ext_check in potential_extensions:
                            check_path = os.path.join(IMAGE_SAVE_FOLDER_ABSOLUTE, f"{image_filename_base}{ext_check}")
                            if os.path.exists(check_path):
                                existing_image_physical_path = check_path
                                break
                        
                        if existing_image_physical_path:
                            self.stdout.write(self.style.NOTICE(f'    Изображение для {card_obj.name} ({card_obj.collector_number}) уже существует: {os.path.basename(existing_image_physical_path)}. Пропуск скачивания.'))
                            final_image_db_path = os.path.join(IMAGE_DB_PATH_PREFIX, os.path.basename(existing_image_physical_path))
                            image_skipped_count +=1
                        else:
                            if not image_url_to_download: # Если URL не было в CSV, пытаемся получить с Scryfall
                                self.stdout.write(self.style.NOTICE(f'    URL изображения для {card_name_csv} отсутствует в CSV. Пытаюсь получить с Scryfall...'))
                                card_data_scryfall = None
                                # Приоритет: по коду сета и номеру коллекционера
                                if set_code_csv and collector_number_csv:
                                    self.stdout.write(self.style.NOTICE(f'    Запрос по сету "{set_code_csv}" и номеру "{collector_number_csv}"...'))
                                    try:
                                        if scryfall_api_requests > 0: time.sleep(0.1)
                                        scryfall_api_url = f"https://api.scryfall.com/cards/{set_code_csv.lower()}/{collector_number_csv.lower()}"
                                        api_response = requests.get(scryfall_api_url, timeout=10)
                                        scryfall_api_requests += 1
                                        api_response.raise_for_status()
                                        card_data_scryfall = api_response.json()
                                    except requests.exceptions.RequestException as sc_re:
                                        self.stderr.write(self.style.WARNING(f'    Ошибка при запросе к Scryfall по сету/номеру для {card_name_csv}: {sc_re}'))
                                    except Exception as sc_e:
                                        self.stderr.write(self.style.WARNING(f'    Непредвиденная ошибка при запросе к Scryfall по сету/номеру для {card_name_csv}: {sc_e}'))
                                
                                # Если по сету/номеру не нашли, или если scryfall_id есть, пробуем по нему (как запасной вариант или если он более надежен)
                                if not card_data_scryfall and scryfall_id:
                                    self.stdout.write(self.style.NOTICE(f'    Запрос по Scryfall ID "{scryfall_id}"...'))
                                    try:
                                        if scryfall_api_requests > 0: time.sleep(0.1)
                                        scryfall_api_url = f"https://api.scryfall.com/cards/{scryfall_id}"
                                        api_response = requests.get(scryfall_api_url, timeout=10)
                                        scryfall_api_requests += 1
                                        api_response.raise_for_status()
                                        card_data_scryfall = api_response.json()
                                    except requests.exceptions.RequestException as sc_re:
                                        self.stderr.write(self.style.ERROR(f'    Ошибка при запросе к Scryfall API по ID для {scryfall_id}: {sc_re}'))
                                    except Exception as sc_e:
                                        self.stderr.write(self.style.ERROR(f'    Непредвиденная ошибка при получении данных с Scryfall по ID для {scryfall_id}: {sc_e}'))

                                if card_data_scryfall:
                                    if 'image_uris' in card_data_scryfall and card_data_scryfall['image_uris'] and 'png' in card_data_scryfall['image_uris']:
                                        image_url_to_download = card_data_scryfall['image_uris']['png']
                                    elif 'image_uris' in card_data_scryfall and card_data_scryfall['image_uris'] and 'large' in card_data_scryfall['image_uris']:
                                        image_url_to_download = card_data_scryfall['image_uris']['large']
                                    elif 'card_faces' in card_data_scryfall and isinstance(card_data_scryfall['card_faces'], list) and len(card_data_scryfall['card_faces']) > 0:
                                        first_face = card_data_scryfall['card_faces'][0]
                                        if 'image_uris' in first_face and first_face['image_uris'] and 'png' in first_face['image_uris']:
                                            image_url_to_download = first_face['image_uris']['png']
                                        elif 'image_uris' in first_face and first_face['image_uris'] and 'large' in first_face['image_uris']:
                                            image_url_to_download = first_face['image_uris']['large']
                                    
                                    if image_url_to_download:
                                        self.stdout.write(self.style.SUCCESS(f'    URL изображения получен с Scryfall: {image_url_to_download}'))
                                    else:
                                        self.stdout.write(self.style.WARNING(f'    Не удалось найти URL изображения на Scryfall для {card_name_csv} (Set: {set_code_csv}, Num: {collector_number_csv}, ID: {scryfall_id}).'))
                            
                            if image_url_to_download:
                                try:
                                    img_response = requests.get(image_url_to_download, stream=True, timeout=15)
                                    img_response.raise_for_status() 

                                    content_type = img_response.headers.get('content-type')
                                    ext = '.jpg' 
                                    if content_type == 'image/jpeg': ext = '.jpg'
                                    elif content_type == 'image/png': ext = '.png'
                                    elif content_type == 'image/webp': ext = '.webp'
                                    
                                    image_filename_with_ext = f"{image_filename_base}{ext}"
                                    image_physical_save_path = os.path.join(IMAGE_SAVE_FOLDER_ABSOLUTE, image_filename_with_ext)

                                    with open(image_physical_save_path, 'wb') as f:
                                        for chunk in img_response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    final_image_db_path = os.path.join(IMAGE_DB_PATH_PREFIX, image_filename_with_ext)
                                    image_download_success += 1
                                    self.stdout.write(self.style.SUCCESS(f"    Изображение для {card_obj.name} скачано и сохранено как {image_filename_with_ext}"))
                                
                                except requests.exceptions.RequestException as re:
                                    self.stderr.write(self.style.ERROR(f'    Ошибка скачивания изображения для {card_name_csv} с URL {image_url_to_download}: {re}'))
                                    image_download_errors += 1
                                except Exception as img_e:
                                    self.stderr.write(self.style.ERROR(f'    Непредвиденная ошибка при сохранении изображения для {card_name_csv}: {img_e}'))
                                    image_download_errors += 1
                            elif card_obj: 
                                 self.stdout.write(self.style.NOTICE(f'    URL изображения для {card_obj.name} не найден.'))
                        
                        if card_obj and final_image_db_path and card_obj.image_url != final_image_db_path:
                            card_obj.image_url = final_image_db_path
                            card_obj.save(update_fields=['image_url']) 
                            self.stdout.write(self.style.NOTICE(f"    Путь к изображению для {card_obj.name} обновлен в БД: {final_image_db_path}"))
                        elif card_obj and not final_image_db_path and card_obj.image_url:
                            self.stdout.write(self.style.NOTICE(f"    Изображение для {card_obj.name} не найдено, путь в БД не изменен (текущий: {card_obj.image_url})."))

                    except ValueError as ve:
                        self.stderr.write(self.style.ERROR(f'Строка {i + 1} ({card_name_csv}): Ошибка значения - {ve}. Пропуск строки.'))
                        error_count += 1
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f'Строка {i + 1} ({card_name_csv} - Scryfall ID: {row.get("Scryfall ID", "N/A")}): Непредвиденная ошибка - {e}. Пропуск строки.'))
                        error_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'--- Обработка файла завершена ---'))
            self.stdout.write(f'Всего строк обработано: {processed_count}')
            self.stdout.write(self.style.SUCCESS(f'Новых записей создано: {created_count}'))
            self.stdout.write(self.style.NOTICE(f'Записей обновлено: {updated_count}'))
            if image_skipped_count > 0:
                self.stdout.write(self.style.NOTICE(f'Изображений пропущено (уже существуют): {image_skipped_count}'))
            if image_download_success > 0:
                self.stdout.write(self.style.SUCCESS(f'Изображений успешно скачано: {image_download_success}'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'Строк с ошибками сохранения данных (пропущено): {error_count}'))
            if image_download_errors > 0:
                self.stdout.write(self.style.ERROR(f'Ошибок скачивания/сохранения изображений: {image_download_errors}'))
            if scryfall_api_requests > 0:
                self.stdout.write(self.style.NOTICE(f'Выполнено запросов к Scryfall API: {scryfall_api_requests}'))
            

        except FileNotFoundError:
            raise CommandError(f'Ошибка: Файл не найден в процессе обработки: {file_path}')
        except UnicodeDecodeError as e:
            raise CommandError(f'Ошибка декодирования файла {file_path} (возможно, неправильная кодировка или файл не является текстовым CSV): {e}')
        except csv.Error as e:
            raise CommandError(f'Ошибка чтения CSV-файла {file_path} (возможно, нарушена структура CSV): {e}')
        except CommandError as ce:
            raise ce
        except Exception as e:
            raise CommandError(f'Непредвиденная ошибка на верхнем уровне обработки CSV-файла {file_path}: {e}')
        finally:
            if options.get('is_called_by_celery_task', False):
                 self.stdout.write(self.style.NOTICE(f'Файл {file_path} будет удален Celery задачей.'))
            elif os.path.exists(file_path):
                try:
                    is_temp_file_to_delete = False
                    real_file_path = os.path.realpath(file_path)
                    system_temp_dir = os.path.realpath(tempfile.gettempdir())
                    if real_file_path.startswith(system_temp_dir):
                        is_temp_file_to_delete = True
                    django_temp_dir_setting = getattr(settings, 'FILE_UPLOAD_TEMP_DIR', None)
                    if django_temp_dir_setting:
                        django_temp_dir = os.path.realpath(django_temp_dir_setting)
                        if real_file_path.startswith(django_temp_dir):
                            is_temp_file_to_delete = True
                    if is_temp_file_to_delete:
                        os.remove(file_path)
                        self.stdout.write(self.style.NOTICE(f'Временный файл очищен: {file_path}'))
                except OSError as e_clean:
                    self.stderr.write(self.style.ERROR(f'Ошибка при попытке очистки временного файла {file_path}: {e_clean}'))
