import time
import json
import requests
import datetime
import schedule

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
        log = f'[+] {datetime.datetime.now()} {name} '

        # findUser
        post_vars = {
            "orgCode" : schcool,
            "name" : encrpyt(name),
            "birthday" : encrpyt(birthday),
            "stdntPNo" : None,
            "loginType" : 'school'
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


        # registerServey
        post_vars = {
        "deviceUuid": '',
        "rspns00": 'Y',
        "rspns01": '1',
        "rspns02": '1',
        "rspns03": None,
        "rspns04": None,
        "rspns05": None,
        "rspns06": None,
        "rspns07": '0',
        "rspns08": '0',
        "rspns09": '0',
        "rspns10": None,
        "rspns11": None,
        "rspns12": None,
        "rspns13": None,
        "rspns14": None,
        "rspns15": None,
        "upperToken" : k.text[1:-1],
        "upperUserNameEncpt" : name
        }



        headers = {
            "Content-Type" : "application/json;charset=UTF-8",
            "Authorization" : k.text[1:-1]
        }



        find_user_url = self.base_url+'/registerServey'
        res = sess.post(find_user_url, json=post_vars, headers=headers)
        log += res.text + '\n'
        write_log(log)


def job():
    macro().start()


schedule.every().day.at("05:00").do(job)
schedule.every().day.at("06:00").do(job)
schedule.every().day.at("07:00").do(job)



while True:
    schedule.run_pending()
    time.sleep(1)
