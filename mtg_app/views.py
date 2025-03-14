from django.shortcuts import render, get_object_or_404
from mtg_app.models import Card,Set, Deck
from django.db.models import Q
from django.db.models import Sum,Count
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
    decks = Deck.objects.all()
    sort = request.GET.get('sort')  # Получаем параметр сортировки

    if sort == 'alphabetical':
        decks = Deck.objects.order_by('name')  # Сортировка по алфавиту
    else:
        decks = Deck.objects.order_by('-id')  # Сортировка по умолчанию (новые колоды в начале)

    return render(request, 'mtg_app/deck_list.html', {'decks': decks,'sort': sort})

def deck_detail(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id)
    sort = request.GET.get('sort')  # Получаем параметр сортировки

    if sort == 'alphabetical':
        cards = deck.cards.order_by('name')  # Сортировка карт по алфавиту
    else:
        cards = deck.cards.order_by('-id')  # Сортировка по умолчанию (новые карты в начале)
    return render(request, 'mtg_app/deck_detail.html', {'deck': deck,'sort': sort,'cards': cards})