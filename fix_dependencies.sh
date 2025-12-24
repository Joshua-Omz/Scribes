#!/bin/bash
# Quick dependency fix script
# Run this if you ever need to reset your environment

echo "======================================"
echo "Scribes - Dependency Reset Script"
echo "======================================"
echo ""

# Step 1: Uninstall problematic numpy
echo "Step 1: Removing NumPy 2.x..."
pip uninstall numpy -y -q

# Step 2: Install all requirements
echo "Step 2: Installing all requirements..."
pip install -r requirements.txt -q

# Step 3: Verify installation
echo ""
echo "Step 3: Verifying installation..."
python test_dependencies.py

# Done
echo ""
echo "======================================"
echo "Done! If all tests passed, you're ready to go."
echo "======================================"
