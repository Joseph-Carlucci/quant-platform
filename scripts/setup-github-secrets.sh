#!/bin/bash

# GitHub Secrets Setup Guide for Quant Platform CI/CD
# This script helps you set up the required secrets for automated deployment

echo "🔐 GitHub Secrets Setup Guide"
echo "=============================="
echo ""
echo "To enable CI/CD for your quantitative research platform, you need to add"
echo "the following secrets to your GitHub repository:"
echo ""
echo "📝 Go to: GitHub Repository → Settings → Secrets and variables → Actions"
echo ""

# AWS Credentials
echo "1. AWS_ACCESS_KEY_ID"
echo "   Value: $(aws configure get aws_access_key_id 2>/dev/null || echo 'YOUR_AWS_ACCESS_KEY')"
echo ""

echo "2. AWS_SECRET_ACCESS_KEY" 
echo "   Value: $(aws configure get aws_secret_access_key 2>/dev/null | sed 's/./*/g' || echo '***YOUR_AWS_SECRET_KEY***')"
echo ""

# Database passwords
echo "3. POSTGRES_PASSWORD"
echo "   Value: quant_password (or your custom password)"
echo ""

echo "4. PGADMIN_PASSWORD"
echo "   Value: admin_password (or your custom password)" 
echo ""

# API Keys
echo "5. POLYGON_API_KEY"
echo "   Value: YOUR_POLYGON_IO_API_KEY"
echo "   Get it from: https://polygon.io/"
echo ""

# Airflow Admin Credentials (Security Critical)
echo "6. AIRFLOW_ADMIN_USERNAME"
echo "   Value: your_secure_admin_username"
echo ""

echo "7. AIRFLOW_ADMIN_PASSWORD"
echo "   Value: your_secure_admin_password"
echo ""

echo "8. AIRFLOW_ADMIN_EMAIL"
echo "   Value: admin@yourcompany.com"
echo ""

# Optional secrets for advanced features
echo "📋 Optional Secrets (for future expansion):"
echo ""
echo "9. ALPHA_VANTAGE_API_KEY (optional)"
echo "   Value: YOUR_ALPHA_VANTAGE_KEY"
echo ""

echo "10. SLACK_WEBHOOK_URL (optional, for notifications)"
echo "   Value: YOUR_SLACK_WEBHOOK_URL"
echo ""

echo "11. DISCORD_WEBHOOK_URL (optional, for notifications)"
echo "   Value: YOUR_DISCORD_WEBHOOK_URL"
echo ""

# Repository setup instructions
echo "🚀 Repository Setup Instructions:"
echo "================================="
echo ""
echo "1. Create your GitHub repository:"
echo "   gh repo create quant-platform --public"
echo ""
echo "2. Add your files and push:"
echo "   git add ."
echo "   git commit -m 'Initial commit: Quantitative Research Platform'"
echo "   git push -u origin main"
echo ""
echo "3. Set up repository secrets (via GitHub web interface):"
echo "   - Go to your repo → Settings → Secrets and variables → Actions"
echo "   - Click 'New repository secret' for each secret above"
echo ""
echo "4. Create a develop branch for staging deployments:"
echo "   git checkout -b develop"
echo "   git push -u origin develop"
echo ""

# Environment setup
echo "🔧 Environment Configuration:"
echo "============================="
echo ""
echo "Your current AWS configuration:"
aws configure list 2>/dev/null || echo "❌ AWS CLI not configured"
echo ""

echo "Your current EKS cluster:"
kubectl config current-context 2>/dev/null || echo "❌ kubectl not configured"
echo ""

# Verification steps
echo "✅ Verification Steps:"
echo "====================="
echo ""
echo "After setting up secrets, verify your deployment by:"
echo "1. Making a change to any file in the dags/ directory"
echo "2. Committing and pushing to main branch"
echo "3. Checking the Actions tab in your GitHub repository"
echo "4. Monitoring the deployment progress"
echo ""

echo "📊 Expected Workflow:"
echo "===================="
echo ""
echo "main branch push → CI/CD Pipeline:"
echo "  ├── Test DAGs for syntax errors"
echo "  ├── Validate Python code"
echo "  ├── Deploy to production EKS cluster"
echo "  ├── Update ConfigMaps with new DAGs"
echo "  ├── Restart Airflow deployment"
echo "  └── Verify deployment success"
echo ""

echo "develop branch push → Staging Pipeline:"
echo "  ├── Test DAGs for syntax errors"
echo "  ├── Validate Python code"
echo "  └── Deploy to staging environment"
echo ""

echo "🎯 Quick Test Commands:"
echo "======================"
echo ""
echo "# Test your DAGs locally before pushing:"
echo "python -c \"import sys; sys.path.append('dags'); from polygon_data_pipeline import dag; print('DAG OK')\""
echo ""
echo "# Check if your AWS credentials work:"
echo "aws eks describe-cluster --name quant-platform-cluster"
echo ""
echo "# Verify kubectl access:"
echo "kubectl get pods -n quant-platform"
echo ""

echo "🔗 Useful GitHub CLI Commands:"
echo "=============================="
echo ""
echo "# Create repository with GitHub CLI:"
echo "gh repo create quant-platform --public --description 'Quantitative Research Platform'"
echo ""
echo "# Set secrets via CLI (if you prefer):"
echo "gh secret set AWS_ACCESS_KEY_ID"
echo "gh secret set AWS_SECRET_ACCESS_KEY" 
echo "gh secret set POLYGON_API_KEY"
echo "gh secret set POSTGRES_PASSWORD"
echo "gh secret set PGADMIN_PASSWORD"
echo ""
echo "# View workflow runs:"
echo "gh run list"
echo ""
echo "# Watch a specific workflow run:"
echo "gh run watch"
echo ""

echo "📚 Additional Resources:"
echo "======================="
echo ""
echo "- GitHub Actions Documentation: https://docs.github.com/en/actions"
echo "- Kubernetes Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/"
echo "- EKS Best Practices: https://aws.github.io/aws-eks-best-practices/"
echo ""

echo "✨ You're all set! Push to main branch to trigger your first automated deployment!" 