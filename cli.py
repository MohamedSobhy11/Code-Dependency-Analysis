"""
Interactive CLI tool for dependency analysis.
Provides a user-friendly interface for exploring code dependencies.
"""

import os
import sys
from neo4j import GraphDatabase
from loader import GraphLoader
from analyzer import DependencyAnalyzer
from parser import find_variable_deps
from typing import Optional


class DependencyCLI:
    """Interactive command-line interface for dependency analysis."""
    
    def __init__(self):
        self.loader = None
        self.analyzer = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup Neo4j connection from environment or defaults."""
        URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        USER = os.getenv("NEO4J_USER", "neo4j")
        PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
        DB_NAME = os.getenv("NEO4J_DB", "cycleanalysis")
        
        self.loader = GraphLoader(URI, (USER, PASSWORD), DB_NAME)
        if not self.loader.connect():
            print("Failed to connect to Neo4j. Please check your connection settings.")
            sys.exit(1)
        
        self.analyzer = DependencyAnalyzer(self.loader.driver, DB_NAME)
        print("Connected to Neo4j successfully.\n")
    
    def show_menu(self):
        """Display the main menu."""
        print("\n" + "="*60)
        print("CODE DEPENDENCY ANALYZER - Interactive CLI")
        print("="*60)
        print("\nMain Menu:")
        print("  1. Load code file(s) into Neo4j")
        print("  2. Detect circular dependencies")
        print("  3. Impact analysis")
        print("  4. Dependency analysis")
        print("  5. Find path between variables")
        print("  6. View graph metrics")
        print("  7. Find unused variables")
        print("  8. Find critical path (longest dependency chain)")
        print("  9. Export graph to JSON")
        print("  10. Quick analysis (all metrics)")
        print("  0. Exit")
        print("\n" + "-"*60)
    
    def load_files(self):
        """Load Python files into Neo4j."""
        print("\nLoad Code Files")
        print("-" * 60)
        path = input("Enter file or directory path (or press Enter for test_vars.py): ").strip()
        
        if not path:
            path = "test_vars.py"
        
        try:
            self.loader.clear_database()
            
            if os.path.isfile(path):
                count = self.loader.load_from_file(path)
                print(f"\nLoaded {count} dependencies from {path}")
            elif os.path.isdir(path):
                count = self.loader.load_from_directory(path)
                print(f"\nLoaded {count} total dependencies from {path}")
            else:
                print(f"Path not found: {path}")
                return
            
            print("\nGraph loaded successfully. Ready for analysis.")
            
        except Exception as e:
            print(f"Error: {e}")
    
    def detect_cycles(self):
        """Detect and display circular dependencies."""
        print("\nCircular Dependency Detection")
        print("-" * 60)
        
        try:
            cycles = self.analyzer.detect_cycles()
            
            if not cycles:
                print("No circular dependencies detected.")
            else:
                print(f"Found {len(cycles)} circular dependency group(s):\n")
                for i, cycle in enumerate(cycles, 1):
                    cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
                    print(f"  Cycle {i}: {cycle_str}")
                print("\nNote: Circular dependencies may indicate design issues that require refactoring.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def impact_analysis(self):
        """Perform impact analysis."""
        print("\nImpact Analysis")
        print("-" * 60)
        var_name = input("Enter variable name to analyze: ").strip()
        
        if not var_name:
            print("Variable name required")
            return
        
        try:
            impact = self.analyzer.find_impact(var_name)
            
            print(f"\nImpact Analysis for '{var_name}':")
            print(f"  Total affected variables: {impact['total_affected']}")
            
            if impact['directly_affected']:
                print(f"\n  Directly affected ({len(impact['directly_affected'])}):")
                for var in impact['directly_affected']:
                    print(f"    - {var}")
            
            if impact['transitively_affected']:
                print(f"\n  Transitively affected ({len(impact['transitively_affected'])}):")
                for var in impact['transitively_affected'][:10]:  # Show first 10
                    depth = impact['depths'][var]
                    print(f"    - {var} (depth: {depth})")
                if len(impact['transitively_affected']) > 10:
                    print(f"    ... and {len(impact['transitively_affected']) - 10} more")
            
            if impact['total_affected'] == 0:
                print("  This variable is not used by any other variables.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def dependency_analysis(self):
        """Perform dependency analysis."""
        print("\nDependency Analysis")
        print("-" * 60)
        var_name = input("Enter variable name to analyze: ").strip()
        
        if not var_name:
            print("Variable name required")
            return
        
        try:
            deps = self.analyzer.find_dependencies(var_name)
            
            print(f"\nDependencies for '{var_name}':")
            print(f"  Total dependencies: {deps['total_dependencies']}")
            
            if deps['direct_dependencies']:
                print(f"\n  Direct dependencies ({len(deps['direct_dependencies'])}):")
                for var in deps['direct_dependencies']:
                    print(f"    - {var}")
            
            if deps['transitive_dependencies']:
                print(f"\n  Transitive dependencies ({len(deps['transitive_dependencies'])}):")
                for var in deps['transitive_dependencies'][:10]:
                    depth = deps['depths'][var]
                    print(f"    - {var} (depth: {depth})")
                if len(deps['transitive_dependencies']) > 10:
                    print(f"    ... and {len(deps['transitive_dependencies']) - 10} more")
            
            if deps['total_dependencies'] == 0:
                print("  This variable has no dependencies (root variable).")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def find_path(self):
        """Find path between two variables."""
        print("\nFind Dependency Path")
        print("-" * 60)
        from_var = input("From variable: ").strip()
        to_var = input("To variable: ").strip()
        
        if not from_var or not to_var:
            print("Both variables required")
            return
        
        try:
            paths = self.analyzer.find_path(from_var, to_var)
            
            if not paths:
                print(f"\nNo path found from '{from_var}' to '{to_var}'")
            else:
                print(f"\nFound {len(paths)} path(s):\n")
                for i, path in enumerate(paths[:5], 1):  # Show first 5 paths
                    path_str = " -> ".join(path)
                    print(f"  Path {i} ({len(path)-1} steps): {path_str}")
                if len(paths) > 5:
                    print(f"\n  ... and {len(paths) - 5} more paths")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def view_metrics(self):
        """Display graph metrics."""
        print("\nGraph Metrics")
        print("-" * 60)
        
        try:
            metrics = self5.analyzer.get_metrics()
            
            print(f"\nOverall Statistics:")
            print(f"  Total variables: {metrics['total_variables']}")
            print(f"  Total dependencies: {metrics['total_dependencies']}")
            print(f"  Circular dependencies: {metrics['circular_dependencies']}")
            
            if metrics.get('most_dependent'):
                print(f"\nMost Dependent Variables (others depend on these):")
                try:
                    for item in metrics['most_dependent'][:5]:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            var = str(item[0])
                            count = int(item[1]) if len(item) > 1 else 0
                            print(f"    - {var}: {count} dependents")
                        elif isinstance(item, (list, tuple)) and len(item) == 1:
                            print(f"    - {item[0]}")
                        else:
                            print(f"    - {item}")
                except Exception as e:
                    print(f"    Error displaying most dependent variables: {e}")
            
            if metrics.get('most_dependencies'):
                print(f"\nVariables with Most Dependencies:")
                try:
                    for item in metrics['most_dependencies'][:5]:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            var = str(item[0])
                            count = int(item[1]) if len(item) > 1 else 0
                            print(f"    - {var}: {count} dependencies")
                        elif isinstance(item, (list, tuple)) and len(item) == 1:
                            print(f"    - {item[0]}")
                        else:
                            print(f"    - {item}")
                except Exception as e:
                    print(f"    Error displaying variables with most dependencies: {e}")
            
            if metrics.get('root_variables'):
                print(f"\nRoot Variables (no dependencies):")
                for var in metrics['root_variables'][:10]:
                    print(f"    - {var}")
            
            if metrics.get('leaf_variables'):
                print(f"\nLeaf Variables (nothing depends on them):")
                for var in metrics['leaf_variables'][:10]:
                    print(f"    - {var}")
        
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
    
    def find_unused(self):
        """Find unused variables."""
        print("\nUnused Variables")
        print("-" * 60)
        
        try:
            unused = self.analyzer.find_unused_variables()
            
            if not unused:
                print("All variables are referenced in the dependency graph.")
            else:
                print(f"\nFound {len(unused)} unused variable(s):")
                for var in unused:
                    print(f"    - {var}")
                print("\nNote: These variables may represent dead code or output variables.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def critical_path(self):
        """Find critical path."""
        print("\nCritical Path (Longest Dependency Chain)")
        print("-" * 60)
        
        try:
            path = self.analyzer.get_critical_path()
            
            if not path:
                print("No critical path found")
            else:
                path_str = " -> ".join(path)
                print(f"\nCritical Path ({len(path)-1} steps):")
                print(f"  {path_str}")
                print(f"\nThis represents the longest dependency chain in the analyzed code.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def export_json(self):
        """Export graph to JSON."""
        print("\nExport Graph to JSON")
        print("-" * 60)
        filename = input("Enter output filename (or press Enter for dependency_graph.json): ").strip()
        
        if not filename:
            filename = "dependency_graph.json"
        
        try:
            output_file = self.analyzer.export_graph_json(filename)
            print(f"\nGraph exported to {output_file}")
            print("You can use this file for visualization tools like D3.js, Cytoscape, etc.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def quick_analysis(self):
        """Perform a quick comprehensive analysis."""
        print("\nQuick Analysis")
        print("-" * 60)
        print("Executing comprehensive analysis...\n")
        
        try:
            metrics = self.analyzer.get_metrics()
            cycles = self.analyzer.detect_cycles()
            
            print("QUICK ANALYSIS RESULTS")
            print("=" * 60)
            print(f"Variables: {metrics['total_variables']}")
            print(f"Dependencies: {metrics['total_dependencies']}")
            print(f"Circular Dependencies: {len(cycles)}")
            print(f"Root Variables: {len(metrics['root_variables'])}")
            print(f"Leaf Variables: {len(metrics['leaf_variables'])}")
            
            if cycles:
                print(f"\nWARNING: {len(cycles)} circular dependency group(s) detected.")
                for i, cycle in enumerate(cycles[:3], 1):
                    print(f"  Cycle {i}: {' -> '.join(cycle[:5])}{'...' if len(cycle) > 5 else ''}")
            
            if metrics['most_dependent']:
                try:
                    first_item = metrics['most_dependent'][0]
                    if isinstance(first_item, (list, tuple)) and len(first_item) == 2:
                        var_name, count = first_item[0], first_item[1]
                        print(f"\nMost Critical Variable: {var_name}")
                        print(f"   ({count} variables depend on it)")
                    else:
                        print(f"\nMost Critical Variable: {first_item}")
                except (IndexError, TypeError, ValueError):
                    pass
        
        except Exception as e:
            print(f"Error: {e}")
    
    def run(self):
        """Run the interactive CLI."""
        while True:
            self.show_menu()
            choice = input("Select an option: ").strip()
            
            if choice == "0":
                print("\nExiting application.")
                self.loader.disconnect()
                break
            elif choice == "1":
                self.load_files()
            elif choice == "2":
                self.detect_cycles()
            elif choice == "3":
                self.impact_analysis()
            elif choice == "4":
                self.dependency_analysis()
            elif choice == "5":
                self.find_path()
            elif choice == "6":
                self.view_metrics()
            elif choice == "7":
                self.find_unused()
            elif choice == "8":
                self.critical_path()
            elif choice == "9":
                self.export_json()
            elif choice == "10":
                self.quick_analysis()
            else:
                print("Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    try:
        cli = DependencyCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

