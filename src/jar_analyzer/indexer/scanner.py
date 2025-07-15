"""Scanner module for extracting class information from JAR files."""
import os
import zipfile
import time
import tempfile
import shutil
from pathlib import Path
from tqdm import tqdm

from jar_analyzer.db import JarDatabase


class JarScanner:
    """Scanner for JAR and WAR files to extract Java class information."""

    def __init__(self, db_path=None):
        """Initialize the scanner with a database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = JarDatabase(db_path)
        
    def scan_directory(self, directory, recursive=True):
        """Scan a directory for JAR and WAR files and index them.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            int: Number of JAR/WAR files processed
        """
        jar_files = []
        
        # Find all JAR and WAR files
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.jar', '.war')):
                    jar_files.append(os.path.join(root, file))
            
            if not recursive:
                break
        
        # Process the JAR files with progress bar
        processed = 0
        with tqdm(total=len(jar_files), desc="Indexing JAR files") as pbar:
            for jar_path in jar_files:
                try:
                    self.scan_jar(jar_path)
                    processed += 1
                except Exception as e:
                    print(f"Error processing {jar_path}: {e}")
                pbar.update(1)
                
        return processed
    
    def scan_jar(self, jar_path, parent_jar_id=None):
        """Scan a single JAR or WAR file and index its classes.
        
        Args:
            jar_path: Path to the JAR/WAR file
            parent_jar_id: ID of the parent JAR if this is an embedded JAR
            
        Returns:
            int: Number of classes found
        """
        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"JAR file not found: {jar_path}")
        
        last_modified = int(os.path.getmtime(jar_path))
        jar_id = self.db.add_jar(jar_path, last_modified, parent_jar_id)
        
        # Clear existing classes for this JAR to handle updates
        self.db.clear_jar_classes(jar_id)
        
        class_count = 0
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                # Process class files in this archive
                for entry in jar.infolist():
                    if self._is_class_file(entry.filename):
                        class_name = self._class_file_to_name(entry.filename)
                        self.db.add_class(class_name, jar_id)
                        class_count += 1
                    
                    # Recursively process embedded JAR files (especially in WAR files)
                    if self._is_jar_file(entry.filename):
                        # Get the original embedded jar filename
                        original_jar_name = os.path.basename(entry.filename)
                        
                        # Create a temporary file for the embedded JAR
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                            tmp_file.write(jar.read(entry.filename))
                            embedded_jar_path = tmp_file.name
                        
                        try:
                            # Create a temp directory for proper naming
                            temp_dir = tempfile.mkdtemp()
                            clean_jar_path = os.path.join(temp_dir, original_jar_name)
                            
                            # Rename the temp file to have the correct name
                            shutil.move(embedded_jar_path, clean_jar_path)
                            
                            # Scan the embedded JAR and add the count, passing the parent JAR ID
                            class_count += self.scan_jar(clean_jar_path, parent_jar_id=jar_id)
                        finally:
                            # Clean up the extracted file and temp directory
                            if os.path.exists(clean_jar_path):
                                os.remove(clean_jar_path)
                            if os.path.exists(temp_dir):
                                shutil.rmtree(temp_dir)
                    
        except zipfile.BadZipFile:
            print(f"Warning: {jar_path} is not a valid ZIP file")
            return 0
            
        return class_count
    
    def _is_jar_file(self, filename):
        """Check if a file in an archive is a JAR/WAR file.
        
        Args:
            filename: Name of the file inside the archive
            
        Returns:
            bool: True if the file is a JAR/WAR file
        """
        return filename.lower().endswith(('.jar', '.war'))
    
    def _is_class_file(self, filename):
        """Check if a file in a JAR is a Java class file.
        
        Args:
            filename: Name of the file inside the JAR
            
        Returns:
            bool: True if the file is a Java class file
        """
        return filename.lower().endswith('.class') and '$' not in filename
    
    def _class_file_to_name(self, class_file):
        """Convert a class file path to a Java class name.
        
        Args:
            class_file: Path to the class file inside the JAR
            
        Returns:
            str: Java class name in dot notation
        """
        # Remove .class extension and convert / to .
        if class_file.lower().endswith('.class'):
            class_file = class_file[:-6]  # Remove .class
        
        return class_file.replace('/', '.')
    
    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()