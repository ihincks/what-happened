import subprocess
import re
import datetime
from collections import OrderedDict
import os
import textwrap
import yaml
import argparse
import functools

# ======================================================================================
# CONSTANTS
# ======================================================================================

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(THIS_FOLDER, "config.yaml")
SEP1 = ":AUXOouLEU9e387:"
SEP2 = ":XDoHXS3OETHHU:"

# ======================================================================================
# ARGUMENTS
# ======================================================================================

parser = argparse.ArgumentParser(
    description=(
        "Merges logs of multiple git repositories and sorts "
        "by date to figure out what you did in the past while."
    )
)
parser.add_argument(
    "config",
    nargs="?",
    action="store",
    default=None,
    help="YAML file with configuration settings.",
)
parser.add_argument("-u", "--user", dest="user", action="store", help="User to search.")

# ======================================================================================
# FUNCTIONS
# ======================================================================================


def in_folder(fn):
    """
    Decorates function so that it operates with the working directory set as the first
    argument to the function.

    :param fn: The function to wrap.
    :returns: The wrapped function.
    """

    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        current_path = os.getcwd()
        os.chdir(args[0])
        out = fn(*args, **kwargs)
        os.chdir(current_path)
        return out

    return wrapped


@in_folder
def get_repo_logs(repo_path, user=None, n_months=3, name=""):

    pretty_keys = ["date", "author", "desc", "subject", "body"]
    pretty_format = SEP2.join(["%ad", "%an", "%D", "%s", "%b"]) + SEP1

    args = [
        "git",
        "log",
        "--pretty=format:{}".format(pretty_format),
        "--date=short",
        "--reverse",
        "--all",
        "--since={}.months.ago".format(n_months),
    ]
    if user:
        args.append("--author={}".format(user))
    out = subprocess.check_output(args).decode("utf-8")
    return [
        {key: part.strip() for key, part in zip(pretty_keys, line.split(SEP2))}
        for line in out.split(SEP1)
    ]


@in_folder
def get_repo_name(repo_path):
    """
    Gets the repo name of the given path. First looks at the remote origin git name,
    and if this fails, just takes the folder name.

    :param str repo_path: Path to the repo.
    :returns: Name for this git repo.
    :rtype: ``str``
    """
    current_path = os.getcwd()
    os.chdir(repo_path)
    try:
        out = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            shell=False,
            stderr=subprocess.STDOUT,
        )
        out = os.path.basename(out.decode("utf-8"))
    except:
        out = os.path.basename(repo_path)
    os.chdir(current_path)
    return out.replace(".git", "").strip()


# ======================================================================================
# MAIN
# ======================================================================================


if __name__ == "__main__":

    args = parser.parse_args()

    # use the config file to get the list of repos
    config_file = args.config if args.config else DEFAULT_CONFIG
    with open(config_file, "r") as f:
        config = yaml.load(f)
    try:
        repo_list = config["repos"]
    except KeyError:
        raise ValueError("Configuration requires an entry for 'repos'.")

    # command line user overrides what is set
    user = args.user if args.user else config["user"]

    subject_wrapper = textwrap.TextWrapper(width=60, fix_sentence_endings=True)
    body_wrapper = textwrap.TextWrapper(
        width=subject_wrapper.width - 3, fix_sentence_endings=True
    )

    logs = []
    for repo in repo_list:
        repo_dir = os.path.expanduser(repo)
        name = get_repo_name(repo_dir)
        new_logs = [
            log
            for log in get_repo_logs(repo_dir, user=user)
            if "date" in log and len(log["date"]) > 0
        ]
        for log in new_logs:
            log["name"] = name
            log["body"] = (
                log["body"]
                .replace(".\r\n\r\n", ".", 500)
                .replace("\r\n\r\n", ".", 500)
                .replace("\t", "", 500)
                .replace("\n", "", 500)
                .replace("\r", "", 500)
                .replace("    ", " ", 500)
                .replace("   ", " ", 500)
                .replace("  ", " ", 500)
                .replace("* ", "")
            )
        logs += new_logs

    logs.sort(
        key=lambda x: datetime.datetime.strptime(x["date"], r"%Y-%m-%d"), reverse=False
    )

    for log in logs:
        print("{date:<12} {name:<16} {subject}".format(**log))
        if len(log["body"]) > 2:
            for line in body_wrapper.wrap(log["body"]):
                print("{:<32}> {}".format("", line.replace("  ", " ")))
