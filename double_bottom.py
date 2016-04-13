# -*- coding:utf-8 -*- 
from strategy import TroyStrategy
from pyalgotrade.talibext import indicator
import pandas as pd
import numpy as np

from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.broker import Order
from pyalgotrade.technical import ma

class DoubleBottomStrategy(TroyStrategy):
    def __init__(self,start,end):
        TroyStrategy.__init__(self,start,end)
        self.__instruments = self._feed.getRegisteredInstruments()
        self.__position = {}
        self.__stop_loss_price = {}
        'add the techical indectitor to the feed'
        self.__indexSma60 = ma.SMA(self._feed['sh'].getPriceDataSeries(), 60)
        self.__indexSma10 = ma.SMA(self._feed['sh'].getPriceDataSeries(), 10)
        self.__hasRisk = False
        for instrument in self.__instruments:
            self.__position[instrument] = None
        
        
    def before_trading(self, bars):
        active_instruments = bars.getInstruments()
        selected_instruments = self.select_instruments(active_instruments, 30)
        
        self.update_universe(selected_instruments)
        self.info("select double bottom stock:%s"%(selected_instruments))
    def handle_data(self, bars,instruments):
        #stop_loss
        #self.stop_loss(bars)
        '''risk management''' 
        self.risk_management(bars)
        if self.__hasRisk:
            return
        #stop_earn
        #self.stop_earn(bars)
        #drop the stock was already in the poforlio
        instruments = self.filter_stock_to_buy(instruments)
        
        if len(instruments) == 0:
            return None
        position = self.getBroker().getPositions()
        
        left_poition_num = 5 - len(position)
        
        if left_poition_num <= 0:
            return None
        
        elif left_poition_num < len(instruments):
            buy_instruments = instruments[0:left_poition_num]
        else:
            buy_instruments = instruments
        
        for instrument in buy_instruments:
            if self.__position[instrument] is None:
                #calculate the cash for each stock
                shares = int(self.getBroker().getCash()*0.9 /left_poition_num / bars[instrument].getPrice())/100*100
                # Enter a buy market order. The order is good till canceled.
                if shares >= 100:
                    self.__position[instrument] = self.enterLong(instrument, shares, True)
    
    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        instrument = position.getInstrument()
        self.info("BUY %s at $%.2f" % (instrument,execInfo.getPrice()))
        ''' stop loss order '''
        stopPrice = self.__stop_loss_price[instrument] * (1-0.04)
        position.exitStop(stopPrice,True)
        
    def onEnterCanceled(self, position):
        instrument = position.getInstrument()
        if instrument is not None:
            self.__position[instrument] = None
            self.info("SELL %s " % (instrument))

    def onExitOk(self, position):
        exitOrder = position.getExitOrder()
        instrument = position.getInstrument()
        execInfo = exitOrder.getExecutionInfo()
        if exitOrder.getType() == Order.Type.STOP and instrument is not None:
            self.__position[instrument] = None
            self.info("stop loss,SELL %s at $%.2f" % (instrument,execInfo.getPrice()))
        elif exitOrder.getType() == Order.Type.MARKET and instrument is not None:
            self.__position[instrument] = None
            self.info("stop earn,SELL %s at $%.2f" % (instrument,execInfo.getPrice()))
        else:
            self.__position[instrument] = None
            self.info("SELL %s at $%.2f" % (instrument,execInfo.getPrice()))
            
            

    def onExitCanceled(self, position):
        
        instrument = position.getInstrument()
        if instrument is not None:
            self.__position[instrument].exitMarket()
    
    def risk_management(self,bars):
        indexPrice = bars['sh'].getPrice()
        if indexPrice < self.__indexSma60[-1]:
            self.__hasRisk = True
            position = self.getBroker().getPositions()
            for instrument,shares in position.items():
                if shares > 0 and self.__position[instrument] is not None:
                    self.info("risk control,SELL %s" % (instrument))
                    if self.__position[instrument].exitActive():
                        self.__position[instrument].cancelExit()
                    else:
                        self.__position[instrument].exitMarket()
        elif self.__hasRisk == True and indexPrice > self.__indexSma60[-1]:
            self.__hasRisk = False
            self.info("Risk release,Recover trade")
        else:
            pass
            
            
    def stop_loss(self,bars):
        positions = self.getBroker().getPositions()
        active_instruments = bars.getInstruments()
        for instrument in positions.keys():
            if instrument not in active_instruments:
                continue
            last_price = bars[instrument].getPrice() 
            stop_loss_price = self.__stop_loss_price[instrument]
            if (last_price - stop_loss_price)/stop_loss_price <= -0.04 and not self.__position[instrument].exitActive() :
                self.info("stop loss:%s,stop_loss_price:$%.2f"%(instrument,self.__stop_loss_price[instrument]))
                self.__position[instrument].exitMarket()
            
                
    def stop_earn(self,bars):
        positions = self.getBroker().getPositions()
        active_instruments = bars.getInstruments()
        for instrument in positions.keys():
            if instrument not in active_instruments:
                continue
            instrument_return = self.__position[instrument].getReturn()
            age = self.__position[instrument].getAge()
            hold_days = int(age.days)
            
            '''time stop earn'''
            if (hold_days > 10 and instrument_return < 0.05) \
            or (hold_days > 20 and instrument_return < 0.15) \
            or (hold_days > 30 and instrument_return < 0.2) \
            or instrument_return > 0.3 :
                
                if  not self.__position[instrument].exitActive():
                    last_price = bars[instrument].getPrice()
                    self.info("time top earn:%s,close price:%.2f"%(instrument,last_price))
                    self.__position[instrument].exitMarket()
                else:
                    last_price = bars[instrument].getPrice()
                    self.info("cancel and time top earn:%s,close price:%.2f"%(instrument,last_price))
                    self.__position[instrument].cancelExit()
                    
                    
            '''normal stop earn'''
            '''
            period = 5
            if hold_days > 5:
                period = hold_days
            last_price = self.__position[instrument].getLastPrice()
            hist_h = self.history(instrument, "high", period)
            high_price = max(hist_h)
            if (high_price - last_price)/high_price > 0.15 and not self.__position[instrument].exitActive():
                self.info("stop earn:%s,close price:%.2f"%(instrument,last_price))
                self.__position[instrument].exitMarket()
            '''
            
    def filter_stock_to_buy(self,instruments):
        positions = self.getBroker().getPositions()
        return [instrument for instrument in instruments if instrument not in positions.keys()]
    
    ''' user function '''
    def count_limit_up(self,hist_close_arr):
        pre_close_price = hist_close_arr[0]
        limit_up_count = 0
        for close_price in hist_close_arr:
            if close_price/pre_close_price >1.097:
                limit_up_count = limit_up_count + 1
            pre_close_price = close_price
        return limit_up_count


            
        
    def get_trough(self,instrument):
        
        hist_l = self.history(instrument,'low',200)
        zig = ZigZag()
        pivots = zig.peak_valley_pivots(hist_l, 0.15, -0.15)
        ts_pivots = pd.Series(hist_l)
        ts_pivots = ts_pivots[pivots == ZigZag.VALLEY]
        trough = np.array([v for v in ts_pivots])
        troughbars = np.array([ i for i in ts_pivots.index])
        return trough,troughbars        
        
    def select_instruments(self,instruments,period):
        
        selected_instruments = []
        for instrument in instruments:
            hist_h = self.history(instrument, 'high', period)
            hist_l = self.history(instrument, 'low', period)
            hist_c = self.history(instrument, 'close', period)
            hist_o = self.history(instrument, 'open', period)
            hist_v = self.history(instrument, 'volume', period)
            '''
            {
            30个交易日内最低点到最高点涨幅超过50%,30日内最少有两个涨停板，上市日期超过60日
            }
            HP:=HHV(HIGH,N);{N日内最高价}
            LP:=LLV(LOW,N);{30日内最低价}
            HD:=HHVBARS(HIGH,N);{出现最高价离现在的时间}
            LD:=LLVBARS(LOW,N);{出现最低价离现在的时间}
            
            OP1 := ((HP-LP)/LP > M/100);{N内涨幅超过M%}
            OP2 := (COUNT(CLOSE/REF(CLOSE,1)>1.097,N)>=2);{N日内出现2个以上涨停板}
            OP3 :=  LD>HD;{30日内最低点出现在最高点前面}
            OP4 := (BARSCOUNT(C)+1)>60;{排除最近60天上市的次新股}
            OP5 := DYNAINFO(4)>0;
            
            条件选股:OP1 AND OP2 AND OP3 AND OP4 AND OP5;
            '''
            hp_arr = indicator.MAX(hist_h,period)
            hp = hp_arr[-1]
            
            lp_arr = indicator.MIN(hist_l,period)
            lp = lp_arr[-1]
            
            hd_arr = indicator.MAXINDEX(hist_h,period)
            ld_arr = indicator.MININDEX(hist_l,period)
            
            hd = len(hist_h) - hd_arr[-1]
            ld = len(hist_l) - ld_arr[-1]
            
            if (hp-lp)/lp < 0.4:
                continue
            
            
            if self.count_limit_up(hist_c) < 2:
                continue
            if hd > ld:
                continue
            
            last_open = hist_o[-1]
            last_close = hist_c[-1]
            pre_last_close = hist_c[-2]
            
            raise_percent = (pre_last_close - last_close)/pre_last_close
            raise_percent2 = (last_close - last_open)/last_open
            
            if raise_percent > 0.03 or raise_percent < -0.03:
                continue
            
            if raise_percent2 > 0.03 or raise_percent2 < -0.02:
                continue
            
            
            
            
            
            '''
            OP1 := ABS((LOW-TROUGH(2,15,1))/TROUGH(2,15,1))<=0.03;
            OP11 := ABS((LOW-TROUGH(2,15,2))/TROUGH(2,15,2))<=0.03  AND (TROUGH(2,15,2) <= TROUGH(2,15,1));
            OP111 := ABS((LOW-TROUGH(2,15,3))/TROUGH(2,15,3))<=0.03 AND (TROUGH(2,15,3) <= TROUGH(2,15,1));
            OP2 := V < MA(V,30) OR V < HHV(V,30)/3;
            OP3 := TROUGHBARS(2,15,1) > 3;
            条件选股:(OP1 OR OP11 OR OP111)  AND OP2 AND OP3;
            '''
            
            ma_volume = indicator.MA(hist_v,period)
            max_volume = indicator.MAX(hist_v,period)
            
            if hist_v[-1] >= ma_volume[-1] and hist_v[-1] >= max_volume[-1]/3:
                continue
            trough,troughbars = self.get_trough(instrument)
            
            
            if len(trough) == 0 or len(troughbars) == 0:
                continue
            
            if troughbars[0] <= 3:
                continue
            
            last_low = hist_l[-1]
            
            op1 = abs((last_low - trough[0])/trough[0]) <= 0.03
            op2 = len(trough) >=2 and abs((last_low - trough[1])/trough[1]) <= 0.03
            op3 = len(trough) >=3 and abs((last_low - trough[2])/trough[2]) <= 0.03
            
            
            if op1:
                self.__stop_loss_price[instrument] = trough[0]
            else:
                continue
            '''
            elif op2:
                self.__stop_loss_price[instrument] = trough[1]
            elif op3:
                self.__stop_loss_price[instrument] = trough[2]
            '''
                
            
            
            selected_instruments.append(instrument)
        return selected_instruments

