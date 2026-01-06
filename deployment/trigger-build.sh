#!/bin/bash
set -e

echo "🚀 Triggering AWS CodeBuild"
echo "============================="
echo ""

# Variables
AWS_REGION="us-west-2"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="dhcs-bht-demo"
CODEBUILD_PROJECT="${PROJECT_NAME}-build"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-service"

echo "📋 Build Configuration:"
echo "   Project: $CODEBUILD_PROJECT"
echo "   Account: $AWS_ACCOUNT"
echo "   Region: $AWS_REGION"
echo ""

# Pre-flight checks
echo "✅ Pre-flight Checks:"
echo ""

# Check AWS credentials
echo -n "   Checking AWS credentials... "
aws sts get-caller-identity > /dev/null 2>&1 && echo "✓" || (echo "✗ Failed" && exit 1)

# Check Docker daemon
echo -n "   Checking Docker daemon... "
docker ps > /dev/null 2>&1 && echo "✓" || (echo "✗ Not running" && exit 1)

# Check CodeBuild project exists
echo -n "   Checking CodeBuild project... "
aws codebuild batch-get-projects --names $CODEBUILD_PROJECT > /dev/null 2>&1 && echo "✓" || (echo "✗ Not found. Run ./deployment/setup-codebuild.sh first" && exit 1)

# Check disk space (need at least 5GB free)
FREE_SPACE=$(df -k . | tail -1 | awk '{print $4}')
FREE_SPACE_GB=$((FREE_SPACE / 1024 / 1024))
echo "   Disk space available: ${FREE_SPACE_GB}GB"
if [ $FREE_SPACE_GB -lt 5 ]; then
  echo "   ⚠️  Warning: Low disk space (need 5GB+)"
fi

echo ""

# Create source bundle for CodeBuild
echo "📦 Creating source bundle..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SOURCE_ZIP="/tmp/dhcs-bht-source-${TIMESTAMP}.zip"

zip -r $SOURCE_ZIP . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pytest_cache*" \
  -x "*node_modules*" \
  -x "*.env*" \
  -x "*venv*" \
  -x "*.DS_Store" \
  -x "*data/*" \
  -x "*.log" \
  > /dev/null 2>&1

SOURCE_SIZE=$(du -h "$SOURCE_ZIP" | cut -f1)
echo "   Source bundle: $SOURCE_ZIP ($SOURCE_SIZE)"
echo ""

# Upload to S3 for CodeBuild
S3_BUCKET="codebuild-${AWS_REGION}-${AWS_ACCOUNT}-source"
S3_KEY="dhcs-bht/${TIMESTAMP}/source.zip"

echo "📤 Uploading source to S3..."
# Create bucket if it doesn't exist
aws s3 mb s3://$S3_BUCKET 2>/dev/null || true

aws s3 cp $SOURCE_ZIP s3://$S3_BUCKET/$S3_KEY
echo "   Uploaded to: s3://$S3_BUCKET/$S3_KEY"
echo ""

# Trigger CodeBuild
echo "🏗️  Starting CodeBuild..."
BUILD_OUTPUT=$(aws codebuild start-build \
  --project-name $CODEBUILD_PROJECT \
  --source-location-override "s3://$S3_BUCKET/$S3_KEY" \
  --source-type-override S3 \
  --environment-variables-override \
    name=AWS_ACCOUNT_ID,value=$AWS_ACCOUNT,type=PLAINTEXT \
    name=AWS_DEFAULT_REGION,value=$AWS_REGION,type=PLAINTEXT \
    name=IMAGE_REPO_NAME,value=dhcs-bht-demo-api,type=PLAINTEXT \
  --query 'build.[id,buildStatus]' \
  --output text)

BUILD_ID=$(echo $BUILD_OUTPUT | awk '{print $1}')
BUILD_STATUS=$(echo $BUILD_OUTPUT | awk '{print $2}')

echo "   Build ID: $BUILD_ID"
echo "   Status: $BUILD_STATUS"
echo ""

echo "⏳ Monitoring build progress..."
echo "   (This typically takes 3-5 minutes)"
echo ""

# Wait for build to complete
aws codebuild wait build-complete --ids $BUILD_ID 2>/dev/null &
WAIT_PID=$!

# Show live logs while waiting
sleep 5  # Give build time to start

LOG_GROUP="/aws/codebuild/$CODEBUILD_PROJECT"
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name $LOG_GROUP \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --query 'logStreams[0].logStreamName' \
  --output text 2>/dev/null)

if [ "$LOG_STREAM" != "None" ] && [ ! -z "$LOG_STREAM" ]; then
  echo "📋 Build logs:"
  echo "---"
  aws logs tail $LOG_GROUP --log-stream-names $LOG_STREAM --follow --format short &
  TAIL_PID=$!
fi

# Wait for completion
wait $WAIT_PID 2>/dev/null
WAIT_RESULT=$?

# Stop log tailing
if [ ! -z "$TAIL_PID" ]; then
  kill $TAIL_PID 2>/dev/null || true
fi

echo ""
echo "---"

# Get final build status
FINAL_STATUS=$(aws codebuild batch-get-builds \
  --ids $BUILD_ID \
  --query 'builds[0].buildStatus' \
  --output text)

if [ "$FINAL_STATUS" = "SUCCEEDED" ]; then
  echo "✅ Build SUCCEEDED!"
  echo ""

  # Update ECS service with new image
  echo "🚀 Deploying to ECS..."
  aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION \
    > /dev/null

  echo "   ECS service updated with new image"
  echo ""

  echo "⏳ Waiting for deployment to stabilize (2-3 minutes)..."
  aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION 2>/dev/null || true

  echo ""
  echo "✅ Deployment Complete!"
  echo "======================"
  echo ""

  # Get service status
  SERVICE_INFO=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'services[0].[runningCount,desiredCount,deployments[0].status]' \
    --output text)

  RUNNING_COUNT=$(echo $SERVICE_INFO | awk '{print $1}')
  DESIRED_COUNT=$(echo $SERVICE_INFO | awk '{print $2}')
  DEPLOYMENT_STATUS=$(echo $SERVICE_INFO | awk '{print $3}')

  echo "📊 Service Status:"
  echo "   Running tasks: $RUNNING_COUNT / $DESIRED_COUNT"
  echo "   Deployment status: $DEPLOYMENT_STATUS"
  echo ""

  # Get load balancer URL
  ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names "${PROJECT_NAME}-alb" \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

  echo "🌐 API Endpoint:"
  echo "   http://$ALB_DNS"
  echo ""
  echo "🧪 Test the deployment:"
  echo "   curl http://$ALB_DNS/health"
  echo ""

  # Cleanup
  echo "🧹 Cleaning up..."
  rm -f $SOURCE_ZIP
  echo "   Temporary files removed"
  echo ""

else
  echo "❌ Build FAILED: $FINAL_STATUS"
  echo ""
  echo "📋 View full logs:"
  echo "   aws logs tail $LOG_GROUP --follow"
  echo ""
  echo "🔍 Build details:"
  echo "   https://console.aws.amazon.com/codesuite/codebuild/projects/$CODEBUILD_PROJECT/build/$BUILD_ID?region=$AWS_REGION"
  echo ""
  exit 1
fi

echo "📊 CodeBuild Console:"
echo "   https://console.aws.amazon.com/codesuite/codebuild/projects/$CODEBUILD_PROJECT?region=$AWS_REGION"
echo ""
