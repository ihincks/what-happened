import subprocess
import re
import datetime
from collections import defaultdict
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
    default=DEFAULT_CONFIG,
    help="YAML file with configuration settings.",
)
parser.add_argument(
    "-u", "--user", dest="user", action="store", help="User to search.", default=None
)
parser.add_argument(
    "-w",
    "--width",
    dest="width",
    action="store",
    help="Line wrap width of the subject and body of the logs.",
    default=60,
)

# ======================================================================================
# FUNCTIONS
# ======================================================================================


def in_folder(fn):
    """
    Decorates function so that it runs in the working directory specified by the
    first argument passed to the function.

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

    pretty_keys = ["date", "user", "desc", "subject", "body"]
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


def get_arg(name, args, config):
    return (
        config[name]
        if name in config and getattr(args, name) == parser.get_default(name)
        else getattr(args, name)
    )


# ======================================================================================
# MAIN
# ======================================================================================


if __name__ == "__main__":

    args = parser.parse_args()

    # use the config file to get the list of repos
    config_file = args.config
    with open(config_file, "r") as f:
        config = yaml.load(f)
    try:
        repo_list = config["repos"]
    except KeyError:
        raise ValueError("Configuration requires an entry for 'repos'.")

    # command line overrides whatever's in config.yaml, though argparser stores defaults
    user = get_arg("user", args, config)
    width = int(get_arg("width", args, config))

    subject_wrapper = textwrap.TextWrapper(width=width, fix_sentence_endings=True)
    body_wrapper = textwrap.TextWrapper(width=width - 3, fix_sentence_endings=True)

    logs = []
    max_lengths = defaultdict(int)
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
            for key, val in log.items():
                max_lengths[key] = max(max_lengths[key], len(val))
            log["body"] = log["body"]
        logs += new_logs

    logs.sort(
        key=lambda x: datetime.datetime.strptime(x["date"], r"%Y-%m-%d"), reverse=False
    )

    if len(logs) > 0:
        meta_template = [
            "{{date:<{date}}}",
            "{{user:<{user}}}",
            "{{name:<{name}}}",
            "{{subject}}",
        ]
        if user:
            # only print user if user is not specified
            del meta_template[1]
        template = "  ".join(meta_template).format(**max_lengths)
        fake_log = logs[0].copy()
        fake_log["subject"] = ""
        body_template = " " * len(template.format(**fake_log)) + " {} {}"

        for log in logs:
            print(template.format(**log))
            if len(log["body"]) > 2:
                for section in log["body"].split("* "):
                    for idx, line in enumerate(body_wrapper.wrap(section)):
                        s = "*" if idx == 0 else " "
                        print(body_template.format(s, line.replace("  ", " ", 500)))
