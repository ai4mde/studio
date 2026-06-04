param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("local", "xyz")]
    [string] $Mode
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

function Set-EnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,
        [Parameter(Mandatory = $true)]
        [string] $Key,
        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    $fullPath = Join-Path $root $Path
    $lines = Get-Content -LiteralPath $fullPath
    $found = $false
    $updated = foreach ($line in $lines) {
        if ($line -match "^$([regex]::Escape($Key))=") {
            $found = $true
            "$Key=$Value"
        } else {
            $line
        }
    }

    if (-not $found) {
        $updated += "$Key=$Value"
    }

    Set-Content -LiteralPath $fullPath -Value $updated
}

if ($Mode -eq "local") {
    $apiHost = "api.ai4mde.localhost"
    $studioHost = "ai4mde.localhost"
    $prototypeHost = "prototype.ai4mde.localhost"
    $apiProto = "http://"
    $apiPort = "80"
    $prototypeProto = "http://"
} else {
    $apiHost = "api.aivorab.xyz"
    $studioHost = "ai4mde.aivorab.xyz"
    $prototypeHost = "prototype.aivorab.xyz"
    $apiProto = "https://"
    $apiPort = "443"
    $prototypeProto = "https://"
}

Set-EnvValue "config/api.env" "HOSTNAME" $apiHost
Set-EnvValue "config/api.env" "STUDIO_HOSTNAME" $studioHost

Set-EnvValue "config/frontend.env" "AI4MDE_HOST" $apiHost
Set-EnvValue "config/frontend.env" "AI4MDE_PORT" $apiPort
Set-EnvValue "config/frontend.env" "AI4MDE_PROTO" $apiProto
Set-EnvValue "config/frontend.env" "RUNNING_PROTOTYPE_HOST" $prototypeHost
Set-EnvValue "config/frontend.env" "RUNNING_PROTOTYPE_PROTO" $prototypeProto
Set-EnvValue "config/frontend.env" "AI4MDE_PROTOTYPE_HOST" $prototypeHost
Set-EnvValue "config/frontend.env" "AI4MDE_PROTOTYPE_PROTO" $prototypeProto

Set-EnvValue "config/prototypes.env" "RUNNING_PROTOTYPE_PUBLIC_HOST" $prototypeHost
Set-EnvValue "config/prototypes.env" "RUNNING_PROTOTYPE_PUBLIC_PROTO" $prototypeProto

Write-Host "Switched Studio domain mode to '$Mode'."
Write-Host "Restart services with: docker compose up -d --force-recreate studio-api studio-prototypes studio"
