# Author: Tarek Rahman, Bangladesh

# builtins
import asyncio
from threading import Thread
import pathlib
import traceback
import time
import configparser
from datetime import datetime

# third-parties
import PySimpleGUI as sg

from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


current_dir = pathlib.Path(__file__).parent.resolve().as_posix()
config_file_path = current_dir + pathlib.os.sep + "trading_bot_configuration.ini"


async def main():
    telegram_session_file_path = (
        current_dir + pathlib.os.sep + "trading_bot_telegram_session"
    )
    if not pathlib.Path(config_file_path).exists():
        create_config()
    api_id, api_hash, phone_number = getConfig()
    client = Client(
        telegram_session_file_path,
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone_number,
    )
    async with client:
        channel_id = await get_channel_id(client)
        client.driver, client.windows = readyDriver()

        @client.on_message(filters.chat(channel_id) & filters.text)
        async def my_handler(client, message):
            signal_handler(client, message)

        Thread(target=simulateMouseEvent, args=[client.driver, client.windows]).start()
        print("The tool is ready and it's listening for signals............\n")
        await idle()


async def get_channel_id(client):
    data = {
        dialog.chat.title: {"chat_id": dialog.chat.id}
        async for dialog in client.get_dialogs()
        if dialog.chat.title and not dialog.chat.first_name
    }
    return data[getChannel(list(data.keys()))]["chat_id"]


def signal_handler(client, signal):
    now = str(datetime.now())
    print("\n**New signal is broadcasted")
    print(f"Signal sent at     : {signal.date}")
    print(f"Signal received at : {now}")
    print(signal)
    return 0
    message = signal.text.replace("`", "").strip().replace("\n", "")
    if "LONG" in message or "SHORT" in message:
        print("Signal Type: Relevent")
        if "ENTRY" in message and "STOP" in message:
            CMD = "LONG" if message.find("LONG") > 0 else "SHORT"
            print(f"Action to do : {CMD}")
            css_selector, indices = get_css_selector_for_trade(CMD, message)
            print("Indices name: ", indices)
            try:
                trade(
                    driver=client.driver,
                    trade_selector=css_selector,
                    window_handle=client.windows["opening_tab_handle"],
                )
            except Exception:
                print(traceback.format_exc())
                print("Attempt to open trade failed")
    elif "CLOSE TRADE ALERT" in message:
        print("Signal Type: Relevent")
        CMD = "CLOSE"
        print(f"Action to do : {CMD}")
        trade_name, indices = get_trade_name_for_closing(message)
        print("Indices name: ", indices)
        try:
            closeTrade(
                driver=client.driver,
                trade_name=trade_name,
                window_handle=client.windows["closing_tab_handle"],
            )
        except Exception:
            print(traceback.format_exc())
            print("Attempt to closing trade failed")
        client.driver.switch_to.window(client.windows["opening_tab_handle"])
    else:
        print("Signal Type: Irrelevent")
    print("Signal metadata --->\n", signal)


wall_street_sell_css = "#ticket-panel-17322 .sell-button"
wall_street_buy_css = "#ticket-panel-17322 .buy-button"

us_tech_100_sell_css = "#ticket-panel-20190 .sell-button"
us_tech_100_buy_css = "#ticket-panel-20190 .buy-button"

uk_100_sell_css = "#ticket-panel-16645 .sell-button"
uk_100_buy_css = "#ticket-panel-16645 .buy-button"

germany_40_sell_css = "#ticket-panel-17068 .sell-button"
germany_40_buy_css = "#ticket-panel-17068 .buy-button"


