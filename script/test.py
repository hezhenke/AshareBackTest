from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument):
        strategy.BacktestingStrategy.__init__(self, feed)
        # We want a 15 period SMA over the closing prices.
        self.__sma = ma.SMA(feed[instrument].getCloseDataSeries(), 15)
        self.__instrument = instrument
        self.closep = feed[instrument].getCloseDataSeries()

    def onBars(self, bars):
        a = self.getFeed()
        if(len(bars.keys()) == 2):
            print bars.keys()
            print self.closep.getDateTimes()
            print self.closep2.getDateTimes()
            print len(self.__sma)
        bar = bars[self.__instrument]
        self.info("%s %s" % (bar.getClose(), self.__sma[-1]))


# Load the yahoo feed from the CSV file
feed = yahoofeed.Feed()
feed.addBarsFromCSV("300247", "300247.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed, "300247")
myStrategy.run()