import subprocess
import re
import datetime
from collections import OrderedDict
import os
import textwrap

DIRS = ["path/to/first/repo", "path/to/second/repo"]
STRIP_CHARS = [" ", "\t", '"']
REGX = re.compile(r"([\d]+-[\d]+-[\d]+):([^:]*):(.*)")


def getlogs(repo_path, user="Ian", n_months=3):
    current_path = os.getcwd()
    os.chdir(repo_path)
    out = (
        subprocess.check_output(
            [
                "git",
                "log",
                r'--pretty=format:"%ad:%D:%B"',
                "--date=short",
                "--reverse",
                "--all",
                "--since={}.months.ago".format(n_months),
                "--author={}".format(user),
            ]
        )
        .decode("utf-8")
        .split("\n")
    )
    os.chdir(current_path)
    return out


def reponame(repo_path):
    current_path = os.getcwd()
    os.chdir(repo_path)
    out = subprocess.check_output(
        ["git", "config", "--get", "remote.origin.url"],
        shell=False,
        stderr=subprocess.STDOUT,
    )
    out = os.path.basename(out.decode("utf-8"))
    os.chdir(current_path)
    return out.replace(".git", "").strip()


def process_line(line):
    for char in STRIP_CHARS:
        line = line.strip(char)
    m = REGX.match(line)
    try:
        return [m.group(1), m.group(2), m.group(3)]
    except:
        return line


logs = []
for git_dir in DIRS:
    name = reponame(git_dir)
    for line in map(process_line, getlogs(git_dir)):
        if isinstance(line, list):
            date, dec, msg = line
            logs.append([date, name, msg, ""])
        else:
            if len(line) >= 2:
                logs[-1][-1] = (logs[-1][-1] + " " + line).strip()

logs.sort(key=lambda x: datetime.datetime.strptime(x[0], r"%Y-%m-%d"), reverse=False)


for line in logs:
    print("{:<12} {:<16} {}".format(*line[:3]))
    if len(line[3]) > 2:
        for subline in textwrap.wrap(line[3], 80):
            print("{:<30} > {}".format("", subline))

