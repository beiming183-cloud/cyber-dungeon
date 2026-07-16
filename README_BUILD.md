# 游戏打包说明

## 快速打包（推荐）

### Windows 用户

直接运行 `build.bat` 批处理文件：

```bash
build.bat
```

### 手动打包

1. **安装 PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **使用批处理文件打包（推荐）**
   ```bash
   build.bat
   ```

3. **或者使用 spec 文件打包**
   ```bash
   pyinstaller CyberDungeon.spec
   ```

4. **或者直接使用命令行打包**
   ```bash
   pyinstaller --name=CyberDungeon --onefile --noconsole --clean --noconfirm --add-data="*.py;." --hidden-import=pygame --hidden-import=pygame.font --collect-all=pygame main.py
   ```

## 打包后的文件位置

打包完成后，exe 文件将位于 `dist/CyberDungeon.exe`

## 注意事项

1. **首次运行**：打包后的 exe 文件首次运行可能需要几秒钟来解压和加载
2. **文件大小**：由于包含了 Python 解释器和所有依赖，exe 文件会比较大（约 20-50MB）
3. **杀毒软件**：某些杀毒软件可能会误报，这是正常现象（PyInstaller 打包的程序经常遇到）
4. **Windows Defender**：如果 Windows Defender 报警，可以选择"允许在设备上"

## 如果遇到问题

1. **缺少模块错误**：检查 `hiddenimports` 是否包含了所有需要的模块
2. **字体问题**：游戏使用系统字体，确保目标机器有中文字体
3. **打包失败**：确保所有依赖都已安装：
   ```bash
   pip install pygame pyinstaller
   ```

## 测试打包的 exe

在打包完成后，在 `dist` 目录下运行 `CyberDungeon.exe` 进行测试。




