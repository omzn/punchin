#!/usr/bin/env python3
"""出勤打刻 20240826"""
import time
import sys
import os
import re
from configparser import ConfigParser
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service as fs
from webdriver_manager.chrome import ChromeDriverManager

parser = argparse.ArgumentParser(
    description='KIT work attending/leaving commitment')
parser.add_argument('-a', '--attend', action='store_true',
                    help='commit attending your work')
parser.add_argument('-l', '--leave', action='store_true',
                    help='commit leaving your work')
parser.add_argument("--headless", action='store_true',
                    help='do not show chrome window')
parser.add_argument('--force', action='store_true', help='force commit')
parser.add_argument('-i', '--inifile', default="config.ini",
                    help='specify ini file')
args = parser.parse_args()

if args.attend is not True and args.leave is not True:
    print("Either --attend(-a) or --leave(-l) must be specified.")
    sys.exit()

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

# ChromeのWebDriverオブジェクトを作成する。
try:
    chrome_service = fs.Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=options)
#  driver = webdriver.Chrome(options=options)
except Exception as e:
    print("[ERROR]Chromeが起動しません．")
    print(e)
    sys.exit()

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
    sys.exit()

# 警告ダイアログが出た場合，とにかくOKを押す．
try:
    btn_modal_ok = driver.find_element(By.CLASS_NAME,
                                       "ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only ui-state-focus")
    btn_modal_ok.click()
    time.sleep(1)
except Exception as e:
    pass

try:
    btn_attend = driver.find_element(By.ID, "starting_stamp_btn")  # 出勤ボタン
    btn_leave = driver.find_element(By.ID, "quitting_stamp_btn")  # 退勤ボタン
except Exception as e:
    print("[ERROR]ボタンを取得できません．(おそらく，ログインに関する問題です．)")
    print(e)
    driver.quit()  # ブラウザーを終了する。
    sys.exit()

try:
    work_info_table = driver.find_element(By.ID, "work_info_tbl")  # 勤務状況テーブル
    trs = work_info_table.find_elements(By.TAG_NAME, "tr")
    tds = trs[3].find_elements(By.TAG_NAME, "td")  # 勤務状況ヘッダを除いた最初の行
except Exception as e:
    print("[ERROR]勤務状況を取得できません．")
    print(e)
    driver.quit()  # ブラウザーを終了する。
    sys.exit()

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
                print("出勤しました．")
            else:
                print("すでに出勤しています．")
        elif args.leave is True:
            if btn_leave.is_enabled():
                btn_leave.click()
                print("退勤しました．")
            else:
                if btn_attend.is_enabled():
                    print("まだ出勤していません．")
                else:
                    print("すでに退勤しています．")
except Exception as e:
    print("[ERROR]操作に失敗しました．")
    print(e)

driver.quit()  # ブラウザーを終了する。
sys.exit()
