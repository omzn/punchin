"""単純にslackにつぶやく"""
import os
import argparse
from configparser import ConfigParser
from slack_sdk import WebClient

parser = argparse.ArgumentParser(description='Soflab slack say something')
parser.add_argument('-r', '--reply', help='who to speak' )
parser.add_argument('-c', '--channel', default='lab_status', help='channels to say something')
parser.add_argument('-m', '--message', default='', help='something')
parser.add_argument('-i', '--inifile', dest='inifile', default="config.ini",
                action="store",
                metavar="FILE",
                help='specify ini file')
args = parser.parse_args()

config = ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__))+'/' + args.inifile)

slack = WebClient(config.get('slackapi', 'token'))

msg = f"<@{args.reply}>" if args.reply else ""
msg += f" {args.message}"

response = slack.chat_postMessage(
  text=msg,
  channel=f"#{args.channel}",
  as_user=True)

print(response)
