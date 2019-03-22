import numpy as np

test_data = [23, 26, 37, 29, 185]
normed = [v / sum(test_data) for v in test_data]

temp = 0.7

softmax = (np.exp(normed)*temp) * (np.sum(np.exp(normed)*temp))
print("Peak diff: {}".format(np.ptp(softmax)))
print(softmax)
