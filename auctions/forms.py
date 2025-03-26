from django import forms
from .models import Auction
from .models import Bid


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['card', 'starting_price', 'end_time']
        widgets = {'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),}

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_amount']

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)  # Безопасное извлечение auction
        super().__init__(*args, **kwargs)

    def clean_bid_amount(self):
        bid_amount = self.cleaned_data['bid_amount']
        current_price = self.auction.current_price or self.auction.starting_price
        if bid_amount <= current_price:
            raise forms.ValidationError('Ставка должна быть выше текущей цены.')
        return bid_amount
