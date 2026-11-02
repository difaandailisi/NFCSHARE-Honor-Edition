#!/usr/bin/env python
# coding: utf-8
#v1.5.13（增强型号匹配功能）
import os
import sys
from os import system
import subprocess
from qrcode import make
from time import sleep
from playsound import playsound  # 导入playsound库
import threading

# ======================
#  路径兼容逻辑
# ======================
def get_program_dir():
    """获取程序根目录（打包后为exe所在目录，开发时为脚本目录）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def find_file(file_name, subdir=None):
    """多路径查找文件（优先程序目录，其次环境变量）"""
    base_dir = get_program_dir()
    paths = [base_dir]
    if subdir:
        paths.append(os.path.join(base_dir, subdir))
    paths.extend(os.environ.get("PATH", "").split(os.pathsep))
    
    for path in paths:
        full_path = os.path.join(path, file_name)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return full_path
    return None

def play_music():
    """播放音乐"""
    music_file = find_file("03 dead feelings.mp3")  # 替换为你的音乐文件名
    if music_file:
        try:
            playsound(music_file)
        except Exception as e:
            print(f"⚠️ 播放音乐失败：{str(e)}")
    else:
        print("❌ 未找到音乐文件，请将音乐文件放在程序同一目录")

# 创建并启动音乐播放线程
music_thread = threading.Thread(target=play_music)
music_thread.start()

# ======================
#  设备信息获取
# ======================
def get_tablet_name():
    """获取平板的用户自定义名称（设备名称）"""
    adb_path = find_file("adb.exe") or "adb.exe"
    try:
        # 优先读取用户自定义名称
        result = subprocess.run(
            [adb_path, "shell", "settings", "get", "global", "device_name"],
            capture_output=True, text=True, encoding='utf-8'
        )
        name = result.stdout.strip()
        print(f"尝试读取用户自定义名称，命令结果：{name}")
        if name:
            return name
        
        # 尝试其他命令
        commands = [
            [adb_path, "shell", "getprop", "ro.product.name"],
            [adb_path, "shell", "getprop", "ro.product.model"],
            [adb_path, "shell", "getprop", "ro.build.product"]
        ]
        for cmd in commands:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            name = result.stdout.strip()
            print(f"尝试命令 {' '.join(cmd)}，结果：{name}")
            if name:
                return name
        
        return "未知设备"
    except Exception as e:
        print(f"⚠️ 获取设备名称失败：{str(e)}")
        return "未知设备"

def checkadb():
    """检查ADB连接"""
    adb_path = find_file("adb.exe") or "adb.exe"
    check = 0
    while check < 2:
        check = 0
        if system(f'"{adb_path}" devices') != 0:
            print('❌ 找不到adb.exe，请将ADB工具放在程序同一目录')
            input('按回车键重试...')
            continue
        check += 1
        
        system(f'"{adb_path}" kill-server')
        result = subprocess.run(
            [adb_path, "devices"],
            capture_output=True, text=True, encoding='gbk'
        )
        devices = result.stdout.splitlines()
        if len(devices) < 2 or devices[1].strip() == '':
            print('❌ 未找到设备，请开启手机USB调试并允许调试权限')
            input('按回车键重试...')
            continue
        check += 1
        print(f"✅ 已连接设备：{devices[1].split()[0]}")

def get_device_brand():
    """通过ADB读取设备品牌"""
    adb_path = find_file("adb.exe") or "adb.exe"
    try:
        result = subprocess.run(
            [adb_path, "shell", "getprop", "ro.product.brand"],
            capture_output=True, text=True, encoding='utf-8'
        )
        brand = result.stdout.strip().lower()
        print(f"📱 检测到设备品牌：{brand}")
        return brand if brand in ["huawei", "honor"] else "honor"
    except Exception as e:
        print(f"⚠️ 品牌检测失败：{str(e)}，默认使用荣耀配置")
        return "honor"

# 华为/荣耀应用包名映射表
APP_PACKAGES = {
    "huawei": {
        "instantshare": "com.huawei.android.instantshare",
        "pcassistant": "com.huawei.pcassistant",
        "iconnect": "com.huawei.iconnect",
        "internal_app": "com.huawei.android.internal.app",
        "touchshare": "com.huawei.touchshare/.ui.MainActivity"
    },
    "honor": {
        "instantshare": "com.hihonor.android.instantshare",
        "pcassistant": "com.hihonor.pcassistant",
        "iconnect": "com.hihonor.iconnect",
        "internal_app": "com.hihonor.android.internal.app",
        "touchshare": "com.hihonor.touchshare/.ui.MainActivity"
    }
}

def get_sn():
    """读取电脑SN"""
    try:
        result = subprocess.run(
            ['wmic', 'bios', 'get', 'serialnumber'],
            capture_output=True, text=True, encoding='gbk'
        )
        sn_lines = result.stdout.splitlines()
        sn = [line.strip() for line in sn_lines if line.strip() and "SerialNumbe" not in line][0]
        print(f"💻 检测到电脑SN：{sn}")
    except (IndexError, Exception) as e:
        sn = ""
        print(f"⚠️ 自动获取SN失败：{str(e)}")
    if not sn:
        print('❌ 未获取到有效SN，请手动输入')
        sn = input('请输入电脑SN：').strip()
        return sn
    print('请选择SN格式（默认a）：')
    print('a. 自动补齐16位（加A补齐，推荐）')
    print('b. 使用原始SN')
    print('c. 手动输入SN')
    opt = input('选择（a/b/c）：').strip().lower() or 'a'
    if opt == 'b':
        return sn
    elif opt == 'c':
        return input('请输入自定义SN：').strip()
    else:
        sn_padded = sn.replace(' ', 'A').ljust(16, 'A')[:16]
        print(f"📌 自动生成16位SN：{sn_padded}")
        return sn_padded

def get_mac():
    """读取电脑蓝牙MAC（优化多语言支持）"""
    # 扩展多语言关键词（蓝牙适配器名称）
    bluetooth_keywords = [
        'Bluetooth', '蓝牙', 'Blåtand', 'Bluetooth',  # 英文、中文、瑞典语
        '藍牙', '블루투스', 'Bluetooth'  # 繁体中文、韩语
    ]
    # 扩展多语言关键词（物理地址）
    physical_keywords = [
        '物理地址', 'Physical Address', 'Adresse physique',  # 中文、英文、法文
        '物理アドレス', '물리 주소', 'Endereço físico'  # 日文、韩文、葡萄牙文
    ]
    
    try:
        result = subprocess.run(
            ['ipconfig', '/all'],
            capture_output=True, text=True, encoding='gbk'
        )
        a = result.stdout.splitlines()
        bluetooth_lines = [line for line in a if any(kw in line for kw in bluetooth_keywords)]
        if not bluetooth_lines:
            print('❌ 未检测到蓝牙适配器（请开启蓝牙）')
            return input('请手动输入电脑蓝牙MAC（不含符号）：').strip().upper()
        
        # 遍历蓝牙相关行，查找物理地址
        for idx, line in enumerate(bluetooth_lines):
            if any(kw in line for kw in physical_keywords):
                parts = [p.strip() for p in line.split(':') if p.strip()]
                if len(parts) >= 2:
                    mac = parts[-1].replace('-', '').replace(':', '').upper()
                    if len(mac) == 12:
                        print(f"📶 检测到电脑蓝牙MAC：{mac}")
                        return mac
            # 检查下一行（部分系统物理地址在蓝牙名称的下一行）
            if idx + 1 < len(a):
                next_line = a[idx + 1]
                if any(kw in next_line for kw in physical_keywords):
                    parts = [p.strip() for p in next_line.split(':') if p.strip()]
                    if len(parts) >= 2:
                        mac = parts[-1].replace('-', '').replace(':', '').upper()
                        if len(mac) == 12:
                            print(f"📶 检测到电脑蓝牙MAC：{mac}")
                            return mac
        
        print('❌ 未从蓝牙适配器信息中提取到MAC地址')
        return input('请手动输入电脑蓝牙MAC（不含符号）：').strip().upper()
    except Exception as e:
        print(f"⚠️ 读取电脑蓝牙MAC失败：{str(e)}")
        return input('请手动输入电脑蓝牙MAC（不含符号）：').strip().upper()

def get_tablet_sn():
    """读取平板SN"""
    adb_path = find_file("adb.exe") or "adb.exe"
    try:
        result = subprocess.run(
            [adb_path, "shell", "getprop", "ro.serialno"],
            capture_output=True, text=True, encoding='utf-8'
        )
        sn = result.stdout.strip()
        if sn and len(sn) >= 6:
            print(f"🖥️  平板SN：{sn}")
            return sn
    except Exception as e:
        print(f"⚠️ 自动获取平板SN失败：{str(e)}")
    
    print('❌ 未获取到平板SN')
    return input('请手动输入平板SN：').strip()

def check_root(adb_path):
    """检查设备是否有root权限"""
    try:
        result = subprocess.run(
            [adb_path, "shell", "id"],
            capture_output=True, text=True, encoding='utf-8'
        ).stdout.strip()
        return "uid=0" in result or "root" in result.lower()
    except Exception:
        return False

def get_android_version(adb_path):
    """获取安卓版本号"""
    try:
        result = subprocess.run(
            [adb_path, "shell", "getprop", "ro.build.version.release"],
            capture_output=True, text=True, encoding='utf-8'
        ).stdout.strip()
        return float(result.split('.')[0]) if result else 0
    except Exception:
        return 0

def get_tablet_mac():
    """多途径获取平板蓝牙MAC（增强安卓15支持）"""
    adb_path = find_file("adb.exe") or "adb.exe"
    brand = get_device_brand()
    mac_candidates = []
    
    # 获取安卓版本
    android_version = get_android_version(adb_path)
    print(f"📱 检测到安卓版本：{android_version}")
    
    # 检查root权限（提示用户）
    is_root = check_root(adb_path)
    if not is_root:
        print("⚠️ 检测到设备未获取root权限，部分MAC读取路径可能受限")
    
    # 检查并临时开启蓝牙
    try:
        bt_state = subprocess.run(
            [adb_path, "shell", "settings", "get", "global", "bluetooth_on"],
            capture_output=True, text=True, encoding='utf-8'
        ).stdout.strip()
        if bt_state == "0":
            print("⚠️ 平板蓝牙未开启，尝试临时开启...")
            system(f'"{adb_path}" shell service call bluetooth_manager 6 >nul 2>&1')
            sleep(3)  # 延长等待时间，确保蓝牙启动
            # 验证蓝牙是否真正开启
            bt_state_after = subprocess.run(
                [adb_path, "shell", "settings", "get", "global", "bluetooth_on"],
                capture_output=True, text=True, encoding='utf-8'
            ).stdout.strip()
            if bt_state_after != "1":
                print("⚠️ 临时开启蓝牙失败，请手动开启平板蓝牙后重试")
    except Exception as e:
        print(f"⚠️ 蓝牙状态检查失败：{str(e)}")
    
    # 安卓15+专用路径
    if android_version >= 15:
        print("🔍 尝试安卓15+专用路径...")
        # 尝试通过Settings.Global获取（需要特殊权限）
        try:
            result = subprocess.run(
                [adb_path, "shell", "settings", "get", "global", "bluetooth_address"],
                capture_output=True, text=True, encoding='utf-8'
            ).stdout.strip()
            if result and len(result.replace(":", "")) == 12:
                mac = result.replace(':', '').upper()
                mac_candidates.append(mac)
                print(f"📶 通过安卓15+路径获取到MAC：{mac}")
        except Exception as e:
            print(f"⚠️ 安卓15+专用路径失败：{str(e)}")
        
        # 尝试通过dumpsys获取（需要特殊权限）
        try:
            result = subprocess.run(
                [adb_path, "shell", "dumpsys", "bluetooth_manager"],
                capture_output=True, text=True, encoding='utf-8'
            ).stdout
            # 查找形如 "address=XX:XX:XX:XX:XX:XX" 的行
            for line in result.splitlines():
                if "address=" in line:
                    parts = line.split("address=")
                    if len(parts) > 1:
                        mac_part = parts[1].strip().split()[0]
                        if len(mac_part.replace(":", "")) == 12:
                            mac = mac_part.replace(':', '').upper()
                            mac_candidates.append(mac)
                            print(f"📶 通过dumpsys获取到MAC：{mac}")
                            break
        except Exception as e:
            print(f"⚠️ dumpsys方法失败：{str(e)}")
    
    # 扩展MAC读取来源（增加荣耀专用路径）
    mac_sources = [
        [adb_path, "shell", "cat", "/sys/class/bluetooth/hci0/address"],
        [adb_path, "shell", "cat", "/sys/class/bluetooth/hci1/address"],
        [adb_path, "shell", "cat", "/sys/class/bluetooth/hci2/address"],
        [adb_path, "shell", "getprop", "ro.boot.btmacaddr"],
        [adb_path, "shell", f"getprop vendor.{brand}.bluetooth.address"],
        [adb_path, "shell", "getprop", "ro.bluetooth.macaddr"],
        [adb_path, "shell", "getprop", "persist.service.bdroid.bdaddr"],
        [adb_path, "shell", "settings", "get", "secure", "bluetooth_address"],
        # 荣耀平板专用路径
        [adb_path, "shell", "getprop", "vendor.hardware.bt.mac"],
        [adb_path, "shell", "getprop", "vendor.honor.bt.mac"],
    ]
    
    # 尝试读取并打印调试信息
    for cmd in mac_sources:
        try:
            print(f"尝试读取MAC：{' '.join(cmd)}")
            # 使用更健壮的编码处理
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',  # 使用UTF-8编码
                errors='replace',  # 替换无法解码的字符
                timeout=5
            ).stdout.strip()
            mac = result.replace(':', '').replace('-', '').upper()
            if mac and len(mac) >= 12:
                mac_candidates.append(mac[:12])
                print(f"  提取到MAC：{mac[:12]}")
            else:
                print(f"  未提取到有效MAC（结果：{result[:30]}...）")
        except Exception as e:
            print(f"  命令执行失败：{str(e)}")
            continue
    
    mac_candidates = list(set(mac_candidates))
    if mac_candidates:
        print(f"📶 平板蓝牙MAC：{mac_candidates[0]}")
        return mac_candidates[0]
    
    print('\n❌ 自动获取失败！请手动查询：')
    print('  路径：平板设置 → 关于平板 → 状态信息 → 蓝牙地址（去除符号）')
    while True:
        manual_mac = input('请输入平板蓝牙MAC（不含符号）：').strip().upper()
        if len(manual_mac) == 12:
            print(f"✅ 已确认平板蓝牙MAC：{manual_mac}")
            return manual_mac
        print("❌ 格式错误！需12位字符（如A1B2C3D4E5F6）")

def get_tablet_model_id():
    """增强版：通过型号和设备名称双重匹配协同码，忽略特定后缀，优先型号匹配"""
    adb_path = find_file("adb.exe") or "adb.exe"
    try:
        result = subprocess.run(
            [adb_path, "shell", "getprop", "ro.product.model"],
            capture_output=True, text=True, encoding='utf-8',
            timeout=5
        )
        model = result.stdout.strip() or "未知型号"
    except Exception as e:
        print(f"⚠️ 获取型号失败：{str(e)}")
        model = "未知型号"
    
    # 获取设备名称（用于双重匹配）
    device_name = get_tablet_name()
    brand = get_device_brand()
    print(f"📱 平板型号：{model}（品牌：{brand}，名称：{device_name}）")
    
    # 协同码映射表（型号 → 协同码）
    model_id_map = {
        "huawei": {
            "M6": "00005101",
            "MatePad": "00005103",
            "MatePad 10.8": "00005105",
            "MatePad Pro": "00005107",
            "MatePad 11": "00005108",
            "MatePad Air": "00005109"
        },
        "honor": {
            "MagicPad2": "00005177",
            "MagicPad 13": "00005168",
            "MagicPad3": "00005191",
            "Honor Pad V7": "00005123",
            "Honor Pad V8": "00005125",
            "honor View Pad 6": "00005104",
            "荣耀平板9Pro": "00005176",
            "荣耀平板8": "00005166",
            "荣耀平板9Pro": "00005172",
            "荣耀平板V9": "00005185",
            "荣耀平板10": "00005188"
        }
    }
    target_map = model_id_map.get(brand, model_id_map["honor"])
    
    # 定义需要忽略的后缀列表
    ignore_suffixes = ["柔光版", "Lite", "Pro", "Max", "SE", "青春版", "尊享版", "旗舰版"]
    
    def clean_name(name):
        """清理名称，移除不需要的后缀并转为小写"""
        name = name.lower()
        for suffix in ignore_suffixes:
            name = name.replace(suffix.lower(), "").strip()
        return name
    
    # 清理型号和设备名称
    cleaned_model = clean_name(model)
    cleaned_name = clean_name(device_name)
    
    print(f"🔍 清理后的型号: {cleaned_model}")
    print(f"🔍 清理后的名称: {cleaned_name}")
    
    # 查找匹配的型号ID
    model_matches = []
    name_matches = []
    
    # 查找型号匹配
    for model_key, model_id in target_map.items():
        key_lower = model_key.lower()
        if key_lower in cleaned_model:
            model_matches.append((model_key, model_id))
    
    # 查找设备名称匹配
    for model_key, model_id in target_map.items():
        key_lower = model_key.lower()
        if key_lower in cleaned_name:
            name_matches.append((model_key, model_id))
    
    # 处理匹配结果
    if model_matches:
        # 型号匹配成功，使用第一个匹配结果
        best_model_match = model_matches[0]
        print(f"🔖 通过型号匹配协同码：{best_model_match[0]} → {best_model_match[1]}")
        
        # 检查名称匹配是否存在且与型号匹配不同
        if name_matches and name_matches[0][1] != best_model_match[1]:
            print(f"💡 注意：设备名称匹配到不同的型号：{name_matches[0][0]} → {name_matches[0][1]}")
            choice = input(f"是否使用名称匹配结果？(y/默认使用型号匹配) ").strip().lower()
            if choice == 'y':
                print(f"🔖 使用名称匹配协同码：{name_matches[0][0]} → {name_matches[0][1]}")
                return name_matches[0][1]
        
        return best_model_match[1]
    
    elif name_matches:
        # 型号未匹配，但名称匹配成功
        best_name_match = name_matches[0]
        print(f"🔖 通过设备名称匹配协同码：{best_name_match[0]} → {best_name_match[1]}")
        return best_name_match[1]
    
    # 双重匹配失败，手动输入
    print('\n❌ 未匹配到协同码！请通过以下方式获取：')
    print('  1. 平板唤醒协同功能，显示二维码')
    print('  2. 荣耀应用商店下载「Alook浏览器」')
    print('  3. 扫描二维码，获取最后一排「0000开头的数字」')
    while True:
        manual_code = input('请输入协同码（0000开头）：').strip()
        if manual_code.startswith("0000") and len(manual_code) >= 4:
            print(f"✅ 已确认协同码：{manual_code}")
            return manual_code
        print("❌ 格式错误！需以0000开头（如00005191）")

def get_qr(code):
    """生成二维码"""
    try:
        save_path = os.path.join(get_program_dir(), "test.png")
        img = make(code)
        img.save(save_path)
        print(f"✅ 二维码已保存至：{save_path}")
    except Exception as e:
        print(f"❌ 二维码保存失败：{str(e)}（请确保程序目录可写入）")

def make_qr():
    """生成电脑一碰传标签"""
    system('cls')
    print('='*60)
    print('📌 电脑一碰传标签生成器')
    print('='*60)
    sn = get_sn()
    mac = get_mac()
    code = f"SN={sn}|MAC={mac}|MODELID=00000506"
    get_qr(code)
    print(f"\n📝 生成标签代码：{code}")
    print(f"📂 二维码路径：{os.path.join(get_program_dir(), 'test.png')}")
    print("\n提示：若SN与电脑管家不一致，请重新运行选择b/c选项")
    try:
        system(f'"{os.path.join(get_program_dir(), "test.png")}"')
    except:
        print("⚠️ 无法自动打开图片，请手动查看test.png")
    print('='*60)
    input('按回车键返回主菜单...')

def make_tablet_qr():
    """生成平板一碰传标签"""
    system('cls')
    print('='*60)
    print('📌 平板一碰传标签生成器')
    print('='*60)
    checkadb()
    brand = get_device_brand()
    device_name = get_tablet_name()
    try:
        result = subprocess.run(
            [find_file("adb.exe") or "adb.exe", "shell", "getprop", "ro.product.model"],
            capture_output=True, text=True, encoding='utf-8',
            timeout=5
        )
        model = result.stdout.strip() or "未知型号"
    except Exception as e:
        print(f"⚠️ 获取型号失败：{str(e)}")
        model = "未知型号"
    print(f"📱 平板信息：品牌 - {brand}，名称 - {device_name}，型号 - {model}")
    
    sn = get_tablet_sn()
    mac = get_tablet_mac()
    model_id = get_tablet_model_id()  # 已包含双重匹配逻辑
    code = f"SN={sn}|MAC={mac}|MODELID={model_id}"
    get_qr(code)
    print(f"\n📝 生成平板标签代码：{code}")
    print(f"📂 二维码路径：{os.path.join(get_program_dir(), 'test.png')}")
    try:
        system(f'"{os.path.join(get_program_dir(), "test.png")}"')
    except:
        print("⚠️ 无法自动打开图片，请手动查看test.png")
    print('='*60)
    input('按回车键返回主菜单...')

def disable_apps():
    """禁用设备相关应用"""
    system('cls')
    print('='*60)
    print('📌 禁用应用（清理标签记录）')
    print('='*60)
    checkadb()
    brand = get_device_brand()
    packages = APP_PACKAGES[brand]
    adb_path = find_file("adb.exe") or "adb.exe"
    
    cmds = [
        f'"{adb_path}" shell pm disable-user {packages["instantshare"]}',
        f'"{adb_path}" shell pm disable-user {packages["pcassistant"]}',
        f'"{adb_path}" shell pm disable-user {packages["iconnect"]}',
        f'"{adb_path}" shell pm disable-user com.android.nfc',
        f'"{adb_path}" shell pm disable-user {packages["internal_app"]}',
        f'"{adb_path}" shell pm clear {packages["instantshare"]}',
        f'"{adb_path}" shell pm clear {packages["pcassistant"]}',
    ]
    for cmd in cmds:
        print(f"执行：{cmd.split()[-1]}")
        system(cmd)
    print('='*60)
    input('按回车键返回主菜单...')

def enable_apps():
    """启用设备相关应用"""
    print('='*60)
    print('📌 启用应用')
    print('='*60)
    checkadb()
    brand = get_device_brand()
    packages = APP_PACKAGES[brand]
    adb_path = find_file("adb.exe") or "adb.exe"
    
    cmds = [
        f'"{adb_path}" shell pm enable {packages["instantshare"]}',
        f'"{adb_path}" shell pm enable {packages["pcassistant"]}',
        f'"{adb_path}" shell pm enable {packages["iconnect"]}',
        f'"{adb_path}" shell pm enable {packages["internal_app"]}',
        f'"{adb_path}" shell pm enable com.android.nfc',
    ]
    for cmd in cmds:
        print(f"执行：{cmd.split()[-1]}")
        system(cmd)
    print('='*60)
    input('按回车键返回主菜单...')

def touchshare():
    """安装并启动一碰传助手"""
    print('='*60)
    print('📌 一碰传助手管理')
    print('='*60)
    adb_path = find_file("adb.exe") or "adb.exe"
    
    if input('是否安装一碰传助手？(y/n) ').strip().lower() == 'y':
        checkadb()
        apk_path = find_file("touchshare.apk", "esc") or "touchshare.apk"
        
        try:
            print(f"开始安装：{os.path.basename(apk_path)}...")
            result = subprocess.run(
                [adb_path, "install", apk_path],
                capture_output=True, text=True
            ).stdout
            if "Success" in result:
                print("✅ 安装成功")
            else:
                print(f"⚠️ 安装可能失败：{result.splitlines()[-1]}")
        except Exception as e:
            print(f"❌ 安装失败：{str(e)}（请确保APK在esc目录或当前目录）")
    
    # 启动应用
    brand = get_device_brand()
    packages = APP_PACKAGES[brand]
    print(f"启动 {brand} 一碰传助手...")
    system(f'"{adb_path}" shell am start -n {packages["touchshare"]}')
    print('='*60)
    input('按回车键返回主菜单...')

def nfctool():
    """安装并启动NFC工具"""
    print('='*60)
    print('📌 NFC工具管理')
    print('='*60)
    adb_path = find_file("adb.exe") or "adb.exe"
    
    if input('是否安装NFC Tool？(y/n) ').strip().lower() == 'y':
        checkadb()
        apk_path = find_file("nfctool.apk", "esc") or "nfctool.apk"
        
        try:
            print(f"开始安装：{os.path.basename(apk_path)}...")
            result = subprocess.run(
                [adb_path, "install", apk_path],
                capture_output=True, text=True
            ).stdout
            if "Success" in result:
                print("✅ 安装成功")
            else:
                print(f"⚠️ 安装可能失败：{result.splitlines()[-1]}")
        except Exception as e:
            print(f"❌ 安装失败：{str(e)}（请确保APK在esc目录或当前目录）")
    
    # 启动应用
    print("启动NFC Tool（用于擦除标签）...")
    system(f'"{adb_path}" shell am start -n com.wakdev.nfctools.pro/.MainActivityPro')
    print("提示：打开后选择「其它」→「删除标签」")
    print('='*60)
    input('按回车键返回主菜单...')

def main_menu():
    """主菜单"""
    system('cls')
    print('='*70)
    print('一碰传标签工具（荣耀优化版 v1.5.13）')  # 版本号更新
    print('='*70)
    # 声明信息
    print("【声明信息】")
    print("-"*50)
    print("修改作者：爱吃丝绒蛋糕（荣耀论坛）")
    print(f"作者主页：https://club.honor.com/cn/space-uid-294574962.html")
    print(f"原项目地址：https://github.com/Masterchiefm/Thirdparty-huawei-Share-OneHop")
    print("使用提示：")
    print("1. 先连接平板用「5」生成标签，保存二维码，用包里其他手机带有NFC的安装NFC tool PRO 到其他页面删除以及格式化NFC标签。再在荣耀或者华为手机上使用一碰传助手 扫描二维码。 ")
    print("12 如果华为一碰传助手扫码失败，检查自己是否蓝牙MAC地址正确。或者检查设备识别码是否正确，如有其余荣耀设备，可以联系作者适配。华为一碰传APP最后提醒是成功。")
    print("2. 再连接手机用「2」 遇到擦除或者生成新标签的请求，直接选择N，返回主菜单也是选择N。因为这是生成电脑端口的标签。当然这里也有安装NFC TOOL PRO。")
    print("3. 程序异常时，可手动安装APK到设备，检查当前程序根目录是否存在ADB程序，或者C盘是否存在ADB程序。程序返回时，请直接选择N。")
    print("4.发现手机端智慧互联消失，请重新执行2同样步骤。如果经常找不到设备，请在开发者模式开启运行在仅仅充电时候运行ADB")
    print("5.如果你想要关闭音乐，请通过Windows音频处理器关闭该程序音乐声音大小")
    print('='*70)
    # 功能菜单
    print("\n【功能选项】")
    print("1. 生成电脑一碰传标签")
    print("2. 擦除手机标签记录（含重启流程）")
    print("3. 修复一碰传失效问题")
    print("4. 仅清除手机标签记录（不重启）")
    print("5. 生成平板一碰传标签")
    print('='*70)
    
    # 选项处理
    try:
        opt = int(input("请输入选项（1-5）：").strip())
    except ValueError:
        print("❌ 输入无效（请输入数字1-5）")
        input('按回车键返回...')
        return
    
    if opt == 1:
        touchshare()
        make_qr()
    elif opt == 2:
        print("\n⚠️ 警告：此操作会重启手机2次，请勿中断！")
        input("确认继续？（按回车）")
        disable_apps()
        print("重启手机（第1次）...")
        system(f'"{find_file("adb.exe") or "adb.exe"}" reboot')
        input("手机重启后连接电脑，按回车继续...")
        disable_apps()
        nfctool()
        input("标签擦除完成后，按回车继续...")
        if input("是否制作新标签？(y/n) ").strip().lower() == 'y':
            touchshare()
            make_qr()
        print("重启手机（第2次）...")
        system(f'"{find_file("adb.exe") or "adb.exe"}" reboot')
        input("手机重启后连接电脑，按回车继续...")
        enable_apps()
        print("✅ 操作完成：请开启手机NFC，重新扫描标签")
        input('按回车键返回主菜单...')
    elif opt == 3:
        print("开始修复一碰传失效...")
        input("请连接手机后按回车...")
        enable_apps()
        print("重启手机...")
        system(f'"{find_file("adb.exe") or "adb.exe"}" reboot')
        input("手机重启后，按回车继续...")
        enable_apps()
        print("✅ 修复完成：请开启NFC重试")
        input('按回车键返回主菜单...')
    elif opt == 4:
        print("开始清除手机标签记录...")
        disable_apps()
        enable_apps()
        print("✅ 记录清除完成（无需重启）")
        input('按回车键返回主菜单...')
    elif opt == 5:
        make_tablet_qr()
    else:
        print("❌ 无效选项（请输入1-5）")
        input('按回车键返回主菜单...')

# 程序入口
if __name__ == "__main__":
    while True:
        main_menu()
        if input("是否退出程序？(y/n) ").strip().lower() == 'y':
            print("感谢使用，再见！")
            break