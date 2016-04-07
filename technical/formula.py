# -*- coding:utf-8 -*- 
'''股票软件的股票公式函数实现'''

from pyalgotrade import technical
from pyalgotrade import dataseries

class HighLowEventWindow(technical.EventWindow):
    def __init__(self, windowSize, useMin):
        technical.EventWindow.__init__(self, windowSize)
        self.__useMin = useMin

    def getValue(self):
        ret = None
        if self.windowFull():
            values = self.getValues()
            if self.__useMin:
                ret = values.min()
            else:
                ret = values.max()
        return ret


class HHV(technical.EventBasedFilter):
    """取最大值"""

    def __init__(self, dataSeries, period, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, HighLowEventWindow(period, False), maxLen)


class LLV(technical.EventBasedFilter):
    """取最小值"""

    def __init__(self, dataSeries, period, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, HighLowEventWindow(period, True), maxLen)
        

class HighLowBarsEventWindow(technical.EventWindow):
    def __init__(self, windowSize, useMin):
        technical.EventWindow.__init__(self, windowSize)
        self.__useMin = useMin

    def getValue(self):
        ret = None
        if self.windowFull():
            values = self.getValues()
            vlist = values.tolist()
            vlist.reverse()
            if self.__useMin:
                minv = values.min()
                ret = vlist.index(minv)
            else:
                maxv = values.max()
                ret = vlist.index(maxv)
        return ret
    
class HHVBARS(technical.EventBasedFilter):
    """取最大值位置"""

    def __init__(self, dataSeries, period, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, HighLowBarsEventWindow(period, False), maxLen)


class LLVBARS(technical.EventBasedFilter):
    """取最小值位置"""

    def __init__(self, dataSeries, period, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, HighLowBarsEventWindow(period, True), maxLen)