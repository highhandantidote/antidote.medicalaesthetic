# AWS Elastic Beanstalk Deployment Guide for Antidote Platform

This guide will help you deploy your Antidote medical aesthetic marketplace platform to AWS Elastic Beanstalk.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **EB CLI** (Elastic Beanstalk Command Line Interface)
4. **Git** for version control

### Install AWS CLI and EB CLI

```bash
# Install AWS CLI
pip install awscli

# Install EB CLI
pip install awsebcli

# Configure AWS credentials
aws configure
```

## Step 1: Set Up RDS PostgreSQL Database

### 1.1 Create RDS PostgreSQL Instance

1. Go to AWS RDS Console
2. Click "Create database"
3. Choose "PostgreSQL"
4. Select "Production" or "Dev/Test" template
5. Configure:
   - **DB instance identifier**: `antidote-postgres`
   - **Master username**: `antidote_admin`
   - **Master password**: (choose a secure password)
   - **DB instance class**: `db.t3.micro` (for testing) or `db.t3.small` (for production)
   - **Storage**: 20 GB SSD (gp2)
   - **VPC**: Default VPC
   - **Publicly accessible**: No
   - **Database name**: `antidote_db`

### 1.2 Security Group Configuration

1. Note the security group ID of your RDS instance
2. Edit the security group to allow connections from Elastic Beanstalk:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: Security group of your EB environment (you'll get this after creating EB)

## Step 2: Initialize Elastic Beanstalk Application

### 2.1 Initialize EB Application

```bash
# Navigate to your project directory
cd /path/to/antidote-platform

# Initialize EB application
eb init

# Follow the prompts:
# - Select region (e.g., us-east-1)
# - Application name: antidote-platform
# - Platform: Python 3.11
# - Use CodeCommit: No
# - Set up SSH: Yes (recommended)
```

### 2.2 Create Environment

```bash
# Create production environment
eb create antidote-production

# Or create staging environment first
eb create antidote-staging
```

## Step 3: Configure Environment Variables

### 3.1 Set Database Connection

```bash
# Set database URL (replace with your RDS endpoint details)
eb setenv DATABASE_URL="postgresql://antidote_admin:YOUR_PASSWORD@your-rds-endpoint.region.rds.amazonaws.com:5432/antidote_db"
```

### 3.2 Set Application Secrets

```bash
# Session secret
eb setenv SESSION_SECRET="your-very-secure-session-secret-here"

# Email configuration
eb setenv MAIL_USERNAME="your-email@gmail.com"
eb setenv MAIL_PASSWORD="your-app-password"
eb setenv MAIL_DEFAULT_SENDER="your-email@gmail.com"

# Payment gateway (Razorpay)
eb setenv RAZORPAY_KEY_ID="your-razorpay-key-id"
eb setenv RAZORPAY_KEY_SECRET="your-razorpay-secret"

# AI Services
eb setenv OPENAI_API_KEY="your-openai-api-key"
eb setenv GOOGLE_API_KEY="your-google-api-key"

# SMS/Communication (Twilio)
eb setenv TWILIO_ACCOUNT_SID="your-twilio-sid"
eb setenv TWILIO_AUTH_TOKEN="your-twilio-token"
eb setenv TWILIO_PHONE_NUMBER="your-twilio-number"

# Production settings
eb setenv FLASK_ENV="production"
eb setenv FLASK_DEBUG="False"
```

## Step 4: Deploy Application

### 4.1 Deploy to Elastic Beanstalk

```bash
# Deploy the application
eb deploy

# Monitor deployment
eb logs --all
```

### 4.2 Update RDS Security Group

1. After deployment, get your EB environment's security group:
   ```bash
   eb status
   ```
2. Go to EC2 Console → Security Groups
3. Find your RDS security group
4. Add inbound rule:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: Your EB environment's security group

## Step 5: Post-Deployment Configuration

### 5.1 Initialize Database

The database will be automatically initialized during deployment due to the container commands in `.ebextensions/03_database.config`.

### 5.2 Configure Domain (Optional)

1. Go to EB Console
2. Select your environment
3. Go to "Configuration" → "Domain"
4. Set up your custom domain if needed

### 5.3 Set Up HTTPS

1. Go to "Configuration" → "Load balancer"
2. Add listener for port 443
3. Upload SSL certificate or use AWS Certificate Manager

## Step 6: Monitoring and Scaling

### 6.1 Enable Enhanced Health Monitoring

Enhanced health monitoring is already configured in `.ebextensions/05_performance.config`.

### 6.2 Configure Auto Scaling

Auto scaling is configured for 1-10 instances. Adjust in EB Console:
1. Go to "Configuration" → "Capacity"
2. Modify scaling settings based on your needs

### 6.3 Monitor Performance

```bash
# View logs
eb logs

# Monitor health
eb health

# Check application status
eb status
```

## Step 7: Maintenance Commands

### 7.1 Update Application

```bash
# Deploy updates
git add .
git commit -m "Update application"
eb deploy
```

### 7.2 Scale Environment

```bash
# Scale to specific instance count
eb scale 3

# Scale based on load (auto-scaling is already configured)
```

### 7.3 Database Migrations

For database migrations, you can use:

```bash
# SSH into instance
eb ssh

# Run migrations manually if needed
cd /var/app/current
python -m flask db upgrade
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check RDS security group rules
   - Verify DATABASE_URL format
   - Ensure RDS instance is running

2. **Application Won't Start**
   - Check logs: `eb logs --all`
   - Verify all environment variables are set
   - Check Python package compatibility

3. **Static Files Not Loading**
   - Verify static file configuration in `.ebextensions/01_python.config`
   - Check S3 bucket permissions if using S3 for static files

4. **Performance Issues**
   - Monitor with `eb health --refresh`
   - Check CloudWatch metrics
   - Consider upgrading instance type

### Useful Commands

```bash
# View current environment status
eb status

# View recent logs
eb logs

# Open application in browser
eb open

# View environment health
eb health

# Terminate environment (BE CAREFUL!)
eb terminate
```

## Security Best Practices

1. **Environment Variables**: Never commit secrets to code
2. **Database**: Keep RDS in private subnet
3. **SSL/TLS**: Always use HTTPS in production
4. **IAM Roles**: Use least-privilege principle
5. **Updates**: Regularly update dependencies and platform

## Cost Optimization

1. **Instance Type**: Start with t3.micro/small
2. **Auto Scaling**: Configure based on actual traffic
3. **RDS**: Use appropriate instance size
4. **Monitoring**: Set up CloudWatch alarms for costs

Your Antidote platform is now ready for AWS Elastic Beanstalk deployment!