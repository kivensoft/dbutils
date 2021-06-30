#! /usr/bin/python3
""" gitea自动备份工具

@author: kiven lee
@since: 2021-07-01

自动备份设置: crontab -e
增加: 50 2 * * * /usr/local/bin/gitea-backup.py
"""

import os, subprocess, re

# 保留最近备份的数量
max_bak_count = 30
# 运行备份程序的用户
user = "git"

sudo = "/usr/bin/sudo"
gitea = "/usr/local/bin/gitea"
bak_re = re.compile("gitea-dump-\d+\.zip")

work_path = f"/home/{user}/gitea"
custom_path = F"{work_path}/custom"
config_path = f"{custom_path}/app.ini"
backup_path = f"/home/{user}/backup"

runas = [sudo, "-u", user]
gitea_bak = [gitea, "--work-path", work_path, "--custom-path", custom_path, "--config", config_path, "dump"]

print("run gitea dump ......")
print("=" * 40)
subprocess.call(runas + gitea_bak, cwd=backup_path)
print("=" * 40)

files = []
for f in os.listdir(backup_path):
    if bak_re.match(f): files.append(f)

if len(files) > max_bak_count:
    files = sorted(files, reverse=True)
    for f in files[max_bak_count:]:
        print(f"remove older file: {f}")
        os.remove(f"{backup_path}/{f}")