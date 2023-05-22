import os
import threading
import time

from nonebot.log import logger
from selenium.webdriver.common.by import By

from .info import Report


class ReportHtml:
    abs_path = os.path.dirname(__file__)

    def __init__(self, driver):
        logger.info(" [ReportHtml] <init>")

        self.is_last = False
        self.now_index = None
        self.driver = driver
        self.html_time = time.time_ns()
        self.dir_path = f"{self.abs_path}/resource/html/reports/{time.strftime('%Y-%m-%d')}"
        self.html_path = f"{self.dir_path}/{self.html_time}.html"
        self.img_dir_path = f"{self.abs_path}/resource/html/reports/img/{time.strftime('%Y-%m-%d')}"
        self.img_path = f"{self.img_dir_path}/{self.html_time}.png"

    def to_img(self):
        logger.info(" [ReportHtml] <to_img> 正在将 CaptchaHtml 转为图片")
        self.driver.get(self.html_path)
        self.driver.implicitly_wait(2)
        group = self.driver.find_element(By.ID, 'group')
        self.driver.set_window_size(540, group.size["height"])
        if not os.path.exists(self.img_dir_path):
            os.mkdir(self.img_dir_path)

        self.driver.find_element(By.ID, "group") \
            .screenshot(self.img_path)
        logger.info(f"{threading.current_thread().name} [ReportHtml] <to_img> [{self.img_path}]")
        return self.img_path

    def build(self, reports: list[Report]):
        logger.info(" [ReportHtml] <build> 开始构建Html")
        group = ''
        for i, report in enumerate(reports):
            self.now_index = i
            if i == len(reports) - 1:
                self.is_last = True
            if i == 0:
                group += self.group_head_info % (report.avatar, report.player_name)
            group += self._build_head(report)

        group = self.group_head % group
        build_html = self.html_base % group

        if not os.path.exists(self.dir_path):
            logger.info(f"{threading.current_thread().name} [ReportHtml] <build> 创建文件夹 [{self.dir_path}]")
            os.mkdir(self.dir_path)

        with open(self.html_path, "w", encoding="utf-8") as html_file:
            logger.info(f"{threading.current_thread().name} [ReportHtml] <build> 构建Html结束 [{self.html_path}]")
            html_file.writelines(build_html)
        pass

    def _build_head(self, report):
        if report.server_is_ranked:
            is_ranked_badge = "light"
            is_ranked_svg = self.unlock_svg
            is_ranked = "公开"
        else:
            is_ranked_badge = "warning"
            is_ranked_svg = self.lock_svg
            is_ranked = "私人"

        if "Conquest" == report.server_mode:
            mode = "征服"
        elif "Outpost0" == report.server_mode:
            mode = "前哨"
        elif "Breakthrough" == report.server_mode:
            mode = "突破"
        else:
            mode = "未知"

        if "失败" == report.is_winner:
            is_winner_badge = "danger"
        else:
            is_winner_badge = "success"

        return self.report_head % (
            report.server_name, report.team, is_winner_badge, report.is_winner, is_ranked_badge, is_ranked_svg,
            is_ranked,
            report.server_time, report.server_duration, report.play_time, report.server_map, mode,
            report.server_max_player) + self._build_body(report)

    def _build_body(self, report):
        build_body = self._build_solider_data(report) + self._build_weapons_data(
            report.weapons) + self._build_gadgets_data(report.gadgets) + self._build_vehicles_data(
            report.vehicles)

        if self.is_last:
            build_body += self.footer
        else:
            build_body += self.no_footer

        return build_body

    def _build_solider_data(self, report):
        stats = report.stats
        return self.solider_data % (stats.kills, stats.deaths, stats.kd,
                                    stats.kpm, stats.shots, stats.hits, stats.acc,
                                    stats.dmg, stats.score, stats.spm, stats.headshots, stats.ka_kills)

    def _build_weapons_data(self, weapons):
        if len(weapons):
            build_weapon = ''
            for weapon in weapons:
                if not weapon.img:
                    build_weapon += self.weapon_data_tr % ("", weapon.name, weapon.time_use,
                                                           weapon.kills, weapon.kpm, weapon.headshots, weapon.shots,
                                                           weapon.hits,
                                                           weapon.acc)
                else:
                    build_weapon += self.weapon_data_tr % (self.img_data % weapon.img, weapon.name, weapon.time_use,
                                                           weapon.kills, weapon.kpm, weapon.headshots, weapon.shots,
                                                           weapon.hits,
                                                           weapon.acc)
            return self.weapons_data_head % build_weapon
        else:
            return self.no_weapons_data

    def _build_gadgets_data(self, gadgets):
        if len(gadgets):
            build_gadgets = ''
            for gadget in gadgets:
                if not gadget.img:
                    build_gadgets += self.gadget_data_tr % (
                        "", gadget.name, gadget.time_use, gadget.kills, gadget.use_times)
                else:
                    build_gadgets += self.gadget_data_tr % (self.img_data % gadget.img, gadget.name, gadget.time_use,
                                                            gadget.kills, gadget.use_times)

            return self.gadgets_data_head % build_gadgets
        else:
            return self.no_gadgets_data

    def _build_vehicles_data(self, vehicles):
        if len(vehicles):
            build_vehicles = ''
            for vehicle in vehicles:
                build_vehicles += self.vehicles_data_tr % (
                    vehicle.name, vehicle.time_use, vehicle.kills, vehicle.destroys)
            return self.vehicles_data_head % build_vehicles
        else:
            return self.no_vehicles_data

    # group_head_info, card list
    group_head = """
<div id="group" class="m-1 card-group">
    %s
</div>
            """

    # avatar, name
    group_head_info = """
<div class="no-gutters mt-0 mb-0 card-header row d-flex  justify-content-around text-center text-white" 
style="background-color: rgb(227, 58, 89);">
        <div class="col-3 text-center">
            <img class="card-img-top w-50 shadow-lg" style="border-radius:4px;" 
            src="%s"/>
            <span class="font-weight-bold shadow-lg">%s</span>
        </div>
        
        <div class="col-8 border pt-2 table-active shadow-lg" style="border-radius: 30px;">
            <span>本次报告由<span class="badge badge-info mx-1">Azusa Bot</span>验证与生成</span>
            <br/>
            <span>如果你有更好的建议欢迎与我联系</span>
            <div class="d-flex font-weight-light  justify-content-around">
                <span class="mb-2">Made by: </span><span class="badge badge-info mt-1 h-100 mx-1">ALsW</span>
            
                <span>QQ Group: </span><span class="badge badge-info mt-1 h-100 mx-1">584151555</span>
            </div>	
        </div>
</div>
            """

    lock_svg = """
<svg class="font-weight-bold bi bi-lock" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" 
xmlns="http://www.w3.org/2000/svg">
    <path fill-rule="evenodd" d="M11.5 8h-7a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1zm-7-1a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-7zm0-3a3.5 3.5 0 1 1 7 0v3h-1V4a2.5 2.5 0 0 0-5 0v3h-1V4z" />
</svg>
        """

    unlock_svg = """
<svg class="bi bi-unlock" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor"
 xmlns="http://www.w3.org/2000/svg">
        <path fill-rule="evenodd" d="M9.655 8H2.333c-.264 0-.398.068-.471.121a.73.73 0 0 0-.224.296 1.626 1.626 0 0 0-.138.59V14c0 .342.076.531.14.635.064.106.151.18.256.237a1.122 1.122 0 0 0 .436.127l.013.001h7.322c.264 0 .398-.068.471-.121a.73.73 0 0 0 .224-.296 1.627 1.627 0 0 0 .138-.59V9c0-.342-.076-.531-.14-.635a.658.658 0 0 0-.255-.237A1.122 1.122 0 0 0 9.655 8zm.012-1H2.333C.5 7 .5 9 .5 9v5c0 2 1.833 2 1.833 2h7.334c1.833 0 1.833-2 1.833-2V9c0-2-1.833-2-1.833-2zM8.5 4a3.5 3.5 0 1 1 7 0v3h-1V4a2.5 2.5 0 0 0-5 0v3h-1V4z" />
</svg>
        """

    # server name, team, is Winner badge, is Winner,is ranked badge, is ranked svg, is ranked,
    # server time, server duration, play time, server map, server mod, server max player
    report_head = """
<div class="no-gutters mt-0 mb-0">
    <div id="header" class="pt-1 text-white text-center" style="background-color: rgb(154, 27, 148);">
        <span class="card-title font-weight-bold">
            %s													
        </span>
        <div>
            <span class="badge badge-pill badge-info">%s</span>
            <span class="badge badge-pill badge-%s">%s</span>							
            <span class="badge badge-pill badge-%s">
                %s
                %s
            </span>
        </div>
    <div class="d-flex justify-content-around mt-1">
        <table class="table text-white table-sm table-active table-borderless card-text text-center" 
        style="border-radius: 30px;">
            <tr>
                <td>
                    <svg class="bi bi-calendar3" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" 
                    xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" d="M14 0H2a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zM1 3.857C1 3.384 1.448 3 2 3h12c.552 0 1 .384 1 .857v10.286c0 .473-.448.857-1 .857H2c-.552 0-1-.384-1-.857V3.857z" />
                        <path fill-rule="evenodd" d="M6.5 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm-9 3a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm-9 3a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm3 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" />
                    </svg>
                    <span class="badge badge-pill badge-secondary">%s</span>
                </td>
                <td>
                    <svg class="bi bi-clock" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor"
                     xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14zm8-7A8 8 0 1 1 0 8a8 8 0 0 1 16 0z" />
                        <path fill-rule="evenodd" d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5z" />
                    </svg>
                    <span class="badge badge-pill badge-secondary">%s</span>
                </td>
                <td>
                    <svg class="bi bi-clock-history" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" 
                    xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" d="M8.515 1.019A7 7 0 0 0 8 1V0a8 8 0 0 1 .589.022l-.074.997zm2.004.45a7.003 7.003 0 0 0-.985-.299l.219-.976c.383.086.76.2 1.126.342l-.36.933zm1.37.71a7.01 7.01 0 0 0-.439-.27l.493-.87a8.025 8.025 0 0 1 .979.654l-.615.789a6.996 6.996 0 0 0-.418-.302zm1.834 1.79a6.99 6.99 0 0 0-.653-.796l.724-.69c.27.285.52.59.747.91l-.818.576zm.744 1.352a7.08 7.08 0 0 0-.214-.468l.893-.45a7.976 7.976 0 0 1 .45 1.088l-.95.313a7.023 7.023 0 0 0-.179-.483zm.53 2.507a6.991 6.991 0 0 0-.1-1.025l.985-.17c.067.386.106.778.116 1.17l-1 .025zm-.131 1.538c.033-.17.06-.339.081-.51l.993.123a7.957 7.957 0 0 1-.23 1.155l-.964-.267c.046-.165.086-.332.12-.501zm-.952 2.379c.184-.29.346-.594.486-.908l.914.405c-.16.36-.345.706-.555 1.038l-.845-.535zm-.964 1.205c.122-.122.239-.248.35-.378l.758.653a8.073 8.073 0 0 1-.401.432l-.707-.707z" />
                        <path fill-rule="evenodd" d="M8 1a7 7 0 1 0 4.95 11.95l.707.707A8.001 8.001 0 1 1 8 0v1z" />
                        <path fill-rule="evenodd" d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5z" />
                    </svg>
                    <span class="badge badge-pill badge-secondary">%s</span>
                </td>
            </tr>
            <tr>
                <td>
                    <svg class="bi bi-map" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor"
                     xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" d="M15.817.613A.5.5 0 0 1 16 1v13a.5.5 0 0 1-.402.49l-5 1a.502.502 0 0 1-.196 0L5.5 14.51l-4.902.98A.5.5 0 0 1 0 15V2a.5.5 0 0 1 .402-.49l5-1a.5.5 0 0 1 .196 0l4.902.98 4.902-.98a.5.5 0 0 1 .415.103zM10 2.41l-4-.8v11.98l4 .8V2.41zm1 11.98l4-.8V1.61l-4 .8v11.98zm-6-.8V1.61l-4 .8v11.98l4-.8z" />
                    </svg>
                    <span class="badge badge-pill badge-secondary">%s</span>
                </td>
                <td>
                    <svg class="bi bi-play" width="1.5em" height="1.5em" viewBox="0 0 10 16" fill="currentColor" 
                    xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" d="M10.804 8L5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 0 1 0 1.392l-6.363 3.692C4.713 12.69 4 12.345 4 11.692V4.308c0-.653.713-.998 1.233-.696l6.363 3.692z" />
                    </svg>
                    <span class="badge badge-pill badge-secondary">%s</span>
                </td>
                <td>
                    <svg class="bi bi-people" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" 
                    xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" d="M15 14s1 0 1-1-1-4-5-4-5 3-5 4 1 1 1 1h8zm-7.995-.944v-.002.002zM7.022 13h7.956a.274.274 0 0 0 .014-.002l.008-.002c-.002-.264-.167-1.03-.76-1.72C13.688 10.629 12.718 10 11 10c-1.717 0-2.687.63-3.24 1.276-.593.69-.759 1.457-.76 1.72a1.05 1.05 0 0 0 .022.004zm7.973.056v-.002.002zM11 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm3-2a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM6.936 9.28a5.88 5.88 0 0 0-1.23-.247A7.35 7.35 0 0 0 5 9c-4 0-5 3-5 4 0 .667.333 1 1 1h4.216A2.238 2.238 0 0 1 5 13c0-1.01.377-2.042 1.09-2.904.243-.294.526-.569.846-.816zM4.92 10c-1.668.02-2.615.64-3.16 1.276C1.163 11.97 1 12.739 1 13h3c0-1.045.323-2.086.92-3zM1.5 5.5a3 3 0 1 1 6 0 3 3 0 0 1-6 0zm3-2a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
                    </svg>
                    <span class="badge badge-pill badge-secondary">%s</span>
                </td>						
            </tr>
        </table>
    </div>
</div>								
        """

    # solider data, weapons data table, gadgets data table, vehicles data table
    report_body = """
<div id="body">
</div>
    %s
<div class="card-footer" style="background-color: rgb(139, 139, 139);">
</div>
        """

    # stats.kills, stats.deaths, stats.kd, stats.kpm, stats.shots, stats.hits, stats.acc,
    # stats.dmg, stats.score, stats.spm, stats.headshots, stats.ka_kills
    solider_data = """
<table id="solider-data" class="border-bottom m-0 text-white table table-sm text-left" 
style="background-color: rgb(85, 90, 94);">
        <tr>
            <td class="pl-3">
                击杀
                <span class="badge badge-dark">%s</span>
            </td>
            <td>
                死亡
                <span class="badge badge-dark">%s</span>
            </td>
            <td>
                KD
                <span class="badge badge-dark">%s</span>
            </td>
            <td>
                KPM
                <span class="badge badge-dark">%s</span>
            </td>
        </tr>
        <tr>
            <td class="pl-3">
                射击
                <span class="badge badge-dark">%s</span>
            </td>
            <td>命中
                <span class="badge badge-dark">%s</span>
            </td>
            <td>ACC
                <span class="badge badge-dark">%s</span>
            </td>
            <td>伤害
                <span class="badge badge-dark">%s</span>
            </td>
        </tr>
        <tr>
            <td class="pl-3">得分
                <span class="badge badge-dark">%s</span>
            </td>
            <td>SPM
                <span class="badge badge-dark">%s</span>
            </td>
            <td>爆头
                <span class="badge badge-dark">%s</span>
            </td>
            <td>助攻
                <span class="badge badge-dark">%s</span>
            </td>
        </tr>
    </table>
"""

    img_data = """
<div style="height: 2rem;">
        <img class="h-100" 
        src='%s'/>
    </div>
"""

    no_weapons_data = """
<table id="weapons-data-table" class=" m-0 table-borderless text-white table table-sm text-left" style="background-color: rgb(85, 90, 94);">
    <th class="pl-3">无武器数据</th>						
</table>
            """
    no_gadgets_data = """
<table id="weapons-data-table" class=" m-0 table-borderless text-white table table-sm text-left" style="background-color: rgb(85, 90, 94);">
    <th class="pl-3">无装备数据</th>						
</table>"""
    no_vehicles_data = """
<table id="weapons-data-table" class=" m-0 table-borderless text-white table table-sm text-left" style="background-color: rgb(85, 90, 94);">
    <th class="pl-3">无载具数据</th>						
</table>
            """

    # weapon_data_tr
    weapons_data_head = """		
<table id="weapons-data-table" class=" m-0 table-borderless text-white table table-sm text-left" 
style="background-color: rgb(85, 90, 94);">
    <th class="pl-3">武器-部分DLC武器可能无法显示</th>
    %s
</table>
                """

    # weapon.img, weapon.name, weapon.time_use, weapon.kills, weapon.kpm, weapon.headshots,
    # weapon.shots, weapon.hits, weapon.acc
    weapon_data_tr = """
<tr id="data-tr" class="d-flex justify-content-center pl-1" style="height: 70px;">
    <td class="col-3 pt-0 pl-0 text-center" style="background-color: rgb(105, 111, 116); width: 90px; height: 67px; 
    margin-top: 0.3rem;">
        %s
        <p style="white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">%s</p>
    </td>
    <td class="col">
        <table id="weapon-data" class="text-white table table-borderless table-sm" 
        style="height: 58px; background-color: rgb(105, 111, 116);">
            <tr>
                <td>
                    使用时长
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    击杀
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    KPM
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    爆头
                    <span class="badge badge-dark">%s</span>
                </td>
            </tr>
            <tr>
                <td>
                    射击
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    命中
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    ACC
                    <span class="badge badge-dark">%s</span>
                </td>
            </tr>
        </table>
    </td>
</tr>
        """

    # gadget_data_tr
    gadgets_data_head = """
<table id="gadgets-data-table" class=" m-0 table-borderless text-white table table-sm text-left" style="background-color: rgb(85, 90, 94);">
    <th class="pl-3">装备</th>
        %s		
</table>					
                """

    # gadget.img, gadget.name, gadget.time_use, gadget.kills, gadget.use_times
    gadget_data_tr = """
<tr id="data-tr" class="d-flex justify-content-center pl-1" style="height: 70px;">
    <td class="col-3 pt-0 pl-0 text-center" style="background-color: rgb(105, 111, 116); width: 90px; height: 58px; 
    margin-top: 0.3rem;">
        %s
        <p style="white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">%s</p>
    </td>
    <td class="col">
        <table id="gadgets-data" class="mt-0 m-auto text-white table table-borderless table-sm" style="height: 58px; 
        background-color: rgb(105, 111, 116);">
            <tr>
                <td class="pt-3">
                    使用时长
                    <span class="badge badge-dark">%s</span>
                </td>
                <td class="pt-3">
                    击杀
                    <span class="badge badge-dark">%s</span>
                </td>
                <td class="pt-3">
                    使用次数
                    <span class="badge badge-dark">%s</span>
                </td>						
            </tr>
        </table>
    </td>
</tr>			
            """

    # vehicles_data_tr
    vehicles_data_head = """
<table id="vehicles-data-table" class="m-0 table-borderless text-white table table-sm text-left" 
style="background-color: rgb(85, 90, 94);">
        <th class="pl-3">载具</th>	
        %s
</table>	
                """

    # vehicle.name, vehicle.time_use, vehicle.kills, vehicle.destroys
    vehicles_data_tr = """
<tr id="data-tr" class="d-flex justify-content-center pl-1" style="height: 40px;">
    <td class="col-4 pt-1 pl-0 text-center" style="background-color: rgb(105, 111, 116); height: 29px; 
    margin-top: 0.3rem;">
        <p style="white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">%s</p>
    </td>
    <td class="col">
        <table id="vehicles-data" class="text-white table table-borderless table-sm" 
        style="background-color: rgb(105, 111, 116);">
            <tr>
                <td>
                    使用时长
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    击杀
                    <span class="badge badge-dark">%s</span>
                </td>
                <td>
                    摧毁
                    <span class="badge badge-dark">%s</span>
                </td>
            </tr>
        </table>
    </td>
</tr>
            """

    footer_author = """
<div class="card-footer text-white" style="background-color: rgb(154, 27, 148);">
    <div style="font-size: 10px;font-weight: 100;">
        <div class="d-flex  justify-content-around">
            <span>Made by: </span><span>ALsW</span>
        </div>
        <div class="d-flex  justify-content-around">
            <span>Group: </span><span>584151555</span>
        </div>
    </div>
</div>
</div>

    """

    footer = """
<div class="card-footer text-white" style="background-color: rgb(154, 27, 148);">			
</div>
</div>		
    """

    no_footer = """			
</div>
    """

    # content
    html_base = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title></title>
    <link href=\"""" + abs_path + """/resource/html/css/bootstrap.css" rel="stylesheet" />
