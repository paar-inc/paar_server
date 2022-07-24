from django.db import models

# other data that could be saved, IP, UserAgent, Amount
# flags like eth_transaction_confirmed or virtual_card_has_been_used
class Transaction(models.Model):
    user_wallet_address = models.CharField(max_length=100)
    transaction_address = models.CharField(max_length=100)
    card_brex_id = models.CharField(max_length=200)
