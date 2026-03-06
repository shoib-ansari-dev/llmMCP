#!/bin/bash
cd /Users/I528664/Downloads/learning/llmMCP
source .venv/bin/activate
echo "Installing python-docx..."
pip install python-docx
echo "Verifying installation..."
python -c "from docx import Document; print('SUCCESS: python-docx installed!')"

