import time
import json
import schedule
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


log_filename = 'macro.log'


def write_log(st):
    with open(log_filename, 'a', encoding='utf-8') as f:
        f.write(st)


class macro:
    def __init__(self):
        # class settings
        self.wait_time = 5
        self.info_list = self.json_read('json.json')

        # selenium settigns
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')


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


    def xpath_enter(self,str):
        button = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, str)))
        button.send_keys(Keys.ENTER)


    def xpath_click(self, str):
        button = WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, str)))
        button.click()


    def macro(self, name, school, birthday, password):
        while True:
            log = f'[+] {datetime.datetime.now()} {name} '
            # selenium start
            try:
                driver = webdriver.Chrome(
                    './chromedriver',
                    chrome_options=self.chrome_options,
                    service_args=['--verbose', '--log-path=/tmp/chromedriver.log']
                )
                driver.get("https://hcs.eduro.go.kr/#/none")
                driver.title.encode('utf-8', 'replace')
                self.driver = driver

                self.xpath_click('//*[@id="btnConfirm2"]')
                self.xpath_click('//*[@id="WriteInfoForm"]/table/tbody/tr[1]/td/button')

                select = Select(driver.find_element_by_id('sidolabel'))
                select.select_by_index(1)
                select = Select(driver.find_element_by_id('crseScCode'))
                select.select_by_index(4)

                elem = driver.find_element_by_class_name("searchArea")
                elem.send_keys(school)

                driver.find_element_by_class_name("searchBtn").click()
                self.xpath_click('//*[@id="softBoardListLayer"]/div[2]/div[1]/ul/li/a/p/a')
                driver.find_element_by_class_name("layerFullBtn").click()

                elem = driver.find_element_by_id("user_name_input")
                elem.send_keys(name)
                elem = driver.find_element_by_id("birthday_input")
                elem.send_keys(birthday)

                driver.find_element_by_id("btnConfirm").click()
                self.xpath_click('//*[@id="password"]')


                # 보안 키패드 로딩 기달리기
                keypad = []
                FLAG = True
                while FLAG:
                    keypad = []
                    # 키패드 가져오기
                    keypad += driver.find_elements_by_class_name("transkey_div_3_3")
                    keypad += driver.find_elements_by_class_name("transkey_div_3_2")

                    keypad_len = 0
                    for i in keypad:
                        get_attr = i.get_attribute("aria-label")
                        if get_attr == None:
                            FLAG = True
                            break
                        elif get_attr == ' ':
                            FLAG = True
                            break
                        keypad_len+=1

                    if keypad_len==12 and FLAG:
                        FLAG = False

                # 딕셔너리에 담기
                dic = {}

                for i in keypad:
                    log += i.get_attribute("aria-label")+' '
                    dic[i.get_attribute("aria-label")] = i



                #페스워드 클릭
                for i in password:
                    dic[i].click()


                self.xpath_click('//*[@id="btnConfirm"]')                # 확인 버튼
                self.xpath_enter('//*[@id="container"]/div/section[2]/div[2]/ul/li/a')



                # 아니요 3개
                self.xpath_click('//*[@id="survey_q1a1"]')
                self.xpath_click('//*[@id="survey_q2a1"]')
                self.xpath_click('//*[@id="survey_q3a1"]')

                # 마지막
                self.xpath_click('//*[@id="btnConfirm"]')

                driver.quit()

                log += 'success\n'
                break                       # 에러가 발생하지 않으면 while문 끝내기
            except:
                driver.quit()
                log += 'failed\n'
                continue                    # 에러 발생시 다시 실행
            finally:
                write_log(log)              # 로그는 try든 except든 무조건 실행



def job():
    macro().start()


schedule.every().day.at("05:00").do(job)
schedule.every().day.at("06:00").do(job)
schedule.every().day.at("07:00").do(job)



while True:
    schedule.run_pending()
    time.sleep(1)
