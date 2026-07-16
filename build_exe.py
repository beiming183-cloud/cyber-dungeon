"""
PyInstaller 打包脚本
用于将游戏打包成可执行文件
"""
import PyInstaller.__main__
import os
import sys

# 游戏主文件
main_file = 'main.py'

# 打包选项
options = [
    main_file,  # 主程序文件
    '--name=CyberDungeon',  # 生成的exe名称
    '--onefile',  # 打包成单个exe文件
    '--windowed',  # 无控制台窗口（如果是GUI程序）
    # '--noconsole',  # 如果是GUI程序，取消注释此行并注释上一行
    '--clean',  # 清理临时文件
    '--noconfirm',  # 覆盖输出目录
    '--add-data=*.py;.',  # 包含所有Python文件（Windows用;分隔，Linux/Mac用:分隔）
    '--hidden-import=pygame',  # 确保pygame被包含
    '--hidden-import=pygame.font',  # 确保字体模块被包含
    '--collect-all=pygame',  # 收集pygame的所有数据文件
    '--icon=NONE',  # 如果有图标文件，可以指定路径
]

print("开始打包游戏...")
print("这将创建一个独立的exe文件，包含所有依赖项。")
print("请确保已安装 PyInstaller: pip install pyinstaller")

# 检查是否安装了PyInstaller
try:
    import PyInstaller
    print("PyInstaller 已安装，开始打包...")
    PyInstaller.__main__.run(options)
    print("\n打包完成！")
    print("exe文件位置: dist/CyberDungeon.exe")
except ImportError:
    print("错误：未安装 PyInstaller")
    print("请运行: pip install pyinstaller")
    sys.exit(1)




