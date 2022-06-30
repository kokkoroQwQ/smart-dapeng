
# -*- coding: utf-8 -*-

__auth__ = "yinbing"
__DEBUG__ = True


from blinker_cum import (
    Device, 
    ButtonWidget,
    NumberWidget, 
    TextWidget, 
    RangeWidget,
)
from sensors import (
    get_humid_indoor,
    get_humid_outdoor,
    get_temp_indoor,
    get_temp_outdoor,
    get_light_indoor,
    get_light_outdoor,
    get_rain_state,
    get_juanlian_chengdu,
    get_fengkou_chengdu
)
from time import sleep
from blinker_cum.device import logger

# from aiohttp.client_exceptions import ClientConnectorError

auto_juanlian = True
auto_fengkou = True

device = Device("3a66eca2c941", websocket=False)

num_temp_indoor = device.addWidget(NumberWidget("num-tid"))
num_temp_outdoor = device.addWidget(NumberWidget("num-tod"))

num_humid_indoor = device.addWidget(NumberWidget("num-hid"))
num_humid_outdoor = device.addWidget(NumberWidget("num-hod"))

num_light_indoor = device.addWidget(NumberWidget("num-lid"))
num_light_outdoor = device.addWidget(NumberWidget("num-lod"))

tex_rain = device.addWidget(TextWidget("tex-rain"))

ran_juanlian = device.addWidget(RangeWidget("ran-jua"))
btn_auto_juanlian = device.addWidget(ButtonWidget("btn-ajl"))

ran_fengkou = device.addWidget(RangeWidget("ran-fen"))
btn_auto_fengkou = device.addWidget(ButtonWidget("btn-afk"))



async def juanlian_fengkou_state():
    await btn_auto_juanlian.turn("on" if auto_juanlian else "off").update()
    await ran_juanlian.value(get_juanlian_chengdu()).update()

    await btn_auto_fengkou.turn("on"  if auto_fengkou else "off").update()
    await ran_fengkou.value(get_fengkou_chengdu()).update()


async def ready_func():
    await num_temp_indoor.value(get_temp_indoor()).update()
    await num_humid_indoor.value(get_humid_indoor()).update()
    await num_light_indoor.value(get_light_indoor()).update()
    await tex_rain.text("有雨" if get_rain_state() else "无雨").update()
    await juanlian_fengkou_state()
    
async def heartbeat_func(msg):
    await ready_func()

async def btn_auto_jualian_callback(received_data):
    global auto_juanlian
    if auto_juanlian == False and received_data[btn_auto_juanlian.key] == "on":
        auto_juanlian = True
        await device.wechat(title="通知", state="状态转换", text="自动控制已启用")
    elif auto_juanlian == True and received_data[btn_auto_juanlian.key] == "off":
        auto_juanlian = False

    await btn_auto_juanlian.turn("on" if auto_juanlian else "off").update()
    await ran_juanlian.value(get_juanlian_chengdu()).update()

async def btn_auto_fengkou_callback(received_data):
    global auto_fengkou
    if auto_fengkou == False and received_data[btn_auto_fengkou.key] == "on":
        auto_fengkou = True
        await device.wechat(title="通知", state="状态转换", text="自动控制已启用")
    elif auto_fengkou == True and received_data[btn_auto_fengkou.key] == "off":
        auto_fengkou = False

    await btn_auto_fengkou.turn("on" if auto_fengkou else "off").update()
    await ran_fengkou.value(get_juanlian_chengdu()).update()

async def ran_juanlian_callback(received_data):
    if auto_juanlian == True:
        sleep(2)
        await ran_juanlian.value(get_juanlian_chengdu()).update()
    else:
        pass

async def ran_fengkou_callback(received_data):
    if auto_fengkou == True:
        sleep(2)
        await ran_fengkou.value(get_fengkou_chengdu()).update()
    else:
        pass

btn_auto_fengkou.func = btn_auto_fengkou_callback
btn_auto_juanlian.func = btn_auto_jualian_callback
ran_fengkou.func = ran_fengkou_callback
ran_juanlian.func = ran_juanlian_callback

device.ready_callable = ready_func
device.heartbeat_callable = heartbeat_func

if __name__ == "__main__":
    if __DEBUG__ == False:
        # 关闭sys.stderr，即关闭console输出
        logger.remove(handler_id=None)
        # 生成日志文件，utf-8编码，每天0点切割，zip压缩，保留30天
        log_path = './log/log.log'
        logger.add(log_path+'_{time}', level="INFO", rotation='00:00',retention='30 days', compression='zip', encoding='utf-8')
        #logger.debug("日志保存路径："+log_path)
    
    device.run()
    
    
