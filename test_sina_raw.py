import requests

def test_sina_data():
    REFERER_HEADER = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://finance.sina.com.cn/"
    }
    SINA_API_URL = "http://hq.sinajs.cn/list="
    
    symbols = ["hf_XAU", "SGE_AU9999"]
    url = f"{SINA_API_URL}{','.join(symbols)}"
    
    try:
        res = requests.get(url, headers=REFERER_HEADER, timeout=5)
        content = res.content.decode('gbk', 'ignore')
        print("Raw Content:")
        print(content)
        
        lines = [l for l in content.split('\n') if l.strip()]
        for line in lines:
            if 'hf_XAU' in line:
                parts = line.split('"')[1].split(',')
                print("\nhf_XAU Parts:")
                for i, p in enumerate(parts):
                    print(f"{i}: {p}")
            elif 'SGE_AU9999' in line:
                parts = line.split('"')[1].split(',')
                print("\nSGE_AU9999 Parts:")
                for i, p in enumerate(parts):
                    print(f"{i}: {p}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sina_data()
