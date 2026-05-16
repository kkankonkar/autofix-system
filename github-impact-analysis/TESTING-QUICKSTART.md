# Testing Quick Start

## 🚀 Quick Commands

```bash
# Run all local tests (recommended before every commit)
./test_local.sh

# Run specific test file
python3 -m pytest tests/test_github_client.py -v --no-cov

# Run all tests with coverage
python3 -m pytest tests/ -v

# Test imports only
python3 -c "from fixium.main import main; print('✓ OK')"
```

## 📋 Pre-Commit Checklist

Before committing changes:

- [ ] Run `./test_local.sh` - all tests pass
- [ ] No new TODOs added to production code
- [ ] Updated tests if you changed functionality
- [ ] Secrets not committed (check `git diff`)

## 🔧 Setup (First Time Only)

```bash
# 1. Create secrets file
cat > secrets.env << 'EOF'
GITHUB_TOKEN=your_token_here
BOBSHELL_API_KEY=your_key_here
FIXIUM_AUTHORIZED_USERS=your_username
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo
EOF

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Make test script executable
chmod +x test_local.sh

# 4. Run tests
./test_local.sh
```

## 🐛 Common Issues

### "Module not found"
```bash
pip3 install -r requirements.txt
```

### "secrets.env not found"
```bash
# Create it (see Setup above)
```

### "Bob CLI not found"
```bash
# Download from: https://github.com/IBM/bob/releases
# Or skip Bob-dependent tests for now
```

### Tests pass locally but fail in GitHub Actions
- Check Python version (Actions uses 3.11)
- Verify GitHub secrets are set
- Check file paths (use relative, not absolute)

## 📚 More Info

- Full guide: [TESTING.md](TESTING.md)
- Main docs: [README.md](README.md)
- Agents: [AGENTS.md](AGENTS.md)