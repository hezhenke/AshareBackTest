# -*- coding:utf-8 -*- 
from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
import os
import datetime
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import returns

class TestPositionStrategy(strategy.BacktestingStrategy):
    
    def __init__(self,start=None,end=None):
        ''' load all the ashare feed'''
        project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_root_dir = os.path.join(project_root_dir,"data","history")
        feed = yahoofeed.Feed()
        for _,_,filenames in os.walk(data_root_dir):
            for filename in filenames:
                if os.path.splitext(filename)[1] == '.csv':
                    stock_code = os.path.splitext(filename)[0]
                    csvfile = os.path.join(data_root_dir, filename)
                    feed.addBarsFromCSV(stock_code, csvfile)
        strategy.BacktestingStrategy.__init__(self, feed)
        self.setUseAdjustedValues(True)
        self._feed = self.getFeed()
        self._universe = []
        self._start_date = None
        self._end_date = None
        if start is not None:
            self._start_date = datetime.datetime.strptime(start,'%Y-%m-%d')
        if end is not None:
            self._end_date = datetime.datetime.strptime(end,'%Y-%m-%d')
            
        self.__instruments = self._feed.getRegisteredInstruments()
        self.__sma = {}
        self.__prices = {}
        self.__position = {}
        'add the techical indectitor to the feed'
        for instrument in self.__instruments:
            self.__sma[instrument] = ma.SMA(self._feed[instrument].getCloseDataSeries(), 15)
            self.__prices[instrument] = self._feed[instrument].getPriceDataSeries()
            self.__position[instrument] = None
    def getSMA(self):
        return self.__sma
    def before_trading(self,bars):
        '''更新股票池'''
        pass
    def handle_data(self,bars):
        for instrument in bars.getInstruments():
            # If a position was not opened, check if we should enter a long position.
            if self.__position[instrument] is None:
                if cross.cross_above(self.__prices[instrument], self.__sma[instrument]) > 0:
                    shares = int(self.getBroker().getCash() * 0.9 / bars[instrument].getPrice())
                    # Enter a buy market order. The order is good till canceled.
                    self.__position[instrument] = self.enterLong(instrument, shares, True)
            # Check if we have to exit the position.
            elif not self.__position[instrument].exitActive() and cross.cross_below(self.__prices[instrument], self.__sma[instrument]) > 0:
                self.__position[instrument].exitMarket()
    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        instrument = position.getInstrument()
        self.info("BUY %s at ￥%.2f" % (instrument,execInfo.getPrice()))
    def onEnterCanceled(self, position):
        instrument = position.getInstrument()
        if instrument is not None:
            self.__position[instrument] = None
            self.info("sell %s " % (instrument))

    def onExitOk(self, position):
        instrument = position.getInstrument()
        if instrument is not None:
            self.__position[instrument] = None

    def onExitCanceled(self, position):
        instrument = position.getInstrument()
        if instrument is not None:
            self.__position[instrument].exitMarket()
    
    def onBars(self, bars):
        current_date = bars.getDateTime()
        if self._start_date is not None and current_date < self._start_date:
            return
        if self._end_date is not None and current_date > self._end_date:
            return
        self.before_trading(bars)
        self.handle_data(bars)
    def get_bardict(self):
        pass
    def update_universe(self,instruments):
        self._universe = instruments
    
    def history(self,instrument,field,period):
        assert(type(period) is int)
        assert(period > 0)
        bards = self._feed.getDataSeries(instrument)
        if field == 'open':
            ds = bards.getOpenDataSeries()
        elif field == 'high':
            ds = bards.getHighDataSeries()
        elif field == 'low':
            ds = bards.getLowDataSeries()
        elif field == 'close':
            ds = bards.getCloseDataSeries()
        elif field == 'adjclose':
            ds = bards.getAdjCloseDataSeries()
        elif field == 'volume':
            ds = bards.getVolumeDataSeries()
        else:
            ds = bards.getPriceDataSeries()
        return ds[-period:]
    
    
if __name__ == '__main__':
    st = TestPositionStrategy('2015-02-25','2016-04-03')
    


    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    st.attachAnalyzer(returnsAnalyzer)
    
    # Attach the plotter to the strategy.
    plt = plotter.StrategyPlotter(st)
    # Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
    #plt.getInstrumentSubplot("orcl").addDataSeries("SMA", st.getSMA())
    # Plot the simple returns on each bar.
    plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    st.run()
    st.info("Final portfolio value: $%.2f" % st.getResult())

    # Plot the strategy.
    plt.plot()