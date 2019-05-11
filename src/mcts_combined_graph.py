import matplotlib.pyplot as plt
import pickle
from glob import glob

colors = ["r", "b", "c", "g", "m", "#00EE00", "#FF8000", "y"]
names = ["Baseline", "Small network", "Only q", "Only z", "400 MCTS iter.", "Q/Z linear falloff", "Growing storage", "Lower noise"]
plt.figure(figsize=(10, 7))
for i in range(8):
    tup_list = []
    x = []
    y = []
    files = glob(f"../resources/combined_graph/test_{i+1}/perform_eval_mcts_*")
    for file in files:
        step = file.strip().split("_")[-1][:-4]
        tup_list.append((int(step), pickle.load(open(file, "rb"))[0]))
    tup_list.sort(key=lambda sd: sd[0])
    x = [data[0] for data in tup_list]
    y = [data[1] for data in tup_list]
    names[i] = f"Test {i+1} - " + names[i]
    plt.plot(x, y, color=colors[i])

plt.legend(names)
plt.title("Win rate vs. MCTS for all tests")
plt.xlabel("Training iterations")
plt.ylabel("Win rate")
plt.grid(which="both", axis="both")
plt.savefig(f"../resources/combined_graph/graph.png")
plt.show()
