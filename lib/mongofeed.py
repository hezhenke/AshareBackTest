# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

from pyalgotrade.barfeed import dbfeed
from pyalgotrade.barfeed import membf
from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade.utils import dt
import datetime


from pymongo import MongoClient
import cons as ct




def normalize_instrument(instrument):
    return instrument


# SQLite DB.
# Timestamps are stored in UTC.
class Database(dbfeed.Database):
    def __init__(self):
        self.host = ct.MONGO_HOST
        self.port = ct.MONGO_PORT
        self.database = ct.MONGO_DATABASE
        self.history_data_collect = ct.MONGO_HIST_COLLECTION
        self.stock_list_collect = ct.MONGO_STOCK_LIST_COLLECTION
        self.max_pool_size = 10
        self.timeout = 10
        
        self.__instrumentIds = {}
        try:
            self.__connection = MongoClient(self.host, self.port, maxPoolSize=self.max_pool_size,
                                            connectTimeoutMS=60 * 60 * self.timeout)
        except Exception as e:
            print(e)

    def __findInstrumentId(self, instrument):
        pass

    def __addInstrument(self, instrument):
        pass

    def __getOrCreateInstrument(self, instrument):
        pass

    

    def addBar(self, instrument, bar, frequency):
        pass

    def getBars(self, instrument, frequency,  fromDateTime=None, toDateTime=None,timezone=None):
        instrument = normalize_instrument(instrument)
        
        args = {}
        args['code'] = instrument
        

        if fromDateTime is not None:
            args['date'] = {"$gte":fromDateTime}
        if toDateTime is not None:
            if args.has_key('date'):
                args['date']['$lte'] = toDateTime
            else:
                args['date'] = {"$lte":toDateTime}

        cursor = self.__connection[self.database][self.history_data_collect].find(args).sort("date")
        ret = []
        for row in cursor:
            dateTime = datetime.datetime.strptime(row['date'],'%Y-%m-%d')
            ret.append(bar.BasicBar(dateTime, row['open'], row['high'], row['low'], row['close'], row['volume'], row['adjclose'],frequency))
        return ret
    def getAllBars(self,frequency,  fromDateTime=None, toDateTime=None,timezone=None):
        
        args = {}
        if fromDateTime is not None:
            args['date'] = {"$gte":fromDateTime}
        if toDateTime is not None:
            if args.has_key('date'):
                args['date']['$lte'] = toDateTime
            else:
                args['date'] = {"$lte":toDateTime}
        cursor = self.__connection[self.database][self.history_data_collect].find(args).sort("date")
        barsDict = {}
        for row in cursor:
            code = str(row['code'])
            if not barsDict.has_key(code):
                barsDict.setdefault(code,[])
                
            dateTime = datetime.datetime.strptime(row['date'],'%Y-%m-%d')
            barsDict[code].append(bar.BasicBar(dateTime, row['open'], row['high'], row['low'], row['close'], row['volume'], row['adjclose'],frequency)) 
        return barsDict
    
    def getStockList(self):
        stock_list = self.__connection[self.database][self.stock_list_collect].find({},{"code":1}).distinct("code")
        return [str(stock) for stock in stock_list]
    def disconnect(self):
        pass


class Feed(membf.BarFeed):
    def __init__(self, fromDateTime=None, toDateTime=None,timezone=None,frequency=bar.Frequency.DAY,maxLen=dataseries.DEFAULT_MAX_LEN):
        if frequency not in [bar.Frequency.DAY]:
            raise Exception("Invalid frequency.")
        membf.BarFeed.__init__(self, frequency, maxLen)
        self.__db = Database()
        self.__fromDateTime = fromDateTime
        self.__toDateTime = toDateTime
        self.__timezone = timezone
    def barsHaveAdjClose(self):
        return True

    def getDatabase(self):
        return self.__db
    def getStockList(self):
        return self.__db.getStockList()

    def loadBars(self, instrument):
        bars = self.__db.getBars(instrument, self.getFrequency(), self.__fromDateTime, self.__toDateTime, self.__timezone)
        self.addBarsFromSequence(instrument, bars)
    
    def loadAllBars(self,includeInstruments=None):
        barsDict = self.__db.getAllBars(self.getFrequency(), self.__fromDateTime, self.__toDateTime, self.__timezone)
        for instrument,bars in barsDict.items():
            if includeInstruments is not None and instrument not in includeInstruments:
                continue
            self.addBarsFromSequence(instrument, bars)
        
        
if __name__ == '__main__':
    feed = Feed("2015-01-01", "2016-04-08")
    #mongofeed.loadBars("600085")
    #mongofeed.loadBars("600750")
    
    print feed.getStockList()
    feed.loadAllBars()
    
    for date,bars in feed:
        instruments = bars.getInstruments()
        for inst in instruments:
            print date,inst,bars[inst].getClose()
    
    
