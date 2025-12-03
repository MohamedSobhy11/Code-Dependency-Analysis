import ast
import os
from typing import List, Tuple, Dict, Set

class VariableDependencyFinder(ast.NodeVisitor):
    """
    Enhanced AST visitor that finds variable dependencies with metadata.
    Tracks file paths, line numbers, and variable locations.
    """

    def __init__(self, filepath: str = ""):
        # List of tuples: (assigned_var, used_var, line_number, filepath)
        self.dependencies: List[Tuple[str, str, int, str]] = []
        self.current_assign_target = None
        self.current_line = 0
        self.filepath = filepath
        self.variable_locations: Dict[str, List[int]] = {}  # var_name -> [line_numbers]
        self.all_variables: Set[str] = set()

    def visit_Assign(self, node):
        """Called when visiting an assignment like 'a = b' or 'a, b = x, y'"""
        self.current_line = node.lineno
        
        # Handle single-variable assignments: a = b
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            self.current_assign_target = node.targets[0].id
            self.all_variables.add(self.current_assign_target)
            self._record_location(self.current_assign_target, node.lineno)
            
            # Visit the right-hand side (the "value")
            self.visit(node.value)
            self.current_assign_target = None
            
        # Handle tuple unpacking: a, b = x, y
        elif len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            target_tuple = node.targets[0]
            
            # If the value is also a tuple (x, y), match them up
            if isinstance(node.value, ast.Tuple):
                value_tuple = node.value
                for target_node, value_node in zip(target_tuple.elts, value_tuple.elts):
                    if isinstance(target_node, ast.Name):
                        self.current_assign_target = target_node.id
                        self.all_variables.add(self.current_assign_target)
                        self._record_location(self.current_assign_target, node.lineno)
                        self.visit(value_node)
                        self.current_assign_target = None
            else:
                # If value is not a tuple (e.g., a, b = some_function())
                for target_node in target_tuple.elts:
                    if isinstance(target_node, ast.Name):
                        self.current_assign_target = target_node.id
                        self.all_variables.add(self.current_assign_target)
                        self._record_location(self.current_assign_target, node.lineno)
                        self.visit(node.value)
                        self.current_assign_target = None
    
    def visit_AugAssign(self, node):
        """Called when visiting augmented assignments like 'a += b' or 'a *= c'"""
        self.current_line = node.lineno
        
        if isinstance(node.target, ast.Name):
            assigned_var = node.target.id
            self.all_variables.add(assigned_var)
            self._record_location(assigned_var, node.lineno)
            
            # Record self-dependency for augmented assignments
            self.dependencies.append((assigned_var, assigned_var, node.lineno, self.filepath))
            
            # Then, find all variables used in the right-hand side
            self.current_assign_target = assigned_var
            self.visit(node.value)
            self.current_assign_target = None
            
    def visit_Name(self, node):
        """Called for *every* variable name found in the code"""
        if self.current_assign_target and isinstance(node.ctx, ast.Load):
            assigned_var = self.current_assign_target
            used_var = node.id
            self.all_variables.add(used_var)
            self.dependencies.append((assigned_var, used_var, node.lineno, self.filepath))
    
    def _record_location(self, var_name: str, line_number: int):
        """Record where a variable is defined/assigned"""
        if var_name not in self.variable_locations:
            self.variable_locations[var_name] = []
        self.variable_locations[var_name].append(line_number)

def find_variable_deps(filepath: str) -> List[Tuple[str, str, int, str]]:
    """
    Parses a Python file and returns dependencies with metadata.
    
    Returns:
        List of tuples: (assigned_var, used_var, line_number, filepath)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Error reading {filepath}: {e}")
    
    try:
        tree = ast.parse(content, filename=filepath)
        finder = VariableDependencyFinder(filepath)
        finder.visit(tree)
        # Return unique dependencies (preserving metadata)
        seen = set()
        unique_deps = []
        for dep in finder.dependencies:
            key = (dep[0], dep[1])  # (assigned_var, used_var)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        return unique_deps
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in {filepath} at line {e.lineno}: {e.msg}")
    except Exception as e:
        raise Exception(f"Error parsing {filepath}: {e}")

def find_variable_deps_simple(filepath: str) -> List[Tuple[str, str]]:
    """
    Simplified version that returns just (assigned_var, used_var) pairs.
    For backward compatibility.
    """
    deps = find_variable_deps(filepath)
    return [(dep[0], dep[1]) for dep in deps]

# --- Main block for testing just this script ---
if __name__ == "__main__":
    # This part only runs if you execute 'python parser.py'
    test_file_name = "test_vars.py"
    
    print(f"Analyzing {test_file_name}...")
    
    deps = find_variable_deps(test_file_name)
    print("\nFound dependencies:")
    for dep in sorted(deps):
        print(f"  {dep[0]} depends on {dep[1]}")
    
    print(f"\nTotal: {len(deps)} dependencies found")