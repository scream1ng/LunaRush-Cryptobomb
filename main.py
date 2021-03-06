import mss
import cv2 as cv
import numpy as np
import os
import pyautogui
import random
from datetime import datetime
import time
import yaml
import pygetwindow as gw
import sys

# load config.yaml
f = open('config.yaml', 'r')
conf = yaml.safe_load(f)
f.close()

def load_template(dir='img/'):
    file_names = os.listdir(dir)
    template = {}
    for file in file_names:
        path = dir + file
        template[file[:-len('.jpg')]] = cv.imread(path)
    return template

def click(x=0, y=0):
    if x == 0 and y == 0:
        pyautogui.click()
    else:
        pyautogui.moveTo(x, y, 0.5 + random.random())
        pyautogui.click()

def screen_shot(screen=(0, 0, 1920, 1080)):
    with mss.mss() as sct:
        monitor = sct.monitors[conf['monitor']]
        left, top, width, height = screen
        scr = sct.grab({
            'monitors': conf['monitor'],
            'left': left,
            'top': top,
            'width': width,
            'height': height
        })
        img = np.array(scr)
    return img

def position(template, threshold=conf['threshold'], img=None, location=(0, 0, 1920, 1080)):
    if img is None:
        img = screen_shot(location)

    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)

    result = cv.matchTemplate(img, template, cv.TM_CCOEFF_NORMED)
    w = template.shape[1]
    h = template.shape[0]

    yloc, xloc = np.where(result >= threshold)
    rectangles = []

    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def click_template(template, count=1, timeout=3, threshold=conf['threshold'], img=None, location=(0, 0, 1920, 1080)):
    start = time.time()
    time_out = False
    left, top, _, _ = location

    while not time_out:
        matches = position(template, threshold, img, location)

        if len(matches) == 0:
            time_out = time.time() - start > timeout
            continue

        if count == 'all':
            count = len(matches)

        i = 0
        while i < count and len(matches) != 0:
            x, y, w, h = matches[i]
            x_loc = left + x + w / 2 + random.randint(-int(w / 2), int(w / 2))
            y_loc = top + y + h / 2 + random.randint(-int(h / 2), int(h / 2))

            pyautogui.moveTo(x_loc, y_loc, 0.5 + random.random())
            pyautogui.click()
            i += 1

        return True
    return False

def check_template(template, timeout=3, threshold=conf['threshold'], img=None, location=(0, 0, 1920, 1080)):
    start = time.time()
    time_out = False

    while not time_out:
        matches = position(template, threshold, img, location)
        if len(matches) == 0:
            time_out = time.time() - start > timeout
            continue
        return True
    return False

def show_matchTemplate(template, threshold=conf['threshold'], img=None, location=(0, 0, 1920, 1080)):
    if img is None:
        img = screen_shot()

    rect = position(template, threshold, img, location)

    for (x, y, w, h) in rect:
        img = cv.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)

    cv.imshow('img', img)

def pause(t):
    time.sleep(t + random.random())

def get_windowTitle(template):
    click_template(template)
    return gw.getActiveWindow().title

class luna():
    def __init__(self, name, window_title):
        self.name = name
        self.template = load_template('luna_img/')
        self.window_left = window_title.left
        self.window_top = window_title.top
        self.window = (window_title.left, window_title.top, window_title.width, window_title.height)
        self.energy = 0

    def login(self):
        click_template(self.template['login'])
        pause(3)
        x, y, w, h = self.window
        click_template(self.template['sign'], location=(x, y, w, h + 170))

    def boss_hunt(self):
        click_template(self.template['boss_hunt_main'], location=self.window)
        pause(1)
        count = len(position(self.template['boss']))
        click_template(self.template['boss'], count, location=self.window)

    def reset(self):
        click_template(self.template['collapse'], threshold=0.9, location=self.window)

        if len(position(self.template['plus'], threshold=0.9, location=self.window)) < 3:
            x, y, _, _ = position(self.template['warrior'], location=self.window)[0]
            click(self.window_left + x + 160, self.window_top + y + 60)
            pause(0.5)
            click(self.window_left + x + 160 + 120, self.window_top +  y + 60)
            pause(0.5)
            click(self.window_left + x + 160 + 120 + 120, self.window_top +  y + 60)

    def play(self):
        click_template(self.template['expand'], location=self.window)

        while True:
            # Check energy
            if len(position(self.template['plus'], threshold=0.9, location=self.window)) >= 1:
                click_template(self.template['expand'], location=self.window)

                if check_template(self.template['energy'], threshold=0.75, location=self.window):
                    self.energy = len(position(self.template['energy'], threshold=0.75, location=self.window))
                    if self.energy > 3:
                        x = 3
                    else:
                        x = len(position(self.template['energy'], threshold=0.75, location=self.window))

                    click_template(self.template['energy'], x, threshold=0.75, location=self.window)
                    click_template(self.template['boss_hunt'], location=self.window)
                else:
                    return

                pause(3)

                # Fighting
                click_template(self.template['vs'], location=self.window)
                fighting = True

                while fighting:
                    if check_template(self.template['tap_to_open'], location=self.window):
                        click_template(self.template['tap_to_open'], location=self.window)
                        pause(3)
                        click()
                        fighting = False
                    elif check_template(self.template['defeat'], location=self.window):
                        click_template(self.template['defeat'], location=self.window)
                        fighting = False

            # Deselecting hero
            elif check_template(self.template['warrior']) and len(position(self.template['plus'], threshold=0.9)) < 3 and len(position(self.template['energy'], threshold=0.75)) >= 1:
                self.reset()

            # Exist loop
            elif len(position(self.template['energy'], threshold=0.75)) < 1:
                return

