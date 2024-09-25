while (1) {
    if (Test-Path .\runtime.json) {
        
        Write-Host "new runtime.json found"
        
        Start-Process powershell.exe -ArgumentList "-File", ".\movejsontowsl.ps1"
        
        Wait-Event -Timeout 10
        Remove-Item .\runtime.json

        Write-Host "job called and removed json"
    }
    Wait-Event -Timeout 2
}
