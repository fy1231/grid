#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "MoShen"

from contextlib import closing
from datetime import date
from functools import reduce

from tqsdk import TargetPosTask, TqApi, TqAuth, TqKq, TqReplay, TqBacktest  # TqSdk

# 参数设置
SYMBOL = "CZCE.SR105"  # 合约代码
X = 10
Y = 6
A = 3
B = 5

# 创建TqApi实例
api = TqApi(  # TqKq(),
    web_gui=True,  # 开启图形化
    # backtest=TqReplay(replay_dt=date(2021, 4, 1)),  # 复盘
    backtest=TqBacktest(start_dt=date(2021, 4, 1), end_dt=date(2021, 4, 7)),
    auth=TqAuth("fy1231", "136890"))  # 用户名和密码

quote = api.get_quote(SYMBOL)  # 行情数据
position = api.get_position(SYMBOL)  # 账户持仓信息
target_pos = TargetPosTask(api, SYMBOL)  # 调仓工具
target_volume = 0  # 目标持仓手数

target_volume = position.pos_long  # 维持持仓
fuckingdown_price = position.position_price_long  # 击穿价位
# (position.position_cost_long-((position.pos_long-X)/Y-1)*B/2*(position.pos_long-X)-(position.pos_long-X)/Y*B*X)/position.pos_long/10-B

with closing(api):
    while True:
        api.wait_update()
        if target_volume == 0:
            target_volume += X
            fuckingdown_price = quote.ask_price1
            print('空仓，买入！现', X, '手')
            target_pos.set_target_volume(target_volume)
        elif position.pos_long == target_volume:
            # print(quote.datetime, '清仓价位', position.position_price_long+A, '下个买入价位',
            #   (position.position_cost_long-((position.pos_long-X)/Y-1)*B/2*(position.pos_long-X)-(position.pos_long-X)/Y*B*X)/position.pos_long/10-B)
            if quote.last_price < fuckingdown_price-B:
                target_volume += Y
                fuckingdown_price = quote.ask_price1
                print('下跌击穿，买入！现', target_volume, '手')
                print(quote.datetime, '清仓价位', position.position_price_long +
                      A, '下个买入价位', fuckingdown_price-B)
                target_pos.set_target_volume(target_volume)
            elif quote.last_price > position.position_price_long+A:
                print('清仓', target_volume, '手!')
                target_volume = 0
                fuckingdown_price = 0
                target_pos.set_target_volume(target_volume)
