#!/usr/bin/env python3

import argparse
import json
import os
import subprocess

parser = argparse.ArgumentParser(description="Build and deploy DECAF App")

parser.add_argument(
    "-n",
    "--app-name",
    action="store",
    help="Name of the app to build",
    required=True,
)

parser.add_argument(
    "-s",
    "--segment",
    action="append",
    help="Segment to build\nE.g: production, staging or v0.1.0",
    required=True,
)

parser.add_argument(
    "-H",
    "--deploy-host",
    help="Deploy host",
    required=True,
)

parser.add_argument(
    "-U",
    "--deploy-user",
    help="Deploy user",
    required=True,
)

parser.add_argument(
    "-P",
    "--deploy-port",
    help="Deploy port (default: 22)",
    required=True,
    default="22",
)

parser.add_argument("--sentry-org", required=False)
parser.add_argument("--sentry-project", required=False)
parser.add_argument("--sentry-token", required=False)

parser.add_argument('--build-folder', required=False, default="build")

args = parser.parse_args()

DEPLOY_HOST = args.deploy_host
DEPLOY_USER = args.deploy_user
DEPLOY_PORT = args.deploy_port

SENTRY_AUTH_TOKEN = args.sentry_token
SENTRY_ORG = args.sentry_org
SENTRY_PROJECT = args.sentry_project

segments = args.segment  # ['production', 'staging', 'v0.0.1']
app_name = args.app_name  # 'some-report-app'
build_folder = args.build_folder # default is 'build'

def get_version_from_package_json():
    with open("package.json", "r") as f:
        data = f.read()
        data_json = json.loads(data)
        return data_json["version"]

def get_packager():
    if os.path.exists("yarn.lock"):
        return "yarn"
    else:
        return "npm"

packager = get_packager()


# https://docs.python.org/3/library/subprocess.html#module-subprocess
subprocess.run([packager, "install"], check=True)

deploy_urls = []

for segment in segments:
    print(f"Starting for {segment}...")
    ## Set URL path:
    url_path = f"/webapps/{app_name}/{segment}"

    ## Set output path:
    out_path = f"dist{url_path}/"

    print("Building...")

    ## Start building:
    subprocess.run(
        [packager, "run", "build"], env={**os.environ, "PUBLIC_URL": url_path}, check=True
    )

    subprocess.run(["mkdir", "-p", out_path], check=True)

    if os.path.exists(build_folder) and os.listdir(build_folder):
        subprocess.run(f"cp -R {build_folder}/** {out_path}", check=True, shell=True)
    
    if not os.path.exists(f"{out_path}") or not os.listdir(f"{out_path}"):
        raise Exception("Dist folder not found or empty. Aborting.")

    # upload release to sentry
    if SENTRY_ORG and SENTRY_PROJECT and SENTRY_AUTH_TOKEN:
        print("Uploading release to Sentry...")
        version = get_version_from_package_json()
        cmd_base = [packager, "run", "sentry-cli", "releases"]
        env = {
            "SENTRY_ORG": SENTRY_ORG,
            "SENTRY_PROJECT": SENTRY_PROJECT,
            "SENTRY_AUTH_TOKEN": SENTRY_AUTH_TOKEN,
        }
        cmds = [
            cmd_base + ["new", version],
            cmd_base + ["files", version, "upload-sourcemaps", out_path],
            cmd_base + ["finalize", version],
        ]
        for cmd in cmds:
            subprocess.run(cmd, check=True, env={**os.environ, **env})

    ## Deploy:
    print("Deploying...")

    remote_path = f"/data/websites/{DEPLOY_HOST}/htdocs{url_path}"
    subprocess.run(
        [
            "rsync",
            "-avzr",
            "--delete",
            f"--rsync-path=mkdir -p {remote_path} && rsync",
            f"-e ssh -o StrictHostKeyChecking=no -p {DEPLOY_PORT}",
            out_path,
            f"{DEPLOY_USER}@{DEPLOY_HOST}:{remote_path}",
        ],
        check=True,
    )

    deploy_urls.append(url_path)


## Set url paths:
name = 'urlpaths'
value = '||'.join(deploy_urls)

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    print(f"{name}={value}", file=f)

print("Done!")
