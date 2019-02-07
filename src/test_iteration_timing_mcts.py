from testing.test_mcts import run_iteration_tests

ITERS = 5
times = [0] * ITERS
for i in range(ITERS):
    time_taken = run_iteration_tests()
    print("MCTS move time: {} s".format(time_taken), flush=True)
    times[i] = time_taken

print("Average time for MCTS: {}".format(sum(times)/len(times)))
