"""
Enhanced Neo4j loader with batch operations, better error handling,
and integration with the analyzer module.
"""

from neo4j import GraphDatabase
from parser import find_variable_deps
from typing import List, Tuple, Optional
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GraphLoader:
    """Enhanced loader for populating Neo4j with dependency data."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 auth: Tuple[str, str] = ("neo4j", "password"),
                 db_name: str = "cycleanalysis"):
        self.uri = uri
        self.auth = auth
        self.db_name = db_name
        self.driver = None
    
    def connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
            self.driver.verify_connectivity()
            logger.info("Neo4j connection successful!")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def disconnect(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    def clear_database(self):
        """Remove all nodes and relationships from the database."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        try:
            self.driver.execute_query(
                "MATCH (n) DETACH DELETE n",
                database_=self.db_name
            )
            logger.info("Database cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise
    
    def load_from_file(self, filepath: str) -> int:
        """
        Load dependencies from a single Python file.
        Returns the number of relationships loaded.
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        logger.info(f"Parsing {filepath} for variable dependencies...")
        
        try:
            deps = find_variable_deps(filepath)
            logger.info(f"Found {len(deps)} dependencies in {filepath}")
            
            if deps:
                self._batch_create_relationships(deps)
            
            return len(deps)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            raise
    
    def load_from_directory(self, directory: str, pattern: str = "*.py") -> int:
        """
        Load dependencies from all Python files in a directory.
        Returns total number of relationships loaded.
        """
        import glob
        
        if not os.path.isdir(directory):
            raise ValueError(f"Not a valid directory: {directory}")
        
        python_files = glob.glob(os.path.join(directory, pattern))
        total_relationships = 0
        
        logger.info(f"Found {len(python_files)} Python files in {directory}")
        
        for filepath in python_files:
            try:
                count = self.load_from_file(filepath)
                total_relationships += count
            except Exception as e:
                logger.warning(f"Skipping {filepath} due to error: {e}")
                continue
        
        return total_relationships
    
    def _batch_create_relationships(self, relationships: List[Tuple[str, str, int, str]]):
        """
        Efficiently create relationships in batches.
        Uses UNWIND for better performance.
        """
        # Prepare data for batch insert
        batch_data = [
            {
                "from_name": dep[0],
                "to_name": dep[1],
                "line_number": dep[2],
                "filepath": dep[3]
            }
            for dep in relationships
        ]
        
        query = """
        UNWIND $data as row
        MERGE (a:Variable {name: row.from_name})
        MERGE (b:Variable {name: row.to_name})
        MERGE (a)-[r:DEPENDS_ON]->(b)
        ON CREATE SET r.line_number = row.line_number,
                      r.filepath = row.filepath
        """
        
        try:
            self.driver.execute_query(
                query,
                parameters_={"data": batch_data},
                database_=self.db_name
            )
            logger.info(f"Loaded {len(relationships)} relationships into Neo4j")
        except Exception as e:
            logger.error(f"Error creating relationships: {e}")
            raise
    
    def add_file_metadata(self):
        """Add file information as nodes for better tracking."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        query = """
        MATCH (v:Variable)
        WHERE v.filepath IS NOT NULL
        WITH DISTINCT v.filepath as filepath
        MERGE (f:File {path: filepath})
        WITH f, filepath
        MATCH (v:Variable {filepath: filepath})
        MERGE (v)-[:DEFINED_IN]->(f)
        """
        
        try:
            self.driver.execute_query(query, database_=self.db_name)
            logger.info("File metadata added")
        except Exception as e:
            logger.error(f"Error adding file metadata: {e}")


def main():
    """Main execution function for standalone use."""
    import sys
    
    # Configuration - can be overridden by environment variables
    URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    USER = os.getenv("NEO4J_USER", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    DB_NAME = os.getenv("NEO4J_DB", "cycleanalysis")
    
    # File or directory to analyze
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "test_vars.py"
    
    loader = GraphLoader(URI, (USER, PASSWORD), DB_NAME)
    
    try:
        if not loader.connect():
            return
        
        loader.clear_database()
        
        if os.path.isfile(target):
            loader.load_from_file(target)
        elif os.path.isdir(target):
            loader.load_from_directory(target)
        else:
            logger.error(f"Target not found: {target}")
            return
        
        logger.info(f"Graph created successfully in '{DB_NAME}' database.")
        logger.info("\nNote: Use analyzer.py or cli.py for advanced analysis.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        loader.disconnect()


if __name__ == "__main__":
    main()
