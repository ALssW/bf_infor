import json
import os
import sqlite3

import requests
from nonebot.log import logger

abs_path = os.path.dirname(__file__)

conn = sqlite3.connect(f'{abs_path}/resource/db/bf_infor.db')
cursor = conn.cursor()
cursor.execute('''
create table if not exists user
(qq_id text primary key,
name text not null,	
bf_id text not null);
       ''')

conn.commit()
cursor.close()


def insert(name, qq_id, bf_id):
    result = query_by_qq(qq_id)
    if result is not None:
        raise UserDBException(f"该QQ下已绑定玩家ID [{result[2]}]\n请使用 [:改绑 玩家ID] 进行改绑")

    insert_cursor = conn.cursor()
    insert_sql = f"insert into user values( '{qq_id}', '{name}', '{bf_id}');"
    logger.info(f"[bf_infor db] <insert> 插入用户数据 - [{insert_sql}]")
    insert_cursor.execute(insert_sql)
    conn.commit()
    insert_cursor.close()
    pass


def update(qq_id, bf_id):
    result = query_by_qq(qq_id)
    if result is None:
        raise UserDBException("该QQ下未绑定玩家ID\n请使用 [:绑定 玩家ID] 进行绑定")

    update_course = conn.cursor()
    update_sql = f"update user set bf_id='{bf_id}' where qq_id = '{qq_id}';"
    logger.info(f"[bf_infor db] <update> 更新用户数据 - [{update_sql}]")
    update_course.execute(update_sql)
    conn.commit()
    update_course.close()
    pass


def query_by_bf(bf_id):
    return _query("user", "*", "bf_id", bf_id)


def query_by_qq(qq_id):
    return _query("user", "*", "qq_id", qq_id)


def _query(table, selects: str | list[str], bys: str | list[str], params: str | list[str]) -> tuple:
    query_cursor = conn.cursor()
    s = ""
    if isinstance(selects, list):
        for select in selects:
            s += select + ", "
    else:
        s = selects

    b = ""
    if isinstance(bys, list):
        for by in bys:
            for param in params:
                b += f"{by} = {param},"
    else:
        b = f"{bys} = {params}"

    query_sql = f"select {s.removesuffix(', ')} from {table} where {b.removesuffix(',')};"
    logger.info(f"[bf_infor db] <_query> 查询用户数据 - [{query_sql}]")
    query_cursor.execute(query_sql)
    result = query_cursor.fetchone()
    logger.debug(f"[bf_infor db] <_query> 查询用户数据 : [{result}]")
    query_cursor.close()
    return result


class UserDBException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


if __name__ == '__main__':
    find_player_url = "https://api.gametools.network/bfv/stats/?name="
    bf_id = "a1svvv"
    res = requests.get(url=find_player_url + bf_id, verify=True)
    if res.status_code == 200:
        print(json.loads(res.text))
        bf_id = json.loads(res.text)["userName"]
        print("*" * 20 + bf_id)
