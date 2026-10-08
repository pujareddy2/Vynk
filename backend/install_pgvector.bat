@echo off
echo =======================================================
echo Localy (Vynk) - Installing pgvector for PostgreSQL 17
echo =======================================================
echo.
echo Please run this script as Administrator (Right click -> Run as administrator)
echo.

set "SRC=%TEMP%\vector_pg17"
set "PG=C:\Program Files\PostgreSQL\17"

if not exist "%SRC%\lib\vector.dll" (
    echo Downloading pgvector binaries...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/andreiramani/pgvector_pgsql_windows/releases/download/0.8.6_17/vector.v0.8.6-pg17.zip' -OutFile '%TEMP%\vector_pg17.zip'; Expand-Archive -Path '%TEMP%\vector_pg17.zip' -DestinationPath '%TEMP%\vector_pg17' -Force"
)

echo Copying extension files to PostgreSQL 17...
copy /Y "%SRC%\lib\vector.dll" "%PG%\lib\"
copy /Y "%SRC%\share\extension\vector*" "%PG%\share\extension\"
if not exist "%PG%\include\server\extension\vector" mkdir "%PG%\include\server\extension\vector"
copy /Y "%SRC%\include\server\extension\vector\*" "%PG%\include\server\extension\vector\"

echo.
echo pgvector binaries installed successfully!
echo.
pause
