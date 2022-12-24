import asyncio
import json
from aiocfscrape import CloudflareScraper as requests


# Decorator to check if the moon access is expired and notify user to update it
def unauthorized(func):
    async def wrapper(*a, **k):
        try:
            fuc = await func(*a, **k)
            return fuc
        except:
            pass

    return wrapper


class Moon:
    def __init__(self, token) -> None:
        if token != "":
            self.access_token = token
        self.authed = True
        self.base = "https://api.paywithmoon.com/v1/moon/"

        # making requests session & adding headers to it

    async def init_session(self, token=None):
        if token == None:
            token = self.access_token
        self.headers = {
            'authority': 'api.paywithmoon.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer ' + token,
            'content-type': 'application/json; charset=UTF-8',
            'origin': 'https://paywithmoon.com',
            'referer': 'https://paywithmoon.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36'
        }
        self.session = requests()
        for key, val in self.headers.items():
            self.session.headers.add(key, val)

    # making requests to base url of moon api
    async def __request(self, method: str, path, posted_data=None):
        if posted_data == None:
            resp = await self.session.request(method, self.base + path, headers=self.headers)
        else:
            resp = await self.session.request(method, self.base + path, headers=self.headers, json=posted_data)
        # checking of moon access token is valid
        if resp.status == 401:
            raise Exception('auth')
        else:
            try:
                return await  resp.json()
            except:
                print()

    async def delete_card(self, card_id):
        resp = await self.__request("post", "cards/delete", {"comments": "", "cardId": card_id, "platform": "web-app"})

    async def get_profile(self):
        try:
            response = await self.__request("GET", "users?includeCoinbaseInfo=false")
            return True, response['user']
        except:
            return False, None

    async def generate_card(self, amount=5):
        suc, card = await self.get_active_card()
        if suc:
            await self.delete_card(card)
        response = await self.__request('POST', "api/cards/funding/onchain",
                                        {"cardValue": f"{amount}.00", "applyRewardSats": False, "applyMoonCredit": True,
                                         "currency": "BTC", "cardProduct": "CREDIT_CARD_PRODUCT",
                                         "blockchain": "BITCOIN", "coin": "BTC"})
        try:
            print(f"{response['pan']}:{response['exp'][:2] + response['exp'][2:]}:{response['cvv']}")
            return True, response["pan"], response["exp"][:2] + "/" + response["exp"][2:], response["cvv"], response[
                'expirationTime']
        except:
            return [False, None, None, None, None]


    # @is_authed
    async def get_transactions(self):
        resp = await self.__request('post', "transactions?currentPage=1&perPage=10")
        return resp

    # @is_authed
    async def get_active_card(self):
        resp = await self.__request('get', "cards?display=&currentPage=1&perPage=1&inactiveCards=false")
        try:
            card = resp["cards"][0]['id']
            return True, card
        except:
            return False, None


config = json.load(open('config.json'))

moon = Moon(config['moon_access_token'])

loop = asyncio.get_event_loop()
loop.run_until_complete(moon.init_session())
for i in range(100):
    loop.run_until_complete(moon.generate_card())
