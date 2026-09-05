# ============================================================
# IconDrop V0.7.1
# Windows Desktop Gravity + Rigid Body Collision + Mouse Stir Physics + Grid Lock Fix
#
# Features:
#   - Windows 11 Desktop Icon Physics
#   - Icon collision boxes
#   - Icon mass
#   - Icon-to-Icon collision
#   - Bounce / friction
#   - Multi-monitor
#   - Negative coordinates
#   - Taskbar work area
#   - Per-monitor DPI
#   - Safe Explorer cross-process memory
#   - 20 FPS physics
#   - Sleep system
#   - Original position restore
#   - Detailed diagnostics
# ============================================================

import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox
import threading
import time
import math
import traceback


# ============================================================
# Windows DLL
# ============================================================

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

try:
    shcore = ctypes.WinDLL("shcore", use_last_error=True)
except Exception:
    shcore = None


# ============================================================
# DPI
# ============================================================

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)


def enable_per_monitor_dpi():

    try:
        fn = user32.SetProcessDpiAwarenessContext
        fn.argtypes = [ctypes.c_void_p]
        fn.restype = wintypes.BOOL

        if fn(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2):
            return True

    except Exception:
        pass

    if shcore:

        try:
            fn = shcore.SetProcessDpiAwareness
            fn.argtypes = [ctypes.c_int]
            fn.restype = ctypes.c_long

            result = fn(2)

            if result == 0:
                return True

        except Exception:
            pass

    try:
        fn = user32.SetProcessDPIAware
        fn.argtypes = []
        fn.restype = wintypes.BOOL

        return bool(fn())

    except Exception:
        return False


enable_per_monitor_dpi()


# ============================================================
# Structures
# ============================================================

class POINT(ctypes.Structure):

    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class RECT(ctypes.Structure):

    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


# ============================================================
# User32 API
# ============================================================

user32.GetCursorPos.argtypes = [
    ctypes.POINTER(POINT),
]
user32.GetCursorPos.restype = wintypes.BOOL


user32.FindWindowW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
]
user32.FindWindowW.restype = wintypes.HWND


user32.FindWindowExW.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
]
user32.FindWindowExW.restype = wintypes.HWND


user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD


user32.IsWindow.argtypes = [
    wintypes.HWND,
]
user32.IsWindow.restype = wintypes.BOOL


user32.GetWindowLongPtrW.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
]
user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t


user32.GetDpiForWindow.argtypes = [
    wintypes.HWND,
]
user32.GetDpiForWindow.restype = wintypes.UINT


user32.ClientToScreen.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(POINT),
]
user32.ClientToScreen.restype = wintypes.BOOL


user32.ScreenToClient.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(POINT),
]
user32.ScreenToClient.restype = wintypes.BOOL


user32.MonitorFromPoint.argtypes = [
    POINT,
    wintypes.DWORD,
]
user32.MonitorFromPoint.restype = wintypes.HMONITOR


user32.GetMonitorInfoW.argtypes = [
    wintypes.HMONITOR,
    ctypes.POINTER(MONITORINFO),
]
user32.GetMonitorInfoW.restype = wintypes.BOOL


MONITOR_ENUM_PROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(RECT),
    wintypes.LPARAM,
)


user32.EnumDisplayMonitors.argtypes = [
    wintypes.HDC,
    ctypes.POINTER(RECT),
    MONITOR_ENUM_PROC,
    wintypes.LPARAM,
]

user32.EnumDisplayMonitors.restype = wintypes.BOOL


user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_size_t),
]

user32.SendMessageTimeoutW.restype = ctypes.c_ssize_t


# ============================================================
# Kernel32 API
# ============================================================

kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]

kernel32.OpenProcess.restype = wintypes.HANDLE


kernel32.CloseHandle.argtypes = [
    wintypes.HANDLE,
]

kernel32.CloseHandle.restype = wintypes.BOOL


kernel32.VirtualAllocEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_size_t,
    wintypes.DWORD,
    wintypes.DWORD,
]

kernel32.VirtualAllocEx.restype = ctypes.c_void_p


kernel32.VirtualFreeEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_size_t,
    wintypes.DWORD,
]

kernel32.VirtualFreeEx.restype = wintypes.BOOL


kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]

kernel32.ReadProcessMemory.restype = wintypes.BOOL


kernel32.WriteProcessMemory.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]

kernel32.WriteProcessMemory.restype = wintypes.BOOL


# ============================================================
# Constants
# ============================================================

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000

PAGE_READWRITE = 0x04

SMTO_ABORTIFHUNG = 0x0002
SMTO_BLOCK = 0x0001

LVM_FIRST = 0x1000

LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_GETITEMPOSITION = LVM_FIRST + 16
LVM_SETITEMPOSITION32 = LVM_FIRST + 49
LVM_GETITEMSPACING = LVM_FIRST + 51
LVM_SETEXTENDEDLISTVIEWSTYLE = LVM_FIRST + 54
LVM_GETEXTENDEDLISTVIEWSTYLE = LVM_FIRST + 55

LVS_AUTOARRANGE = 0x0100
LVS_EX_SNAPTOGRID = 0x00080000

GWLP_STYLE = -16

MONITOR_DEFAULTTONEAREST = 2


# ============================================================
# Utilities
# ============================================================

def win_error(prefix):

    error = ctypes.get_last_error()

    if error:

        try:
            text = ctypes.FormatError(error).strip()

        except Exception:
            text = "Unknown Windows error"

        return (
            f"{prefix}："
            f"错误码 {error}，"
            f"{text}"
        )

    return f"{prefix}：Windows 未返回错误码"


# ============================================================
# Monitor
# ============================================================

class MonitorInfoEx:

    def __init__(
        self,
        handle,
        monitor,
        work,
    ):

        self.handle = handle

        self.monitor = monitor
        self.work = work

        ml, mt, mr, mb = monitor
        wl, wt, wr, wb = work

        self.taskbar_edges = []

        if wl > ml:
            self.taskbar_edges.append("left")

        if wt > mt:
            self.taskbar_edges.append("top")

        if wr < mr:
            self.taskbar_edges.append("right")

        if wb < mb:
            self.taskbar_edges.append("bottom")


def enumerate_monitors():

    monitors = []

    def callback(
        hmonitor,
        hdc,
        rect_ptr,
        data,
    ):

        info = MONITORINFO()

        info.cbSize = ctypes.sizeof(
            MONITORINFO
        )

        if user32.GetMonitorInfoW(
            hmonitor,
            ctypes.byref(info),
        ):

            monitor = (
                info.rcMonitor.left,
                info.rcMonitor.top,
                info.rcMonitor.right,
                info.rcMonitor.bottom,
            )

            work = (
                info.rcWork.left,
                info.rcWork.top,
                info.rcWork.right,
                info.rcWork.bottom,
            )

            monitors.append(
                MonitorInfoEx(
                    hmonitor,
                    monitor,
                    work,
                )
            )

        return True

    callback_ref = MONITOR_ENUM_PROC(
        callback
    )

    user32.EnumDisplayMonitors(
        None,
        None,
        callback_ref,
        0,
    )

    return monitors


