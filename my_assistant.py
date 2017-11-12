#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

The Google Assistant Library can be installed with:
    env/bin/pip install google-assistant-library==0.0.2

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import subprocess
import sys

import aiy.assistant.auth_helpers
import aiy.audio
import aiy.voicehat
from google.assistant.library import Assistant
from google.assistant.library.event import EventType

from datetime import datetime, time

radio=False

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)

def in_between(now, start,end):
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now <end

def power_off_pi():
    aiy.audio.say('Good bye!')
    subprocess.call('sudo shutdown now', shell=True)

def test_message():
    aiy.audio.say('This is a test message')

def reboot_pi():
    aiy.audio.say('See you in a bit!')
    subprocess.call('sudo reboot', shell=True)


def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))

def classic_fm():
    subprocess.call('mpc clear', shell=True)
    subprocess.call('mpc add http://media-ice.musicradio.com/ClassicFMMP3', shell=True)
    subprocess.call('mpc play', shell=True)

def news():
    subprocess.call('mpc clear', shell=True)
    subprocess.call('mpc add http://media-ice.musicradio.com/LBCUKMP3Low', shell=True)
    subprocess.call('mpc play', shell=True)
    
def radio_off():
    subprocess.call('mpc clear', shell=True)
    subprocess.call('mpc stop', shell=True)
    

def process_event(assistant, event):
    status_ui = aiy.voicehat.get_status_ui()
    if event.type == EventType.ON_START_FINISHED:
        if in_between(datetime.now().time(),time(22),time(6)): 
            status_ui.status('off')
        else:
            status_ui.status('ready')
        if sys.stdout.isatty():
            print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        status_ui.status('listening')
        print ("Started a conversation so I will switch off the radio")
        check_radio=subprocess.check_output("mpc status", shell=True)
        if "playing" in str(check_radio):
            global radio
            radio = True
            print (radio)
            print ("The radio was playing")
        else:
            global radio
            radio = False
            print ("The radio wasn't playing")
        subprocess.call('mpc stop', shell=True)

    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        print('You said:', event.args['text'])
        text = event.args['text'].lower()
        if text == 'sleep':
            assistant.stop_conversation()
            power_off_pi()
        if text == 'check audio':
            assistant.stop_conversation()
            test_message()
        elif text == 'reboot':
            assistant.stop_conversation()
            reboot_pi()
        elif text == 'ip address':
            assistant.stop_conversation()
            say_ip()
        elif text == 'my radio':
            assistant.stop_conversation()
            classic_fm()
        elif text == 'stop my radio':
            assistant.stop_conversation()
            radio_off()
        elif text == 'my news':
            assistant.stop_conversation()
            news()

    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')
        

    elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED:
        print ("Conversation has ended - starting listening again")
        print (radio)
        if radio == True:
            print ("The radio had been on before")
            subprocess.call('mpc play', shell=True)
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)

def _on_button_pressed():
    print ("button pressed")
    subprocess.call('mpc stop', shell=True)
    radio=True
    
    

def main():
    radio = False
    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        aiy.voicehat.get_button().on_press(_on_button_pressed)
        for event in assistant.start():
                process_event(assistant, event)


if __name__ == '__main__':
    main()
