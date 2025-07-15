# Project

Goal of the project is write a python project to analyze java jar files.

## Components

- Indexer script that indexes java class names/files found in the jar files and store the index information into a sqlite3 database.
- The indexer shall provide progress information as it analyzes the java project folder containing jar and war files.
- The indexer shall recursively descend into war files. E.g. if a war file contains jar files, the embedded jar files will be indexed as well.
- Write a prompt_toolkit frontend that allows the user to search for class names like the fzf utility and display the jar files
  that the class appears in.

## Requirements

- Design the project to use the python click module for all cli interfaces.
- Make the jar-searcher default to use the ~/.jar_analyzer/jar_index.db when no database is specified.
- Embedded jar file names shall be presented in a user friendly manner. E.g. <warfile.war>->mycool.jar
- The jar-search shall allow the user to press esc after finding a jar to search again while retaining the previous class name they found. E.g. allow them to edit that class name to find another class. 
