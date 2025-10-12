@echo off
REM WhisperEngine Docker Cleanup Script (Windows Batch)
REM Removes all containers, volumes, and networks for a fresh start

setlocal enabledelayedexpansion

echo.
echo ================================
echo WhisperEngine Docker Cleanup
echo ================================
echo This will remove ALL WhisperEngine containers, volumes, and data
echo.

echo WARNING: This will DELETE:
echo   * All WhisperEngine containers
echo   * All database data (PostgreSQL)
echo   * All vector memory data (Qdrant)
echo   * All time-series data (InfluxDB)
echo   * All conversation logs
echo.
echo You will need to reconfigure your LLM settings after cleanup!
echo.

set /p confirm="Are you sure you want to continue? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Cleanup cancelled
    exit /b 0
)

echo.
echo [Step] Stopping all WhisperEngine containers...

REM Try to stop using any compose files we can find
if exist docker-compose.quickstart.yml (
    echo [Success] Stopping containers from docker-compose.quickstart.yml...
    docker-compose -f docker-compose.quickstart.yml down 2>nul
)

if exist docker-compose.containerized.yml (
    echo [Success] Stopping containers from docker-compose.containerized.yml...
    docker-compose -f docker-compose.containerized.yml down 2>nul
)

if exist docker-compose.yml (
    echo [Success] Stopping containers from docker-compose.yml...
    docker-compose -f docker-compose.yml down 2>nul
)

REM Stop any containers with whisperengine in the name
for /f "tokens=*" %%i in ('docker ps -aq --filter "name=whisperengine" 2^>nul') do (
    for /f "tokens=*" %%n in ('docker inspect --format "{{.Name}}" %%i 2^>nul') do (
        set containerName=%%n
        set containerName=!containerName:/=!
        docker stop %%i >nul 2>&1
        docker rm %%i >nul 2>&1
        echo [Success] Removed container: !containerName!
    )
)

echo.
echo [Step] Removing WhisperEngine volumes...

REM Remove volumes with whisperengine in the name
for /f "tokens=*" %%i in ('docker volume ls --format "{{.Name}}" 2^>nul ^| findstr /i whisperengine') do (
    docker volume rm %%i >nul 2>&1
    echo [Success] Removed volume: %%i
)

REM Also try common volume name patterns
for %%v in (postgres_data qdrant_data influxdb_data whisperengine_logs grafana_data) do (
    docker volume rm %%v >nul 2>&1
    if not errorlevel 1 (
        echo [Success] Removed volume: %%v
    )
)

echo.
echo [Step] Removing WhisperEngine networks...

REM Remove networks
for %%n in (whisperengine-network whisperengine_default) do (
    docker network rm %%n >nul 2>&1
    if not errorlevel 1 (
        echo [Success] Removed network: %%n
    )
)

echo.
echo [Step] Cleaning up dangling resources...
docker volume prune -f >nul 2>&1

echo.
echo ================================
echo [Success] Cleanup complete!
echo ================================
echo.
echo Next steps:
echo.
echo 1. Run the quickstart setup again:
echo    quickstart-setup.bat
echo.
echo 2. Or if you already have the files, start fresh:
echo    docker-compose -f docker-compose.quickstart.yml up -d
echo.
echo NOTE: You'll need to reconfigure your LLM settings in .env
echo.

endlocal
