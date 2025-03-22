from django.shortcuts import render, get_object_or_404, redirect
from mtg_app.models import Card,Set, Deck
from django.db.models import Q
from django.db.models import Sum,Count
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import CardForm
from .forms import DeckForm
from django.contrib.auth import logout
from django.http import Http404
from django.views.decorators.http import require_POST
# Create your views here.

def home(request):
    latest_cards = Card.objects.all().order_by('-id')[:10]  # Последние 10 карт
    popular_sets = Set.objects.all()[:5]  # Топ-5 сетов
    return render(request, 'mtg_app/home.html', {
        'latest_cards': latest_cards,
        'popular_sets': popular_sets,
    })

def card_list(request):
    query = request.GET.get('q')  # Получаем поисковый запрос
    sort = request.GET.get('sort')  # Получаем параметр сортировки

    if query:
        cards = Card.objects.filter(
            Q(name__icontains=query) |  # Поиск по названию карты
            Q(set__name__icontains=query) |  # Поиск по названию сета
            Q(rarity__icontains=query)  # Поиск по редкости
        )
        # Считаем общее количество карт в результатах поиска (сумма quantity)
        total_cards = cards.aggregate(total=Sum('quantity'))['total'] or 0
    else:
        cards = Card.objects.all()  # Все карты, если запроса нет
        total_cards = Card.objects.aggregate(total=Sum('quantity'))['total'] or 0
    
    if sort == 'alphabetical':
        cards = cards.order_by('name')
    elif sort == 'price':
        cards = cards.order_by('purchase_price')
    elif sort == 'price_desc':
        cards = cards.order_by('-purchase_price')
    else:
        cards = cards.order_by('-id')
        
    return render(request, 'mtg_app/card_list.html', {'cards': cards, 'query': query, 'total_cards': total_cards,'sort': sort})

def card_detail(request, card_id):
    card = get_object_or_404(Card, id=card_id)  # Находим карту по ID
    return render(request, 'mtg_app/card_detail.html', {'card': card})

def set_list(request):
    sort = request.GET.get('sort', '')  # Получаем параметр сортировки
    sets = Set.objects.annotate(total_cards=Count('cards'))  # Подсчет количества карт в каждом сете

    # Применяем сортировку
    if sort == 'alphabetical':
        sets = sets.order_by('name')  # Сортировка по алфавиту
    else:
        sets = sets.order_by('-id')  # Сортировка по умолчанию (новые сеты в начале)

    return render(request, 'mtg_app/set_list.html', {'sets': sets, 'sort': sort})

def set_detail(request, set_id):
    set_obj = get_object_or_404(Set, id=set_id)
    cards = set_obj.cards.all()  # Получаем все карты этого сета
    sort = request.GET.get('sort')  # Получаем параметр сортировки

    # Применяем сортировку
    if sort == 'alphabetical':
        cards = cards.order_by('name')  # Сортировка по имени
    elif sort == 'price':
        cards = cards.order_by('purchase_price')
    elif sort == 'price_desc':
        cards = cards.order_by('-purchase_price')
    
    else:
        cards = cards.order_by('-id')  # Сортировка по умолчанию

    # Подсчёт общего количества карт в сете
    total_cards = cards.aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, 'mtg_app/set_detail.html', {
        'set': set_obj,
        'cards': cards,
        'sort': sort,
        'total_cards': total_cards,  # Передаём количество карт в шаблон
    })
    
def deck_list(request):
    # Показываем:
    # 1. Все публичные колоды (is_private=False)
    # 2. Приватные колоды текущего пользователя
    decks = Deck.objects.filter(
        Q(is_private=False) | Q(owner=request.user.id)
    ) if request.user.is_authenticated else Deck.objects.filter(is_private=False)
    
    sort = request.GET.get('sort')
    
    if sort == 'alphabetical':
        decks = decks.order_by('name')
    else:
        decks = decks.order_by('-created_at')
    
    return render(request, 'mtg_app/deck_list.html', {'decks': decks, 'sort': sort})

def deck_detail(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id)
    
    if deck.is_private and deck.owner != request.user:
        raise Http404("Колода не найдена")
    
    cards = deck.cards.all()  # Все карты колоды
    sort = request.GET.get('sort')  # Получаем параметр сортировки
    
    # Сортировка
    if sort == 'alphabetical':
        cards = cards.order_by('name')
    elif sort == 'purchase_price':
        cards = cards.order_by('purchase_price')
    elif sort == 'purchase_price_desc':
        cards = cards.order_by('-purchase_price')
    else:
        cards = cards.order_by('-id')
    
    return render(request, 'mtg_app/deck_detail.html', {
        'deck': deck,
        'cards': cards,
        'sort': sort
    })
    
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('mtg_app:card_list')  # Перенаправление на главную страницу или другую
    else:
        form = CustomUserCreationForm()
    return render(request, 'mtg_app/register.html', {'form': form})

@login_required
def add_card(request):
    if request.method == 'POST':
        form = CardForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.owner = request.user  # Привязываем карту к текущему пользователю
            card.save()
            return redirect('mtg_app:card_list')
    else:
        form = CardForm()
    return render(request, 'mtg_app/add_card.html', {'form': form})

@login_required
def add_deck(request):
    """
    Представление для добавления новой колоды. Доступно только авторизованным пользователям.
    """
    if request.method == 'POST':
        form = DeckForm(request.POST)
        if form.is_valid():
            deck = form.save(commit=False)
            deck.owner = request.user  # Привязываем колоду к текущему пользователю
            deck.save()
            form.save_m2m()  # Сохраняем связи ManyToMany (карты в колоде)
            # Если нужно добавить карточки в колоду, можно добавить дополнительную логику здесь.
            return redirect('mtg_app:deck_list')  # Перенаправляем пользователя на страницу со списком колод
    else:
        form = DeckForm()
    return render(request, 'mtg_app/add_deck.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('mtg_app:home')  # Перенаправление на главную страницу

@login_required
@require_POST  # Разрешаем только POST-запросы
def delete_deck(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id)
    
    # Проверяем, что пользователь - владелец колоды
    if deck.owner != request.user:
        raise Http404("У вас нет прав на удаление этой колоды")
    
    deck.delete()
    return redirect('mtg_app:deck_list')