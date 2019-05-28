from sys import argv

x = int(argv[1])
y = int(argv[2])
size = 8

diag_x = size - (y - x) - 1 if y > x else size - (x - y) - 1
diag_y = size - (x-y) - 1 if x > y else size - (y-x) - 1

print((diag_x, diag_y))
