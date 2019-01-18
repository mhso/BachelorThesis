import keras
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Activation, Dense, Dropout
from keras.optimizers import Adam

model = Sequential()
model.add(Dense(128, activation="relu", input_shape=(2, 4)))
model.add(Dense(1, activation="relu"))

model.compile(Adam(), "mean_squared_error", ["accuracy"])