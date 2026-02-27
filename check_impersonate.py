from curl_cffi import requests

def list_supported_impersonations():
    print("Supported impersonation targets (check documentation or try common ones):")
    # curl_cffi doesn't have a direct API to list all, but we can check the version
    # and try common ones.
    targets = [
        "chrome100", "chrome101", "chrome110", "chrome120",
        "safari15.5", "safari15.6.1", "safari17",
        "edge101", "edge99"
    ]
    for t in targets:
        try:
            requests.get("https://www.google.com", impersonate=t, timeout=5)
            print(f"[OK] {t}")
        except Exception as e:
            if "not supported" in str(e):
                print(f"[NO] {t}")
            else:
                print(f"[ERR] {t}: {e}")

if __name__ == "__main__":
    list_supported_impersonations()