def monitor_for_point(
    x,
    y,
):

    pt = POINT(
        int(x),
        int(y),
    )

    hmonitor = user32.MonitorFromPoint(
        pt,
        MONITOR_DEFAULTTONEAREST,
    )

    if not hmonitor:
        return None

    for monitor in enumerate_monitors():

        if monitor.handle == hmonitor:
            return monitor

    return None


# ============================================================
# Find Desktop ListView
# ============================================================

def find_desktop_listview():

    # --------------------------------------------------------
    # Progman
    # --------------------------------------------------------

    progman = user32.FindWindowW(
        "Progman",
        None,
    )

    if progman:

        shell_view = user32.FindWindowExW(
            progman,
            None,
            "SHELLDLL_DefView",
            None,
        )

        if shell_view:

            listview = user32.FindWindowExW(
                shell_view,
                None,
                "SysListView32",
                None,
            )

            if listview:
                return listview

    # --------------------------------------------------------
    # WorkerW
    # --------------------------------------------------------

    worker = None

    while True:

        worker = user32.FindWindowExW(
            None,
            worker,
            "WorkerW",
            None,
        )

        if not worker:
            break

        shell_view = user32.FindWindowExW(
            worker,
            None,
            "SHELLDLL_DefView",
            None,
        )

        if shell_view:

            listview = user32.FindWindowExW(
                shell_view,
                None,
                "SysListView32",
                None,
            )

            if listview:
                return listview

    return None


# ============================================================
# Explorer Bridge
# ============================================================

class ExplorerBridge:

    def __init__(self):

        self.hwnd = None
        self.pid = None
        self.process = None
        self.remote_point = None

        self.connected = False

        self.last_error = ""
        self.last_valid_error = ""

        self.message_timeout = 150


    # --------------------------------------------------------
    # Close
    # --------------------------------------------------------

    def close(self):

        try:

            if (
                self.process
                and
                self.remote_point
            ):

                kernel32.VirtualFreeEx(
                    self.process,
                    self.remote_point,
                    0,
                    MEM_RELEASE,
                )

        except Exception:
            pass

        try:

            if self.process:

                kernel32.CloseHandle(
                    self.process
                )

        except Exception:
            pass

        self.hwnd = None
        self.pid = None
        self.process = None
        self.remote_point = None

        self.connected = False


    # --------------------------------------------------------
    # Connect
    # --------------------------------------------------------

    def connect(self):

        self.close()

        # 1. Find ListView
        hwnd = find_desktop_listview()

        if not hwnd:

            self.last_error = (
                "找不到桌面 SysListView32。\n\n"
                "请确认 Windows Explorer 正常运行。"
            )

            raise RuntimeError(
                self.last_error
            )

        # 2. Explorer PID
        pid = wintypes.DWORD()

        tid = user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(pid),
        )

        if not tid or not pid.value:

            self.last_error = win_error(
                "GetWindowThreadProcessId 失败"
            )

            raise RuntimeError(
                self.last_error
            )

        # 3. Open Explorer
        access = (
            PROCESS_VM_OPERATION
            |
            PROCESS_VM_READ
            |
            PROCESS_VM_WRITE
            |
            PROCESS_QUERY_INFORMATION
        )

        process = kernel32.OpenProcess(
            access,
            False,
            pid.value,
        )

        if not process:

            access = (
                PROCESS_VM_OPERATION
                |
                PROCESS_VM_READ
                |
                PROCESS_VM_WRITE
                |
                PROCESS_QUERY_LIMITED_INFORMATION
            )

            process = kernel32.OpenProcess(
                access,
                False,
                pid.value,
            )

        if not process:

            self.last_error = win_error(
                f"OpenProcess 失败，PID={pid.value}"
            )

            raise RuntimeError(
                self.last_error
            )

        # 4. Remote POINT
        remote_point = kernel32.VirtualAllocEx(
            process,
            None,
            ctypes.sizeof(POINT),
            MEM_COMMIT | MEM_RESERVE,
            PAGE_READWRITE,
        )

        if not remote_point:

            error = win_error(
                "VirtualAllocEx 失败"
            )

            kernel32.CloseHandle(
                process
            )

            self.last_error = error

            raise RuntimeError(
                error
            )

        # 5. Save
        self.hwnd = hwnd
        self.pid = int(pid.value)
        self.process = process
        self.remote_point = remote_point

        self.connected = True

        self.last_error = ""
        self.last_valid_error = ""

        # 6. Validate
        if not self.valid():

            error = (
                "Explorer Bridge 建立后验证失败：\n"
                +
                self.last_valid_error
            )

            self.close()

            self.last_error = error

            raise RuntimeError(
                error
            )

        return True


    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    def valid(self):

        self.last_valid_error = ""

        if not self.connected:

            self.last_valid_error = (
                "connected=False"
            )

            return False

        if not self.hwnd:

            self.last_valid_error = (
                "桌面 ListView HWND 无效"
            )

            return False

        if not user32.IsWindow(
            self.hwnd
        ):

            self.last_valid_error = (
                "桌面 ListView 窗口已经失效"
            )

            return False

        if not self.process:

            self.last_valid_error = (
                "Explorer Process Handle 无效"
            )

            return False

        if not self.remote_point:

            self.last_valid_error = (
                "远程 POINT 内存无效"
            )

            return False

        pid = wintypes.DWORD()

        user32.GetWindowThreadProcessId(
            self.hwnd,
            ctypes.byref(pid),
        )

        if not pid.value:

            self.last_valid_error = (
                "无法重新获取 ListView PID"
            )

            return False

        if int(pid.value) != self.pid:

            self.last_valid_error = (
                f"Explorer PID 已变化："
                f"{self.pid} -> {pid.value}"
            )

            return False

        return True


    # --------------------------------------------------------
    # Send Message
    # --------------------------------------------------------

    def send_message(
        self,
        msg,
        wparam=0,
        lparam=0,
        timeout=None,
    ):

        if not self.valid():

            raise RuntimeError(
                "Explorer Bridge 无效："
                +
                self.last_valid_error
            )

        if timeout is None:
            timeout = self.message_timeout

        result = ctypes.c_size_t()

        ret = user32.SendMessageTimeoutW(
            self.hwnd,
            msg,
            wparam,
            lparam,
            SMTO_ABORTIFHUNG | SMTO_BLOCK,
            timeout,
            ctypes.byref(result),
        )

        if not ret:

            raise RuntimeError(
                win_error(
                    f"SendMessageTimeoutW 失败，"
                    f"msg=0x{msg:X}"
                )
            )

        return result.value


    # --------------------------------------------------------
    # Icon Count
    # --------------------------------------------------------

    def get_icon_count(self):

        return int(
            self.send_message(
                LVM_GETITEMCOUNT
            )
        )


    # --------------------------------------------------------
    # Get Icon Position
    # --------------------------------------------------------

    def get_position(
        self,
        index,
    ):

        point = POINT()

        written = ctypes.c_size_t()

        if not kernel32.WriteProcessMemory(
            self.process,
            self.remote_point,
            ctypes.byref(point),
            ctypes.sizeof(point),
            ctypes.byref(written),
        ):

            raise RuntimeError(
                win_error(
                    "WriteProcessMemory 初始化 POINT 失败"
                )
            )

        self.send_message(
            LVM_GETITEMPOSITION,
            index,
            self.remote_point,
        )

        read = ctypes.c_size_t()

        if not kernel32.ReadProcessMemory(
            self.process,
            self.remote_point,
            ctypes.byref(point),
            ctypes.sizeof(point),
            ctypes.byref(read),
        ):

            raise RuntimeError(
                win_error(
                    f"ReadProcessMemory 获取图标 "
                    f"{index} 位置失败"
                )
            )

        if read.value != ctypes.sizeof(point):

            raise RuntimeError(
                "ReadProcessMemory 数据长度异常"
            )

        return (
            int(point.x),
            int(point.y),
        )


    # --------------------------------------------------------
    # Set Icon Position
    # --------------------------------------------------------

    def set_position(
        self,
        index,
        x,
        y,
    ):

        point = POINT(
            int(x),
            int(y),
        )

        written = ctypes.c_size_t()

        if not kernel32.WriteProcessMemory(
            self.process,
            self.remote_point,
            ctypes.byref(point),
            ctypes.sizeof(point),
            ctypes.byref(written),
        ):

            raise RuntimeError(
                win_error(
                    f"WriteProcessMemory 设置图标 "
                    f"{index} 位置失败"
                )
            )

        if written.value != ctypes.sizeof(point):

            raise RuntimeError(
                "WriteProcessMemory 写入长度异常"
            )

        self.send_message(
            LVM_SETITEMPOSITION32,
            index,
            self.remote_point,
        )


    # --------------------------------------------------------
    # Icon Spacing
    # --------------------------------------------------------

    def get_icon_spacing(self):

        value = self.send_message(
            LVM_GETITEMSPACING
        )

        x = value & 0xFFFF
        y = (
            value >> 16
        ) & 0xFFFF

        if x & 0x8000:
            x -= 0x10000

        if y & 0x8000:
            y -= 0x10000

        return (
            max(32, x),
            max(32, y),
        )


    # --------------------------------------------------------
    # Desktop ListView grid behavior
    # --------------------------------------------------------

    def get_extended_style(self):

        return int(
            self.send_message(
                LVM_GETEXTENDEDLISTVIEWSTYLE
            )
        )


    def set_extended_style(self, mask, value):

        self.send_message(
            LVM_SETEXTENDEDLISTVIEWSTYLE,
            mask,
            value,
        )


    def disable_snap_to_grid(self):

        try:
            style = self.get_extended_style()
            enabled = bool(style & LVS_EX_SNAPTOGRID)
            self._snap_to_grid_was_enabled = enabled

            if enabled:
                self.set_extended_style(
                    LVS_EX_SNAPTOGRID,
                    0,
                )

            return enabled

        except Exception:
            self._snap_to_grid_was_enabled = None
            return False


    def restore_snap_to_grid(self):

        state = self._snap_to_grid_was_enabled

        if state is None:
            return

        try:
            self.set_extended_style(
                LVS_EX_SNAPTOGRID,
                LVS_EX_SNAPTOGRID if state else 0,
            )
        except Exception:
            pass
        finally:
            self._snap_to_grid_was_enabled = None


    # --------------------------------------------------------
    # Auto Arrange
    # --------------------------------------------------------

    def has_auto_arrange(self):

        style = user32.GetWindowLongPtrW(
            self.hwnd,
            GWLP_STYLE,
        )

        return bool(
            style & LVS_AUTOARRANGE
        )


    # --------------------------------------------------------
    # Test
    # --------------------------------------------------------

    def test(self):

        if not self.valid():

            raise RuntimeError(
                "Explorer Bridge 无效："
                +
                self.last_valid_error
            )

        count = self.get_icon_count()

        if count > 0:

            x, y = self.get_position(0)

            self.set_position(
                0,
                x,
                y,
            )

        return count


