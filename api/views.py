from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from api.models import Transaction
import requests
import datetime
import environ
from web3 import Web3

def virtual_card(request):
    # after verifying t_addr and u_w_addr are being sent and extracted by url arg get
    # then create Transaction object in djano and continually update the object
    # from top to bottom of this view. transaction_address, wallet_address
    # brex_card_id, etc will all be saved against transaction
    # TODO start here..... create and save transaction obj before returning reponse json

    transaction_address = request.GET.get('transaction', 'NOT FOUND')
    user_wallet_address = request.GET.get('wallet', 'NOT FOUND')

    if transaction_address == 'NOT FOUND' or user_wallet_address == 'NOT FOUND': 
            return JsonResponse({"result": "failure"})


    url = "https://eth-mainnet.g.alchemy.com/v2/HkqW3tzpSLhcB0GVY47WPkRRXY42S9S-"
    web3 = Web3(Web3.HTTPProvider(url))
    network_transaction = web3.eth.get_transaction(transaction_address)

   # check if network transaction sent eth to paar wallet
    print(network_transaction.to)
    print("0x953a9e6afed5f3835042b4f33d1cce81183adc62")
    if str(network_transaction.to).lower() != "0x953a9e6afed5f3835042b4f33d1cce81183adc62":
        # if paar wallet not receiver fail the request
        return JsonResponse({"result": "invalid_transaction: paar wallet did not receive transaction"})

  # grab value from network transaction and convert ETH to USD
    eth = float(Web3.fromWei(network_transaction.value, 'ether'))
    coinbase_url = "https://api.coinbase.com/v2/exchange-rates?currency=ETH"
    res = requests.get(coinbase_url)
    res_json = res.json()
    eth_to_usd = float(res_json["data"]["rates"]["USD"])
    usd_value = eth_to_usd * eth

   # derive maximum value based on converted ETHtoUSD value + .05% ??'
    adjusted_usd_value = 1.05 * usd_value
    adjusted_cent_value = int(adjusted_usd_value * 100)

    print("transaction AMOUNT IS: ")
    print(adjusted_usd_value)

    try:
        t_a = int(adjusted_cent_value)
        if int(t_a) > 800:
            return JsonResponse({"result": "failure"})
    except ValueError:
        return JsonResponse({"result": "invalid argument"})

    url = "https://platform.brexapis.com/v2/cards"
    exp_date = datetime.date.today() + datetime.timedelta(days=1)
    exp_date_string = exp_date.strftime("%Y-%m-%d")


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
              "amount": adjusted_cent_value,
              "currency": "USD"
              },
          "spend_duration": "ONE_TIME",
          "reason": "faciliate eth shopify transaction",
          "lock_after_date": exp_date_string 
          },
    }

    headers = {
      "Content-Type": "application/json",
      "Idempotency-Key": transaction_address,
      "Authorization": "Bearer " + env("BREX_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    print(data)
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
