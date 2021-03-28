#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "MoShen"

from contextlib import closing
from datetime import date
from functools import reduce

from tqsdk import TargetPosTask, TqApi, TqAuth, TqReplay  # TqSdk

# 网格参数设置
SYMBOL = "CZCE.SR105"  # 合约代码
START_PRICE = 5000  # 起始价位
GRID_AMOUNT = 10  # 网格数量
GRID_REGION = 100  # 网格密度
GRID_VOLUME = 10  # 每格交易手数


# 生成网格
grid_amount_long = GRID_AMOUNT  # 多头网格数量
grid_amount_short = GRID_AMOUNT  # 空头网格数量
grid_region_long = [GRID_REGION] * GRID_AMOUNT  # 多头网格密度
grid_region_short = [GRID_REGION] * GRID_AMOUNT  # 空头网格密度
grid_volume_long = [GRID_VOLUME] * GRID_AMOUNT  # 多头每格交易手数
grid_volume_short = [-GRID_VOLUME] * GRID_AMOUNT  # 空头每格交易手数
grid_prices_long = [reduce(lambda p, r: p*(1-r) if r < 1 else p-r, grid_region_long[:i], START_PRICE)
                    for i in range(GRID_AMOUNT + 1)]  # 多头每格触发价位列表, 第一个元素为起始价位
grid_prices_short = [reduce(lambda p, r: p*(1+r) if r < 1 else p+r, grid_region_short[:i], START_PRICE)
                     for i in range(GRID_AMOUNT + 1)]  # 空头每格触发价位列表, 第一个元素为起始价位


print("起始价位:", START_PRICE)
print("多头每格交易量:", grid_volume_long)
print("空头每格交易量:", grid_volume_short)
print("多头每格的价位:", grid_prices_long)
print("空头每格的价位:", grid_prices_short)


# 创建TqApi实例
api = TqApi(web_gui=True,  # 开启图形化
            # backtest=TqReplay(replay_dt=date(2021, 3, 24)),  # 复盘
            auth=TqAuth("fy1231", "136890"))  # 用户名和密码

quote = api.get_quote(SYMBOL)  # 行情数据
target_pos = TargetPosTask(api, SYMBOL)  # 调仓工具
position = api.get_position(SYMBOL)  # 账户持仓信息
target_volume = 0  # 目标持仓手数


# 异步监视器
async def price_watcher(open_price, close_price, volume):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    global target_volume
    # 当 quote 有更新时会发送通知到 update_chan 上
    async with api.register_update_notify(quote) as update_chan:
        while True:
            async for _ in update_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发开仓条件
                if (volume > 0 and quote.last_price <= open_price) or (volume < 0 and quote.last_price >= open_price):
                    break
            target_volume += volume
            target_pos.set_target_volume(target_volume)
            print("时间:", quote.datetime, "最新价:", quote.last_price,
                  "开仓", volume, "手", "总仓位:", target_volume, "手")
            async for _ in update_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发平仓条件
                if (volume > 0 and quote.last_price > close_price) or (volume < 0 and quote.last_price < close_price):
                    break
            target_volume -= volume
            target_pos.set_target_volume(target_volume)
            print("时间:", quote.datetime, "最新价:", quote.last_price,
                  "平仓", volume, "手", "总仓位:", target_volume, "手")


# 添加监视
for i in range(GRID_AMOUNT):
    api.create_task(price_watcher(
        grid_prices_long[i+1], grid_prices_long[i], grid_volume_long[i]))
    api.create_task(price_watcher(
        grid_prices_short[i+1], grid_prices_short[i], grid_volume_short[i]))

# 运行策略
with closing(api):
    while True:
        api.wait_update()
