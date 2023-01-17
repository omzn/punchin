#!/usr/bin/env python3
# 
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service as fs
import time 
import sys
import os
import re
from datetime import datetime
from configparser import ConfigParser
import argparse   
import wget

parser = argparse.ArgumentParser(description='KIT work attending/leaving commitment') 
parser.add_argument('-a', '--attend', action='store_true', help='commit attending your work') 
parser.add_argument('-l', '--leave', action='store_true', help='commit leaving your work')
parser.add_argument('--holidays', default="https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv", help='specify holiday definition file at CAO')
parser.add_argument("--headless", action='store_true', help='do not show chrome window' )
parser.add_argument('--force', action='store_true', help='force commit')
parser.add_argument('-i', '--inifile', default="config.ini", help='specify ini file')
args = parser.parse_args()  

if args.attend != True and args.leave != True:
  print("Either --attend(-a) or --leave(-l) must be specified.")
  sys.exit()

config = ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__))+'/' + args.inifile)


web_url = config.get("jinjiweb","url")
login_id = config.get("jinjiweb","id")
login_pass = config.get("jinjiweb","pass")

holidayfile = wget.download(args.holidays)
with open(holidayfile,encoding='shift_jis') as f:
  holidaydef = [s.strip() for s in f.readlines()]
today = datetime.today().strftime("%Y/%-m/%-d")
isholiday = True if [s for s in holidaydef if s.startswith(today)] else False

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
if args.headless == True:
    options.add_argument('--headless')

# ChromeのWebDriverオブジェクトを作成する。
chrome_service = fs.Service(ChromeDriverManager().install()) 
driver = webdriver.Chrome(service=chrome_service, options=options)

# open web
try:
  driver.get(web_url) # 該当ページを開く → シボレスへ飛ぶ
  time.sleep(2) 
  driver.find_element(By.ID,"username").send_keys(login_id)   # ユーザ名  
  driver.find_element(By.ID,"password").send_keys(login_pass) # パスワード
  time.sleep(1)
  driver.find_element(By.NAME, "_eventId_proceed").click()    # 進む
  time.sleep(2)
except Exception as e:
  print("[ERROR]ログインできません．")
  print(e)
  driver.quit()  # ブラウザーを終了する。
  sys.exit()

try:
  btn_attend = driver.find_element(By.ID, "starting_stamp_btn") # 出勤ボタン
  btn_leave  = driver.find_element(By.ID, "quitting_stamp_btn") # 退勤ボタン
except Exception as e:
  print("[ERROR]ボタンを取得できません．(おそらく，ログインに関する問題です．)")
  print(e)
  driver.quit()  # ブラウザーを終了する。
  sys.exit()

try:
  work_info_table = driver.find_element(By.ID, "work_info_tbl") # 勤務状況テーブル
  trs = work_info_table.find_elements(By.TAG_NAME, "tr")
  tds = trs[3].find_elements(By.TAG_NAME,"td") # 勤務状況ヘッダを除いた最初の行
except Exception as e:
  print("[ERROR]勤務状況を取得できません．")
  print(e)
  driver.quit()  # ブラウザーを終了する。
  sys.exit()

try:
  dow = datetime.now().weekday()
  result = re.search('休暇',tds[6].text) # 最後のセルに「休暇」と書いてあるか
  if result and not args.force:
    print("本日は休暇取得中です．")
  elif (dow >= 5 or isholiday) and not args.force: 
    print("本日は休日です．")
  else:    
    if args.attend == True:
      if btn_attend.is_enabled():
        btn_attend.click()
        print("出勤しました．")
      else:
        print("すでに出勤しています．")
    elif args.leave == True:
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