# ============================================================
# Icon Rigid Body
# ============================================================

class IconBody:

    def __init__(
        self,
        index,
        x,
        y,
        width,
        height,
    ):

        self.index = index

        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        self.x = float(x)
        self.y = float(y)

        self.original_x = int(x)
        self.original_y = int(y)

        # ----------------------------------------------------
        # Collision Box
        # ----------------------------------------------------

        self.width = float(width)
        self.height = float(height)

        # ----------------------------------------------------
        # Mass
        # ----------------------------------------------------

        # 96x96 ≈ 1.0
        self.mass = (
            self.width
            *
            self.height
            /
            9216.0
        )

        self.mass = max(
            0.5,
            min(
                10.0,
                self.mass,
            )
        )

        # ----------------------------------------------------
        # Material
        # ----------------------------------------------------

        self.restitution = 0.34

        self.friction = 0.82

        # ----------------------------------------------------
        # Velocity
        # ----------------------------------------------------

        self.vx = 0.0
        self.vy = 0.0

        # ----------------------------------------------------
        # Last written position
        # ----------------------------------------------------

        self.last_write_x = int(x)
        self.last_write_y = int(y)

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.monitor = None

        self.sleeping = False
        self.sleep_timer = 0.0

        self.update_bounds()


    # ========================================================
    # Collision Bounds
    # ========================================================

    def update_bounds(self):

        self.left = self.x
        self.top = self.y

        self.right = (
            self.x
            +
            self.width
        )

        self.bottom = (
            self.y
            +
            self.height
        )

        self.center_x = (
            self.x
            +
            self.width / 2.0
        )

        self.center_y = (
            self.y
            +
            self.height / 2.0
        )


# ============================================================
# Physics Engine
# ============================================================

