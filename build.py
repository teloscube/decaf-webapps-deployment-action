import argparse
import os
import subprocess

# get rid of this when we are ready to read from github secrets
secrets = {
    "DEPLOY_HOST": os.environ["DEPLOY_HOST"],
    "DEPLOY_USER": os.environ["DEPLOY_USER"],
    "DEPLOY_KEY": os.environ["DEPLOY_KEY"],
}


parser = argparse.ArgumentParser(description="Build and deploy DECAF App")
parser.add_argument(
    "-s",
    "--segment",
    action="append",
    help="Segment to build\nE.g: production, staging or v0.1.0",
    required=True,
)
args = parser.parse_args()

segments = args.segment  # ['production', 'staging', 'v0.0.1']


subprocess.run(["yarn", "install"])
subprocess.run(["yarn", "build"])

for segment in segments:
    print(f"Starting for {segment}...")
    ## Set URL path:
    url_path = f"/webapps/action-test/{segment}"

    ## Set output path:
    out_path = f"dist{url_path}/"

    ## Set environment variables:
    os.environ["PUBLIC_URL"] = url_path

    print("Building...")

    ## Start building:
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
            f"-e ssh -o StrictHostKeyChecking=no -i {secrets['DEPLOY_KEY']}",
            out_path,
            f"{secrets['DEPLOY_USER']}@{secrets['DEPLOY_HOST']}:{remote_path}",
        ]
    )

    ## Set outputs:
    subprocess.run(["echo", "::set-output", f'name=segment::"{segment}"'])
    subprocess.run(["echo", "::set-output", f'name=urlpath::"{url_path}"'])
    subprocess.run(["echo", "::set-output", f'name=outpath::"{out_path}"'])
    subprocess.run(["echo", "::set-output", f'name=PUBLIC_URL::"{url_path}"'])

    print("Done!")
