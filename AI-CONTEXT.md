# NFCSHARE 荣耀版 —— 机制说明（给 AI 读）

> 本文是 `NFCSHARE.py`（荣耀优化版 v1.5.13，769 行）的结构化说明，
> 供 AI 在不读全部源码的情况下，准确掌握：载荷格式、数据来源、命令级流程与已知缺陷。
>
> 目标用途：为「用手机单独实现一版」做准备。**本文不含手机版实现**。
>
> 事实来源：`NFCSHARE.py` + `NFCSHARE.spec` + `docs/使用说明.md`。
> 凡标注【推断】的，是读代码推导而非实测；标注【待验证】的，是当前无法确认的。

## 0. 一句话

把「**目标设备的 SN + 蓝牙 MAC + 型号 ID**」编码成一个二维码，
由装了「华为/荣耀一碰传助手」的手机扫码后写入 NFC 标签，贴到设备上，实现一碰连接。

**它不写 NFC。** 它只负责**算数据 + 出二维码**，写标签是手机端 App 的事。这是理解全篇的前提。

---

## 1. 事实锚点

| 项 | 值 |
|---|---|
| 主程序 | `NFCSHARE.py`，Python 3，单文件，769 行 |
| 版本 | 源码头注释 v1.5.13；随包说明书 v1.5.9（文档滞后于代码） |
| 打包 | PyInstaller（`NFCSHARE.spec`，`console=True`，UPX 压缩）→ `NFCSHARE.exe` |
| 运行环境 | Windows（依赖 `wmic` / `ipconfig`），需 `adb.exe` 同目录或在 PATH |
| 上游 | `github.com/Masterchiefm/Thirdparty-huawei-Share-OneHop`（**无许可证**） |
| 分发形态 | `dist/` 内含 exe + `adb.exe` + AdbWinApi.dll + 若干 exe + 一个 mp3 |

**第三方依赖**：`qrcode`、`playsound`（后台播放 mp3）、`threading`（标准库）。

---

## 2. 核心：标签载荷格式

这是整个项目最关键的一行：

```python
code = f"SN={sn}|MAC={mac}|MODELID={model_id}"
```

三段，竖线分隔，**顺序固定**：

| 字段 | 位数/格式 | 来源 |
|---|---|---|
| `SN` | 归一化后 **16 位**，不足补 `A` | 目标设备的序列号 |
| `MAC` | **12 位大写十六进制**，无分隔符 | 目标设备的蓝牙 MAC |
| `MODELID` | **8 位数字**，`0000` 开头 | 型号映射表查得 |

**电脑的 MODELID 是写死的 `00000506`**，不查表：

```python
code = f"SN={sn}|MAC={mac}|MODELID=00000506"
```

> 【推断】一碰传助手扫码后，把这段字符串写进 NFC 标签的 NDEF 记录；
> 设备碰标签时读出来，用 SN/MAC 建立蓝牙连接，MODELID 决定用哪套协同配置。

---

## 3. 归一化规则（写代码时必须完全一致）

### SN

```python
sn_padded = sn.replace(' ', 'A').ljust(16, 'A')[:16]
```

- 空格 → `A`
- 左对齐补 `A` 到 16 位
- **超长直接截断到 16 位**

### MAC

```python
mac = raw.replace(':', '').replace('-', '').upper()
# 有效条件：len(mac) == 12
```

- 去掉 `:` 和 `-`，转大写
- **必须是 12 位**，否则视为失败

---

## 4. 数据表（可直接复用）

### 4.1 品牌判定

```python
brand = getprop("ro.product.brand").lower()
brand = brand if brand in ("huawei", "honor") else "honor"   # 兜底荣耀
```

### 4.2 包名映射

