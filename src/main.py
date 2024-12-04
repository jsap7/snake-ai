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
                    
                snake_positions = state['snake_positions']
                food_position = state['food_position']
                grid_bounds = state['grid_bounds']
                
                # Convert positions to grid coordinates if needed
                snake_grid = [controller.convert_to_grid_coordinates(pos, grid_bounds) for pos in snake_positions]
                food_grid = controller.convert_to_grid_coordinates(food_position, grid_bounds)
                
                # Get optimal path
                path = pathfinder.find_path(snake_grid, food_grid)
                if path and len(path) >= 2:
                    next_pos = path[1]
                    
                    # Validate next position
                    if pathfinder.is_valid_position(next_pos, snake_grid):
                        direction = controller.get_next_move(snake_grid[0], next_pos)
                        if direction:
                            logging.info(f"Moving {direction} from {snake_grid[0]} to {next_pos}")
                            controller.make_move(direction)
                        else:
                            logging.error(f"Invalid direction for movement to {next_pos}")
                    else:
                        logging.error(f"Next position {next_pos} is invalid")
                else:
                    logging.warning("No valid path found")
                
                # Add slightly longer delay to ensure movement is registered
                time.sleep(0.15)
                
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