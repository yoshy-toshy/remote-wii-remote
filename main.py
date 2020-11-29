# -*- coding: utf-8 -*-

from flask import Flask, render_template, request
import RPi.GPIO as GPIO
import urllib.request
import signal
import time
import os
import json
import sys
import subprocess

NGROK_PATH = os.environ['NGROK_PATH']
SPREADSHEET_URL = os.environ['SPREADSHEET_URL']

# ピン設定
PINS = {}
PINS["A"] = 21
PINS["B"] = 20
PINS["u"] = 16
PINS["r"] = 12
PINS["d"] = 26
PINS["l"] = 19
PINS["+"] = 13
PINS["-"] = 6

app = Flask(__name__)
ngrok_process = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/push", methods=["POST"])
def push():
    if "POST" == request.method:
        button_name = request.form["button_name"]
        pin = PINS[button_name]
        GPIO.output(pin, True)
        time.sleep(0.1)
        GPIO.output(pin, False)
    return ""

@app.route("/shutdown")
def shutdown():
    GPIO.cleanup()
    os.killpg(os.getpgid(ngrok_process.pid), signal.SIGTERM)
    sys.exit()

def start_ngrok():
    global ngrok_process
    ngrok_process = subprocess.Popen([NGROK_PATH,'http','5000'], stdout=subprocess.PIPE)
    time.sleep(3)
    responce = urllib.request.urlopen("http://localhost:4040/api/tunnels").read()
    responce_json = json.loads(responce)
    url = responce_json['tunnels'][0]['public_url']
    send_url(url)

def send_url(url):
    data = {"url" : url};
    headers = {"Content-Type" : "application/json; charset=UTF-8"};
    request = urllib.request.Request(SPREADSHEET_URL, json.dumps(data).encode(), headers)
    urllib.request.urlopen(request)

def sigint_handler(signal, frame):
    shutdown()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    start_ngrok()
    GPIO.setmode(GPIO.BCM)
    for button_name in PINS:
        GPIO.setup(PINS[button_name], GPIO.OUT)
    app.run("0.0.0.0")
