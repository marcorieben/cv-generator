#!/bin/bash
# Pre-commit hook installer and setup

set -e

HOOK_DIR=".git/hooks"
HOOK_FILE="$HOOK_DIR/pre-commit"
SCRIPT_PATH="scripts/pre_commit_hook.py"

echo "🔧 Setting up Pre-Commit Hook..."

# Create hook file
mkdir -p "$HOOK_DIR"

cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# Pre-commit hook - automatically runs before each commit

# Get commit message from editor temp file
COMMIT_MSG_FILE="$1"

# Run Python pre-commit script
python3 scripts/pre_commit_hook.py "$COMMIT_MSG_FILE"
EXIT_CODE=$?

# If issues found, warn but allow commit (non-blocking)
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  Pre-commit checks had warnings (commit allowed)"
    exit 0
else
    exit 0
fi
EOF

# Make executable
chmod +x "$HOOK_FILE"

echo "✅ Hook installed at: $HOOK_FILE"
echo ""
echo "📝 Hook behavior:"
echo "   • Validates commit message format"
echo "   • Extracts structured metadata"
echo "   • Scans for unused files"
echo "   • Generates commit documentation"
echo ""
echo "🚀 The hook will run automatically before each commit."
echo ""
echo "To test the hook manually:"
echo "   $HOOK_FILE"
