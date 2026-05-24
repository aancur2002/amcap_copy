import serial
import serial.tools.list_ports
import win32gui
import win32api
import os
import traceback
import subprocess
import time
from pynput import keyboard, mouse

# ================================================================
#  CONFIGURATION & STORAGE MANAGEMENT
# ================================================================
BAUD_RATE   = 115200
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
AMCAP_EXE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amcap.exe")

def save_config(port, window):
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(f"{port}\n{window}")
    except: pass

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2: return lines[0], lines[1]
        except: pass
    return None, None

def get_all_windows():
    windows = []
    try:
        win32gui.EnumWindows(lambda hwnd, _: windows.append(win32gui.GetWindowText(hwnd)) 
                             if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) else None, None)
    except: pass
    return list(set(windows))

def launch_amcap():
    if not os.path.exists(AMCAP_EXE): return False
    
    # FIX: Explicitly set working directory so AMCap can find its icon/resources
    amcap_dir = os.path.dirname(os.path.abspath(AMCAP_EXE))
    subprocess.Popen([AMCAP_EXE], cwd=amcap_dir)
    
    for _ in range(20):
        time.sleep(0.5)
        if any('amcap' in w.lower() for w in get_all_windows()):
            time.sleep(1.0)
            return True
    return True

def get_selections():
    old_port, old_window = load_config()
    selected_port, selected_window = None, None

    while True:
        ports = list(serial.tools.list_ports.comports())
        print("\n" + "="*45 + "\n STEP 1: SELECT COM PORT\n" + "="*45)
        for i, p in enumerate(ports):
            tag = " <- last used" if p.device == old_port else ""
            print(f"  [{i}] {p.device} - {p.description}{tag}")
        p_exit = len(ports)
        print(f"  [{p_exit}] EXIT")
        choice = input(f"\nSelect [Default: {old_port}]: ").strip()
        if not choice and old_port: selected_port = old_port; break
        try:
            idx = int(choice)
            if idx == p_exit: os._exit(0)
            if 0 <= idx < len(ports): selected_port = ports[idx].device; break
        except: print(">> Invalid.")

    while True:
        options = []
        print("\n" + "="*45 + "\n STEP 2: SELECT LIGHTWEIGHT VIDEO DISPLAY\n" + "="*45)
        amcap_running = any('amcap' in w.lower() for w in get_all_windows())
        print(f"  [0] AMCap {'[running]' if amcap_running else '[launch]'}")
        options.append(("AMCap", "amcap"))
        
        video_keywords = ['vlc', 'obs', 'camera', 'potplayer', 'mpc-hc', 'mpc-be', 'classic', 'hdmi', 'usb video']
        detected = [w for w in get_all_windows() if any(k in w.lower() for k in video_keywords) and 'amcap' not in w.lower()]
        for i, w in enumerate(detected):
            print(f"  [{i+1}] {w}")
            options.append((w, w))
        
        idx = len(options)
        print(f"  [{idx}] REFRESH")
        print(f"  [{idx+1}] EXIT")
        
        choice = input(f"\nSelect [Default: {old_window}]: ").strip()
        if not choice and old_window:
            selected_window = old_window
            if 'amcap' in old_window.lower() and not amcap_running: launch_amcap()
            break
        try:
            n = int(choice)
            if n == idx + 1: os._exit(0)
            if n == idx: continue
            if 0 <= n < len(options):
                label, match = options[n]
                if match == "amcap":
                    if not amcap_running: launch_amcap()
                    wins = [w for w in get_all_windows() if 'amcap' in w.lower()]
                    selected_window = wins[0] if wins else "AMCap"
                else: selected_window = match
                break
        except: print(">> Invalid.")

    save_config(selected_port, selected_window)
    return selected_port, selected_window

