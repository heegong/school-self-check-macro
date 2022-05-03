import time
import json
import datetime
import schedule
from urllib import parse

import requests
from bs4 import BeautifulSoup

from base64 import b64encode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
from mTransKey.transkey import mTransKey


def fileRead(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def write_log(st):
    with open('macro.log', 'a', encoding='utf-8') as f:
        f.write(st)


def encrpyt(msg):
    cipher_text = cipher.encrypt(msg.encode())
    emsg = b64encode(cipher_text)
    return emsg.decode()

def fromhex(st):
    ls = [int(st[i:i+2],16) for i in range(0, len(st)-1, 2)]
    return bytes(ls)



pubkey = fileRead('public_key.txt')
pubkey = fromhex(pubkey)
keyDER = b64encode(pubkey)
keyDER = b'-----BEGIN PUBLIC KEY-----\n' + keyDER + b'\n-----END PUBLIC KEY-----'
keyPub = RSA.importKey(keyDER)
cipher = Cipher_PKCS1_v1_5.new(keyPub)






class macro:
    def __init__(self):
        self.base_url = 'https://senhcs.eduro.go.kr'
        self.info_list = self.json_read('json.json')


    def json_read(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.loads(f.read())


    def start(self):
        user_info = self.json_read('json.json')

        for user in user_info:
            name     = user['name']
            school   = user['school']
            birthday = user['birthday']
            password = user['password']

            self.macro(name, school, birthday, password)


    def macro(self, name, schcool, birthday, password):
        while True:
            log = f'[+] {datetime.datetime.now()} [Success] {name} '
            try:
                # find client version
                url = 'https://hcs.eduro.go.kr/#/main'

                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                client_version_url = soup.find('link')['href']
                client_version = client_version_url[client_version_url.rfind('eduro/')+6:client_version_url.rfind('/')]


                # school key, orgCode
                r = requests.get(self.base_url+f'/v2/searchSchool?lctnScCode=01&schulCrseScCode=4&orgName={parse.quote(schcool)}&loginType=school', headers={
                    "Referer": "https://hcs.eduro.go.kr/",
                    "Accept": "application/json, text/plain, */*",
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/json;charset=utf-8"
                    }
                )

                r_json = r.json()
                orgCode = r_json['schulList'][0]['orgCode']
                searchKey = r_json['key']



                # findUser
                post_vars = {
                    "orgCode" : orgCode,
                    "name" : encrpyt(name),
                    "birthday" : encrpyt(birthday),
                    "stdntPNo" : None,
                    "loginType" : 'school',
                    "searchKey" : searchKey
                }


                headers = {
                    "Content-Type" : "application/json;charset=UTF-8"
                }

                sess = requests.session()
                res = sess.post(self.base_url+'/v2/findUser', json=post_vars, headers=headers)
                find_user = json.loads(res.text)
                log += res.text+' '


                # transkeyServlet
                mtk = mTransKey(sess, "https://hcs.eduro.go.kr/transkeyServlet")

                pw_pad = mtk.new_keypad("number", "password", "password", "password")

                encrypted = pw_pad.encrypt_password(password)
                hm = mtk.hmac_digest(encrypted.encode())
                passs = {"raon": [
                    {
                        "id": "password",
                        "enc": encrypted,
                        "hmac": hm,
                        "keyboardType": "number",
                        "keyIndex": pw_pad.get_key_index(),
                        "fieldType": "password",
                        "seedKey": mtk.crypto.get_encrypted_key(),
                        "initTime": mtk.initTime,
                        "ExE2E": "false"
                    }
                ]}


                # validatePassword
                k = sess.post(self.base_url+"/v2/validatePassword", headers={
                    "User-Agent": "",
                    "Referer": "https://hcs.eduro.go.kr/",
                    "Authorization": find_user['token'],
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/json;charset=utf-8"
                }, data=json.dumps({
                    "password": json.dumps(passs),
                    "deviceUuid": "",
                    "makeSession": True
                }))

                token_json = json.loads(k.text)
                # registerServey
                post_vars = {
                    "deviceUuid": '',
                    "rspns00": 'Y',
                    "rspns01": '1',
                    "rspns02": '1',
                    "rspns03": '1',
                    "rspns04": None,
                    "rspns05": None,
                    "rspns06": None,
                    "rspns07": None,
                    "rspns08": None,
                    "rspns09": None,
                    "rspns10": None,
                    "rspns11": None,
                    "rspns12": None,
                    "rspns13": None,
                    "rspns14": None,
                    "rspns15": None,
                    "upperToken" : token_json['token'],
                    "upperUserNameEncpt" : name,
                    "clientVersion":client_version
                }


                headers = {
                    "Content-Type" : "application/json;charset=UTF-8",
                    "Authorization" : token_json['token']
                }



                find_user_url = self.base_url+'/registerServey'
                res = sess.post(find_user_url, json=post_vars, headers=headers)


                if '<!DOCTYPE' in res.text:
                    raise('')
                log += res.text + '\n'
                break

            except:
                log = f'[+] {datetime.datetime.now()} [failed] {name} '
                continue

            finally:
                write_log(log)



def job():
    macro().start()


schedule.every().day.at("05:00").do(job)
schedule.every().day.at("06:00").do(job)
schedule.every().day.at("07:00").do(job)



while True:
    schedule.run_pending()
    time.sleep(1)
