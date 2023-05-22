import asyncio
import json
import threading
from pathlib import Path

import requests
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.log import logger
from nonebot.plugin.on import on_command
from nonebot.typing import T_State
from selenium.common import WebDriverException, StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver

from .db import UserDBException
from .ibrowser import ChromePool
from .ihtml import CaptchaHtml, ReportHtml
from .info import Tracker, Captcha, InfoNotFoundException


class CMD:
    CMD_START_EN = ":"
    CMD_START_CN = "："
    PARM_ERROR = "指令[%s]参数错误\n<%s %s>"

    GET_REPORT = "最近"
    GET_REPORT_CMD = CMD_START_EN + GET_REPORT
    GET_REPORT_PARM = "[玩家ID 或 为空]"
    GET_REPORT_PARM_ERROR = PARM_ERROR % (GET_REPORT_CMD, GET_REPORT_CMD, GET_REPORT_PARM)

    BIND_ID = "绑定"
    BIND_ID_CMD = CMD_START_EN + BIND_ID
    BIND_ID_PARM = "[玩家ID]"
    BIND_ID_PARM_ERROR = PARM_ERROR % (BIND_ID_CMD, BIND_ID_CMD, BIND_ID_PARM)

    CHANGE_BIND_ID = "改绑"
    CHANGE_BIND_ID_CMD = CMD_START_EN + CHANGE_BIND_ID
    CHANGE_BIND_ID_PARM = "[玩家ID]"
    CHANGE_BIND_ID_PARM_ERROR = PARM_ERROR % (CHANGE_BIND_ID_CMD, CHANGE_BIND_ID_CMD, CHANGE_BIND_ID_PARM)


REPORT = on_command((CMD.GET_REPORT,), priority=2)
BIND = on_command((CMD.BIND_ID,), priority=3)
CHANGE_BIND = on_command((CMD.CHANGE_BIND_ID,), priority=3)

find_player_url = "https://api.gametools.network/bfv/stats/?name="


@BIND.handle()
async def do_bind_id(event, state):
    parm: str = state["_prefix"]["command_arg"].extract_plain_text().split(" ")

    if len(parm) > 1:
        logger.warning(f" <do_bind_id> 处理指令[:绑定] {CMD.BIND_ID_PARM_ERROR}")
        await BIND.finish(MessageSegment.text(CMD.BIND_ID_PARM_ERROR))
    elif parm[0].isspace() or parm[0] == "":
        logger.warning(f" <do_bind_id> 处理指令[:绑定] {CMD.BIND_ID_PARM_ERROR}")
        await BIND.finish(MessageSegment.text(CMD.BIND_ID_PARM_ERROR))

    bf_id = parm[0]
    qq_id = event.user_id
    logger.info(f" <do_bind_id> 处理指令[:绑定] QQ:{qq_id}, 玩家ID: {bf_id}")
    try:
        bf_id = await find_bf_id(bf_id)
        if bf_id:
            db.insert(event.sender.nickname, qq_id, bf_id)
            logger.success(f" <do_bind_id> 绑定成功 QQ:{qq_id}, 玩家ID: {bf_id}")
            await BIND.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                              MessageSegment.text(
                                                                  f"已为QQ[{qq_id}]绑定玩家ID[{bf_id}]")))
        else:
            logger.warning(f" <do_bind_id> 绑定失败 QQ:{qq_id}, 未找到玩家ID: {bf_id}")
            await BIND.finish(MessageSegment.text(f"未找到玩家ID[{bf_id}]"))
    except UserDBException as e:
        logger.warning(f" <do_bind_id> 绑定失败 - {e.msg}")
        await BIND.finish(MessageSegment.text(e.msg))


