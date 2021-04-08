#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "MoShen"

from contextlib import closing
from datetime import date
from functools import reduce

from tqsdk import TargetPosTask, TqApi, TqAuth, TqKq, TqReplay  # TqSdk

# 参数设置
SYMBOL = "CZCE.SR105"  # 合约代码
X = 10
A = 5
B = 11

# 创建TqApi实例
api = TqApi(#TqKq(),
            web_gui=True,  # 开启图形化
            backtest=TqReplay(replay_dt=date(2021, 4, 1)),  # 复盘
            auth=TqAuth("fy1231", "136890"))  # 用户名和密码

quote = api.get_quote(SYMBOL)  # 行情数据
position = api.get_position(SYMBOL)  # 账户持仓信息
target_pos = TargetPosTask(api, SYMBOL)  # 调仓工具
target_volume = 0  # 目标持仓手数

target_volume = position.pos_long  # 维持持仓


with closing(api):
    while True:
        api.wait_update()
        if target_volume == 0 or quote.last_price < position.position_price_long-(position.pos_long/X-1)*B/2-B:
            target_volume += X
            print('买入！现', target_volume, '手')
            target_pos.set_target_volume(target_volume)
        elif quote.last_price > position.position_price_long+A:
            print('清仓', target_volume, '手!')
            target_volume = 0
            target_pos.set_target_volume(target_volume)
        # print(quote.datetime, '清仓价位', position.position_price_long+A, '下个买入价位',
        #       position.position_price_long-(position.pos_long/X-1)*B/2-B)
