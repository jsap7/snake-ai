from ..game.state import GameState
from ..game.browser import GameController
from .pathfinder import PathFinder

class SnakeAgent:
    def __init__(self):
        self.game = GameController()
        self.pathfinder = PathFinder()
    
    def start(self):
        """Start the AI agent"""
        pass
    
    def make_move(self, state: GameState):
        """Decide and execute next move"""
        pass
    
    def run(self):
        """Main game loop"""
        pass 