# ================================================================
#  CORE MATRIX DICTIONARIES
# ================================================================
HID_MAP = {
    0x41:0x04, 0x42:0x05, 0x43:0x06, 0x44:0x07, 0x45:0x08, 0x46:0x09, 0x47:0x0A, 0x48:0x0B,
    0x49:0x0C, 0x4A:0x0D, 0x4B:0x0E, 0x4C:0x0F, 0x4D:0x10, 0x4E:0x11, 0x4F:0x12, 0x50:0x13,
    0x51:0x14, 0x52:0x15, 0x53:0x16, 0x54:0x17, 0x55:0x18, 0x56:0x19, 0x57:0x1A, 0x58:0x1B,
    0x59:0x1C, 0x5A:0x1D, 0x30:0x27, 0x31:0x1E, 0x32:0x1F, 0x33:0x20, 0x34:0x21, 0x35:0x22,
    0x36:0x23, 0x37:0x24, 0x38:0x25, 0x39:0x26, 0x70:0x3A, 0x71:0x3B, 0x72:0x3C, 0x73:0x3D,
    0x74:0x3E, 0x75:0x3F, 0x76:0x40, 0x77:0x41, 0x78:0x42, 0x79:0x43, 0x7A:0x44, 0x7B:0x45,
    0x25:0x50, 0x26:0x52, 0x27:0x4F, 0x28:0x51, 0x1B:0x29, 0x0D:0x28, 0x08:0x2A, 0x09:0x2B,
    0x20:0x2C, 0x2E:0x4C, 0x2D:0x49, 0x14:0x39, 0x2C:0x46, 0x91:0x47, 0x13:0x48, 0x24:0x4A,
    0x23:0x4D, 0x21:0x4B, 0x22:0x4E, 0x10:0xE1, 0xA0:0xE1, 0xA1:0xE5, 0x11:0xE0, 0xA2:0xE0,
    0xA3:0xE4, 0x12:0xE2, 0xA4:0xE2, 0xA5:0xE6, 0x5B:0xE3, 0x5C:0xE7, 0x60:0x62, 0x61:0x59,
    0x62:0x5A, 0x63:0x5B, 0x64:0x5C, 0x65:0x5D, 0x66:0x5E, 0x67:0x5F, 0x68:0x60, 0x69:0x61,
    0x6A:0x55, 0x6B:0x57, 0x6D:0x56, 0x6E:0x63, 0x6F:0x54, 0xBA:0x33, 0xBB:0x2E, 0xBC:0x36,
    0xBD:0x2D, 0xBE:0x37, 0xBF:0x38, 0xC0:0x35, 0xDB:0x2F, 0xDC:0x31, 0xDD:0x30, 0xDE:0x34,
}

CONSUMER_MAP = {
    0xAD: 0x00E2, 0xAE: 0x00EA, 0xAF: 0x00E9, 0xB0: 0x00B5, 
    0xB1: 0x00B6, 0xB2: 0x00B7, 0xB3: 0x00CD,
}

# ================================================================
#  GLOBAL PROGRAM VARIABLES
# ================================================================
ser = None
k_list = None
m_list = None
fn_active = False
ctrl_held = False
alt_held = False
gui_held = False
last_pos = None
T_WIN = ""
ABS_MOUSE = True
_was_focused = False
last_mouse_time = 0  # FIX: Mouse transmission limiter throttler

# ================================================================
#  SIGNAL EMISSION CONTROL
# ================================================================
def is_focused():
    try:
        cur = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lower()
        return T_WIN.lower() in cur
    except: return False

def send_pkt(t, b1, b2, b3=0):
    global ser
    if ser and ser.is_open:
        try: ser.write(bytes([t, b1&0xFF, b2&0xFF, b3&0xFF]))
        except: pass

def reset_hid():
    if not ser or not ser.is_open: return
    for mod in [0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7]:
        send_pkt(1, 0, mod)
    send_pkt(1, 0, 0)
    send_pkt(6, 0x00, 0)

