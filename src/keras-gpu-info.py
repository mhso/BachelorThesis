from tensorflow.python.client import device_lib
print(device_lib.list_local_devices())

# confirm TensorFlow sees the GPU
assert 'GPU' in str(device_lib.list_local_devices())

# confirm Keras sees the GPU
from keras import backend
assert len(backend.tensorflow_backend._get_available_gpus()) > 0