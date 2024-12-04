import logging
import time
from game.browser import GameController
from game.pathfinding import PathFinder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def play_game():
    controller = GameController()
    pathfinder = PathFinder()
    
    try:
        # Initialize game
        if not controller.initialize():
            logging.error("Failed to initialize game")
            return
        
        game_count = 0
        max_games = 10  # Limit number of games for testing
        
        while game_count < max_games:
            logging.info(f"Starting game {game_count + 1}")
            
            # Start new game
            if not controller.start_game():
                logging.error("Failed to start game")
                break
            
            moves_without_food = 0
            max_moves_without_food = 100  # Safety limit
            last_score = 0
            
            # Single game loop
            while True:
                # Get current game state
                game_state = controller.get_game_state()
                
                # Check for game over or invalid state
                if game_state is None:
                    logging.error("Failed to get game state")
                    break
                    
                if game_state.get('game_over', False):
                    logging.info("Game over detected")
                    break
                
                # Convert positions to grid coordinates
                grid_bounds = game_state.get('grid_bounds')
                snake_positions = game_state.get('snake_positions', [])
                food_position = game_state.get('food_position')
                
                if not grid_bounds or not snake_positions or not food_position:
                    logging.warning("Missing essential game state components")
                    continue
                
                # Convert pixel coordinates to grid coordinates
                snake_grid_positions = [
                    controller.convert_to_grid_coordinates(pos, grid_bounds)
                    for pos in snake_positions
                ]
                food_grid_pos = controller.convert_to_grid_coordinates(
                    food_position, grid_bounds
                )
                
                logging.info(f"Snake head at {snake_grid_positions[0]}, food at {food_grid_pos}")
                
                # Find path to food
                path = pathfinder.find_path(snake_grid_positions, food_grid_pos)
                
                if not path:
                    logging.warning("No path found")
                    # Try to make a safe move
                    safe_neighbors = pathfinder.get_neighbors(snake_grid_positions[0], snake_grid_positions[1:])
                    if safe_neighbors:
                        next_pos = safe_neighbors[0]
                        direction = controller.get_next_move(snake_grid_positions[0], next_pos)
                        if direction:
                            controller.make_move(direction)
                            time.sleep(0.1)
                    else:
                        logging.error("No safe moves available")
                        break
                    continue
                
                # Execute next move from path
                if len(path) >= 2:
                    current_pos = path[0]
                    next_pos = path[1]
                    direction = controller.get_next_move(current_pos, next_pos)
                    
                    if direction:
                        logging.info(f"Moving {direction} from {current_pos} to {next_pos}")
                        controller.make_move(direction)
                        time.sleep(0.1)  # Small delay between moves
                    else:
                        logging.warning("Could not determine direction")
                else:
                    logging.warning("Path too short")
                    continue
                
                # Track progress
                current_score = game_state.get('score', 0)
                if current_score > last_score:
                    moves_without_food = 0
                    last_score = current_score
                    logging.info(f"Score increased to {current_score}")
                else:
                    moves_without_food += 1
                
                # Check for potential infinite loop
                if moves_without_food > max_moves_without_food:
                    logging.warning("Possible infinite loop detected")
                    break
            
            # Wait before starting next game
            time.sleep(2)
            game_count += 1
            
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.close()

if __name__ == "__main__":
    play_game() 