class ZigZag(object):
    PEAK, VALLEY = 1, -1
    
    def _identify_initial_pivot(self,X, up_thresh, down_thresh):
        """Quickly identify the X[0] as a peak or valley."""
        x_0 = X[0]
        max_x = x_0
        max_t = 0
        min_x = x_0
        min_t = 0
        up_thresh += 1
        down_thresh += 1
    
        for t in range(1, len(X)):
            x_t = X[t]
    
            if x_t / min_x >= up_thresh:
                return ZigZag.VALLEY if min_t == 0 else ZigZag.PEAK
    
            if x_t / max_x <= down_thresh:
                return ZigZag.PEAK if max_t == 0 else ZigZag.VALLEY
    
            if x_t > max_x:
                max_x = x_t
                max_t = t
    
            if x_t < min_x:
                min_x = x_t
                min_t = t
    
        t_n = len(X)-1
        return ZigZag.VALLEY if x_0 < X[t_n] else ZigZag.PEAK
    
    def peak_valley_pivots(self,X, up_thresh, down_thresh):
        """
        Finds the peaks and valleys of a series.
        """
        if down_thresh > 0:
            raise ValueError('The down_thresh must be negative.')
        X.reverse()
        initial_pivot = self._identify_initial_pivot(X, up_thresh, down_thresh)
    
        t_n = len(X)
        pivots = np.zeros(t_n, dtype='i1')
        pivots[0] = initial_pivot
    
    
        up_thresh += 1
        down_thresh += 1
    
        trend = -initial_pivot
        last_pivot_t = 0
        last_pivot_x = X[0]
        for t in range(1, len(X)):
            x = X[t]
            r = x / last_pivot_x
    
            if trend == -1:
                if r >= up_thresh:
                    pivots[last_pivot_t] = trend
                    trend = 1
                    last_pivot_x = x
                    last_pivot_t = t
                elif x < last_pivot_x:
                    last_pivot_x = x
                    last_pivot_t = t
            else:
                if r <= down_thresh:
                    pivots[last_pivot_t] = trend
                    trend = -1
                    last_pivot_x = x
                    last_pivot_t = t
                elif x > last_pivot_x:
                    last_pivot_x = x
                    last_pivot_t = t
    
        if last_pivot_t == t_n-1:
            pivots[last_pivot_t] = trend
        elif pivots[t_n-1] == 0:
            pivots[t_n-1] = -trend
    
        return pivots
    
if __name__ == '__main__':
    st = DoubleBottomStrategy('2013-05-25','2016-04-08')
    
    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    st.attachAnalyzer(returnsAnalyzer)
    
    # Attach the plotter to the strategy.
    plt = plotter.StrategyPlotter(st,False)
    # Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
    #plt.getInstrumentSubplot("orcl").addDataSeries("SMA", st.getSMA())
    # Plot the simple returns on each bar.
    plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    st.run()
    st.info("Final portfolio value: $%.2f" % st.getResult())
    
    fig = plt.buildFigure()
    fig.savefig("/tmp/test.png")
    # Plot the strategy
    #plt.plot()