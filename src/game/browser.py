import cv2
import numpy as np
import logging
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class GameController:
    def __init__(self):
        """Initialize the game controller"""
        self.driver = None
        
    def initialize(self):
        """Initialize the browser and navigate to the game"""
        try:
            options = ChromeOptions()
            options.add_argument('--window-size=1200,800')
            self.driver = Chrome(options=options)
            self.driver.get('https://www.google.com/search?q=snake+game')
            return True
        except Exception as e:
            logging.error(f"Error initializing: {e}")
            return False
            
    def start_game(self):
        """Click play button to start the game"""
        try:
            # Look for first Play button
            logging.info("Looking for first Play button...")
            play_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.fxvhbc[role="button"]'))
            )
            logging.info("Found first Play button, clicking...")
            play_button.click()
            time.sleep(2)
            
            # Look for game Play button
            logging.info("Looking for game Play button...")
            play_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.FL0z2d[aria-label="Play"]'))
            )
            logging.info("Found game Play button, clicking...")
            play_button.click()
            time.sleep(2)  # Wait for game to fully load
            
            # Now capture and verify game bounds with grid
            logging.info("Capturing initial game bounds...")
            game_image = self.capture_game_area()
            if game_image is not None:
                # Draw numbered grid on the game area
                self.draw_debug_grid(game_image)
                logging.info("Saved numbered grid debug image")
                
            return True
            
        except Exception as e:
            logging.error(f"Error starting game: {e}")
            return False
            
    def capture_game_area(self):
        """Capture screenshot of game area"""
        try:
            logging.info("Taking screenshot...")
            screenshot = self.driver.get_screenshot_as_png()
            nparr = np.frombuffer(screenshot, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Find the actual game area (green play area)
            height, width = image.shape[:2]
            game_x = int(width * 0.253)  # Keep left position
            game_y = int(height * 0.156)  # Keep top position
            game_width = int(width * 0.496)  # Keep same width
            game_height = int(width * 0.438)  # 43.8% for 5 pixels less
            
            # Draw debug rectangle to verify game area bounds
            debug_image = image.copy()
            cv2.rectangle(debug_image, 
                         (game_x, game_y), 
                         (game_x + game_width, game_y + game_height),
                         (0, 0, 255), 2)  # Red rectangle
            cv2.imwrite('debug_game_bounds.png', debug_image)
            
            # Crop to game area
            game_area = image[game_y:game_y+game_height, game_x:game_x+game_width]
            
            logging.info(f"Game area bounds: ({game_x}, {game_y}) {game_width}x{game_height}")
            return game_area
            
        except Exception as e:
            logging.error(f"Error capturing game area: {e}")
            return None
            
    def find_game_grid(self, image):
        """Find the game grid boundaries"""
        try:
            height, width = image.shape[:2]
            
            # Grid dimensions are 17x15 - adjusted based on debug image
            grid_x = int(width * 0.10)  # Move more left (10% from left)
            grid_y = int(height * 0.16)  # Keep at 16% from top
            cell_size = int(width * 0.60) // 17  # Increase width to 60%
            grid_width = cell_size * 17
            grid_height = cell_size * 15
            
            # Debug logging
            logging.info(f"Image dimensions: {width}x{height}")
            logging.info(f"Grid start: ({grid_x}, {grid_y})")
            logging.info(f"Cell size: {cell_size}")
            logging.info(f"Grid size: {grid_width}x{grid_height}")
            
            # Draw debug rectangle to verify position
            debug_image = image.copy()
            cv2.rectangle(debug_image, 
                         (grid_x, grid_y), 
                         (grid_x + grid_width, grid_y + grid_height),
                         (0, 0, 255), 2)  # Red rectangle with thickness 2
            cv2.imwrite('debug_grid_bounds.png', debug_image)
            
            return ((grid_x, grid_y), (grid_width, grid_height))
            
        except Exception as e:
            logging.error(f"Error finding grid: {e}")
            return None
            
    def find_snake(self, image):
        """Find the snake in the image"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            snake_positions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 50:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        snake_positions.append((cx, cy))
                        logging.info(f"Found snake segment at ({cx}, {cy}) with area {area}")
            
            if not snake_positions:
                return None
                
            logging.info(f"Total snake segments found: {len(snake_positions)}")
            return snake_positions
            
        except Exception as e:
            logging.error(f"Error finding snake: {e}")
            return None
            
    def find_food(self, image):
        """Find the food in the image"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_red = np.array([0, 50, 50])
            upper_red = np.array([10, 255, 255])
            mask = cv2.inRange(hsv, lower_red, upper_red)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
                
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            logging.info(f"Food contour area: {area}")
            
            M = cv2.moments(largest_contour)
            if M["m00"] == 0:
                return None
                
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            logging.info(f"Found food at ({cx}, {cy})")
            return (cx, cy)
            
        except Exception as e:
            logging.error(f"Error finding food: {e}")
            return None
            
    def convert_to_grid_coordinates(self, pos, grid_bounds):
        """Convert screen coordinates to grid coordinates"""
        try:
            x, y = pos
            grid_x, grid_y = grid_bounds[0]
            grid_width, grid_height = grid_bounds[1]
            
            # Calculate cell size based on 17 columns
            cell_width = grid_width / 17
            cell_height = grid_height / 15
            
            # Calculate relative position
            rel_x = x - grid_x + (cell_width * 0.15)
            rel_y = y - grid_y + (cell_height * 0.15)
            
            # Convert to grid coordinates
            grid_col = int(rel_x / cell_width)
            grid_row = int(rel_y / cell_height)
            
            # Ensure coordinates are within bounds
            grid_col = max(0, min(grid_col, 16))  # 0-16 for 17 columns
            grid_row = max(0, min(grid_row, 14))  # 0-14 for 15 rows
            
            logging.info(f"Converting ({x}, {y}) to grid pos ({grid_col}, {grid_row})")
            return (grid_col, grid_row)
            
        except Exception as e:
            logging.error(f"Error converting coordinates: {e}")
            return None
            
    def get_next_move(self, current_pos, next_pos):
        """Determine direction to move based on current and next position"""
        try:
            current_x, current_y = current_pos
            next_x, next_y = next_pos
            
            dx = next_x - current_x
            dy = next_y - current_y
            
            logging.info(f"Current pos: {current_pos}, Next pos: {next_pos}")
            logging.info(f"Delta: dx={dx}, dy={dy}")
            
            if dx > 0:
                return 'right'
            elif dx < 0:
                return 'left'
            elif dy > 0:
                return 'down'
            elif dy < 0:
                return 'up'
            return None
            
        except Exception as e:
            logging.error(f"Error getting next move: {e}")
            return None
            
    def make_move(self, direction):
        """Make a move in the game"""
        try:
            key = None
            if direction == 'up':
                key = Keys.ARROW_UP
            elif direction == 'down':
                key = Keys.ARROW_DOWN
            elif direction == 'left':
                key = Keys.ARROW_LEFT
            elif direction == 'right':
                key = Keys.ARROW_RIGHT
                
            if key:
                logging.info(f"Sending {direction} command")
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(key)
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error making move: {e}")
            return False
            
    def check_death(self):
        """Check if the game is over"""
        try:
            # First check for play button
            try:
                play_button = self.driver.find_element(By.CSS_SELECTOR, 'div.FL0z2d[aria-label="Play"]')
                if play_button.is_displayed():
                    logging.info("Found play button - game over detected")
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking death: {e}")
            return False
            
    def get_quick_state(self):
        """Get the current game state quickly"""
        try:
            game_image = self.capture_game_area()
            if game_image is None:
                logging.error("Failed to capture game area")
                return None
            
            # Check for death first
            if self.check_death():
                logging.info("Death state detected")
                return {'game_over': True}
            
            # Get image dimensions for grid calculations
            height, width = game_image.shape[:2]
            grid_x = 0  # Since we've already cropped to game area
            grid_y = 0  # Since we've already cropped to game area
            grid_width = width
            grid_height = height
            
            # Calculate grid bounds in the format expected by convert_to_grid_coordinates
            grid_bounds = ((grid_x, grid_y), (grid_width, grid_height))
            
            # Find snake and food
            snake_positions = self.find_snake(game_image)
            if not snake_positions:
                logging.error("Failed to find snake positions")
                return None
            
            food_position = self.find_food(game_image)
            if food_position is None:
                logging.error("Failed to find food position")
                return None
            
            logging.info(f"Snake positions: {snake_positions}")
            logging.info(f"Food position: {food_position}")
            
            return {
                'snake_positions': snake_positions,
                'food_position': food_position,
                'grid_bounds': grid_bounds,
                'game_over': False
            }
            
        except Exception as e:
            logging.error(f"Error in quick state check: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            
    def draw_debug_grid(self, image):
        """Draw a 17x15 numbered grid with enhanced snake visualization"""
        try:
            height, width = image.shape[:2]
            cell_width = width // 17
            cell_height = height // 15
            debug_image = image.copy()
            
            # Draw base grid and numbers (keeping existing code)
            for row in range(15):
                for col in range(17):
                    x = col * cell_width
                    y = row * cell_height
                    cv2.rectangle(debug_image, 
                                (x, y), 
                                (x + cell_width, y + cell_height),
                                (255, 255, 255), 1)
                    
                    cell_num = row * 17 + col
                    cv2.putText(debug_image, 
                              str(cell_num),
                              (x + 5, y + cell_height - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 
                              0.3,
                              (255, 255, 255),
                              1)
            
            # Enhanced snake visualization
            snake_positions = self.find_snake(image)
            if snake_positions:
                # Draw snake body cells with grid numbers
                for i, pos in enumerate(snake_positions):
                    col = pos[0] // cell_width
                    row = pos[1] // cell_height
                    cell_pos = row * 17 + col
                    
                    # Different visualization for head vs body
                    if i == 0:  # Head
                        # Draw double rectangle for head
                        cv2.rectangle(debug_image,
                                    (col * cell_width, row * cell_height),
                                    ((col + 1) * cell_width, (row + 1) * cell_height),
                                    (0, 0, 255), 3)  # Thick red border
                        
                        # Add "H" label
                        cv2.putText(debug_image,
                                  f"H({cell_pos})",
                                  (col * cell_width + 2, row * cell_height + 15),
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  0.4,
                                  (0, 0, 255),
                                  1)
                    else:  # Body
                        cv2.rectangle(debug_image,
                                    (col * cell_width, row * cell_height),
                                    ((col + 1) * cell_width, (row + 1) * cell_height),
                                    (255, 0, 0), 2)  # Blue border
                        
                        # Add segment number
                        cv2.putText(debug_image,
                                  f"S{i}({cell_pos})",
                                  (col * cell_width + 2, row * cell_height + 15),
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  0.3,
                                  (255, 0, 0),
                                  1)
            
            # Food visualization
            food_position = self.find_food(image)
            if food_position:
                food_col = food_position[0] // cell_width
                food_row = food_position[1] // cell_height
                food_cell_pos = food_row * 17 + food_col
                
                cv2.rectangle(debug_image,
                            (food_col * cell_width, food_row * cell_height),
                            ((food_col + 1) * cell_width, (food_row + 1) * cell_height),
                            (0, 255, 0), 2)  # Green for food
                
                # Add "F" label with grid position
                cv2.putText(debug_image,
                          f"F({food_cell_pos})",
                          (food_col * cell_width + 2, food_row * cell_height + 15),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          0.4,
                          (0, 255, 0),
                          1)
            
            cv2.imwrite('debug_numbered_grid.png', debug_image)
            return debug_image
            
        except Exception as e:
            logging.error(f"Error drawing debug grid: {e}")
            return None