@CHANGE_BIND.handle()
async def do_change_bind(event, state):
    parm: str = state["_prefix"]["command_arg"].extract_plain_text().split(" ")

    if len(parm) > 1:
        logger.warning(f" <do_change_bind> 处理指令[:改绑] {CMD.CHANGE_BIND_ID_PARM_ERROR}")
        await CHANGE_BIND.finish(MessageSegment.text(CMD.CHANGE_BIND_ID_PARM_ERROR))
    elif parm[0].isspace() or parm[0] == "":
        logger.warning(f" <do_change_bind> 处理指令[:改绑] {CMD.CHANGE_BIND_ID_PARM_ERROR}")
        await CHANGE_BIND.finish(MessageSegment.text(CMD.CHANGE_BIND_ID_PARM_ERROR))

    bf_id = parm[0]
    qq_id = event.user_id
    logger.info(f" <do_change_bind> 处理指令[:改绑] QQ:{qq_id}, BF: {bf_id}")
    try:
        bf_id = await find_bf_id(bf_id)
        if bf_id:
            db.update(qq_id, bf_id)
            logger.success(f" <do_change_bind> 改绑成功 QQ:{qq_id}, 玩家ID: {bf_id}")
            await CHANGE_BIND.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                     MessageSegment.text(
                                                                         f"已为QQ[{qq_id}]绑定玩家ID[{bf_id}]")))
        else:
            logger.warning(f" <do_change_bind> 改绑失败 QQ:{qq_id}, 未找到玩家ID: {bf_id}")
            await BIND.finish(MessageSegment.text(f"未找到玩家ID[{bf_id}]"))
    except UserDBException as e:
        logger.warning(f" <do_change_bind> 改绑失败 - {e.msg}")
        await CHANGE_BIND.finish(MessageSegment.text(e.msg))


async def find_bf_id(bf_id):
    res = requests.get(url=find_player_url + bf_id, verify=True)
    if res.status_code == 200:
        bf_id = json.loads(res.text)["userName"]
        return bf_id
    return None


time_out_set = 60
driver_nums = 2
driver_pools = ChromePool(driver_nums, 0, time_out_set)


def get_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# @REPORT.handle()
# def new_get_report(event, state):
#     do = do_get_report()
#     new_loop = asyncio.new_event_loop()
#     t = threading.Thread(target=get_loop, args=(new_loop,))
#     t.start()
#     asyncio.run_coroutine_threadsafe(do, new_loop)


