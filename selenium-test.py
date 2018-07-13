import os
import re
import logging
import requests
from time import sleep
from selenium import webdriver
from threading import Lock
from queue import Queue
from threading import Thread
from datetime import datetime
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='vote.log',
                    filemode='a'
    )

host = '9.112.57.52' 
port = 4444
REMOTE = False

def worker(voter, proxy_queue):
    while True:
        try:
            proxy_ip, proxy_port = proxy_queue.get()
        except Exception as e:
            logging.info('one of thread is end')
            break
        try:
            voter.vote_for_jason(proxy_ip, proxy_port)
        except Exception as e:
            logging.error(e)
        sleep(1)

class Voter(object):
    def __init__(self):
        self.lock = Lock()
        self.successful_counts = 0

    def vote_for_jason(self, proxy_ip, proxy_port, remote=REMOTE):
        if remote:
            driver = webdriver.Remote(''.join(['http://', host, ':', str(port), '/wd/hub']),
                                      desired_capabilities=DesiredCapabilities.CHROME,
                                      # chrome_options=self.options
                                      )
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            # self.options.add_argument('disable-gpu')
            # self.options.add_argument('window-size=1200x600')
            options.add_argument('--proxy-server=http://{}:{}'.format(proxy_ip, proxy_port))
            prefs = {'profile.default_content_settings.popups': 0,'download.default_directory': os.getcwd()}
            options.add_experimental_option('prefs', prefs)
            try:
                driver = webdriver.Chrome(chrome_options=options)
            except Exception as e:
                raise

        try:
            driver.get("http://enterprises.chinasourcing.org.cn/Vote/VoteIndex?id=18")
            vote = driver.find_element_by_xpath("//div[@data='154']")
            for i in range(50):
                sleep(0.25)
                vote.click()
        except Exception as e:
            # remove the ip from the proxy pool
            logging.info(
                'fail one, ip is {}:{}'.format( proxy_ip, proxy_port))
            with open('failure_ip.txt', 'a') as fp:
                fp.write('{}:{}'.format(proxy_ip, proxy_port) + '\n')
        else:
            with self.lock:
                with open('success_ip.txt', 'a') as fp:
                    fp.write('{}:{}'.format(proxy_ip, proxy_port)+'\n')

                self.successful_counts += 1
                logging.info('successful one, total number is {}, ip is {}:{}'.format(self.successful_counts, proxy_ip, proxy_port))
        finally:
            driver.quit()

def get_proxies_vip(apiUrl, proxy_queue):
    fetchSecond = 5
    while True:
        # 获取IP列表
        res = requests.get(apiUrl).content.decode()
        # 按照\n分割获取到的IP
        ips = res.split('\n')
        # 利用每一个IP
        for proxyip in ips:
            p = tuple(re.split(':', proxyip))
            proxy_queue.put(p)
        # 休眠
        sleep(fetchSecond)

def run_get_proxies_vip(apiUrl, proxy_queue):
    args=(apiUrl, proxy_queue)
    t = Thread(target=get_proxies_vip, args=args)
    t.start()

def get_proxies(f, failure_proxies=None):
    proxy_pool = set()
    with open(f, 'r') as fp:
        for line in fp.readlines():
            p = tuple(re.split(':',re.sub(r'\n','', line)))
            proxy_pool.add(p)

    if failure_proxies:
        proxy_pool = proxy_pool - failure_proxies
    return proxy_pool

def process_queue(voter, proxy_queue, thread_counts=16):
    threads = []
    args=(voter,proxy_queue)
    for _ in range(thread_counts):
        thread = Thread(target=worker, args=args)
        thread.start()

    for t in threads:
        t.join()

def main_process(voter, proxy_queue):

    #load failure ip
    f = r'C:\Users\LIMIANHUANG\workspace\proxy pool\failure_ip.txt'
    failure_proxies = get_proxies(f)

    #load new ip from proxy websites
    f = r'C:\Users\LIMIANHUANG\workspace\proxy pool\proxy_pool\Test\proxy.txt'
    raw_proxies = get_proxies(f, failure_proxies)
    for p in raw_proxies:
        proxy_queue.put(p)

    #load successful ip
    f = r'C:\Users\LIMIANHUANG\workspace\proxy pool\success_ip.txt'
    success_proxies = get_proxies(f, failure_proxies)
    for p in success_proxies:
        proxy_queue.put(p)

    process_queue(voter, proxy_queue)

if __name__ == '__main__':
    #init voter object
    voter = Voter()
    proxy_queue = Queue()
    start_time = datetime.now()

    # #use vip
    # order = "please-input-your-order-here"
    # # 获取IP的API接口
    # apiUrl = "http://dynamic.goubanjia.com/dynamic/get/" + order + ".html"

    # run_get_proxies_vip(apiUrl, proxy_queue)
    # sleep(10)
    # logging.info('# Start new cycle {}'.format(datetime.today()))
    # process_queue(voter, proxy_queue)

    # use free
    while True:
        try:
            main_process(voter, proxy_queue)
        except Exception as e:
            logging.error(e)

        end_time = datetime.now()
        sleep_time = 3600 - (end_time - start_time).seconds
        logging.info('One process cycle is done. Sleep for {} seconds'.format(sleep_time))

        sleep(max(1, sleep_time))

        # refresh start time
        start_time = datetime.now()