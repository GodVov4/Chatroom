import asyncio
import logging
import names
import websockets

from abc import ABC, abstractmethod
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

from exchange import main as get_exchange


log_format = '%(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
file_handler = logging.FileHandler("exchange.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger()
logger.addHandler(file_handler)


class ABServer(ABC):

    @abstractmethod
    async def register(self, ws: WebSocketServerProtocol):
        pass

    @abstractmethod
    async def unregister(self, ws: WebSocketServerProtocol):
        pass

    @abstractmethod
    async def send_to_clients(self, message: str):
        pass

    @abstractmethod
    async def ws_handler(self, ws: WebSocketServerProtocol):
        pass

    @abstractmethod
    async def distribute(self, ws: WebSocketServerProtocol):
        pass


class Server(ABServer):
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnect')

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
            message_split = message.split()
            match message_split:
                case ['exchange']:
                    await self.send_to_clients('Шукаю курс валют...')
                    logger.info('Get exchange with default parameters')
                    exchange = await get_exchange()
                    await self.send_to_clients(exchange)
                case 'exchange', days, *currency:
                    await self.send_to_clients('Шукаю курс валют...')
                    logger.info(f'Get exchange with custom parameters: {days}, {currency}')
                    exchange = await get_exchange(int(days), currency)
                    await self.send_to_clients(exchange)
                case _:
                    await self.send_to_clients(f'{ws.name}: {message}')


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
