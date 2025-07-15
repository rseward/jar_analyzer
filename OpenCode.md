# OpenCode Memory

## Commands

### Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Build
```bash
pip install build
python -m build
```

### Test
```bash
pytest
pytest --cov=src tests/
```

### Lint
```bash
flake8 src tests
# or
ruff check .
```

### Typecheck
```bash
mypy src
```

## Code Style

- Follow PEP 8 guidelines
- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants
- 4 space indentation
- 79-character line length limit
- Docstrings in Google or NumPy format

## Project Structure

- `/src` - Source code package
- `/tests` - Test files
- `/docs` - Documentation
- `/notebooks` - Jupyter notebooks
- `requirements.txt` - Project dependencies
- `setup.py` or `pyproject.toml` - Project metadata