# -*- coding: utf-8 -*-

__auth__ = "yinbing"
__DEBUG__ = False

import asyncio
import json
import threading
from asyncio import sleep as async_sleep

from aiohttp.client_exceptions import \
    ClientConnectorError as aiohttp_ClientConnectorError
from requests import get as sync_get
from requests.exceptions import ConnectionError as requests_ConnectionError

from blinker_cum import (ButtonWidget, Device, NumberWidget, RangeWidget,
                         TextWidget)
from blinker_cum.device import logger
# sensors.py模块内封装了各类传感器的读写函数
from sensors import (Fengkou, Juanlian, get_humid_indoor, get_humid_outdoor,
                     get_light_indoor, get_light_outdoor, get_rain_state,
                     get_temp_indoor, get_temp_outdoor)

__weather_icon__ =   {"晴":"fas fa-sun",         "阴":"fas fa-cloud",          "多云":"fas fa-sun-cloud", 
                    "小雨":"fas fa-cloud-rain",  "中雨":"fas fa-cloud-rain",    "大雨":"fas fa-cloud-rain", 
                    "暴雨":"fas fa-cloud-rain",  "雷雨":"fas fa-thunderstorm",  "台风":"fas fa-tornado", 
                    "冰雹":"fas fa-cloud-hail",  "雨夹雪":"fas fa-cloud-sleet", "雪":"fas fa-snowflake", 
                    "小雪":"fas fa-snowflake",   "中雪":"fas fa-snowflake",     "大雪":"fas fa-snowflake", 
                    "暴雪":"fas fa-snowflake",   "雾":"fas fa-fog",             "小雾":"fas fa-fog",
                    "中雾":"fas fa-fog",         "大雾":"fas fa-fog",           "重雾":"fas fa-fog",
                    "浓雾":"fas fa-fog",         "霾":"fas fa-smog",            "雾霾":"fas fa-smog"}


