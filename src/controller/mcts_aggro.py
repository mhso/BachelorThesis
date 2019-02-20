from controller.mcts_basic import MCTS_Basic

class MCTS_Aggro(MCTS_Basic):
    def back_propagate(self, node, value):
        """
        After a full simulation, propagate result up the tree.
        """
        new_value = value - 0.0001 if value > 0 else value + 0.0001
        node.visits += 1
        node.value += new_value
        node.mean_value = node.value/node.visits

        if node.parent is None:
            return
        self.back_propagate(node.parent, -new_value)
