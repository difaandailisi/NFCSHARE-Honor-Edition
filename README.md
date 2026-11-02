# NFCSHARE · 荣耀一碰传标签工具（荣耀优化版）

> 给华为 / 荣耀设备的「一碰传」生成 NFC 标签：读目标设备的 **SN / 蓝牙 MAC / 型号**，
> 拼成载荷与二维码；用手机扫码写入 NFC 贴纸，贴到设备上即可碰一碰连接。
>
> 支持给**电脑、平板、手机**生成标签，并提供配套的标签记录擦除 / 修复流程。
>
> **这是荣耀适配版本**，在原华为版基础上重写了设备识别、MAC 读取与型号匹配逻辑。

---

## 下载

打包好的程序在 [Releases](https://github.com/difaandailisi/NFCSHARE-Honor-Edition/releases/latest) 页：

| 文件 | 大小 | 说明 |
|---|---|---|
| `NFCSHARE.exe` | 248 MB | 主程序，PyInstaller 单文件；运行需同目录放 `adb.exe` |

**配套的两款手机 App 请自行安装，本项目不提供下载：**

| App | 用途 | 获取方式 |
|---|---|---|
| 一碰传助手（`com.huawei.touchshare` / `com.hihonor.touchshare`） | 扫码并把载荷写入 NFC 标签 | 华为 / 荣耀应用市场，或从自己的旧设备备份中提取 |
| NFC Tools Pro（`com.wakdev.nfctools.pro`） | 擦除 / 格式化 NFC 标签 | Google Play 或官网购买 |

> exe 因为把 Python 运行环境一起打进去了，体积很大、首次启动较慢。这是 PyInstaller 单文件模式的固有代价。

---

## 它不做什么

**它不写 NFC。** 写标签是手机端 App 的事（一碰传助手 / NFC Tools Pro）。
这个工具只负责「算数据 + 出二维码」。理解这一点，后面的流程才说得通。

---

## 载荷格式

```
SN=<16位序列号>|MAC=<12位大写蓝牙MAC>|MODELID=<8位型号码>
```

| 字段 | 规则 |
|---|---|
| `SN` | 空格转 `A`，左对齐补 `A` 到 16 位，超长截断 |
| `MAC` | 去掉 `:` 和 `-`，转大写，必须 12 位 |
| `MODELID` | 电脑固定 `00000506`；平板/手机按型号查表 |

---

## 功能

| 选项 | 作用 |
|---|---|
| 1 | 生成**电脑**一碰传标签（读本机 SN + 蓝牙 MAC） |
| 2 | 擦除**手机**标签记录（含两次重启流程） |
| 3 | 修复一碰传失效 |
| 4 | 仅清除手机标签记录（不重启） |
| 5 | 生成**平板**一碰传标签（经 ADB 读 SN/MAC/型号） |

荣耀适配的重点在 **选项 5**：
新增 `command 设置 → 关于平板 → 状态信息` 之外的十余条蓝牙 MAC 读取路径
（含 Android 15+ 专用、荣耀私有 `vendor.honor.bt.mac` 等），
并支持**型号 + 设备名双重匹配**协同码，剥离「柔光版 / Lite / Pro / Max」等后缀。

---

## 运行

**要求**

- Windows（依赖 `wmic`、`ipconfig`）
- Python 3 + `qrcode`、`playsound`
- `adb.exe` 与程序同目录，或在系统 PATH 中

```bash
pip install qrcode playsound
python NFCSHARE.py
```

**打包**

```bash
pyinstaller NFCSHARE.spec
```

> 生成的单文件 exe 体积很大（实测约 248 MB），因为把运行环境一起打进去了。

---

## 目录

```
.
├── NFCSHARE.py          主程序（769 行，单文件）
├── NFCSHARE.spec        PyInstaller 打包配置
├── AI-CONTEXT.md        ★ 给 AI 读的结构化说明
├── docs/
│   └── 使用说明.md      原随包说明书
├── NOTICE.md            来源、许可与致谢
└── LICENSE              MIT
```

**读 `AI-CONTEXT.md` 能得到什么**（它比源码本身更适合快速理解）：

- 载荷格式与归一化规则
- 全部数据表：华为/荣耀包名映射、型号↔协同码、需剥离的 8 个后缀
- 取数逻辑：PC 用 `wmic`/`ipconfig`，安卓用 ADB；**12 条 MAC 读取候选路径**
- 五个功能的命令级流程，含 `disable_apps` 实际执行的 5 条 `pm disable` + 2 条 `pm clear`
- **9 个已知缺陷**（含型号匹配的真实 bug）
- 「纯手机实现」的边界分析

---

## 已知缺陷

从代码里读出来的，不是猜的，详见 `AI-CONTEXT.md` 第 7 节：

1. **MatePad 系列的协同码会匹配错**——剥离后缀时把 `Pro` 去掉了，
   于是 `MatePad Pro` 命中 `MatePad` 的 `00005103`，而不是 `00005107`
2. `荣耀平板9Pro` 在映射表里写了两遍，后者覆盖前者
3. 型号匹配用子串 `in`，短键（如 `Honor Pad V7`）容易误命中
4. `wmic` 在 Windows 11 24H2 起已弃用
5. 无 root 时多数 MAC 读取路径为空，「手动输入」应作为常规路径而非兜底

---

## 许可

**MIT** —— 可以商用、可以修改、可以闭源再发布、可以免费使用，
唯一要求是保留版权声明与许可声明。详见 [LICENSE](LICENSE)。

文档（`AI-CONTEXT.md`、本 README、`docs/使用说明.md`）同样以 MIT 发布；
如你希望**连署名都不需要**，可以自行改为 CC0。

---

## 致谢

本项目的思路与早期实现参考自
[Masterchiefm/Thirdparty-huawei-Share-OneHop](https://github.com/Masterchiefm/Thirdparty-huawei-Share-OneHop)
（华为一碰传标签工具）。荣耀适配版本由 **爱吃丝绒蛋糕（荣耀论坛）** 完成。
详见 [NOTICE.md](NOTICE.md)。

---

## 免责

修改系统包状态（`pm disable-user` / `pm clear`）与一碰传配置属于非官方途径，
可能导致智慧互联失效、需要重启恢复。**请自行承担风险。**

本项目仅供学习研究，请勿用于绕过授权或其他不当用途。
华为、荣耀、一碰传、多屏协同等名称与商标归各自权利人所有。
