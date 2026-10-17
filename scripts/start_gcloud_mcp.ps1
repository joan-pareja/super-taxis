$ErrorActionPreference = 'Stop'

# Keep this repository's Google login separate from the default user login.
$env:CLOUDSDK_CONFIG = Join-Path (Split-Path $PSScriptRoot -Parent) '.cache/gcloud'

# stdout belongs to the MCP protocol; do not print startup messages here.
& npx.cmd -y '@google-cloud/gcloud-mcp@0.5.3'
exit $LASTEXITCODE
