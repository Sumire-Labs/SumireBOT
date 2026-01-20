# SumireBot 起動スクリプト
# /restart コマンドでの自動再起動をサポート

$RESTART_CODE = 26

Write-Host "SumireBot 起動スクリプト" -ForegroundColor Cyan
Write-Host "終了: Ctrl+C | 再起動: /restart コマンド" -ForegroundColor Gray
Write-Host ""

# 仮想環境をアクティベート（存在する場合）
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
}

while ($true) {
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Bot を起動します..." -ForegroundColor Green

    python bot.py
    $exitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Bot が終了しました (終了コード: $exitCode)" -ForegroundColor Yellow

    if ($exitCode -eq $RESTART_CODE) {
        Write-Host "再起動します..." -ForegroundColor Cyan
        Start-Sleep -Seconds 2
    } else {
        Write-Host "終了します。" -ForegroundColor Red
        break
    }
}
