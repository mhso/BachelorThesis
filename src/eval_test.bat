PAUSE
start cmd.exe /c conda activate tf_env

start cmd.exe /k python .\main.py Random Minimax . 4 42 -g
start cmd.exe /k python .\main.py Random Minimax . 4 42 -g -mini1
start cmd.exe /k python .\main.py Random Minimax . 4 42 -g -mini2

PAUSE