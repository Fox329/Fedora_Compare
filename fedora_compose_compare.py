#!/usr/bin/env python

from flask import Flask, jsonify

import requests
import json
import os
import re
import argparse

URL = "https://kojipkgs.fedoraproject.org/compose/branched/"
OLD = "Fedora-41-20241023.n.0"
NEW = "Fedora-41-20241024.n.0"

parser = argparse.ArgumentParser()
parser.add_argument("mode", nargs="?", choices=["sync", "daemon", "compare"])
parser.add_argument("comp", nargs="?")

args = parser.parse_args()
app = Flask(__name__)

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
        
@app.route('/<oldc>:<newc>')
def compare_endpoint(oldc:str, newc:str):
    return jsonify(compare(oldc, newc))

def compare(oldc:str, newc:str) -> dict[str:list[str, str]]:
    """
    Compares the specified composes
    """
    old = json.loads(open(f"data/{oldc}", "r").read())
    new = json.loads(open(f"data/{newc}", "r").read())

    results = {}
    out = {}

    for package in old:
        # package.rsplit returns package name
        results[package.rsplit('-',2)[0]] = [package, None]

    for package in new:
        results[package.rsplit('-',2)[0]][1] = package
    
    for package in results:
        if results[package][0] != results[package][1]:
            print(f"{results[package][0]} changed to {results[package][1]}")
            out[package] = results[package]
    
    return out

if __name__ == "__main__":
    #import pdb; pdb.set_trace()
    if args.mode == "sync":
        # Ensure the 'data' directory exists
        if not os.path.exists('data'):
            os.makedirs('data')

        # Downloads composes for comparison
        for compose in figure_composes():
            download_compose(compose)
    
    if args.mode == "daemon":
        app.run()

    if args.mode == "compare":
        comparison = args.comp.split(":")
        compare(comparison[0], comparison[1])


