import os
import shutil
import subprocess

target_exe = r"C:\Users\khy1s\Documents\antigravity\dazzling-euclid\dist\turkce-otoduzeltici.exe"
v2_exe = r"C:\Users\khy1s\Documents\antigravity\dazzling-euclid\dist\turkce-otoduzeltici-v2.exe"
icon_path = r"C:\Users\khy1s\Documents\antigravity\dazzling-euclid\src\icon.ico"
work_dir = r"C:\Users\khy1s\Documents\antigravity\dazzling-euclid"

shutil.copyfile(target_exe, v2_exe)
print("[+] v2 ikili dosyası güncellendi.")

# Desktop shortcut update
desktop_lnk = r"C:\Users\khy1s\OneDrive\Desktop\turkce-otoduzeltici.exe.lnk"
script = f"""
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('{desktop_lnk}')
$sc.TargetPath = '{target_exe}'
$sc.WorkingDirectory = '{work_dir}'
$sc.IconLocation = '{icon_path}'
$sc.Save()
Write-Output "Masaüstü kısayolu başarıyla güncellendi!"
"""

ps_file = os.path.join(work_dir, "_update_shortcut.ps1")
with open(ps_file, "w", encoding="utf-8") as f:
    f.write(script)

res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file], capture_output=True, text=True)
print(res.stdout)
if os.path.exists(ps_file):
    os.remove(ps_file)
