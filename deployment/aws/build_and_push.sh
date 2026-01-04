#!/bin/bash
# Build and push Docker images to AWS ECR

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-west-2}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "================================================"
echo "Building and Pushing Images to ECR"
echo "================================================"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo ""

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push agent-api
echo ""
echo "Building agent-api..."
docker build -t dhcs-bht/agent-api -f api/Dockerfile .
docker tag dhcs-bht/agent-api:latest $ECR_REGISTRY/dhcs-bht/agent-api:latest
docker push $ECR_REGISTRY/dhcs-bht/agent-api:latest
echo "✅ agent-api pushed"

# Build and push dashboard
echo ""
echo "Building dashboard..."
docker build -t dhcs-bht/dashboard -f dashboard/Dockerfile .
docker tag dhcs-bht/dashboard:latest $ECR_REGISTRY/dhcs-bht/dashboard:latest
docker push $ECR_REGISTRY/dhcs-bht/dashboard:latest
echo "✅ dashboard pushed"

# Build and push generator
echo ""
echo "Building generator..."
docker build -t dhcs-bht/generator -f generator/Dockerfile .
docker tag dhcs-bht/generator:latest $ECR_REGISTRY/dhcs-bht/generator:latest
docker push $ECR_REGISTRY/dhcs-bht/generator:latest
echo "✅ generator pushed"

echo ""
echo "================================================"
echo "All images pushed successfully!"
echo "================================================"
echo ""
echo "Images:"
echo "  $ECR_REGISTRY/dhcs-bht/agent-api:latest"
echo "  $ECR_REGISTRY/dhcs-bht/dashboard:latest"
echo "  $ECR_REGISTRY/dhcs-bht/generator:latest"
echo ""
