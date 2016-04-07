INDEX_LABELS = ['sh', 'sz', 'hs300', 'sz50', 'cyb', 'zxb']
INDEX_LIST = {'sh': 'sh000001', 'sz': 'sz399001', 'hs300': 'sz399300',
              'sz50': 'sh000016', 'zxb': 'sz399005', 'cyb': 'sz399006'}
HIST_FQ_FACTOR_URL = 'http://vip.stock.finance.sina.com.cn/api/json.php/BasicStockSrv.getStockFuQuanData?symbol=%s&type=hfq'
import sys
PY3 = (sys.version_info[0] >= 3)
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"
