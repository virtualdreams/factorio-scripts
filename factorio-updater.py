#!/usr/bin/env python3

import sys
import re
import os
import argparse
import requests
import subprocess
import time


def parse_args():
    parser = argparse.ArgumentParser(description="Fetches factorio updates")
    parser.add_argument(
        "-b", "--binary", required=True, dest="binary", help="Factorio binary."
    )
    parser.add_argument("-u", "--user", dest="user", help="Factorio username.")
    parser.add_argument("-t", "--token", dest="token", help="Factorio token.")
    parser.add_argument(
        "-p",
        "--package",
        default="core-linux_headless64",
        dest="package",
        help="Factorio package.",
    )
    parser.add_argument(
        "-o", "--output", default="/tmp/", dest="output", help="Download directory."
    )
    parser.add_argument(
        "-l",
        "--list-packages",
        action="store_true",
        dest="list_packages",
        help="List packages.",
    )
    parser.add_argument(
        "-f",
        "--from-version",
        dest="from_version",
        help="Get updates from specified version.",
    )
    parser.add_argument(
        "-x",
        "--experimental",
        action="store_true",
        dest="experimental",
        help="Get experimental versions.",
    )
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        dest="apply",
        help="Apply update after download.",
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        dest="delete",
        help="Delete update after apply.",
    )

    return parser.parse_args()


class Error(Exception):
    pass


def version_key(v):
    if v is None:
        return []
    return [int(x) for x in v.split(".")]


def dict_version_key(v):
    return [int(x) for x in v[0].split(".")]


def get_available_versions(username, token):
    """Get the list of available versions."""
    payload = {
        "username": username,
        "token": token,
    }

    r = requests.get(
        "https://updater.factorio.com/get-available-versions",
        params=payload,
    )
    if r.status_code != 200:
        raise Error(
            "Failed to download version informations: HTTP {}.".format(r.status_code)
        )

    return r.json()


def get_updates(json, package, vfrom, experimental):
    """Get a list of updates."""
    latest = None
    current = vfrom
    available = {}

    # get latest or stable version
    for row in json[package]:
        if not experimental:
            if "from" not in row:
                latest = row["stable"]
        else:
            if "from" in row:
                latest = max(latest, row["to"], key=version_key)

    while True:
        sublist = []

        # iterate over all version paths
        for row in json[package]:
            if (
                "from" in row
                and current == row["from"]
                and min(row["to"], latest, key=version_key) == row["to"]
            ):
                sublist.append(row["to"])

        # get the highest version
        if len(sublist) > 0:
            m = max(sublist, key=version_key)
            available[current] = m
            current = m
        else:
            break

    return latest, sorted(available.items(), key=dict_version_key)


def get_download_link(username, token, package, vfrom, vto):
    """Get the download link for the update"""
    payload = {
        "username": username,
        "token": token,
        "package": package,
        "from": vfrom,
        "to": vto,
    }

    r = requests.get(
        "https://updater.factorio.com/get-download-link",
        params=payload,
    )
    if r.status_code != 200:
        raise Error("Get download link failed. HTTP {}.".format(r.status_code))

    return r.json()[0]


def fetch_update(url, path, package, vfrom, vto):
    """Fetch the update from server and store it."""
    fpath = os.path.join(path, "{}-{}-{}-update.zip".format(package, vfrom, vto))

    r = requests.get(url, stream=True)
    cl = r.headers.get("content-length")

    start = time.perf_counter()

    with open(fpath, "wb") as fd:
        dl = 0
        tl = int(cl)
        for chunk in r.iter_content(8192):
            dl += len(chunk)

            print(
                "\r  Download: [{:>3}%] {:6.1f} MB/s ({:.2f} MB)".format(
                    int(dl * 100 / tl),
                    (dl // (time.perf_counter() - start)) / 1000 / 1000,
                    int(cl) / 1000 / 1000,
                ),
                end="",
            )

            fd.write(chunk)

    print()
    return fpath


def apply_update(binary, path):
    """Apply update"""
    try:
        subprocess.check_output(
            [binary, "--apply-update", path],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print(e.output)
        sys.exit(1)


def delete_update(path):
    os.remove(path)


def get_version(binary):
    """Get version number from binary"""
    sp_output = subprocess.check_output([binary, "--version"], universal_newlines=True)
    re_output = re.search(r"Version: (\d+\.\d+\.\d+)", sp_output)
    if re_output:
        version = re_output.group(1)
        return version


def main():
    args = parse_args()

    if args.from_version is not None:
        version = args.from_version
        print("Version from command line: {}.".format(version))
    else:
        version = get_version(args.binary)
        print("Version auto-detected: {}.".format(version))

    versions = get_available_versions(args.user, args.token)
    if args.list_packages:
        print("Available packages:")
        for package in versions.keys():
            print("  ", package)
        sys.exit(0)

    if args.package not in versions.keys():
        print("Package {} does not exists.".format(args.package))
        sys.exit(1)

    print("Get updates for package:", args.package)

    latest, updates = get_updates(versions, args.package, version, args.experimental)
    print("Latest version:", latest)

    if len(updates) == 0:
        print("No updates available.")
    else:
        for vfrom, vto in updates:
            print("Update available: {} -> {}.".format(vfrom, vto))

        user_continue = input("Do you want to continue? (y/N): ")
        if user_continue.lower() in ["yes", "y"]:
            for vfrom, vto in updates:
                print("Get update: {} -> {}.".format(vfrom, vto))
                url = get_download_link(args.user, args.token, args.package, vfrom, vto)
                path = fetch_update(url, args.output, args.package, vfrom, vto)
                print("  Stored to", path)
                if args.from_version is None and args.apply:
                    print("  Apply update {} -> {}.".format(vfrom, vto))
                    apply_update(args.binary, path)
                    if args.delete:
                        print("  Delete update {} -> {}.".format(vfrom, vto))
                        delete_update(path)


if __name__ == "__main__":
    sys.exit(main())
