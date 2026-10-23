# AccessLens Deployment Guide

## Overview

This document describes how to deploy and manage the AccessLens MVP on AWS using CloudFormation/SAM and GitHub Actions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [AWS Infrastructure](#aws-infrastructure)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Deployment Procedures](#deployment-procedures)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- AWS CLI >= 2.0
- AWS SAM CLI >= 1.92.0
- Python >= 3.11
- Docker (for local testing)
- Git
- Node.js >= 18 (for frontend)

### AWS Account Setup

1. Create AWS account
2. Configure AWS CLI credentials:
   ```bash
   aws configure
   ```
3. Create S3 bucket for deployment artifacts:
   ```bash
   aws s3 mb s3://accesslens-deployment-<account-id>
   ```

## Local Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start local server
uvicorn src.app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start
```

### Local AWS Simulation

```bash
cd backend

# Start LocalStack (optional, for local DynamoDB/S3)
docker-compose up -d localstack

# Run tests with local AWS
pytest tests/ -v --env=local
```

## AWS Infrastructure

### Infrastructure Components

**SAM Template: `backend/infrastructure/template.yaml`**

Defines:
- **DynamoDB Tables**: Scans, Findings, Repairs, Verification
- **S3 Buckets**: Lambda code, Reports, Frontend
- **API Gateway**: HTTP API with CORS
- **Lambda Execution Role**: IAM role for Lambda functions
- **CloudWatch Logs**: API Gateway and Lambda logs

### Key Configuration

| Component | Dev | Test | Prod |
|-----------|-----|------|------|
| Billing Mode | PAY_PER_REQUEST | PAY_PER_REQUEST | PROVISIONED |
| Point-in-Time Recovery | Disabled | Disabled | Enabled |
| Log Retention | 7 days | 14 days | 30 days |
| Encryption | AES256 | AES256 | KMS |

### Deploying Infrastructure

```bash
# Validate template
sam validate --template backend/infrastructure/template.yaml

# Deploy dev environment
sam deploy \
  --template-file backend/infrastructure/template.yaml \
  --stack-name accesslens-dev \
  --parameter-overrides Environment=dev \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# Deploy production environment
sam deploy \
  --template-file backend/infrastructure/template.yaml \
  --stack-name accesslens-prod \
  --parameter-overrides Environment=prod \
  --capabilities CAPABILITY_IAM \
  --region us-east-1 \
  --no-confirm-changeset
```

## CI/CD Pipeline

### GitHub Actions Workflow

**File: `.github/workflows/ci-cd.yaml`**

### Pipeline Stages

#### 1. Build & Test (Always Runs)

- Python 3.11 setup
- Install dependencies
- Lint code (pylint)
- Run unit tests (pytest)
- Generate coverage report
- Build Lambda package

#### 2. Deploy Dev (Runs on `develop` branch push)

- Configure AWS credentials
- Deploy SAM stack with dev parameters
- Create/update dev infrastructure

#### 3. Deploy Prod (Runs on `main` branch push)

- Configure AWS credentials
- Deploy SAM stack with prod parameters
- Run smoke tests
- Notify on success/failure

### Required Secrets

Add to GitHub repository secrets:

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

```bash
# Via GitHub CLI
gh secret set AWS_ACCESS_KEY_ID -b"<value>"
gh secret set AWS_SECRET_ACCESS_KEY -b"<value>"
```

### Pipeline Triggers

- **Pull Requests**: Runs build & test only
- **Push to `develop`**: Runs build, test, deploy-dev
- **Push to `main`**: Runs build, test, deploy-prod

## Deployment Procedures

### Manual Deployment

#### Prerequisites

```bash
sam --version
aws --version
```

#### Deploy Step-by-Step

```bash
# 1. Package Lambda functions
cd backend
mkdir -p build/lambda
pip install -r requirements.txt -t build/lambda/
cp -r src/app/* build/lambda/
cd build/lambda && zip -r ../lambda-package.zip .

# 2. Upload to S3
aws s3 cp lambda-package.zip s3://accesslens-deployment-<account-id>/

# 3. Deploy infrastructure
sam deploy \
  --template-file infrastructure/template.yaml \
  --stack-name accesslens-prod \
  --parameter-overrides Environment=prod \
  --capabilities CAPABILITY_IAM

# 4. Run smoke tests
pytest tests/e2e/ -v

# 5. Verify deployment
aws cloudformation describe-stacks \
  --stack-name accesslens-prod \
  --query 'Stacks[0].StackStatus'
```

### Rollback Procedure

```bash
# Rollback to previous stack version
aws cloudformation cancel-update-stack \
  --stack-name accesslens-prod

# Or delete stack and redeploy from backup
aws cloudformation delete-stack \
  --stack-name accesslens-prod
```

## Environment Configuration

### Environment Variables

**Development (.env.dev)**
```
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
AWS_REGION=us-east-1
API_TIMEOUT=60
```

**Production (.env.prod)**
```
ENVIRONMENT=prod
LOG_LEVEL=INFO
AWS_REGION=us-east-1
API_TIMEOUT=30
CACHE_TTL=3600
```

### Lambda Environment Variables

Set via SAM template parameters:

```yaml
Environment:
  Variables:
    ENVIRONMENT: !Ref Environment
    LOG_LEVEL: INFO
    DYNAMODB_REGION: !Ref AWS::Region
```

## Monitoring and Logs

### CloudWatch Logs

Access logs:

```bash
# View API Gateway logs
aws logs tail /aws/apigateway/accesslens-prod --follow

# View Lambda logs
aws logs tail /aws/lambda/accesslens-prod --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/accesslens-prod \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics

Monitor key metrics:

- **API Gateway**: Request count, latency, errors
- **Lambda**: Duration, errors, throttles
- **DynamoDB**: ConsumedWriteCapacityUnits, ConsumedReadCapacityUnits
- **S3**: Object count, storage size

### Alarms

Create alarms for:

- Lambda error rate > 1%
- API latency > 5 seconds (p99)
- DynamoDB throttling events
- S3 bucket size > 100GB

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name accesslens-lambda-errors \
  --alarm-description "Alert if Lambda error rate > 1%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Common Issues

#### 1. Lambda Package Too Large

**Error**: `An error occurred (RequestEntityTooLargeException) when calling the CreateFunction operation`

**Solution**:
- Remove dev dependencies from Lambda package
- Use Lambda layers for shared dependencies
- Exclude test files from package

```bash
pip install -r requirements.txt -t build/lambda/ --no-dev
find build/lambda -name "*.pyc" -delete
find build/lambda -name "tests" -type d -exec rm -rf {} +
```

#### 2. DynamoDB Provisioning Errors

**Error**: `The table TableName already exists`

**Solution**:
- Check CloudFormation stack status
- Update stack instead of creating new one
- Use stack drift detection

```bash
aws cloudformation detect-stack-drift \
  --stack-name accesslens-prod

aws cloudformation get-template-summary \
  --template-body file://infrastructure/template.yaml
```

#### 3. API Gateway 404 Errors

**Error**: `{"message":"Not Found"}`

**Solution**:
- Verify routes are correctly mapped
- Check Lambda proxy integration
- Review API Gateway logs

```bash
aws apigatewayv2 get-routes \
  --api-id <api-id>

aws logs tail /aws/apigateway/accesslens-prod --follow
```

### Debug Mode

Enable debug logging:

```bash
export SAM_DEBUG=true
sam deploy --debug
```

## Cleanup

### Delete Stack

```bash
aws cloudformation delete-stack \
  --stack-name accesslens-prod

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name accesslens-prod
```

### Empty and Delete S3 Buckets

```bash
aws s3 rm s3://accesslens-reports-prod-<account-id> --recursive
aws s3 rb s3://accesslens-reports-prod-<account-id>
```

## References

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AccessLens API Documentation](./API.md)