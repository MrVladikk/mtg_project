from django.db import models
from django.contrib.auth.models import User
from mtg_app.models import Card

# Create your models here.
class Auction(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='auctions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions')
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    end_time = models.DateTimeField()
    approved = models.BooleanField(default=False)  # Аукцион публикуется только после подтверждения администратора
    is_active = models.BooleanField(default=True)   # Флаг активности аукциона
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Auction for {self.card.name} by {self.seller.username}"

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid of {self.bid_amount} by {self.bidder.username}"