class bomb:
    def __init__(self, name, window_title):
        self.name = name
        self.template = load_template('bomb_img/')
        self.window_left = window_title.left
        self.window_top = window_title.top
        self.window = (window_title.left, window_title.top, window_title.width, window_title.height)
        self.energy = 0

    def login(self):
        click_template(self.template['connect_wallet'], location=self.window)
        pause(3)
        x, y, w, h = self.window
        click_template(self.template['sign'], location=(x, y, w, h + 170))
        pause(3)
        click_template(self.template['treasure_hunt'], location=self.window)

    def resend(self):
        click_template(self.template['back2home'], location=self.window)
        pause(1)
        click_template(self.template['hero_home'], location=self.window)
        click_template(self.template['all'], location=self.window)
        click_template(self.template['x'], location=self.window)
        click_template(self.template['treasure_hunt'], location=self.window)

    def connection(self):
        click_template(self.template['ok'], location=self.window)
        pause(10)
        self.login()

def main():
    print(f'=====> The script to be used with 50% zoom')
    print(f'=====> Loaded "config.yaml"')

    # load image template
    pyautogui.PAUSE = conf['interval']
    # global template
    luna_img = load_template('luna_img/')
    bomb_img = load_template('bomb_img/')
    template = luna_img | bomb_img


    print(f'=====> Loaded template\n')
    print('=====> Program will start capturing screen within 5 sec\n')

    pause(5)

    num_bomb = len(position(template['bomb'], threshold=0.9))
    print('=====> Total Crypto Bomb Window :', num_bomb)
    bot_bomb = list(range(num_bomb))

    num_luna = len(position(template['luna']))
    print('=====> Total Luna Rush Window :', num_luna, '\n')
    bot_luna = list(range(num_luna))

    for i in bot_bomb:
        x, y, w, h = position(template['bomb'], threshold=0.9)[i]
        click(x + w / 2, y + h / 2)
        bot_name = 'BOMB_BOT_' + str(i + 1)
        bot_bomb[i] = bomb(bot_name, gw.getActiveWindow())

    for i in bot_luna:
        x, y, w, h = position(template['luna'])[i]
        click(x + w/2, y + h/2)
        bot_name = 'LUNA_BOT_' + str(i + 1)
        bot_luna[i] = luna(bot_name, gw.getActiveWindow())

    last = {'refresh': 0}
    login_timeout, resend_timeout, connection_timeout = 0, 0, 0

    while True:
        now = time.time()
        tnow = datetime.now().strftime('[%H:%M:%S]')

        if now - last['refresh'] > resend_timeout:
            print(f'{tnow} --------------------')

            # Crypto Bomb
            if num_bomb != 0:
                for i in bot_bomb:
                    print(f'{tnow} ----- {i.name}')
                    try:
                        if check_template(template['connect_wallet']):
                            print(f'{tnow} Connecting wallet...')
                            i.login()
                    except Exception as e:
                        print(f'{tnow} Login function error!!!')
                        print(f'{tnow} SYSTEM ===> {e}')

                    try:
                        if check_template(template['ok']):
                            print(f'{tnow} Connecting wallet...')
                            i.connection()
                    except Exception as e:
                        print(f'{tnow} Connection function error!!!')
                        print(f'{tnow} SYSTEM ===> {e}')

                    try:
                        if check_template(template['back2home']):
                            print(f'{tnow} Send heroes to work...')
                            i.resend()
                    except Exception as e:
                        print(f'{tnow} Send function error!!!')
                        print(f'{tnow} SYSTEM ===> {e}')

            # Luna Rush
            if num_luna != 0:
                for i in bot_luna:
                    print(f'{tnow} ----- {i.name}')
                    try:
                        if check_template(template['login']):
                            print(f'{tnow} Connecting wallet...')
                            i.login()
                    except Exception as e:
                        print(f'{tnow} Login function error!!!')
                        print(f'{tnow} SYSTEM ===> {e}')

                    try:
                        if check_template(template['boss_hunt_main']):
                            i.boss_hunt()

                        if check_template(template['warrior']):
                            print(f'{tnow} Send warrior to fight...')
                            i.reset()
                            i.play()
                    except Exception as e:
                        print(f'{tnow} Send function error!!!')
                        print(f'{tnow} SYSTEM ===> {e}')

            last['refresh'] = now
            resend_timeout = conf['refresh'] * 60 + random.randint(0, conf['random'] * 60)
            ntime = time.strftime("%M min %S sec", time.gmtime(resend_timeout))
            print(f'{tnow} --------------------')
            print(f'{tnow} Checking again in next {ntime}')

        pause(1)

if __name__ == '__main__':
    main()
