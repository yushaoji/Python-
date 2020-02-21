#海龟策略的核心是头寸管理
#特别是根据盈利选择加仓的力度
#而期货则具有自带杠杆以及双向交易等特点

#标的：沪深300
#频率：日线
#信号：
#1. 根据20日的最高、最低、收盘价计算出ATR
#2. 计算出近十日的最高与最低价
#3. 价格突破2最高时，多单入场
#4. 如果价格继续上涨0.5倍真实波幅则再次加仓
#5. 价格回落2倍真实波幅或者突破10日最低则止损止盈出场
#6. 空仓思想类似


from WindPy import *
from datetime import *
import pandas as pd
import talib as ta
w.start()
from WindAlgo import *

class turtle:
    #交易信号和仓位管理
    def __init__(self, high, low, close, asset, N1 = 20, N2 = 10):
        self.high = high
        self.low = low
        self.close = close
        self.asset = asset
        self.N1 = N1
        self.N2 = N2
        
    def trade_signal(self):
        #唐齐安通道来得到交易信号
        #self.high[:-1]除了最后一天（最近交易日）
        upperband = ta.MAX(self.high[:-1], timeperiod = self.N2)
        lowerband = ta.MIN(self.low[:-1], timeperiod = self.N2)
        self.upperlimit = upperband[-1]
        self.lowerlimit = lowerband[:-1]
        
    def position(self):
        #仓位管理
         vol = ta.ATR(self.high, self.low, self.close, timeperiod = self.N1)
        self.vol = vol[-1]
        unit = max((self.asset * 0.005) / (self.vol * 300 * 0.1), 1)
        #需要交易的单位数量- 手
        self.unit = int(unit)
    
def back_test_turtle(stk_code):
    #回测
    def initialize(context):
        context.capital = 10000000
        context.securities = [stk_code]
        contecontext.start_date = "20150101"        
        context.end_date = "20151110"          
        context.period = 'd'                  
        context.benchmark = stk_code       
        context.order_id = 0                   #用来记录 加仓或者买入的 订单ID
    
    def handle_data(bar_datetime, context, bar_data):
        his = bkt.history(context.se[0], 60)
        high = np.array(his.get_field('high'))
        low = np.array(his.get_field('low'))
        close = np.array(his.get_field('close'))
        #查看总资产
        asset = bkt.query_capital().get_field('total_asset')[0]
        turtle_system = turtle(high, low, close, asset)
        turtle_system.trade_signal()
        turtule_system.position()
        
        #查询当前持仓
        position = bkt.query_position()
        
        #先确认是否有持仓
        #1. 有持仓
         if context.securities[0] in position.get_field('code'):
            last_price = bkt.query_order(context.order_id).get_field('price')[0]  #last_price 上一次买入或加仓的价格
            if position.get_field('side')[0] =='long':
                if  close[-1] > last_price + 0.5 * turtle_system.vol : 
                    '''加多单信号'''
                    res_add = bkt.order(context.securities[0], turtle_system.unit, trade_side='buy',price='close',volume_check=False)
                    context.order_id = res_add['order_id']
                if  close[-1] < last_price - 2*turtle_system.vol :     #last_price 上一次买入或加仓的价格
                    '''多单止损'''
                    res = bkt.batch_order.sell_all()        #清仓处理
                    #如果要做空，先确定是否有仓位
                    #若没有仓位，直接开空仓
                    #若有多仓，先平仓，再开空仓
                    if close[-1] < turtle_system.lowerlimit :
                        res_short = bkt.order(context.securities[0], turtle_system.unit, trade_side='short', price='close',volume_check=False)
                        context.order_id = res_short['order_id']
                if close[-1] < turtle_system.lowerlimit:
                    '''多单止盈'''
                    res = bkt.batch_order.sell_all()
            elif position.get_field('side')[0] =='short':
                if  close[-1] < last_price - 0.5 * turtle_system.vol : 
                    '''加空单信号'''
                    res_add = bkt.order(context.securities[0], turtle_system.unit, trade_side='short',price='close',volume_check=False)
                    context.order_id = res_add['order_id']
                if  close[-1] > last_price + 2*turtle_system.vol :     #last_price 上一次买入或加仓的价格
                    '''空单止损'''
                    res = bkt.batch_order.sell_all()        #清仓处理
                    if close[-1] > turtle_system.upperlimit :
                        res_buy = bkt.order(context.securities[0], turtle_system.unit, trade_side='buy', price='close',volume_check=False)
                        context.order_id = res_buy['order_id']
                if close[-1] > turtle_system.upperlimit:
                    '''空单止盈'''
                    res = bkt.batch_order.sell_all()
        #2. 没有持仓            
        else:
            if close[-1] > turtle_system.upperlimit:
                '''多单买入信号'''
                res_buy = bkt.order(context.securities[0], turtle_system.unit, trade_side='buy', price='close',volume_check=False)
                context.order_id = res_buy['order_id']
            elif close[-1] < turtle_system.lowerlimit:
                '''空单买入信号'''
                res_buy = bkt.order(context.securities[0], turtle_system.unit, trade_side='short', price='close',volume_check=False)
                context.order_id = res_buy['order_id']

    bkt = BackTest(init_func = initialize, handle_data_func=handle_data) #实例化回测对象
    res = bkt.run(show_progress=True) #调用run()函数开始回测,show_progress可用于指定是否显示回测净值曲线图
    nav_df=bkt.summary('nav') #获取回测结果

backtest_turtle('IF.CFE')
