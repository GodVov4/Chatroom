import aiohttp
import argparse
import asyncio
import datetime

from prettytable import PrettyTable


IPS = ['37.19.220.129', '37.19.220.179', '37.19.220.180', '138.199.48.1', '138.199.48.4']
PORT = '8443'
proxies = [None] + [f'http://{IP}:{PORT}' for IP in IPS]
proxies.extend(proxies)


async def request(url: str, proxy: None | str) -> dict[str | int | float | list[dict[str | int | float]]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, verify_ssl=False, proxy=proxy) as response:
            if response.status == 200:
                return await response.json()


async def str_date(date: datetime) -> str:
    return datetime.datetime.strftime(date, '%d.%m.%Y')


async def get_table(data: tuple[dict[str | int | float | list[dict[str | int | float]]]], currency: list):

    first_column = []
    for curr in currency:
        first_column.append(curr)
        first_column.append('')

    second_column = []
    for _ in range(len(currency)):
        second_column.append('Sale')
        second_column.append('Buy')

    table = PrettyTable()
    if len(data) == 1:
        table.title = f'Курс валют {", ".join(currency)} за {data[0].get("date")[:-5]}'
    else:
        table.title = f'Курс валют {", ".join(currency)} з {data[-1].get("date")[:-5]} по {data[0].get("date")[:-5]}'
    table.add_column('', first_column)
    table.add_column('Дата', second_column)

    for day in data:
        if not day.get('exchangeRate'):
            table.title = f'Відсутні дані за {day.get("date")}'
            continue
        main_column = []
        for curr in currency:
            main_column.extend([round(elem.get('saleRate', elem.get('saleRateNB')), 2)
                                for elem in day.get('exchangeRate') if elem.get('currency') == curr])
            main_column.extend([round(elem.get('purchaseRate', elem.get('purchaseRateNB')), 2)
                                for elem in day.get('exchangeRate') if elem.get('currency') == curr])
        table.add_column(day.get('date'), main_column)
    table.align['Дата'] = table.align[''] = 'r'
    return table


async def get_all_dates(days: int) -> list[str]:
    today = datetime.date.today()
    choose_date = today - datetime.timedelta(days)
    result = []
    while today > choose_date:
        date = await str_date(today)
        result.append(date)
        today -= datetime.timedelta(1)
    return result


async def main(days=1, currency=('EUR', 'USD')):
    default_days = 1
    default_currency = ['EUR', 'USD']

    parser = argparse.ArgumentParser('Exchange', 'Get exchange from PryvatBank')
    parser.add_argument(
        '-d', '--days', type=int, default=default_days, help='Number of days to display (default=1)')
    parser.add_argument(
        '-c', '--currency', type=str, default=default_currency, help='Choose currency to display (default=EUR, USD)')
    args = parser.parse_args()

    # validate days
    if days == default_days:
        days = args.days
    if not 0 < days <= 10:
        print('Покажу лише від 1 до 10 днів')
        return 'Покажу лише від 1 до 10 днів'
    dates = await get_all_dates(days)

    # validate currency
    currency = list(currency)
    if currency != default_currency:
        currency = default_currency + currency
    if currency == default_currency and currency != args.currency:
        currency = args.currency.upper().replace(',', '').strip().split()

    responses = []
    for date, proxy in zip(dates, proxies):
        url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'
        responses.append(asyncio.create_task(request(url, proxy)))

    exchanges = await asyncio.gather(*responses)
    try:
        result = await get_table(exchanges, currency)
    except ValueError:
        print(f'Валюти {", ".join(currency)} немає.')
        return f'Валюти {", ".join(currency)} немає.'
    print(result)
    return result.get_string()


if __name__ == '__main__':
    asyncio.run(main())
