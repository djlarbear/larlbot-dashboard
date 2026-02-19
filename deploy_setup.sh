#!/bin/bash
# LarlBot Dashboard Deployment Setup Script 🎰

echo "🎰 LarlBot Dashboard Deployment Setup"
echo "====================================="

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "📦 Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.db
*.sqlite3
.env
.venv/
betting_env/
node_modules/
.DS_Store
*.log
.streamlit/
EOF
    echo "✅ .gitignore created"
fi

# Add deployment files
echo "📁 Adding deployment files..."
git add streamlit_app.py requirements.txt Procfile DEPLOYMENT.md

# Create initial commit if needed
if ! git rev-parse --verify HEAD > /dev/null 2>&1; then
    echo "💾 Creating initial commit..."
    git commit -m "🎰 LarlBot Dashboard - Ready for external hosting

- Cost optimized with Haiku model (90% savings)
- Beautiful Apple Glass Tahoe design  
- Mobile responsive
- Shows latest betting analysis
- Ready for Streamlit Cloud / Render / Railway deployment"
    echo "✅ Initial commit created"
else
    echo "💾 Repository has existing commits"
fi

echo ""
echo "🚀 READY FOR DEPLOYMENT!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: Create repo at github.com and run:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/larlbot-dashboard.git"
echo "   git push -u origin main"
echo ""
echo "2. Deploy to Streamlit Cloud:"
echo "   - Visit: https://share.streamlit.io/"
echo "   - Connect your GitHub repo"  
echo "   - Set main file: streamlit_app.py"
echo "   - Deploy!"
echo ""
echo "3. Your dashboard will be live at: https://YOUR_APP.streamlit.app/"
echo ""
echo "💰 Benefits:"
echo "✅ 90% cheaper AI costs (Haiku model)"
echo "✅ 24/7 dashboard access from anywhere"
echo "✅ No more SIGKILL issues"
echo "✅ Professional web presence"
echo ""
echo "Ready to make some money! 🎯"