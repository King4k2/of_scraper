import asyncio
import config
import os
import selenium.common.exceptions
from telethon import TelegramClient
from telethon import types
from telethon.tl.types import PeerChannel
import time
import re
import openpyxl
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
import pathlib
import pickle


async def download_img(msg, f_loc):
    await client.download_media(message=msg, file=f_loc)
    print("downloaded")
    return 1


class BadInternetConnectionException(Exception):
    pass


def check_for_el(driver, value: str, method: str):
    x = 0
    if method.lower() == "id":
        method = By.ID
    elif method.lower() == "xpath":
        method = By.XPATH
    while x < 20:
        try:
            el = driver.find_element(method, value)
            return el
        except selenium.common.exceptions.NoSuchElementException:
            x = x + 1
            time.sleep(1)
            continue
    raise BadInternetConnectionException


def upload_stories(driver, people_tag, img_dir):
    el = check_for_el(driver=driver, value="add-story-btn", method="id")
    el.click()
    time.sleep(1)

    input_el = check_for_el(driver=driver, value="file_upload_input", method="id")
    input_el.send_keys(str(pathlib.Path(img_dir).absolute()))

    el_btn = check_for_el(driver=driver, value='//*[@id="content"]/div[2]/section/div[1]/div[2]/button[1]', method="xpath")
    el_btn.click()

    el_btn = check_for_el(driver=driver, method="xpath",
                          value='//*[@id="photo-editor-add-asset___BV_modal_body_"]/div/div[2]/div/div[6]/button')
    el_btn.click()

    el_textarea = check_for_el(driver=driver, method="xpath",
                               value='//*[@id="content"]/div[2]/section/div[1]/section/div[3]/form/div/textarea')
    el_textarea.send_keys(people_tag)

    el_btn = check_for_el(driver=driver, method="xpath",
                          value='//*[@id="content"]/div[2]/section/div[1]/section/div[2]/div[2]/button')
    el_btn.click()

    el_publish = check_for_el(driver=driver, method="xpath", value='//*[@id="content"]/div[2]/section/div[3]/button')
    el_publish.click()
    screenshot_dir = f"screenshots/{people_tag}_screenshot.png"
    driver.save_screenshot(screenshot_dir)
    for s in range(0, 21):
        try:
            el_publish.get_attribute(name="disabled")
            time.sleep(1)
        except selenium.common.exceptions.NoSuchElementException:
            return screenshot_dir


async def of_login(account_name: str, people_tags_list: list, img_dir_list: list, group_entity):
    options = ChromeOptions()
    service = ChromeService(executable_path='chromedriver-win64/chromedriver.exe')
    # disable webdriver mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    options.add_argument(r'user-data-dir=C:\Users\King\AppData\Local\Google\Chrome\User Data')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--profile-directory=Profile 1')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")

    driver = WebDriver(options=options, service=service)
    try:
        driver.get(url="https://onlyfans.com/")

        # Load cookie
        for cookie in pickle.load(open(f'{account_name}_OFS_cookies.pkl', 'rb')):
            driver.add_cookie(cookie)
        driver.refresh()
    except Exception as err:
        print(err)
    x = 0
    while x < 2:
        try:
            # Uploading stories
            uploaded_files = []
            screenshot_dir_list = []
            for n, img_dir, people_tag in zip(range(0, 5), img_dir_list, people_tags_list):
                screenshot_dir = upload_stories(driver=driver, people_tag=people_tag, img_dir=img_dir)
                screenshot_dir_list.append(screenshot_dir)
                # Sending screenshots to chat
                uploaded_files.append(await client.upload_file(screenshot_dir))
            await client.send_file(entity=group_entity, file=uploaded_files)
            for s_dir, i_dir in zip(screenshot_dir_list, img_dir_list):
                if os.path.exists(s_dir):
                    os.remove(s_dir)
                if os.path.exists(i_dir):
                    os.remove(i_dir)
        except BadInternetConnectionException:
            if x != 1:
                continue
            else:
                print(f'Error: bad Internet connection or your cookies is old. '
                      f'If it occurs again try to relogin in account with name "{account_name}"')
                return 1
        finally:
            driver.quit()


async def check_for_posts():
    try:

        async with client:
            msg_pattern = re.compile(r'@\w*\b')
            wb = openpyxl.load_workbook("OnlyFansExcel.xlsx")
            sh = wb["Лист1"]
            posts_list = [] # 0-channel_id int, 1-msg_id, 2-counter int, 3-img_dir_list list, 4-people_tags_list list, 5-account_name str
            for c in range(2, sh.max_row+1):
                group_link = sh[f"A{c}"].value
                account_name = sh[f"B{c}"].value
                if sh[f"A{c}"] is None or sh[f"B{c}"] is None:
                    break
                group = await client.get_entity(group_link)  # t.me/onlyfans5k
                msg_list = await client.get_messages(group, limit=20)
                for msg in msg_list:
                    if msg_pattern.match(msg.text) and type(msg.media) is types.MessageMediaPhoto:
                        counter = 0
                        img_dir_list = []
                        people_tags_list = []
                        posts_list.append([int(msg.peer_id.channel_id), msg.id, counter, img_dir_list, people_tags_list])
                        break
            process_list = []
            me_entity = await client.get_entity("t.me/AstronomOOS")

            while inp_comm[0] != "e":
                for group in posts_list:
                    group_entity = await client.get_entity(PeerChannel(group[0]))  # t.me/onlyfans5k
                    msg_list = await client.get_messages(group_entity, limit=30)
                    for msg in msg_list:
                        if not msg_pattern.match(msg.message):
                            continue
                        if msg.id == group[1]:
                            break
                        print(msg)
                        msg_reply = msg.reply_to
                        print(type(msg.media))
                        if type(msg.media) is types.MessageMediaPhoto:
                            f_dir = f"imgs/photo_{msg.id}_{msg.peer_id.channel_id}"
                            await download_img(msg=msg, f_loc=f_dir)
                            group[4].append(msg.message)
                            group[3].append(f_dir)
                            print("2")
                            group[2] = group[2] + 1
                            group[1] = msg.id
                        print(msg.date, msg.text)
                        if group[2] == 5:
                            img_dir_list = group[3].copy()
                            people_tags_list = group[4].copy()
                            await of_login(account_name=group[5], people_tags_list=people_tags_list,
                                           img_dir_list=img_dir_list, group_entity=me_entity)
                            group[4] = []
                            group[2] = 0
                            group[1] = msg.id
                            group[3] = []
                            print("stories")
                print("sleep-time")
                time.sleep(20)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # API ID (получается при регистрации приложения на my.telegram.org)
    # API Hash (оттуда же)
    client = TelegramClient('OnlyFansBot', int(config.api_id), config.api_hash)
    client.start()
    inp_comm = [""]
    client.loop.run_until_complete(check_for_posts())
