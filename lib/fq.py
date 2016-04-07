# -*- coding:utf-8 -*- 

import pandas as pd
import json
import numpy as np
import cons as ct
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

def parase_fq_factor(code):
    symbol = _code_to_symbol(code)
    try:
        request = Request(ct.HIST_FQ_FACTOR_URL%(symbol))
        request.add_header("User-Agent", ct.USER_AGENT)
        text = urlopen(request, timeout=20).read()
        text = text[1:len(text)-1]
        text = text.decode('utf-8') if ct.PY3 else text
        text = text.replace('{_', '{"')
        text = text.replace('total', '"total"')
        text = text.replace('data', '"data"')
        text = text.replace(':"', '":"')
        text = text.replace('",_', '","')
        text = text.replace('_', '-')
        text = json.loads(text)
        df = pd.DataFrame({'date':list(text['data'].keys()), 'fqprice':list(text['data'].values())})
        df['date'] = df['date'].map(_fun_except) # for null case
        if df['date'].dtypes == np.object:
            df['date'] = df['date'].astype(np.str)
        df = df.drop_duplicates('date')
        df = df.sort('date', ascending=False)
        df = df.set_index("date")
        df['fqprice'] = df['fqprice'].astype(float)
        return df
    except Exception as e:
        print(e)
        
def _code_to_symbol(code):
    """
        生成symbol代码标志
    """
    if code in ct.INDEX_LABELS:
        return ct.INDEX_LIST[code]
    else:
        if len(code) != 6 :
            return ''
        else:
            return 'sh%s'%code if code[:1] in ['5', '6'] else 'sz%s'%code
        
def _fun_except(x):
    if len(x) > 10:
        return x[-10:]
    else:
        return x