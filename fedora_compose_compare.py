#!/usr/bin/env python

import requests
import json
import os
import re
import argparse

URL = "https://kojipkgs.fedoraproject.org/compose/branched/"
OLD = "Fedora-41-20241023.n.0"
NEW = "Fedora-41-20241024.n.0"

parser = argparse.ArgumentParser()
parser.add_argument("sync", nargs="?")
args = parser.parse_args()

def figure_composes(days:int=3) -> list[str]:
    """
    We grab the last N composes's jsons to compare
    """

    rule = r"Fedora-[0-9]{2}-[0-9]{8}.n.[0-9]"
    resp = requests.get(URL)
    
    composes_match = re.findall(rule, resp.text)
    composes = sorted(set(composes_match))
    return composes[-days:] # Returns the last N composes

def download_compose(compose:str) -> None:
    """
    Downloads the rpms.json for the specified compose
    """
    url = f"{URL}{compose}/compose/metadata/rpms.json"
    file_name = f"data/{compose}"

    # Check if files exist, if not, download them
    if os.path.exists(file_name):
        print(f"{file_name} found, skipping download")
    
        return
    
    raw = requests.get(url)

    if raw.status_code == 200:        
        # Save the downloaded JSON file into the 'data' directory with the compose name
        data = json.loads(raw.text)
        data_keys = data['payload']['rpms']['Everything']['x86_64'].keys()

        with open(f"data/{compose}", "w") as f:
            f.write(json.dumps(list(data_keys)))
        print(f"Downloaded rpms.json for {compose}")
    else:
        print(f"Failed to download rpms.json for {compose}. HTTP status code: {raw.status_code}")
        
def compare(oldc:str, newc:str) -> None:
    """
    Compares the specified composes
    """
    old = json.loads(open(f"data/{oldc}", "r").read())
    new = json.loads(open(f"data/{newc}", "r").read())

    results = {}

    for package in old:
        # package.rsplit returns package name
        results[package.rsplit('-',2)[0]] = [package, None]

    for package in new:
        results[package.rsplit('-',2)[0]][1] = package
    
    for package in results:
        if results[package][0] != results[package][1]:
            print(f"{results[package][0]} changed to {results[package][1]}")

if __name__ == "__main__":
    if args.sync:
        # Ensure the 'data' directory exists
        if not os.path.exists('data'):
            os.makedirs('data')

        # Downloads composes for comparison
        for compose in figure_composes():
            download_compose(compose)

    # Compare the two composes
    compare(OLD, NEW)