def sync_mouse():
    global ABS_MOUSE, last_pos
    ABS_MOUSE = not ABS_MOUSE
    last_pos = None
    print(f"[KVM] Engine Mode: {'ABSOLUTE' if ABS_MOUSE else 'RELATIVE'}")

def check_focus_change():
    global _was_focused
    curr = is_focused()
    if curr and not _was_focused:
        reset_hid()
    _was_focused = curr
    return curr

# ================================================================
#  EVENT SUBSYSTEM LISTENERS
# ================================================================
def on_press(key):
    global fn_active, ctrl_held, alt_held, gui_held
    if not check_focus_change(): return

    vk = getattr(key, 'vk', None) or (hasattr(key, 'value') and key.value.vk)
    if not vk: return

    if vk in (0x11, 0xA2, 0xA3): ctrl_held = True
    if vk in (0x12, 0xA4, 0xA5): alt_held = True
    if vk in (0x5B, 0x5C): gui_held = True

    if vk == 0x2D: # INSERT
        fn_active = True
        return

    if fn_active:
        fn_map = {
            0x70: 0x00E2, 0x71: 0x00EA, 0x72: 0x00E9, 
            0x76: 0x0070, 0x77: 0x00B5, 0x78: 0x006F, 
        }
        if vk in fn_map:
            code = fn_map[vk]
            send_pkt(5, (code >> 8) & 0xFF, code & 0xFF)
            return

    # --- BIOS COMPATIBLE INTERCEPT (FIXED FOR LEGACY HARDWARE) ---
    if ctrl_held and alt_held and vk == 0x08: # Backspace
        print("[NCS] Forwarding Ctrl + Alt + Delete...")
        
        # 1. Send the key presses safely
        send_pkt(1, 1, 0xE0); time.sleep(0.002) # Ctrl Down
        send_pkt(1, 1, 0xE2); time.sleep(0.002) # Alt Down
        send_pkt(1, 1, 0x4C); time.sleep(0.010) # Delete/Backspace Down
        
        # 2. CRITICAL FIX: Force immediate release commands before power cuts
        send_pkt(1, 0, 0x4C); time.sleep(0.002) # Delete/Backspace Up
        send_pkt(1, 0, 0xE2); time.sleep(0.002) # Alt Up
        send_pkt(1, 0, 0xE0); time.sleep(0.002) # Ctrl Up
        
        # 3. EXTRA SAFEGUARD: Send a type-6 panic clear packet to the Pico firmware
        # This completely resets the kbd_keys and kbd_modifiers arrays inside the Pico.
        send_pkt(6, 0x00, 0) 
        return
    
    
    # if ctrl_held and alt_held and vk == 0x08: # Backspace -> Sends Ctrl+Alt+Del array safely
        # print("[KVM] Forwarding Secure Boot CAD Array...")
        # send_pkt(1, 0, 0); time.sleep(0.002)
        # send_pkt(1, 1, 0xE0); time.sleep(0.002)
        # send_pkt(1, 1, 0xE2); time.sleep(0.002)
        # send_pkt(1, 1, 0x4C); time.sleep(0.005)
        # send_pkt(1, 0, 0x4C); time.sleep(0.002)
        # send_pkt(1, 0, 0xE2); time.sleep(0.002)
        # send_pkt(1, 0, 0xE0)
        # return

    if ctrl_held and alt_held and vk == 0x43: # C
        reset_hid(); return

    if ctrl_held and alt_held and vk == 0x52: # R
        sync_mouse(); return

    if vk in CONSUMER_MAP:
        code = CONSUMER_MAP[vk]
        send_pkt(5, (code >> 8) & 0xFF, code & 0xFF)
        return

    if vk in HID_MAP:
        send_pkt(1, 1, HID_MAP[vk])

