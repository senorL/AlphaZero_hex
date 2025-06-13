import tkinter as tk
from game import Board, Game
from mcts_pure import MCTSPlayer as MCTS_Pure
import math 

BOARD_SIZE = 5  # 可改为 4、5、6、7、8、9、11 等

class HexGUI:
    def __init__(self, board_size=BOARD_SIZE):
        self.board_size = board_size
        self.board = Board(width=board_size, height=board_size)
        self.game = Game(self.board)
        self.ai = MCTS_Pure(c_puct=5, n_playout=800)
        self.window = tk.Tk()
        self.window.title("Hex 海克斯棋")
        self.cell = 50
        self.margin = 40
        self.canvas = tk.Canvas(self.window, width=self.margin*2+self.cell*board_size*1.2,
                                height=self.margin*2+self.cell*board_size*1.2, bg="#f8f8f8")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)
        self.reset_btn = tk.Button(self.window, text="重开", command=self.reset)
        self.reset_btn.pack()
        self.status = tk.Label(self.window, text="红棋(1)先手，点击棋盘落子")
        self.status.pack()
        self.reset()
        self.window.mainloop()

    def reset(self):
        self.board.init_board(0)
        self.current_player = 2
        self.draw_board()
        ai_move = self.ai.get_action(self.board)  # AI makes the first move
        self.board.do_move(ai_move)
        self.draw_board()
        self.status.config(text="请点击棋盘落子")

    def draw_board(self):
        self.canvas.delete("all")
        n = self.board_size
        for h in range(n):
            for w in range(n):
                x, y = self.hex_center(h, w)
                self.draw_hex(x, y)
                move = self.board.location_to_move((h, w))
                p = self.board.states.get(move, 0)
                if p == 1:
                    self.canvas.create_oval(x-15, y-15, x+15, y+15, fill="red")
                elif p == 2:
                    self.canvas.create_oval(x-15, y-15, x+15, y+15, fill="blue")
        # 边界高亮
        for i in range(n):
            self.canvas.create_line(*self.hex_center(0, i), *self.hex_center(0, i), fill="red", width=4)
            self.canvas.create_line(*self.hex_center(n-1, i), *self.hex_center(n-1, i), fill="red", width=4)
            self.canvas.create_line(*self.hex_center(i, 0), *self.hex_center(i, 0), fill="blue", width=4)
            self.canvas.create_line(*self.hex_center(i, n-1), *self.hex_center(i, n-1), fill="blue", width=4)

    def hex_center(self, h, w):
        x = self.margin + w * self.cell * 1.1 + h * self.cell * 0.55
        y = self.margin + h * self.cell * 0.95
        return x, y

    def draw_hex(self, x, y):
        r = self.cell // 2
        points = []
        for i in range(6):
            angle = math.pi/3 * i + math.pi/6 # <--- 修改这里，使用 math.pi
            px = x + r * 1.05 * math.cos(angle) # <--- 修改这里，使用 math.cos
            py = y + r * 1.05 * math.sin(angle) # <--- 修改这里，使用 math.sin
            points.extend([px, py])
        self.canvas.create_polygon(points, outline="#888", fill="#fff", width=2)
    
    def click(self, event):
        if self.board.game_end()[0]:
            return
        pos = self.pixel_to_hex(event.x, event.y)
        if pos is None:
            return
        h, w = pos
        move = self.board.location_to_move((h, w))
        if move not in self.board.availables:
            return
        self.board.do_move(move)
        self.draw_board()
        if self.board.game_end()[0]:
            self.show_result()
            return
        # AI回合
        self.status.config(text="AI思考中...")
        self.window.update()
        ai_move = self.ai.get_action(self.board)
        self.board.do_move(ai_move)
        self.draw_board()
        if self.board.game_end()[0]:
            self.show_result()
        else:
            self.status.config(text="请点击棋盘落子")

    def pixel_to_hex(self, x, y):
        n = self.board_size
        for h in range(n):
            for w in range(n):
                cx, cy = self.hex_center(h, w)
                if (x-cx)**2 + (y-cy)**2 < (self.cell//2)**2:
                    return (h, w)
        return None

    def show_result(self):
        end, winner = self.board.game_end()
        if winner == 1:
            self.status.config(text="红棋(1)胜利！")
        elif winner == 2:
            self.status.config(text="蓝棋(2)胜利！")
        else:
            self.status.config(text="平局")

if __name__ == "__main__":
    HexGUI()