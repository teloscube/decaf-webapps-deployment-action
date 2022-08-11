#!/usr/bin/env python3

import argparse
import os
import subprocess

secrets = {
    "DEPLOY_HOST": os.environ["INPUT_REMOTE_HOST"],
    "DEPLOY_USER": os.environ["INPUT_REMOTE_USER"],
    "DEPLOY_PORT": os.environ.get("INPUT_REMOTE_PORT", "22"),
}


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

args = parser.parse_args()

segments = args.segment  # ['production', 'staging', 'v0.0.1']
app_name = args.app_name  # 'some-report-app'

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
    subprocess.run(
        f"mkdir -p {out_path} && cp -R build/** {out_path}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    ## Deploy:
    print("Deploying...")

    remote_path = f"/data/websites/{secrets['DEPLOY_HOST']}/htdocs{url_path}"
    subprocess.run(
        [
            "rsync",
            "-avzr",
            "--delete",
            f"--rsync-path=mkdir -p {remote_path} && rsync",
            f"-e ssh -o StrictHostKeyChecking=no -p {secrets['DEPLOY_PORT']}",
            out_path,
            f"{secrets['DEPLOY_USER']}@{secrets['DEPLOY_HOST']}:{remote_path}",
        ],
        check=True,
    )

    deploy_urls.append(url_path)


## Set url paths:
print(f"::set-output name=urlpaths::{'||'.join(deploy_urls)}")
print("Done!")
