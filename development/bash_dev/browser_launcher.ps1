# TI-CSC Browser Launcher for Windows Host
# This script monitors for browser launch triggers from the Docker GUI
# and opens browsers on the Windows host for optimal performance

param(
    [string]$ProjectPath = "",
    [int]$CheckInterval = 2,
    [switch]$Verbose = $false
)

# Function to write log messages
function Write-Log {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch($Type) {
        "INFO" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Type] $Message" -ForegroundColor $color
}

# Function to get the project directory
function Get-ProjectDirectory {
    if ($ProjectPath -and (Test-Path $ProjectPath)) {
        return $ProjectPath
    }
    
    # Try to auto-detect from current directory or common locations
    $currentDir = Get-Location
    $possiblePaths = @(
        $currentDir.Path,
        (Split-Path $currentDir.Path -Parent),
        "$env:USERPROFILE\Documents\02_Work\01_Projects\TI-Toolbox"
    )
    
    foreach ($path in $possiblePaths) {
        $tiCscInfo = Join-Path $path ".ti-csc-info"
        if (Test-Path $tiCscInfo) {
            Write-Log "Auto-detected project directory: $path"
            return $path
        }
    }
    
    Write-Log "Could not find project directory. Please specify with -ProjectPath parameter" "ERROR"
    return $null
}

# Function to launch browser
function Launch-Browser {
    param([string]$Url)
    
    try {
        Write-Log "Launching browser for: $Url"
        Start-Process $Url
        Write-Log "Browser launched successfully"
        return $true
    }
    catch {
        Write-Log "Failed to launch browser: $_" "ERROR"
        return $false
    }
}

# Function to process trigger file
function Process-TriggerFile {
    param([string]$TriggerFile)
    
    try {
        $triggerData = Get-Content $TriggerFile -Raw | ConvertFrom-Json
        
        if ($Verbose) {
            Write-Log "Processing trigger: $($triggerData.action)"
            Write-Log "URL: $($triggerData.url)"
            Write-Log "Timestamp: $($triggerData.timestamp)"
        }
        
        if ($triggerData.action -eq "launch_browser" -and $triggerData.url) {
            if (Launch-Browser -Url $triggerData.url) {
                # Delete the trigger file after successful launch
                Remove-Item $TriggerFile -Force
                Write-Log "Trigger file processed and removed"
                return $true
            }
        }
        
        return $false
    }
    catch {
        Write-Log "Error processing trigger file: $_" "ERROR"
        return $false
    }
}

# Main monitoring loop
function Start-Monitoring {
    param([string]$ProjectDir)
    
    $triggerDir = Join-Path $ProjectDir ".ti-csc-info"
    $triggerFile = Join-Path $triggerDir "launch_browser_trigger.json"
    
    Write-Log "Starting browser launch monitor..."
    Write-Log "Project directory: $ProjectDir"
    Write-Log "Monitoring: $triggerFile"
    Write-Log "Check interval: $CheckInterval seconds"
    Write-Log "Press Ctrl+C to stop monitoring"
    Write-Log ("=" * 60)
    
    $lastCheck = Get-Date
    
    while ($true) {
        try {
            if (Test-Path $triggerFile) {
                $fileInfo = Get-Item $triggerFile
                
                # Only process if file is newer than our last check
                if ($fileInfo.LastWriteTime -gt $lastCheck) {
                    Write-Log "New trigger file detected!"
                    
                    if (Process-TriggerFile -TriggerFile $triggerFile) {
                        $lastCheck = Get-Date
                    }
                }
            }
            
            Start-Sleep -Seconds $CheckInterval
        }
        catch {
            Write-Log "Monitor error: $_" "ERROR"
            Start-Sleep -Seconds ($CheckInterval * 2)
        }
    }
}

# Main execution
Clear-Host
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "   TI-CSC Browser Launcher for Windows Host" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

$projectDir = Get-ProjectDirectory
if ($projectDir) {
    Start-Monitoring -ProjectDir $projectDir
}
else {
    Write-Host ""
    Write-Host "Usage Examples:" -ForegroundColor Yellow
    Write-Host "  .\browser_launcher.ps1" -ForegroundColor White
    Write-Host "  .\browser_launcher.ps1 -ProjectPath `"C:\Path\To\Your\Project`"" -ForegroundColor White
    Write-Host "  .\browser_launcher.ps1 -Verbose" -ForegroundColor White
    Write-Host "  .\browser_launcher.ps1 -CheckInterval 1" -ForegroundColor White
    exit 1
} 