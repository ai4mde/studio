$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

$logFrontend = "$env:TEMP\tunnel-frontend.log"
$logApi      = "$env:TEMP\tunnel-api.log"
$logProto    = "$env:TEMP\tunnel-proto.log"

Remove-Item $logFrontend, $logApi, $logProto -ErrorAction SilentlyContinue

Write-Host "Starting tunnels..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit -Command `"cloudflared tunnel --url http://localhost:80 --http-host-header ai4mde.localhost 2>&1 | Tee-Object -FilePath '$logFrontend'`"" -WindowStyle Minimized
Start-Process powershell -ArgumentList "-NoExit -Command `"cloudflared tunnel --url http://localhost:8000 --http-host-header api.ai4mde.localhost 2>&1 | Tee-Object -FilePath '$logApi'`"" -WindowStyle Minimized
Start-Process powershell -ArgumentList "-NoExit -Command `"cloudflared tunnel --url http://localhost:80 --http-host-header prototype.ai4mde.localhost 2>&1 | Tee-Object -FilePath '$logProto'`"" -WindowStyle Minimized

function Get-TunnelUrl($logFile) {
    $timeout = 30
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 1
        $elapsed++
        if (Test-Path $logFile) {
            $line = Get-Content $logFile | Select-String "trycloudflare.com" | Select-Object -Last 1
            if ($line) {
                if ($line -match "https://[a-z0-9\-]+\.trycloudflare\.com") {
                    return $Matches[0]
                }
            }
        }
    }
    return $null
}

Write-Host "Waiting for tunnel URLs..." -ForegroundColor Yellow

$urlFrontend = Get-TunnelUrl $logFrontend
$urlApi      = Get-TunnelUrl $logApi
$urlProto    = Get-TunnelUrl $logProto

if (-not $urlFrontend -or -not $urlApi -or -not $urlProto) {
    Write-Host "Failed to get tunnel URLs. Check logs at $env:TEMP" -ForegroundColor Red
    exit 1
}

$hostApi   = $urlApi   -replace "https://", ""
$hostProto = $urlProto -replace "https://", ""

Write-Host ""
Write-Host "Frontend : $urlFrontend" -ForegroundColor Green
Write-Host "API      : $urlApi"      -ForegroundColor Green
Write-Host "Prototype: $urlProto"    -ForegroundColor Green

$envContent = @"
HOSTNAME=ai4mde.localhost
AI4MDE_HOST=$hostApi
AI4MDE_PORT=443
AI4MDE_PROTO=https://
RUNNING_PROTOTYPE_HOST=$hostProto
RUNNING_PROTOTYPE_PROTO=https://
"@

Set-Content -Path "E:\projects\studio\config\frontend.env" -Value $envContent -Encoding utf8

Write-Host ""
Write-Host "Restarting frontend container..." -ForegroundColor Yellow
Set-Location E:\projects\studio
docker compose up -d --force-recreate studio | Out-Null

Write-Host ""
Write-Host "Done! Share this URL with participants:" -ForegroundColor Green
Write-Host $urlFrontend -ForegroundColor White