class PhysicsEngine:

    def __init__(
        self,
        bridge,
    ):

        self.bridge = bridge

        self.running = False
        self.paused = False

        self.thread = None

        self.error = None
        self.error_traceback = ""

        # ----------------------------------------------------
        # Physics
        # ----------------------------------------------------

        self.gravity = 1800.0

        self.default_restitution = 0.34

        self.default_friction = 0.82

        self.air_drag = 0.999

        self.target_fps = 20.0

        self.min_move = 1.5

        self.sleep_velocity = 35.0

        self.sleep_time = 0.25

        # ----------------------------------------------------
        # Mouse Stir Physics + Grid Lock Fix
        # ----------------------------------------------------
        # 鼠标被视为一个“无限质量”的圆形运动碰撞体。
        # 采用“上一帧 -> 当前帧”的鼠标轨迹做连续检测，
        # 即使物理线程只有 20 FPS，快速划过图标也不会轻易漏碰。
        self.mouse_radius = 52.0
        self.mouse_influence = 155.0
        self.mouse_push_strength = 2100.0
        self.mouse_stir_strength = 0.72
        self.mouse_collision_restitution = 0.72
        self.mouse_min_speed = 35.0
        self.mouse_max_speed = 2500.0

        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.prev_mouse_x = None
        self.prev_mouse_y = None
        self.mouse_segment_start_x = 0.0
        self.mouse_segment_start_y = 0.0
        self.mouse_vx = 0.0
        self.mouse_vy = 0.0

        # ----------------------------------------------------
        # Geometry
        # ----------------------------------------------------

        self.geometry_refresh = 1.0

        self.last_geometry_update = 0.0

        self.icon_width = 96
        self.icon_height = 96

        self.monitors = []

        self.icons = []

        self.lock = threading.RLock()

        # Explorer 桌面 ListView 状态。
        # SNAPTOGRID 会在我们移动图标后把图标吸回网格，
        # 看起来就像“鼠标推开后自动归位”。物理运行期间临时关闭，
        # 停止物理时恢复原来的状态。
        self._snap_to_grid_was_enabled = None


    # ========================================================
    # Monitor
    # ========================================================

    def update_monitors(self):

        monitors = enumerate_monitors()

        if not monitors:

            raise RuntimeError(
                "没有检测到显示器"
            )

        self.monitors = monitors


    # ========================================================
    # Find Monitor
    # ========================================================

    def find_monitor(
        self,
        x,
        y,
    ):

        for monitor in self.monitors:

            l, t, r, b = (
                monitor.monitor
            )

            if (
                l <= x < r
                and
                t <= y < b
            ):

                return monitor

        return monitor_for_point(
            int(x),
            int(y),
        )


    # ========================================================
    # Bounds
    # ========================================================

    def get_bounds(
        self,
        x,
        y,
    ):

        monitor = self.find_monitor(
            x,
            y,
        )

        if not monitor:

            raise RuntimeError(
                f"无法找到坐标 "
                f"({x:.1f},{y:.1f}) "
                f"所属显示器"
            )

        ml, mt, mr, mb = (
            monitor.monitor
        )

        wl, wt, wr, wb = (
            monitor.work
        )

        left = float(ml)

        top = float(mt)

        right = float(
            mr - self.icon_width
        )

        bottom = float(
            mb - self.icon_height
        )

        # Taskbar
        if "left" in monitor.taskbar_edges:
            left = float(wl)

        if "top" in monitor.taskbar_edges:
            top = float(wt)

        if "right" in monitor.taskbar_edges:
            right = float(
                wr - self.icon_width
            )

        if "bottom" in monitor.taskbar_edges:
            bottom = float(
                wb - self.icon_height
            )

        if right < left:
            right = left

        if bottom < top:
            bottom = top

        return (
            left,
            top,
            right,
            bottom,
        )


    # ========================================================
    # Screen -> ListView
    # ========================================================

    def screen_to_view(
        self,
        x,
        y,
    ):

        point = POINT(
            int(round(x)),
            int(round(y)),
        )

        if not user32.ScreenToClient(
            self.bridge.hwnd,
            ctypes.byref(point),
        ):

            raise RuntimeError(
                win_error(
                    "ScreenToClient 失败"
                )
            )

        return (
            int(point.x),
            int(point.y),
        )


    # ========================================================
    # ListView -> Screen
    # ========================================================

    def view_to_screen(
        self,
        x,
        y,
    ):

        point = POINT(
            int(round(x)),
            int(round(y)),
        )

        if not user32.ClientToScreen(
            self.bridge.hwnd,
            ctypes.byref(point),
        ):

            raise RuntimeError(
                win_error(
                    "ClientToScreen 失败"
                )
            )

        return (
            int(point.x),
            int(point.y),
        )


    # ========================================================
    # Capture Icons
    # ========================================================

    def capture_icons(self):

        count = self.bridge.get_icon_count()

        if count <= 0:

            raise RuntimeError(
                "桌面没有检测到图标"
            )

        spacing_x, spacing_y = (
            self.bridge.get_icon_spacing()
        )

        # ----------------------------------------------------
        # 碰撞箱尺寸
        #
        # Windows 图标位置是网格位置。
        # 使用 spacing 作为默认碰撞箱尺寸，
        # 再留出一点边距。
        # ----------------------------------------------------

        self.icon_width = max(
            48,
            int(spacing_x * 0.82),
        )

        self.icon_height = max(
            48,
            int(spacing_y * 0.82),
        )

        icons = []

        for index in range(count):

            try:

                vx, vy = (
                    self.bridge.get_position(
                        index
                    )
                )

                sx, sy = (
                    self.view_to_screen(
                        vx,
                        vy,
                    )
                )

                icon = IconBody(
                    index,
                    sx,
                    sy,
                    self.icon_width,
                    self.icon_height,
                )

                icon.restitution = (
                    self.default_restitution
                )

                icon.friction = (
                    self.default_friction
                )

                icon.monitor = (
                    self.find_monitor(
                        sx,
                        sy,
                    )
                )

                icons.append(
                    icon
                )

            except Exception as e:

                raise RuntimeError(
                    f"读取桌面图标 {index} 失败：\n"
                    f"{e}"
                )

        with self.lock:

            self.icons = icons

        return len(icons)


    # ========================================================
    # AABB Collision
    # ========================================================

    def check_collision(
        self,
        a,
        b,
    ):

        if a.right <= b.left:
            return False

        if a.left >= b.right:
            return False

        if a.bottom <= b.top:
            return False

        if a.top >= b.bottom:
            return False

        return True


    # ========================================================
    # Resolve Collision
    # ========================================================

    def resolve_collision(
        self,
        a,
        b,
    ):

        if not self.check_collision(
            a,
            b,
        ):

            return

        # ----------------------------------------------------
        # Center difference
        # ----------------------------------------------------

        dx = (
            b.center_x
            -
            a.center_x
        )

        dy = (
            b.center_y
            -
            a.center_y
        )

        overlap_x = (
            a.width / 2.0
            +
            b.width / 2.0
            -
            abs(dx)
        )

        overlap_y = (
            a.height / 2.0
            +
            b.height / 2.0
            -
            abs(dy)
        )

        if (
            overlap_x <= 0
            or
            overlap_y <= 0
        ):
            return

        # ----------------------------------------------------
        # Collision normal
        # ----------------------------------------------------

        if overlap_x < overlap_y:

            penetration = overlap_x

            if dx >= 0:
                nx = 1.0
            else:
                nx = -1.0

            ny = 0.0

        else:

            penetration = overlap_y

            nx = 0.0

            if dy >= 0:
                ny = 1.0
            else:
                ny = -1.0

        # ----------------------------------------------------
        # Mass
        # ----------------------------------------------------

        inv_mass_a = (
            1.0 / a.mass
        )

        inv_mass_b = (
            1.0 / b.mass
        )

        total_inv_mass = (
            inv_mass_a
            +
            inv_mass_b
        )

        if total_inv_mass <= 0:
            return

        # ----------------------------------------------------
        # Positional correction
        #
        # 防止 Icon 卡在一起
        # ----------------------------------------------------

        correction_percent = 0.85

        correction_slop = 0.01

        correction = (
            max(
                penetration
                -
                correction_slop,
                0.0,
            )
            *
            correction_percent
            /
            total_inv_mass
        )

        a.x -= (
            nx
            *
            correction
            *
            inv_mass_a
        )

        a.y -= (
            ny
            *
            correction
            *
            inv_mass_a
        )

        b.x += (
            nx
            *
            correction
            *
            inv_mass_b
        )

        b.y += (
            ny
            *
            correction
            *
            inv_mass_b
        )

        a.update_bounds()
        b.update_bounds()

        # ----------------------------------------------------
        # Relative velocity
        # ----------------------------------------------------

        rvx = (
            b.vx
            -
            a.vx
        )

        rvy = (
            b.vy
            -
            a.vy
        )

        velocity_along_normal = (
            rvx * nx
            +
            rvy * ny
        )

        # 已经分离
        if velocity_along_normal > 0:

            return

        # ----------------------------------------------------
        # Restitution
        # ----------------------------------------------------

        restitution = min(
            a.restitution,
            b.restitution,
        )

        # ----------------------------------------------------
        # Normal impulse
        # ----------------------------------------------------

        impulse = (
            -(1.0 + restitution)
            *
            velocity_along_normal
        )

        impulse /= total_inv_mass

        impulse_x = (
            impulse * nx
        )

        impulse_y = (
            impulse * ny
        )

        a.vx -= (
            impulse_x
            *
            inv_mass_a
        )

        a.vy -= (
            impulse_y
            *
            inv_mass_a
        )

        b.vx += (
            impulse_x
            *
            inv_mass_b
        )

        b.vy += (
            impulse_y
            *
            inv_mass_b
        )

        # ----------------------------------------------------
        # Tangential friction
        # ----------------------------------------------------

        tx = (
            rvx
            -
            velocity_along_normal
            *
            nx
        )

        ty = (
            rvy
            -
            velocity_along_normal
            *
            ny
        )

        tangent_length = math.sqrt(
            tx * tx
            +
            ty * ty
        )

        if tangent_length > 0.0001:

            tx /= tangent_length
            ty /= tangent_length

            tangent_velocity = (
                rvx * tx
                +
                rvy * ty
            )

            friction_impulse = (
                -tangent_velocity
            )

            friction_impulse /= (
                total_inv_mass
            )

            friction = math.sqrt(
                a.friction
                *
                b.friction
            )

            max_friction = (
                abs(impulse)
                *
                friction
            )

            friction_impulse = max(
                -max_friction,
                min(
                    max_friction,
                    friction_impulse,
                )
            )

            friction_x = (
                friction_impulse
                *
                tx
            )

            friction_y = (
                friction_impulse
                *
                ty
            )

            a.vx -= (
                friction_x
                *
                inv_mass_a
            )

            a.vy -= (
                friction_y
                *
                inv_mass_a
            )

            b.vx += (
                friction_x
                *
                inv_mass_b
            )

            b.vy += (
                friction_y
                *
                inv_mass_b
            )

        # ----------------------------------------------------
        # Wake up both bodies
        # ----------------------------------------------------

        a.sleeping = False
        b.sleeping = False

        a.sleep_timer = 0.0
        b.sleep_timer = 0.0


    # ========================================================
    # Resolve All Collisions
    # ========================================================

    def resolve_all_collisions(self):

        with self.lock:

            count = len(
                self.icons
            )

            # ------------------------------------------------
            # 多次迭代提高堆叠稳定性
            # ------------------------------------------------

            for _ in range(3):

                for i in range(count - 1):

                    a = self.icons[i]

                    for j in range(
                        i + 1,
                        count,
                    ):

                        b = self.icons[j]

                        self.resolve_collision(
                            a,
                            b,
                        )


    # ========================================================
    # Start
    # ========================================================

    def start(self):

        if self.running:
            return

        if not self.bridge.valid():

            raise RuntimeError(
                "Explorer Bridge 无效："
                +
                self.bridge.last_valid_error
            )

        self.bridge.test()

        self.update_monitors()

        count = self.capture_icons()

        if self.bridge.has_auto_arrange():

            raise RuntimeError(
                "Windows 桌面当前启用了“自动排列图标”。\n\n"
                "请关闭：\n"
                "右键桌面 → 查看 → 自动排列图标"
            )

        # 关键修复：关闭“将图标与网格对齐”。
        # 否则 Explorer 可能在 LVM_SETITEMPOSITION32 后再次吸附图标，
        # 导致鼠标搅动后图标看起来自动回到原网格位置。
        # 修改点：调用 bridge 的方法
        self.bridge.disable_snap_to_grid()

        self.error = None
        self.error_traceback = ""

        self.running = True
        self.paused = False

        self.last_geometry_update = (
            time.monotonic()
        )

        self.reset_mouse_state()

        self.thread = threading.Thread(
            target=self.loop,
            daemon=True,
            name="IconDropPhysics",
        )

        self.thread.start()

        return count


    # ========================================================
    # Stop
    # ========================================================

    def stop(self):

        self.running = False

        thread = self.thread

        if (
            thread
            and
            thread.is_alive()
        ):

            thread.join(
                timeout=1.5
            )

        self.thread = None

        # 物理停止后恢复用户原来的“与网格对齐”设置。
        # 修改点：调用 bridge 的方法
        self.bridge.restore_snap_to_grid()


    # ========================================================
    # Pause
    # ========================================================

    def pause(self):

        if self.running:

            self.paused = True


    # ========================================================
    # Resume
    # ========================================================

    def resume(self):

        if self.running:

            self.paused = False

            # 唤醒所有图标
            with self.lock:

                for icon in self.icons:

                    icon.sleeping = False
                    icon.sleep_timer = 0.0


    # ========================================================
    # Mouse State
    # ========================================================

    def reset_mouse_state(self):

        point = POINT()

        try:
            if user32.GetCursorPos(ctypes.byref(point)):
                self.mouse_x = float(point.x)
                self.mouse_y = float(point.y)
                self.prev_mouse_x = self.mouse_x
                self.prev_mouse_y = self.mouse_y
                self.mouse_segment_start_x = self.mouse_x
                self.mouse_segment_start_y = self.mouse_y
            else:
                self.mouse_x = 0.0
                self.mouse_y = 0.0
                self.prev_mouse_x = None
                self.prev_mouse_y = None
                self.mouse_segment_start_x = 0.0
                self.mouse_segment_start_y = 0.0
        except Exception:
            self.mouse_x = 0.0
            self.mouse_y = 0.0
            self.prev_mouse_x = None
            self.prev_mouse_y = None

        self.mouse_vx = 0.0
        self.mouse_vy = 0.0


    def update_mouse_state(self, dt):

        point = POINT()

        try:
            if not user32.GetCursorPos(ctypes.byref(point)):
                self.mouse_vx = 0.0
                self.mouse_vy = 0.0
                return

            x = float(point.x)
            y = float(point.y)

            if (
                self.prev_mouse_x is None
                or self.prev_mouse_y is None
            ):
                self.mouse_x = x
                self.mouse_y = y
                self.prev_mouse_x = x
                self.prev_mouse_y = y
                self.mouse_vx = 0.0
                self.mouse_vy = 0.0
                return

            old_x = self.prev_mouse_x
            old_y = self.prev_mouse_y

            self.mouse_segment_start_x = old_x
            self.mouse_segment_start_y = old_y
            self.mouse_x = x
            self.mouse_y = y

            safe_dt = max(0.001, float(dt))

            self.mouse_vx = (x - old_x) / safe_dt
            self.mouse_vy = (y - old_y) / safe_dt

            speed = math.hypot(
                self.mouse_vx,
                self.mouse_vy,
            )

            if speed > self.mouse_max_speed:
                scale = self.mouse_max_speed / speed
                self.mouse_vx *= scale
                self.mouse_vy *= scale

            self.prev_mouse_x = x
            self.prev_mouse_y = y

        except Exception:
            self.mouse_vx = 0.0
            self.mouse_vy = 0.0
            self.mouse_segment_start_x = self.mouse_x
            self.mouse_segment_start_y = self.mouse_y


    @staticmethod
    def closest_point_on_segment(
        px,
        py,
        ax,
        ay,
        bx,
        by,
    ):

        sx = bx - ax
        sy = by - ay
        length_sq = sx * sx + sy * sy

        if length_sq <= 0.000001:
            return ax, ay

        t = (
            (px - ax) * sx
            +
            (py - ay) * sy
        ) / length_sq

        t = max(0.0, min(1.0, t))

        return (
            ax + sx * t,
            ay + sy * t,
        )


    # ========================================================
    # Mouse Stir
    # ========================================================

    def apply_mouse_stir(self, dt):

        speed = math.hypot(
            self.mouse_vx,
            self.mouse_vy,
        )

        if speed < self.mouse_min_speed:
            return

        speed_ratio = min(
            1.0,
            speed / self.mouse_max_speed,
        )

        # 上一帧到当前帧的轨迹。
        # 连续线段检测可以避免 20 FPS 下鼠标快速移动“穿过”图标。
        ax = self.mouse_segment_start_x
        ay = self.mouse_segment_start_y
        bx = self.mouse_x
        by = self.mouse_y

        mouse_dir_x = self.mouse_vx / max(speed, 0.001)
        mouse_dir_y = self.mouse_vy / max(speed, 0.001)

        for icon in self.icons:

            closest_x, closest_y = (
                self.closest_point_on_segment(
                    icon.center_x,
                    icon.center_y,
                    ax,
                    ay,
                    bx,
                    by,
                )
            )

            dx = icon.center_x - closest_x
            dy = icon.center_y - closest_y
            distance = math.hypot(dx, dy)

            # 图标本身也占据空间，因此有效碰撞半径随图标尺寸变化。
            icon_radius = 0.5 * min(
                icon.width,
                icon.height,
            )

            collision_radius = (
                self.mouse_radius
                +
                icon_radius * 0.42
            )

            if distance > self.mouse_influence + icon_radius:
                continue

            if distance > 0.001:
                nx = dx / distance
                ny = dy / distance
            else:
                # 鼠标正好落在图标中心时，用鼠标运动方向的法线
                # 作为稳定的推出方向，避免除零和方向抖动。
                nx = -mouse_dir_y
                ny = mouse_dir_x

            influence = 1.0 - min(
                1.0,
                max(0.0, distance / (self.mouse_influence + icon_radius)),
            )

            # ------------------------------------------------
            # 1. Radial push：鼠标扫过时把图标向外掀起。
            # ------------------------------------------------
            radial_accel = (
                self.mouse_push_strength
                *
                influence
                *
                (0.35 + 0.65 * speed_ratio)
            )

            icon.vx += (
                nx * radial_accel * dt / icon.mass
            )
            icon.vy += (
                ny * radial_accel * dt / icon.mass
            )

            # ------------------------------------------------
            # 2. Tangential stir：沿圆周方向“搅动”图标。
            # ------------------------------------------------
            tx = -ny
            ty = nx

            tangent_mouse_speed = (
                self.mouse_vx * tx
                +
                self.mouse_vy * ty
            )

            # 鼠标运动方向决定顺/逆时针；当投影很小时，
            # 使用鼠标运动方向本身，保证横扫图标时仍有明显搅动。
            if abs(tangent_mouse_speed) < speed * 0.08:
                tangent_mouse_speed = speed * (
                    mouse_dir_x * tx
                    +
                    mouse_dir_y * ty
                )

            tangential_accel = (
                tangent_mouse_speed
                *
                self.mouse_stir_strength
                *
                7.5
                *
                influence
            )

            # 防止极端 DPI/鼠标采样造成单帧爆速。
            tangential_accel = max(
                -5000.0,
                min(5000.0, tangential_accel),
            )

            icon.vx += (
                tx * tangential_accel * dt / icon.mass
            )
            icon.vy += (
                ty * tangential_accel * dt / icon.mass
            )

            # ------------------------------------------------
            # 3. 真正进入圆形碰撞体时，做一次 kinematic impulse。
            # ------------------------------------------------
            if distance < collision_radius:

                penetration = (
                    collision_radius - distance
                )

                # 位置轻微推出，防止鼠标穿过后图标卡在碰撞体内部。
                correction = min(
                    penetration * 0.55,
                    18.0,
                )

                icon.x += nx * correction
                icon.y += ny * correction

                icon.update_bounds()

                relative_normal_speed = (
                    (icon.vx - self.mouse_vx) * nx
                    +
                    (icon.vy - self.mouse_vy) * ny
                )

                if relative_normal_speed < 0.0:
                    impulse = (
                        -relative_normal_speed
                        *
                        (1.0 + self.mouse_collision_restitution)
                    )

                    icon.vx += (
                        nx * impulse
                    )
                    icon.vy += (
                        ny * impulse
                    )

                # 鼠标实际碰到图标时，确保它从 sleep 状态唤醒。
                icon.sleeping = False
                icon.sleep_timer = 0.0


    # ========================================================
    # Physics Step
    # ========================================================

    def step(
        self,
        dt,
    ):

        now = time.monotonic()

        if (
            now
            -
            self.last_geometry_update
            >=
            self.geometry_refresh
        ):

            self.update_monitors()

            self.last_geometry_update = now

        self.update_mouse_state(dt)

        with self.lock:

            # ------------------------------------------------
            # Physics Integration
            # ------------------------------------------------

            for icon in self.icons:

                if icon.sleeping:
                    continue

                # Gravity
                icon.vy += (
                    self.gravity
                    *
                    dt
                )

                # Air drag
                drag = (
                    self.air_drag
                    **
                    (dt * 60.0)
                )

                icon.vx *= drag
                icon.vy *= drag

                # Position
                icon.x += (
                    icon.vx
                    *
                    dt
                )

                icon.y += (
                    icon.vy
                    *
                    dt
                )

                icon.update_bounds()

                # ------------------------------------------------
                # Desktop boundary
                # ------------------------------------------------

                left, top, right, bottom = (
                    self.get_bounds(
                        icon.x,
                        icon.y,
                    )
                )

                collided = False

                # Left
                if icon.x < left:

                    icon.x = left

                    if icon.vx < 0:

                        icon.vx = (
                            -icon.vx
                            *
                            icon.restitution
                        )

                    collided = True

                # Right
                if icon.x > right:

                    icon.x = right

                    if icon.vx > 0:

                        icon.vx = (
                            -icon.vx
                            *
                            icon.restitution
                        )

                    collided = True

                # Top
                if icon.y < top:

                    icon.y = top

                    if icon.vy < 0:

                        icon.vy = (
                            -icon.vy
                            *
                            icon.restitution
                        )

                    collided = True

                # Bottom
                if icon.y > bottom:

                    icon.y = bottom

                    if icon.vy > 0:

                        icon.vy = (
                            -icon.vy
                            *
                            icon.restitution
                        )

                    icon.vx *= (
                        icon.friction
                    )

                    collided = True

                icon.update_bounds()

            # ------------------------------------------------
            # Mouse Stir Physics + Grid Lock Fix
            # ------------------------------------------------
            self.apply_mouse_stir(dt)

            # ------------------------------------------------
            # Icon-to-Icon collision
            # ------------------------------------------------

            self.resolve_all_collisions()

            # ------------------------------------------------
            # Sleep detection
            # ------------------------------------------------

            for icon in self.icons:

                if icon.sleeping:
                    continue

                speed = math.sqrt(
                    icon.vx * icon.vx
                    +
                    icon.vy * icon.vy
                )

                if speed < self.sleep_velocity:

                    # 只在接近地面时累计睡眠时间
                    _, _, _, bottom = (
                        self.get_bounds(
                            icon.x,
                            icon.y,
                        )
                    )

                    distance_to_ground = (
                        abs(
                            icon.y
                            -
                            bottom
                        )
                    )

                    if (
                        distance_to_ground
                        < 3.0
                    ):

                        icon.sleep_timer += dt

                    else:

                        icon.sleep_timer = 0.0

                    if (
                        icon.sleep_timer
                        >=
                        self.sleep_time
                    ):

                        icon.sleeping = True

                        icon.vx = 0.0
                        icon.vy = 0.0

                else:

                    icon.sleep_timer = 0.0


    # ========================================================
    # Flush
    # ========================================================

    def flush_positions(self):

        with self.lock:

            for icon in self.icons:

                if icon.sleeping:
                    continue

                x = int(
                    round(icon.x)
                )

                y = int(
                    round(icon.y)
                )

                dx = abs(
                    x
                    -
                    icon.last_write_x
                )

                dy = abs(
                    y
                    -
                    icon.last_write_y
                )

                if (
                    dx < self.min_move
                    and
                    dy < self.min_move
                ):

                    continue

                vx, vy = (
                    self.screen_to_view(
                        x,
                        y,
                    )
                )

                try:

                    self.bridge.set_position(
                        icon.index,
                        vx,
                        vy,
                    )

                except Exception as e:

                    raise RuntimeError(
                        f"写入图标 "
                        f"{icon.index} "
                        f"位置失败：\n"
                        f"屏幕坐标=({x},{y})\n"
                        f"ListView坐标=({vx},{vy})\n"
                        f"{e}"
                    )

                icon.last_write_x = x
                icon.last_write_y = y


    # ========================================================
    # Loop
    # ========================================================

    def loop(self):

        interval = (
            1.0
            /
            self.target_fps
        )

        last = time.monotonic()

        try:

            while self.running:

                frame_start = (
                    time.monotonic()
                )

                if not self.paused:

                    now = time.monotonic()

                    dt = (
                        now
                        -
                        last
                    )

                    last = now

                    dt = max(
                        0.001,
                        min(
                            0.05,
                            dt,
                        )
                    )

                    self.step(
                        dt
                    )

                    self.flush_positions()

                else:

                    last = (
                        time.monotonic()
                    )

                elapsed = (
                    time.monotonic()
                    -
                    frame_start
                )

                sleep_time = (
                    interval
                    -
                    elapsed
                )

                if sleep_time > 0:

                    time.sleep(
                        sleep_time
                    )

        except Exception as e:

            self.error = str(e)

            self.error_traceback = (
                traceback.format_exc()
            )

        finally:

            self.running = False


    # ========================================================
    # Restore
    # ========================================================

    def restore(self):

        if not self.bridge.valid():

            raise RuntimeError(
                "Explorer Bridge 无效，"
                "无法恢复图标："
                +
                self.bridge.last_valid_error
            )

        with self.lock:

            for icon in self.icons:

                try:

                    vx, vy = (
                        self.screen_to_view(
                            icon.original_x,
                            icon.original_y,
                        )
                    )

                    self.bridge.set_position(
                        icon.index,
                        vx,
                        vy,
                    )

                    icon.x = (
                        icon.original_x
                    )

                    icon.y = (
                        icon.original_y
                    )

                    icon.vx = 0.0
                    icon.vy = 0.0
                    icon.sleeping = False
                    icon.sleep_timer = 0.0

                    icon.update_bounds()

                except Exception:
                    pass

        # restore() 也可能在未经过 stop() 的情况下被调用。
        # 修改点：调用 bridge 的方法
        self.bridge.restore_snap_to_grid()


