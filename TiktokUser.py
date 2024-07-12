import json
import random
import time
from io import BytesIO
from urllib.parse import urlencode, quote

import pycurl
from bs4 import BeautifulSoup


def pycurl_send_request(url, method='GET', headers=None, cookies=None, proxy=None, data=None):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)

    c.setopt(pycurl.CONNECTTIMEOUT, 3)

    c.setopt(pycurl.TIMEOUT, 5)

    if method.upper() == 'POST':
        c.setopt(c.POST, 1)
        if data:
            post_data = urlencode(data)
            c.setopt(c.POSTFIELDS, post_data)
        else:
            c.setopt(c.POSTFIELDS, '')
    else:
        c.setopt(c.HTTPGET, 1)
    # Set headers
    if headers:
        headers_list = [f'{key}: {value}' for key, value in headers.items()]
        c.setopt(c.HTTPHEADER, headers_list)

    # Set cookies
    if cookies:
        cookies_list = [f'{key}={value}' for key, value in cookies.items()]
        c.setopt(c.COOKIE, '; '.join(cookies_list))

    # Set proxy
    if proxy:
        c.setopt(c.PROXY, proxy)
    else:
        print('NO PROXY!!!')
    # Set response buffer
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_TLSv1_2)
    c.perform()

    # Get response
    response_code = c.getinfo(pycurl.RESPONSE_CODE)
    response_data = buffer.getvalue().decode('utf-8', errors='ignore')

    # Cleanup
    c.close()

    return response_code, response_data


def get_target_info(target_url, proxies, finger_print):
    headers = {
        'User-Agent': finger_print
    }
    try:
        response_code, response_data = pycurl_send_request(target_url, headers=headers, proxy=proxies)
        if response_code == 200:
            html = response_data
            soup = BeautifulSoup(html, 'html.parser')
            DATA = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
            if DATA:
                script_text = json.loads(DATA.string)['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo']['user']
                return script_text['id'], script_text['nickname'], script_text['secUid']
            else:
                print("__UNIVERSAL_DATA_FOR_REHYDRATION__ not found, maybe bad session")
        else:
            print('Request error')
    except Exception as e:
        print('Just error:', str(e))
    return None, None, None


