# KIT出退勤打刻ツール

## インストール

0. Google Chromeをインストールしておきます．
1. 展開/クローンしたディレクトリ内で，`config.sample.ini` を`config.ini`にコピーし，id, passを適切に記述します．
2. システムにpipenvが存在しなかったら，pipenvをインストールします．
```
$ pip install pipenv
```
3. ディレクトリ内で`pipenv install`を実行します．
```
$ pipenv install 
```
これで準備完了です．

## 使い方

ディレクトリ内で，以下のコマンドを実行します．
初回実行時，または，Chromeのバージョンが上がった時は，ChromeDriverを自動でインストールするため，少し時間がかかります．

### 出勤
```
$ pipenv run attend
```
または（こちらはChromeのブラウザウィンドウが開きます．）
```
$ pipenv run python punchin.py -a
```
実行が成功すると以下のいずれかのメッセージが表示されます．

* 出勤しました．
* すでに出勤しています．
* 本日は休暇取得中です．

実行が失敗すると`[ERROR]〜`というメッセージが表示されます．

### 退勤
```
$ pipenv run leave
```
または（こちらはChromeのブラウザウィンドウが開きます．）
```
$ pipenv run python punchin.py -l
```
実行が成功すると以下のいずれかのメッセージが表示されます．

* 退勤しました．
* すでに退勤しています．
* まだ出勤していません．
* 本日は休暇取得中です．

実行が失敗すると`[ERROR]〜`というメッセージが表示されます．

## 実行ファイル(punchin.py)の仕様

```
usage: punchin.py [-h] [-a] [-l] [--headless] [--force] [-i INIFILE]

KIT work attending/leaving commitment

options:
  -h, --help            show this help message and exit 
  -a, --attend          commit attending your work
  -l, --leave           commit leaving your work
  --headless            do not show chrome window
  --force               force commit
  -i INIFILE, --inifile INIFILE
                        specify ini file
```
`punchin.py`は年次休暇等の取得を認識して，休暇の日には出勤ボタンを押せないようにしていますが，`--force`オプションによってこれを無効化できます．

## 高度な使い方

* 配布パッケージはpipenvを利用した環境になっていますが，お手持ちのシステムのpythonに必要パッケージをインストールすることで，ディレクトリに依存せず実行できるようになります．
```
$ pip3 install -r requirements.txt
```
その後，`punchin.py`を任意のディレクトリにコピーして，実行させることができます．
```
$ python /some/where/else/punchin.py -a --headless  # 出勤・ウィンドウ無
$ python /some/where/else/punchin.py -l             # 退勤・ウィンドウ有
```