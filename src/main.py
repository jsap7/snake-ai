import logging
import time
from game.browser import GameController
from game.pathfinding import PathFinder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def play_game():
    controller = GameController()
    pathfinder = PathFinder()
    
    try:
        if not controller.initialize():
            logging.error("Failed to initialize game")
            return
            
        logging.info("Starting game")
        
        if not controller.start_game():
            logging.error("Failed to start game")
            return
            
        time.sleep(1)  # Wait for game to start
        
        # Play just one game
        while True:
            try:
                state = controller.get_quick_state()
                if not state:
                    logging.error("Failed to get game state")
                    break
                    
                if state.get('game_over'):
                    logging.info("Game over detected")
                    break
                    
                snake_pos = state['snake_positions']
                food_pos = state['food_position']
                grid_bounds = state['grid_bounds']
                
                # Convert positions
                snake_grid = [controller.convert_to_grid_coordinates(pos, grid_bounds) for pos in snake_pos]
                food_grid = controller.convert_to_grid_coordinates(food_pos, grid_bounds)
                
                # Get path
                path = pathfinder.find_path(snake_grid, food_grid)
                if not path:
                    logging.error("No path found")
                    continue
                
                # Get direction
                if len(path) >= 2:
                    direction = controller.get_next_move(path[0], path[1])
                    if direction:
                        if not controller.make_move(direction):
                            logging.error("Failed to make move")
                    else:
                        logging.error("No valid direction found")
                
                time.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error in game loop: {e}")
                import traceback
                traceback.print_exc()
                break
            
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        controller.close()

if __name__ == "__main__":
    play_game() 