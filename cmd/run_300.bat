@echo off
call activate cv
python ../split_lite_video.py %1 300
pause