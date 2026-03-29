"""
models/asm_model.py
Data model for an ASM (Algorithmic State Machine) chart.
Full implementation in Milestone 4/5.
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BlockType(Enum):
    STATE    = "state"
    OUTPUT   = "output"
    DIAMOND  = "diamond"
    HEXAGON  = "hexagon"


@dataclass
class ASMBlock:
    block_id:   str
    block_type: BlockType
    label:      str = ""
    x:          float = 0.0
    y:          float = 0.0
    # Extra data per type (e.g. condition vars, output assignments)
    data:       dict = field(default_factory=dict)


@dataclass
class ASMConnection:
    conn_id:   str
    from_id:   str          # source block id
    from_port: str          # port label (e.g. "Y", "N", "00", "01" …)
    to_id:     str          # destination block id


class ASMModel:
    """
    Holds all blocks and connections of one ASM chart.
    Milestone 4 will populate this from QGraphicsScene items.
    Milestone 5 will validate and generate VHDL from it.
    """

    def __init__(self):
        self._blocks:      dict[str, ASMBlock]      = {}
        self._connections: dict[str, ASMConnection] = {}
        self._initial_state: Optional[str]          = None

    def add_block(self, block: ASMBlock):
        self._blocks[block.block_id] = block

    def remove_block(self, block_id: str):
        self._blocks.pop(block_id, None)
        # Remove dangling connections
        dangling = [
            cid for cid, c in self._connections.items()
            if c.from_id == block_id or c.to_id == block_id
        ]
        for cid in dangling:
            del self._connections[cid]

    def add_connection(self, conn: ASMConnection):
        self._connections[conn.conn_id] = conn

    def remove_connection(self, conn_id: str):
        self._connections.pop(conn_id, None)

    def blocks(self) -> list[ASMBlock]:
        return list(self._blocks.values())

    def connections(self) -> list[ASMConnection]:
        return list(self._connections.values())

    def state_blocks(self) -> list[ASMBlock]:
        return [b for b in self._blocks.values() if b.block_type == BlockType.STATE]
