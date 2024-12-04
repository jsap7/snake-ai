from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import cv2
import numpy as np
import logging
import traceback

class GameController:
    def __init__(self):
        self.driver = None
        self.game_url = "https://www.google.com/search?q=snake+game"
    
    def initialize(self):
        """Initialize the browser and navigate to the game"""
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--window-size=1200,800')
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.game_url)
        
        try:
            # Wait for page to load
            time.sleep(3)
            return True
                
        except Exception as e:
            logging.error(f"Error initializing game: {e}")
            self.close()
            return False
    
    def start_game(self):
        """Start a new game, handling both initial launch and replays"""
        try:
            # Wait for initial load
            time.sleep(1)
            
            # Check if this is the first game (we need to click both buttons)
            if not hasattr(self, '_first_game_started'):
                self._first_game_started = False
            
            if not self._first_game_started:
                # First game - need to click the initial Play button
                logging.info("Looking for first Play button...")
                first_play = self.driver.find_element(By.XPATH, "//div[text()='Play']")
                if first_play:
                    logging.info("Found first Play button, clicking...")
                    first_play.click()
                    time.sleep(2)
                    self._first_game_started = True
                else:
                    logging.error("Could not find first Play button")
                    return False
            
            # For all games (first and replays), click the game Play button
            logging.info("Looking for game Play button...")
            try:
                game_play = self.driver.find_element(By.CSS_SELECTOR, "div[jsname='NSjDf'][class='FL0z2d'][aria-label='Play']")
                if game_play and game_play.is_displayed():
                    logging.info("Found game Play button, clicking...")
                    self.driver.execute_script("arguments[0].click();", game_play)
                    time.sleep(1)
                    # Reset first move tracker
                    self._made_first_move = False
                    return True
                else:
                    logging.error("Could not find game Play button")
                    return False
                
            except Exception as e:
                logging.error(f"Error finding game Play button: {e}")
                # Try alternative selector if the first one fails
                try:
                    game_play = self.driver.find_element(By.CSS_SELECTOR, ".FL0z2d[aria-label='Play']")
                    if game_play and game_play.is_displayed():
                        self.driver.execute_script("arguments[0].click();", game_play)
                        time.sleep(1)
                        self._made_first_move = False
                        return True
                except:
                    return False
            
        except Exception as e:
            logging.error(f"Error in start_game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_game_state(self):
        """Capture and return the current game state with multiple validations"""
        try:
            # Take multiple snapshots to ensure accurate state
            states = []
            for _ in range(3):  # Take 3 snapshots
                game_image = self.capture_game_area()
                if game_image is None:
                    continue
                    
                snake_positions = self.find_snake(game_image)
                if not snake_positions:
                    continue
                    
                food_position = self.find_food(game_image)
                if not food_position:
                    continue
                    
                states.append({
                    'raw_image': game_image,
                    'grid_bounds': self.find_game_grid(game_image),
                    'snake_positions': snake_positions,
                    'snake_length': len(snake_positions),
                    'food_position': food_position,
                    'score': self.get_score_from_image(game_image),
                    'game_over': False
                })
                    
                time.sleep(0.05)  # Small delay between captures
            
            if not states:
                logging.warning("No valid states captured")
                return None
                
            # Validate states are consistent
            if len(states) >= 2:
                # Check if snake positions are relatively consistent
                head_positions = [state['snake_positions'][0] for state in states]
                max_head_diff = max(
                    abs(head_positions[0][0] - pos[0]) + abs(head_positions[0][1] - pos[1])
                    for pos in head_positions[1:]
                )
                    
                if max_head_diff > 50:  # Pixel threshold for movement
                    logging.warning(f"Inconsistent snake movement detected: {max_head_diff}px")
                    # Take one more capture to confirm position
                    time.sleep(0.1)
                    final_state = self.get_single_state()
                    if final_state:
                        states.append(final_state)
            
            # Use the most recent valid state
            current_state = states[-1]
            
            # Enhanced game over detection
            if self.is_game_over(current_state['snake_positions']):
                logging.info("Game over detected: Snake frozen")
                return {'game_over': True}
                
            # Validate food is reachable
            grid_bounds = current_state['grid_bounds']
            if grid_bounds:
                snake_head = current_state['snake_positions'][0]
                food_pos = current_state['food_position']
                head_grid = self.convert_to_grid_coordinates(snake_head, grid_bounds)
                food_grid = self.convert_to_grid_coordinates(food_pos, grid_bounds)
                    
                logging.info(f"Snake head at {head_grid}, food at {food_grid}")
                    
                # Check if food is in impossible position
                if (abs(head_grid[0] - food_grid[0]) + abs(head_grid[1] - food_grid[1])) > 30:
                    logging.warning("Food appears to be in unreachable position")
            
            return current_state
            
        except Exception as e:
            logging.error(f"Error getting game state: {e}")
            traceback.print_exc()
            return None
    
    def get_single_state(self):
        """Capture a single game state"""
        try:
            game_image = self.capture_game_area()
            if game_image is None:
                return None
                
            snake_positions = self.find_snake(game_image)
            if not snake_positions:
                return None
                
            return {
                'raw_image': game_image,
                'grid_bounds': self.find_game_grid(game_image),
                'snake_positions': snake_positions,
                'snake_length': len(snake_positions),
                'food_position': self.find_food(game_image),
                'score': self.get_score_from_image(game_image),
                'game_over': False
            }
        except Exception as e:
            logging.error(f"Error getting single state: {e}")
            return None
    
    def find_game_grid(self, image):
        """Find the game grid with improved detection"""
        try:
            if image is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Find contours
            contours, _ = cv2.findContours(
                cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1],
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                return None
            
            # Find largest contour (should be game grid)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            logging.info(f"Largest contour area: {area}")
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Log grid detection details
            logging.info(f"Found grid at ({x}, {y}) with size {w}x{h}")
            
            return ((x, y), (w, h))
            
        except Exception as e:
            logging.error(f"Error finding game grid: {e}")
            return None
    
    def find_snake(self, image):
        """Find snake positions in the image with more flexible segment detection"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Purple/blue color range for snake
        lower_blue = np.array([110, 50, 50])  # More permissive color range
        upper_blue = np.array([130, 255, 255])
        
        # Create mask for snake
        snake_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Find contours
        contours, _ = cv2.findContours(snake_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and merge nearby contours
        snake_positions = []
        min_area = 50  # Minimum area to consider
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Check if this position is close to any existing positions
                    is_new_segment = True
                    for i, (x, y) in enumerate(snake_positions):
                        if abs(cx - x) < 20 and abs(cy - y) < 20:  # Merge threshold
                            is_new_segment = False
                            break
                    
                    if is_new_segment:
                        snake_positions.append((cx, cy))
                        logging.info(f"Found snake segment at ({cx}, {cy}) with area {area}")
        
        # Only consider it invalid if we find no segments at all
        if not snake_positions:
            logging.info("No snake segments found")
            return []
        
        # Sort positions roughly from head to tail
        snake_positions.sort(key=lambda pos: (-pos[1], pos[0]))  # Sort by y then x
        
        logging.info(f"Total snake segments found: {len(snake_positions)}")
        return snake_positions
    
    def find_food(self, image):
        """Find food position in the image"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Red color range in HSV
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])
        
        # Create mask for food (combining both red ranges)
        food_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        food_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        food_mask = cv2.bitwise_or(food_mask1, food_mask2)
        
        cv2.imwrite('food_mask.png', food_mask)
        
        # Find contours
        contours, _ = cv2.findContours(food_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            logging.info(f"Food contour area: {area}")
            if area > 20:  # Adjusted threshold
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    logging.info(f"Found food at ({cx}, {cy})")
                    return (cx, cy)
        
        return None
    
    def get_score_from_image(self, image):
        """Extract score from the top of the image"""
        try:
            # The score is in the top-left corner
            # Let's crop that region
            height, width = image.shape[:2]
            top_region = image[0:100, 0:200]  # Adjust these values based on where the score appears
            
            # Save the cropped region for debugging
            cv2.imwrite('score_region.png', cv2.cvtColor(top_region, cv2.COLOR_RGB2BGR))
            
            # For now, we can count the snake parts to verify the score
            snake_positions = self.find_snake(image)
            snake_length = len(snake_positions)
            
            if snake_length > 0:
                # Score = snake length - initial length (4)
                calculated_score = max(0, snake_length - 4)
                logging.info(f"Snake length: {snake_length}, Calculated score: {calculated_score}")
                return calculated_score
            
            return 0
            
        except Exception as e:
            logging.error(f"Error getting score: {e}")
            return 0
    
    def send_move(self, direction):
        """Send a move command to the game"""
        key_mapping = {
            'up': Keys.ARROW_UP,
            'down': Keys.ARROW_DOWN,
            'left': Keys.ARROW_LEFT,
            'right': Keys.ARROW_RIGHT
        }
        
        if direction in key_mapping:
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(key_mapping[direction])
                return True
            except Exception as e:
                logging.error(f"Error sending move: {e}")
                return False
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
    
    def capture_game_area(self):
        """Capture the game area and return it as a numpy array"""
        try:
            logging.info("Taking screenshot...")
            # Take screenshot of the whole page
            screenshot = self.driver.get_screenshot_as_png()
            
            # Convert to numpy array with correct color format
            nparr = np.frombuffer(screenshot, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB (cv2 uses BGR by default)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            logging.info(f"Screenshot captured. Shape: {image.shape}")
            
            # Save both BGR and RGB versions for debugging
            cv2.imwrite('debug_bgr.png', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            
            # Save a color sample image
            sample_point = image[300, 300]  # Get color of a random point
            logging.info(f"Sample color at (300,300): {sample_point}")  # This will help us verify colors
            
            return image
            
        except Exception as e:
            logging.error(f"Error capturing game area: {e}")
            import traceback
            traceback.print_exc()
            return None 
    
    def convert_to_grid_coordinates(self, pixel_pos, grid_bounds):
        """Convert pixel coordinates to grid coordinates with detailed logging"""
        try:
            if not pixel_pos or not grid_bounds:
                logging.error(f"Invalid input - pixel_pos: {pixel_pos}, grid_bounds: {grid_bounds}")
                return None
            
            grid_x, grid_y = grid_bounds[0]
            grid_width, grid_height = grid_bounds[1]
            
            # Log raw values
            logging.debug(f"""
            Converting coordinates:
            Pixel position: {pixel_pos}
            Grid origin: ({grid_x}, {grid_y})
            Grid size: {grid_width}x{grid_height}
            """)
            
            # Calculate cell size (assume 30x30 grid)
            cell_width = grid_width / 30
            cell_height = grid_height / 30
            
            # Calculate relative position
            rel_x = pixel_pos[0] - grid_x
            rel_y = pixel_pos[1] - grid_y
            
            # Log intermediate calculations
            logging.debug(f"""
            Cell size: {cell_width}x{cell_height}
            Relative position: ({rel_x}, {rel_y})
            """)
            
            # Convert to grid coordinates
            grid_pos_x = int(rel_x / cell_width)
            grid_pos_y = int(rel_y / cell_height)
            
            # Ensure within bounds
            grid_pos_x = max(0, min(29, grid_pos_x))
            grid_pos_y = max(0, min(29, grid_pos_y))
            
            logging.info(f"Converted {pixel_pos} -> ({grid_pos_x}, {grid_pos_y})")
            return (grid_pos_x, grid_pos_y)
            
        except Exception as e:
            logging.error(f"Error converting coordinates: {e}")
            traceback.print_exc()
            return None
    
    def make_move(self, direction):
        """Execute a move with validation"""
        try:
            # Map direction to key
            key_map = {
                'up': Keys.ARROW_UP,
                'right': Keys.ARROW_RIGHT,
                'down': Keys.ARROW_DOWN,
                'left': Keys.ARROW_LEFT
            }
            
            if direction not in key_map:
                logging.warning(f"Invalid direction: {direction}")
                return False
            
            # Get current state before move
            pre_move_state = self.get_single_state()
            if not pre_move_state:
                return False
            
            # Focus game area and send key
            body = self.driver.find_element(By.TAG_NAME, 'body')
            body.click()
            
            # Send key command
            body.send_keys(key_map[direction])
            logging.info(f"Sent {direction} command")
            
            # Small delay to let move register
            time.sleep(0.1)
            
            # Verify move was made
            post_move_state = self.get_single_state()
            if not post_move_state:
                return False
            
            # Check if snake head actually moved
            pre_head = pre_move_state['snake_positions'][0]
            post_head = post_move_state['snake_positions'][0]
            
            if pre_head == post_head:
                logging.warning("Snake did not move after command")
                return False
            
            self._made_first_move = True
            return True
            
        except Exception as e:
            logging.error(f"Error making move: {e}")
            return False
    
    def get_next_move(self, current_pos, next_pos):
        """Determine direction to move from current position to next position"""
        try:
            if not current_pos or not next_pos:
                logging.error(f"Invalid positions - current: {current_pos}, next: {next_pos}")
                return None
            
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]
            
            logging.info(f"Movement vector: dx={dx}, dy={dy}")
            
            # Determine direction
            if abs(dx) > abs(dy):
                direction = 'right' if dx > 0 else 'left'
            else:
                direction = 'down' if dy > 0 else 'up'
            
            logging.info(f"Chose direction: {direction}")
            return direction
            
        except Exception as e:
            logging.error(f"Error getting next move: {e}")
            traceback.print_exc()
            return None
    
    def is_game_over(self, snake_positions):
        """Check if snake is actually dead by verifying movement"""
        try:
            # First check if play button is visible (fastest check)
            try:
                play_button = self.driver.find_elements(By.CSS_SELECTOR, '[aria-label="Play"]')
                if play_button and len(play_button) > 0 and play_button[0].is_displayed():
                    logging.info("DEATH: Play button visible")
                    return True
            except:
                pass

            if not snake_positions:
                logging.info("DEATH: No snake positions found")
                return True
            
            # Don't check for frozen snake until we've made at least one move
            if not hasattr(self, '_made_first_move'):
                self._made_first_move = False
                return False
            
            if not self._made_first_move:
                return False
            
            # Store initial head position
            initial_head = snake_positions[0]
            
            # Wait a moment
            time.sleep(0.2)
            
            # Get new positions
            new_positions = self.find_snake(self.capture_game_area())
            
            # If we can't find the snake at all, it's dead
            if not new_positions:
                logging.info("DEATH: Snake disappeared")
                return True
            
            # Get new head position
            new_head = new_positions[0]
            
            # If head hasn't moved AT ALL between frames, snake is dead
            if initial_head == new_head:
                # Double check with another small delay
                time.sleep(0.2)
                final_check = self.find_snake(self.capture_game_area())
                if final_check and final_check[0] == initial_head:
                    logging.info(f"DEATH: Snake frozen at {initial_head}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking death: {e}")
            return False
    
    def reset_game(self):
        """Reset the game after game over"""
        try:
            logging.info("Resetting game...")
            time.sleep(1)  # Wait for game over animation
            
            # Click the play button to restart
            play_button = self.driver.find_element(By.CSS_SELECTOR, ".FL0z2d[aria-label='Play']")
            if play_button:
                play_button.click()
                time.sleep(1)  # Wait for game to restart
                logging.info("Game reset successful")
                return True
            
            logging.error("Could not find Play button to reset game")
            return False
            
        except Exception as e:
            logging.error(f"Error resetting game: {e}")
            traceback.print_exc()
            return False
