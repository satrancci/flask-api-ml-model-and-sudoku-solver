from collections import defaultdict

######## Util functions

def validate_input(s):
    if len(s) != 81:
        return False
    valid = '0123456789.'
    return all(char in valid for char in s)

def preprocess_sudoku(s): # s is a string of length 81; 0 stands for empty cell
    digits = list(map(lambda x: '.' if x == '0' else x, s))
    matrix = [digits[i:i+9] for i in range(0,len(digits),9)]
    return matrix

def postprocess_sudoku(matrix): # once solved, convert the board back into a string of length 81
    return ''.join([matrix[i][j] for i in range(9) for j in range(9)])




#########################################################

class Sudoku:

    BOARD_SIZE = 9

    def __init__(self, matrix):
        self._matrix = matrix
    
    def is_valid_position(self):
        rows = {i: defaultdict(int) for i in range(self.BOARD_SIZE)}
        columns = {i: defaultdict(int) for i in range(self.BOARD_SIZE)}
        submatrices = {i: defaultdict(int) for i in range(self.BOARD_SIZE)}

        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                num = self._matrix[i][j]
                if num != '.':
                    num = int(num)
                    submatrix_idx = (i//3) * 3 + j // 3
                    if rows[i][num] > 0 or columns[j][num] > 0 or submatrices[submatrix_idx][num] > 0:
                        return False
                    rows[i][num] = 1
                    columns[j][num] = 1
                    submatrices[submatrix_idx][num] = 1
        return True

    def is_valid_placement(self, x, y, num):
        for i in range(self.BOARD_SIZE):
            if self._matrix[x][i] == num or self._matrix[i][y] == num or self._matrix[3*(x//3)+i//3][3*(y//3)+i%3] == num:
                return False
        return True

    def solve(self):
        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                if self._matrix[i][j] == '.': # if a cell is empty,
                    for num in range (1,10): # try every number
                        if self.is_valid_placement(i,j,str(num)): # if we can place the current number,
                            self._matrix[i][j] = str(num) # we place it
                            if self.solve(): # if we can solve the problem recursively,
                                return True # then we are done
                            self._matrix[i][j] = '.' # otherwise, we set the current cell to empty (backtrack)
                        if num == 9: # if we tried all numbers for this cell and still didn't solve it,
                            return False # then there is no solution and we need to backtrack to make changes in earlier cells
        return False if any(self._matrix[i][j] == '.' for i in range(self.BOARD_SIZE) for j in range(self.BOARD_SIZE)) else True #return True if we are out of boundaries which means that we placed numbers on all cells and that the configuration is legal