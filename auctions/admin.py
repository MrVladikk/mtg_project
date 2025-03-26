from django.contrib import admin
from .models import Auction, Bid
# Register your models here.

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('card', 'seller', 'starting_price', 'current_price', 'end_time', 'approved', 'is_active', 'created_at')
    list_filter = ('approved', 'is_active')
    search_fields = ('card__name', 'seller__username')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'bid_amount', 'bid_time')
    search_fields = ('auction__card__name', 'bidder__username')