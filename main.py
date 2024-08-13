import os
import sys
import json
import time
import requests
import websocket
from threading import Thread
from flask import Flask, request

app = Flask(__name__)

status = "online"  # online/dnd/idle

GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SELF_MUTE = os.getenv("SELF_MUTE")
SELF_DEAF = os.getenv("SELF_DEAF")

usertoken = os.getenv("TOKEN")
if not usertoken:
    print("[ERROR] Please add a token inside Secrets.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

validate = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

# Global WebSocket variable
ws = None

def joiner(token, status):
    global ws
    if ws is None or not ws.connected:
        ws = websocket.WebSocket()
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        start = json.loads(ws.recv())
        heartbeat = start['d']['heartbeat_interval']
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 10",
                    "$browser": "Google Chrome",
                    "$device": "Windows"
                },
                "presence": {
                    "status": status,
                    "afk": False
                }
            },
            "s": None,
            "t": None
        }
        ws.send(json.dumps(auth))
        time.sleep(heartbeat / 1000)
        ws.send(json.dumps({"op": 1, "d": None}))

def connect_vc():
    global ws
    vc = {
        "op": 4,
        "d": {
            "guild_id": GUILD_ID,
            "channel_id": CHANNEL_ID,
            "self_mute": SELF_MUTE,
            "self_deaf": SELF_DEAF
        }
    }
    if ws and ws.connected:
        ws.send(json.dumps(vc))

def disconnect_vc():
    global ws
    vc = {
        "op": 4,
        "d": {
            "guild_id": GUILD_ID,
            "channel_id": None,  # Set channel_id to None to disconnect
            "self_mute": SELF_MUTE,
            "self_deaf": SELF_DEAF
        }
    }
    if ws and ws.connected:
        ws.send(json.dumps(vc))
        ws.close()

@app.route('/connect', methods=['POST'])
def connect():
    connect_vc()
    return "Connected to VC", 200

@app.route('/disconnect', methods=['POST'])
def disconnect():
    disconnect_vc()
    return "Disconnected from VC", 200

def run_server():
    app.run(host="0.0.0.0", port=8080)

def run_joiner():
    os.system("clear")
    print(f"Logged in as {username}#{discriminator} ({userid}).")
    joiner(usertoken, status)
    while True:
        time.sleep(30)

if __name__ == "__main__":
    Thread(target=run_server).start()  # Start the Flask server in a separate thread
    keep_alive()
    run_joiner()
