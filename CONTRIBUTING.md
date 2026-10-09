# Contributing to AstPack

Thank you for your interest in contributing to AstPack! 

## Development Setup

AstPack uses [`uv`](https://github.com/astral-sh/uv) or standard `pip` for development.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zxcompany311-svg/astpack.git
   cd astpack
   ```

2. **Create a virtual environment & install dependencies**:
   ```bash
   uv venv
   uv pip install -e ".[dev,cli]"
   ```

3. **Run the test suite**:
   ```bash
   uv run pytest
   ```

## Pull Request Guidelines

- Ensure all new features come with corresponding unit tests in `tests/`.
- Keep the core engine zero-dependency (no required C-extensions or external wheels for basic operations).
- Follow clean PEP 8 style formatting.
- Write clear, concise commit messages.
