"""Database utilities for JAR Analyzer."""
import os
import sqlite3
from pathlib import Path


class JarDatabase:
    """Database manager for JAR analysis data."""

    @staticmethod
    def get_default_db_path():
        """Get the default database path.
        
        Returns:
            str: Default path to the database file
        """
        home_dir = os.path.expanduser("~")
        db_dir = os.path.join(home_dir, ".jar_analyzer")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "jar_index.db")
    
    def __init__(self, db_path=None):
        """Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file. If None, uses a default
                     location in the user's home directory.
        """
        if db_path is None:
            db_path = self.get_default_db_path()
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initialize the database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create jars table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jars (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            parent_jar_id INTEGER,
            last_modified INTEGER NOT NULL,
            FOREIGN KEY (parent_jar_id) REFERENCES jars (id) ON DELETE CASCADE
        )
        ''')
        
        # Create classes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            jar_id INTEGER NOT NULL,
            FOREIGN KEY (jar_id) REFERENCES jars (id) ON DELETE CASCADE,
            UNIQUE (name, jar_id)
        )
        ''')
        
        # Create indices for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_classes_name ON classes (name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jars_path ON jars (path)')
        
        self.conn.commit()

    def add_jar(self, jar_path, last_modified, parent_jar_id=None):
        """Add a JAR file to the database.
        
        Args:
            jar_path: Full path to the JAR file
            last_modified: Last modified timestamp of the file
            parent_jar_id: ID of the parent JAR if this is an embedded JAR
            
        Returns:
            int: The ID of the inserted or existing JAR record
        """
        cursor = self.conn.cursor()
        jar_path = os.path.abspath(jar_path)
        filename = os.path.basename(jar_path)
        
        # Check if jar already exists
        cursor.execute('SELECT id FROM jars WHERE path = ?', (jar_path,))
        result = cursor.fetchone()
        
        if result:
            jar_id = result[0]
            # Update last_modified and parent_jar_id if needed
            cursor.execute(
                'UPDATE jars SET last_modified = ?, parent_jar_id = ? WHERE id = ?',
                (last_modified, parent_jar_id, jar_id)
            )
        else:
            cursor.execute(
                'INSERT INTO jars (path, filename, parent_jar_id, last_modified) VALUES (?, ?, ?, ?)',
                (jar_path, filename, parent_jar_id, last_modified)
            )
            jar_id = cursor.lastrowid
        
        self.conn.commit()
        return jar_id

    def add_class(self, class_name, jar_id):
        """Add a class to the database.
        
        Args:
            class_name: Fully qualified Java class name
            jar_id: ID of the JAR file containing this class
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO classes (name, jar_id) VALUES (?, ?)',
                (class_name, jar_id)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Class already exists for this jar, ignore
            pass

    def get_jars_for_class(self, class_name):
        """Get all JARs containing a class with the given name.
        
        Args:
            class_name: Full or partial class name to search for
            
        Returns:
            List of dictionaries with jar information including parent jar details
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT j.id, j.path, j.filename, j.parent_jar_id,
               p.filename as parent_filename, p.path as parent_path
        FROM jars j
        JOIN classes c ON j.id = c.jar_id
        LEFT JOIN jars p ON j.parent_jar_id = p.id
        WHERE c.name LIKE ?
        ORDER BY j.filename
        ''', (f'%{class_name}%',))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_classes_matching(self, pattern):
        """Get all classes matching a pattern.
        
        Args:
            pattern: Pattern to match against class names
            
        Returns:
            List of class names matching the pattern
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT DISTINCT name FROM classes
        WHERE name LIKE ?
        ORDER BY name
        ''', (f'%{pattern}%',))
        
        return [row[0] for row in cursor.fetchall()]

    def clear_jar_classes(self, jar_id):
        """Remove all classes associated with a specific JAR.
        
        Args:
            jar_id: ID of the JAR file
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM classes WHERE jar_id = ?', (jar_id,))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()