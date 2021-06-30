#! /usr/bin/python3
""" mysql自动备份工具

@author: kiven lee
@since: 2021-07-01

自动备份设置: crontab -e
增加: 50 2 * * * /usr/local/bin/mysql-backup.py
"""

import os, subprocess, re, time

# 保留最近备份的数量
max_bak_count = 30
# 备份路径
bak_path = "/home/mysqlbak"
# mysql用户
dbuser = "root"
# mysql密码
dbpass = "Zh&lgwt5ewot"

mysqldump = "/usr/bin/mysqldump"
bak_prefix = "mysql-"
bak_suffix = ".sql.xz"

dynname = time.strftime("%Y-%m-%d", time.localtime())
bkrun = f"{mysqldump} -u{dbuser} -p\"{dbpass}\" --default-character-set=utf8 --all-databases | /usr/bin/xz - > {bak_path}/{bak_prefix}{dynname}{bak_suffix}"
subprocess.run(bkrun, shell=True)

fre = re.compile(bak_prefix + "\d{4}-\d{2}-\d{2}" + bak_suffix)
files = []
for f in os.listdir(bak_path):
   if fre.match(f):
       files.append(f)

if len(files) > max_bak_count:
    files = sorted(files, reverse=True)
    for f in files[max_bak_count:]:
        print(f"remove older file: {f}")
        os.remove(f"{bak_path}/{f}")