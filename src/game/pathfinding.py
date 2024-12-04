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
    def __init__(self, grid_size=(15, 15)):
        self.grid_size = grid_size
        # Prioritize straight lines but maintain all directions
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, down, left, up
        
    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def is_valid_position(self, pos, snake_positions):
        """More careful validity check"""
        x, y = pos
        
        # Strict boundary check - stay away from walls
        if x < 1 or x >= self.grid_size[0] - 1 or y < 1 or y >= self.grid_size[1] - 1:
            return False
            
        # Avoid snake body
        if pos in snake_positions[:-1]:  # Can move into tail position
            return False
            
        return True
    
    def is_near_wall(self, pos):
        """Check if position is near a wall"""
        x, y = pos
        return x <= 1 or x >= self.grid_size[0] - 2 or y <= 1 or y >= self.grid_size[1] - 2
    
    def get_neighbors(self, pos, snake_positions, food_position):
        """Get neighbors with better wall avoidance"""
        neighbors = []
        
        for dx, dy in self.directions:
            new_pos = (pos[0] + dx, pos[1] + dy)
            if self.is_valid_position(new_pos, snake_positions):
                # Calculate priority score (lower is better)
                score = 0
                
                # Distance to food
                score += self.manhattan_distance(new_pos, food_position)
                
                # Heavy penalty for positions next to walls
                if self.is_near_wall(new_pos):
                    score += 5
                    
                # Extra penalty for corners
                if abs(dx) + abs(dy) == 2:  # Diagonal check
                    score += 3
                    
                neighbors.append((new_pos, score))
        
        # Sort by score
        neighbors.sort(key=lambda x: x[1])
        return [pos for pos, _ in neighbors]
    
    def find_path(self, snake_positions, food_position):
        """A* pathfinding with better wall avoidance"""
        try:
            if not snake_positions or not food_position:
                return None
                
            head = snake_positions[0]
            
            # If food is near wall, find safer approach
            if self.is_near_wall(food_position):
                # Find safer intermediate target
                for dx, dy in self.directions:
                    safe_target = (food_position[0] + dx, food_position[1] + dy)
                    if not self.is_near_wall(safe_target) and self.is_valid_position(safe_target, snake_positions):
                        food_position = safe_target
                        break
            
            # A* search
            open_set = []
            closed_set = set()
            nodes = {}
            
            start = Node(head, 0)
            nodes[head] = start
            heappush(open_set, start)
            
            while open_set:
                current = heappop(open_set)
                
                if current.position == food_position:
                    path = []
                    while current.parent:
                        path.append(current.position)
                        current = current.parent
                    path.append(head)
                    path.reverse()
                    return path
                
                closed_set.add(current.position)
                
                for neighbor_pos in self.get_neighbors(current.position, snake_positions, food_position):
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
                    # Add wall avoidance to heuristic
                    wall_penalty = 5 if self.is_near_wall(neighbor_pos) else 0
                    neighbor.h_cost = self.manhattan_distance(neighbor_pos, food_position) + wall_penalty
                    
                    if neighbor_pos not in [n.position for n in open_set]:
                        heappush(open_set, neighbor)
            
            return self.find_survival_move(snake_positions)
            
        except Exception as e:
            logging.error(f"Error in pathfinding: {e}")
            return None
    
    def find_survival_move(self, snake_positions):
        """Find safest possible move"""
        head = snake_positions[0]
        safe_moves = []
        
        for dx, dy in self.directions:
            new_pos = (head[0] + dx, head[1] + dy)
            if self.is_valid_position(new_pos, snake_positions):
                # Score the safety of this move
                safety_score = 0
                if not self.is_near_wall(new_pos):
                    safety_score += 3
                safe_moves.append((new_pos, safety_score))
        
        if safe_moves:
            # Sort by safety score and return safest move
            safe_moves.sort(key=lambda x: x[1], reverse=True)
            return [head, safe_moves[0][0]]
            
        return None