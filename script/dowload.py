# -*- coding:utf-8 -*- 

import sys
sys.path.append("..")

import struct
import pandas as pd
import datetime
import numpy as np
import threadpool
import lib.fq as fq
import lib.trading as td



tdx_base_dir = 'D:/new_tdx/vipdoc'
def get_tdx_data(symbol):
    file_path = '%s/sh/lday/sh%s.day'%(tdx_base_dir,symbol) \
    if symbol[:1] in ['5', '6'] else '%s/sz/lday/sz%s'%(tdx_base_dir,symbol)
    fid=open(file_path,"rb");
    ulist = []
    try:
        while True:
            chunk = fid.read(32)
            if not chunk:
                break
            chunk_list = list(struct.unpack("iiiiifii", chunk))
            num = int(chunk_list[0])
            year=num/10000
            month=num%10000/100
            day=num%100
            chunk_list[0] = datetime.date(year,month,day)
            chunk_list[1] = float(chunk_list[1])/100
            chunk_list[2] = float(chunk_list[2])/100
            chunk_list[3] = float(chunk_list[3])/100
            chunk_list[4] = float(chunk_list[4])/100
            ulist.append(chunk_list[:-1])
    finally:
        fid.close()
    df = pd.DataFrame(ulist,columns=['Date','Open','High','Low','Close','Amout','Volume'])
    df = df.drop_duplicates("Date")
    df['Date'] = df['Date'].astype(np.str)
    df = df.sort('Date', ascending=False)
    df = df.set_index("Date")   
    return df


    
def get_adj_rate(code,tdx_df,fuquan_df):
    last_date = tdx_df.index[0]
    if last_date not in fuquan_df.index:
        return None

    rate = float(fuquan_df.loc[last_date,'fqprice']) / tdx_df.loc[last_date,'Close']
    return rate

def get_hist_data(code):
    df = get_tdx_data(code)
    
    #get the fuquan data
    fuquan_df = fq.parase_fq_factor(code)
    if not isinstance(fuquan_df, pd.DataFrame):
        return None
    
    #add two columns 
    df.insert(len(df.columns), "Adj Close",0)
    rate = get_adj_rate(code,df,fuquan_df)
    for date in df.index:
        if date not in fuquan_df.index:
            df = df.drop(date)
            continue
        df.loc[date,'Adj Close'] = round(fuquan_df.loc[date,'fqprice']/rate,2)
    return df

def callback(request, result):
    symbol = request.args[0]
    csvFile = "../data/%s.csv"%(symbol)
    if result is not None:
        result.to_csv(csvFile,columns=['Open','High','Low','Close','Volume','Adj Close'])

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
