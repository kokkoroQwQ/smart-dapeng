

import requests

weather_api = "http://autodev.openspeech.cn/csp/api/v2.1/weather"
city_name = "五寨"

url = '{0}?openId=aiuicus&clientType=android&sign=android&needMoreData=true&pageNo=1&pageSize=1&city={1}'.format(weather_api, city_name)
try:
    r = requests.get(url)
    print(r.text,type(r.text))
except requests.exceptions.ConnectionError:
    print("ConnectionError")
