@echo off
chcp 65001 >nul
echo ======================================
echo   灵犀客服 - 运维脚本集
echo ======================================
echo.
echo 请选择操作：
echo   [1] 启动中间件 (start_middleware.sh)
echo   [2] 检测服务状态 (check_services.sh)
echo   [3] 执行数据库迁移 (migrate.sql)
echo   [4] 退出
echo.
set /p choice=请输入选项 [1-4]:

if "%choice%"=="1" goto start
if "%choice%"=="2" goto check
if "%choice%"=="3" goto migrate
if "%choice%"=="4" goto end

:start
echo.
echo 正在启动中间件...
bash scripts\start_middleware.sh
pause
goto end

:check
echo.
echo 正在检测服务状态...
bash scripts\check_services.sh
pause
goto end

:migrate
echo.
echo 执行数据库迁移...
echo 请确保 PostgreSQL 已启动！
echo.
set /p HOST:=请输入数据库地址 [默认: 10.99.216.94]:
if "%HOST%"=="" set HOST=10.99.216.94

set /p USER:=请输入数据库用户 [默认: lingxi]:
if "%USER%"=="" set USER=lingxi

set /p DB:=请输入数据库名 [默认: lingxi_support]:
if "%DB%"=="" set DB=lingxi_support

psql -h %HOST% -p 5432 -U %USER% -d %DB% -f scripts\migrate.sql
pause
goto end

:end
echo.
echo 操作完成！
