import requests

with open('proxies.txt') as F:
    for proxy in F.read().split('\n'):
        response = requests.get('https://yourdomain',proxies={'http':proxy},timeout=2)
        if response.ok:
            print('Good!')
        else:
            print('Bad!')