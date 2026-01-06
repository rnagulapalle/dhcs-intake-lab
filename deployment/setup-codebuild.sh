#!/bin/bash
set -e

echo "🏗️  Setting up AWS CodeBuild for DHCS BHT"
echo "=========================================="
echo ""

# Variables
AWS_REGION="us-west-2"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="dhcs-bht-demo"
CODEBUILD_PROJECT="${PROJECT_NAME}-build"
SERVICE_ROLE_NAME="${PROJECT_NAME}-codebuild-role"

echo "📋 Configuration:"
echo "   AWS Account: $AWS_ACCOUNT"
echo "   Region: $AWS_REGION"
echo "   CodeBuild Project: $CODEBUILD_PROJECT"
echo ""

# 1. Store AWS Account ID in Parameter Store (for buildspec.yml)
echo "📦 Step 1/4: Storing AWS Account ID in Parameter Store..."
aws ssm put-parameter \
  --name "/codebuild/account-id" \
  --value "$AWS_ACCOUNT" \
  --type "String" \
  --overwrite \
  2>/dev/null && echo "   Parameter stored" || echo "   Parameter already exists"
echo ""

# 2. Create IAM role for CodeBuild
echo "🔑 Step 2/4: Creating CodeBuild service role..."

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "codebuild.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}'

aws iam create-role \
  --role-name $SERVICE_ROLE_NAME \
  --assume-role-policy-document "$TRUST_POLICY" \
  2>/dev/null && echo "   Role created" || echo "   Role already exists"

# Attach necessary policies
aws iam attach-role-policy \
  --role-name $SERVICE_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser \
  2>/dev/null || true

aws iam attach-role-policy \
  --role-name $SERVICE_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess \
  2>/dev/null || true

# Create inline policy for SSM and S3
INLINE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameters", "ssm:GetParameter"],
      "Resource": "arn:aws:ssm:'$AWS_REGION':'$AWS_ACCOUNT':parameter/codebuild/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::codepipeline-'$AWS_REGION'-*/*"
    }
  ]
}'

aws iam put-role-policy \
  --role-name $SERVICE_ROLE_NAME \
  --policy-name "${PROJECT_NAME}-codebuild-policy" \
  --policy-document "$INLINE_POLICY" \
  2>/dev/null || true

ROLE_ARN=$(aws iam get-role --role-name $SERVICE_ROLE_NAME --query 'Role.Arn' --output text)
echo "   Role ARN: $ROLE_ARN"
echo ""

# Wait for IAM role to propagate
echo "⏳ Waiting for IAM role to propagate (10 seconds)..."
sleep 10
echo ""

# 3. Create CodeBuild project
echo "🏗️  Step 3/4: Creating CodeBuild project..."

# Check if project exists
PROJECT_EXISTS=$(aws codebuild list-projects --query "projects[?contains(@, '$CODEBUILD_PROJECT')]" --output text)

if [ -z "$PROJECT_EXISTS" ]; then
  aws codebuild create-project \
    --name $CODEBUILD_PROJECT \
    --description "Build DHCS BHT Multi-Agent Docker images" \
    --source type=S3 \
    --artifacts type=NO_ARTIFACTS \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:7.0,computeType=BUILD_GENERAL1_SMALL,privilegedMode=true \
    --service-role $ROLE_ARN \
    --region $AWS_REGION
  echo "   CodeBuild project created"
else
  echo "   CodeBuild project already exists"
fi

echo ""

# 4. Create a zip of the source code for CodeBuild
echo "📦 Step 4/4: Preparing source code for CodeBuild..."
TEMP_DIR=$(mktemp -d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SOURCE_ZIP="/tmp/dhcs-bht-source-${TIMESTAMP}.zip"

echo "   Creating source archive..."
# Create zip excluding unnecessary files
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
echo "   Source archive created: $SOURCE_ZIP ($SOURCE_SIZE)"
echo ""

echo "✅ CodeBuild Setup Complete!"
echo "=============================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start a build manually:"
echo "   aws codebuild start-build --project-name $CODEBUILD_PROJECT \\"
echo "     --source-version main \\"
echo "     --source-location-override \$(pwd) \\"
echo "     --environment-variables-override \\"
echo "       name=AWS_ACCOUNT_ID,value=$AWS_ACCOUNT,type=PLAINTEXT \\"
echo "       name=AWS_DEFAULT_REGION,value=$AWS_REGION,type=PLAINTEXT \\"
echo "       name=IMAGE_REPO_NAME,value=dhcs-bht-demo-api,type=PLAINTEXT"
echo ""
echo "2. Or use the trigger script:"
echo "   ./deployment/trigger-build.sh"
echo ""
echo "3. Monitor the build:"
echo "   aws codebuild list-builds-for-project --project-name $CODEBUILD_PROJECT"
echo ""
echo "📊 CodeBuild Console:"
echo "   https://console.aws.amazon.com/codesuite/codebuild/projects/$CODEBUILD_PROJECT?region=$AWS_REGION"
echo ""
