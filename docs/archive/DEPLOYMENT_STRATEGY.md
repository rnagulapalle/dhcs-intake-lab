# Industry-Standard Deployment Strategy for DHCS BHT

## Current Situation Analysis

### What We Have:
- ✅ ECS Cluster: `dhcs-bht-demo-cluster` (ACTIVE)
- ✅ ECS Service: `dhcs-bht-demo-service` (ACTIVE, but 0 running tasks)
- ✅ Load Balancer: `dhcs-bht-demo-alb` (active)
- ✅ ECR Repository: `dhcs-bht-demo-api`
- ⚠️ Issue: Docker image built for ARM64, AWS ECS runs AMD64

### Root Cause:
Building on Mac (ARM64) but deploying to AWS Fargate (AMD64/x86_64) causes platform mismatch.

---

## Industry-Standard Deployment Patterns (Research)

### 1. **AWS Best Practices** (AWS Well-Architected Framework)

**Build Pipeline:**
```
Developer Machine → Git Push → CI/CD Pipeline → AWS
                                      ↓
                            Build in Cloud (AMD64)
                                      ↓
                            Push to ECR → Deploy to ECS
```

**Benefits:**
- Builds happen in cloud (correct architecture)
- No local machine dependencies
- Consistent, repeatable builds
- Automated testing before deploy

### 2. **Industry Standard Tools**

#### Option A: **GitHub Actions** (Most Popular for Startups)
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS ECS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest  # AMD64 by default
    steps:
      - Checkout code
      - Build Docker image (AMD64)
      - Push to ECR
      - Update ECS service
```

**Pros:**
- Free for public repos, 2000 min/month private
- Native AMD64 runners
- Easy to set up
- Industry standard

**Cons:**
- Need GitHub secrets for AWS credentials
- ~5 min per deployment

#### Option B: **AWS CodePipeline** (AWS Native)
```
CodeCommit/GitHub → CodeBuild → ECR → ECS Deploy
```

**Pros:**
- Fully AWS integrated
- No GitHub needed
- IAM-based security
- AWS-optimized

**Cons:**
- More complex setup
- Costs $1/pipeline/month + build time
- AWS vendor lock-in

#### Option C: **Docker Buildx with Multi-Platform** (Current Approach)
```bash
docker buildx build --platform linux/amd64,linux/arm64 --push ...
```

**Pros:**
- Works from local machine
- No CI/CD setup needed
- Immediate deployment

**Cons:**
- SLOW (10-20 min for cross-compilation)
- Resource intensive
- Not scalable for team

#### Option D: **AWS CDK** (Infrastructure as Code)
```typescript
// Define infrastructure in code
const cluster = new ecs.Cluster(...)
const service = new ecs.FargateService(...)

// Deploy with: cdk deploy
```

**Pros:**
- Infrastructure versioned in Git
- Repeatable deployments
- Type-safe (TypeScript)
- AWS best practices built-in

**Cons:**
- Initial setup time
- Learning curve
- Still need image built for AMD64

---

## Recommended Approach: **Hybrid (Best for Your Situation)**

### Phase 1: Quick Fix (Today) - Build AMD64 in Cloud

Use **AWS CodeBuild** to build the image (no GitHub Actions setup needed):

```bash
# Create buildspec.yml
version: 0.2
phases:
  build:
    commands:
      - docker build -t $IMAGE_URI -f deployment/minimal/Dockerfile .
      - docker push $IMAGE_URI
```

**Why:**
- Builds in AWS (AMD64 native)
- Fast (~3 min)
- No local cross-compilation

### Phase 2: Automate (Next Week) - GitHub Actions

Set up simple CI/CD:

```yaml
name: Deploy
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aws-actions/configure-aws-credentials@v2
      - run: |
          docker build -f deployment/minimal/Dockerfile -t $ECR_URI:latest .
          docker push $ECR_URI:latest
          aws ecs update-service --cluster dhcs-bht-demo-cluster --service dhcs-bht-demo-service --force-new-deployment
```

**Why:**
- Automated on every push
- Team-friendly
- Industry standard

### Phase 3: Production (Future) - CDK + CI/CD

Full infrastructure as code with automated deployments.

---

## Safeguards Before Deployment

### 1. **Pre-Deployment Checks**
```bash
# ✅ Check AWS credentials
aws sts get-caller-identity

# ✅ Check existing resources
aws ecs describe-services --cluster dhcs-bht-demo-cluster --services dhcs-bht-demo-service

# ✅ Verify Docker daemon running
docker ps

# ✅ Check disk space
df -h | grep -E "/$"  # Need 10GB+ free
```

### 2. **Build Validation**
```bash
# ✅ Build locally first (test)
docker build -f deployment/minimal/Dockerfile -t test:local .

