import win32com.client
import json

def test_winhttp():
    print("\n--- Testing WinHTTP COM Object ---")
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AU9999&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=1&fqt=1&lmt=120"
    
    try:
        # Create WinHttpRequest object
        http = win32com.client.Dispatch("WinHttp.WinHttpRequest.5.1")
        
        # Open connection
        http.Open("GET", url, False)
        
        # Set headers to mimic browser
        http.SetRequestHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        http.SetRequestHeader("Referer", "https://quote.eastmoney.com/")
        http.SetRequestHeader("Accept", "*/*")
        
        # Send request
        print("Sending request via WinHTTP...")
        http.Send()
        
        # Get response
        status = http.Status
        print(f"Status Code: {status}")
        
        response_text = http.ResponseText
        if status == 200 and '"data"' in response_text:
            print("Success with WinHTTP!")
            print(f"Response snippet: {response_text[:200]}")
            return True
        else:
            print(f"Failed. Response: {response_text[:500]}")
            
    except Exception as e:
        print(f"WinHTTP Error: {e}")
    return False

if __name__ == "__main__":
    test_winhttp()
