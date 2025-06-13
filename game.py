import numpy as np
from collections import deque


class Board:
    def __init__(self, **kwargs):  # 初始化函数
        self.width = kwargs.get("width", 11)
        self.height = kwargs.get("height", 11)
        self.states = {}  # key: (h, w), value: player
        self.players = [1, 2]  # 玩家1(黑棋)和玩家2(白棋)
        self.feature_planes = 8

        self.states_sequence = deque(maxlen=self.feature_planes)
        self.states_sequence.extendleft([[-1, -1]] * self.feature_planes)
        # 8个最近的状态平面

    def init_board(self, start_player=0):
        '''
        初始化棋盘并设置一些变量
        '''
        # 设置当前玩家（默认从players列表的第一个玩家开始）
        self.current_player = self.players[start_player]

        # 初始化可用移动列表，包含所有可能的位置
        self.availables = list(range(self.width * self.height))

        # 初始化状态字典，用于记录每个位置的落子情况
        self.states = {}

        # 记录上一步的移动（-1表示还没有移动）
        self.last_move = -1

        # 重置移动历史队列，清除之前的游戏记录
        self.states_sequence = deque(maxlen=self.feature_planes)
        self.states_sequence.extendleft([[-1, -1]] * self.feature_planes)

    def move_to_location(self, move: int):
        h = move // self.width
        w = move % self.width
        return [h, w]

    def location_to_move(self, location):  # 位置表示转换函数
        if len(location) != 2:
            return -1
        h: int = location[0]
        w: int = location[1]

        move: int = h * self.width + w
        if move not in range(self.width * self.height):
            return -1
        return move

    def current_state(self):
        '''
        返回当前玩家视角的棋盘状态
        形状为(feature_planes + 1) * width * height
        +1 用于标识当前玩家
        '''
        square_state = np.zeros((self.feature_planes + 1, self.width, self.height))
        if self.states:
            moves, players = np.array(list(zip(*self.states.items())))
            # 解码出玩家的移动和对应的玩家
            move_curr = moves[players == self.current_player]
            move_oppo = moves[players != self.current_player]

            # 构建特征平面
            for i in range(self.feature_planes):
                # 每个平面表示一个移动
                if i % 2 == 0:
                    square_state[i][move_oppo // self.width, move_oppo % self.height] = 1.0
                else:
                    square_state[i][move_curr // self.width, move_curr % self.height] = 1.0
            # 删除一些移动以构建具有历史特征的平面
            for i in range(0, len(self.states_sequence) - 2, 2):
                for j in range(i + 2, len(self.states_sequence), 2):
                    if self.states_sequence[i][1] != -1:
                        assert square_state[j][self.states_sequence[i][0] // self.width, self.states_sequence[i][
                            0] % self.height] == 1.0, 'wrong oppo number'
                        square_state[j][
                            self.states_sequence[i][0] // self.width, self.states_sequence[i][0] % self.height] = 0.
            for i in range(1, len(self.states_sequence) - 2, 2):
                for j in range(i + 2, len(self.states_sequence), 2):
                    if self.states_sequence[i][1] != -1:
                        assert square_state[j][self.states_sequence[i][0] // self.width, self.states_sequence[i][
                            0] % self.height] == 1.0, 'wrong player number'
                        square_state[j][
                            self.states_sequence[i][0] // self.width, self.states_sequence[i][0] % self.height] = 0.

        if len(self.states) % 2 == 0:
            # if %2==0，it's player1's turn to player,then we assign 1 to the the whole plane,otherwise all 0
            square_state[self.feature_planes][:, :] = 1.0  # indicate the colour to play

        # we should reverse it before return,for example the board is like
        # 0,1,2,
        # 3,4,5,
        # 6,7,8,
        # we will change it like
        # 6 7 8
        # 3 4 5
        # 0 1 2
        return square_state[:, ::-1, :]

    def do_move(self, move):
        # 更新棋盘
        self.states[move] = self.current_player
        self.states_sequence.appendleft([move, self.current_player])
        self.availables.remove(move)

        self.current_player = (
            self.players[0] if self.current_player == self.players[1]
            else self.players[1]
        )

        self.last_move = move

    def has_a_winner(self):  # 判断是否有玩家胜利
        # 检查玩家1(黑棋)是否连接上下边界
        if self._is_connected(1, lambda h, w: h == 0, lambda h, w: h == self.height - 1):
            return True, 1

        # 检查玩家2(白棋)是否连接左右边界
        if self._is_connected(2, lambda h, w: w == 0, lambda h, w: w == self.width - 1):
            return True, 2
        # 如果没有玩家胜利
        return False, -1

    def _is_connected(self, player, start_condition, end_condition):
        # 初始化
        visited = set()

        # 六方向邻居(六边形网格)
        directions = [
            (-1, 0),  # 上
            (-1, 1),  # 右上
            (0, 1),  # 右
            (1, 0),  # 下
            (1, -1),  # 左下
            (0, -1)  # 左
        ]

        for h in range(self.height):
            for w in range(self.width):
                move = self.location_to_move((h, w))
                if move in self.states and self.states[move] == player and start_condition(h,
                                                                                           w) and move not in visited:
                    # BFS 初始化
                    queue = deque([move])
                    visited.add(move)

                    while queue:
                        current_move = queue.popleft()
                        current_h, current_w = self.move_to_location(current_move)

                        if end_condition(current_h, current_w):
                            return True
                        for dh, dw in directions:
                            new_h, new_w = current_h + dh, current_w + dw

                            # 检查边界
                            if 0 <= new_h < self.height and 0 <= new_w < self.width:
                                # 检查是否为同玩家的棋子且未访问过
                                new_move = self.location_to_move((new_h, new_w))
                                if new_move in self.states and self.states[
                                    new_move] == player and new_move not in visited:
                                    visited.add(new_move)
                                    queue.append(new_move)
        return False

    def game_end(self):
        """检查游戏是否结束，返回(是否结束, 获胜者)"""
        end, winner = self.has_a_winner()
        if end:
            return True, winner
        else:
            return False, -1

    def get_current_player(self):
        """获取当前玩家"""
        return self.current_player


class Game:
    def __init__(self, board, **kwargs):
        self.board = board

    def graphic(self, board, player1, player2):
        width = board.width
        height = board.height

        print("Player", player1, "with X (连接上下)")
        print("Player", player2, "with O (连接左右)")
        print("棋盘状态:", board.states)
        print()

        # 打印列号
        print(' ' * 4, end='')
        for x in range(width):
            print("{0:4d}".format(x), end='')
        print('\n')

        # 正确的行序显示
        for i in range(height):  # ✓ 从0到height-1，正序显示
            print("{0:4d}".format(i), end='')
            for j in range(width):
                # 使用标准的location_to_move计算
                move = board.location_to_move((i, j))  # ✓ 保持一致性
                p = board.states.get(move, -1)
                if p == player1:
                    print('X'.center(4), end='')
                elif p == player2:
                    print('O'.center(4), end='')
                else:
                    print('-'.center(4), end='')
            print('\r\n\r\n')

    def start_play(self, player1, player2, start_player=0, is_shown=1):
        """start a game between two players"""
        if start_player not in (0, 1):
            raise Exception('start_player should be either 0 (player1 first) '
                            'or 1 (player2 first)')
        self.board.init_board(start_player)
        p1, p2 = self.board.players
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2: player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player)
        while True:
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, player1.player, player2.player)
            end, winner = self.board.game_end()
            if end:
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is", players[winner])
                    else:
                        print("Game end. Tie")
                return winner

    def start_self_play(self, player, is_shown=0, temp=1e-3):
        """ start a self-play game using a MCTS player, reuse the search tree,
        and store the self-play data: (state, mcts_probs, z) for training
        """
        self.board.init_board()
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.get_action(self.board,
                                                 temp=temp,
                                                 return_prob=1)
            # store the data
            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            current_players.append(self.board.current_player)
            # perform a move
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, p1, p2)
            end, winner = self.board.game_end()
            if end:
                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is player:", winner)
                    else:
                        print("Game end. Tie")
                return winner, zip(states, mcts_probs, winners_z)