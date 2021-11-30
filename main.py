import sys
# import sqlite3

from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QLabel, QRadioButton, QButtonGroup
from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap
from PyQt5.QtCore import Qt

WHITE = 1
BLACK = 2


FIGURE_TO_CHAR = {
    'Queen': 'Q',
    'Bishop': 'B',
    'Knight': 'N',
    'Rook': 'R'
}
IMAGE_FOR_FIGURES = {}
for row, color in enumerate(['W', 'B']):
    for col, char in enumerate(['K', 'Q', 'B', 'N', 'R', 'P']):
        if '/' in __file__:
            path = '/'.join(__file__.split('/')[:-1]) + '/'
        else:
            path = '\\'.join(__file__.split('\\')[:-1]) + '\\'
        img = Image.open(path + 'Chess_Pieces_Sprite.png').convert('RGBA')
        img = img.crop([200 * col, 200 * row, 200 * (col + 1), 200 * (row + 1)])
        img = img.resize([60, 60])
        IMAGE_FOR_FIGURES[color + char] = ImageQt(img)



def correct_coords(row, col):
    '''Проверка координат на корректность'''
    return 0 <= row < 8 and 0 <= col < 8


def opponent(color):
    if color == WHITE:
        return BLACK
    return WHITE


def checkmate(board, color):
    i, j, row, col = 0, 0, 0, 0
    for i in range(8):
        for j in range(8):
            if isinstance(board.field[i][j], King) and board.field[i][j].color == color:
                row, col = i, j

    if not isinstance(board.field[row][col], King):
        return True
    if board.field[row][col].color == opponent(color):
        return False

    if not board.is_under_attack(row, col, opponent(color)):
        return False
    for i in range(-1, 2):
        for j in range(-1, 2):
            if board.field[row][col].can_move(board, row, col, row + i, col + j):
                if not board.is_under_attack(row + i, col + j, opponent(color)):
                    return False
    for row1 in range(8):
        for col1 in range(8):
            if board.field[row1][col1] and board.field[row1][col1].color == color:
                for i in range(8):
                    for j in range(8):
                        if board.field[row1][col1].can_move(board, row1, col1, i, j) and \
                           not board.is_under_attack(row, col, opponent(color)):
                            return False
    for row1 in range(8):
        for col1 in range(8):
            if board.field[row1][col1] and board.field[row1][col1].color == opponent(color) and board.field[row1][col1].can_move(board, row1, col1, row, col):
                for i in range(8):
                    for j in range(8):
                        if board.field[i][j] and board.field[i][j].color == color and board.field[i][j].can_move(board, i, j, row1, col1):
                            return False
    return True


