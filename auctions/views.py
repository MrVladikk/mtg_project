from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Auction
from .forms import AuctionForm, BidForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Список аукционов
def auction_list(request):
    auctions = Auction.objects.filter(
        approved=True, 
        is_active=True, 
        end_time__gt=timezone.now()
    ).order_by('end_time')
    return render(request, 'auctions/auction_list.html', {'auctions': auctions})

# Детали аукциона
def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    bids = auction.bids.all().order_by('-bid_amount', '-bid_time')
    now = timezone.now()
    can_bid = (
        request.user.is_authenticated and 
        auction.approved and 
        auction.is_active and 
        auction.end_time > now and 
        auction.seller != request.user
    )

    if request.method == 'POST' and can_bid:
        form = BidForm(request.POST, auction=auction)  # Передаем auction
        if form.is_valid():
            bid = form.save(commit=False)
            bid.auction = auction
            bid.bidder = request.user
            bid.save()
            auction.current_price = bid.bid_amount
            auction.save()
            messages.success(request, "Ставка успешно сделана!")
            return redirect('auctions:auction_detail', auction_id=auction.id)
        else:
            messages.error(request, "Ошибка в форме ставки.")
    else:
        form = BidForm(auction=auction)  # Передаем auction

    context = {
        'auction': auction,
        'bids': bids,
        'form': form,
        'now': now,
        'can_bid': can_bid,
    }
    return render(request, 'auctions/auction_detail.html', context)

# Создание аукциона
@login_required
def create_auction(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.seller = request.user
            auction.current_price = auction.starting_price
            auction.save()
            messages.success(request, "Аукцион создан и ожидает подтверждения.")
            return redirect('auctions:auction_list')
    else:
        form = AuctionForm()
    return render(request, 'auctions/create_auction.html', {'form': form})