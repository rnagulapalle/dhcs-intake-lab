# AWS Minimal Deployment Checklist - DHCS BHT Demo

**Goal**: Deploy cost-optimized demo ($66-86/month) for stakeholder presentation

**Total Time**: 30-45 minutes (+ 15 min CloudFront propagation)

---

## Pre-Deployment Checklist

### ✅ 1. Local Environment Verified

- [ ] System running locally without errors
  ```bash
  cd /Users/raj/dhcs-intake-lab
  docker compose ps  # All services "Up"
  curl http://localhost:8000/health  # Returns {"status":"healthy"}
  ```

- [ ] OpenAI API key working
  ```bash
  grep OPENAI_API_KEY .env  # Should show valid key starting with sk-
  ```

### ✅ 2. AWS Account Setup

- [ ] AWS account created at https://aws.amazon.com/
- [ ] Credit card added (will be charged ~$66-86/month)
- [ ] AWS CLI installed
  ```bash
  # macOS
  brew install awscli

  # Verify
  aws --version  # Should show 2.x
  ```

- [ ] AWS credentials configured
  ```bash
  aws configure
  # Enter:
  # - AWS Access Key ID: [from IAM console]
  # - AWS Secret Access Key: [from IAM console]
  # - Region: us-west-2
  # - Output: json
  ```

- [ ] Test AWS connection
  ```bash
  aws sts get-caller-identity
  # Should return your account info
  ```

### ✅ 3. AWS IAM Permissions

Ensure your user/role has these services enabled:
- [ ] ECR (Elastic Container Registry)
- [ ] ECS (Elastic Container Service)
- [ ] IAM (to create roles)
- [ ] EC2 (for networking)
- [ ] ELB (Load Balancer)
- [ ] S3 (Storage)
- [ ] CloudFront (CDN)
- [ ] Secrets Manager
- [ ] CloudWatch Logs

**Quick check**: Your user should have `AdministratorAccess` policy for demo (not recommended for production)

### ✅ 4. Budget Alert

- [ ] Set up AWS Budget:
  ```bash
  # Via AWS Console:
  # Billing → Budgets → Create budget
  # - Type: Cost budget
  # - Amount: $120/month
  # - Alert threshold: 80% ($96)
  # - Email: [your-email]
  ```

### ✅ 5. Required Tools

- [ ] Docker installed
  ```bash
  docker --version  # 20.x+
  docker compose version  # 2.x+
  ```

- [ ] jq installed (for JSON parsing)
  ```bash
  # macOS
  brew install jq

  # Verify
  jq --version
  ```

- [ ] Node.js installed (for UI)
  ```bash
  node --version  # 18.x+
  npm --version
  ```

---

## Deployment Scripts Ready

All deployment scripts are in [AWS_MINIMAL_DEPLOYMENT.md](AWS_MINIMAL_DEPLOYMENT.md).

**Quick summary of what needs to be created**:

### 1. Backend Files (Need to Create)

- [ ] `deployment/minimal/Dockerfile` - Minimal container image
- [ ] `deployment/minimal/requirements-minimal.txt` - Slim dependencies
- [ ] `deployment/minimal/synthetic_data.db` - Pre-loaded SQLite database
- [ ] `deployment/deploy-minimal.sh` - Backend deployment script
- [ ] `deployment/teardown.sh` - Cleanup script

### 2. UI Files (Need to Create)

- [ ] `ui-modern/` - Next.js project
- [ ] `deployment/deploy-ui.sh` - UI deployment script

**These are detailed in [AWS_MINIMAL_DEPLOYMENT.md](AWS_MINIMAL_DEPLOYMENT.md) - I can create them when you're ready.**

---

## Deployment Steps (30-45 minutes)

### Phase 1: Deploy Backend to AWS (15 minutes)

- [ ] Make script executable
  ```bash
  chmod +x deployment/deploy-minimal.sh
  ```

- [ ] Run deployment
  ```bash
  ./deployment/deploy-minimal.sh
  ```

  **Watch for**:
  - ECR repository created ✓
  - Docker image built ✓
  - Image pushed to ECR ✓
  - ECS cluster created ✓
  - Service started ✓
  - Load balancer ready ✓

- [ ] Save the API URL from output
  ```bash
  # Script outputs:
  # "Your API is available at: http://dhcs-bht-demo-alb-XXXXXXX.us-west-2.elb.amazonaws.com"

  export API_URL="<paste-that-url>"
  echo $API_URL
  ```

- [ ] Wait for service to start (2-3 minutes)
  ```bash
  # Check status
  aws ecs describe-services \
    --cluster dhcs-bht-demo-cluster \
    --services dhcs-bht-demo-service \
    --query 'services[0].deployments[0].rolloutState' \
    --output text

  # Wait for "COMPLETED"
  ```

- [ ] Test API
  ```bash
  curl $API_URL/health
  # Should return: {"status":"healthy","plugins_loaded":3}
  ```

  ```bash
  curl -X POST $API_URL/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"How many events in the last hour?"}'
  # Should return AI response
  ```

