# PowerShell script to rename template files
# Run this script from within your templates folder

Write-Host "Starting template file renaming..." -ForegroundColor Green

# Change to templates directory (adjust path if needed)
$templatesPath = "."
if (-not (Test-Path $templatesPath)) {
    Write-Host "Error: Templates directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $templatesPath

# List current files
Write-Host "Current files in templates directory:" -ForegroundColor Yellow
Get-ChildItem *.html | Select-Object Name

# Rename files
$renameOperations = @(
    @{
        OldName = "employee_admin_message_send.html"
        NewName = "employee_admin_messages_send.html"
    },
    @{
        OldName = "employee_message_send.html" 
        NewName = "employee_messages_send.html"
    }
)

Write-Host "`nRenaming files..." -ForegroundColor Yellow

foreach ($operation in $renameOperations) {
    $oldFile = $operation.OldName
    $newFile = $operation.NewName
    
    if (Test-Path $oldFile) {
        if (Test-Path $newFile) {
            Write-Host "Warning: $newFile already exists. Skipping rename of $oldFile" -ForegroundColor Red
        } else {
            Rename-Item -Path $oldFile -NewName $newFile
            Write-Host "Renamed: $oldFile -> $newFile" -ForegroundColor Green
        }
    } else {
        Write-Host "Warning: $oldFile not found" -ForegroundColor Yellow
    }
}

# Check for duplicate admin_message_send.html and remove if admin_send_message.html exists
if (Test-Path "admin_message_send.html") {
    if (Test-Path "admin_send_message.html") {
        Write-Host "Removing duplicate: admin_message_send.html" -ForegroundColor Yellow
        Remove-Item "admin_message_send.html"
    }
}

# Show final file list
Write-Host "`nFinal files in templates directory:" -ForegroundColor Yellow
Get-ChildItem *.html | Select-Object Name | Sort-Object Name

Write-Host "`nRenaming completed!" -ForegroundColor Green