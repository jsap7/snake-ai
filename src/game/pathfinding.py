import numpy as np
from heapq import heappush, heappop
import logging
import random

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
    def __init__(self, grid_size=(17, 15)):
        self.grid_size = grid_size
        self.directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left
        
    def find_path(self, snake_positions, food_position):
        """Simple A* pathfinding with wall avoidance"""
        if not snake_positions or not food_position:
            return None
            
        head = snake_positions[0]
        
        # Don't try to path to invalid food positions
        if not self.is_valid_position(food_position, snake_positions):
            logging.error(f"Invalid food position: {food_position}")
            return None
            
        # Initialize A* structures
        open_set = {head}
        closed_set = set()
        came_from = {}
        g_score = {head: 0}
        f_score = {head: self.manhattan_distance(head, food_position)}
        
        while open_set:
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            if current == food_position:
                path = self.reconstruct_path(came_from, current)
                logging.info(f"Found path: {path}")
                return path
                
            open_set.remove(current)
            closed_set.add(current)
            
            # Check each possible direction
            for dx, dy in self.directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if not self.is_valid_position(neighbor, snake_positions) or neighbor in closed_set:
                    continue
                    
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                    
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self.manhattan_distance(neighbor, food_position)
        
        logging.error("No path found to food")
        return None
    
    def is_valid_position(self, position, snake_positions):
        """
        Check if a position is valid (not occupied by snake and within bounds)
        Args:
            position: tuple (x, y) to check
            snake_positions: list of (x, y) tuples representing snake body
        Returns:
            bool: True if position is valid, False otherwise
        """
        x, y = position
        
        # Check bounds (17x15 grid)
        if x < 0 or x >= 17 or y < 0 or y >= 15:
            return False
        
        # Check if position collides with snake
        if position in snake_positions:
            return False
        
        return True
    
    def manhattan_distance(self, pos1, pos2):
        """Calculate Manhattan distance between two points"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def reconstruct_path(self, came_from, current):
        """Reconstruct path from came_from dict"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]