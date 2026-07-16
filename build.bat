@echo off
chcp 65001 >nul
echo ====================================
echo 游戏打包脚本 - Cyber Dungeon
echo ====================================
echo.

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [提示] 未检测到 PyInstaller，正在安装...
    echo 这可能需要几分钟时间，请耐心等待...
    pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo [错误] PyInstaller 安装失败！
        echo 请手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
    echo.
    echo [成功] PyInstaller 安装完成！
    echo.
)

echo [开始] 正在打包游戏...
echo 这可能需要1-3分钟，请耐心等待...
echo.

REM 使用 PyInstaller 打包
pyinstaller --name=CyberDungeon ^
    --onefile ^
    --noconsole ^
    --clean ^
    --noconfirm ^
    --add-data="config.py;." ^
    --add-data="entities.py;." ^
    --add-data="game.py;." ^
    --add-data="skill_entities.py;." ^
    --add-data="systems.py;." ^
    --add-data="visual_effects.py;." ^
    --add-data="ui_components.py;." ^
    --hidden-import=pygame ^
    --hidden-import=pygame.font ^
    --hidden-import=pygame.mixer ^
    --collect-all=pygame ^
    main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！请检查上面的错误信息。
    echo.
    echo 常见问题解决：
    echo 1. 确保已安装所有依赖: pip install pygame
    echo 2. 尝试使用管理员权限运行此脚本
    echo 3. 检查是否有杀毒软件阻止
    pause
    exit /b 1
)

echo.
echo ====================================
echo [成功] 打包完成！
echo ====================================
echo.
echo exe文件位置: dist\CyberDungeon.exe
echo.
echo [提示]
echo - 首次运行可能需要几秒钟加载
echo - 如果杀毒软件报警，请添加信任
echo - 文件大小约 20-50MB（包含Python解释器）
echo.
echo 按任意键退出...
pause >nul