# ============================================================
# GUI
# ============================================================

class IconDropApp:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(
            "IconDrop V0.7.1"
        )

        self.root.geometry(
            "540x560"
        )

        self.root.resizable(
            False,
            False,
        )

        self.bridge = (
            ExplorerBridge()
        )

        self.physics = (
            PhysicsEngine(
                self.bridge
            )
        )

        self.status_var = tk.StringVar(
            value="未连接 Explorer"
        )

        self.icon_var = tk.StringVar(
            value="0"
        )

        self.monitor_var = tk.StringVar(
            value="检测中"
        )

        self.dpi_var = tk.StringVar(
            value="未知"
        )

        self.gravity_var = tk.StringVar(
            value="1800"
        )

        self.build_ui()

        self.root.bind(
            "<F8>",
            lambda e: self.start()
        )

        self.root.bind(
            "<F9>",
            lambda e: self.pause()
        )

        self.root.bind(
            "<F10>",
            lambda e: self.restore()
        )

        self.root.bind(
            "<Escape>",
            lambda e: self.exit()
        )

        self.root.after(
            300,
            self.update_status
        )


    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        tk.Label(
            self.root,
            text="IconDrop V0.7.1",
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
        ).pack(
            pady=(20, 5)
        )

        tk.Label(
            self.root,
            text="(。・∀・ノ",
            font=(
                "Segoe UI",
                9,
            ),
        ).pack(
            pady=(0, 20)
        )

        info = tk.Frame(
            self.root
        )

        info.pack(
            padx=30,
            fill="x"
        )

        self.add_info(
            info,
            "状态",
            self.status_var,
        )

        self.add_info(
            info,
            "桌面图标",
            self.icon_var,
        )

        self.add_info(
            info,
            "显示器",
            self.monitor_var,
        )

        self.add_info(
            info,
            "DPI",
            self.dpi_var,
        )

        gravity_frame = tk.Frame(
            self.root
        )

        gravity_frame.pack(
            pady=20
        )

        tk.Label(
            gravity_frame,
            text="重力：",
        ).pack(
            side="left"
        )

        tk.Entry(
            gravity_frame,
            textvariable=self.gravity_var,
            width=10,
        ).pack(
            side="left"
        )

        tk.Label(
            gravity_frame,
            text=" px/s²",
        ).pack(
            side="left"
        )

        buttons = tk.Frame(
            self.root
        )

        buttons.pack(
            pady=10
        )

        tk.Button(
            buttons,
            text="连接 Explorer",
            width=18,
            command=self.connect,
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
        )

        tk.Button(
            buttons,
            text="开始物理",
            width=18,
            command=self.start,
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
        )

        tk.Button(
            buttons,
            text="暂停 / 继续",
            width=18,
            command=self.pause,
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
        )

        tk.Button(
            buttons,
            text="恢复原位置",
            width=18,
            command=self.restore,
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
        )

        tk.Button(
            self.root,
            text="退出",
            width=38,
            command=self.exit,
        ).pack(
            pady=15
        )

        tk.Label(
            self.root,
            text=(
                "F8  开始物理\n"
                "F9  暂停 / 继续\n"
                "F10 恢复原位置\n"
                "ESC 退出"
            ),
            justify="left",
            font=(
                "Segoe UI",
                9,
            ),
        ).pack(
            pady=5
        )

        tk.Label(
            self.root,
            text=(
                "物理模型：重力 + 质量 + AABB碰撞 + "
                "反弹 + 摩擦 + 堆叠"
            ),
            font=(
                "Segoe UI",
                8,
            ),
        ).pack(
            pady=10
        )


    def add_info(
        self,
        parent,
        name,
        variable,
    ):

        frame = tk.Frame(
            parent
        )

        frame.pack(
            fill="x",
            pady=4
        )

        tk.Label(
            frame,
            text=name,
            width=12,
            anchor="w",
        ).pack(
            side="left"
        )

        tk.Label(
            frame,
            textvariable=variable,
            anchor="w",
        ).pack(
            side="left"
        )


    # ========================================================
    # Connect
    # ========================================================

    def connect(self):

        try:

            self.status_var.set(
                "正在连接 Explorer..."
            )

            self.root.update_idletasks()

            self.bridge.connect()

            count = (
                self.bridge.test()
            )

            self.icon_var.set(
                str(count)
            )

            if self.bridge.hwnd:

                dpi = (
                    user32.GetDpiForWindow(
                        self.bridge.hwnd
                    )
                )

                self.dpi_var.set(
                    f"{dpi} DPI"
                    if dpi
                    else "未知"
                )

            monitors = (
                enumerate_monitors()
            )

            self.monitor_var.set(
                f"{len(monitors)} 个显示器"
            )

            self.status_var.set(
                "Explorer 连接成功"
            )

            return True

        except Exception as e:

            error = str(e)

            bridge_error = getattr(
                self.bridge,
                "last_error",
                "",
            )

            if (
                bridge_error
                and
                bridge_error not in error
            ):

                error += (
                    "\n\nBridge：\n"
                    +
                    bridge_error
                )

            try:
                self.bridge.close()
            except Exception:
                pass

            self.status_var.set(
                "连接失败"
            )

            messagebox.showerror(
                "IconDrop Explorer Bridge",
                error,
            )

            return False


    # ========================================================
    # Start
    # ========================================================

    def start(self):

        try:

            if not self.bridge.valid():

                if not self.connect():

                    return

            try:

                gravity = float(
                    self.gravity_var.get()
                )

                if gravity < 0:

                    raise ValueError

                self.physics.gravity = (
                    gravity
                )

            except Exception:

                messagebox.showerror(
                    "参数错误",
                    "重力必须是大于等于 0 的数字。",
                )

                return

            count = (
                self.physics.start()
            )

            self.icon_var.set(
                str(count)
            )

            self.status_var.set(
                "物理模拟运行中"
            )

        except Exception as e:

            messagebox.showerror(
                "启动物理模拟失败",
                str(e),
            )

            self.status_var.set(
                "物理模拟启动失败"
            )


    # ========================================================
    # Pause
    # ========================================================

    def pause(self):

        if not self.physics.running:

            return

        if self.physics.paused:

            self.physics.resume()

            self.status_var.set(
                "物理模拟运行中"
            )

        else:

            self.physics.pause()

            self.status_var.set(
                "物理模拟已暂停"
            )


    # ========================================================
    # Restore
    # ========================================================

    def restore(self):

        try:

            self.physics.stop()

            if self.physics.icons:

                self.physics.restore()

                self.status_var.set(
                    "图标已恢复原位置"
                )

        except Exception as e:

            messagebox.showerror(
                "恢复失败",
                str(e),
            )


    # ========================================================
    # Status
    # ========================================================

    def update_status(self):

        try:

            if self.physics.error:

                error = (
                    self.physics.error
                )

                trace = (
                    self.physics.error_traceback
                )

                self.physics.error = None

                messagebox.showerror(
                    "物理模拟发生错误",
                    error
                    +
                    "\n\n详细信息：\n"
                    +
                    trace,
                )

                self.status_var.set(
                    "物理模拟异常停止"
                )

            elif self.physics.running:

                if self.physics.paused:

                    self.status_var.set(
                        "物理模拟已暂停"
                    )

                else:

                    self.status_var.set(
                        "物理模拟运行中"
                    )

        except Exception:
            pass

        self.root.after(
            300,
            self.update_status
        )


    # ========================================================
    # Exit
    # ========================================================

    def exit(self):

        try:

            self.physics.stop()

            if self.physics.icons:

                try:
                    self.physics.restore()
                except Exception:
                    pass

            self.bridge.close()

        finally:

            self.root.destroy()


    # ========================================================
    # Run
    # ========================================================

    def run(self):

        self.root.mainloop()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    app = IconDropApp()

    app.run()
