from pathlib import Path

p = Path("sicuan/brain.py")
s = p.read_text()

old = '"action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info",'

new = '"action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info | godmeme_status",'

if old not in s:
    print("ACTION ANCHOR NOT FOUND")
    exit()

s = s.replace(old, new, 1)

p.write_text(s)
print("ACTION STATUS PATCH DONE")
