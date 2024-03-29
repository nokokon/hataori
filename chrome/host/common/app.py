"""
hataori app
License: MIT License (http://www.opensource.org/licenses/mit-license.php)
 (c) 2023 Fukasawa Takashi

Note: Open an application, execute a command.
"""

import subprocess

def open_app(path):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 5|3
        proc = subprocess.Popen(path.replace('\\', '/'), startupinfo=startupinfo)
    except Exception as error:
        return False
    return True

def run_command(command, wait = False):
    if wait:
        proc = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE)
        return proc.stdout
    if not wait:
        subprocess.Popen(command, shell = True)
        return None

if __name__ == '__main__':
    print('Please import and use it.')
    exit()
