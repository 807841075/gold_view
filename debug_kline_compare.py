import requests
import json

def get_sina_hf_gc():
    url = "http://hq.sinajs.cn/list=hf_GC"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn/"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        content = res.content.decode('gbk', 'ignore')
        print("Sina hf_GC Raw:")
        print(content)
        if '"' in content:
            data = content.split('"')[1].split(',')
            print(f"Sina Index 7 (Prev Close): {data[7] if len(data)>7 else 'N/A'}")
            print(f"Sina Index 2 (Latest): {data[2] if len(data)>2 else 'N/A'}")
    except Exception as e:
        print(f"Sina Error: {e}")

def get_hf_gc_alt():
    # 测试一些其它的 COMEX 黄金代码
    symbols = ["hf_GC", "hf_XAU", "hf_XAG"]
    for sym in symbols:
        url = f"http://hq.sinajs.cn/list={sym}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            content = res.content.decode('gbk', 'ignore')
            if '"' in content:
                data = content.split('"')[1].split(',')
                print(f"{sym} Prev Close (Index 7): {data[7] if len(data)>7 else 'N/A'}")
        except: pass

def get_sina_kline_specific(symbol):
    url = f"https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var_k=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol={symbol}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        content = res.text
        if '(' in content and ')' in content:
            json_str = content[content.find('(')+1 : content.rfind(')')]
            data = json.loads(json_str)
            if data and isinstance(data, list):
                # 寻找 2026-02-04 的数据
                target = next((k for k in data if k.get('date') == '2026-02-04'), None)
                if target:
                    print(f"Sina {symbol} 2026-02-04 Close: {target.get('close')}")
                else:
                    print(f"Sina {symbol} 2026-02-04 not found")
    except: pass

def get_eastmoney_variants():
    # 测试一些变体
    secids = ["101.GC0Y", "101.GC", "101.GC00Y"]
    for secid in secids:
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=101&fqt=1&end=20500101&lmt=5"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            if data.get('data'):
                k = data['data']['klines'][-2] # 2.4 的数据
                print(f"Eastmoney {secid} 2026-02-04: {k}")
        except: pass

def get_eastmoney_markets():
    # 测试所有可能的市场前缀
    for m in range(101, 110):
        secid = f"{m}.GC00Y"
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=101&fqt=1&end=20500101&lmt=5"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            if data.get('data'):
                k = data['data']['klines'][-2] # 2.4 的数据
                print(f"Eastmoney {secid} 2026-02-04: {k}")
        except: pass

def get_eastmoney_fqt():
    # 测试不同的复权方式
    for fqt in [0, 1, 2]:
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=101.GC00Y&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=101&fqt={fqt}&end=20500101&lmt=5"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            if data.get('data'):
                k = data['data']['klines'][-2] # 2.4 的数据
                print(f"Eastmoney fqt={fqt} 2026-02-04: {k}")
        except: pass

def get_eastmoney_xau():
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=101.XAU&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=101&fqt=1&end=20500101&lmt=5"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        if data.get('data'):
            k = data['data']['klines'][-2] # 2.4 的数据
            print(f"Eastmoney 101.XAU 2026-02-04: {k}")
    except: pass

def get_eastmoney_full_fields(secid="101.GC00Y"):
    # 请求更多字段以寻找结算价
    fields2 = ",".join([f"f{i}" for i in range(51, 80)])
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2={fields2}&klt=101&fqt=1&beg=0&end=20500101"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if data and data.get("data") and data["data"].get("klines"):
            last_k = data["data"]["klines"][-2:] # 取最后两天对比
            print(f"\n--- Eastmoney {secid} Full Fields (Last 2 days) ---")
            for k in last_k:
                parts = k.split(',')
                print(f"Data: {parts}")
                # 打印索引以方便对照
                # for i, val in enumerate(parts):
                #    print(f"  Index {i} (f{51+i}): {val}")
    except Exception as e:
        print(f"Error fetching EM full fields: {e}")

if __name__ == "__main__":
    get_eastmoney_full_fields("101.GC00Y")
    # 也看看具体的合约，比如 GC2604
    # get_eastmoney_full_fields("102.GC2604") 
