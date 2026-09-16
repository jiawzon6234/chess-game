"""完整規則邏輯：攻擊格判斷、將軍/將死/逼和、合法走法過濾、套用走法到棋盤。

這一層把 pieces.py 產生的「虛擬合法走法」，過濾成真正合法(不會讓自己國王被將軍)
的走法，並且負責處理易位、吃過路兵、兵升變等特殊規則的「棋盤狀態更新」。
"""

from .moves import Move
from .pieces import Color, Piece, PieceType


def is_square_attacked(board, pos: tuple, by_color: Color) -> bool:
    """判斷 pos 這一格是否被 by_color 一方的任何棋子攻擊。"""
    for piece_pos, piece in board.all_pieces(by_color):
        if piece.type is PieceType.PAWN:
            # 兵的攻擊格是斜前方，即使該格是空的也算被攻擊
            # (這對於判斷國王是否可以走過去、以及易位規則很重要)。
            row, col = piece_pos
            direction = -1 if piece.color is Color.WHITE else 1
            if (row + direction, col - 1) == pos or (row + direction, col + 1) == pos:
                return True
        else:
            for move in piece.pseudo_legal_moves(piece_pos, board):
                if move.to_pos == pos:
                    return True
    return False


def is_in_check(board, color: Color) -> bool:
    king_pos = board.find_king(color)
    if king_pos is None:
        return False
    return is_square_attacked(board, king_pos, color.opposite)


def _castling_moves(board, color: Color) -> list:
    moves = []
    row = 7 if color is Color.WHITE else 0
    king_pos = (row, 4)
    king = board.get_piece(king_pos)
    if king is None or king.type is not PieceType.KING or king.has_moved:
        return moves
    if is_in_check(board, color):
        return moves

    rights = board.castling_rights[color]
    opponent = color.opposite

    if rights["kingside"]:
        rook = board.get_piece((row, 7))
        if (
            rook is not None
            and rook.type is PieceType.ROOK
            and not rook.has_moved
            and board.is_empty((row, 5))
            and board.is_empty((row, 6))
            and not is_square_attacked(board, (row, 5), opponent)
            and not is_square_attacked(board, (row, 6), opponent)
        ):
            moves.append(Move(king_pos, (row, 6), king, is_castling=True))

    if rights["queenside"]:
        rook = board.get_piece((row, 0))
        if (
            rook is not None
            and rook.type is PieceType.ROOK
            and not rook.has_moved
            and board.is_empty((row, 1))
            and board.is_empty((row, 2))
            and board.is_empty((row, 3))
            and not is_square_attacked(board, (row, 2), opponent)
            and not is_square_attacked(board, (row, 3), opponent)
        ):
            moves.append(Move(king_pos, (row, 2), king, is_castling=True))

    return moves


def generate_pseudo_legal_moves(board, color: Color) -> list:
    moves = []
    for pos, piece in board.all_pieces(color):
        moves.extend(piece.pseudo_legal_moves(pos, board))
    moves.extend(_castling_moves(board, color))
    return moves


def _rebind_move(trial_board, move: Move) -> Move:
    """board.clone() 會深層複製所有棋子物件，因此需要在複製後的棋盤上
    重新取得對應位置的棋子物件，才能正確套用走法。"""
    piece = trial_board.get_piece(move.from_pos)
    return Move(
        move.from_pos,
        move.to_pos,
        piece,
        captured_piece=trial_board.get_piece(move.to_pos),
        promotion=move.promotion,
        is_castling=move.is_castling,
        is_en_passant=move.is_en_passant,
        is_double_pawn_push=move.is_double_pawn_push,
    )


def generate_legal_moves(board, color: Color) -> list:
    """回傳真正合法的走法：走完之後自己的國王不會被將軍。"""
    legal_moves = []
    for move in generate_pseudo_legal_moves(board, color):
        trial_board = board.clone()
        apply_move(trial_board, _rebind_move(trial_board, move))
        if not is_in_check(trial_board, color):
            legal_moves.append(move)
    return legal_moves


def _update_castling_rights(board, move: Move) -> None:
    for color in (Color.WHITE, Color.BLACK):
        home_row = 7 if color is Color.WHITE else 0
        king_start = (home_row, 4)
        kingside_rook_start = (home_row, 7)
        queenside_rook_start = (home_row, 0)

        if move.from_pos == king_start and move.piece.type is PieceType.KING:
            board.castling_rights[color]["kingside"] = False
            board.castling_rights[color]["queenside"] = False
        if move.from_pos == kingside_rook_start or move.to_pos == kingside_rook_start:
            board.castling_rights[color]["kingside"] = False
        if move.from_pos == queenside_rook_start or move.to_pos == queenside_rook_start:
            board.castling_rights[color]["queenside"] = False


def apply_move(board, move: Move) -> None:
    """將 move 套用到 board 上(就地修改)，並更新易位權、吃過路兵目標格與回合。"""
    piece = move.piece
    board.set_piece(move.from_pos, None)

    if move.is_en_passant:
        captured_pawn_pos = (move.from_pos[0], move.to_pos[1])
        board.set_piece(captured_pawn_pos, None)

    piece.has_moved = True

    if move.promotion is not None:
        promoted_piece = Piece(piece.color, move.promotion, has_moved=True)
        board.set_piece(move.to_pos, promoted_piece)
    else:
        board.set_piece(move.to_pos, piece)

    if move.is_castling:
        row = move.from_pos[0]
        if move.to_pos[1] == 6:  # 王翼易位
            rook = board.get_piece((row, 7))
            board.set_piece((row, 7), None)
            board.set_piece((row, 5), rook)
            if rook is not None:
                rook.has_moved = True
        else:  # 后翼易位
            rook = board.get_piece((row, 0))
            board.set_piece((row, 0), None)
            board.set_piece((row, 3), rook)
            if rook is not None:
                rook.has_moved = True

    _update_castling_rights(board, move)

    if move.is_double_pawn_push:
        mid_row = (move.from_pos[0] + move.to_pos[0]) // 2
        board.en_passant_target = (mid_row, move.from_pos[1])
    else:
        board.en_passant_target = None

    if piece.color is Color.BLACK:
        board.fullmove_number += 1
    if move.piece.type is PieceType.PAWN or move.captured_piece is not None:
        board.halfmove_clock = 0
    else:
        board.halfmove_clock += 1

    board.turn = board.turn.opposite


def is_checkmate(board, color: Color) -> bool:
    return is_in_check(board, color) and len(generate_legal_moves(board, color)) == 0


def is_stalemate(board, color: Color) -> bool:
    return not is_in_check(board, color) and len(generate_legal_moves(board, color)) == 0
