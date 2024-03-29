"""
hataori host
License: MIT License (http://www.opensource.org/licenses/mit-license.php)
 (c) 2023 Fukasawa Takashi
"""

import json
import os
import sys
import time
import struct
import datetime
import threading

sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + '/common')
import w32api
import file_io
import app

class thread(threading.Thread):
    __function = None

    def __init__(self, function = None):
        threading.Thread.__init__(self)
        self.set_function(function)
        self.__e = threading.Event()

    def set_function(self, function):
        self.__function = function

    def run(self):
        if self.__function != None:
            return self.__function()

    def start(self):
        super().start()

def recv_message():
    while True:
        leng = sys.stdin.buffer.read(4)
        if not leng:
            #raise RuntimeError('The message length of Native Messaging is zero.')
            return None

        try:
            message_leng = struct.unpack('=I', leng)[0]
            message = sys.stdin.buffer.read(message_leng).decode("utf-8")
            return json.loads(message)
        except Exception as e:
            raise RuntimeError('Failed to recv Native Messaging.')

def send_message(message):
    try:
        message_text = json.dumps(message).encode("utf-8")
        content = struct.pack(str(len(message_text))+"s",message_text)
        leng = struct.pack('=I', len(message_text))

        sys.stdout.buffer.write(leng)
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.flush()
        return True
    except Exception as e:
        return False

    return None

def is_float(text):
    try:
        float(text)
        return True
    except Exception:
        return False

def __lock_prevention():
    global stop_lock_prevention
    while True:
        cursor_pos = w32api.get_mouse_pos()
        w32api.mouse_move(cursor_pos['x'], cursor_pos['y'])
        time.sleep(10)
        if stop_lock_prevention:
            break

def __browser_process_watch():
    while True:
        time.sleep(0.5)
        exists = False
        hwnds = w32api.find_windows_by_class('Chrome_WidgetWin_1')
        for hwnd in hwnds:
            title = w32api.get_window_title(hwnd)
            browser_title = ' - ' + 'Google Chrome'
            pos = title.rfind(browser_title)
            if (len(title) - len(browser_title)) == pos:
                exists = True
                break

        if not exists:
            os._exit(0)

def check_response(message):
    for key in message.keys():
        if (key != 'ret') and (key != 'err'):
            return False

    if (not 'ret' in message) or (not 'err' in message):
        return False

    return True

def check_wait_response(message):
    for key in message.keys():
        if (key != 'ret') and (key != 'err'):
            return False

    if (not 'ret' in message) or (not 'err' in message):
        return False

    if not message['ret'] == 'wait':
        return False

    return True

def check_request(message):
    for key in message.keys():
        if (key != 'gp') and (key != 'fc') and (key != 'p'):
            return False

    if (not 'gp' in message) or (not 'fc' in message):
        return False
    elif (not type(message['gp']) is str) or (not type(message['fc']) is str):
        return False

    if 'p' in message:
        for key in message['p'].keys():
            if (key != 'v1') and (key != 'v2') and (key != 'v3') and (key != 'v4') and (key != 'v5'):
                return False

    return True

def assign(message):
    ret = None

    if (message['gp'] == 'host') and (message['fc'] == 'action'):
        if message['p']['v1'] == 'open':
            app_path = message['p']['v3']
            url_string = message['p']['v2']
            app.open_app(app_path + ' --new-window --kiosk-printing ' + url_string)
            ret = True
        elif message['p']['v1'] == 'set_clip':
            ret = w32api.clip(message['p']['v2'])
        elif message['p']['v1'] == 'send_text':
            w32api.send_text(message['p']['v2'])
            ret = True
        elif message['p']['v1'] == 'send_key':
            ret = w32api.send_keys(message['p']['v2'])
        elif message['p']['v1'] == 'exists':
            ret = True
        else:
            ret = False
    elif (message['gp'] == 'host') and (message['fc'] == 'window'):
        if message['p']['v1'] == 'get_window_len':
            hwnds = w32api.find_windows_by_title(message['p']['v2'])
            ret = len(hwnds)
        elif message['p']['v1'] == 'get_active_window_title':
            ret = w32api.get_window_title(w32api.get_active_window())
        elif message['p']['v1'] == 'active_by_title':
            hwnds = w32api.find_windows_by_title(message['p']['v2'])
            pos = message['p']['v3']
            if len(hwnds) < 1:
                ret = False
            elif len(hwnds) > pos:
                time.sleep(0.1)
                #w32api.set_show_window(hwnds[pos], w32api.SW_SHOWMAXIMIZED)
                time.sleep(0.1)
                w32api.set_active_window2(hwnds[pos])
                w32api.set_active_window(hwnds[pos])
                time.sleep(0.1)
                w32api.set_window_pos(hwnds[pos], w32api.HWND_TOPMOST, 0, 0, 0, 0, w32api.SWP_NOMOVE | w32api.SWP_NOSIZE)
                w32api.set_window_pos(hwnds[pos], w32api.HWND_NOTOPMOST, 0, 0, 0, 0, w32api.SWP_SHOWWINDOW | w32api.SWP_NOMOVE | w32api.SWP_NOSIZE)
                time.sleep(0.1)
                ret = True
        else:
            ret = False

    return ret

if __name__ == '__main__':
    request_file = 'req'
    response_file = 'res'
    directory_path = os.path.dirname(os.path.abspath(sys.argv[0])) + '/../../file'

    browser_process_watch = thread()
    browser_process_watch.set_function(__browser_process_watch)
    browser_process_watch.start()

    stop_lock_prevention = False
    lock_prevention = thread()
    lock_prevention.set_function(__lock_prevention)
    lock_prevention.start()

    while True:
        message = recv_message()
        if message is None:
            os._exit(0)

        if (not check_wait_response(message)) and (check_response(message)):
            file_io.set_dir_path(directory_path)
            file_io.set_file_name(response_file)
            file_io.set_data(message)

        file_io.set_timeout_sec(2 * 60)
        file_io.set_dir_path(directory_path)
        file_io.set_file_name(request_file)

        message = {'gp': 'system', 'fc': 'nothing'}

        if file_io.start():
            message = file_io.get_data()
            assign_ret = assign(message)
            if not assign_ret is None:
                file_io.set_dir_path(directory_path)
                file_io.set_file_name(response_file)
                file_io.set_data({'ret': assign_ret, 'err': None})
                message = {'gp': 'system', 'fc': 'nothing'}

        send_message(message)
        message = recv_message()
