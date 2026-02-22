"""
USB软件狗（硬件加密锁）验证模块
支持多种USB加密锁的检测和验证
"""
import os
import sys
import logging
from typing import Optional, Tuple, Dict
from ctypes import windll, c_char_p, c_int, c_uint, byref, create_string_buffer, POINTER
from ctypes.wintypes import DWORD, HANDLE

logger = logging.getLogger(__name__)


class USBDongleChecker:
    """USB软件狗检测器"""
    
    def __init__(self):
        self.dongle_detected = False
        self.dongle_info = {}
        self.sdk_path = None
        
    def check_dongle_available(self) -> bool:
        """
        检查USB软件狗是否可用
        
        Returns:
            bool: 如果检测到有效的软件狗返回True
        """
        try:
            # 方法1: 尝试使用HID设备检测（通用方法）
            if self._check_hid_device():
                return True
            
            # 方法2: 尝试使用特定加密锁SDK（需要安装对应驱动）
            if self._check_specific_dongle():
                return True
                
            # 方法3: 检查USB设备列表
            if self._check_usb_devices():
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"检测USB软件狗时出错: {e}")
            return False
    
    def _check_hid_device(self) -> bool:
        """通过HID接口检测USB设备"""
        try:
            # 尝试导入hidapi（需要安装: pip install hidapi）
            try:
                import hid
            except ImportError:
                logger.debug("hidapi未安装，跳过HID检测")
                return False
            
            # 枚举HID设备
            devices = hid.enumerate()
            
            # 查找可能的加密锁设备（根据VID/PID识别）
            # 这里需要根据实际使用的加密锁型号设置VID/PID
            dongle_vids = [
                0x0529,  # 示例VID（需要替换为实际值）
                0x1234,  # 示例VID
            ]
            
            for device in devices:
                vid = device.get('vendor_id', 0)
                pid = device.get('product_id', 0)
                
                if vid in dongle_vids:
                    self.dongle_detected = True
                    self.dongle_info = {
                        'vendor_id': vid,
                        'product_id': pid,
                        'manufacturer': device.get('manufacturer_string', ''),
                        'product': device.get('product_string', ''),
                        'serial': device.get('serial_number', ''),
                    }
                    logger.info(f"检测到USB软件狗: VID={vid:04X}, PID={pid:04X}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug(f"HID检测失败: {e}")
            return False
    
    def _check_specific_dongle(self) -> bool:
        """检查特定品牌的加密锁（如SafeNet Sentinel, Wibu等）"""
        try:
            # 示例：检查SafeNet Sentinel加密锁
            # 需要安装Sentinel HASP/LDK运行时库
            sentinel_dll_paths = [
                r"C:\Windows\System32\hasplms.dll",
                r"C:\Windows\System32\aksusb.dll",
            ]
            
            for dll_path in sentinel_dll_paths:
                if os.path.exists(dll_path):
                    try:
                        # 尝试加载DLL并调用检测函数
                        dll = windll.LoadLibrary(dll_path)
                        # 这里需要根据实际SDK文档调用相应函数
                        # result = dll.SomeDetectionFunction()
                        logger.info(f"找到加密锁SDK: {dll_path}")
                        return True
                    except Exception as e:
                        logger.debug(f"加载SDK失败: {e}")
                        continue
                        
            return False
            
        except Exception as e:
            logger.debug(f"特定加密锁检测失败: {e}")
            return False
    
    def _check_usb_devices(self) -> bool:
        """通过Windows API检查USB设备"""
        try:
            if sys.platform != 'win32':
                return False
                
            # 使用Windows SetupAPI枚举USB设备
            # 这需要更复杂的实现，这里提供简化版本
            import subprocess
            
            # 使用wmic命令查询USB设备（Windows）
            try:
                result = subprocess.run(
                    ['wmic', 'path', 'win32_usbcontrollerdevice', 'get', 'dependent'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    # 解析输出，查找可能的加密锁设备
                    output = result.stdout.lower()
                    # 根据设备描述或厂商ID识别
                    keywords = ['dongle', 'key', 'lock', 'sentinel', 'hasp', 'wibu']
                    for keyword in keywords:
                        if keyword in output:
                            logger.info(f"可能检测到加密锁设备（关键词: {keyword}）")
                            return True
                            
            except Exception:
                pass
                
            return False
            
        except Exception as e:
            logger.debug(f"USB设备检测失败: {e}")
            return False
    
    def verify_license(self, license_key: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证软件授权
        
        Args:
            license_key: 可选的许可证密钥
            
        Returns:
            (是否授权, 消息)
        """
        if not self.check_dongle_available():
            return False, "未检测到USB软件狗，请插入加密锁后重试"
        
        # 如果检测到软件狗，可以进行进一步验证
        # 例如：读取软件狗中的授权信息、验证签名等
        
        try:
            # 这里可以添加更复杂的验证逻辑
            # 例如：读取软件狗中的序列号、验证授权期限等
            
            if self.dongle_info:
                serial = self.dongle_info.get('serial', '')
                if serial:
                    logger.info(f"软件狗序列号: {serial}")
            
            return True, "USB软件狗验证成功"
            
        except Exception as e:
            logger.error(f"验证授权时出错: {e}")
            return False, f"授权验证失败: {str(e)}"
    
    def get_dongle_info(self) -> Dict:
        """获取软件狗信息"""
        return self.dongle_info.copy() if self.dongle_info else {}


class SimpleDongleChecker:
    """
    简化版USB软件狗检测器
    不依赖第三方库，使用系统命令检测
    """
    
    @staticmethod
    def check_dongle() -> bool:
        """检查是否有USB软件狗"""
        try:
            if sys.platform == 'win32':
                # Windows: 使用wmic查询USB设备
                import subprocess
                result = subprocess.run(
                    ['wmic', 'path', 'win32_pnpentity', 'where', 
                     'DeviceID like "%USB%"', 'get', 'Name'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    output = result.stdout.lower()
                    # 查找可能的加密锁关键词
                    keywords = ['dongle', 'key', 'lock', 'sentinel', 'hasp', 'wibu', '加密']
                    for keyword in keywords:
                        if keyword in output:
                            logger.info(f"检测到可能的加密锁设备: {keyword}")
                            return True
                            
            elif sys.platform == 'linux':
                # Linux: 使用lsusb命令
                import subprocess
                result = subprocess.run(
                    ['lsusb'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    output = result.stdout.lower()
                    keywords = ['dongle', 'key', 'lock', 'sentinel', 'hasp']
                    for keyword in keywords:
                        if keyword in output:
                            return True
                            
            return False
            
        except Exception as e:
            logger.error(f"检测USB软件狗失败: {e}")
            return False


def check_usb_dongle() -> Tuple[bool, str]:
    """
    便捷函数：检查USB软件狗
    
    Returns:
        (是否检测到, 消息)
    """
    checker = USBDongleChecker()
    detected = checker.check_dongle_available()
    
    if detected:
        return True, "USB软件狗已检测到"
    else:
        return False, "未检测到USB软件狗"


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("检测USB软件狗...")
    checker = USBDongleChecker()
    
    if checker.check_dongle_available():
        print("✓ USB软件狗已检测到")
        print(f"设备信息: {checker.get_dongle_info()}")
        
        authorized, msg = checker.verify_license()
        print(f"授权状态: {msg}")
    else:
        print("✗ 未检测到USB软件狗")

