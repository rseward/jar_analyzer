"""Command line interface for searching indexed JAR classes."""
import os
import sys
from pathlib import Path

import click
from prompt_toolkit import Application, PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style

from jar_analyzer.db import JarDatabase


class ClassCompleter(Completer):
    """Completer for Java class names."""

    def __init__(self, db):
        """Initialize with database access.
        
        Args:
            db: JarDatabase instance
        """
        self.db = db

    def get_completions(self, document, complete_event):
        """Get completions for the current document text.
        
        Args:
            document: Document being edited
            complete_event: Complete event
            
        Yields:
            Completion objects
        """
        word = document.text
        
        # Get matching classes from the database
        classes = self.db.get_classes_matching(word)
        
        for class_name in classes:
            yield Completion(
                class_name, 
                start_position=-len(word),
                display=class_name
            )


class JarSearch:
    """Interactive UI for searching JAR classes."""

    def __init__(self, db_path=None):
        """Initialize the search interface.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = JarDatabase(db_path)
        self.selected_class = None
        self.jars = []
        
        # Set up key bindings
        self.kb = KeyBindings()
        
        @self.kb.add('c-c')
        @self.kb.add('c-q')
        def _(event):
            """Exit the application."""
            event.app.exit(result="EXIT")
            
        @self.kb.add('escape')
        def _(event):
            """Return to search prompt."""
            event.app.exit(result="SEARCH_AGAIN")
        
        # Define styles
        self.style = Style.from_dict({
            'jar': 'ansibrightyellow',
            'path': 'ansibrightblack',
            'selected': 'ansibrightgreen',
            'header': 'bold',
            'no-results': 'italic'
        })
        
        # Create the layout
        self.jar_window = Window(
            FormattedTextControl(self._get_jar_display),
            always_hide_cursor=True,
        )
        
        self.info_window = Window(
            FormattedTextControl(
                lambda: [
                    ('class:header', 
                     ' Enter class name to search, press TAB for matches, ESC to search again, Ctrl+C to exit')
                ]
            ),
            height=1,
        )
        
        # Main container
        self.container = HSplit([
            self.info_window,
            Window(height=1, char='-'),
            self.jar_window,
        ])
        
        # Application
        self.app = Application(
            layout=Layout(self.container),
            key_bindings=self.kb,
            style=self.style,
            full_screen=False,
        )
        
        # Session for input
        self.session = PromptSession(
            completer=ClassCompleter(self.db),
            complete_while_typing=True,
        )
    
    def _get_jar_display(self):
        """Get the formatted text for the JAR display window.
        
        Returns:
            Formatted text for display
        """
        result = []
        
        if self.selected_class:
            result.append(('class:selected', f" Selected: {self.selected_class}\n\n"))
            
            if not self.jars:
                result.append(('class:no-results', " No JARs containing this class\n"))
            else:
                result.append(('class:header', f" Found in {len(self.jars)} JAR files:\n\n"))
                for jar in self.jars:
                    # Format jar name, showing parent relationship for embedded JARs
                    if jar['parent_jar_id'] is not None and jar['parent_filename'] is not None:
                        jar_name = f" • <{jar['parent_filename']}>->{jar['filename']}"
                    else:
                        jar_name = f" • {jar['filename']}"
                    
                    result.append(('class:jar', f"{jar_name}\n"))
                    result.append(('class:path', f"   {jar['path']}\n\n"))
        else:
            result.append(('class:header', " Enter a class name to search\n"))
            
        return result
    
    def run(self):
        """Run the interactive search interface."""
        click.clear()
        click.echo("JAR Analyzer Class Search")
        click.echo("========================\n")
        
        previous_query = ""
        
        while True:
            try:
                # Get input from the user, using previous query as default
                query = self.session.prompt("> ", default=previous_query)
                
                if not query.strip():
                    continue
                
                # Store the selected class
                self.selected_class = query
                previous_query = query  # Remember this query for next time
                
                # Get JAR files containing this class
                self.jars = self.db.get_jars_for_class(query)
                
                # Display the results
                result = self.app.run()
                
                # Check the result
                if result == "SEARCH_AGAIN":
                    # User pressed ESC, go back to search prompt
                    continue
                else:
                    # User pressed Ctrl+C/Ctrl+Q to exit
                    break
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
    
    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@click.command(help="Search for Java classes in indexed JAR/WAR files")
@click.option(
    "--db",
    type=click.Path(exists=False),
    help="Path to the SQLite database file (default: ~/.jar_analyzer/jar_index.db)"
)
def main(db):
    """Main entry point for the JAR search CLI."""
    try:
        with JarSearch(db_path=db) as search:
            search.run()
        return 0
    except KeyboardInterrupt:
        click.echo("\nSearch canceled.")
        return 0
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())