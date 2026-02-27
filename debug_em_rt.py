import requests
import json

def test_eastmoney_rt():
    # 东方财富实时行情 API
    # 101.GC00Y 是 COMEX 黄金
    # fields: f19(结算价), f18(昨收), f2(最新价), f3(涨跌幅), f4(涨跌额), f5(成交量), f6(成交额), f17(今开), f15(最高), f16(最低)
    url = "http://push2.eastmoney.com/api/qt/stock/get?secid=101.GC00Y&fields=f58,f73,f59,f169,f170,f161,f163,f171,f126,f168,f164,f116,f84,f85,f167,f117,f190,f188,f189,f110,f43,f44,f45,f46,f60,f47,f48,f49,f50,f162,f152,f18,f17,f15,f16"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        if data.get('data'):
            d = data['data']
            print("Eastmoney Realtime Data for 101.GC00Y:")
            print(f"Name (f58): {d.get('f58')}")
            print(f"Latest Price (f43/f2): {d.get('f43')}")
            print(f"Open (f46/f17): {d.get('f46')}")
            print(f"High (f44/f15): {d.get('f44')}")
            print(f"Low (f45/f16): {d.get('f45')}")
            print(f"Prev Close (f60/f18): {d.get('f60')}")
            # 期货特有：结算价
            # 在某些 API 中，f18 是昨收，f19 是昨日结算
            # 我们需要找 4950.8 这个数值
            for k, v in d.items():
                if v == 4950.8:
                    print(f"Found 4950.8 in field: {k}")
                if v == 4986.4:
                    print(f"Found 4986.4 in field: {k}")
            
            print("\nAll fields for reference:")
            print(json.dumps(d, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_eastmoney_rt()
