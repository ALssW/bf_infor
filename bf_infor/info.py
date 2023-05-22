import json
import re

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

from .ihtml import *


class InfoNotFoundException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    pass


class Tracker:
    BASE_STATION_URL = "https://battlefieldtracker.com/bfv/profile/"
    BASE_API_URL = "https://api.tracker.gg/api"

    PROFILE_API_URL = BASE_API_URL + "/v2/bfv/standard/profile/"

    # https://battlefieldtracker.com/bfv/profile/origin/ALssssW/gamereports
    # https://api.tracker.gg/api/v1/bfv/gamereports/origin/latest/ALssssW
    REPORTS_URL = BASE_STATION_URL + "%s/%s/gamereports"
    CODE_NOT_FOUND = "CollectorResultStatus::NotFound"

    BASE_REPORT_API = BASE_API_URL + "/v1/bfv/gamereports/origin/direct/"

    REPORT_PASE_SOURCE_PRE = '<html><head><meta name="color-scheme" content="light dark"></head><body>' \
                             '<pre style="word-wrap: break-word; white-space: pre-wrap;">'
    REPORT_PASE_SOURCE_SUF = '</pre></body></html>'

    wait_reports_result = None

    def __init__(self, driver):
        logger.info(" [Tracker] <init>")
        self.driver = driver

    # def __init__(self):
    # 	logger.info(" [Tracker] <init>")

    def _get_overview(self, bf_id, station):
        """ 获取 bfv 生涯信息"""
        url = f"{self.PROFILE_API_URL + station}/{bf_id}"
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.get(url)
        data: dict = json.loads(self.driver.find_element(By.TAG_NAME, "pre").text)
        if data.get("errors")[0]["code"] == self.CODE_NOT_FOUND:
            raise InfoNotFoundException(f"未找到玩家[{bf_id}]的相关信息")
        return data["data"]

    def get_overview_text(self, bf_id, station="origin"):
        """ 以文字的方式获取 bfv 生涯数据"""
        # data = self._get_overview_(bf_id, station)
        # name = data["platformInfo"]["platformUserIdentifier"]

        return

    def get_overview_img(self, bf_id, station="origin"):
        """ 以图片的方式获取 bfv 生涯数据"""
        self._get_overview(bf_id, station)

    def get_reports(self, bf_id, station="origin", nums=5):
        """ 获取 bfv 战绩信息"""
        url = self.REPORTS_URL % (station, bf_id)
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.get(url)
        self.driver.set_page_load_timeout(10)
        logger.info(f"{threading.current_thread().name} [Tracker] <get_reports> 开始获取玩家[{bf_id}]的最近游戏报告")

        logger.debug(f"{threading.current_thread().name} [Tracker] <get_reports> 正在等待[reports]加载")
        element = WebDriverWait(
            self.driver, timeout=60).until(self._wait_for_reports, "等待[reports]加载超时")
        if self.wait_reports_result == 404:
            self._error_handle_404(bf_id)
        if self.wait_reports_result == 403:
            self._error_handle_403()
        elif self.wait_reports_result == 400:
            self._error_handle_400()
        elif self.wait_reports_result == 1:
            return self._reports_handle(bf_id, nums)
        elif self.wait_reports_result == 2:
            return 3, element

    def _error_handle_404(self, bf_id):
        """ 错误处理 404"""
        raise InfoNotFoundException(f"未找到玩家[{bf_id}]的相关信息")

    def _error_handle_403(self):
        """ 错误处理 403"""
        raise InfoNotFoundException(f"BTR 服务器错误")

    def _error_handle_400(self):
        """ 错误处理 400"""
        raise InfoNotFoundException(f"BTR 服务器访问错误")

    def _reports_handle(self, bf_id, nums):
        """ 报告处理 """
        avatar = self.driver.find_element(By.CLASS_NAME, "user-avatar__image").get_attribute("src")
        logger.info(f"{threading.current_thread().name} [Tracker] <_reports_handle> 正在获取最近[{nums} 份 reports]")
        report_urls = self.driver.find_elements(By.CSS_SELECTOR, ".reports-list a")[:nums]
        report_ids = []
        for url in report_urls:
            report_ids.append(
                re.search("/\\d*\\?", url.get_attribute("href")).group(0).removeprefix("/").removesuffix("?"))

        report_datas = []
        for iid in report_ids:
            report_url = self.BASE_REPORT_API + iid
            time.sleep(0.2)
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get(report_url)
            report_datas.append(json.loads(self.driver.page_source.replace(self.REPORT_PASE_SOURCE_PRE, "")
                                           .replace(self.REPORT_PASE_SOURCE_SUF, "")))
        logger.info(f"{threading.current_thread().name} [Tracker] <_reports_handle> 成功获取最近[{nums} 份 reports]")
        self.reports = []

        for data in report_datas:
            if data.get("error") is not None:
                return 3, None
            else:
                self._parse_report_data(bf_id, avatar, data["data"])
        logger.info(f"{threading.current_thread().name} [Tracker] <_reports_handle> 成功获取最近[{nums} 份 reports]")

        return 2, self.reports

    # def _reports_handle(self, bf_id, nums, avatar):
    # 	report_datas = []
    # 	for i in range(5):
    # 		with open(str(i) + "00.txt", "r", encoding="utf-8") as f:
    # 			report_datas.append(json.loads(f.read()))
    #
    # 	# logger.info(f"{threading.current_thread().name} [Tracker] <_reports_handle> 成功获取最近[{nums} 份 reports]")
    # 	# avatar = self.driver.find_element(By.CLASS_NAME, "ph-avatar__image").get_attribute("src")
    # 	# self.driver.close()
    # 	self.reports = []
    # 	for data in report_datas:
    # 		self._parse_report_data(bf_id, avatar, data["data"])
    # 	logger.info(f"{threading.current_thread().name} [Tracker] <_reports_handle> 成功获取最近[{nums} 份 reports]")
    # 	return 2, self.reports

    def _parse_report_data(self, bf_id, avatar, data):
        """ 解析报告 json """
        logger.info(f"{threading.current_thread().name} [Tracker] <_parse_report_data> 解析 [report data]")
        report = Report()
        server_dict = data["metadata"]
        report.server_name = server_dict["serverName"]
        try:
            report.server_map = server_dict["map"]["name"]
        except TypeError:
            report.server_map = server_dict["mapKey"]

        if server_dict["mode"]:
            report.server_mode = server_dict["mode"]["name"]
        else:
            report.server_mode = server_dict["modeKey"]
            
        report.server_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(server_dict["timestamp"]))
        report.server_duration = time.strftime('%M分%S秒', time.gmtime(server_dict["duration"]))
        report.server_is_ranked = server_dict["isRanked"]
        report.avatar = avatar

        teams_dict = data["children"]
        try:
            report.server_max_player = len(teams_dict[0]["children"]) + len(teams_dict[1]["children"]) + len(
                teams_dict[2]["children"])
        except IndexError:
            report.server_max_player = 0

        for team_dict in teams_dict:
            team_players_dict = team_dict["children"]
            for player_dict in team_players_dict:
                if player_dict["metadata"]["name"].lower() == bf_id.lower():
                    report.player_name = player_dict['metadata']['name']
                    report.play_time = time.strftime('%M分%S秒', time.gmtime(player_dict['metadata']['timePlayed']))
                    report.team = team_dict['metadata']['name']
                    if team_dict['metadata']['isWinner']:
                        report.is_winner = "胜利"
                    else:
                        report.is_winner = "失败"

                    report.stats = PlayerStat(player_dict['stats'])
                    for weapon_dict in player_dict["children"]:
                        if "weapon" == weapon_dict["type"]:
                            if "gadget" == weapon_dict["metadata"]["categoryKey"]:
                                report.gadgets.append(Gadget(weapon_dict))
                            else:
                                report.weapons.append(Weapon(weapon_dict))

                        elif "vehicle" == weapon_dict["type"]:
                            report.vehicles.append(Vehicle(weapon_dict))

        self.reports.append(report)

    def _wait_for_reports(self, driver):
        try:
            element: WebElement = driver.find_element(By.CLASS_NAME, "content--error")
            if element.text.find("400") != -1:
                logger.warning(" [Tracker] <_wait_for_reports> [error] BTR 网络错误")
                self.wait_reports_result = 400
            elif element.text.find("403") != -1:
                logger.warning(" [Tracker] <_wait_for_reports> [error] BTR 服务器错误")
                self.wait_reports_result = 403
            else:
                logger.warning(" [Tracker] <_wait_for_reports> [error] 玩家信息不存在")
                self.wait_reports_result = 404
            return element
        except NoSuchElementException:
            try:
                element = driver.find_element(By.CLASS_NAME, "reports-list")
                logger.info(
                    " [Tracker] <_wait_for_reports> [success] 本次获取报告无需验证")
                self.wait_reports_result = 1
                return element
            except NoSuchElementException:
                try:
                    element = driver.find_elements(By.CSS_SELECTOR,
                                                   "iframe[src*='sitekey=719e6c36-9055-4bc9-b01f-720bceda362e']")
                    self.wait_reports_result = 2
                    return element
                except NoSuchElementException:
                    raise NoSuchElementException()
            pass


