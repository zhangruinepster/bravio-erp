@echo off
chcp 65001 > nul
echo ========================================================
echo        Bravio ERP 企业系统 - 本地实时测试环境启动
echo ========================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未检测到 .venv 虚拟环境，请先初始化虚拟环境。
    pause
    exit /b 1
)

echo [1/2] 激活虚拟环境并检查系统依赖...
set PYTHONPATH=%cd%\backend

echo [2/2] 启动 FastAPI 开发服务器 (热重载模式: http://127.0.0.1:8000)...
echo.
echo ========================================================
echo   * 访问 ERP 登录门户: http://127.0.0.1:8000
echo   * 查看 Swagger 文档: http://127.0.0.1:8000/api/v1/docs
echo   * 超级管理员凭据:   admin / admin123
echo   * 演示操作员凭据:   operator / operator123
echo ========================================================
echo.

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
pause
