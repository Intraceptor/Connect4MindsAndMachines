import asyncio, websockets, random, copy, sys, time

BOARDHEIGHT = 6  # Width
BOARDWIDTH = 7 # Height

DEPTH = 4 # Increase to increase skill level

BLACK = 1 # Computer
RED = 2 # Opponent
EMPTY = 0
OPPONENT = 'opponent'
COMPUTER = 'computer'

async def gameloop (socket, created):
  active = True
  mainBoard = getNewBoard()
  first = int(input("First Player? [1 = Computer, 2 = Opponent] "))

  while active:
    message = (await socket.recv()).split(':')
    time.sleep(1)
    match message[0]:
      case 'GAMESTART' | 'OPPONENT':
        print(message)

        if first == 1:
            if len(message) > 1:
                colR = int(message[1])
                makeMove(mainBoard, RED, colR)

            colB = getComputerMove(mainBoard, first)
            makeMove(mainBoard, BLACK, colB)
            await socket.send(f'PLAY:{colB}')


        if first == 2 and len(message) > 1:
            colR = int(message[1])
            makeMove(mainBoard, RED, colR)

            colB = getComputerMove(mainBoard, first)
            makeMove(mainBoard, BLACK, colB)
            await socket.send(f'PLAY:{colB}')

        for i in mainBoard:
            print(i)
        print('')

      case 'WIN' | 'LOSS' | 'DRAW' | 'TERMINATED':
        print(message[0])

        active = False
async def create_game (server):
  async with websockets.connect(f'ws://{server}/create') as socket:
    await gameloop(socket, True)
async def join_game(server, id):
  async with websockets.connect(f'ws://{server}/join/{id}') as socket:
    await gameloop(socket, False)


def makeMove(board, player, column):
    lowest = getLowestEmptySpace(board, column)
    if lowest != -1:
        board[column][lowest] = player


def getNewBoard():
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY] * BOARDHEIGHT)
    return board


def getComputerMove(board, player):
    potentialMoves = getPotentialMoves(board, BLACK, DEPTH, player)
    print(potentialMoves)
    bestMoveFitness = -1
    for i in range(BOARDWIDTH):
        if potentialMoves[i] > bestMoveFitness and isValidMove(board, i):
            bestMoveFitness = potentialMoves[i]
    bestMoves = []
    for i in range(len(potentialMoves)):
        if potentialMoves[i] == bestMoveFitness and isValidMove(board, i):
            bestMoves.append(i)
    if bestMoves.count(3) > 0:
        return 3
    print(bestMoves)
    return random.choice(bestMoves)


def getPotentialMoves(board, tile, lookAhead, player):
    if lookAhead == 0:
        return [0] * BOARDWIDTH

    if tile == RED:
        enemyTile = BLACK
    else:
        enemyTile = RED

    potentialMoves = [0] * BOARDWIDTH
    for firstMove in range(BOARDWIDTH):
        dupeBoard = copy.deepcopy(board)
        if not isValidMove(dupeBoard, firstMove):
            continue
        makeMove(dupeBoard, tile, firstMove)
        if isWinner(dupeBoard, tile):
            potentialMoves[firstMove] = 1
            break
        else:
            if False:
                pass
            else:
                for counterMove in range(BOARDWIDTH):
                    dupeBoard2 = copy.deepcopy(dupeBoard)
                    if not isValidMove(dupeBoard2, counterMove):
                        continue
                    makeMove(dupeBoard2, enemyTile, counterMove)
                    if isWinner(dupeBoard2, enemyTile):
                        potentialMoves[firstMove] = -1
                        break
                    else:
                        results = getPotentialMoves(dupeBoard2, tile, lookAhead - 1, player)
                        potentialMoves[firstMove] += (sum(results) / BOARDWIDTH) / BOARDWIDTH
    if isValidMove(board, 3) is True and getLowestEmptySpace(board, 3) > 0:
        potentialMoves[3] += 0.19
    if isValidMove(board, 3) is True and 5 > getLowestEmptySpace(board, 2) > 2:
        potentialMoves[2] += 0.01
    if isValidMove(board, 3) is True and 5 > getLowestEmptySpace(board, 4) > 2:
        potentialMoves[4] += 0.01
    if isValidMove(board, 3) is True and getLowestEmptySpace(board, 1) % 2 == player % 2:
        potentialMoves[1] += 0.03
    if isValidMove(board, 3) is True and getLowestEmptySpace(board, 5) % 2 == player % 2:
        potentialMoves[5] += 0.03
    return potentialMoves


def getLowestEmptySpace(board, column):
    for y in range(BOARDHEIGHT-1, -1, -1):
        if board[column][y] == EMPTY:
            return y
    return -1


def isValidMove(board, column):
    if column < 0 or column >= (BOARDWIDTH) or board[column][0] != EMPTY:
        return False
    return True


def isWinner(board, tile):
    for x in range(BOARDWIDTH - 3):
        for y in range(BOARDHEIGHT):
            if board[x][y] == tile and board[x+1][y] == tile and board[x+2][y] == tile and board[x+3][y] == tile:
                return True
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 3):
            if board[x][y] == tile and board[x][y+1] == tile and board[x][y+2] == tile and board[x][y+3] == tile:
                return True
    for x in range(BOARDWIDTH - 3):
        for y in range(3, BOARDHEIGHT):
            if board[x][y] == tile and board[x+1][y-1] == tile and board[x+2][y-2] == tile and board[x+3][y-3] == tile:
                return True
    for x in range(BOARDWIDTH - 3):
        for y in range(BOARDHEIGHT - 3):
            if board[x][y] == tile and board[x+1][y+1] == tile and board[x+2][y+2] == tile and board[x+3][y+3] == tile:
                return True
    return False


if __name__ == '__main__':
    server = input('Server IP: ').strip()

    protocol = input('Join game or create game? (j/c): ').strip()

    match protocol:
        case 'c':
            asyncio.run(create_game(server))
        case 'j':
            id = input('Game ID: ').strip()

            asyncio.run(join_game(server, id))
        case _:
            print('Invalid protocol!')