class Captcha:
    # f"{os.path.dirname(__file__)}/resource/html/imgs/example/example-example-id.png
    example_path = None
    # f"{os.path.dirname(__file__)}/resource/html/imgs/img/img-img-id.png
    images_path = []
    images = []
    task_images = []
    now_times = 1

    def __init__(self, driver, frames):
        logger.info(" [Captcha] <init>")
        self.chooses = set()
        self.button = None
        self.target_text = None
        self.need_times = None
        self.times = None
        self.is_error = None

        self.dir_path = os.path.dirname(__file__) + "/resource/html/imgs/"
        if not os.path.exists(self.dir_path):
            os.mkdir(self.dir_path)

        self.example_img = None
        self.driver: WebDriver = driver
        self.frames = frames
        self._build_base()

    def _build_base(self):
        logger.info(" [Captcha] <_build_base_>")

        logger.info(" [Captcha] <_build_base_> 本次查询需要[hCaptcha]验证")
        checkbox_frame: WebElement = self.frames[0]
        self.pic_frame: WebElement = self.frames[1]

        checkbox = self._switch_until_find(checkbox_frame, "checkbox")
        checkbox.click()
        logger.debug(" [Captcha] <_build_base_> [hCaptcha checkbox]已点击")

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.pic_frame)
        time.sleep(2)
        self._get_example_and_times(True)
        self._get_task_image()
        pass

    def _get_example_and_times(self, is_first):
        self.driver.implicitly_wait(10)
        if is_first:
            logger.debug(
                " [Captcha] <_get_example_and_times> 等待[hCaptcha]图片验证码框架加载")
            self.example_img = self._switch_until_find(self.pic_frame, ".challenge-example .image", False,
                                                       By.CSS_SELECTOR, 30)
        else:
            self.example_img = self.driver.find_element(By.CSS_SELECTOR,
                                                        ".challenge-example .image")

        example_style = self.driver.find_element(By.CSS_SELECTOR,
                                                 ".challenge-example .image .image").get_attribute("style")
        time.sleep(0.5)
        logger.info(
            " [Captcha] <_get_example_and_times> [hCaptcha]图片验证码框架加载 成功")
        example_id = re.search('url\\("https://imgs.hcaptcha.com/.*"', example_style)
        if example_id is not None:
            example_id = example_id.group(0).removesuffix("\"")
            if len(example_id[example_id.rfind("/") + 1:]) >= 10:
                example_id = example_id[:10]
        else:
            example_id = time.time_ns()

        self.example_path = "example-%s.png" % example_id
        self.example_img.screenshot(f"{self.dir_path}/example/{self.example_path}")
        # 验证次数 .crumb-bg
        try:
            times = self.driver.find_elements(By.CSS_SELECTOR, ".crumbs-wrapper .Crumb")
            self.need_times = len(times)
        except NoSuchElementException:
            self.need_times = 1
        times = f"本次需要的验证次数为[{str(self.need_times)}]次,当前为第[{+ self.now_times}]次"
        self.times = times

        prompt = self.driver.find_element(By.CSS_SELECTOR, ".prompt-text span")
        target_text = str(prompt.text)
        if target_text.startswith("请点击每张包含"):
            target_text = target_text.removeprefix("请点击每张包含").removesuffix("的图片")
        elif target_text.startswith("请单击每个包含"):
            target_text = target_text.removeprefix("请单击每个包含").removesuffix("的图像")
        else:
            target_text = target_text.removeprefix("请点击").removesuffix("的每张图片")
        # 示例文字 .prompt-text span
        self.target_text = target_text
        logger.info(f"{threading.current_thread().name} [Captcha] <_get_example_and_times> 验证次数 [{times}]")
        logger.info(f"{threading.current_thread().name} [Captcha] <_get_example_and_times> 目标 [{target_text}]")

    def _get_task_image(self):
        self.images_path = []
        # 验证图片 .task-grid .image
        self.images = self.driver.find_elements(By.CSS_SELECTOR, ".task-grid .image")

        # 验证图片点击 .task-grid .task-image
        self.task_images = self.driver.find_elements(By.CSS_SELECTOR, ".task-grid .border-focus")

        # 确定按钮 .interface-challenge .button-submit
        self.button = self.driver.find_element(By.CSS_SELECTOR, ".interface-challenge .button-submit")
        logger.info(" [Captcha] <_build_base_> 开始保存验证图片")
        time.sleep(0.5)
        for image in self.images:
            image_path = "img-%s.png" % time.time_ns()
            image.screenshot(self.dir_path + "img/" + image_path)
            self.images_path.append(image_path)
        logger.info(" [Captcha] <_build_base_>  验证图片保存成功")
        pass

    def _click_task_image(self):
        logger.info(" [Captcha] <_click_task_image_> 开始点击验证图片")

        for choose in self.chooses:
            self.task_images[choose - 1].click()
            time.sleep(0.2)

        self.button.click()
        time.sleep(2)
        # 错误提示 .display-error aria-hidden="false"
        try:
            error = self.driver.find_element(By.CLASS_NAME, "display-error")
            sty = error.get_attribute("style")
            self.is_error = int(
                re.search("opacity: .;", sty).group(0).removeprefix("opacity: ")
                .removesuffix(";"))
        except WebDriverException:
            pass

        logger.info(" [Captcha] <_click_task_image_> 点击验证图片结束")
        pass

    def put_chooses(self, chooses: set):
        self.chooses.clear()
        logger.info(" [Captcha] <put_chooses> ", self.chooses)
        for choose in chooses:
            self.chooses.add(int(choose))

    def vail_times(self):
        return self.now_times <= self.need_times

    def vail(self):
        logger.info(f"{threading.current_thread().name} [Captcha] <vail> 开始验证 {self.times}")

        self._click_task_image()
        if self.is_success():
            return True

        self._get_example_and_times(False)
        self._get_task_image()
        if self.is_error == 1:
            logger.warning(" [Captcha] <vail> 请再试一次")
            self.now_times = 1
            self.times = f"本次需要的验证次数为[{str(self.need_times)}]次,当前为第[{+ self.now_times}]次"
            return False
        else:
            self.now_times += 1
            self.times = f"本次需要的验证次数为[{str(self.need_times)}]次,当前为第[{+ self.now_times}]次"
            logger.info(" [Captcha] <vail> 本次验证结束")
            return True

    def is_success(self):
        try:
            time.sleep(1)
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(self.pic_frame)
        except WebDriverException as e:
            logger.info(" [is_success] <True> " + e.msg)
            return True
        else:
            logger.info(" [is_success] <False>")
            return False

    def _switch_until_find(self, frame, find, multi=False, by=By.ID, _timeout=10):
        _timeout *= 2
        times = 0
        logger.debug(" [Captcha] <_switch_until_find_> [开始]")
        while True:
            try:
                try:
                    logger.debug(" [Captcha] <_switch_until_find_> [切换]")
                    self.driver.switch_to.frame(frame)
                except StaleElementReferenceException:
                    logger.debug(
                        " [Captcha] <_switch_until_find_> 框架已切换 [" + frame.id + "]")
                    pass
                if not multi:
                    logger.debug(" [Captcha] <_switch_until_find_> [寻找]")
                    value = self.driver.find_element(by, find)
                else:
                    value = self.driver.find_elements(by, find)
                    logger.debug(" [Captcha] <_switch_until_find_> [寻找]")
                if value:
                    logger.info(" [Captcha] <_switch_until_find_> [成功]")
                    return value
            except NoSuchElementException:
                pass
            time.sleep(0.5)
            times += 1
            if times > _timeout:
                raise TimeoutError("[Captcha] <_switch_until_find_> [超时]")


