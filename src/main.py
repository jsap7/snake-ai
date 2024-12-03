from ai.agent import SnakeAgent

def main():
    agent = SnakeAgent()
    try:
        agent.start()
        agent.run()
    except KeyboardInterrupt:
        print("\nStopping the agent...")
    finally:
        agent.game.close()

if __name__ == "__main__":
    main() 