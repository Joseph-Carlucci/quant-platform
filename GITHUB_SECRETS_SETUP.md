# GitHub Secrets Setup Guide

## Overview

This guide walks you through setting up GitHub repository secrets for secure CI/CD deployment of your quantitative research platform.

## 🔐 Required GitHub Secrets

### AWS Credentials
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

### Database Credentials
```
POSTGRES_PASSWORD
PGADMIN_PASSWORD
PGADMIN_EMAIL
```

### API Keys
```
POLYGON_API_KEY
```

### Airflow Admin Credentials
```
AIRFLOW_ADMIN_USERNAME
AIRFLOW_ADMIN_PASSWORD
AIRFLOW_ADMIN_EMAIL
```

## 🚀 Setup Instructions

### Step 1: Navigate to Repository Secrets

1. Go to your GitHub repository
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

### Step 2: Add Repository Secrets

Click **New repository secret** for each of the following:

#### AWS Credentials
**Name:** `AWS_ACCESS_KEY_ID`  
**Value:** Your AWS access key ID

**Name:** `AWS_SECRET_ACCESS_KEY`  
**Value:** Your AWS secret access key

#### Database Secrets
**Name:** `POSTGRES_PASSWORD`  
**Value:** `your_secure_db_password_123`

**Name:** `PGADMIN_PASSWORD`  
**Value:** `your_secure_pgadmin_password_123`

**Name:** `PGADMIN_EMAIL`  
**Value:** `admin@yourcompany.com`

#### API Keys
**Name:** `POLYGON_API_KEY`  
**Value:** Your Polygon.io API key ([Get free key](https://polygon.io/))

#### Airflow Admin Credentials
**Name:** `AIRFLOW_ADMIN_USERNAME`  
**Value:** `your_admin_username`

**Name:** `AIRFLOW_ADMIN_PASSWORD`  
**Value:** `your_secure_admin_password_123`

**Name:** `AIRFLOW_ADMIN_EMAIL`  
**Value:** `admin@yourcompany.com`

## 🛡️ Security Best Practices

### Password Requirements
- **Minimum 12 characters**
- **Mix of letters, numbers, and symbols**
- **Unique passwords for each service**
- **No dictionary words or personal information**

### Example Secure Passwords
```
Database: MyQuant2024!Database#Secure
pgAdmin: PgAdmin$Strong&Password2024
Airflow: AirflowAdmin!2024#Platform
```

## ✅ Verification

### Step 1: Check Secret Status
After adding all secrets, you should see them listed in **Settings** → **Secrets and variables** → **Actions**

### Step 2: Test Deployment
1. Make a small change to any file in `dags/` directory
2. Commit and push to `main` branch
3. Check **Actions** tab for workflow execution
4. Verify deployment succeeds without credential errors

### Step 3: Verify Access
```bash
# After deployment, test secure access
kubectl port-forward -n quant-platform service/airflow 8080:8080

# Access Airflow at http://localhost:8080
# Use your AIRFLOW_ADMIN_USERNAME and AIRFLOW_ADMIN_PASSWORD
```

## 🔧 Using GitHub CLI (Optional)

If you prefer command line:

```bash
# Install GitHub CLI if not already installed
brew install gh  # macOS
# or: sudo apt install gh  # Ubuntu

# Authenticate
gh auth login

# Set secrets via CLI
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY  
gh secret set POSTGRES_PASSWORD
gh secret set PGADMIN_PASSWORD
gh secret set PGADMIN_EMAIL
gh secret set POLYGON_API_KEY
gh secret set AIRFLOW_ADMIN_USERNAME
gh secret set AIRFLOW_ADMIN_PASSWORD
gh secret set AIRFLOW_ADMIN_EMAIL

# Verify secrets are set
gh secret list
```

## 🐛 Troubleshooting

### Secret Not Found Error
```
Error: couldn't find key airflow-admin-username in Secret
```
**Solution:** Ensure secret name exactly matches (case-sensitive):
- `AIRFLOW_ADMIN_USERNAME` (not `airflow_admin_username`)

### Deployment Fails
1. Check **Actions** tab for specific error
2. Verify all 8 required secrets are set
3. Ensure AWS credentials have EKS permissions
4. Check secret values don't contain extra spaces

### Can't Access Airflow
1. Verify `AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` are set
2. Check deployment logs: `kubectl logs -f deployment/airflow -n quant-platform`
3. Restart deployment: `kubectl rollout restart deployment/airflow -n quant-platform`

## 📚 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## 🎯 Next Steps

After setting up secrets:

1. **Test the pipeline** by pushing a change to main branch
2. **Monitor deployment** in the Actions tab
3. **Access your platform** securely via port-forwarding
4. **Add more secrets** as needed for additional integrations

## 🗑️ Note: No Template Files

This platform no longer uses template secret files that could accidentally expose credentials. All secrets are created directly from your GitHub repository secrets during CI/CD deployment.

---

**✨ Your quantitative research platform is now securely configured for production deployment!**