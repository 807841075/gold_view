import subprocess
import json

def test_webclient(url):
    ps_script = f"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    try {{
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        $wc.Headers.Add("Referer", "https://quote.eastmoney.com/")
        $output = $wc.DownloadString("{url}")
        Write-Output $output
    }} catch {{
        Write-Host "PS_ERROR: $($_.Exception.Message)"
        exit 0
    }}
    """
    
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script]
    print(f"Testing URL with WebClient: {url}")
    
    result = subprocess.run(cmd, capture_output=True)
    stdout = result.stdout.decode('utf-8', errors='ignore')
    
    if "PS_ERROR" in stdout:
        print(f"Error: {stdout}")
    elif stdout.strip():
        print("Success!")
        print(stdout[:500] + "...")
    else:
        print("Failed with empty output")

if __name__ == "__main__":
    test_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&ut=fa5fd1943c41138ebe.0b69&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=1&fqt=1&end=20500101&lmt=120"
    test_webclient(test_url)
