@ECHO OFF
SET player1=Random
SET player2=Minimax
SET game=.
SET/A size=4
SET /P test_name="Enter Test_name [Test1_xyz]: "
SET /P seed="Enter Seed [42, 59, 89, 91]: "
SET /P conda_env="Enter you conda env name [tf_env]: "

:: %game% %size% set in eval_test_setup.bat
START cmd.exe /K CALL eval_test_setup.bat %conda_env% %player1% %player2% %seed% -g -eval 0 %test_name%
START cmd.exe /K CALL eval_test_setup.bat %conda_env% %player1% %player2% %seed% -g -eval 1 %test_name%
START cmd.exe /K CALL eval_test_setup.bat %conda_env% %player1% %player2% %seed% -g -eval 2 %test_name%
START cmd.exe /K CALL eval_test_setup.bat %conda_env% %player1% %player2% %seed% -g -eval 3 %test_name%
START cmd.exe /K CALL eval_test_setup.bat %conda_env% %player1% %player2% %seed% -g -eval 4 %test_name%
START cmd.exe /K CALL eval_test_setup.bat %conda_env% %player1% %player2% %seed% -g -eval 5 %test_name%

:: START cmd.exe /K python .\main.py  . %size% %seed% -g -eval 0 %test_name%
:: START cmd.exe /K python .\main.py Random Minimax . %size% %seed% -g -eval 1 %test_name%
:: START cmd.exe /K python .\main.py Random Minimax . %size% %seed% -g -eval 2 %test_name%
:: START cmd.exe /K python .\main.py Random Minimax . %size% %seed% -g -eval 3 %test_name%
:: START cmd.exe /K python .\main.py Random Minimax . %size% %seed% -g -eval 4 %test_name%
:: START cmd.exe /K python .\main.py Random Minimax . %size% %seed% -g -eval 5 %test_name%

PAUSE