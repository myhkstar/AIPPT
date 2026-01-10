@echo off
echo Checking for .env file...
if not exist .env (
    echo .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please update .env with your credentials.
)

echo Building and starting Docker containers...
docker-compose up --build -d

echo.
echo Containers started!
echo Backend: http://localhost:8080
echo Frontend: http://localhost:3000
echo.
echo To view logs: docker-compose logs -f
pause
