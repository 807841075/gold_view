import subprocess
import json
import sys

def test_powershell_fetch(url):
    host = "push2his.eastmoney.com"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    
    headers_dict = f"""
    $headers = @{{
        'Accept' = '*/*'
        'Accept-Language' = 'zh-CN,zh;q=0.9,en;q=0.8'
        'Cache-Control' = 'no-cache'
        'Connection' = 'keep-alive'
        'Pragma' = 'no-cache'
        'Referer' = 'https://quote.eastmoney.com/'
        'Host' = '{host}'
        'Sec-Fetch-Dest' = 'empty'
        'Sec-Fetch-Mode' = 'cors'
        'Sec-Fetch-Site' = 'same-site'
    }}
    """
    
    ps_script = f"""
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    {headers_dict}
    try {{
        $resp = Invoke-WebRequest -Uri '{url}' -Headers $headers -UserAgent '{user_agent}' -Method Get -UseBasicParsing
        $resp.Content
    }} catch {{
        Write-Host "PS_ERROR: $($_.Exception.Message)"
        exit 0
    }}
    """
    
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script]
    print(f"Testing URL: {url}")
    
    # Try to run without specifying encoding first, then decode manually
    result = subprocess.run(cmd, capture_output=True)
    
    # Try decoding with gbk (common on Chinese Windows PS)
    try:
        stdout = result.stdout.decode('gbk')
        stderr = result.stderr.decode('gbk')
    except:
        stdout = result.stdout.decode('utf-8', errors='ignore')
        stderr = result.stderr.decode('utf-8', errors='ignore')

    if "PS_ERROR" in stdout:
        print(f"PowerShell logic error: {stdout}")
    elif result.returncode == 0 and stdout.strip():
        print("Success!")
        print(stdout[:500] + "...")
    else:
        print("Failed!")
        print(f"Exit Code: {result.returncode}")
        print(f"Stderr: {stderr}")

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_powershell_fetch(test_url)