def on_release(key):
    global fn_active, ctrl_held, alt_held, gui_held
    vk = getattr(key, 'vk', None) or (hasattr(key, 'value') and key.value.vk)
    if not vk: return

    if vk in (0x11, 0xA2, 0xA3): ctrl_held = False
    if vk in (0x12, 0xA4, 0xA5): alt_held = False
    if vk in (0x5B, 0x5C): gui_held = False

    if vk == 0x2D:
        fn_active = False; return

    if not is_focused(): return

    if fn_active and 0x70 <= vk <= 0x7B:
        send_pkt(5, 0, 0); return
    if vk in CONSUMER_MAP:
        send_pkt(5, 0, 0); return

    if vk in HID_MAP:
        send_pkt(1, 0, HID_MAP[vk])

def on_move(x, y):
    global last_pos, ABS_MOUSE, last_mouse_time
    if not check_focus_change(): 
        last_pos = None; return
    
    # FIX: Limit mouse event transmissions to ~60Hz (every 16ms)
    # This completely stops buffer choking and bus overflows on legacy laptops
    now = time.time()
    if (now - last_mouse_time) < 0.016: 
        return
    last_mouse_time = now
    
    if ABS_MOUSE:
        try:
            hwnd = win32gui.GetForegroundWindow()
            x_left, y_top, x_right, y_bottom = win32gui.GetWindowRect(hwnd)
            _, _, client_w, client_h = win32gui.GetClientRect(hwnd)
            
            border_x = ((x_right - x_left) - client_w) // 2
            title_y = (y_bottom - y_top) - client_h - border_x
            
            canvas_x = x - (x_left + border_x)
            canvas_y = y - (y_top + title_y)
            
            if 0 <= canvas_x <= client_w and 0 <= canvas_y <= client_h:
                sx = int((canvas_x / client_w) * 255)
                sy = int((canvas_y / client_h) * 255)
                send_pkt(4, sx, sy)
        except:
            sw = win32api.GetSystemMetrics(0)
            sh = win32api.GetSystemMetrics(1)
            sx = int((x / sw) * 255)
            sy = int((y / sh) * 255)
            send_pkt(4, sx, sy)
    else:
        if last_pos:
            dx = max(-127, min(127, int(x - last_pos[0])))
            dy = max(-127, min(127, int(y - last_pos[1])))
            if dx != 0 or dy != 0: send_pkt(2, dx, dy)
        last_pos = (x, y)

def on_click(x, y, button, pressed):
    if check_focus_change():
        bid = (1 if "left" in str(button) else 2 if "right" in str(button) else 3)
        send_pkt(3, bid, 1 if pressed else 0)

# ================================================================
#  SYSTEM INIT ENTRYPOINT
# ================================================================
if __name__ == "__main__":
    try:
        S_PORT, T_WIN = get_selections()
        
        # FIX: Open serial instance strictly WITHOUT triggering DTR/RTS auto-reset signals.
        # This keeps the Pico running consistently even when opening/closing the terminal app.
        ser = serial.Serial()
        ser.port = S_PORT
        ser.baudrate = BAUD_RATE
        ser.timeout = 0.01
        ser.dtr = False
        ser.rts = False
        ser.open()
        
        # Flush electrical echo artifacts cleanly
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        print(f"\n{'='*45}\n  PRODUCTION KVM RUNNING\n  Interface: {S_PORT}\n  Target Canvas: '{T_WIN}'\n{'='*45}\n")
        k_list = keyboard.Listener(on_press=on_press, on_release=on_release)
        m_list = mouse.Listener(on_move=on_move, on_click=on_click)
        k_list.start(); m_list.start()
        while k_list.running and m_list.running: k_list.join(0.1); m_list.join(0.1)
    except KeyboardInterrupt: print("\n[!] Gracefully exiting system.")
    except Exception: traceback.print_exc()
    finally:
        if 'k_list' in locals() and k_list: k_list.stop()
        if 'm_list' in locals() and m_list: m_list.stop()
        if 'ser' in locals() and ser and ser.is_open: ser.close()
        os._exit(0)