</head>
<body>
    %s
    </body>
</html>
        """


class CaptchaHtml:
    abs_path = os.path.dirname(__file__)

    def __init__(self, driver):
        logger.info(" [CaptchaHtml] <init>")

        self.build_card_head = ""
        self.build_card_body = ""
        self.build_card_body_row = ""
        self.build_card_body_row_col = ""
        self.driver = driver
        self.html_time = time.time_ns()
        self.dir_path = f"{self.abs_path}/resource/html/pages/{time.strftime('%Y-%m-%d')}"
        self.html_path = f"{self.dir_path}/{self.html_time}.html"
        self.img_dir_path = f"{self.abs_path}/resource/html/pages/img/{time.strftime('%Y-%m-%d')}"
        self.img_path = f"{self.img_dir_path}/{self.html_time}.png"

    def to_img(self):
        logger.info(" [CaptchaHtml] <to_img> 正在将 CaptchaHtml 转为图片")
        self.driver.get(self.html_path)
        self.driver.implicitly_wait(2)
        self.driver.set_window_size(600, 600)

        if not os.path.exists(self.img_dir_path):
            os.mkdir(self.img_dir_path)

        self.driver.find_element(By.ID, "card") \
            .screenshot(self.img_path)
        logger.info(f"{threading.current_thread().name} [CaptchaHtml] <to_img> [{self.img_path}]")
        return self.img_path

    def build(self, captcha, member_name="ALsW"):
        logger.info(" [CaptchaHtml] <build> 开始构建Html")

        build_html = self.html_base % (self.build_head(captcha, member_name) + self.build_body(captcha))

        if not os.path.exists(self.dir_path):
            logger.info(f"{threading.current_thread().name} [CaptchaHtml] <build> 创建文件夹 [{self.dir_path}]")
            os.mkdir(self.dir_path)

        with open(self.html_path, "w", encoding="utf-8") as html_file:
            logger.info(f"{threading.current_thread().name} [CaptchaHtml] <build> 构建Html结束 [{self.html_path}]")
            html_file.writelines(build_html)

    def build_head(self, captcha, member_name="ALsW"):
        logger.debug(" [CaptchaHtml] <build_head>")

        self.build_card_head = self.card_head % (
            captcha.example_path, captcha.target_text, member_name, captcha.now_times,
            captcha.need_times)
        return self.build_card_head

    def build_body(self, captcha):
        logger.debug(" [CaptchaHtml] <build_body>")

        self.build_card_body = self.card_body % self.build_body_row(captcha)
        return self.build_card_body

    def build_body_row(self, captcha):
        logger.debug(" [CaptchaHtml] <build_body_row>")

        # 建造 row 3次
        for i in range(0, 8, 3):
            h = self.card_body_row % self.build_row_col(captcha, i)
            self.build_card_body_row += h
        return self.build_card_body_row

    def build_row_col(self, captcha, _num):
        logger.debug(" [CaptchaHtml] <build_row_col>")

        paths = captcha.images_path
        self.build_card_body_row_col = ""
        # 建造 col 9次
        for i in range(_num, _num + 3):
            self.build_card_body_row_col += self.card_body_row_col % (paths[i], i + 1)
        return self.build_card_body_row_col

    # example_path, target_text, member_name, now_times, need_times
    card_head = """
