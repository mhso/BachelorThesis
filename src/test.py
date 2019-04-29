import pickle

class SaveStuff:
    def __init__(self, val=None):
        self.val = val or "z"

s = SaveStuff()
s.val = "avg"

with open("wow.bin", "wb") as f:
    pickle.dump(s, f)

with open("wow.bin", "rb") as f:
    s = pickle.load(f)
    print(s.val)
