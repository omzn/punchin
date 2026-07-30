#!/usr/bin/env python3
"""出勤打刻 20260730"""
import time
import sys
import os
import re
import random
from configparser import ConfigParser
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service as fs
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)

# タイトルが「警告」の jQuery UI ダイアログ
DIALOG_XPATH = (
    '//div[contains(@class, "ui-dialog")]'
    '[.//span[contains(@class, "ui-dialog-title")][normalize-space() = "警告"]]'
)
# そのダイアログのボタン領域にある OK ボタン（dialog 要素からの相対パス）
OK_BUTTON_XPATH = (
    './/div[contains(@class, "ui-dialog-buttonpane")]'
    '//button[normalize-space() = "OK"]'
)

def dismiss_warning_dialog(driver, timeout=5.0):
    """警告ダイアログが出ていれば OK を押す．出なければ何もしない．

    Returns:
        bool: ダイアログを閉じたら True，出現しなかったら False．
    """
    try:
        dialog = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, DIALOG_XPATH))
        )
    except TimeoutException:
        return False

    try:
        dialog.find_element(By.XPATH, OK_BUTTON_XPATH).click()
    except ElementClickInterceptedException:
        # ui-widget-overlay やフェードイン中のアニメーションに邪魔された場合の保険
        btn_ok = dialog.find_element(By.XPATH, OK_BUTTON_XPATH)
        driver.execute_script("arguments[0].click();", btn_ok)
    except StaleElementReferenceException:
        # クリック前にダイアログ側が勝手に閉じた
        return True

    # 実際に閉じたことを確認してから戻る（後続処理がオーバーレイに邪魔されないように）
    WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element_located((By.XPATH, DIALOG_XPATH))
    )
    return True


parser = argparse.ArgumentParser(
    description='Work attending/leaving commitment')
parser.add_argument('-a', '--attend', action='store_true',
                    help='commit attending your work')
parser.add_argument('-l', '--leave', action='store_true',
                    help='commit leaving your work')
parser.add_argument('--delay', action='store', type=int,
                    help='delay time to commit in seconds')
parser.add_argument('--random', action='store_true',
                    help='randomize delay time up to --delay')
parser.add_argument("--headless", action='store_true',
                    help='do not show chrome window')
parser.add_argument('--force', action='store_true', help='force commit')
parser.add_argument('-i', '--inifile', default="config.ini",
                    help='specify ini file')
args = parser.parse_args()

if args.attend is not True and args.leave is not True:
    print("Either --attend(-a) or --leave(-l) must be specified.")
    sys.exit(-1)

config = ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__))+'/' + args.inifile)

web_url = config.get("jinjiweb", "url")
login_id = config.get("jinjiweb", "id")
login_pass = config.get("jinjiweb", "pass")

options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {
    "download.default_directory": "./",
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.plugins_disabled": ["Chrome PDF Viewer"],
    "plugins.always_open_pdf_externally": True
})
options.add_argument("--disable-extensions")
options.add_argument("--disable-print-preview")
options.add_argument("--no-sandbox")
if args.headless is True:
    options.add_argument('--headless')

# 遅延処理
if args.delay:
    if args.random:
        delay = random.randint(1, args.delay)
    else:
        delay = args.delay
    time.sleep(delay)

# ChromeのWebDriverオブジェクトを作成する。
try:
    chrome_service = fs.Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=options)
#  driver = webdriver.Chrome(options=options)
except Exception as e:
    print("[ERROR]Chromeが起動しません．")
    print(e)
    sys.exit(-1)

# open web
try:
    driver.get(web_url)  # 該当ページを開く → シボレスへ飛ぶ
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys(login_id)   # ユーザ名
    driver.find_element(By.ID, "password").send_keys(login_pass)  # パスワード
    time.sleep(1)
    driver.find_element(By.NAME, "_eventId_proceed").click()    # 進む
    time.sleep(2)
except Exception as e:
    print("[ERROR]ログインできません．")
    print(e)
    driver.quit()  # ブラウザーを終了する。
    sys.exit(-1)

# 警告ダイアログが出た場合，とにかくOKを押す．
if dismiss_warning_dialog(driver):
    #print("[INFO]警告ダイアログが出たため，OKを押しました．")
    pass

try:
    btn_attend = driver.find_element(By.ID, "starting_stamp_btn")  # 出勤ボタン
    btn_leave = driver.find_element(By.ID, "quitting_stamp_btn")  # 退勤ボタン
except Exception as e:
    print("[ERROR]ボタンを取得できません．(おそらく，ログインに関する問題です．)")
    print(e)
    driver.quit()  # ブラウザーを終了する。
    sys.exit(-1)

try:
    work_info_table = driver.find_element(By.ID, "work_info_tbl")  # 勤務状況テーブル
    trs = work_info_table.find_elements(By.TAG_NAME, "tr")
    tds = trs[3].find_elements(By.TAG_NAME, "td")  # 勤務状況ヘッダを除いた最初の行
except Exception as e:
    print("[ERROR]勤務状況を取得できません．")
    print(e)
    driver.quit()  # ブラウザーを終了する。
    sys.exit(-1)

try:
    nonworking1 = re.search('休暇', tds[6].text)  # 最後のセルに「休暇」と書いてあるか
    nonworking2 = re.search('休日', tds[0].text)  # 最初のセルに「休日」と書いてあるか
    working = re.search('出勤', tds[0].text)  # 最初のセルに「出勤」と書いてあるか
    if nonworking1:
        print("本日は休暇取得中です．")
    elif nonworking2 and not working:
        print("本日は休日です．")
    elif working:
        if args.attend is True:
            if btn_attend.is_enabled():
                btn_attend.click()
                time.sleep(2)
                print("出勤しました．")
            else:
                print("すでに出勤しています．")
        elif args.leave is True:
            if btn_leave.is_enabled():
                btn_leave.click()
                time.sleep(2)
                print("退勤しました．")
            else:
                if btn_attend.is_enabled():
                    print("まだ出勤していません．")
                else:
                    print("すでに退勤しています．")
except Exception as e:
    print("[ERROR]操作に失敗しました．")
    print(e)
    sys.exit(-1)

driver.quit()  # ブラウザーを終了する。
sys.exit(0)  # 正常終了
