#!/bin/bash
# Clone additional test repositories for evaluation

REPO_DIR="examples/additional_repos"
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

echo "Cloning Flask..."
if [ ! -d "flask" ]; then
    git clone --depth 1 https://github.com/pallets/flask.git
    echo "✓ Flask cloned"
else
    echo "✓ Flask already exists"
fi

echo "Cloning FastAPI..."
if [ ! -d "fastapi" ]; then
    git clone --depth 1 https://github.com/tiangolo/fastapi.git
    echo "✓ FastAPI cloned"
else
    echo "✓ FastAPI already exists"
fi

echo "Cloning pytest..."
if [ ! -d "pytest" ]; then
    git clone --depth 1 https://github.com/pytest-dev/pytest.git
    echo "✓ pytest cloned"
else
    echo "✓ pytest already exists"
fi

echo ""
echo "All repositories cloned successfully!"
echo "Location: $(pwd)"