| key | huawei | honor |
|---|---|---|
| `instantshare` | `com.huawei.android.instantshare` | `com.hihonor.android.instantshare` |
| `pcassistant` | `com.huawei.pcassistant` | `com.hihonor.pcassistant` |
| `iconnect` | `com.huawei.iconnect` | `com.hihonor.iconnect` |
| `internal_app` | `com.huawei.android.internal.app` | `com.hihonor.android.internal.app` |
| `touchshare` | `com.huawei.touchshare/.ui.MainActivity` | `com.hihonor.touchshare/.ui.MainActivity` |

另有独立的两个：

- NFC 服务：`com.android.nfc`
- NFC 擦写工具：`com.wakdev.nfctools.pro/.MainActivityPro`（NFC Tools Pro，第三方）

### 4.3 型号 → MODELID 映射表

**华为**

| 型号关键词 | MODELID |
|---|---|
| `M6` | 00005101 |
| `MatePad` | 00005103 |
| `MatePad 10.8` | 00005105 |
| `MatePad Pro` | 00005107 |
| `MatePad 11` | 00005108 |
| `MatePad Air` | 00005109 |

**荣耀**

| 型号关键词 | MODELID |
|---|---|
| `MagicPad2` | 00005177 |
| `MagicPad 13` | 00005168 |
| `MagicPad3` | 00005191 |
| `Honor Pad V7` | 00005123 |
| `Honor Pad V8` | 00005125 |
| `honor View Pad 6` | 00005104 |
| `荣耀平板9Pro` | 00005176 → **被下一行覆盖为 00005172** |
| `荣耀平板8` | 00005166 |
| `荣耀平板V9` | 00005185 |
| `荣耀平板10` | 00005188 |

> ⚠️ `荣耀平板9Pro` 在字典里写了两次，Python 后者覆盖前者，**实际生效的是 00005172**。

### 4.4 匹配前剥离的后缀

```python
ignore_suffixes = ["柔光版", "Lite", "Pro", "Max", "SE", "青春版", "尊享版", "旗舰版"]
```

`ro.product.model` 和 `settings get global device_name` **都会先被剥离这些后缀并转小写**，再去匹配上表的 key。

---

## 5. 取数逻辑

### 5.1 电脑（Windows 本机）

| 字段 | 命令 | 解析 |
|---|---|---|
| SN | `wmic bios get serialnumber` | 取第一条非空、不含 `SerialNumbe` 的行 |
| 蓝牙 MAC | `ipconfig /all` | 先找含蓝牙关键词的行（多语言），再在该行或其下一行找物理地址关键词 |

蓝牙关键词（多语言）：`Bluetooth`、`蓝牙`、`Blåtand`、`藍牙`、`블루투스`
物理地址关键词：`物理地址`、`Physical Address`、`Adresse physique`、`物理アドレス`、`물리 주소`、`Endereço físico`

> ⚠️ `wmic` 在 Windows 11 24H2 起已被标记弃用，可能在新系统上不存在。

### 5.2 安卓设备（经 ADB）

| 字段 | 命令 |
|---|---|
| 品牌 | `getprop ro.product.brand` |
| 型号 | `getprop ro.product.model` |
| 设备名 | `settings get global device_name` → 退回 `ro.product.name` / `ro.product.model` / `ro.build.product` |
| SN | `getprop ro.serialno`（长度需 ≥ 6） |
| 安卓版本 | `getprop ro.build.version.release` → 取整数部分 |
| root | `shell id` → 含 `uid=0` 或 `root` |

**蓝牙 MAC 的多路径尝试（按顺序）**：

```text
1.  Android 15+ 专用：settings get global bluetooth_address
2.  Android 15+ 专用：dumpsys bluetooth_manager  →  匹配 "address=" 行
3.  cat /sys/class/bluetooth/hci0/address
4.  cat /sys/class/bluetooth/hci1/address
5.  cat /sys/class/bluetooth/hci2/address
6.  getprop ro.boot.btmacaddr
7.  getprop vendor.<brand>.bluetooth.address
8.  getprop ro.bluetooth.macaddr
9.  getprop persist.service.bdroid.bdaddr
10. settings get secure bluetooth_address
11. getprop vendor.hardware.bt.mac          ← 荣耀专用
12. getprop vendor.honor.bt.mac             ← 荣耀专用
```

