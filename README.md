# Call Analyzer

AI-powered call transcription, analysis, and action item extraction service for SMBs. Upload call recordings and automatically get transcripts, summaries, sentiment analysis, and actionable tasks.

## 🎯 Features

- **Audio Upload**: Support for MP3, WAV, M4A, MP4 audio files
- **AI Transcription**: Automatic speech-to-text using AWS Transcribe
- **Smart Analysis**: AI-powered summaries and sentiment analysis using Amazon Bedrock
- **Action Items**: Automatic extraction of tasks and follow-ups
- **Web Interface**: Beautiful Flask-based dashboard for managing calls
- **REST API**: FastAPI backend for programmatic access
- **Cloud Native**: Deployed on AWS ECS with PostgreSQL and DynamoDB

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask WebApp  │────│  FastAPI Backend│────│   AWS Services  │
│   (Port 5000)   │    │   (Port 8000)   │    │ Transcribe/Bedrock│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
    ┌─────────┐              ┌─────────┐              ┌─────────┐
    │   ECS   │              │   ECS   │              │   RDS   │
    │ Fargate │              │ Fargate │              │ postgres│
    └─────────┘              └─────────┘              └─────────┘
                                   │
                              ┌──────────┐
                              │ DynamoDB │
                              │ Actions  │
                              └──────────┘
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed
- Terraform installed
- uv (Python package manager)

### 1. Infrastructure Setup

```bash
# Clone the repository
git clone <repository-url>
cd remember-all-calls

# Configure variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your settings

# Deploy infrastructure
cd terraform
terraform init
terraform apply
```

### 2. Application Deployment

```bash
# Deploy the FastAPI backend
./deploy.sh

# Deploy the Flask webapp
./deploy-webapp.sh
```

### 3. Access Your Application

After deployment, get the IP addresses:

```bash
# Get webapp IP
aws ecs list-tasks --cluster call-analyzer --service-name call-analyzer-webapp --region us-east-1
aws ecs describe-tasks --cluster call-analyzer --tasks <TASK_ARN> --region us-east-1
aws ec2 describe-network-interfaces --network-interface-ids <ENI_ID> --region us-east-1

# Access the web interface
http://<WEBAPP_IP>:5000

# API documentation
http://<API_IP>:8000/docs
```

## 📱 Usage

### Web Interface
1. **Dashboard**: View all uploaded calls and their processing status
2. **Upload**: Upload new call recordings (drag & drop or file picker)
3. **Call Details**: View transcripts, summaries, and action items

### API Endpoints
- `POST /upload-call` - Upload audio file
- `GET /calls` - List all calls
- `GET /calls/{id}` - Get detailed call information
- `GET /health` - Health check

### Call Processing Flow
1. **Upload** → File stored in S3, call record created
2. **Transcription** → AWS Transcribe converts audio to text
3. **Analysis** → Amazon Bedrock generates summary and extracts action items
4. **Complete** → Results stored in PostgreSQL and DynamoDB

## 🛠️ Development

### Local Development

#### Backend (FastAPI)
```bash
cd app
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (Flask)
```bash
cd webapp
uv sync
export API_BASE_URL=http://localhost:8000
uv run python app.py
```

### Environment Variables

#### Backend (.env)
```bash
DB_HOST=your-rds-endpoint
DB_NAME=callanalyzer
DB_USER=your-db-username
DB_PASSWORD=your-db-password
S3_BUCKET_NAME=your-s3-bucket
DYNAMODB_TABLE=your-dynamodb-table
```

#### Frontend
```bash
API_BASE_URL=http://your-api-url:8000
```

### Database Schema

#### PostgreSQL Tables
- **calls**: Basic call information and status
- **transcriptions**: AI transcription results
- **summaries**: AI-generated summaries and analysis

#### DynamoDB Table
- **action_items**: Extracted tasks and follow-ups

## 🔧 Configuration

### AWS Services Used
- **ECS Fargate**: Container orchestration
- **RDS PostgreSQL**: Relational data storage  
- **DynamoDB**: Action items storage
- **S3**: Audio file storage
- **Transcribe**: Speech-to-text
- **Bedrock**: AI analysis (Claude)
- **Comprehend**: Sentiment analysis

### Required IAM Permissions
- ECS task execution and service management
- S3 read/write access
- RDS connectivity
- DynamoDB read/write
- Transcribe job management
- Bedrock model invocation

## 🔒 Security Considerations

### Current Setup (Development)
- ⚠️ Public IP access on non-standard ports
- ⚠️ Database credentials in environment variables
- ⚠️ CORS allows all origins

### Production Recommendations
- Use Application Load Balancer for standard HTTP/HTTPS
- Store secrets in AWS Secrets Manager
- Implement proper authentication (Cognito integration available)
- Configure specific CORS origins
- Use private subnets with NAT Gateway
- Enable AWS WAF protection

## 📊 Monitoring & Logs

### CloudWatch Logs
- ECS task logs: `/ecs/call-analyzer`
- Application logs include request/response details

### Health Checks
- Backend: `GET /health`
- Frontend: `GET /health`

## 🚢 Deployment Scripts

### `deploy.sh`
Builds and deploys the FastAPI backend:
- Docker build with platform targeting
- ECR push
- ECS service update

### `deploy-webapp.sh`
Builds and deploys the Flask webapp:
- Terraform infrastructure updates
- Docker build and ECR push
- ECS service deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Webapp not accessible**
- Check security group allows port 5000
- Verify ECS task has public IP assigned
- Check subnet has internet gateway route

**Database connection timeout**
- Verify RDS security group allows connections from ECS
- Check VPC networking configuration
- Ensure RDS is publicly accessible if needed

**Transcription failures**
- Verify IAM permissions for Transcribe service
- Check supported audio formats (MP3, WAV, M4A, MP4)
- Ensure S3 bucket policy allows Transcribe access

**AI analysis failures**  
- Confirm Bedrock model access permissions
- Check if Claude model is available in your region
- Verify request format and content limits

### Getting Help
- Check CloudWatch logs for detailed error messages
- Review ECS service events for deployment issues
- Use AWS CLI to debug resource configurations