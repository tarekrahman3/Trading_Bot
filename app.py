
# builtins
from datetime import datetime
import sys
import traceback
import time
import re
import os
import logging
import concurrent.futures
from multiprocessing import Process

# third-party
from telethon.sync import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# core-bot
from src.sel import TradeOpeningLatencyCounter , readyDriver, trade, closeTrade
from src.ui import getAuthCode, getChannel, getPass, TaskStopper
from src.config import create_config, getConfig

#preparing logger
logging.basicConfig(
    filename="application_logger.log",
    level=logging.INFO,
    format="%(asctime)s : %(levelname)s : %(name)s : %(message)s",
)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1) 

def info(msg):
    executor.submit(logging.info, msg)


wall_street_sell_css = "#ticket-panel-17322 .spnSellPrice"
wall_street_buy_css = "#ticket-panel-17322 .spnBuyPrice"

us_tech_100_sell_css = '#ticket-panel-20190 .spnSellPrice'
us_tech_100_buy_css = '#ticket-panel-20190 .spnBuyPrice'

uk_100_sell_css = '#ticket-panel-16645 .spnSellPrice'
uk_100_buy_css = '#ticket-panel-16645 .spnBuyPrice'

germany_40_sell_css = '#ticket-panel-17068 .spnSellPrice'
germany_40_buy_css = '#ticket-panel-17068 .spnBuyPrice'


def css_for_sell(telegramSignal : str):
    if "FTSE" in telegramSignal :
        return uk_100_sell_css
    elif "GERMAN" in telegramSignal :
        return germany_40_sell_css
    elif "NASDAQ" in telegramSignal :
        return us_tech_100_sell_css
    elif "JONES" in telegramSignal :
        return wall_street_sell_css


def css_for_buy(telegramSignal : str):
    if "FTSE" in telegramSignal :
        return uk_100_buy_css
    elif "GERMAN" in telegramSignal :
        return germany_40_buy_css
    elif "NASDAQ" in telegramSignal :
        return us_tech_100_buy_css
    elif "JONES" in telegramSignal :
        return wall_street_buy_css    

def get_css_selector_for_trade(CMD:str, telegramSignal : str):
    if CMD=="SHORT":
        return css_for_sell(telegramSignal)
    elif CMD=="LONG":
        return css_for_buy(telegramSignal)


def getEntity(client):
    data = {}
    [data.update({dialog.name: {"thread_id": dialog.id}}) for dialog in client.iter_dialogs() if dialog.is_channel and dialog.name != ""]
    user_input = getChannel(list(data.keys()))
    return client.get_entity(data[user_input]["thread_id"])

if not os.path.exists("config.ini"):
    create_config()

api_id, api_hash, phone_number = getConfig()

if os.path.exists("mysession.session"):
    client = TelegramClient("mysession", int(api_id), api_hash)
else:
    client = TelegramClient("mysession", int(api_id), api_hash)
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone_number)
        client.sign_in(phone_number)
        try:
            client.sign_in(code=int(getAuthCode()))
        except SessionPasswordNeededError:
            client.sign_in(password=getPass())
    client.disconnect()
    client = TelegramClient("mysession", int(api_id), api_hash)


client.connect()


entity = getEntity(client)

@client.on(events.NewMessage(entity))
async def my_event_handler(event):
    latencyCounter = TradeOpeningLatencyCounter()
    signal_received = datetime.now()
    print(f'{str(signal_received)} **New signal is broadcasted')
    print(f"Message initiated at (UTC): {event.message.date}")
    message = event.text.replace("`", "").strip().replace('\n','')
    print(f"Full body of the received signal: {message}")
    if "LONG" in message or "SHORT" in message:
        print('Signal Type: [Relevent] [SELL/BUY]')
        if "ENTRY" in message and "STOP" in message:
            CMD = "LONG" if message.find("LONG")>0 else "SHORT"
            print(f'Action to do : {CMD}')
            css_selector = get_css_selector_for_trade(CMD, message)
            try:
                await trade( latencyCounter=latencyCounter, driver=driver, css_selector=css_selector )
            except Exception:
                print(traceback.format_exc())
            print(f"{str(datetime.now())} - Trade Button CLick Complete \n")
            #print(f"difference between signal recieve and trade button click: {(datetime.fromtimestamp(latencyCounter.button_clicked_timestamp)-signal_received).microseconds/1000.0} seconds\n\n")
    elif "CLOSE TRADE ALERT" in message:
        signal_name = re.search("CLOSING (.+) trade now", message).group(1)
        if signal_name == "FTSE INDEX":
            trade_name = "UK 100 - Rolling Cash"
        elif signal_name == "DAX INDEX":
            trade_name = "Germany 40 - Rolling Cash"
        elif signal_name == "NASDAQ INDEX":
            trade_name = "US Tech 100 - Rolling Cash"
        elif signal_name == "DOW INDEX":
            trade_name = "Wall Street 30 - Rolling Cash"
        await closeTrade(driver, trade_name, windows["closing_tab_handle"])
        driver.switch_to.window(windows["opening_tab_handle"])


client.disconnect()


print("Starting up the browser and setting up one click trade....")
driver, windows = readyDriver()

client.start()
print("client is listening for commands..................\n\n")


#pid = os.getpid()
#p = Process(target=TaskStopper, args=(pid, driver))
#p.start()


client.run_until_disconnected()
