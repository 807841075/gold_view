import os
from PIL import Image

def convert_png_to_ico():
    png_path = "app_icon.png"
    ico_path = "app_icon.ico"
    
    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found.")
        return

    try:
        img = Image.open(png_path)
        # 确保图片是 RGBA 模式以支持透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # 生成多个尺寸的 ico 以适应不同 Windows 视图
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, sizes=icon_sizes)
        print(f"Successfully converted {png_path} to {ico_path}")
    except Exception as e:
        print(f"Failed to convert icon: {e}")

if __name__ == "__main__":
    convert_png_to_ico()
