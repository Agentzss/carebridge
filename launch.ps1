# CareBridge Hospital - PowerShell Control Menu
# Run this script to control the web app from PowerShell

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "    ╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "    ║                                                               ║" -ForegroundColor Cyan
    Write-Host "    ║           🏥  CAREBRIDGE HOSPITAL SYSTEM                     ║" -ForegroundColor Cyan
    Write-Host "    ║              PowerShell Control Menu                          ║" -ForegroundColor Cyan
    Write-Host "    ║                                                               ║" -ForegroundColor Cyan
    Write-Host "    ╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Check Docker status
    $dockerRunning = $null
    try { $dockerRunning = docker ps --filter "name=carebridge" --format "{{.Names}}" 2>$null } catch {}

    if ($dockerRunning -eq "carebridge") {
        Write-Host "    [Docker Container] " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green
        Write-Host "    [Local URL]      http://localhost:5000" -ForegroundColor Green
    } else {
        Write-Host "    [Docker Container] " -NoNewline
        Write-Host "STOPPED" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "    ┌─────────────────────────────────────────────────────────────┐"
    Write-Host "    │  1.  Start Docker Container                                 │"
    Write-Host "    │  2.  Stop Docker Container                                  │"
    Write-Host "    │  3.  Rebuild Docker Image                                   │"
    Write-Host "    │  4.  Start ngrok (Public URL)                               │"
    Write-Host "    │  5.  Open Browser - Dashboard                               │"
    Write-Host "    │  6.  Open Browser - Register Patient                        │"
    Write-Host "    │  7.  Open Browser - Book Appointment                        │"
    Write-Host "    │  8.  Open Browser - Calculate Bill                          │"
    Write-Host "    │  9.  Open Browser - Triage Room                             │"
    Write-Host "    │  10. Show Docker Status                                     │"
    Write-Host "    │  11. Stop Everything (Docker + ngrok)                       │"
    Write-Host "    │  0.  Exit                                                   │"
    Write-Host "    └─────────────────────────────────────────────────────────────┘"
    Write-Host ""
}

function Start-DockerContainer {
    Write-Host ""
    Write-Host "    Starting Docker container..." -ForegroundColor Yellow

    # Check if already running
    $running = docker ps --filter "name=carebridge" --format "{{.Names}}" 2>$null
    if ($running -eq "carebridge") {
        Write-Host "    Container is already running!" -ForegroundColor Green
        Start-Sleep -Seconds 2
        return
    }

    # Check if exists but stopped
    $exists = docker ps -a --filter "name=carebridge" --format "{{.Names}}" 2>$null
    if ($exists -eq "carebridge") {
        docker start carebridge | Out-Null
    } else {
        docker run -d -p 5000:5000 --name carebridge carebridge-hospital | Out-Null
    }

    Start-Sleep -Seconds 3
    $running = docker ps --filter "name=carebridge" --format "{{.Names}}" 2>$null
    if ($running -eq "carebridge") {
        Write-Host "    ✅ Container started successfully!" -ForegroundColor Green
        Write-Host "    🌐 Open http://localhost:5000 in your browser" -ForegroundColor Cyan
    } else {
        Write-Host "    ❌ Failed to start container. Check Docker Desktop." -ForegroundColor Red
    }
    Start-Sleep -Seconds 2
}

function Stop-DockerContainer {
    Write-Host ""
    Write-Host "    Stopping Docker container..." -ForegroundColor Yellow
    docker stop carebridge 2>$null | Out-Null
    Write-Host "    ✅ Container stopped." -ForegroundColor Green
    Start-Sleep -Seconds 2
}

function Rebuild-DockerImage {
    Write-Host ""
    Write-Host "    Rebuilding Docker image..." -ForegroundColor Yellow

    # Stop and remove old container
    docker stop carebridge 2>$null | Out-Null
    docker rm carebridge 2>$null | Out-Null

    # Rebuild
    docker build -t carebridge-hospital . 2>&1 | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "    ✅ Image rebuilt! Start the container with option 1." -ForegroundColor Green
    Start-Sleep -Seconds 3
}

function Start-Ngrok {
    Write-Host ""
    Write-Host "    Starting ngrok..." -ForegroundColor Yellow
    Write-Host "    (A new window will open. Copy the https:// URL from it.)" -ForegroundColor Cyan
    Write-Host ""
    Start-Sleep -Seconds 1

    # Start ngrok in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 5000"

    Write-Host "    ✅ ngrok started in a new window!" -ForegroundColor Green
    Write-Host "    📱 Copy the https:// URL and test on your phone." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
}

function Open-Browser {
    param([string]$Path = "")
    $url = "http://localhost:5000$Path"
    Write-Host ""
    Write-Host "    Opening $url ..." -ForegroundColor Yellow
    Start-Process $url
    Start-Sleep -Seconds 1
}

function Show-DockerStatus {
    Write-Host ""
    Write-Host "    Docker Container Status:" -ForegroundColor Cyan
    Write-Host "    ─────────────────────────" -ForegroundColor Gray
    docker ps --filter "name=carebridge" --format "table {{.Names}}	{{.Status}}	{{.Ports}}" 2>$null
    if ($LASTEXITCODE -ne 0 -or !(docker ps --filter "name=carebridge" --format "{{.Names}}" 2>$null)) {
        Write-Host "    No container running." -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "    Press Enter to continue..." -ForegroundColor Gray
    Read-Host
}

function Stop-Everything {
    Write-Host ""
    Write-Host "    Stopping everything..." -ForegroundColor Yellow
    docker stop carebridge 2>$null | Out-Null
    docker rm carebridge 2>$null | Out-Null
    Write-Host "    ✅ Docker container stopped and removed." -ForegroundColor Green
    Write-Host "    ⚠️  Close the ngrok window manually if it's still open." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

# ========== MAIN LOOP ==========
do {
    Show-Menu
    $choice = Read-Host "    Enter your choice (0-11)"

    switch ($choice) {
        "1" { Start-DockerContainer }
        "2" { Stop-DockerContainer }
        "3" { Rebuild-DockerImage }
        "4" { Start-Ngrok }
        "5" { Open-Browser "" }
        "6" { Open-Browser "/register" }
        "7" { Open-Browser "/appointment" }
        "8" { Open-Browser "/bill" }
        "9" { Open-Browser "/triage" }
        "10" { Show-DockerStatus }
        "11" { Stop-Everything }
        "0" { 
            Write-Host ""
            Write-Host "    Goodbye! 👋" -ForegroundColor Green
            exit 
        }
        default {
            Write-Host ""
            Write-Host "    ❌ Invalid choice. Press Enter to try again." -ForegroundColor Red
            Read-Host
        }
    }
} while ($true)
