## Katafanga - Python implementation of AlphaZero
This repository hosts the source code that served as the submission for our Bachelor Thesis at the IT-University of Copenhagen
in spring 2019. The point of this thesis was to implement a functioning version of Google DeepMind's *AlphaZero*, and to
have such an implementation train, and perform well, on consumer-grade hardware.
![Frontpage](http://mhooge.com/misc/katafanga.png)

#### Features
- Fully functional implementation of AlphaZero
- Training using Reinforcement Learning and Monte Carlo Tree Search with graphs and analytical data
- Support for three board games: Connect Four, Othello (Reversi), and Latrunculi
- Three types of AI agents: MCTS with Neural Network, Minimax, and MCTS without Neural Network
- Support for a human player to play against any of these using a visualized board with GUI
- Trained networks outperform all knowledge-based implementations (Minimax/Barebones MCTS) after ~1-2 days of training

### Katafanga playing Othello
[![Katafanga Demo](https://img.youtube.com/vi/BNDp_DNfXV8/maxresdefault.jpg)](https://www.youtube.com/watch?v=BNDp_DNfXV8)
