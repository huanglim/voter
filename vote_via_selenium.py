import os
import re
import logging
import requests
import random
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

host = '9.110.24.227'
port = 4444
REMOTE = True

USER_AGENTS = [
"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36",
"Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
"Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/52.0",
"Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0",
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
"Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
"Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
"Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
"Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
"Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52"
]

class Worker(Thread):
    def __init__(self, voter, in_queue):
        """"""
        super().__init__()
        self.voter = voter
        self.in_queue = in_queue

    def run(self):
        while True:
            proxy_ip, proxy_port = self.in_queue.get()
            try:
                self.voter.vote_for_jason(proxy_ip, proxy_port)
            except Exception as e:
                logging.error(e)


class Voter(object):
    def __init__(self):
        self.lock = Lock()
        self.successful_counts = 0



    def vote_for_jason(self, proxy_ip, proxy_port, remote=REMOTE):

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        # self.options.add_argument('disable-gpu')
        # self.options.add_argument('window-size=1200x600')
        options.add_argument(random.choice(USER_AGENTS))
        options.add_argument('--proxy-server=http://{}:{}'.format(proxy_ip, proxy_port))

        if remote:
            driver = webdriver.Remote(''.join(['http://', host, ':', str(port), '/wd/hub']),
                                      desired_capabilities=options.to_capabilities()
                                      # chrome_options=options.to_capabilities()
                                      )
        else:
            try:
                driver = webdriver.Chrome(chrome_options=options)
            except Exception as e:
                raise

        try:
            driver.get("http://enterprises.chinasourcing.org.cn/Vote/VoteIndex?id=18")
            vote = driver.find_element_by_xpath("//div[@data='154']")
            for i in range(50):
                sleep(0.20)
                vote.click()
        except Exception as e:
            # remove the ip from the proxy pool
            logging.info(
                'fail one, ip is {}:{}'.format( proxy_ip, proxy_port))
        else:
                self.successful_counts += 1
                logging.info('successful one, total number is {}, ip is {}:{}'.format(self.successful_counts, proxy_ip, proxy_port))
        finally:
            driver.quit()

def get_proxies_vip(apiUrl, proxy_queue, fetchSecond=15):
    while True:
        res = requests.get(apiUrl).content.decode()
        ips = res.split('\n')
        for proxyip in ips:
            if proxyip:
                p = tuple(re.split(':', proxyip))
                print('get new ip {}'.format(p))
                proxy_queue.put(p)
        sleep(fetchSecond)

def run_get_proxies_vip(apiUrl, proxy_queue, fetchSecond):
    args=(apiUrl, proxy_queue, fetchSecond)
    t = Thread(target=get_proxies_vip, args=args)
    t.start()

if __name__ == '__main__':
    #init voter object
    voter = Voter()
    proxy_queue = Queue()
    start_time = datetime.now()

    #use proxy agent to fetch the proxies
    order = "b7b4fdc28dd613163dc2b85ba550c3ca"
    apiUrl = "http://api.ip.data5u.com/dynamic/get.html?order="+order+"&sep=3"
    fetchSecond = 6

    run_get_proxies_vip(apiUrl, proxy_queue, fetchSecond)

    threads = []
    for _ in range(16):
        threads.append(Worker(voter, proxy_queue))

    for thread in threads:
        thread.start()
