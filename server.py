import asyncio
import logging
from datetime import datetime, timedelta

import aiofile
import aiohttp
import httpx
import websockets
import names
import aiopath
import aiopath

from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

import logging

logging.basicConfig(level=logging.INFO, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


async def request_arg(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                result = r.json()
                view = await pretty_view(await result)
            return view


async def format_date(day):
    data_list = []
    for i in range(1, day + 1):
        d = datetime.now() - timedelta(days=int(i))
        shift = d.strftime("%d.%m.%Y")
        response = await request_arg(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
        data_list.append(str(response))
    return str(data_list)


async def pretty_view(data):
    return {data["date"]: {
        'EUR': {"sale": data["exchangeRate"][8]["saleRateNB"], "purchase": data["exchangeRate"][8]["purchaseRateNB"]},
        "USD": {"sale": data["exchangeRate"][23]["saleRateNB"],
                "purchase": data["exchangeRate"][23]["purchaseRateNB"]}}}


async def request(url: str) -> dict | str:
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            result = r.json()
            return result


async def get_exchange(url='https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5'):
    response = await request(url)
    data_view_eur = f"EUR: buy - {response[0]['buy']}, sale - {response[0]['sale']}"
    data_view_usd = f"USD: buy - {response[1]['buy']}, sale - {response[0]['sale']}"
    return data_view_eur, data_view_usd


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if len(message.split(" ")) == 1:
                if message == "exchange":
                    async with aiofile.async_open("log.txt", mode='a') as log_file:
                        await log_file.write(f"{datetime.now()} - command 'exchange' executed\n")
                    exchange_eur, exchange_usd = await get_exchange()
                    await self.send_to_clients("Current exchange: ")
                    await self.send_to_clients(exchange_eur)
                    await self.send_to_clients(exchange_usd)
            else:
                args = message.split(" ")
                try:
                    if args[0] == "exchange" and 11 > int(args[1]) > 0:
                        r = await format_date(int(args[1]))
                        await self.send_to_clients(r)
                        async with aiofile.async_open("log.txt", mode='a') as log_file:
                            await log_file.write(f"{datetime.now()} - command 'exchange' executed\n")
                except Exception:
                    print("You need to write something like 'exchange 5'")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
