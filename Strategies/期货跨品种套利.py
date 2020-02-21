from Windpy import *
import numpy as np
import pandas as pd
import talib as ta
from datetime import *
w.start() #import windpy之后启动windpy

# 引入回测框架
from WindAlgo import *

# 定义初始化函数
def initialize(context):
    #回测初始资金
    context.capital = 1000000
    #回测开始时间
    context.start_date = '20130501'
    #回测结束时间
    context.end_date = '20150701'
    #设置豆油为基准
    context.benchmark = 'Y.DCE'
    #策略涉及证券池
    context.securities = ['Y.DCE', 'P.DCE', 'OI.CZC']
    #策略运行周期
    context.period = 'd'
    context.trade_flag = 0

#定义策略函数
def handle_data(bar_datetime, context, bar_data):
	trade_flag = context.trade_flag
	count_days = 60
	his_data_df = pd.DataFrame()
    #获取证券池里涉及品种的历史数据
    #并存储为his_data_df
	for i in range(len(context.securities)):
		his_data = wa.history(context.securities[len(context.securities)-i-1], count_days + 1)
        temp_data_df = pd.DataFrame(his_data.get_field('close'), index = his_data.get_field('time'), columns = [context.securities[len(context.securities) - i - 1]])
        his_data_df = temp_data_df.join(his_data_df)
    #计算指标
    #((豆油价格-棕榈油价格)-(菜籽油价格-豆油价格))/(菜籽油价格-棕榈油价格)
    his_data_df['indicator'] = ((his_data_df['Y.DCE'] - his_data_df['P.DCE']) - (his_data_df['OI.CZC'] - his_data_df['Y.DCE'])) / (his_data_df['OI.CZC'] - his_data_df['P.DCE'])
    #近20天的平均值
    ind_rec = his_data_df['indicator'][-20:].mean()
    #近30天的平均值（中期）
    ind_mid = his_data_df['indicator'][-30:].mean()
    #近40天的平均值（长期）
    ind_lon = his_data_df['indicator'][-40:].mean()
    ind_cur = float(his_data_df['indicator'][-1:])

#交易区
    position = wa.query_position()
    if(ind_rec > ind_mid and ind_mid > ind_lon and ind_cur > 1.05 * ind_rec):
        if(trade_flag != 1):
            if len(position) > 0:
                res = wa.batch_order.sell_all(price = 'close', volume_check = False, no_quotation = 'error')
            res_l = wa.order_percent('P.DCE', 0.1, 'buy', volume_check = True)
            res_s = wa.order_percent('Y.DCE', 0.1, 'short', volume_check = True)
            trade_flag = 1
    elif(ind_rec < ind_mid and ind_mid < ind_lon and ind_cur < 0.98 * ind_rec):
        if(trade_flag != -1):
            if len(position) > 0:
                res = wa.batch_oder.sell_all(price = 'close', volume_check = False, no_quotation = 'error')
            res_l = wa.order_percent('Y.DCE', 0.1, 'buy', volume_check = True)
            res_s = wa.order_percent('OI.CZC', 0.1, 'short', volume_check = True)
            trade_flag = -1
    elif(ind_cur < 1.02 * ind_rec and ind_cur > 0.98 * ind_rec):
        if len(position) > 0:
             res = wa.batch_order.sell_all(price='close', volume_check=False, no_quotation='error')
        trade_flag=0

        context.trade_flag = trade_flag

wa = BackTest(init_func = initialize, handle_data_func = handle_data)
res = wa.run(show_progress = True)
nav_df_hedged = wa.summary('nav')