@logger.catch
@REPORT.handle()
async def do_get_report(event, state):
    driver_pools.check_timeout()

    parm: str = state["_prefix"]["command_arg"].extract_plain_text().split(" ")
    for p in parm:
        p.strip()

    if len(parm) > 1:
        logger.warning(" <do_get_report> 处理指令[:最近] 指令参数错误")
        await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                            MessageSegment.text(CMD.GET_REPORT_PARM_ERROR)))

    bf_id = parm[0]
    qq_id = event.user_id
    for caller_qq_id in driver_pools.caller.values():
        if caller_qq_id == qq_id:
            logger.warning(" <get_report_handle> 当前QQ已经开启一项driver任务",
                           bf_id)
            await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                MessageSegment.text(
                                                                    f"当前QQ已经开启一项任务 任务池使用情况: [{driver_pools.actives}/"
                                                                    f"{len(driver_pools.chrome_pools)}]")))

    if bf_id.isspace() or bf_id == "":
        logger.info(" <do_get_report> 处理指令[:最近],qq_id为{}在数据库中查询bf_id", qq_id)
        result = db.query_by_qq(qq_id)
        if result is None:
            logger.warning(" <do_get_report> 未在在数据库中查询到QQ{}", qq_id)
            await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                MessageSegment.text(
                                                                    "该QQ下未绑定玩家ID\n请使用 [:绑定 玩家ID] 进行绑定")))
        bf_id = result[2]

    logger.info(" <get_report_handle> 处理指令[:最近],玩家ID为{}", bf_id)
    state.update(bf_id=bf_id)
    chrome, h_chrome = driver_pools.check_and_get(event.user_id)
    if chrome is None:
        await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                            MessageSegment.text(
                                                                f"当前无空闲driver 任务池使用情况: [{driver_pools.actives}/"
                                                                f"{len(driver_pools.chrome_pools)}]")))

    await REPORT.send(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                      MessageSegment.text(f"正在获取玩家[{bf_id}]的最近游戏报告\n"
                                                                          f"当前任务池使用情况: [{driver_pools.actives}/"
                                                                          f"{len(driver_pools.chrome_pools)}]")))

    state.update(chrome=chrome)
    state.update(h_chrome=h_chrome)

    trc = Tracker(chrome.driver)
    state.update(tracker=trc)
    try:
        stat, element = trc.get_reports(bf_id)

        if stat == 2:
            state.update(bf_id=bf_id)
            await get_reports_handle(element, event.user_id, state)

        if stat == 3:
            if element is None:
                logger.warning(" <do_get_report> 获取报告被 BTR 拦截")
                driver_pools.put_back(chrome, h_chrome)
                await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                    MessageSegment.text(
                                                                        "本次获取报告被 BTR 拦截，请重新查询以进行验证")))
            else:
                logger.info(" <do_get_report> 本次获取报告需要进行验证")
                state.update(captcha_frames=element)
                chrome.wait()
                await REPORT.pause(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                   MessageSegment.text(
                                                                       "本次获取报告需要进行验证,是否进行验证?\n请输入[是/否]")))

    except InfoNotFoundException as e:
        logger.warning(" <do_get_report> " + e.msg)
        driver_pools.put_back(chrome, h_chrome)
        await REPORT.finish(Message(e.msg))
    except TimeoutError:
        logger.warning(" <do_get_report> 等待[btr reports]响应超时")
        driver_pools.put_back(chrome, h_chrome)
        await REPORT.finish(Message("等待[btr reports]响应超时"))
    except WebDriverException as e:
        logger.error(" <do_get_report> [Web Driver]响应异常" + e.msg)
        driver_pools.put_back(chrome, h_chrome)
        await REPORT.send(Message("[Web Driver]响应异常"))
        raise e


# await REPORT.finish(Message("[Web Driver]响应异常"))


