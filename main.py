import selenium.common.exceptions
from telethon import TelegramClient
import config
from telethon import types
from telethon.tl.types import PeerChannel
import time
import re
import openpyxl
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import json
import pathlib


async def download_img(msg, f_loc):
    await client.download_media(message=msg, file=f_loc)
    print("downloaded")
    return 1


def check_for_el_by_xpath(driver, value: str):
    x = 0
    while x < 40:
        try:
            el = driver.find_element(By.XPATH, value)
            return el
        except selenium.common.exceptions.NoSuchElementException:
            if x == 39:
                return 1
            time.sleep(1)
            continue
        finally:
            x = x + 1


def check_for_el_by_id(driver, value: str):
    x = 0
    while x < 40:
        try:
            el = driver.find_element(By.ID, value)
            return el
        except selenium.common.exceptions.NoSuchElementException:
            if x == 39:
                return 1
            time.sleep(1)
            continue
        finally:
            x = x + 1



def upload_stories_process(driver, people_tag):
    el = check_for_el_by_id(driver=driver, value="add-story-btn")
    if type(el) is int:
        return "connection xueta"
    el = driver.find_element(By.ID, "add-story-btn")
    el.click()
    time.sleep(1)

    input_el = check_for_el_by_id(driver=driver, value="file_upload_input")
    if type(input_el) is int:
        return 1
    input_el.send_keys(str(pathlib.Path("imgs/photo_393211_1646485453.jpg").absolute()))

    el_btn = check_for_el_by_xpath(driver=driver, value='//*[@id="content"]/div[2]/section/div[1]/div[2]/button[1]')
    if type(el_btn) is int:
        return 1
    el_btn.click()

    el_btn = check_for_el_by_xpath(driver=driver,
                                   value='//*[@id="photo-editor-add-asset___BV_modal_body_"]/div/div[2]/div/div[6]/button')
    if type(el_btn) is int:
        return 1
    el_btn.click()

    el_textarea = check_for_el_by_xpath(driver=driver,
                                        value='//*[@id="content"]/div[2]/section/div[1]/section/div[3]/form/div/textarea')
    if type(el_textarea) is int:
        return 1
    el_textarea.send_keys(people_tag)

    el_btn = check_for_el_by_xpath(driver=driver,
                                   value='//*[@id="content"]/div[2]/section/div[1]/section/div[2]/div[2]/button')
    if type(el_btn) is int:
        return 1
    el_btn.click()


def upload_stories(ofs_data_dict: dict, account_name: str, people_tag: str):
    options_ = webdriver.ChromeOptions()
    # disable webdriver mode
    options_.add_argument("start-maximized")
    options_.add_experimental_option("excludeSwitches", ["enable-automation"])
    options_.add_argument("--disable-blink-features=AutomationControlled")

    options_.add_argument(f"user-agent={ofs_data_dict.get(account_name)[0]}")
    options_.add_argument(f"accept-language={ofs_data_dict.get(account_name)[1]}")

    driver = webdriver.Chrome(options=options_)
    driver.get(url="https://onlyfans.com/")
    # --------------------------- ЗДЕСЬ ДОЛЖНА БЫТЬ АВТОРИЗАЦИЯ

    # ----------------------------
    inp = input()
    for counter_ in range(0, 1):
        upload_stories_process(driver=driver, people_tag=people_tag)
    time.sleep(5)
    driver.quit()
    # time.sleep(1000)
    # __cf_bm _cfuvid fp