全部失败 → 提示用户手动输入，路径提示是「设置 → 关于平板 → 状态信息 → 蓝牙地址」。

**蓝牙开关**：若 `settings get global bluetooth_on` == `0`，会尝试
`service call bluetooth_manager 6` 打开，等 3 秒后复查 `bluetooth_on`。

---

## 6. 五个功能的确切行为

### 选项 1 · 生成电脑一碰传标签

```
touchshare()  → 询问是否安装 APK → am start 启动一碰传助手
make_qr()     → 取 PC 的 SN + MAC → 拼 "SN=..|MAC=..|MODELID=00000506"
              → qrcode.make() → 存 <程序目录>/test.png → 尝试用系统默认程序打开
```

### 选项 2 · 擦除手机标签记录（含两次重启）

```
确认警告
→ disable_apps()          # pm disable-user ×5 + pm clear ×2
→ adb reboot              # 第 1 次
→ 用户回车
→ disable_apps()          # 再来一遍
→ nfctool()               # 装/启 NFC Tools Pro，人工擦标签
→ 用户回车
→ [可选] 制作新标签：touchshare() + make_qr()
→ adb reboot              # 第 2 次
→ 用户回车
→ enable_apps()           # pm enable ×5
```

【推断】两次重启的用意：禁用 + 清数据后必须让系统重新读一遍包状态，
否则残留的服务绑定会立刻把记录写回去；第二次重启后启用，确保系统在干净的基线上重建。

### 选项 3 · 修复一碰传失效

```
enable_apps() → adb reboot → 用户回车 → enable_apps()
```

### 选项 4 · 仅清除标签记录（不重启）

```
disable_apps() → enable_apps()
```

### 选项 5 · 生成平板一碰传标签

```
checkadb() → 品牌 → 设备名 → 型号
→ SN（ro.serialno）
→ MAC（上面 12 条路径）
→ MODELID（型号/设备名双重匹配）
→ 拼串 → 二维码 → test.png
```

### `disable_apps()` 实际执行的命令

```text
pm disable-user <instantshare>
pm disable-user <pcassistant>
pm disable-user <iconnect>
pm disable-user com.android.nfc
pm disable-user <internal_app>
pm clear <instantshare>
pm clear <pcassistant>
```

`enable_apps()` 是前五个的 `pm enable` 版本（含 `com.android.nfc`），无 `pm clear`。

---

## 7. 已知的坑（写新实现时不要照抄）

| # | 问题 | 具体表现 | 建议 |
|---|---|---|---|
| 1 | **MATEPAD 系列会匹配错** | 剥离后缀时把 `Pro` 去掉了，于是 `MatePad Pro` → 清理成 `matepad` → 命中 `MatePad`(00005103) 而不是 `MatePad Pro`(00005107)。加上字典遍历取 `[0]`，短键必胜 | 精确匹配优先 + 最长键优先，且**不要对型号做后缀剥离**，只对设备名剥离 |
| 2 | 荣耀平板9Pro 双写 | 字典里重复 key，后者覆盖 → 实际 00005172 | 去重，确认正确值 |
| 3 | 型号匹配用 `in` 子串 | `Honor Pad V7` 这类短键容易误命中 | 改 token 级匹配或正则锚定 |
| 4 | `wmic` 已弃用 | Win11 24H2+ 可能没有 wmic | 改用 PowerShell `Get-CimInstance` |
| 5 | MAC 读取依赖 root | 无 root 时多数 sysfs / getprop 路径为空 | 把「手动输入」做成一等公民，而不是兜底 |
| 6 | 蓝牙自动开启用 `service call bluetooth_manager 6` | 该事务号随系统版本变化，可能无效 | 只做提示，不强行代劳 |
| 7 | 硬编码 `test.png` | 多标签场景会互相覆盖 | 按 SN 或时间戳命名 |
| 8 | 后台音乐线程无退出控制 | 只能靠系统音量调节 | 加开关或去掉 |
| 9 | 全程 `system()` 拼字符串 | 路径含空格时依赖引号，易碎 | 用 `subprocess.run(list)` |

