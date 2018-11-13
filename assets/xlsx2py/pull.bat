@echo "将会清空更改 是否继续"
pause
cd /d D:\develop\unityProject
git reset --hard
git pull LOSER master
cd D:\develop\server\KBE\assets
git reset --hard
git pull SERVER master 
pause