class Board:
    def __init__(self):
        self.color = WHITE
        self.field = []
        for _ in range(8):
            self.field.append([None] * 8)

    def copy(self):
        board = Board()
        for i, arr in enumerate(self.field):
            for j, fig in i:
                board.field[i][j] = self.field[i][j]
        return board

    def current_player_color(self):
        return self.color

    def cell(self, row, col):
        '''Возвращает координаты фигуры в виде строки из 2 символов, либо 2 пробела'''
        piece = self.field[row][col]
        if piece is None:
            return '  '
        c = 'w' if piece.get_color() == WHITE else 'b'
        return c + piece.char()

    def get_piece(self, r, c):
        return self.field[r][c]

    def can_move_piece(self, row, col, row1, col1):
        if not correct_coords(row, col) or not correct_coords(row1, col1):
            return False
        if row == row1 and col == col1:
            return False  # нельзя пойти в ту же клетку
        piece = self.field[row][col]
        if piece is None:
            return False
        if piece.get_color() != self.color:
            return False
        if not piece.can_move(self, row, col, row1, col1):
            return False
        return True

    def move_piece(self, row, col, row1, col1):
        if self.can_move_piece(row, col, row1, col1):
            piece = self.field[row][col]
            piece.move = True
            self.field[row][col] = None  # Снять фигуру.
            self.field[row1][col1] = piece  # Поставить на новое место.
            self.color = opponent(self.color)
            return True
        return False

    def move_and_promote_pawn(self, row, col, row1, col1, char):
        if not correct_coords(row, col) or not correct_coords(row1, col1):
            return False
        if row == row1 and col == col1:
            return False  # нельзя пойти в ту же клетку
        if row1 != 0 and row1 != 7:
            return False
        piece = self.field[row][col]
        if not isinstance(piece, Pawn):
            return False
        if piece.get_color() != self.color:
            return False
        if not piece.can_move(self, row, col, row1, col1):
            return False

        self.field[row][col] = None  # Снять фигуру.
        self.field[row1][col1] = Rook(self.color) if char == 'R' else \
            Bishop(self.color) if char == 'B' else Knight(self.color) if char == 'N' else \
            Queen(self.color)
        self.color = opponent(self.color)
        return True

    def is_under_attack(self, row, col, color):
        for r in range(8):
            for c in range(8):
                fig = self.field[r][c]
                if fig is None:
                    continue
                if fig.can_move(self, r, c, row, col) and fig.get_color() == color:
                    return True
        return False

    def can_castling0(self):
        a = 0 if self.color == WHITE else 7
        if isinstance(self.field[a][0], Rook) and not self.field[a][0].move and \
           isinstance(self.field[a][4], King) and not self.field[a][4].move and \
           self.field[a][1] == self.field[a][2] == self.field[a][3] is None:
            return True
        return False

    def castling0(self):
        a = 0 if self.color == WHITE else 7
        if self.can_castling0():
            self.field[a][0], self.field[a][3] = None, self.field[a][0]
            self.field[a][2], self.field[a][4] = self.field[a][4], None
            self.color = opponent(self.color)

    def can_castling7(self):
        a = 0 if self.color == WHITE else 7
        if isinstance(self.field[a][7], Rook) and not self.field[a][7].move and \
           isinstance(self.field[a][4], King) and not self.field[a][4].move and \
           self.field[a][5] == self.field[a][6] is None:
            return True
        return False

    def castling7(self):
        a = 0 if self.color == WHITE else 7
        if self.can_castling7():
            self.field[a][7], self.field[a][5] = None, self.field[a][7]
            self.field[a][6], self.field[a][4] = self.field[a][4], None
            self.color = opponent(self.color)


####################################################


class BasicFigure:
    def __init__(self, color):
        self.color = color
        self.move = False

    def __str__(self):
        return self.str_color() + self.char()

    def str_color(self):
        return 'W' if self.color == WHITE else 'B'

    def char(self):
        return '-'
 
    def get_color(self):
        return self.color


class Pawn(BasicFigure):  # Пешка
    def char(self):
        return 'P'
 
    def can_move(self, board, r0, c0, row, col):
        if not (0 <= row <= 7 and 0 <= col <= 7) or (r0 == row and c0 == col):
            return False
 
        if self.color == WHITE:
            direction = 1
            start_row = 1
        else:
            direction = -1
            start_row = 6

        if c0 - col == 0:
            # ход на 1 клетку
            if r0 + direction == row and board.field[row][col] is None:
                return True
    
            # ход на 2 клетки из начального положения
            if r0 == start_row and r0 + 2 * direction == row and\
               board.field[row][col] is None and board.field[r0 + direction][c0] is None:
                return True
        elif abs(c0 - col) == 1:
            if r0 + direction == row and\
               board.field[row][col] is not None and\
               board.field[row][col].color == opponent(self.color):
                return True
 
        return False


class Knight(BasicFigure):  # Конь
    def char(self):
        return 'N'

    def can_move(self, board, r0, c0, row, col):
        if not (0 <= row <= 7 and 0 <= col <= 7) or (r0 == row and c0 == col):
            return False
        if (abs(c0 - col) == 1 and abs(r0 - row) == 2) or \
           (abs(c0 - col) == 2 and abs(r0 - row) == 1):
            if board.field[row][col] is None or board.field[row][col].color == opponent(self.color):
                return True
        return False


class Rook(BasicFigure):  # Ладья
    def char(self):
        return 'R'

    def can_move(self, board, r0, c0, row, col):
        if not (0 <= row <= 7 and 0 <= col <= 7) or (r0 == row and c0 == col):
            return False
        if (r0 != row and c0 != col):
            return False

        r1, c1 = r0, c0
        f = True
        dr = 1 if r0 < row else -1 if r0 > row else 0
        dc = 1 if c0 < col else -1 if c0 > col else 0
        while abs(row - r1) > 1 or abs(col - c1) > 1:
            r1 += dr
            c1 += dc

            if board.field[r1][c1] is not None:
                f = False
                break

        if f:
            if board.field[row][col] is None or \
               board.field[row][col].color == opponent(self.color):
                return True
        return False