<div class="text-monospace card mb-3 m-5 text-center bg-info text-white" style="width: 500px;">
<div id="card" class="row no-gutters">
    <div class="col-sm-4 h-auto card-header bg-secondary">
        <img class="border card-img w-75" style="border-radius: 7px;"
            src=\"""" + abs_path + """/resource/html/imgs/example/%s">
            <p class="m-2">请选择图片中包含<br /><span class="badge-warning font-weight-bold border" style="border-radius: 4px;">
            %s</span></p>
        <div class="mb-1" style="font-size: 13px;">
            请发送<span class="badge-warning font-weight-bold border m-1" style="border-radius: 4px;">[1~9]</span>的纯数字
            <br/>
            <small>例 [3569]</small>
        </div>
        <p class="small mt-2">本次验证仅成员<br/><span class="border">%s<br/></span>可进行验证</p>
        <p>当前为第<span class=" badge-warning font-weight-bold border m-1" style="border-radius: 4px;">%s</span>次验证<br />
            需要的验证次数为<span class="badge-warning font-weight-bold border m-1" style="border-radius: 4px;">%s</span>次</p>
        <div class="card-footer">
        <div style="font-size: 10px;font-weight: 100;">
            <div class="d-flex  justify-content-between">
                <span>Made by: </span><span>ALsW</span>
            </div>
            <div class="d-flex  justify-content-between">
                <span>Group: </span><span>584151555</span>
            </div>
        </div>						
    </div>
