# -*- coding: utf-8 -*-

__auth__ = "yinbing"

from random import randint
from time import sleep
from asyncio import sleep as async_sleep
import aiofiles
from threading import Thread


def get_humid_indoor():
    return 33.258

def get_humid_outdoor():
    return randint(1, 100)

def get_temp_indoor():
    return randint(-40, 50)

def get_temp_outdoor():
    return randint(-40, 50)

def get_light_indoor():
    return randint(0, 65535)

def get_light_outdoor():
    return randint(0, 200000)

def get_rain_state():
    if randint(0,1) == 1:
        return True
    else:
        return False

class Motor:
    _speed:float = None
    _state:int = 0   #0停止，1正转， 2反转
    _path:str = None
    _set_speed_able:bool = True
    _set_chengdu_able:bool = True
    _set_state_able:bool = True
    _chengdu:float = 0
    _exit_last_motor_threading_now:bool = False
    _motor_threading_running:bool = False

    def __init__(self, dev_path:str):
        self._path = dev_path
        self.load()
    
    def power_func(self, mode:str):
        pass
    
    async def _save_config(self, speed:float, chengdu:float, state:int):
        if (self._set_speed_able and self._set_chengdu_able and self._set_state_able) == False:
            return -1
        
        self._set_speed_able = False
        async with aiofiles.open(self._path+"speed", "w") as fp:
            await fp.write(str(speed))
            await fp.close()
        self._set_speed_able = True

        self._set_chengdu_able = False
        async with aiofiles.open(self._path+"chengdu", "w") as fp:
            await fp.write(str(chengdu))
            await fp.close()
        self._set_chengdu_able = True

        self._set_state_able = False
        async with aiofiles.open(self._path+"state", "w") as fp:
            await fp.write(str(state))
            await fp.close()
        self._set_state_able = True
    
    async def set_speed(self, speed:float):
        if self._set_speed_able == False:
            return -1
        self._speed = speed
        self._set_speed_able = False
        async with aiofiles.open(self._path+"speed", "w") as fp:
            await fp.write(str(self._speed))
            await fp.close()
        self._set_speed_able = True
        return 0
    
    def get_speed(self):
        return self._speed
    
    def get_chengdu(self, flush:bool = False):
        if flush:
            with open(self._path+"chengdu", "r") as fp:
                self._chengdu = float(fp.read())
                fp.close()
        return self._chengdu
    
    def get_state(self, flush:bool = False):
        if flush:
            with open(self._path+"state", "r") as fp:
                self._state = int(fp.read())
                fp.close()
        return self._state
    
    def load(self):
        with open(self._path+"speed", "r") as fp:
            self._speed = float(fp.read())
            fp.close()

        with open(self._path+"chengdu", "r") as fp:
            self._chengdu = float(fp.read())
            fp.close()

        with open(self._path+"state", "r") as fp:
            self._state = int(fp.read())
            fp.close()
    
    def set_chengdu(self, val):
        # if (self._set_chengdu_able and self._set_state_able) == False:
        #     print("return -1")
        #     return -1

        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self._exit_last_motor_threading_now = False
            
        if self.power_func == None:
            # print("return -3")
            return -3
        self._set_chengdu_able = False
        self._set_state_able = False
        
        self.get_chengdu(flush = True)
        with open(self._path+"state", "w") as fp_state:
            if self._chengdu < val:
                fp_state.write("1") #正转
                self._state = 1
                # print("state: {}".format(self._state))
            elif self._chengdu > val:
                fp_state.write("-1") #反转
                self._state = -1
                # print("state: {}".format(self._state))
            else:
                fp_state.write("0") #停止
                self._state = 0
                self._set_chengdu_able = True
                self._set_state_able = True
                # print("state: {}".format(self._state))
                return -2

        def task():
            self._motor_threading_running = True
            with open(self._path+"chengdu", "w") as fp_chengdu:
                self.power_func("on")    #here let the GPIO ouput evaluate
                while (self._state>0 and self._chengdu<val) or (self._state<0 and self._chengdu>val):
                    if self._exit_last_motor_threading_now == True:
                        break
                    self._chengdu += self._state * self._speed
                    sleep(1)
                self.power_func("off")    #here let the GPIO ouput disevaluate
                fp_chengdu.write(str(self._chengdu))
                fp_chengdu.close()
            
            self._state = 0
            fp_state = open(self._path+"state", "w")
            fp_state.write("0")
            fp_state.close()

            self._set_chengdu_able = True
            self._set_state_able = True
            self._motor_threading_running = False
        
        t_task = Thread(target=task)
        t_task.start()

        return 0




class Juanlian(Motor):
    def __init__(self, dev_path:str="./dev/juanlian/"):
        super().__init__(dev_path)

    def power_func(self, mode:str):
        pass

class Fengkou(Motor):
    def __init__(self, dev_path:str="./dev/fengkou/"):
        super().__init__(dev_path)

    def power_func(self, mode:str):
        pass


