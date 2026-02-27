import urllib.request
import ssl
import json
import subprocess

def test_custom_ssl_fingerprint(url):
    print("\n--- Testing Custom SSL Fingerprint ---")
    # 模拟 Chrome 的加密套件
    context = ssl.create_default_context()
    context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
    context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://quote.eastmoney.com/',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            data = response.read()
            # 处理可能存在的 gzip
            if response.info().get('Content-Encoding') == 'gzip':
                import gzip
                data = gzip.decompress(data)
            text = data.decode('utf-8')
            if '"data"' in text:
                print("Success with Custom SSL Fingerprint!")
                return True
    except Exception as e:
        print(f"Custom SSL failed: {e}")
    return False

def test_winhttp_com(url):
    print("\n--- Testing WinHTTP COM ---")
    # WinHTTP 是 Windows 系统原生组件，常用于绕过脚本指纹检测
    ps_script = f"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    try {{
        $request = New-Object -ComObject WinHttp.WinHttpRequest.5.1
        $request.Open("GET", "{url}", $false)
        $request.SetRequestHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        $request.SetRequestHeader("Referer", "https://quote.eastmoney.com/")
        $request.SetRequestHeader("Accept", "*/*")
        $request.Send()
        Write-Output $request.ResponseText
    }} catch {{
        Write-Host "PS_ERROR: $($_.Exception.Message)"
    }}
    """
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if '"data"' in result.stdout:
            print("Success with WinHTTP!")
            return True
        else:
            print(f"WinHTTP failed: {result.stdout[:100]}")
    except Exception as e:
        print(f"WinHTTP error: {e}")
    return False

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    if not test_custom_ssl_fingerprint(test_url):
        test_winhttp_com(test_url)