def getConfigFromUser():
    layout = [
        [sg.Text("API ID", size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Text("API Hash", size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Text("Phone", size=(15, 1)), sg.InputText("+44xxxxxxxxxx", size=(42, 1))],
        [sg.Submit("Save"), sg.Cancel()],
    ]
    window = sg.Window("Setup", layout, element_justification="c")
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values[0], values[1], values[2]


def getPass():
    layout = [
        [
            sg.Text("Password", size=(15, 1)),
            sg.InputText("", key="Password", password_char="*"),
        ],
        [sg.Submit("OK"), sg.Cancel()],
    ]
    window = sg.Window("Password", layout, element_justification="c")
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values["Password"]


def getAuthCode():
    layout = [
        [sg.Text("Code", size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Submit("Next"), sg.Cancel()],
    ]
    window = sg.Window("Phone Number Authentication", layout, element_justification="c")
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values[0]


def getChannel(channels: list):
    layout = [
        [sg.Text("Channel Name"), sg.Combo(channels, readonly=True)],
        [sg.Submit("OK"), sg.Cancel()],
    ]
    window = sg.Window(
        "Select Signal Provider Channel", layout, element_justification="c"
    )
    event, values = window.read()
    window.close()
    if event == "Cancel":
        exit()
    return values[0]


def create_config():
    api_id, api_hash, phone = getConfigFromUser()
    config = configparser.ConfigParser()
    config.add_section("API_Details")
    config.set("API_Details", "api_id", api_id)
    config.set("API_Details", "api_hash", api_hash)
    config.set("API_Details", "phone", phone)
    with open(config_file_path, "w") as configfile:
        config.write(configfile)


def getConfig():
    config_obj = configparser.ConfigParser()
    config_obj.read(config_file_path)
    return (
        config_obj["API_Details"]["api_id"],
        config_obj["API_Details"]["api_hash"],
        config_obj["API_Details"]["phone"],
    )


def readyDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        },
    )
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging", "enable-automation"]
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.maximize_window()
    driver.get("https://traders.td365.com/")
    sg.Popup(
        "Notice!",
        "After signing in open the trading tab. Then press OK.\nPS: The bot will automatically prepare the four trading window by itself.",
        keep_on_top=True,
    )
    while True:
        if len(driver.window_handles) != 1:
            sg.Popup(
                "Please close the other tab and keep only the trading tab",
                keep_on_top=True,
            )
        else:
            break

    opening_tab_handle = driver.window_handles[0]
    driver.switch_to.window(opening_tab_handle)
    driver.execute_script(f"window.open('{driver.current_url}');")
    driver.switch_to.window(opening_tab_handle)
    prepareTradeWindows(driver)
    return driver, {
        "opening_tab_handle": opening_tab_handle,
        "closing_tab_handle": driver.window_handles[1],
    }


def trade(driver, trade_selector, window_handle):
    driver.switch_to.window(
        window_handle
    ) if driver.current_window_handle != window_handle else None
    parentSelector = trade_selector.split(" ")
    backBtn = parentSelector[0] + " .btnBack"
    javascript = f"""
        function waitForElm(selector) {{
            return new Promise(resolve => {{
                if (document.querySelector(selector)) {{
                    return resolve(document.querySelector(selector));
                }}
                const observer = new MutationObserver(mutations => {{
                    if (document.querySelector(selector) && window.getComputedStyle(document.querySelector(`${{selector.split(' ')[0]}} .deal-ticket-holder.instance`).nextSibling, null).display=='block') {{
                        resolve(document.querySelector(selector));
                        observer.disconnect();
                    }}
                }});
                observer.observe(document.body, {{
                    childList: true,
                    subtree: true
                }});
            }});
        }};
        document.querySelector("{trade_selector}").click();
        waitForElm('{backBtn}').then((elm) => {{elm.click();}});
    """
    driver.execute_script(javascript)
    print(" Trade -- Opened ")


def closeTrade(driver, trade_name, window_handle):
    driver.switch_to.window(window_handle)
    stop_xpath = f'//div[@id="divCurrentPositions"]//div[text()="{trade_name}" and @class="marketName"]/ancestor::tr[1]//div[@class="closeIcon"]'
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, stop_xpath)))
    driver.find_element(By.XPATH, stop_xpath).click()
    submit_xpath = f'//p[@class="market-name" and text()="{trade_name}"]/ancestor::div[@class="trade-ticket"]//button[@class="btnSubmit"]'
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, submit_xpath))
    )
    driver.find_element(By.XPATH, submit_xpath).click()
    close_xpath = f'//p[@class="market-name" and text()="{trade_name}"]/ancestor::div[@class="trade-ticket"]//button[@class="btnClose"]'
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, close_xpath)))
    driver.find_element(By.XPATH, close_xpath).click()
    print(trade_name, " -- Closed")