class PlayerStat:
    def __init__(self, player_dict):
        self.kills = player_dict[0]["value"]
        self.deaths = player_dict[1]["value"]
        self.kd = player_dict[2]["displayValue"]
        self.kpm = player_dict[3]["displayValue"]
        self.dmg = player_dict[4]["displayValue"]
        self.headshots = player_dict[5]["displayValue"]
        self.ka_kills = player_dict[6]["displayValue"]
        self.avg_kills = player_dict[7]["displayValue"]
        self.savior_kills = player_dict[8]["displayValue"]
        self.shots = player_dict[9]["displayValue"]
        self.hits = player_dict[10]["displayValue"]
        self.acc = player_dict[11]["displayValue"]
        self.dog_tags = player_dict[12]["displayValue"]
        self.longest_hs = player_dict[13]["displayValue"]
        self.highest_ks = player_dict[14]["displayValue"]
        self.highest_mk = player_dict[15]["displayValue"]
        self.heals = player_dict[16]["displayValue"]
        self.revives = player_dict[17]["displayValue"]
        self.revives_received = player_dict[18]["displayValue"]
        self.resupplies = player_dict[19]["displayValue"]
        self.repairs = player_dict[20]["displayValue"]
        self.squad_spawns = player_dict[21]["displayValue"]
        self.squad_wipes = player_dict[22]["displayValue"]
        self.orders_completed = player_dict[23]["displayValue"]
        self.score = player_dict[24]["displayValue"]
        self.spm = player_dict[25]["displayValue"]


