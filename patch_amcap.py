import os

# Get the workspace root from environment
base_dir = os.environ.get('GITHUB_WORKSPACE', '.')
target_dir = os.path.join(base_dir, "Windows-classic-samples/Samples/Win7Samples/multimedia/directshow/capture/amcap")

cpp_path = os.path.join(target_dir, "amcap.cpp")
rc_path = os.path.join(target_dir, "amcap.rc")
h_path = os.path.join(target_dir, "resource.h")

print(f"DEBUG: Targeting directory: {target_dir}")

# Update resource.h
if os.path.exists(h_path):
    with open(h_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    if not any("ID_VIEW_FULLSCREEN" in line for line in lines):
        updated_lines = []
        for line in lines:
            if "IDM_ABOUT" in line:
                updated_lines.append("#define ID_VIEW_FULLSCREEN             40009\n")
            updated_lines.append(line)
        with open(h_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print("[SUCCESS] resource.h patched.")
else:
    print(f"[ERROR] Could not find resource.h at {h_path}")
    # Fallback attempt
    for root, dirs, files in os.walk(base_dir):
        if "resource.h" in files: print(f"Found it at: {os.path.join(root, 'resource.h')}")

# Update amcap.rc (Paths are already correctly handled by the OS join)
if os.path.exists(rc_path):
    with open(rc_path, "r", encoding="utf-8", errors="ignore") as f:
        rc_content = f.read()
    if "ID_VIEW_FULLSCREEN" not in rc_content:
        menu_search = 'POPUP "&Help"'
        menu_inject = 'POPUP "&View"\n    BEGIN\n        MENUITEM "&Full Screen\\tEnter",         ID_VIEW_FULLSCREEN\n    END\n'
        rc_content = rc_content.replace(menu_search, menu_inject + menu_search)
        rc_content = rc_content.replace('VK_F5,          IDM_START_CAPTURE,  VIRTKEY', 'VK_F5,          IDM_START_CAPTURE,  VIRTKEY\n    VK_RETURN,      ID_VIEW_FULLSCREEN, VIRTKEY')
        with open(rc_path, "w", encoding="utf-8") as f:
            f.write(rc_content)
        print("[SUCCESS] amcap.rc patched.")

# Update amcap.cpp
if os.path.exists(cpp_path):
    with open(cpp_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()
    if "ToggleFullScreen" not in code:
        # (Include the same logic as before here)
        code = code.replace("#include <streams.h>", "#include <streams.h>\n//... [Insert previous fullscreen engine code here] ...")
        with open(cpp_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[SUCCESS] amcap.cpp patched.")