async def check_for_posts():
    try:
        ofs_data_wb = openpyxl.load_workbook("OnlyFansConfig.xlsx")
        ofs_data_sh = ofs_data_wb["Sheet1"]
        if ofs_data_sh.max_row == 2:
            print("You need to login into your OFS account first!")
            return "error"
        account_data_dict = {}
        for i in range(2, ofs_data_sh.max_row+1):
            acc_name = ofs_data_sh[f"A{i}"]
            user_agent = ofs_data_sh[f"B{i}"]
            accept_language = ofs_data_sh[f"C{i}"]
            sec_ch_ua = ofs_data_sh[f"D{i}"]
            cookie = ofs_data_sh[f"E{i}"]
            if acc_name is None or user_agent is None or accept_language is None or sec_ch_ua is None or cookie is None:
                continue
            account_data_dict.update({acc_name: [user_agent, accept_language, sec_ch_ua, cookie]})
        async with client:
            msg_pattern = re.compile(r'@\w*\b')
            wb = openpyxl.load_workbook("OnlyFansExcel.xlsx")
            sh = wb["Лист1"]

            posts_list = [] # 0-channel_id, 1-msg_id
            for c in range(2, sh.max_row+1):
                group_link = sh[f"A{c}"].value
                if sh[f"A{c}"] is None or sh[f"B{c}"] is None:
                    break
                print("1")
                group = await client.get_entity(group_link)  # t.me/onlyfans5k
                msg_list = await client.get_messages(group, limit=20)
                for msg in msg_list:
                    if msg_pattern.match(msg.text) and type(msg.media) is types.MessageMediaPhoto:
                        counter = 0
                        img_dir_list = []
                        posts_list.append([int(msg.peer_id.channel_id), msg.id, counter, img_dir_list])
                        break

            while True:
                for group in posts_list:
                    group_entity = await client.get_entity(PeerChannel(group[0]))  # t.me/onlyfans5k
                    print("1")
                    msg_list = await client.get_messages(group_entity, limit=30)
                    for msg in msg_list:
                        if not msg_pattern.match(msg.message):
                            continue
                        if msg.id == group[1]:
                            print("==group[1]")
                            break
                        print(msg)
                        msg_text = msg.message
                        msg_reply = msg.reply_to
                        print(type(msg.media))
                        if type(msg.media) is types.MessageMediaPhoto:
                            f_dir = f"imgs/photo_{msg.id}_{msg.peer_id.channel_id}"
                            await download_img(msg=msg, f_loc=f_dir)
                            group[3].append(f_dir)
                            print("2")
                            group[2] = group[2] + 1
                        print(msg.date, msg.text)
                        if group[2] == 5:
                            upload_stories(ofs_data_dict=account_data_dict, account_name="",
                                           people_tag=str(msg.text).replace("@", ""))
                            group[2] = 0
                            group[1] = msg.id
                            group[3] = []
                            print("stories")
                print("sleep-time")
                time.sleep(10)
    except Exception as err:
        print(err)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    ofs_data_wb = openpyxl.load_workbook("OnlyFansConfig.xlsx")
    ofs_data_sh = ofs_data_wb["Sheet1"]
    if ofs_data_sh.max_row == 2:
        print("You need to login into your OFS account first!")
    account_data_dict = {}
    for i in range(2, ofs_data_sh.max_row + 1):
        acc_name = ofs_data_sh[f"A{i}"].value
        user_agent = ofs_data_sh[f"B{i}"].value
        accept_language = ofs_data_sh[f"C{i}"].value
        sec_ch_ua = ofs_data_sh[f"D{i}"].value
        cookie = ofs_data_sh[f"E{i}"].value
        if acc_name is None or user_agent is None or accept_language is None or sec_ch_ua is None or cookie is None:
            continue
        account_data_dict.update({acc_name: [user_agent, accept_language, sec_ch_ua, cookie]})
        print(account_data_dict)
    api_id = 25453682  # API ID (получается при регистрации приложения на my.telegram.org)
    api_hash = "ce7d4ffbf0946e858ab05004e53dacbb"  # API Hash (оттуда же
    client = TelegramClient('OnlyFansBot', api_id, api_hash)
    #client.start()
    #client.loop.run_until_complete(check_for_posts())
    upload_stories(account_data_dict, account_name="kimonosino", people_tag="@sweetie")
