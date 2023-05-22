import os
import sys
from datetime import datetime

from nonebot.log import logger
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.chrome.options import Options

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)


class Chrome:
    state = True
    start_time: datetime = None
    need_check = False
    is_timeout = False
    caller = None
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    chrome_driver_path = os.path.dirname(__file__) + "\\resource\\tool\\browser_driver\\chromedriver.exe"

    def __init__(self):
        self.driver = None
        self.chrome_options = None
        self.set_options()
        self._get_chrome()

    def set_options(self):
        self.chrome_options: Options = webdriver.ChromeOptions()
        self.chrome_options.binary_location = self.chrome_path
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-ssl-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument("Access-Control-Allow-Origin: *")
        self.chrome_options.add_argument("--args")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("enable-automation")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--dns-prefetch-disable")
        
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.chrome_options.add_experimental_option("detach", True)

    def _get_chrome(self):
        logger.info(" [Chrome] <init>")
        self.driver = webdriver.Chrome(self.chrome_driver_path, chrome_options=self.chrome_options)

    def wait(self):
        self.start_time = datetime.now()
        self.need_check = True

    def start(self):
        self.need_check = False

    def stop(self):
        self.state = True
        self.need_check = False

    pass

    def alive(self):
        try:
            if self.driver.title is None:
                raise WebDriverException
        except WebDriverException:
            return False
        else:        
            return True


class ChromeHeadless(Chrome):

    def __init__(self):
        super().__init__()
        pass

    def set_options(self):
        self.chrome_options: Options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        print(self.chrome_options.arguments)

    def _get_chrome(self):
        logger.info(" [ChromeHeadless] <init>")
        self.driver = webdriver.Chrome(self.chrome_driver_path, chrome_options=self.chrome_options)


class ChromePool:
    chrome_pools: list[Chrome] = list()
    h_chrome_pools: list[ChromeHeadless] = list()
    caller = dict()
    actives = 0

    def __init__(self, nums, windows, timeout):
        """
        创建 Chrome 池
        :param nums: Chrome 数 = Headless Chrome 数
        :param windows: Chrome 的窗口
        :param timeout: 任务超时时间
        """
        self._set_pools(nums, windows)
        self.nums = nums
        self.timeout = timeout
        logger.debug(f" [ChromePool] <init> chrome pools[{len(self.chrome_pools)}] "
                     f" h_chrome pools[{len(self.h_chrome_pools)}]")

    def _set_pools(self, nums, windows):
        for num in range(nums):
            chrome = Chrome()
            h_chrome = ChromeHeadless()
            for i in range(windows):
                chrome.driver.execute_script("window.open('','_blank');")
            self.h_chrome_pools.append(h_chrome)
            self.chrome_pools.append(chrome)

    def check_and_get(self, qq_id):
        logger.info(f" [check_and_get] 检查 active: [{str(self.actives)}/"
                    f"{len(self.chrome_pools)}]")
        for i in range(self.nums):
            logger.info(f" [check_and_get] 检查 active: [{self.chrome_pools[i].state} / "
                        f"{self.h_chrome_pools[i].state}]")

            if self.chrome_pools[i].state and self.h_chrome_pools[i].state:
                logger.info(" [check_and_get] 发现空闲 driver")
                if self.chrome_pools[i].alive():
                    self.chrome_pools[i].state = False
                else:
                    logger.error(" [check_and_get] chrome driver 异常 开始重建")
                    self.chrome_pools[i] = Chrome()

                if self.h_chrome_pools[i].alive():
                    self.h_chrome_pools[i].state = False
                else:
                    logger.error(" [check_and_get] h_chrome driver 异常 开始重建")
                    self.h_chrome_pools[i] = ChromeHeadless()
                self.chrome_pools[i].start_time = datetime.now()
                self.chrome_pools[i].need_check = True
                self.caller.update({self.chrome_pools[i]: qq_id})
                if self.actives < self.nums:
                    self.actives += 1
                return self.chrome_pools[i], self.h_chrome_pools[i]
        logger.warning(" [check_and_get] 无空闲 driver")
        return None, None

    def check_timeout(self):
        logger.debug(f"[ChromePool] <check_timeout> 使用情况: [{self.actives}/{len(self.chrome_pools)}]")

        for i in range(self.nums):
            check = self.chrome_pools[i]
            if check.need_check:
                logger.debug("[ChromePool] <check_timeout> 检查")
                if (datetime.now() - check.start_time).total_seconds() >= self.timeout:
                    logger.info("[ChromePool] <check_timeout> 发现超时的 driver任务")
                    try:
                        check.state = True
                        check.need_check = False
                        self.h_chrome_pools[i].state = True
                        self.caller.pop(check)
                    except KeyError:
                        self.caller.clear()
                        self.actives = 0

                    if self.actives > 0:
                        self.actives -= 1
                    return True

    def put_back(self, chrome, h_chrome):
        try:
            logger.info(
                f"[put_back] 结束了[{self.caller.get(chrome)}]的driver任务 使用情况: [{self.actives}/{len(self.chrome_pools)}]")
            chrome.stop()
            h_chrome.stop()
            self.caller.pop(chrome)
            if self.actives > 0:
                self.actives -= 1
        except KeyError:
            logger.info(
                f"[put_back] 结束[{self.caller.get(chrome)}]的driver任务 发生 Key异常 使用情况: [{self.actives}/"
                f"{len(self.chrome_pools)}]")
            pass
