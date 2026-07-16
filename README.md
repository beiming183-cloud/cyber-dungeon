# 赛博地牢 (Cyber Dungeon)

一款使用 Pygame 制作的赛博朋克动作肉鸽游戏。选择不同战斗角色和初始天赋，在随机地牢中迎战波次、精英敌人与 Boss，并通过技能和商店构筑本局能力。

## 下载运行

不想配置 Python 的玩家可前往仓库的 Releases 页面，下载 `CyberDungeon.exe` 后直接运行。

## 源码运行

需要 Python 3.7 或更高版本：

```powershell
pip install -r requirements.txt
python main.py
```

## 基本操作

- `WASD` 或方向键：移动
- 鼠标左键：普通攻击
- 数字键：选择角色、天赋或释放技能
- `Space`：确认与开始游戏
- `Esc`：暂停或返回上一级
- `B`：商店可用时打开商店

完整机制和角色说明参见 [游戏使用说明书.md](./游戏使用说明书.md)。

## 构建 EXE

安装 PyInstaller 后运行：

```powershell
pyinstaller CyberDungeon.spec --clean --noconfirm
```

生成文件位于 `dist/CyberDungeon.exe`。`build/`、`dist/` 和 Python 缓存不会提交到源码分支，可执行版本通过 GitHub Releases 发布。
