from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Call Analyzer API",
    description="Call summarization and analysis service for SMBs",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
s3_client = boto3.client("s3")
transcribe_client = boto3.client("transcribe")
bedrock_client = boto3.client("bedrock-runtime")
comprehend_client = boto3.client("comprehend")
dynamodb = boto3.resource("dynamodb")

@app.get("/")
async def root():
    return {"message": "Call Analyzer API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload-call")
async def upload_call(file: UploadFile = File(...)):
    """Upload call audio file to S3"""
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")
        key = f"calls/{file.filename}"
        
        s3_client.upload_fileobj(file.file, bucket_name, key)
        
        return {
            "message": "File uploaded successfully",
            "s3_key": key,
            "bucket": bucket_name
        }
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)