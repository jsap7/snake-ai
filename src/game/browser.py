from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class GameController:
    def __init__(self):
        self.driver = None
        self.game_url = "https://www.google.com/search?q=snake+game"
    
    def initialize(self):
        """Initialize the browser and navigate to the game"""
        # Set up Chrome options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Uncomment to run headless
        chrome_options.add_argument('--window-size=1200,800')
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.game_url)
        
        try:
            # Wait longer for the page to fully load
            time.sleep(3)
            
            # Press Enter to start the game
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ENTER)
            time.sleep(1)  # Wait a moment after pressing Enter
            return True
                
        except Exception as e:
            print(f"Error initializing game: {e}")
            self.close()
            return False
    
    def start_game(self):
        """Start a new game"""
        try:
            # Press Enter to start the game
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"Error starting game: {e}")
            return False
    
    def get_game_state(self):
        """Capture and return the current game state"""
        # We'll implement this later
        pass
    
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
                print(f"Error sending move: {e}")
                return False
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit() 