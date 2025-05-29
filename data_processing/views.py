from django.shortcuts import render, HttpResponseRedirect
from django.contrib import messages
from django.core.management import call_command, CommandError
from django.conf import settings
from django.utils.text import get_valid_filename # Для очистки имени файла
import tempfile
import os

from .forms import CSVUploadForm # Импортируем нашу форму

# Эта вспомогательная функция поможет нам получить путь к файлу,
# независимо от того, хранится ли он в памяти или как временный файл на диске.
def get_persistent_temp_path(uploaded_file):
    """
    Сохраняет UploadedFile (если он в памяти) во временный файл
    и возвращает путь к нему. Если файл уже TemporaryUploadedFile,
    возвращает его путь.
    Файл создается с delete=False, поэтому его нужно будет удалить вручную.
    """
    # if hasattr(uploaded_file, 'temporary_file_path') and callable(uploaded_file.temporary_file_path):
    #     # Файл уже на диске (TemporaryUploadedFile)
    #     # Для синхронного вызова команды это нормально.
    #     # Для Celery может потребоваться создать копию с delete=False, чтобы Django не удалил его раньше времени.
    #     # Для простоты синхронного случая, пока оставим так.
    #     # НО! Чтобы быть уверенным, что файл не удалится Django, лучше всегда создавать свой временный файл:
    #     pass # Переходим к созданию своего файла ниже для большей надежности

    # Всегда создаем наш собственный временный файл, чтобы контролировать его жизненный цикл,
    # особенно если планируется переход на Celery.

    # Очищаем имя файла и берем расширение
    base_name, ext = os.path.splitext(uploaded_file.name)
    safe_base_name = get_valid_filename(base_name)

    # Используем системную временную директорию или указанную в settings.FILE_UPLOAD_TEMP_DIR
    temp_dir = getattr(settings, 'FILE_UPLOAD_TEMP_DIR', None)

    # Создаем именованный временный файл. delete=False означает, что мы удалим его сами.
    temp_save = tempfile.NamedTemporaryFile(
        delete=False, 
        prefix=f"{safe_base_name}_", # Добавляем префикс для узнаваемости
        suffix=ext or '.csv', # Гарантируем расширение
        dir=temp_dir
    )

    try:
        for chunk in uploaded_file.chunks():
            temp_save.write(chunk)
        temp_save.close() # Закрываем файл, чтобы management-команда могла его открыть
        return temp_save.name # Это путь к нашему временному файлу
    except Exception as e:
        # Важно: удалить временный файл, если произошла ошибка при записи
        if os.path.exists(temp_save.name):
            os.remove(temp_save.name)
        raise e # Перевыбрасываем исключение


def upload_csv_view(request):
    temp_file_path_for_command = None # Путь к файлу, который передадим в команду

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['csv_file']

            # --- Валидация файла ---
            # 1. Проверка расширения файла
            file_name = uploaded_file.name
            _, ext = os.path.splitext(file_name)
            if not ext.lower() == '.csv':
                messages.error(request, 'Ошибка: Файл должен быть в формате CSV.')
                return render(request, 'data_processing/upload_csv.html', {'form': form})

            # 2. Проверка размера файла (пример: 5MB)
            MAX_UPLOAD_SIZE_MB = 5
            if uploaded_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                messages.error(request, f'Ошибка: Размер файла не должен превышать {MAX_UPLOAD_SIZE_MB}MB.')
                return render(request, 'data_processing/upload_csv.html', {'form': form})

            # (Опционально) Проверка MIME типа (может быть ненадежной)
            # content_type = uploaded_file.content_type
            # if content_type not in ['text/csv', 'application/vnd.ms-excel', 'application/octet-stream', 'text/plain']:
            #     messages.warning(request, f'Предупреждение: Неожиданный тип файла: {content_type}. Обработка будет продолжена.')

            try:
                # Получаем путь к временному файлу, который будет существовать достаточно долго
                temp_file_path_for_command = get_persistent_temp_path(uploaded_file)

                # --- Вызов Django management command ---
                # Замените 'process_uploaded_csv' на имя вашей команды, если оно другое.
                # self.stdout.write(self.style.NOTICE(f'Вызов команды process_uploaded_csv с файлом: {temp_file_path_for_command}')) # Это для management команд, не для views
                print(f'INFO: Вызов команды process_uploaded_csv с файлом: {temp_file_path_for_command}') # Используйте print или logging во views
                call_command('process_uploaded_csv', temp_file_path_for_command) 

                messages.success(request, f'Файл "{file_name}" успешно загружен и обработан.')
                # Можно перенаправить на другую страницу или остаться на текущей
                # return HttpResponseRedirect('/some_success_url/') 

            except CommandError as ce: # Ошибки, выброшенные самой командой
                messages.error(request, f'Ошибка выполнения команды: {ce}')
            except Exception as e:
                messages.error(request, f'Произошла непредвиденная ошибка при обработке файла: {e}')
                # Логирование ошибки здесь очень важно для отладки
                # import logging
                # logger = logging.getLogger(__name__)
                # logger.exception(f"Ошибка при обработке файла {file_name}")
            finally:
                # Очистка временного файла, созданного get_persistent_temp_path.
                # Этот блок выполняется, если команда вызывается СИНХРОННО.
                # Если ваша management-команда (Шаг 2) сама удаляет файл в своем блоке finally,
                # то здесь удаление может быть избыточным или вызвать ошибку, если файл уже удален.
                # Решите, где будет происходить очистка: во view или в команде.
                # Если команда УЖЕ удаляет, закомментируйте этот блок.
                # Если команда НЕ удаляет, этот блок должен удалить файл.
                # Для Celery (Шаг 6) очистка будет в задаче Celery.
                if temp_file_path_for_command and os.path.exists(temp_file_path_for_command):
                    try:
                        # Если команда сама удаляет файл, этот вызов os.remove() вызовет ошибку.
                        # Если команда не удаляет, то этот вызов обязателен.
                        # Для текущей реализации, где команда удаляет файл, этот блок можно закомментировать
                        # или добавить проверку, что файл еще существует.
                        # os.remove(temp_file_path_for_command)
                        # messages.info(request, f"Временный файл {temp_file_path_for_command} удален представлением.")
                        pass # Предполагаем, что команда сама удалила файл
                    except OSError as e_clean:
                        messages.warning(request, f'Не удалось удалить временный файл {temp_file_path_for_command} из представления: {e_clean}')
        else: # Если форма невалидна
            messages.error(request, 'Ошибка в форме. Пожалуйста, исправьте.')
    else: # Если GET-запрос
        form = CSVUploadForm()

    return render(request, 'data_processing/upload_csv.html', {'form': form})
