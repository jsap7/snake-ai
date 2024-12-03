from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class GameState:
    grid_size: Tuple[int, int]
    snake_position: List[Tuple[int, int]]
    food_position: Tuple[int, int]
    score: int
    game_over: bool

class StateDetector:
    def __init__(self):
        """Initialize the state detector"""
        pass
    
    def process_screen(self, screenshot) -> GameState:
        """Process a screenshot and return the game state"""
        pass 