# ✅ Run container locally
docker run -p 8000:8000 test:local

# ✅ Test health endpoint
curl http://localhost:8000/health
```

### 3. **Deployment Safety**
```bash
# ✅ Tag images with version (not just 'latest')
docker tag IMAGE $ECR_URI:v1.0.0
docker tag IMAGE $ECR_URI:latest

# ✅ Keep old task definition (rollback capability)
aws ecs describe-task-definition --task-definition dhcs-bht-demo-task:1 > backup.json

# ✅ Monitor deployment
aws ecs wait services-stable --cluster dhcs-bht-demo-cluster --services dhcs-bht-demo-service
```

### 4. **Rollback Plan**
```bash
# If deployment fails:
aws ecs update-service \
  --cluster dhcs-bht-demo-cluster \
  --service dhcs-bht-demo-service \
  --task-definition dhcs-bht-demo-task:1  # Previous version
```

### 5. **Cost Monitoring**
```bash
# Set up budget alert (already done)
# Monitor daily:
aws ce get-cost-and-usage --time-period Start=$(date -u -d "1 day ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) --granularity DAILY --metrics BlendedCost
```

---

## TODAY'S DEPLOYMENT PLAN

### Approach: Use EC2 Instance for AMD64 Build

**Why EC2?**
- Native AMD64 environment
- Fast builds (no cross-compilation)
- Can reuse for CI/CD later
- Cost: ~$0.10/hour (t4g.micro spot)

**Steps:**

1. **Launch EC2 build instance** (t4g.micro, Amazon Linux 2)
2. **Install Docker on EC2**
3. **Clone repo on EC2**
4. **Build Docker image on EC2** (native AMD64)
5. **Push to ECR from EC2**
6. **Update ECS service**
7. **Terminate EC2 instance** (save cost)

**Alternative: Use AWS CodeBuild**
- Managed service
- No EC2 management
- Pay per minute ($0.005/min)
- ~3 min build = $0.015

---

## Decision Matrix

| Approach | Time | Cost | Complexity | Scalability |
|----------|------|------|------------|-------------|
| **Local Buildx (current)** | 20 min | $0 | Low | ❌ |
| **EC2 Build** | 5 min | $0.10 | Low | ⚠️ |
| **AWS CodeBuild** | 3 min | $0.02 | Medium | ✅ |
| **GitHub Actions** | 5 min | Free | Medium | ✅ |
| **AWS CDK** | 10 min | $0.02 | High | ✅✅ |

---

## RECOMMENDED: AWS CodeBuild (Quick & Clean)

### Why CodeBuild?
1. ✅ Native AMD64 build environment
2. ✅ Fast (3-5 minutes)
3. ✅ Cheap ($0.015 per build)
4. ✅ No EC2 management
5. ✅ Easy to convert to CI/CD later

### Implementation:

```bash
# 1. Create buildspec.yml
# 2. Create CodeBuild project
# 3. Trigger build
# 4. Image auto-pushed to ECR
# 5. Update ECS service
```

**Total time:** 15 minutes setup + 3 minutes per build

---

## Alternative: Simplest Working Solution

### Use Pre-built Base Image Strategy

Instead of building from scratch, use a multi-stage build that leverages AMD64 base images:

```dockerfile
# Use official Python AMD64 image
FROM --platform=linux/amd64 python:3.11-slim

# Rest of Dockerfile...
```

Then build with:
```bash
docker build --platform linux/amd64 -f deployment/minimal/Dockerfile -t IMAGE .
```

**Docker will automatically pull AMD64 layers** (no cross-compilation needed)

---

## Final Recommendation for TODAY

**Use AWS CodeBuild** with the following steps:

1. Create buildspec.yml (2 min)
2. Create CodeBuild project via console (5 min)
3. Trigger build (3 min build time)
4. Update ECS service (1 min)
5. Test deployment (2 min)

**Total: 13 minutes**

**Cost: $0.015**

**Safeguards:**
- Build happens in AWS (correct platform)
- Can review build logs before deploying
- Can rollback to previous task definition
- Budget alerts already in place

---

## Next Steps (After Today)

1. **Week 1:** Set up GitHub Actions for auto-deployment
2. **Week 2:** Add automated tests in CI/CD
3. **Week 3:** Implement blue-green deployments
4. **Month 2:** Move to AWS CDK for full IaC

---

**Let me know which approach you want to proceed with:**
- A) AWS CodeBuild (recommended, 13 min)
- B) EC2 build instance (5 min, manual)
- C) Local Docker buildx with --load flag (20 min, we tried this)
- D) Something else?
