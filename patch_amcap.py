import os

# FIXED PATHS: Added the repository folder prefix explicitly
cpp_path = r"Windows-classic-samples/Samples/Win7Samples/multimedia/directshow/capture/amcap/amcap.cpp"
rc_path = r"Windows-classic-samples/Samples/Win7Samples/multimedia/directshow/capture/amcap/amcap.rc"
h_path = r"Windows-classic-samples/Samples/Win7Samples/multimedia/directshow/capture/amcap/resource.h"

print("Starting verification and patching process...")

# 1. Update resource.h using a dynamic line parser to bypass whitespace layout bugs
if os.path.exists(h_path):
    with open(h_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    has_fullscreen = any("ID_VIEW_FULLSCREEN" in line for line in lines)
    
    if not has_fullscreen:
        updated_lines = []
        patched = False
        for line in lines:
            if "IDM_ABOUT" in line and not patched:
                updated_lines.append("#define ID_VIEW_FULLSCREEN             40009\n")
                patched = True
            updated_lines.append(line)
            
        with open(h_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print("[SUCCESS] resource.h dynamically patched with ID_VIEW_FULLSCREEN.")
else:
    print(f"[ERROR] resource.h could not be found at path: {h_path}")

# 2. Patch amcap.rc to add the Full Screen option to the menu and accelerators
if os.path.exists(rc_path):
    with open(rc_path, "r", encoding="utf-8", errors="ignore") as f:
        rc_content = f.read()
    
    if "ID_VIEW_FULLSCREEN" not in rc_content:
        menu_search = 'POPUP "&Help"'
        menu_inject = """POPUP "&View"
    BEGIN
        MENUITEM "&Full Screen\\tEnter",         ID_VIEW_FULLSCREEN
    END
    """
        rc_content = rc_content.replace(menu_search, menu_inject + menu_search)
        
        accel_search = 'VK_F5,          IDM_START_CAPTURE,  VIRTKEY'
        accel_inject = '\n    VK_RETURN,      ID_VIEW_FULLSCREEN, VIRTKEY'
        rc_content = rc_content.replace(accel_search, accel_search + accel_inject)
        
        with open(rc_path, "w", encoding="utf-8") as f:
            f.write(rc_content)
        print("[SUCCESS] amcap.rc menu structure and accelerators patched successfully.")
else:
    print(f"[ERROR] amcap.rc could not be found at path: {rc_path}")

# 3. Patch amcap.cpp to include runtime fullscreen mechanics and event loops
if os.path.exists(cpp_path):
    with open(cpp_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    if "ToggleFullScreen" not in code:
        globals_code = """
// --- Custom KVM Borderless Fullscreen Engine Implementation ---
bool            g_bFullScreen = false;
WINDOWPLACEMENT g_wpPrev = { sizeof(WINDOWPLACEMENT) };
HMENU           g_hMainMenu = NULL;

void ToggleFullScreen(HWND hwnd)
{
    DWORD dwStyle = GetWindowLong(hwnd, GWL_STYLE);
    if (!g_bFullScreen) {
        GetWindowPlacement(hwnd, &g_wpPrev);
        HMONITOR hMonitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
        MONITORINFO mi = { sizeof(MONITORINFO) };
        GetMonitorInfo(hMonitor, &mi);
        g_hMainMenu = GetMenu(hwnd);
        SetMenu(hwnd, NULL);
        SetWindowLong(hwnd, GWL_STYLE, dwStyle & ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX));
        SetWindowPos(hwnd, HWND_TOP, mi.rcMonitor.left, mi.rcMonitor.top,
                     mi.rcMonitor.right - mi.rcMonitor.left, mi.rcMonitor.bottom - mi.rcMonitor.top,
                     SWP_NOOWNERZORDER | SWP_FRAMECHANGED);
        g_bFullScreen = true;
    } else {
        SetWindowLong(hwnd, GWL_STYLE, dwStyle | (WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX));
        if (g_hMainMenu) SetMenu(hwnd, g_hMainMenu);
        SetWindowPlacement(hwnd, &g_wpPrev);
        SetWindowPos(hwnd, NULL, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_FRAMECHANGED);
        g_bFullScreen = false;
    }
    extern IVideoWindow *g_pVW;
    if (g_pVW) {
        RECT rc; GetClientRect(hwnd, &rc);
        g_pVW->SetWindowPosition(0, 0, rc.right, rc.bottom);
    }
}
"""
        code = code.replace("#include <streams.h>", "#include <streams.h>\n" + globals_code)

        input_hooks = """    switch (message)
    {
        case WM_LBUTTONDBLCLK:
            ToggleFullScreen(hwnd);
            return 0;
        case WM_KEYDOWN:
            if (wParam == VK_ESCAPE && g_bFullScreen) {
                ToggleFullScreen(hwnd);
                return 0;
            }
            break;"""
        code = code.replace("    switch (message)\n    {", input_hooks)

        command_hook = """case ID_VIEW_FULLSCREEN:
            ToggleFullScreen(hwnd);
            break;"""
        code = code.replace("switch (g_bvbiPreview)", command_hook + "\n        switch (g_bvbiPreview)")

        code = code.replace("wc.style = 0;", "wc.style = CS_DBLCLKS;")

        with open(cpp_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[SUCCESS] amcap.cpp engine logic updated.")
else:
    print(f"[ERROR] amcap.cpp could not be found at path: {cpp_path}")