# 定义一个自定义的blinker设备
class IotDevice(Device):
    def __init__(self, auth_key, websocket: bool = False):
        super().__init__(auth_key, websocket=websocket)
        self.weather_api = "http://autodev.openspeech.cn/csp/api/v2.1/weather"

        self.num_temp_indoor = self.addWidget(NumberWidget("num-tid"))
        self.num_temp_outdoor = self.addWidget(NumberWidget("num-tod"))

        self.num_humid_indoor = self.addWidget(NumberWidget("num-hid"))
        self.num_humid_outdoor = self.addWidget(NumberWidget("num-hod"))

        self.num_light_indoor = self.addWidget(NumberWidget("num-lid"))
        self.num_light_outdoor = self.addWidget(NumberWidget("num-lod"))

        self.tex_weather = self.addWidget(TextWidget("tex-wea"))

        self.tex_rain = self.addWidget(TextWidget("tex-rain"))

        self.num_juanlian = self.addWidget(NumberWidget("num-jua"))
        self.num_fengkou = self.addWidget(NumberWidget("num-fen"))

        self.ran_juanlian = self.addWidget(RangeWidget("ran-jua"))
        self.btn_manual_juanlian = self.addWidget(ButtonWidget("btn-mjl"))

        self.ran_fengkou = self.addWidget(RangeWidget("ran-fen"))
        self.btn_manual_fengkou = self.addWidget(ButtonWidget("btn-mfk"))

        self.ready_callable = self.ready_callable_cumstom
        self.heartbeat_callable = self.heartbeat_callable_cumstom
        self.realtime_callable = self.realtime_callable_cumstom

        self.btn_manual_juanlian.func = self.btn_manual_juanlian_callable
        self.btn_manual_fengkou.func  = self.btn_manual_fengkou_callable

        self.ran_juanlian.func = self.ran_juanlian_callable
        self.ran_fengkou.func  = self.ran_fengkou_callable

        self.weather = None
        self.sunrise = None
        self.sunset  = None

    def get_weather_moji(self, city_name="五寨"):
        url = '{0}?openId=aiuicus&clientType=android&sign=android&needMoreData=true&pageNo=1&pageSize=1&city={1}'.format(self.weather_api, city_name)
        try:
            text = sync_get(url).text
            weather_json =  json.loads(text)
            if weather_json['code'] != 0:
                return
            print(type(weather_json)) #dict
            self.weather = weather_json['data']['list'][0]['weather']
            self.sunrise = weather_json['data']['list'][0]['moreData']['sunrise']
            self.sunset  = weather_json['data']['list'][0]['moreData']['sunset']
        except requests_ConnectionError:
            print("requests.ConnectionError")
        

    def ready_callable_cumstom(self):
        self.get_weather_moji()
        self.scheduler.add_job(self.get_weather_moji, 'interval', minutes=30, jitter=60)    # 每30分钟get一次天气，动作的上下浮动时间在60秒内

    async def heartbeat_callable_cumstom(self, dapeng_device):
        await self.num_temp_indoor.value(dapeng_device.temperature_indoor).update()
        await self.num_temp_outdoor.value(dapeng_device.temperature_outdoor).update()

        await self.num_humid_indoor.value(dapeng_device.humid_indoor).update()
        await self.num_humid_outdoor.value(dapeng_device.humid_outdoor).update()

        await self.num_light_indoor.value(dapeng_device.light_indoor).update()
        await self.num_light_outdoor.value(dapeng_device.light_outdoor).update()

        if self.weather != None:
            if self.weather in __weather_icon__:
                icon = __weather_icon__[self.weather]
            else:
                icon = "fas fa-exclamation-circle"
            await self.tex_weather.text(self.weather).icon(icon).update()

        is_rain = dapeng_device.rain_state
        await self.tex_rain.text("有雨" if is_rain else "无雨").icon("fad fa-raindrops" if is_rain else "fas fa-sun").update()

        await self.num_juanlian.value(dapeng_device.juanlian_chengdu).update()
        await self.num_fengkou.value(dapeng_device.fengkou_chengdu).update()

        if dapeng_device.manual_juanlian_able == False:
            await self.ran_juanlian.value(dapeng_device.juanlian_chengdu).update()
        if dapeng_device.manual_fengkou_able == False:
            await self.ran_fengkou.value(dapeng_device.fengkou_chengdu).update()

        await self.btn_manual_juanlian.turn("on" if dapeng_device.manual_juanlian_able else "off").update()
        await self.btn_manual_fengkou.turn( "on" if dapeng_device.manual_fengkou_able  else "off").update()

        
    
    async def realtime_callable_cumstom(self, dapeng_device, keys):
        # print(dapeng_device.juanlian_state)
        # print(dapeng_device.fengkou_state)
        # print(keys)
        for key in keys:
            if key == "num-jua":
                if dapeng_device.juanlian_state == 0:
                    if key in self.realtime_tasks:
                        self.realtime_tasks[key].remove()
                        del self.realtime_tasks[key]
                    continue
                await self.sendRtData(key, dapeng_device.juanlian_dev.get_chengdu)
            elif key == "num-fen":
                if dapeng_device.fengkou_state == 0:
                    if key in self.realtime_tasks:
                        self.realtime_tasks[key].remove()
                        del self.realtime_tasks[key]
                    continue
                await self.sendRtData(key, dapeng_device.fengkou_dev.get_chengdu)
            else:
                pass

    async def btn_manual_juanlian_callable(self, dapeng_device, received_data):
        if received_data[self.btn_manual_juanlian.key] == "on" and not dapeng_device.manual_juanlian_able:
            dapeng_device.manual_juanlian_able = True
            # await self.wechat(title="通知", state="切换手动", text="手动控制已启用")
        elif received_data[self.btn_manual_juanlian.key] == "off" and dapeng_device.manual_juanlian_able:
            dapeng_device.manual_juanlian_able = False
            # await self.wechat(title="通知", state="切换自动", text="手动控制已停用")
        dapeng_device.auto_run = not (dapeng_device.manual_juanlian_able or dapeng_device.manual_fengkou_able)
        await self.btn_manual_juanlian.turn("on" if dapeng_device.manual_juanlian_able else "off").update()
        await self.ran_juanlian.value(dapeng_device.juanlian_chengdu).update()

    async def btn_manual_fengkou_callable(self, dapeng_device, received_data):
        if received_data[self.btn_manual_fengkou.key] == "on" and not dapeng_device.manual_fengkou_able:
            dapeng_device.manual_fengkou_able = True
            # await self.wechat(title="通知", state="切换手动", text="手动控制已启用")
        elif received_data[self.btn_manual_fengkou.key] == "off" and dapeng_device.manual_fengkou_able:
            dapeng_device.manual_fengkou_able = False
            # await self.wechat(title="通知", state="切换自动", text="手动控制已停用")
        dapeng_device.auto_run = not (dapeng_device.manual_juanlian_able or dapeng_device.manual_fengkou_able)
        await self.btn_manual_fengkou.turn("on" if dapeng_device.manual_fengkou_able else "off").update()
        await self.ran_fengkou.value(dapeng_device.fengkou_chengdu).update()
    
    async def ran_juanlian_callable(self, dapeng_device, received_data):
        if dapeng_device.manual_juanlian_able == True:
            dapeng_device.set_juanlian_chengdu(received_data[self.ran_juanlian.key])
            await self.sendRtData("num-jua", dapeng_device.juanlian_dev.get_chengdu)
        else:
            await async_sleep(1.5)
            await self.ran_juanlian.value(dapeng_device.juanlian_chengdu).update()

    async def ran_fengkou_callable(self, dapeng_device, received_data):
        if dapeng_device.manual_fengkou_able == True:
            dapeng_device.set_fengkou_chengdu(received_data[self.ran_fengkou.key])
            await self.sendRtData("num-fen", dapeng_device.fengkou_dev.get_chengdu)
        else:
            await async_sleep(1.5)
            await self.ran_fengkou.value(dapeng_device.fengkou_chengdu).update()

    async def _receiver(self, dapeng_device):
        self.mqtt_connected.wait()

        logger.success("Receiver ready...")
        while True:
            data = self.received_data.get()
            logger.info("received msg: {0}".format(data))

            if isinstance(data, str):
                data = json.loads(data)

            if "fromDevice" in data:
                self.target_device = data["fromDevice"]
            else:
                self.target_device = self.config.uuid

            if "data" in data:
                received_data = data["data"]
            else:
                received_data = data

            if "get" in received_data:
                if received_data["get"] == "state":
                    self.mqtt_client.send_to_device({"state": "online"})
                    if self.heartbeat_callable:
                        await self._custom_runner(self.heartbeat_callable, dapeng_device=dapeng_device)
                elif received_data["get"] == "timing":
                    self.mqtt_client.send_to_device(self.get_timing_data())
                elif received_data["get"] == "countdown":
                    self.mqtt_client.send_to_device(self.get_countdown_data())
            elif "set" in received_data:
                if "timing" in received_data["set"]:
                    if "dlt" in received_data["set"]["timing"][0]:
                        await self.del_timing_data(received_data["set"]["timing"][0]["dlt"])
                    else:
                        await self.set_timing_data(received_data["set"]["timing"])

                    self.mqtt_client.send_to_device(self.get_timing_data())
                elif "countdown" in received_data["set"]:
                    await self.set_countdown_data(received_data["set"]["countdown"])
                    self.mqtt_client.send_to_device(self.get_countdown_data())
            elif "rt" in received_data:
                if self._realtime_callable:
                    await self._custom_runner(self._realtime_callable, dapeng_device=dapeng_device, keys=received_data["rt"])
            else:
                for key in received_data.keys():
                    if key in self.widgets.keys():
                        await self.widgets[key].handler(dapeng_device=dapeng_device, received_data=received_data)
                    else:
                        self.data_reader.put({"fromDevice": self.target_device, "data": {key: received_data[key]}})

            await async_sleep(0)

    # 使得在网络不通时，设备可以进行重连
    async def my_device_init(self):
        while True:
            try:
                await self.device_init()
                break
            except aiohttp_ClientConnectorError:
                print("aiohttp.client_exceptions.ClientConnectorError")
                await async_sleep(5)
            
    async def main(self, dapeng_device):
        tasks = [
            threading.Thread(target=asyncio.run, args=(self.my_device_init(),), daemon=True),
            threading.Thread(target=asyncio.run, args=(self.mqttclient_init(),), daemon=True),
            threading.Thread(target=asyncio.run, args=(self._cloud_heartbeat(),), daemon=True),
            threading.Thread(target=asyncio.run, args=(self._receiver(dapeng_device),), daemon=True),
            threading.Thread(target=self.scheduler_run, daemon=True)
        ]

        if self.websocket:
            tasks.append(threading.Thread(target=asyncio.run, args=(self.init_local_service(),)))

        if self.ready_callable:
            tasks.append(threading.Thread(target=asyncio.run, args=(self._custom_runner(self.ready_callable),)))

        if self.voice_assistant:
            tasks.append(threading.Thread(target=asyncio.run, args=(self.voice_assistant.listen(),)))

        # start
        for task in tasks:
            task.start()
            await async_sleep(1.5)
            # print("tasks[{}].is_alive() = {}".format(tasks.index(task), task.is_alive()))
        
        for task in tasks:
            task.join()
        

    def run(self, dapeng_device):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main(dapeng_device))
        except KeyboardInterrupt:
            loop.stop()
        finally:
            loop.close()


