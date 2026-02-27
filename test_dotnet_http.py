import subprocess
import json

def test_dotnet_http():
    print("\n--- Testing .NET HttpClient via PowerShell ---")
    
    # PowerShell script to use HttpClient with browser-like headers
    ps_script = """
Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.DefaultRequestHeaders.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
$client.DefaultRequestHeaders.Add("Referer", "https://quote.eastmoney.com/")
$client.DefaultRequestHeaders.Add("Accept", "*/*")

$url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"

try {
    $response = $client.GetAsync($url).Result
    $content = $response.Content.ReadAsStringAsync().Result
    Write-Output $content
} catch {
    Write-Error $_.Exception.Message
}
"""
    
    try:
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        output = result.stdout.strip()
        if '"data"' in output:
            print("Success with .NET HttpClient!")
            print(f"Output snippet: {output[:200]}")
            return True
        else:
            print(f"Failed. Output: {output[:500]}")
            if result.stderr:
                print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Execution Error: {e}")
    return False

if __name__ == "__main__":
    test_dotnet_http()