class TiktokUser():
    def __init__(self, target_url, target_secUid, target_id, target_nick_name, proxies, cookie, finger_print,
                 reason='9004'):
        self.target_url = target_url
        self.target_nick_name = target_nick_name
        self.target_secUid = target_secUid
        self.target_id = target_id
        self.csrf = ''
        self.finger_print = finger_print
        self.proxies = proxies
        self.payload = {}
        self.data = ''
        self.reason = reason
        self.url = ''
        self.__prepare_cookies(cookie)

    def send_follow(self):
        if self.__prepare_url_follow():
            self.__sign_and_send()

    def send_report(self):
        if self.__prepare_url():
            self.__sign_and_send()

    def __prepare_cookies(self, cookie):
        redacted_cookies = {}
        for cookie_line in cookie.split('\n'):
            redacted = cookie_line.strip().split('\t')
            try:
                redacted_cookies[redacted[-2]] = redacted[-1]
            except:
                pass
        self.cookie = redacted_cookies

    def __get_user_id(self, url='https://www.tiktok.com/'):
        headers = {
            'User-Agent': self.finger_print
        }
        try:
            response_code, response_data = pycurl_send_request(url, headers=headers, proxy=self.proxies,
                                                               cookies=self.cookie)
            if response_code == 200:
                html = response_data
                soup = BeautifulSoup(html, 'html.parser')
                DATA = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
                if DATA:
                    script_text = json.loads(DATA.string)['__DEFAULT_SCOPE__']['webapp.app-context']
                    user = script_text['user']
                    return user['uid'], user['region'], user['secUid'], script_text['csrfToken']
                else:
                    print("__UNIVERSAL_DATA_FOR_REHYDRATION__ not found, maybe bad session")
            else:
                print('Request error')
        except Exception as e:
            print(f'Bad access {e}')
        return None, None, None, None

    def __prepare_url(self):
        self.url = f"https://www.tiktok.com/aweme/v2/aweme/feedback/?"
        owner_id, country, secUidOwner, csrf = self.__get_user_id()
        if owner_id is None:
            return False
        if country == '':
            country = 'EN'
        low_country = f'{country.lower()}-{country.upper()}'
        self.payload = {
            "WebIdLastTime": str(int(time.time())),
            "aid": '1988',
            "app_language": low_country,
            "app_name": "tiktok_web",
            "browser_language": low_country,
            "browser_name": "Mozilla",
            "browser_online": 'true',
            "browser_platform": "Win32",
            "browser_version": self.finger_print,
            "channel": "tiktok_web",
            "cookie_enabled": 'true',
            "current_region": country,
            "device_id": str(random.randint(3333333333333333333, 8888888888888999999)),
            "device_platform": "web_pc",
            "focus_state": 'true',
            "from_page": "user",
            "history_len": str(random.choice([5, 10, 15, 20, 30])),
            "is_fullscreen": 'false',
            "is_page_visible": 'true',
            "lang": low_country,
            "nickname": self.target_nick_name,
            "object_id": self.target_id,
            "os": "windows",
            "owner_id": self.target_id,
            "priority_region": "",
            "reason": self.reason,
            "referer": "https://www.tiktok.com",
            "root_referer": "https://www.tiktok.com/foryou",
            "region": country,
            "report_type": "user",
            "reporter_id": owner_id,
            "screen_height": '1080',
            "screen_width": '1920',
            "secUid": self.target_secUid,
            "target": self.target_id,
            "tz_name": "Europe/Paris",
            "webcast_language": low_country
        }
        return True

    def __prepare_url_follow(self):
        self.url = f"https://www.tiktok.com/api/commit/follow/user/?"
        owner_id, country, secUidOwner, csrf = self.__get_user_id()
        if owner_id is None:
            return False
        if country == '':
            country = 'EN'
        low_country = f'{country.lower()}-{country.upper()}'
        self.payload = {
            "WebIdLastTime": str(int(time.time())),
            "action_type": 1,
            "aid": 1988,
            "app_language": country.lower(),
            "app_name": "tiktok_web",
            "browser_language": low_country,
            "browser_name": "Mozilla",
            "browser_online": True,
            "browser_platform": "Win32",
            "browser_version": self.finger_print,
            "channel": "tiktok_web",
            "channel_id": 0,
            "cookie_enabled": True,
            "device_id": str(random.randint(3333333333333333333, 8888888888888999999)),
            "device_platform": "web_pc",
            "focus_state": True,
            "from": 18,
            "fromWeb": 1,
            "from_page": "fyp",
            "from_pre": 0,
            "history_len": str(random.choice([5, 10, 15, 20, 30])),
            "is_fullscreen": False,
            "is_page_visible": True,
            "os": "windows",
            "priority_region": country,
            "referer": "https://www.google.com/",
            "region": country,
            "root_referer": "https://www.google.com/",
            "screen_height": 1080,
            "screen_width": 1920,
            "sec_user_id": self.target_secUid,
            "type": 1,
            "tz_name": "Europe",
            "user_id": self.target_id,
            "webcast_language": country.lower()
        }

        return True

    def __sign_and_send(self):
        for i, j in self.payload.items():
            self.url += f'{i}={j}&'
        self.url = self.url[:-1]
        url = 'https://tiktok-signature.onrender.com/api/signature/'  # API url
        data = {
            'url': self.url,  # TikTok url want to sign
            'userAgent': self.finger_print,  # Paste your browser userAgent
            'version': '2',  # choice 1 or 2
            'Token': 'main-CPO@Signature',  # API Token, TY for chinese friends! return 'signed'
            'data': '',  # TikTok request body
            'Bogus': True,  # make True to generate
            'msToken': True,  # ...
            '_signature': True  # ...
        }
        response_code, response_data = pycurl_send_request(url=url, method='POST', data=data, proxy=self.proxies)
        if response_code == 200:
            go_url = json.loads(response_data)['new_url']
            headers = {
                'Referer': self.target_url,
                'User-Agent': self.finger_print
            }
            if self.csrf != '':
                # headers['Origin'] = 'https://www.tiktok.com'
                # headers['Tt-Csrf-Token'] = self.csrf
                # headers['Tt-Ticket-Guard-Iteration-Version']=0
                # headers['Tt-Ticket-Guard-Public-Key']='BJZSEagCx9In39vnmTKx8mao8gWbBVVhIs/OdWszTUbmqUkxJYWPcARvJ48naRpQGT9nCCxlPmJKQhRyg/aCmLE='
                # headers['Tt-Ticket-Guard-Version']=2
                # headers['Tt-Ticket-Guard-Web-Version:']=1
                # headers['X-Secsdk-Csrf-Token'] ='000100000001b3e7d098af9db90016316752cb8952b745741d3d0e5d50dcac306eaa136f47f517e0f298e6b9ce82'
                pass
            encoded_url = quote(go_url, safe=':/?&=')
            res_code, res_data = pycurl_send_request(url=encoded_url, method='POST', proxy=self.proxies,
                                                     cookies=self.cookie, headers=headers)
            if res_code == 200:
                global counter
                resp = json.loads(res_data)
                counter += 1
                return 'signed'
            elif res_code == 403:
                print(f'Bad proxy! {res_code}! {self.proxies}')
                return 'bad_proxy'
            else:
                print(f'{res_code} {res_data} skip...')
                return 'skip'
        else:
            print('url not signed!')

        return 'url not signed'
