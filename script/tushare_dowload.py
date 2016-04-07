# -*- coding:utf-8 -*- 
import sys
sys.path.append("..")
import tushare as ts
import threadpool
import lib.trading as td
from datetime import datetime

_start_ = '2005-01-01'
_end_ = datetime.now().strftime('%Y-%m-%d')


def callback(request, result):
    symbol = request.args[0]
    csvFile = "../data/history/%s.csv"%(symbol)
    if result is not None:
        result.to_csv(csvFile,columns=['open','high','low','close','volume','close'],header=['Open','High','Low','Close','Volume','Adj Close'],index_label='Date')
def get_hist_data(code):
    df = ts.get_hist_data(str(code),start=_start_,end=_end_)
    return df
    
def run():
    
    stock_list = td.get_stock_hq_list()
    data = stock_list['code'].tolist()
    thread_num = 100    
    pool = threadpool.ThreadPool(thread_num) 
    requests = threadpool.makeRequests(get_hist_data, data, callback) 
    [pool.putRequest(req) for req in requests] 
    pool.wait()
    pool.dismissWorkers(thread_num, do_join=True)
    

if __name__ == '__main__':
    run()