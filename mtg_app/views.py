from django.shortcuts import render, get_object_or_404
from mtg_app.models import Card,Set, Deck
from django.db.models import Q
from django.db.models import Sum
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
        
    return render(request, 'mtg_app/card_list.html', {'cards': cards, 'query': query, 'total_cards': total_cards})

def card_detail(request, card_id):
    card = get_object_or_404(Card, id=card_id)  # Находим карту по ID
    return render(request, 'mtg_app/card_detail.html', {'card': card})

def set_list(request):
    sets = Set.objects.all()  # Все сеты
    return render(request, 'mtg_app/set_list.html', {'sets': sets})

def set_detail(request, set_id):
    set_obj = get_object_or_404(Set, id=set_id)
    cards = Card.objects.filter(set=set_obj)
    return render(request, 'mtg_app/set_detail.html', {'set': set_obj, 'cards': cards})

def deck_list(request):
    decks = Deck.objects.all()
    return render(request, 'mtg_app/deck_list.html', {'decks': decks})

def deck_detail(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id)
    return render(request, 'mtg_app/deck_detail.html', {'deck': deck})