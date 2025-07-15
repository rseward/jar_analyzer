compile:
	uv pip install -r requirements.txt
	uv pip install .

query:
	sqlite3 ~/.jar_analyzer/jar_index.db

clean:
	rm -rf ~/.jar_analyzer/

index:
	jar-indexer java/

test:
	jar-search