@REPORT.handle()
async def need_challenge(event: GroupMessageEvent, state: T_State):
    logger.info(" <need_challenge> 开始处理验证")
    chrome = state["chrome"]
    h_chrome = state["h_chrome"]
    driver: WebDriver = chrome.driver
    chrome.start()

    state.update(choose=event.get_plaintext())
    bf_id = state.get("bf_id")
    is_start_vali = state.get("is_start_vali")

    try:
        if state["choose"] == "否":
            # 不进行验证
            driver_pools.put_back(chrome, h_chrome)
            logger.info(f" <need_challenge> 用户拒绝验证, driver 任务结束 使用情况:[{driver_pools.actives}/"
                        f"{len(driver_pools.chrome_pools)}]")
            await REPORT.finish(Message(f"已停止获取玩家[{bf_id}]的最近游戏报告"))
        elif state["choose"] == "是" or is_start_vali is not None:
            # 进行验证 choose == 是 或 is_start_vali != None
            logger.info(" <need_challenge> 用户同意验证")
            captcha = state.get("captcha")
            if captcha is None:
                # 当 captcha is None 构建 Captcha
                logger.info(" <need_challenge> [Captcha] 开始构建")
                captcha = Captcha(driver, state["captcha_frames"])
                state.update(captcha=captcha)
                logger.info(" <need_challenge> [Captcha] 构建完成")
            if not is_start_vali:
                if captcha.vail_times():
                    await build_captcha_img("请按照图示完成验证", captcha, event, state)
            else:
                try:
                    logger.info(f"<need_challenge> [chooses] [{state['choose']}]")
                    chooses = state["choose"]
                    if chooses == ":取消" or chooses == "：取消":
                        await REPORT.finish(Message.template("{}").format(MessageSegment.text(
                                                                            "已取消验证")))
                    captcha.put_chooses(chooses)
                except ValueError:
                    logger.warning(f"{threading.current_thread().name} <need_challenge> [chooses] 选择出错")
                    chrome.wait()
                    await REPORT.reject(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                        MessageSegment.text(
                                                                            "选择出错,请输入[1~9]的纯数字\n输入[:取消]以取消验证")))

                # 开始验证 is_start_vali True
                is_success = None
                try:
                    is_success = captcha.vail()
                except StaleElementReferenceException:
                    driver_pools.put_back(chrome, h_chrome)
                    await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                        MessageSegment.text(
                                                                            "验证超时或BTR 取消了本次验证，请重新开始验证")))
                logger.info(f"<need_challenge> [vail] 验证结束")
                if not is_success:
                    state.update(is_start_vali=False)
                    logger.warning(f"{threading.current_thread().name} <need_challenge> [chooses] 验证出错")
                    await build_captcha_img("验证错误,请重新开始验证", captcha, event, state)

                if captcha.vail_times() and not captcha.is_success():
                    await build_captcha_img(f"请按照图示完成第[{captcha.now_times}]次验证", captcha, event, state)

                # 验证通过 开始获取 Reports
                logger.success(f"{threading.current_thread().name} <need_challenge> [chooses] 验证成功")
                await REPORT.send(Message.template("{}{}").format(MessageSegment.at(event.user_id),
                                                                  MessageSegment.text(
                                                                      f"正在获取玩家[{bf_id}]的最近游戏报告")))
                trc = state.get("tracker")
                stat, reports = trc.get_reports(bf_id)
                chrome.start()                
                await get_reports_handle(reports, event.user_id, state)

        else:
            logger.warning(
                f"{threading.current_thread().name} <need_challenge> [error] 输入错误,已停止获取玩家[{bf_id}]的最近游戏报告")
            driver_pools.put_back(chrome, h_chrome)
            await REPORT.finish(Message(f"输入错误,已停止获取玩家[{bf_id}]的最近游戏报告"))
    except TimeoutError as e:
        logger.error(" <need_challenge> [TimeoutError] ", e)
        driver_pools.put_back(chrome, h_chrome)
        await REPORT.send(Message("[hCaptcha]响应超时,已停止本次查询"))
        raise e

    except WebDriverException as e:
        # try:
        # 	driver.switch_to.new_window()
        # except WebDriverException:
        # 	pass
        logger.error(" <need_challenge> [WebDriverException] {}", e)
        driver_pools.put_back(chrome, h_chrome)
        await REPORT.send(Message("[Web Driver]响应异常,已停止本次查询"))
        raise e
    # await REPORT.finish(Message("[Web Driver]响应异常,已停止本次查询"))
    except Exception as e:
        logger.error(" <need_challenge> [BF INFOR Exception] {}", e)
        driver_pools.put_back(chrome, h_chrome)
        # await REPORT.send(Message("[BF INFOR]发生未知异常,已停止本次查询"))
        raise e
    pass


async def build_captcha_img(msg, captcha, event, state):
    logger.info(" <build_captcha_img> [CaptchaHtml img] 开始构建")
    html = CaptchaHtml(state["h_chrome"].driver)
    html.build(captcha, event.sender.nickname)
    # 更新状态 is_start_vali [正在进行验证]
    state.update(is_start_vali=True)
    logger.info(" <build_captcha_img> [CaptchaHtml img] 构建完成 开始转换为图片")
    state["chrome"].wait()
    await REPORT.reject_arg("choose", Message.template("{}{}{}")
                            .format(MessageSegment.at(event.user_id),
                                    MessageSegment.text(msg),
                                    MessageSegment.image(Path(html.to_img()))))

    return html


async def get_reports_handle(reports, user_id, state):
    chrome = state["chrome"]
    h_chrome = state["h_chrome"]
    html = ReportHtml(h_chrome.driver)
    html.build(reports)
    driver_pools.put_back(chrome, h_chrome)
    await REPORT.finish(Message.template("{}{}").format(MessageSegment.at(user_id),
                                                        MessageSegment.image(Path(html.to_img()))))


logger.success(" 插件 [bf-infor] 加载成功")
