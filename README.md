# Code Dependency Analyzer

A powerful Python tool for analyzing variable dependencies in your code using **Neo4j** graph database. Perfect for understanding code structure, detecting circular dependencies, and performing impact analysis.

## Features

### Core Capabilities
- **AST-based Parsing**: Uses Python's Abstract Syntax Tree for accurate dependency detection
- **Multi-file Support**: Analyze entire projects or single files
- **Neo4j Integration**: Store and query dependencies in a graph database
- **Line Number Tracking**: Know exactly where dependencies occur

### Advanced Analysis Features

1. **Circular Dependency Detection**
   - Find all circular dependencies in your code
   - Uses Tarjan's algorithm for comprehensive cycle detection

2. **Impact Analysis**
   - See what breaks when you change a variable
   - Track direct and transitive impacts

3. **Dependency Analysis**
   - Understand what a variable needs to work
   - Find all dependencies (direct and transitive)

4. **Path Finding**
   - Find all dependency paths between variables
   - Understand the dependency chain

5. **Graph Metrics**
   - Most dependent variables
   - Variables with most dependencies
   - Root and leaf variables
   - Critical path (longest dependency chain)

6. **Dead Code Detection**
   - Find unused variables
   - Identify potential dead code

7. **Export Functionality**
   - Export graph to JSON for visualization
   - Compatible with D3.js, Cytoscape, and other tools

## Quick Start

### Prerequisites

1. **Neo4j Desktop** (or Neo4j server)
   - Download from [neo4j.com](https://neo4j.com/download/)
   - Create a new database (default name: `cycleanalysis`)
   - Note your password (default: `password`)

2. **Python 3.7+**

### Installation

1. **Clone or download this project**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Neo4j connection** (optional):
   ```bash
   # Set environment variables (or use defaults)
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your_password"
   export NEO4J_DB="cycleanalysis"
   ```

### Usage

#### Option 1: Interactive CLI (Recommended)

```bash
python cli.py
```

This launches an interactive menu where you can:
- Load code files
- Detect cycles
- Perform impact analysis
- View metrics
- And much more!

#### Option 2: Command Line Loader

```bash
# Load a single file
python loader.py test_vars.py

# Load all Python files in a directory
python loader.py /path/to/your/project
```

#### Option 3: Programmatic Usage

```python
from loader import GraphLoader
from analyzer import DependencyAnalyzer

# Connect and load
loader = GraphLoader()
loader.connect()
loader.load_from_file("your_file.py")

# Analyze
analyzer = DependencyAnalyzer(loader.driver)
cycles = analyzer.detect_cycles()
impact = analyzer.find_impact("variable_name")
metrics = analyzer.get_metrics()
```

## Use Cases

### 1. **Refactoring Safety**
Before refactoring, check what will break:
```python
impact = analyzer.find_impact("old_variable_name")
# See all variables that depend on it
```

### 2. **Code Review**
Quickly understand complex code:
```python
deps = analyzer.find_dependencies("complex_variable")
# Understand what it needs
```

### 3. **Architecture Analysis**
Find the critical path and most important variables:
```python
metrics = analyzer.get_metrics()
critical_path = analyzer.get_critical_path()
```

### 4. **Dead Code Detection**
Find unused variables:
```python
unused = analyzer.find_unused_variables()
```

### 5. **Circular Dependency Detection**
Find problematic cycles:
```python
cycles = analyzer.detect_cycles()
```

## Example: Analyzing test_vars.py

```bash
# 1. Load the test file
python loader.py test_vars.py

# 2. Run interactive analysis
python cli.py
# Select option 2 to detect cycles
# Select option 10 for quick analysis
```

**Expected Output:**
- Detects the circular dependency: `x -> y -> z -> x`
- Shows impact analysis for each variable
- Displays graph metrics

## Project Structure

```
.
├── parser.py          # AST-based dependency parser
├── loader.py          # Neo4j data loader
├── analyzer.py        # Advanced analysis functions
├── cli.py             # Interactive CLI tool
├── test_vars.py       # Example test file
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

### Environment Variables

You can configure the connection using environment variables:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export NEO4J_DB="cycleanalysis"
```

Or modify the defaults in `loader.py` and `cli.py`.

## Supported Python Features

- Simple assignments: `a = b`
- Augmented assignments: `a += b`, `a *= c`
- Tuple unpacking: `a, b = x, y`
- Complex expressions: `result = (x + y) * z`
- Multi-line assignments

## Limitations

- Function calls are not tracked (e.g., `result = func(x)` doesn't track `func` dependencies)
- Import dependencies are not analyzed
- Attribute access (e.g., `obj.attr`) is not tracked
- Class methods and instance variables need enhancement

