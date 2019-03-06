

@echo off
set /A size=4
:: Seeds used 42, 59, 89, 91
set /A seed=59
set /p test_name="Enter Test_name: "
start cmd.exe /c conda activate tf_env

start cmd.exe /c python .\main.py Random Minimax . %size% %seed% -g -eval 0 %test_name%
start cmd.exe /c python .\main.py Random Minimax . %size% %seed% -g -eval 1 %test_name%
start cmd.exe /c python .\main.py Random Minimax . %size% %seed% -g -eval 2 %test_name%
start cmd.exe /c python .\main.py Random Minimax . %size% %seed% -g -eval 3 %test_name%
start cmd.exe /c python .\main.py Random Minimax . %size% %seed% -g -eval 4 %test_name%
start cmd.exe /c python .\main.py Random Minimax . %size% %seed% -g -eval 5 %test_name%

PAUSE