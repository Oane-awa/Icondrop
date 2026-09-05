

# 🧊 IconDrop

**让 Windows 桌面图标拥有物理效果**  
*重力 · 刚体碰撞 · 鼠标搅动 · 智能休眠*

<br>

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Stars](https://img.shields.io/github/stars/yourusername/IconDrop.svg?label=Stars)](https://github.com/yourusername/IconDrop/stargazers)
[![Windows](https://img.shields.io/badge/platform-Windows-0078d7.svg)](https://www.microsoft.com/windows)

</div>

---

## 声明  
本项目部分代码和文本由AI生成

---

## ✨ 特性

- 🧱 **刚体碰撞** – 每个图标拥有独立的 AABB 碰撞箱，相互推挤、反弹，模拟真实物理。
- 🌍 **可调重力** – 图标受向下的重力影响，默认 1800 px/s²，可在 GUI 中实时调整。
- 🖱️ **鼠标搅动** – 鼠标划过或推动图标时，产生径向推力与切向搅动，连续轨迹检测确保 20 FPS 下也不会漏碰。
- 💤 **智能休眠** – 静止在桌面底部的图标自动休眠，降低 CPU 占用。
- 🖥️ **多显示器支持** – 自动识别每个显示器的任务栏工作区，图标不会飞出边界。
- 🎯 **DPI 感知** – 支持 Per-Monitor DPI，适配高 DPI 屏幕。
- 🔧 **一键恢复** – 随时将图标恢复至原始位置，并自动恢复系统“与网格对齐”设置。
- 📊 **轻量高效** – 物理循环 20 FPS，资源占用低，运行流畅。
<img width="1280" height="761" alt="屏幕截图 2026-09-05 210315" src="https://github.com/user-attachments/assets/79f1f01f-b43d-4755-8220-e8678ca97566" />
<img width="1280" height="761" alt="image" src="https://github.com/user-attachments/assets/4c79e86c-3b9f-4cb1-8de4-ff40858ce8c6" />



  


---

## 📦 依赖

- **Python 3.7+**（仅使用标准库 + `tkinter`，无需额外安装第三方包）
- **Windows 10 / 11**（依赖 Win32 API，仅限 Windows 平台）

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/IconDrop.git
cd IconDrop
```

### 2. 运行

bash

```
python icondrop.py
```

### 3. 操作步骤

1. 点击 **“连接 Explorer”** – 建立与桌面 ListView 的安全通信（跨进程内存操作）。
2. 点击 **“开始物理”** – 所有桌面图标立即获得物理效果。
3. 用鼠标在桌面上搅动、推动图标，体验物理交互。
4. 随时点击 **“暂停 / 继续”** 或 ​**“恢复原位置”**​。

---

## ⌨️ 快捷键

| 快捷键    | 功能                     |
| ----------- | -------------------------- |
| `F8`  | 开始物理模拟             |
| `F9`  | 暂停 / 继续物理          |
| `F10` | 恢复所有图标至原始位置   |
| `ESC` | 退出程序（自动恢复图标） |

---

## ⚙️ 参数调节

* ​**重力**​（默认 1800 px/s²） – 可在 GUI 的输入框中实时修改，建议范围 500\~5000。

---

## ⚠️ 注意事项

* **必须关闭“自动排列图标”** – 运行前请确保桌面右键 → **查看** → **自动排列图标** 未勾选，否则物理引擎无法生效。
* **“与网格对齐”自动处理** – 程序运行时会临时关闭该选项，停止时自动恢复，不影响用户习惯。
* **权限** – 普通用户即可运行，无需管理员权限。
* **安全** – 使用 `ReadProcessMemory` / `WriteProcessMemory` 安全访问 Explorer 内存，仅操作桌面 ListView 的图标位置，不修改其它数据。

---

## 🛠️ 工作原理

1. 通过 `FindWindow` 定位桌面 `SysListView32` 窗口。
2. 获取图标数量及位置（使用 `LVM_GETITEMPOSITION` / `LVM_SETITEMPOSITION32`）。
3. 每个图标建模为带有质量、弹性系数、摩擦系数的刚体。
4. 物理循环（20 FPS）：
   * 应用重力、空气阻力。
   * 检测图标间 AABB 碰撞，解决重叠与冲量。
   * 鼠标轨迹连续检测，施加径向推力和切向搅动。
   * 边界约束（显示器工作区）。
   * 休眠检测。
5. 通过跨进程内存写入更新图标位置。

---



## 📝 许可证

本项目采用 ​**MIT License**​，可自由使用、修改、分发。

---



<div align="center">**Enjoy playing with your desktop icons!**
(。・∀・ノ)

</div>
