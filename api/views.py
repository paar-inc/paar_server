from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from api.models import Transaction
import requests
import datetime
import environ

def virtual_card(request):
    # after verifying t_addr and u_w_addr are being sent and extracted by url arg get
    # then create Transaction object in djano and continually update the object
    # from top to bottom of this view. transaction_address, wallet_address
    # brex_card_id, etc will all be saved against transaction
    # TODO start here..... create and save transaction obj before returning reponse json

    transaction_address = request.GET.get('transaction', 'NOT FOUND')
    user_wallet_address = request.GET.get('wallet', 'NOT FOUND')
    transaction_amount = request.GET.get('transaction_amount', 'NOT FOUND')

    if transaction_address == 'NOT FOUND' or user_wallet_address == 'NOT FOUND' or transaction_amount == 'NOT FOUND': 
            return JsonResponse({"result": "failure"})

    try:
        t_a = int(transaction_amount)
        if int(t_a) > 700:
            return JsonResponse({"result": "failure"})
    except ValueError:
        return JsonResponse({"result": "invalid argument"})


    print("transaction AMOUNT IS: ")
    print(transaction_amount)

    url = "https://platform.brexapis.com/v2/cards"

    env = environ.Env()
    environ.Env.read_env()
    payload = {
      "owner": {
        "type": "USER",
        "user_id": "cuuser_cl5clyqhd00gr0jsnaw8jqqv8"
      },
      "card_name": transaction_address,
      "card_type": "VIRTUAL",
      "limit_type": "CARD",
      "spend_controls": {
          "spend_limit": {
              "amount": int(transaction_amount),
              "currency": "USD"
              },
          "spend_duration": "ONE_TIME",
          "reason": "faciliate eth shopify transaction",
          "lock_after_date": "2022-07-29"
          },
    }

    headers = {
      "Content-Type": "application/json",
      "Idempotency-Key": transaction_address,
      "Authorization": "Bearer " + env("BREX_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    id = data["id"] 
    url = "https://platform.brexapis.com/v2/cards/" + id + "/pan"

    headers = {"Authorization": "Bearer " + env("BREX_KEY")}

    response = requests.get(url, headers=headers)

    data = response.json()

    print(data)
    new_transaction = Transaction(user_wallet_address=user_wallet_address, transaction_address=transaction_address, card_brex_id=id)
    new_transaction.save()

    month = data["expiration_date"]["month"]
    year = data["expiration_date"]["year"]
    date_str = str(year) + "-" + str(month)
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m")
    formatted_response_date = date_obj.strftime("%m") + "/" + date_obj.strftime("%y")

    response_data = {"num": data["number"], "cvv": data["cvv"], "expiration": formatted_response_date}	
    response_obj = JsonResponse(response_data)
    response_obj["Access-Control-Allow-Origin"] = "*"
    response_obj["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response_obj["Access-Control-Max-Age"] = "1000"
    response_obj["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response_obj 