def prepareTradeWindows(driver):
    wallstreet30Window = "document.querySelector('#div-buttonTrade-mq6647').click()"
    ustech100Window = "document.querySelector('#div-buttonTrade-mq16917').click()"
    germany40Window = "document.querySelector('#div-buttonTrade-mq6374').click()"
    uk100Window = "document.querySelector('#div-buttonTrade-mq5945').click()"

    wallstreet30Style = "document.querySelector('#ticket-panel-17322_c').style='visibility: visible; z-index: 300; left: 10px; top: 10px;'"
    ustech100Style = "document.querySelector('#ticket-panel-20190_c').style='visibility: visible; z-index: 302; left: 342px; top: 10px;'"
    germany40Style = "document.querySelector('#ticket-panel-17068_c').style='visibility: visible; z-index: 304; left: 644px; top: 10px;'"
    uk100Style = "document.querySelector('#ticket-panel-16645_c').style='visibility: visible; z-index: 306; left: 945px; top: 10px;'"
    driver.execute_script(wallstreet30Window)
    driver.execute_script(ustech100Window)
    driver.execute_script(germany40Window)
    driver.execute_script(uk100Window)
    driver.execute_script(wallstreet30Style)
    driver.execute_script(ustech100Style)
    driver.execute_script(germany40Style)
    driver.execute_script(uk100Style)


def simulateMouseEvent(driver, windows):
    time.sleep(100)
    while True:
        if driver.current_window_handle != windows["closing_tab_handle"]:
            driver.execute_script(
                "document.querySelector('#lblAccountSummary').click()"
            )
            time.sleep(40)
        if driver.current_window_handle != windows["closing_tab_handle"]:
            driver.execute_script(
                "document.querySelector('#lblTransactionHistory').click()"
            )
            time.sleep(40)


def css_for_sell(telegramSignal: str):
    if "FTSE" in telegramSignal:
        return uk_100_sell_css, "FTSE INDEX"
    elif "GERMAN" in telegramSignal:
        return germany_40_sell_css, "DAX INDEX"
    elif "NASDAQ" in telegramSignal:
        return us_tech_100_sell_css, "NASDAQ INDEX"
    elif "JONES" in telegramSignal:
        return wall_street_sell_css, "DOW INDEX"


def css_for_buy(telegramSignal: str):
    if "FTSE" in telegramSignal:
        return uk_100_buy_css, "FTSE INDEX"
    elif "GERMAN" in telegramSignal:
        return germany_40_buy_css, "DAX INDEX"
    elif "NASDAQ" in telegramSignal:
        return us_tech_100_buy_css, "NASDAQ INDEX"
    elif "JONES" in telegramSignal:
        return wall_street_buy_css, "DOW INDEX"


def get_trade_name_for_closing(telegramSignal: str):
    if "FTSE INDEX" in telegramSignal:
        return "UK 100 - Rolling Cash", "FTSE INDEX"
    elif "DAX INDEX" in telegramSignal:
        return "Germany 40 - Rolling Cash", "DAX INDEX"
    elif "NASDAQ INDEX" in telegramSignal:
        return "US Tech 100 - Rolling Cash", "NASDAQ INDEX"
    elif "DOW INDEX" in telegramSignal:
        return "Wall Street 30 - Rolling Cash", "DOW INDEX"


def get_css_selector_for_trade(CMD: str, telegramSignal: str):
    if CMD == "SHORT":
        return css_for_sell(telegramSignal)
    elif CMD == "LONG":
        return css_for_buy(telegramSignal)
    elif CMD == "CLOSE":
        return get_trade_name_for_closing(telegramSignal)


if __name__ == "__main__":
    asyncio.run(main())
