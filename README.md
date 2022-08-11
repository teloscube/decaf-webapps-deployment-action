# DECAF Web Apps Deployment Action

1. Builds a DECAF Web App based on `branch`, `tag` and `deployment path`.
2. Deploys the built app to the remote server.

## Required Secrets

Set the following secrets in your repository or organization settings:

- `DEPLOY_HOST`: The hostname of the remote server.
- `DEPLOY_USER`: The username of the remote server.
- `DEPLOY_KEY`: The private key of the remote server.

## Example Usage

```yml
name: Deploy

on:
  release:
    types: [created]
  pull_request:
  push:
    branches:
      - main
    tags:
      - "*"

jobs:
  build:
    runs-on: ubuntu-18.04

    strategy:
      matrix:
        node-version: [16.x]

    steps:
      - uses: actions/checkout@v1

      - name: Use Node.js ${{matrix.node-version}}
        uses: actions/setup-node@v1
        with:
          node-version: ${{matrix.node-version}}

      - name: "Build and Deploy"
        id: build
        uses: teloscube/decaf-webapps-deployment-action
        with:
          app_name: demo-app
          production: true
          staging: true
          preview: true
          version: v0.1.0
          remote_host: ${{ secrets.DEPLOY_HOST }}
          remote_user: ${{ secrets.DEPLOY_USER }}
          remote_key: ${{ secrets.DEPLOY_KEY }}
```

## Outputs

You can use the following outputs. The values are populated after the action is completed. Normally, you would not need to use these outputs.

- `urlpaths`: The URL paths of the deployed apps separated by `||`. (e.g `/webapps/xxx/production||/webapps/xxx/staging||/webapps/xxx/preview-42`)

Example usage of the output values (Assuming the id of the step is `build`):

```yml
${{ steps.build.outputs.urlpaths }}
```
