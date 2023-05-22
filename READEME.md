# BF_INFOR 
> 一款基于 nonebot2 的 BFV 战局查询插件
> 
> 由于 BTR 在近期 (2023-5-13日，人机验证已取消) 为战局报告的查询开启的人机验证，导致目前所使用到战局查询的软件都已无法查询，
> 为了方便玩家们能够不通过魔法上网等方式就能够便捷查询到最近战局，所以在今年春节假期期间我从从自学 Python 完成了该插件的编写。

# 准备
本插件是基于 selenium 通过 Chrome 浏览器数据爬虫完成

所以在使用前请准备好以下：

1. 下载最新版本的 [Chrome](https://www.google.cn/intl/zh-CN/chrome/) 浏览器
2. 下载该版本浏览器对应的 [driver](https://registry.npmmirror.com/binary.html?path=chromedriver/)

# 开始
1. 下载本插件源码后，将源码（bf_infor 文件夹）放入你的 nonebot2 中的 plugins 文件夹中
2. 将你下好的 chrome driver 替换 ../bf_infor/resource/tool/browser_driver 目录中的 driver
3. 重启 bot 即可开始使用

# 命令
本插件使用的命令前缀为 “:” 冒号

| 指令       | 作用                                                           |
|----------|--------------------------------------------------------------|
| :最近 [id] | 查询指定玩家最近5场(最多5场，具体数量以BTR当前页面展示数量为准)战局报告<br/>(当绑定ID后可以省略输入ID) |
| :绑定 [id] | 为发送该指令的QQ号绑定该玩家ID                                            |
| :改绑 [id] | 修改当前QQ号所绑定的玩家ID                                              |