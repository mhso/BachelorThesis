import numpy as np

def softmax_sample(child_nodes, visit_counts, tempature=2.5):
    """
    Perform softmax sampling on a set of nodes
    based on a probability distribution of their
    visit counts.
    """
    sum_visits = sum(visit_counts)
    prob_visits = [(v/sum_visits) * tempature for v in visit_counts]
    exps = np.exp(prob_visits)
    print(f"Probabilities of softmax: {exps/sum(exps)}")

    return np.random.choice(child_nodes,
                            p=exps/sum(exps))

softmax_sample(["Node 1", "Node 2", "Node 3", "Node 4", "Node 5"],
               [10, 40, 24, 4, 22])
