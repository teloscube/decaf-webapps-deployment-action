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

parser.add_argument(
    "--upload-to-sentry",
    help="Upload sourcemaps to Sentry",
    action=argparse.BooleanOptionalAction,
    default=False,
    required=False,
)

parser.add_argument(
    "--sentry-token",
    help="Sentry token",
    required=False,
)

args = parser.parse_args()

DEPLOY_HOST = args.deploy_host
DEPLOY_USER = args.deploy_user
DEPLOY_PORT = args.deploy_port
SENTRY_AUTH_TOKEN = args.sentry_token

segments = args.segment  # ['production', 'staging', 'v0.0.1']
app_name = args.app_name  # 'some-report-app'
upload_release = args.upload_to_sentry


def get_version_from_package_json():
    with open("package.json", "r") as f:
        data = f.read()
        data_json = json.loads(data)
        return data_json["version"]


# https://docs.python.org/3/library/subprocess.html#module-subprocess
subprocess.run(["yarn", "install"], check=True)

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
        ["yarn", "build"], env={**os.environ, "PUBLIC_URL": url_path}, check=True
    )
    subprocess.run(["mkdir", "-p", out_path], check=True)
    subprocess.run(["cp", "-R", "build/**", out_path], check=True)

    # upload release to sentry
    if upload_release and SENTRY_AUTH_TOKEN:
        print("Uploading release to Sentry...")
        version = get_version_from_package_json()
        cmd_base = ["yarn", "run", "sentry-cli", "releases"]
        cmds = [
            cmd_base + ["new", version],
            cmd_base + ["files", version, "upload-sourcemaps", out_path],
            cmd_base + ["finalize", version],
        ]
        for cmd in cmds:
            subprocess.run(
                cmd,
                check=True,
                environ={**os.environ, "SENTRY_AUTH_TOKEN": SENTRY_AUTH_TOKEN},
            )

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
print(f"::set-output name=urlpaths::{'||'.join(deploy_urls)}")
print("Done!")
