# Contributing to SniffrAI

Thank you for your interest in contributing to SniffrAI! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic understanding of FastAPI, Pydantic, and web scraping
- API access to OpenAI, Gemini, and Supabase

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/SniffrAI.git
   cd SniffrAI
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints for all functions
- Add comprehensive docstrings
- Keep functions focused and under 50 lines
- Use meaningful variable names

### Project Structure
```
app/
├── api/endpoints/     # API endpoints
├── models/           # Pydantic models
├── services/         # Business logic
├── utils/           # Utility functions
└── config/          # Configuration
```

### Database Guidelines
- Always use "id" as primary key (TEXT type)
- Auto-generate UUIDs for missing primary keys
- Use unique constraints for business fields
- Include timestamps (created_at, updated_at)

### Testing
- Write tests for new features
- Use pytest for testing
- Include both unit and integration tests
- Test error conditions

### Documentation
- Update README.md for major changes
- Document new API endpoints
- Include usage examples
- Keep docstrings current

## 🔧 Making Changes

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow the coding standards
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Your Changes
```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for adding tests
- `refactor:` for code refactoring

### 4. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 🐛 Reporting Issues

### Bug Reports
Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error logs if available

### Feature Requests
Include:
- Clear description of the feature
- Use case and benefits
- Proposed implementation approach
- Any relevant examples

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest app/testing/test_specific.py

# Run with coverage
python -m pytest --cov=app
```

### Test Structure
- Unit tests for individual functions
- Integration tests for API endpoints
- Mock external API calls
- Test both success and error cases

## 📊 Adding New Use Cases

### 1. Update Configuration
Add to `config.yaml`:
```yaml
use_cases:
  your_usecase:
    keywords: ["keyword1", "keyword2"]
    table_name: "your_table"
    primary_key: "unique_field"
    output_format: "YourSchema"
```

### 2. Create Pydantic Schema
Add to `app/models/schemas.py`:
```python
class YourSchema(BaseModel):
    field1: str
    field2: Optional[str] = None
```

### 3. Add Schema Mapping
Update `schema_match()` in `sniffer.py`:
```python
elif schema == "YourSchema":
    return YourSchema
```

### 4. Add Tests
Create tests for the new use case.

## 🔍 Code Review Process

### What We Look For
- Code follows project standards
- Adequate test coverage
- Clear documentation
- No breaking changes
- Performance considerations
- Security best practices

### Review Timeline
- Initial review within 2-3 days
- Follow-up reviews within 1-2 days
- Approval and merge after all checks pass

## 🚀 Release Process

### Version Numbering
We use Semantic Versioning (SemVer):
- MAJOR.MINOR.PATCH
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

### Release Steps
1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Merge to main
6. Create GitHub release
7. Deploy to production

## 🤝 Community Guidelines

### Be Respectful
- Use inclusive language
- Be constructive in feedback
- Help newcomers
- Respect different perspectives

### Communication
- Use GitHub issues for bugs and features
- Join discussions in pull requests
- Ask questions if unclear
- Share knowledge and examples

## 📚 Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Supabase Documentation](https://supabase.com/docs)

### Tools
- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pytest Documentation](https://docs.pytest.org/)

## ❓ Questions?

If you have questions about contributing:
1. Check existing issues and documentation
2. Create a new issue with the "question" label
3. Join our community discussions

Thank you for contributing to SniffrAI! 🎉