class Bishop(BasicFigure):  # Слон
    def char(self):
        return 'B'

    def can_move(self, board, r0, c0, row, col):
        if not (0 <= row <= 7 and 0 <= col <= 7) or (r0 == row and c0 == col):
            return False
        if abs(r0 - row) != abs(c0 - col):
            return False
        
        r1, c1 = r0, c0
        f = True
        dr = 1 if r0 < row else -1 if r0 > row else 0
        dc = 1 if c0 < col else -1 if c0 > col else 0
        while abs(row - r1) > 1 and abs(col - c1) > 1:
            r1 += dr
            c1 += dc

            if board.field[r1][c1] is not None:
                f = False

        if f:
            if board.field[row][col] is None or \
               board.field[row][col].color == opponent(self.color):
                return True
        return False


class Queen(BasicFigure):  # Ферзь
    def char(self):
        return 'Q'

    def can_move(self, board, r0, c0, row, col):
        if Rook(self.color).can_move(board, r0, c0, row, col) or\
           Bishop(self.color).can_move(board, r0, c0, row, col):
            return True
        else:
            return False


class King(BasicFigure):  # Король
    def char(self):
        return 'K'

    def can_move(self, board, r0, c0, row, col):
        if not (0 <= row <= 7 and 0 <= col <= 7) or (r0 == row and c0 == col):
            return False
        if abs(r0 - row) > 1 or abs(c0 - col) > 1:
            return False
        if board.field[row][col] is None or \
           board.field[row][col].color == opponent(self.color):
            return True
        return False


####################################################


board = Board()
for c in range(8):
    board.field[1][c] = Pawn(WHITE)
    board.field[6][c] = Pawn(BLACK)
for r in [0, 7]:
    c0 = WHITE if r == 0 else BLACK
    for c in [0, 7]:
        board.field[r][c] = Rook(c0)
    for c in [1, 6]:
        board.field[r][c] = Knight(c0)
    for c in [2, 5]:
        board.field[r][c] = Bishop(c0)
    board.field[r][3] = Queen(c0)
    board.field[r][4] = King(c0)