# 定义一个大棚设备类，物质实体和联网实体都是其一方面
class DapengDevice(object):
    __threshold_temp: dict = {"high":30, "low":0}
    __time_auto_act: dict = None
    __time_sunrise: str = None
    __time_sunset: str = None
    iot_device: IotDevice = None
    auto_run: bool = True
    manual_juanlian_able: bool = False
    manual_fengkou_able: bool = False
    juanlian_dev = None
    fengkou_dev  = None

    @property
    def humid_indoor(self):
        return get_humid_indoor()

    @property
    def humid_outdoor(self):
        return get_humid_outdoor()

    @property
    def temperature_indoor(self):
        return get_temp_indoor()

    @property
    def temperature_outdoor(self):
        return get_temp_outdoor()

    @property
    def light_indoor(self):
        return get_light_indoor()

    @property
    def light_outdoor(self):
        return get_light_outdoor()

    @property
    def rain_state(self):
        return get_rain_state()

    @property
    def juanlian_chengdu(self):
        return self.juanlian_dev.get_chengdu()
    def set_juanlian_chengdu(self, val):
        self.juanlian_dev.set_chengdu(val)
    
    @property
    def fengkou_chengdu(self):
        return self.fengkou_dev.get_chengdu()
    def set_fengkou_chengdu(self, val):
        self.fengkou_dev.set_chengdu(val)

    @property
    def juanlian_state(self):
        return self.juanlian_dev.get_state()
    
    @property
    def fengkou_state(self):
        return self.fengkou_dev.get_state()
    
    @property
    def threshold_temp(self):
        return self.__threshold_temp
    def set_threshold_temp(self, dic):
        if dic:
            if "high" in dic.keys():
                self.__threshold_temp["high"] = dic["high"]
            elif "low" in dic.keys():
                self.__threshold_temp["low"] = dic["low"]
        return self.threshold_temp
        


    def __init__(self, auth_key):
        self._auth_key = auth_key
        self.juanlian_dev = Juanlian(dev_path="./dev/juanlian/")
        self.fengkou_dev  = Fengkou(dev_path="./dev/fengkou/")
    
    def __load_config(self):
        # to load self.__threshlod_temp and self.__time_auto_act from the json file
        pass
    def __save_config(self):
        # to save self.__threshlod_temp and self.__time_auto_act to the json file
        pass

    def reset_juanlian_fengkou_runtime(self):
        pass
    
    def __device_init(self):
        self.iot_device = IotDevice(self._auth_key, websocket=False)
        self.__load_config()


    def __auto_control(self):
        pass

    def __main(self):
        self.__device_init()
        self.__auto_control() #这里要再创建一个线程独立跑

    def run(self):
        self.__main()
        self.iot_device.run(self)

if __name__ == "__main__":
    if __DEBUG__ == False:
        logger.remove(handler_id=None)
    dapeng_device = DapengDevice("3a66eca2c941")
    dapeng_device.run()
    