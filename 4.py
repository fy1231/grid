
#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "MoShen"

import csv
import datetime
import json
import os
import sys
import threading
import time
from contextlib import closing
from datetime import date
from functools import reduce

import numpy as np
import pandas as pd

# TqSdk
from tqsdk import (BacktestFinished, TargetPosTask, TqApi, TqAuth, TqBacktest,
                   TqKq, TqReplay)

replay = TqReplay(date(2021, 4, 19))

api = TqApi(
    # TqKq(),# 快期模拟
    web_gui=":34444",  # 开启图形化，固定端口
    # backtest=TqReplay(replay_dt=date(2021, 4, 19)),  # 复盘
    # backtest=replay,  # 复盘
            backtest=TqBacktest(start_dt=date(2020, 8, 2),  # 回测
                                end_dt=date(2021, 4, 21)),
            # _stock=False,  # 老行情服务器，维护时使用
            auth=TqAuth("18367005519", "Shiyan66"))  # 用户名和密码
replay.set_replay_speed(100.0)
symbol = "CZCE.SR105"

quote = api.get_quote(symbol)  # 行情数据
tick = api.get_tick_serial(symbol)  # tick序列数据
position = api.get_position(symbol)  # 账户持仓信息
target_pos = TargetPosTask(api, symbol)  # 调仓工具
target_volume = 0  # 目标持仓手数
target_volume = position.pos_long  # 维持持仓

dorecord = 0
df2 = 0
preprice = [0, 0]


async def try_async():
    global target_volume
    global dorecord
    global df2
    global preprice

    if not os.path.exists("xxx.csv"):
        df = pd.DataFrame(columns=["类型", "时间", "价格"])
        df.loc[df.shape[0]] = ["游标", datetime.datetime.fromtimestamp(
            int(tick.iloc[-1].datetime/1000000000)), tick.iloc[-1].last_price]
        df.to_csv("xxx.csv", index=False)
    else:
        df = pd.read_csv("xxx.csv")

    if not os.path.exists("sss.csv"):
        df2 = pd.DataFrame(columns=["数量", "时间", "价格"])
        df2.loc[df2.shape[0]] = [0, 0, float("inf")]
        df2.to_csv("sss.csv", index=False)
    else:
        df2 = pd.read_csv("sss.csv")

    A = 10
    B = 10
    C = 10
    D = 1.1
    E = 10
    F = 10

    t = df.loc[0, "价格"]
    n = df2.loc[0, "数量"]

    async with api.register_update_notify() as update_chan:
        async for _ in update_chan:
            if df.shape[0] % 2 == 1:
                if tick.iloc[-1].last_price > t:
                    t = tick.iloc[-1].last_price
                    df.loc[0] = ["游标", datetime.datetime.fromtimestamp(
                        int(tick.iloc[-1].datetime/1000000000)), t]
                    df.to_csv("xxx.csv", index=False)
                elif tick.iloc[-1].last_price < t-A:
                    df.loc[df.shape[0]] = ["高点", datetime.datetime.fromtimestamp(
                        int(tick.iloc[-1].datetime/1000000000)), t]
                    df.to_csv("xxx.csv", index=False)
                    # 卖
                    if df2[df2['价格'] < tick.iloc[-1].last_price - E]['数量'].sum() > 0:
                        # mai
                        print("现价：", tick.iloc[-1].last_price, "时间", datetime.datetime.fromtimestamp(
                            int(tick.iloc[-1].datetime/1000000000)))
                        print("卖出这些单子\n", df2[df2['价格'] <
                              tick.iloc[-1].last_price - E])
                        target_volume -= df2[df2['价格'] <
                                             tick.iloc[-1].last_price - E]['数量'].sum()
                        n = 0
                        df2.loc[0, "数量"] = n
                        df2 = df2.drop(
                            df2[df2['价格'] < tick.iloc[-1].last_price - E].index.to_list()).reset_index(drop=True)
                        df2.to_csv("sss.csv", index=False)
                        target_pos.set_target_volume(target_volume)

            else:
                if tick.iloc[-1].last_price < t:
                    t = tick.iloc[-1].last_price
                    df.loc[0] = ["游标", datetime.datetime.fromtimestamp(
                        int(tick.iloc[-1].datetime/1000000000)), tick.iloc[-1].last_price]
                    df.to_csv("xxx.csv", index=False)
                elif tick.iloc[-1].last_price > t+B:
                    df.loc[df.shape[0]] = ["低点", datetime.datetime.fromtimestamp(
                        int(tick.iloc[-1].datetime/1000000000)), t]
                    df.to_csv("xxx.csv", index=False)
                    # 买
                    if tick.iloc[-1].last_price < df2.iloc[-1, 2]-F:
                        target_volume += round(C*pow(D, n))
                        preprice = [position.pos_long,
                                    position.position_cost_long]
                        if preprice[0] == 0:
                            preprice = [0, 0]
                        dorecord = 1
                        n += 1
                        df2.loc[0, "数量"] = n
                        df2.to_csv("sss.csv", index=False)
                        target_pos.set_target_volume(target_volume)

# df6=df3.drop(df3[df3['价格']>5400].index.to_list()).reset_index(drop=True)
# tt[tt['价格']<5330]['数量'].sum()


async def savebuys():
    global dorecord
    global preprice
    async with api.register_update_notify() as update_chan:
        async for _ in update_chan:
            if dorecord == 1 and target_volume == position.pos_long:
                df2.loc[df2.shape[0]] = [position.pos_long-preprice[0], datetime.datetime.fromtimestamp(
                    int(tick.iloc[-1].datetime/1000000000)), (position.position_cost_long-preprice[1])/(position.pos_long-preprice[0])/10]
                if position.margin_long > df2.loc[0, "时间"]:
                    df2.loc[0, "时间"] = position.margin_long
                df2.to_csv("sss.csv", index=False)
                print('买入单子\n', df2.iloc[-1])
                dorecord = 0


api.create_task(try_async())
api.create_task(savebuys())

# quote1 = api.get_quote("CZCE.SR105")
# quote2 = api.get_quote("CZCE.SR109")


with closing(api):
    while True:
        api.wait_update()
