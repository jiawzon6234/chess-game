"""定義單一步棋的資料結構 (Move)。"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Move:
    """代表一次走棋的完整資訊。

    piece / captured_piece 使用 Any 型別註記，避免與 pieces.py 產生循環匯入；
    實際上它們是 pieces.Piece 的實例。
    """

    from_pos: tuple
    to_pos: tuple
    piece: Any
    captured_piece: Optional[Any] = None
    promotion: Optional[Any] = None  # PieceType，若此步為兵升變
    is_castling: bool = False
    is_en_passant: bool = False
    is_double_pawn_push: bool = False

    def to_algebraic(self) -> str:
        """回傳如 'e2e4'、'e7e8q' 的簡易走法記譜。"""
        from .board import Board  # 延遲匯入，避免循環匯入

        base = f"{Board.pos_to_square(self.from_pos)}{Board.pos_to_square(self.to_pos)}"
        if self.promotion is not None:
            base += self.promotion.value.lower()
        return base

    def __repr__(self) -> str:  # pragma: no cover - 純粹方便除錯顯示
        return self.to_algebraic()
