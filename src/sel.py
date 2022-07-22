from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import PySimpleGUI as sg
import logging,concurrent



class TradeOpeningLatencyCounter:
    """docstring for TimeCounter"""
    def __init__(self):
        self.signal_recieved_timestamp = time.time()
    def record_trade_button_click(self):
        self.button_clicked_timestamp = time.time()
    def record_trade_request_completion_time(self):
        self.trade_request_completion_time = time.time()
    def record_back_button_clickcing_time(self):
        self.back_button_clicking_time=time.time()
    def record_starting_time_to_wait_for_the_back_button_to_appear(self):
        self.started_to_wait_for_the_back_button_to_appear = time.time()
    def record_back_button_appearing_time(self):
        self.back_button_appearing_time = time.time()
    def record_returning_time_from_trade_voucher(self):
        self.returning_time_from_trade_voucher = time.time()
    def calculate(self):
        ...

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1) 

def info(msg):
    executor.submit(logging.info, msg)

def readyDriver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get("https://clients.tradedirect365.com/#/auth/login")
    sg.Popup(
        "after signing in Prepare the four trading window such as they don't overlap one another. Then press OK"
    )
    if len(driver.window_handles)!=1:
        sg.Popup(
            "Please close the other tab and keep only the tab you managed"
        )
    print(
        "The bot has been deployed successfully. You can now start sending trading commands....\n"
    )
    opening_tab_handle = driver.window_handles[0]
    driver.switch_to.window(opening_tab_handle)
    driver.execute_script(f"window.open('{driver.current_url}');")
    driver.switch_to.window(opening_tab_handle)
    return driver, {
        "opening_tab_handle": opening_tab_handle,
        "closing_tab_handle": driver.window_handles[1],
    }


async def trade(latencyCounter, driver, css_selector):
    javascript = f"""
        function waitForElm(selector) {{
            return new Promise(resolve => {{
                if (document.querySelector(selector)) {{
                    return resolve(document.querySelector(selector));
                }}

                const observer = new MutationObserver(mutations => {{
                    if (document.querySelector(selector)) {{
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
        document.querySelector("{css_selector}").click();
        waitForElm('{css_selector.split(" ")[0]} .btnBack').then((elm) => {{elm.click();}});
    """
    print(f'{str(datetime.now())} attempting to click trade Button')
    #latencyCounter.record_trade_button_click()
    #driver.execute_script(f'document.querySelector("{css_selector}").click()')
    #print(f'{str(datetime.now())} ** Clicked the trade Button')
    #print(f"{str(datetime.now())} Waiting for the trading request to complete")
    #latencyCounter.record_trade_request_completion_time()
    #print(f"{str(datetime.now())} **Trading request completed")
    #latencyCounter.record_starting_time_to_wait_for_the_back_button_to_appear()
    #print(f"{str(datetime.now())} Waiting for the back button to render")
    driver.execute_script(javascript)
    #latencyCounter.record_returning_time_from_trade_voucher()
    #print(f"{str(datetime.now())} -----------Clicked the back button")

def closeTrade(driver, trade_name, window_handle):
    driver.switch_to.window(window_handle)
    stop_xpath = f'//div[@class="yui-dt-liner"]/div[not(@style="display: none;")]//div[text()="{trade_name}" and @class="marketName"]/ancestor::tr[1]//*[@class="closeIcon"]'
    driver.find_element(By.XPATH, stop_xpath).click()
    submit_xpath = f'//p[@class="market-name" and text()="{trade_name}"]/ancestor::div[@class="trade-ticket"]//button[@class="btnSubmit"]'
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,submit_xpath)))
    driver.find_element(By.XPATH, submit_xpath).click()
    close_xpath = f'//p[@class="market-name" and text()="{trade_name}"]/ancestor::div[@class="trade-ticket"]//button[@class="btnClose"]'
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,close_xpath)))
    driver.find_element(By.XPATH, close_xpath).click()