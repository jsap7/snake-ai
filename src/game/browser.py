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
            time.sleep(2)
            return True
            
        except Exception as e:
            logging.error(f"Error finding game Play button: {e}")
            return False
            
    def capture_game_area(self):
        """Capture screenshot of game area"""
        try:
            logging.info("Taking screenshot...")
            screenshot = self.driver.get_screenshot_as_png()
            nparr = np.frombuffer(screenshot, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            logging.info(f"Screenshot captured. Shape: {image.shape}")
            logging.info(f"Sample color at (300,300): {image[300,300]}")
            
            return image
        except Exception as e:
            logging.error(f"Error capturing game area: {e}")
            return None
            
    def find_game_grid(self, image):
        """Find the game grid boundaries"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
                
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            logging.info(f"Largest contour area: {area}")
            
            x, y, w, h = cv2.boundingRect(largest_contour)
            logging.info(f"Found grid at ({x}, {y}) with size {w}x{h}")
            
            return ((x, y), (w, h))
            
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
            
            # Calculate relative position
            rel_x = x - grid_x
            rel_y = y - grid_y
            
            # Calculate cell size
            cell_width = grid_width / 15
            cell_height = grid_height / 15
            
            # Convert to grid coordinates
            grid_col = int(rel_x / cell_width)
            grid_row = int(rel_y / cell_height)
            
            # Log the conversion
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
            # Take screenshot
            screenshot = self.capture_game_area()
            if screenshot is None:
                return False
            
            # Look for the play button that appears on death
            try:
                play_button = self.driver.find_element(By.CSS_SELECTOR, 'div.FL0z2d[aria-label="Play"]')
                if play_button.is_displayed():
                    logging.info("Found play button - game over detected")
                    return True
            except:
                pass
            
            # Backup check: look for snake
            snake_positions = self.find_snake(screenshot)
            if not snake_positions:
                logging.info("No snake found - game over detected")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking death: {e}")
            return False
            
    def get_quick_state(self):
        """Fast state check for responsive gameplay"""
        try:
            game_image = self.capture_game_area()
            if game_image is None:
                return None

            if self.check_death():
                return {'game_over': True}

            grid_bounds = self.find_game_grid(game_image)
            if not grid_bounds:
                return None

            snake_positions = self.find_snake(game_image)
            if not snake_positions:
                return None

            food_position = self.find_food(game_image)
            if not food_position:
                return None

            return {
                'snake_positions': snake_positions,
                'food_position': food_position,
                'grid_bounds': grid_bounds,
                'game_over': False
            }
            
        except Exception as e:
            logging.error(f"Error in quick state check: {e}")
            return None
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()