from game.browser import GameController
import time

def test_game_initialization():
    controller = GameController()
    
    print("Initializing game...")
    if controller.initialize():
        print("Game initialized successfully!")
        
        print("Starting game...")
        time.sleep(2)  # Wait for game to settle
        if controller.start_game():
            print("Game started successfully!")
            
            # Test some basic movements
            print("Testing movement...")
            time.sleep(1)
            movements = ['up', 'right', 'down', 'left']
            for move in movements:
                print(f"Moving {move}")
                controller.send_move(move)
                time.sleep(0.5)
            
            time.sleep(2)  # Watch the result
    
    print("Closing browser...")
    controller.close()

if __name__ == "__main__":
    test_game_initialization() 