</div>		
        """

    # card_body_row
    card_body = """
<div class="col-sm">
    <div class="card-body ">
        %s
    </div>
</div>	
        """

    # card_body_row_col
    card_body_row = """
<div class="row">
    %s
</div>	
        """

    # path, index
    card_body_row_col = """
<div class="col p-1 mb-1" style="border: 2px solid #0084C7; border-radius: 10px; ">
    <img class="card-img" style="border-radius: 5px 5px 0px 0px;"
        src=\"""" + abs_path + """/resource/html/imgs/img/%s"/>
<h4 class="w-100 mt-0 mb-0 pb-1 badge-warning" style="border-radius: 0 0 10px 10px;">%s</h4>
</div>	
        """

    # content
    html_base = """
<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title></title>
        <link href=\"""" + abs_path + """/resource/html/css/bootstrap.css" rel="stylesheet" />
    </head>
    <body>
        %s
           </div>
            </div>
        </body>
    </html>
            """


if __name__ == '__main__':
    """"
    driver = Chrome().browser
    driver.get("D:/Codes/bot/nonebot2/BotTest/Azusa-bot-test/src/plugins/bf_infor/resource/html/pages/2023-01-18"
               "/2023_01_18_15_02_16.html")
    driver.implicitly_wait(2)
    driver.find_element(By.ID, "card")\
        .screenshot(f"resource/html/pages/img/{time.strftime('%Y_%m_%d_%H_%M_%S')}.png")

    imgkit_path = "D:/Tools/wkhtmltopdf/bin/wkhtmltoimage.exe"
    config = imgkit.config(wkhtmltoimage=imgkit_path)
    options = {
        'crop-w': 600,  # 需要截图的宽高位置，这里可以进行调整
        'crop-h': 600,
        'crop-x': 47,
        'crop-y': 47,
        "width": 1000,
        "height": 10000,
        # "--disable-smart-width": "",
        "enable-local-file-access": "",
        'encoding': 'UTF-8'
    }
    imgkit.from_file(filename="resource/html/pages/2023-01-18/2023_01_18_15_02_16.html",
                     config=config,
                     options=options,
                     output_path=f"resource/html/pages/img/{time.strftime('%Y_%m_%d_%H_%M_%S')}.jpg")
    """