### Phase 2: Build Modern UI (10 minutes)

- [ ] Create Next.js project
  ```bash
  cd ui-modern
  npx create-next-app@latest . --typescript --tailwind --app
  ```

- [ ] Install dependencies
  ```bash
  npm install framer-motion react-markdown recharts axios swr
  ```

- [ ] Copy UI components (I'll provide these files)
  - Components from [UI_MODERN_DESIGN.md](UI_MODERN_DESIGN.md)

- [ ] Configure API URL
  ```bash
  echo "NEXT_PUBLIC_API_URL=$API_URL" > .env.local
  ```

- [ ] Build for production
  ```bash
  npm run build
  ```

- [ ] Test locally
  ```bash
  npm run start &
  sleep 5
  curl http://localhost:3000
  # Should return HTML
  ```

### Phase 3: Deploy UI to S3/CloudFront (10 minutes)

- [ ] Make script executable
  ```bash
  cd ..
  chmod +x deployment/deploy-ui.sh
  ```

- [ ] Run UI deployment
  ```bash
  ./deployment/deploy-ui.sh
  ```

  **Watch for**:
  - S3 bucket created ✓
  - Files uploaded ✓
  - CloudFront distribution created ✓

- [ ] Save CloudFront URL from output
  ```bash
  # Script outputs:
  # "Your demo is available at: https://dXXXXXXXX.cloudfront.net"

  export DEMO_URL="<paste-that-url>"
  echo $DEMO_URL
  ```

- [ ] Wait for CloudFront propagation (10-15 minutes)
  ```bash
  # Check status
  aws cloudfront list-distributions \
    --query 'DistributionList.Items[0].Status' \
    --output text

  # Wait for "Deployed"
  ```

### Phase 4: Verify Everything Works (5 minutes)

- [ ] Open UI in browser
  ```bash
  # macOS
  open $DEMO_URL

  # Linux
  xdg-open $DEMO_URL

  # Or paste in browser manually
  ```

- [ ] Test UI functionality:
  - [ ] Page loads (dark mode by default)
  - [ ] Chat input works
  - [ ] Quick actions visible
  - [ ] Send test message: "How many high-risk events?"
  - [ ] AI responds with data
  - [ ] Source citations show up
  - [ ] Dark/light toggle works
  - [ ] Resize browser (mobile view works)

- [ ] Check CloudWatch logs (for any errors)
  ```bash
  aws logs tail /ecs/dhcs-bht-demo --follow
  ```

---

## Post-Deployment

### ✅ Document Deployment Info

- [ ] Create deployment info file
  ```bash
  cat > DEPLOYMENT_INFO.txt <<EOF
  DHCS BHT Demo - Deployment Information
  ======================================

  Deployed: $(date)

  Demo URL: $DEMO_URL
  API URL: $API_URL

  AWS Resources:
  - Region: us-west-2
  - ECS Cluster: dhcs-bht-demo-cluster
  - ECS Service: dhcs-bht-demo-service
  - Load Balancer: dhcs-bht-demo-alb

  Estimated Cost: \$66-86/month

  Management:
  -----------
  # Stop service (saves ~\$15/mo)
  aws ecs update-service --cluster dhcs-bht-demo-cluster --service dhcs-bht-demo-service --desired-count 0

  # Restart service
  aws ecs update-service --cluster dhcs-bht-demo-cluster --service dhcs-bht-demo-service --desired-count 1

  # View logs
  aws logs tail /ecs/dhcs-bht-demo --follow

  # Delete everything
  ./deployment/teardown.sh
  EOF

  cat DEPLOYMENT_INFO.txt
  ```

### ✅ Share with Stakeholders

- [ ] Email demo link: `$DEMO_URL`
- [ ] Include note: "This is a minimal demo deployment running on AWS"
- [ ] Schedule demo meeting (15 minutes)

### ✅ Prepare Demo Script

- [ ] Review demo script in [AWS_MINIMAL_DEPLOYMENT.md](AWS_MINIMAL_DEPLOYMENT.md)
- [ ] Practice 2-3 times
- [ ] Take backup screenshots (in case of network issues)

---

## Daily Maintenance (During Demo Period)

### Quick Health Check

```bash
# Check API
curl $API_URL/health

# Check UI
curl -I $DEMO_URL  # Should return 200 OK

# Check ECS service
aws ecs describe-services \
  --cluster dhcs-bht-demo-cluster \
  --services dhcs-bht-demo-service \
  --query 'services[0].runningCount'
# Should return: 1
```

### Check Costs

```bash
# View today's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d "1 day ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Should be ~$2-3 per day
```

### Cost Optimization

**When not demoing** (saves ~$15/month):
```bash
# Stop service
aws ecs update-service \
  --cluster dhcs-bht-demo-cluster \
  --service dhcs-bht-demo-service \
  --desired-count 0

# Restart before demo
aws ecs update-service \
  --cluster dhcs-bht-demo-cluster \
  --service dhcs-bht-demo-service \
  --desired-count 1

# Wait 2-3 minutes for service to start
```

---

## Troubleshooting

### Issue: Service won't start

```bash
# View task details
aws ecs describe-tasks \
  --cluster dhcs-bht-demo-cluster \
  --tasks $(aws ecs list-tasks --cluster dhcs-bht-demo-cluster --query 'taskArns[0]' --output text) \
  --query 'tasks[0].containers[0].reason'

# View logs
aws logs tail /ecs/dhcs-bht-demo --follow

# Common fixes:
# 1. Check OpenAI key in Secrets Manager
# 2. Restart service:
aws ecs update-service \
  --cluster dhcs-bht-demo-cluster \
  --service dhcs-bht-demo-service \
  --force-new-deployment
```

### Issue: UI shows "Connection Error"

```bash
# Verify API is responding
curl $API_URL/health

# Check CORS headers
curl -I -X OPTIONS $API_URL/chat

# Common fix: Wait 2-3 minutes for service to fully start
```

### Issue: High costs

```bash
# Check what's expensive
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d "7 days ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Common issues:
# 1. Running multiple tasks (should be 1)
# 2. Not using Fargate Spot
# 3. OpenAI API usage high

# Fix: Check task count
aws ecs describe-services \
  --cluster dhcs-bht-demo-cluster \
  --services dhcs-bht-demo-service \
  --query 'services[0].desiredCount'
```

### Issue: CloudFront not serving UI

```bash
# Check distribution status
aws cloudfront list-distributions \
  --query 'DistributionList.Items[0].{Status:Status,DomainName:DomainName}'

# Common fix: Wait 10-15 minutes for propagation
# Or clear browser cache
```

---

## Teardown (After Demo)

When you're done and want to delete everything:

- [ ] Run teardown script
  ```bash
  ./deployment/teardown.sh
  ```

  **This deletes**:
  - ECS Service and Cluster
  - Load Balancer
  - CloudFront Distribution (takes 20-30 min)
  - S3 Bucket
  - ECR Repository
  - Security Groups
  - IAM Roles
  - Secrets

- [ ] Verify deletion
  ```bash
  aws ecs list-clusters  # Should be empty
  aws elbv2 describe-load-balancers  # Should be empty
  aws s3 ls  # DHCS bucket should be gone
  ```

- [ ] Check final costs (24 hours later)
  ```bash
  aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d "1 day ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity DAILY \
    --metrics BlendedCost
  ```

---

## Success Criteria

Before presenting to stakeholders, verify:

- [ ] ✅ API health check returns 200 OK
- [ ] ✅ UI loads in < 3 seconds
- [ ] ✅ Chat query returns response in < 10 seconds
- [ ] ✅ Dark/light mode works
- [ ] ✅ Quick actions work
- [ ] ✅ Mobile view renders correctly
- [ ] ✅ Source citations visible
- [ ] ✅ No browser console errors
- [ ] ✅ Demo script practiced
- [ ] ✅ Costs < $3/day ($90/month)
- [ ] ✅ Backup screenshots ready

---

## What to Tell Stakeholders

**Key Messages**:

1. **Cost-Effective**: "This demo costs **$66-86/month** on AWS - that's **95% cheaper** than full production while showing all capabilities."

2. **Scalable**: "When ready for production, we can scale to handle millions of events by adjusting a few settings."

3. **Modern**: "Built with latest AI agent technology (LangChain, GPT-4) and pluggable architecture."

4. **Real-time**: "Processes crisis events in real-time, provides insights in seconds."

5. **Extensible**: "Easy to add new use cases - policy Q&A, infrastructure tracking - without changing core system."

**Demo Duration**: 15 minutes (10 min demo + 5 min Q&A)

---

## Timeline Summary

| Phase | Duration |
|-------|----------|
| Pre-flight checks | 10 min |
| Deploy backend | 15 min |
| Build UI | 10 min |
| Deploy UI | 10 min |
| Verification | 5 min |
| **Total (hands-on)** | **50 min** |
| CloudFront wait | +15 min (parallel) |
| **Total (wall clock)** | **~65 min** |

---

## Next Steps

1. **[ ] Create deployment files** - Tell me when you're ready and I'll create all the needed files
2. **[ ] Run pre-flight checks** - Verify AWS account and tools
3. **[ ] Deploy backend** - Run deploy-minimal.sh
4. **[ ] Build & deploy UI** - Run deploy-ui.sh
5. **[ ] Verify & test** - Ensure everything works
6. **[ ] Demo to stakeholders** - Show the value!

---

**Ready to start?** Let me know and I'll create all the deployment files for you.

**Questions?** Everything is documented in:
- [AWS_MINIMAL_DEPLOYMENT.md](AWS_MINIMAL_DEPLOYMENT.md) - Complete deployment guide
- [UI_MODERN_DESIGN.md](UI_MODERN_DESIGN.md) - UI design specifications
- [PLUGGABLE_ARCHITECTURE.md](PLUGGABLE_ARCHITECTURE.md) - How to add new use cases