---

## 8. 「纯手机实现」的边界（供下一步参考，非实现）

用户设想用手机单独实现一版，并怀疑需要两台手机。基于源码事实的分析：

### 8.1 工具的职责拆分

```
[取数] 读目标设备的 SN / 蓝牙MAC / 型号   ← 本工具用 ADB 或 wmic 完成
  ↓
[编码] 拼 "SN=..|MAC=..|MODELID=.."      ← 纯字符串
  ↓
[出码] 生成二维码                         ← qrcode 库
  ↓
[写签] 一碰传助手扫码 → 写入 NFC 标签      ← 手机端 App，本工具不参与
```

**纯手机实现，难在第 1 步和第 4 步，不在第 2、3 步。**

### 8.2 第 1 步（取数）的现实约束

- 手机不是 ADB host，**无法用 ADB 去读另一台设备的 SN/MAC**
- 当目标是**电脑**时，PC 的 SN 与蓝牙 MAC 只能：命令读取（需要 PC 端配合）、或手动输入
- 当目标是**另一台手机/平板**时，同理
- 因此纯手机版大概率退化成：**手动输入 SN + MAC + 选型号**

### 8.3 第 4 步（写签）与「两台手机」

- 一碰传助手负责**扫码并把数据写入 NFC 标签**（【待验证】其是否自带写入能力；
  源码里擦除动作明确交给了第三方 NFC Tools Pro）
- 若目标是**电脑或平板**：一台手机足够（扫码 → 写签 → 贴到目标设备）
- 若目标是**这台手机自己**：本机既当数据源又要扫码写签，流程上需要**第二台手机**代劳

> 结论（【推断】）：**"需要两台手机"只在"给手机自己做标签"时成立**。
> 做电脑/平板的标签，一台手机就够——前提是 SN 和 MAC 能拿到（这一步在纯手机下要手动）。
>
> 这一点直接决定手机版要不要做「手动输入 + 型号选择」界面，建议先验证再设计。

### 8.4 需要先确认的三件事

1. 一碰传助手（`com.huawei.touchshare` / `com.hihonor.touchshare`）**是否有公开的写入 Intent**，
   还是只能靠它自己的 UI 扫码？
2. 写入的 NDEF 记录类型是什么（纯文本？自定义 MIME？URI？）——决定能否自研写签 App 绕过助手
3. `MODELID` 是否会被目标设备侧校验（不同值会不会连不上 / 协同能力不同）

---

## 9. 相关文件位置（本机，非仓库）

| 用途 | 路径 |
|---|---|
| 源码 | `F:\2024写作盘\桌面文件夹\AAAAAASANDAIGAIBAN\SANDAIGAIBAN11111111\NFCSHARE.py` |
| 一碰传助手 APK | `F:\另一个C盘下载\v1.5.3\一碰传标签制作器\touchshare.apk` |
| NFC Tools Pro APK | `F:\另一个C盘下载\v1.5.3\一碰传标签制作器\nfctool.apk` |
| 打包产物 | 同目录 `dist\NFCSHARE.exe` |

---

## 10. 术语

| 词 | 含义 |
|---|---|
| 一碰传 / OneHop | 华为/荣耀的 NFC 碰一碰连接能力 |
| 一碰传助手 | `com.huawei.touchshare` / `com.hihonor.touchshare`，扫码写签的官方 App |
| 协同码 / MODELID | 8 位数字，标识设备型号对应的协同配置 |
| 协同 | 多屏协同（投屏 + 跨设备操作） |
| NFC Tools Pro | 第三方 NFC 读写工具，`com.wakdev.nfctools.pro` |