class Chess(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.f = True
        self.char = 'Q'
        self.resetData()

        self.update()

    def initUI(self):
        self.setWindowTitle('Шахматы')
        self.setGeometry(300, 300, 700, 700)
        self.setMouseTracking(True)

        for i in range(8):
            label = QLabel(str(i), self)
            label.move(60 * (i + 1) + 15, -5)
            label.setFont(QFont('Segoe', 35))

            label = QLabel(str(i), self)
            label.move(10, 60 * (i + 1))
            label.setFont(QFont('Segoe', 35))
        
        self.situation = QLabel('Ход белых', self)
        self.situation.setGeometry(60, 540, 500, 50)

        self.buttonGroup = QButtonGroup(self)
        for i, figure in enumerate(FIGURE_TO_CHAR):
            button = QRadioButton(figure, self)
            button.move(550, 60 + 25 * i)
            self.buttonGroup.addButton(button)
        self.buttonGroup.buttonClicked.connect(self.check)
        self.buttonGroup.buttons()[0].setChecked(True)

    def resetData(self):
        self.need_to_redraw = []
        self.must_draw = []
        self.move_from = []
        self.move_to = []

    def move(self):
        if checkmate(board, board.color):
            a = 'Чёрные' if board.color == WHITE else 'Белые'
            self.setWindowTitle(f'Шахматы, {a} победили!')
            self.update()
            self.f = False
        elif self.f:
            # if '/' in __file__:
                # path = '/'.join(__file__.split('/')[:-1]) + '/'
            # else:
                # path = '\\'.join(__file__.split('\\')[:-1]) + '\\'
            # con = sqlite3.connect(path + 'chess_moves.db')
            # cur = con.cursor()
            s = 'INSERT INTO moves (type, move_from, move_to)\nVALUES ('
            lis = []

            if board.current_player_color() == WHITE:
                text = 'Ход белых'
            else:
                text = 'Ход чёрных'
            # self.situation.setText(text)

            if self.move_from == [] or self.move_to == []:
                return self.situation.setText(f'{text}\nНужно выбрать откуда сходить')
            row, col, row1, col1 = self.move_from[0], self.move_from[1],\
                                    self.move_to[0], self.move_to[1]
            char = self.char

            if isinstance(board.field[row][col], King):
                if board.is_under_attack(row, col, opponent(board.color)):
                    self.situation.setText(f'{text}\nКороля на этой клетке будут атаковать. Попробуйте другой ход!')
                else:
                    if board.move_piece(row, col, row1, col1):
                        self.situation.setText('Ход белых' if text == 'Ход чёрных' else 'Ход чёрных')
                        lis = ['"move"', f'{row}{col}', f'{row1}{col1}']
                    elif self.move_to[1] == 0 and board.can_castling0():
                        board.castling0()
                        lis = ['"castling"', f'{row}{col}', f'{row1}{col1}']
                    elif self.move_to[1] == 7 and board.can_castling7():
                        board.castling7()
                        lis = ['"castling"', f'"{row}{col}"', f'"{row1}{col1}"']
                    else:
                        self.situation.setText(f'{text}\nКоординаты некорректы! Попробуйте другой ход!')
            else:
                if board.move_and_promote_pawn(row, col, row1, col1, char) \
                or board.move_piece(row, col, row1, col1):
                    self.situation.setText('Ход белых' if text == 'Ход чёрных' else 'Ход чёрных')
                    lis = ['"move"', f'{row}{col}', f'{row1}{col1}']
                else:
                    self.situation.setText(f'{text}\nКоординаты некорректы! Попробуйте другой ход!')
            # if lis:
                # cur.execute(s + ', '.join(lis) + ')')
                # con.commit()
            # con.close()
            self.resetData()
            self.update()
        if checkmate(board, board.color):
            a = 'Чёрные' if board.color == WHITE else 'Белые'
            self.setWindowTitle(f'Шахматы, {a} победили!')
            self.update()
            self.f = False

    def check(self, button):
        self.char = button.text()

    def paintEvent(self, PaintEvent):
        qp = QPainter()
        qp.begin(self)
        qp.fillRect(60, 60, 480, 480, QColor(255, 255, 255))
        qp.setPen(QColor(0, 0, 0))
        for i in range(9):
            qp.drawLine(60 * (i + 1), 60, 60 * (i + 1), 540)
            qp.drawLine(60, 60 * (i + 1), 540, 60 * (i + 1))
        for i in self.need_to_redraw:
            qp.fillRect(*i)
        if isinstance(self.must_draw, list):
            for i in self.must_draw:
                qp.fillRect(*i)

        for row, i in enumerate(board.field):
            for col, figure in enumerate(i):
                if not figure is None:
                    img = IMAGE_FOR_FIGURES[str(figure)]
                    pixmap = QPixmap.fromImage(img)
                    qp.drawPixmap(60 * (col + 1), 60 * (row + 1), pixmap)
        qp.end()

    def mouseMoveEvent(self, event):
        if 60 <= event.x() < 540 and 60 <= event.y() < 540 and self.f:
            x, y = event.x() // 60 * 60, event.y() // 60 * 60
            self.need_to_redraw = [[x + 1, y + 1, 59, 59, QColor(255, 255, 0)]]
            self.update()

    def mousePressEvent(self, event):
        if not (60 <= event.x() < 540 and 60 <= event.y() < 540 and self.f):
            return

        x, y = event.x() // 60, event.y() // 60
        row, col = y - 1, x - 1
        if event.button() == Qt.RightButton:
            if board.field[row][col] is None or board.field[row][col].color != board.color:
                return
            self.move_from = [row, col]
            self.must_draw = [[60 * x + 1, 60 * y + 1, 59, 59, QColor(255, 0, 255)]]
            for i in range(8):
                for j in range(8):
                    if board.can_move_piece(row, col, i, j):
                        self.must_draw.append([60 * (j + 1) + 1, 60 * (i + 1) + 1, 59, 59, QColor(0, 255, 0)])
            if isinstance(board.field[row][col], King):
                if board.color == BLACK:
                    if board.can_castling0():
                        self.must_draw.append([61, 481, 59, 59, QColor(0, 255, 255)])
                    elif board.can_castling7():
                        self.must_draw.append([481, 481, 59, 59, QColor(0, 255, 255)])
                else:
                    if board.can_castling0():
                        self.must_draw.append([61, 61, 59, 59, QColor(0, 255, 255)])
                    elif board.can_castling7():
                        self.must_draw.append([481, 61, 59, 59, QColor(0, 255, 255)])
            self.update()

        elif event.button() == Qt.LeftButton:
            self.move_to = [row, col]
            self.move()


app = QApplication(sys.argv)
game = Chess()
game.show()
sys.exit(app.exec())