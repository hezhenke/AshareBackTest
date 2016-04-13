from lib import mongofeed
import threadpool




def run():
    
    feed = mongofeed.Feed("2015-01-01", "2016-04-09")
    stock_list = feed.getStockList()
    thread_num = 100    
    pool = threadpool.ThreadPool(thread_num) 
    requests = threadpool.makeRequests(feed.loadBars, stock_list) 
    [pool.putRequest(req) for req in requests] 
    pool.wait()
    pool.dismissWorkers(thread_num, do_join=True)
    
    for date,bars in feed:
        instruments = bar.getInstruments()
        for inst in instruments:
            print date,inst,bar[inst].getClose()
    

if __name__ == '__main__':
    run()