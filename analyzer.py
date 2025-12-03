"""
Advanced dependency analysis module for code dependency graphs.
Provides cycle detection, impact analysis, metrics, and query utilities.
"""

from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict, deque
from neo4j import GraphDatabase
import json


class DependencyAnalyzer:
    """Advanced analyzer for dependency graphs stored in Neo4j."""
    
    def __init__(self, driver, db_name: str = "cycleanalysis"):
        self.driver = driver
        self.db_name = db_name
    
    def detect_cycles(self) -> List[List[str]]:
        """
        Detect all circular dependencies in the graph using DFS.
        Returns list of cycles, where each cycle is a list of variable names.
        """
        query = """
        MATCH path = (start:Variable)-[:DEPENDS_ON*]->(start:Variable)
        WHERE length(path) > 0
        RETURN [n in nodes(path) | n.name] as cycle
        LIMIT 100
        """
        
        cycles = []
        result = self.driver.execute_query(query, database_=self.db_name)
        
        for record in result.records:
            cycle = record["cycle"]
            # Remove duplicates while preserving order
            seen = set()
            unique_cycle = []
            for var in cycle:
                if var not in seen:
                    unique_cycle.append(var)
                    seen.add(var)
                elif var == unique_cycle[0] and len(unique_cycle) > 1:
                    # Found the cycle, return it
                    cycles.append(unique_cycle)
                    break
        
        # Also use Tarjan's algorithm for more comprehensive detection
        cycles.extend(self._tarjan_cycles())
        
        # Remove duplicate cycles
        unique_cycles = []
        seen_cycles = set()
        for cycle in cycles:
            cycle_tuple = tuple(sorted(cycle))
            if cycle_tuple not in seen_cycles:
                seen_cycles.add(cycle_tuple)
                unique_cycles.append(cycle)
        
        return unique_cycles
    
    def _tarjan_cycles(self) -> List[List[str]]:
        """Use Tarjan's algorithm to find strongly connected components (cycles)."""
        # Build adjacency list
        query = "MATCH (a:Variable)-[:DEPENDS_ON]->(b:Variable) RETURN a.name as from, b.name as to"
        result = self.driver.execute_query(query, database_=self.db_name)
        
        graph = defaultdict(list)
        for record in result.records:
            graph[record["from"]].append(record["to"])
        
        # Tarjan's algorithm
        index = {}
        lowlink = {}
        stack = []
        on_stack = set()
        cycles = []
        index_counter = [0]
        
        def strongconnect(v):
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack.add(v)
            
            for w in graph.get(v, []):
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], index[w])
            
            if lowlink[v] == index[v]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.append(w)
                    if w == v:
                        break
                if len(component) > 1:
                    cycles.append(component)
        
        for node in graph:
            if node not in index:
                strongconnect(node)
        
        return cycles
    
    def find_impact(self, variable_name: str) -> Dict[str, any]:
        """
        Find all variables that depend on the given variable (impact analysis).
        Useful for understanding what breaks when you change a variable.
        """
        query = """
        MATCH (start:Variable {name: $var_name})
        MATCH path = (dependent:Variable)-[:DEPENDS_ON*]->(start)
        WHERE dependent <> start
        RETURN DISTINCT dependent.name as affected_var, 
               length(path) as depth
        ORDER BY depth, affected_var
        """
        
        result = self.driver.execute_query(
            query, 
            parameters_={"var_name": variable_name},
            database_=self.db_name
        )
        
        affected = [record["affected_var"] for record in result.records]
        depths = {record["affected_var"]: record["depth"] for record in result.records}
        
        return {
            "variable": variable_name,
            "directly_affected": [v for v, d in depths.items() if d == 1],
            "transitively_affected": [v for v, d in depths.items() if d > 1],
            "total_affected": len(affected),
            "affected_variables": affected,
            "depths": depths
        }
    
    def find_dependencies(self, variable_name: str) -> Dict[str, any]:
        """
        Find all variables that the given variable depends on.
        Useful for understanding what a variable needs to work.
        """
        query = """
        MATCH (start:Variable {name: $var_name})
        MATCH path = (start)-[:DEPENDS_ON*]->(dependency:Variable)
        WHERE dependency <> start
        RETURN DISTINCT dependency.name as dep_var,
               length(path) as depth
        ORDER BY depth, dep_var
        """
        
        result = self.driver.execute_query(
            query,
            parameters_={"var_name": variable_name},
            database_=self.db_name
        )
        
        deps = [record["dep_var"] for record in result.records]
        depths = {record["dep_var"]: record["depth"] for record in result.records}
        
        return {
            "variable": variable_name,
            "direct_dependencies": [v for v, d in depths.items() if d == 1],
            "transitive_dependencies": [v for v, d in depths.items() if d > 1],
            "total_dependencies": len(deps),
            "all_dependencies": deps,
            "depths": depths
        }
    
    def find_path(self, from_var: str, to_var: str) -> List[List[str]]:
        """
        Find all paths from one variable to another.
        Useful for understanding the dependency chain.
        """
        query = """
        MATCH path = (start:Variable {name: $from_var})-[:DEPENDS_ON*]->(end:Variable {name: $to_var})
        WITH path, [n in nodes(path) | n.name] as path_list
        RETURN path_list
        ORDER BY length(path)
        LIMIT 20
        """
        
        result = self.driver.execute_query(
            query,
            parameters_={"from_var": from_var, "to_var": to_var},
            database_=self.db_name
        )
        
        paths = [record["path_list"] for record in result.records]
        return paths
    
    def get_metrics(self) -> Dict[str, any]:
        """Get comprehensive metrics about the dependency graph."""
        queries = {
            "total_variables": "MATCH (v:Variable) RETURN count(v) as count",
            "total_dependencies": "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) as count",
            "most_dependent": """
                MATCH (v:Variable)<-[:DEPENDS_ON]-(dependent)
                WITH v, count(dependent) as count
                RETURN v.name as var, count
                ORDER BY count DESC
                LIMIT 10
            """,
            "most_dependencies": """
                MATCH (v:Variable)-[:DEPENDS_ON]->(dep)
                WITH v, count(dep) as count
                RETURN v.name as var, count
                ORDER BY count DESC
                LIMIT 10
            """,
            "isolated_variables": """
                MATCH (v:Variable)
                WHERE NOT (v)-[:DEPENDS_ON]-()
                RETURN v.name as var
            """,
            "root_variables": """
                MATCH (v:Variable)
                WHERE NOT (v)<-[:DEPENDS_ON]-()
                RETURN v.name as var
            """,
            "leaf_variables": """
                MATCH (v:Variable)
                WHERE NOT (v)-[:DEPENDS_ON]->()
                RETURN v.name as var
            """
        }
        
        metrics = {}
        
        for key, query in queries.items():
            try:
                result = self.driver.execute_query(query, database_=self.db_name)
                
                # Neo4j driver returns result object with .records attribute
                records = result.records if hasattr(result, 'records') else result
                
                if key in ["total_variables", "total_dependencies"]:
                    metrics[key] = records[0]["count"] if records else 0
                elif key in ["most_dependent", "most_dependencies"]:
                    # These queries return both var and count - ensure we create proper tuples
                    result_list = []
                    for record in records:
                        try:
                            # Neo4j records support dict-like access
                            var_name = record["var"]
                            count_val = record["count"]
                            
                            # Ensure we have valid values
                            if var_name is None:
                                continue
                            
                            # Ensure count is an integer
                            try:
                                count_val = int(count_val) if count_val is not None else 0
                            except (ValueError, TypeError):
                                count_val = 0
                            
                            # Create tuple - MUST be exactly 2 elements for unpacking
                            # Convert to string and int to ensure proper types
                            tuple_item = (str(var_name), int(count_val))
                            
                            # Verify it's a proper 2-tuple before adding
                            if isinstance(tuple_item, tuple) and len(tuple_item) == 2:
                                result_list.append(tuple_item)
                            else:
                                # Skip if not a proper 2-tuple
                                continue
                        except (KeyError, IndexError, TypeError, AttributeError):
                            # Skip malformed records
                            continue
                    metrics[key] = result_list
                else:
                    metrics[key] = [record["var"] for record in records]
            except Exception as e:
                # If there's an error, set empty/default values
                if key in ["total_variables", "total_dependencies"]:
                    metrics[key] = 0
                elif key in ["most_dependent", "most_dependencies"]:
                    metrics[key] = []
                else:
                    metrics[key] = []
                # Log the error for debugging (optional)
                # print(f"Warning: Error processing {key}: {e}")
        
        # Calculate additional metrics
        cycles = self.detect_cycles()
        metrics["circular_dependencies"] = len(cycles)
        metrics["cycles"] = cycles
        
        return metrics
    
    def find_unused_variables(self) -> List[str]:
        """
        Find variables that are defined but never used as dependencies.
        These might be dead code or output variables.
        """
        query = """
        MATCH (v:Variable)
        WHERE NOT (v)<-[:DEPENDS_ON]-()
        RETURN v.name as var
        """
        
        result = self.driver.execute_query(query, database_=self.db_name)
        return [record["var"] for record in result.records]
    
    def get_critical_path(self) -> List[str]:
        """
        Find the longest dependency chain (critical path).
        Useful for understanding the most complex dependency flow.
        """
        query = """
        MATCH path = (start:Variable)-[:DEPENDS_ON*]->(end:Variable)
        WHERE NOT (start)<-[:DEPENDS_ON]-() AND NOT (end)-[:DEPENDS_ON]->()
        WITH path, [n in nodes(path) | n.name] as path_list
        RETURN path_list
        ORDER BY length(path) DESC
        LIMIT 1
        """
        
        result = self.driver.execute_query(query, database_=self.db_name)
        if result.records:
            return result.records[0]["path_list"]
        return []
    
    def export_graph_json(self, output_file: str = "dependency_graph.json"):
        """Export the entire graph to JSON format."""
        query = """
        MATCH (a:Variable)-[r:DEPENDS_ON]->(b:Variable)
        RETURN a.name as from, b.name as to
        """
        
        result = self.driver.execute_query(query, database_=self.db_name)
        
        graph_data = {
            "nodes": [],
            "edges": []
        }
        
        nodes_set = set()
        for record in result.records:
            from_var = record["from"]
            to_var = record["to"]
            
            if from_var not in nodes_set:
                graph_data["nodes"].append({"id": from_var, "label": from_var})
                nodes_set.add(from_var)
            if to_var not in nodes_set:
                graph_data["nodes"].append({"id": to_var, "label": to_var})
                nodes_set.add(to_var)
            
            graph_data["edges"].append({
                "source": from_var,
                "target": to_var
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)
        
        return output_file