class Vehicle:
    def __init__(self, vehicle_dict):
        self.name: str = vehicle_dict["metadata"]["name"]
        if self.name.startswith("time played with"):
            self.name = self.name.replace("time played with/", "")
        stats = vehicle_dict["stats"]

        self.time_use = stats[0]["displayValue"]
        self.kills = stats[1]["displayValue"]
        self.destroys = stats[2]["displayValue"]

    pass


class Gadget:
    def __init__(self, gadget_dict):
        self.name = gadget_dict["metadata"]["name"]
        self.img = gadget_dict["metadata"]["imageUrl"]

        gadget_stats = gadget_dict["stats"]
        self.time_use = gadget_stats[0]["displayValue"]
        self.kills = gadget_stats[1]["displayValue"]
        self.use_times = gadget_stats[4]["displayValue"]


class Weapon:
    def __init__(self, weapon_dict):
        self.name = weapon_dict["metadata"]["name"]
        self.img = weapon_dict["metadata"]["imageUrl"]

        stats = weapon_dict["stats"]
        self.time_use = stats[0]['displayValue']
        kills = stats[1]['value']
        self.kills = kills
        time_use = stats[0]['value']
        if time_use:
            self.kpm = format(kills / (time_use / 60), '.2f')
        else:
            self.kpm = 0

        self.score = stats[2]['displayValue']
        self.spm = stats[3]['displayValue']
        self.use_times = stats[4]['displayValue']
        self.headshots = stats[5]['displayValue']
        self.shots = stats[6]['displayValue']
        self.hits = stats[7]['displayValue']
        self.acc = stats[8]['displayValue']


class Report:
    server_name = None
    server_map = None
    server_mode = None
    server_time = None
    server_duration = None
    server_is_ranked = None
    server_max_player = None

    avatar = None
    player_name = None
    play_time = None
    team = None
    is_winner = None
    stats: PlayerStat

    def __init__(self):
        self.weapons: list[Weapon] = list()
        self.gadgets: list[Gadget] = list()
        self.vehicles: list[Vehicle] = list()
