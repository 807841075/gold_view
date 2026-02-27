
import subprocess
import os

def build():
    cmd = [
        r"E:\python\Scripts\pyinstaller.exe",
        "--clean",
        "GoldView.spec"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    with open("build_log.txt", "w", encoding="utf-8") as f:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="gbk", # Use GBK for Windows console output
            errors="replace" # Replace characters that can't be decoded
        )
        
        for line in process.stdout:
            print(line, end="")
            f.write(line)
            f.flush()
            
        process.wait()
        f.write(f"\nProcess exited with code: {process.returncode}")
        print(f"\nProcess exited with code: {process.returncode}")

if __name__ == "__main__":
    build()
