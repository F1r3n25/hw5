import sys
from datetime import datetime, timedelta

import aiohttp
import asyncio
import platform


async def pretty_view(data, new_curr=None):
    if new_curr:
        return {data["date"]: {
            'EUR': {"sale": data["exchangeRate"][8]["saleRateNB"],
                    "purchase": data["exchangeRate"][8]["purchaseRateNB"]},
            "USD": {"sale": data["exchangeRate"][23]["saleRateNB"],
                    "purchase": data["exchangeRate"][23]["purchaseRateNB"]},
            "PLN": {"sale": data["exchangeRate"][17]["saleRateNB"],
                    "purchase": data["exchangeRate"][17]["purchaseRateNB"]}}}

    return {data["date"]: {
        'EUR': {"sale": data["exchangeRate"][8]["saleRateNB"], "purchase": data["exchangeRate"][8]["purchaseRateNB"]},
        "USD": {"sale": data["exchangeRate"][23]["saleRateNB"],
                "purchase": data["exchangeRate"][23]["purchaseRateNB"]}}}


async def request(url: str, add_curr=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                result = r.json()
                if add_curr:
                    view_adder = await pretty_view(await result, "pln")
                    return view_adder
                else:
                    view = await pretty_view(await result)
                    return view


async def main(arg, sec_arg=None):
    data_list = []
    for i in range(1, int(arg) + 1):
        d = datetime.now() - timedelta(days=int(i))
        shift = d.strftime("%d.%m.%Y")
        if sec_arg:
            response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}', sec_arg)
        else:
            response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
        data_list.append(str(response))
    return "\n".join(data_list)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        if 10 >= int(sys.argv[1]) > 0:
            try:
                if sys.argv[2] == "pln":
                    r = asyncio.run(main(sys.argv[1], sys.argv[2]))
                    print(r)
            except IndexError:
                r = asyncio.run(main(sys.argv[1]))
                print(r)
        else:
            print("Entered argument should be from 1 to 10")
    except IndexError:
        print("Enter argument!")
