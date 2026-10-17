# Bravio ERP - PowerShell 本地开发环境启动脚本
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Bravio ERP 企业系统 - 本地实时测试环境启动" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[错误] 未检测到 .venv 虚拟环境！" -ForegroundColor Red
    exit 1
}

$env:PYTHONPATH = Join-Path $scriptDir "backend"

Write-Host "✨ 启动 FastAPI 开发服务器 (热重载模式: http://127.0.0.1:8000)..." -ForegroundColor Yellow
Write-Host "  * 访问 ERP 登录门户: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  * 查看 Swagger 文档: http://127.0.0.1:8000/api/v1/docs" -ForegroundColor White
Write-Host "  * 默认管理员凭据:   admin / admin123" -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Cyan

& $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
