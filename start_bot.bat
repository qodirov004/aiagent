@echo off
chcp 65001 >nul
cd /d "d:\Projects\Ai agent"
echo [%date% %time%] Bot ishga tushmoqda... >> telegram_bot_startup.log
"d:\Projects\Ai agent\venv\Scripts\pythonw.exe" -m telegram_bot.run
