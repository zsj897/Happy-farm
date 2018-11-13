call basePath.bat

@echo off
set pydatas=%ktpydatas%/task.py
set excel1=%ktexcels%/xlsxs/task.xlsx

echo on
python ../xlsx2py/xlsx2py.py %pydatas% %excel1%
if not defined ktall (ping -n 30 127.1>nul)

