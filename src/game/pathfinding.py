import numpy as np
from heapq import heappush, heappop
import logging
import traceback

class Node:
    def __init__(self, position, g_cost=float('inf'), h_cost=0):
        self.position = position
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.parent = None
        
    def f_cost(self):
        return self.g_cost + self.h_cost
        
    def __lt__(self, other):
        return self.f_cost() < other.f_cost()

class PathFinder:
    def __init__(self, grid_size=(30, 30)):
        self.grid_size = grid_size
        self.directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left
        
    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def is_valid_position(self, pos, snake_positions, check_tail=True):
        """Check if a position is valid and safe"""
        x, y = pos
        
        # Less conservative boundary checking
        if x < 0 or x >= self.grid_size[0] or y < 0 or y >= self.grid_size[1]:
            return False
            
        # Don't check tail if it's moving
        if check_tail:
            if pos in snake_positions:
                return False
        else:
            if pos in snake_positions[:-1]:  # Exclude tail
                return False
                
        return True
    
    def get_neighbors(self, pos, snake_positions):
        """Get valid neighboring positions"""
        neighbors = []
        for dx, dy in self.directions:
            new_pos = (pos[0] + dx, pos[1] + dy)
            if self.is_valid_position(new_pos, snake_positions, check_tail=False):
                neighbors.append(new_pos)
        return neighbors
    
    def find_path(self, snake_positions, food_position):
        """A* pathfinding with simplified logic"""
        try:
            if not snake_positions or not food_position:
                logging.warning("Invalid snake or food positions")
                return None
                
            head = snake_positions[0]
            logging.info(f"Finding path from {head} to {food_position}")
            
            # Initialize A* structures
            open_set = []
            closed_set = set()
            nodes = {}
            
            # Create start node
            start = Node(head, 0)
            nodes[head] = start
            heappush(open_set, start)
            
            while open_set:
                current = heappop(open_set)
                
                # Found the food
                if current.position == food_position:
                    path = []
                    while current.parent:
                        path.append(current.position)
                        current = current.parent
                    path.append(head)
                    path.reverse()
                    logging.info(f"Found path of length {len(path)}: {path}")
                    return path
                    
                closed_set.add(current.position)
                
                # Check all valid neighbors
                for neighbor_pos in self.get_neighbors(current.position, snake_positions):
                    if neighbor_pos in closed_set:
                        continue
                        
                    g_cost = current.g_cost + 1
                    
                    if neighbor_pos not in nodes:
                        neighbor = Node(neighbor_pos)
                        nodes[neighbor_pos] = neighbor
                    else:
                        neighbor = nodes[neighbor_pos]
                        if g_cost >= neighbor.g_cost:
                            continue
                    
                    neighbor.parent = current
                    neighbor.g_cost = g_cost
                    neighbor.h_cost = self.manhattan_distance(neighbor_pos, food_position)
                    
                    if neighbor_pos not in [n.position for n in open_set]:
                        heappush(open_set, neighbor)
            
            logging.warning("No path found to food")
            return self.find_safe_path(snake_positions)
            
        except Exception as e:
            logging.error(f"Error finding path: {e}")
            traceback.print_exc()
            return None
            
    def find_safe_path(self, snake_positions):
        """Find a safe move when no path to food exists"""
        head = snake_positions[0]
        neighbors = self.get_neighbors(head, snake_positions)
        
        if neighbors:
            logging.info(f"Found safe move to {neighbors[0]}")
            return [head, neighbors[0]]
            
        logging.warning("No safe moves available")
        return None