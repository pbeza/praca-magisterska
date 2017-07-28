#!/usr/bin/env python3
# `apt-file search` vs `dpkg -S` speed comparison (dpkg wins).
import os
import subprocess
import time

from numpy import random

dir_path = "/var"


def test_fun(cmd, paths):
    i = 1

    for p in paths:
        path = os.path.join(dir_path, p)
        proc = None

        print("{} | {}\n".format(i, path))

        try:
            proc = subprocess.run(cmd + [path], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print("  Fail! Details: {}".format(e))
        else:
            print("  " + proc.stdout.decode("utf-8").strip())

        i += 1

        print()


paths = random.choice(os.listdir(dir_path), 100)

cmds = [
    ["dpkg", "-S"],
    ["apt-file", "search"]
]

for i in range(len(cmds)):
    cmd = cmds[i]
    start = time.time()
    test_fun(cmd, paths)
    end = time.time()
    print(end - start)
    print("__________________________________")
