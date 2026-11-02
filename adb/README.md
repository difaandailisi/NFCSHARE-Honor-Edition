# adb · Android Debug Bridge

> ⚠️ **这个目录里的东西不是本项目写的。**
>
> `adb` 是 Google / Android Open Source Project 的官方工具，版权归其作者所有，
> 与本项目无关。这里只是**随附一份**，方便没有装过 Android SDK 的人直接使用。

## 里面有什么

| 文件 | 大小 | 说明 |
|---|---|---|
| `adb.exe` | 6,641,760 B | ADB 主程序 |
| `AdbWinApi.dll` | 108,128 B | Windows USB 支持库 |
| `AdbWinUsbApi.dll` | 73,312 B | Windows USB 支持库 |
| `source.properties` | 38 B | 版本标记 |
| `NOTICE.txt` | 1,089,730 B | **Apache License 2.0 全文与归属声明** |

## 版本

```
Android Debug Bridge version 1.0.41
Version 36.0.0-13206524
Pkg.Revision=36.0.0
```

## 校验值（SHA-256）

```
adb.exe           1e1c2280b90b3f01ad84cd8df4858b1b1995012814f3ca8893bcc3ba3848edec
AdbWinApi.dll     9a56e72fe1372cb722a80c00b79dcecf2b37165884e470ed05f00c668c0043b0
AdbWinUsbApi.dll  5e77ccb2f25cd3a97553745adf1cd28a5fe8137cf64613b7fef9c6f92ff91f37
```

Windows 上校验：

```powershell
Get-FileHash .\adb.exe -Algorithm SHA256
```

## 许可

**Apache License 2.0**，全文见 [NOTICE.txt](NOTICE.txt)。

Apache-2.0 允许再分发，条件是保留版权与许可声明——这就是 `NOTICE.txt` 放在这里的原因。
本项目对 ADB 不作任何修改，也未对其主张任何权利。

## 官方来源

如需自行下载（推荐，可确保最新）：

- **Android SDK Platform-Tools**
  https://developer.android.com/tools/releases/platform-tools
- 或装 Android Studio，SDK Manager 里勾选 Platform-Tools

## 为什么这里要放一份

NFCSHARE 通过 ADB 与手机通信（读 SN、蓝牙 MAC、型号，执行 `pm` 命令）。
没有 `adb.exe` 程序会直接报错退出。为了让人下载后开箱能跑，这里随附一份。

**但它不是必需的。** 如果你已经有 ADB，或系统 PATH 里有，程序会优先用你的。

## 使用提醒

- 手机需要开启「开发者选项 → USB 调试」，并在弹窗里允许该电脑的调试授权
- 部分荣耀/华为机型还需要打开「仅充电时允许 ADB 调试」之类的开关，否则会时断时连
- ADB 连接等同于较高的设备权限，**请只在你自己信任的电脑上启用调试**
