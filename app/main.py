from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import boto3
from botocore.exceptions import ClientError
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

from app.database import get_db, create_tables, Call, Transcription, Summary
from app.models import CallResponse, CallDetail, ActionItem

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
action_items_table = dynamodb.Table(os.getenv("DYNAMODB_TABLE", "call-analyzer-action-items"))

# Initialize database
create_tables()

@app.get("/")
async def root():
    return {"message": "Call Analyzer API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload-call", response_model=CallResponse)
async def upload_call(
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload call audio file and start processing"""
    try:
        # Upload to S3
        bucket_name = os.getenv("S3_BUCKET_NAME")
        file_id = str(uuid.uuid4())
        key = f"calls/{file_id}/{file.filename}"
        
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        s3_client.upload_fileobj(file.file, bucket_name, key)
        
        # Create call record in database
        call = Call(
            filename=file.filename,
            s3_key=key,
            status="uploaded",
            file_size_bytes=file_size
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        
        # Start background processing
        background_tasks.add_task(process_call, call.id, bucket_name, key)
        
        return CallResponse(
            id=call.id,
            filename=call.filename,
            status=call.status,
            upload_timestamp=call.upload_timestamp
        )
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

async def process_call(call_id: int, bucket_name: str, s3_key: str):
    """Background task to process call: transcribe -> analyze -> extract actions"""
    db = next(get_db())
    
    try:
        # Update status to transcribing
        call = db.query(Call).filter(Call.id == call_id).first()
        call.status = "transcribing"
        db.commit()
        
        # Start transcription job
        job_name = f"transcribe-{call_id}-{uuid.uuid4().hex[:8]}"
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket_name}/{s3_key}'},
            MediaFormat='mp3',  # Adjust based on your file types
            LanguageCode='en-US'
        )
        
        # Wait for transcription (in production, use SQS/SNS)
        import time
        while True:
            job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            status = job['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get transcription text
                transcript_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                import urllib.request
                with urllib.request.urlopen(transcript_uri) as response:
                    transcript_data = json.loads(response.read())
                    transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                
                # Save transcription
                transcription = Transcription(
                    call_id=call_id,
                    transcription_text=transcript_text,
                    transcription_job_name=job_name
                )
                db.add(transcription)
                
                # Update call status
                call.status = "processing"
                db.commit()
                
                # Generate summary and actions
                await generate_summary_and_actions(call_id, transcript_text, db)
                break
                
            elif status == 'FAILED':
                call.status = "failed"
                db.commit()
                break
                
            time.sleep(10)
            
    except Exception as e:
        print(f"Error processing call {call_id}: {str(e)}")
        call = db.query(Call).filter(Call.id == call_id).first()
        call.status = "failed"
        db.commit()
    finally:
        db.close()

async def generate_summary_and_actions(call_id: int, transcript_text: str, db: Session):
    """Generate summary and extract action items using AI"""
    try:
        # Generate summary using Amazon Bedrock
        summary_prompt = f"""Analyze this call transcript and provide:
1. A concise summary (2-3 sentences)
2. Key topics discussed
3. Overall sentiment

Transcript: {transcript_text}

Respond in JSON format:
{{
  "summary": "summary text",
  "topics": ["topic1", "topic2"],
  "sentiment": "positive/negative/neutral"
}}"""
        
        # Call Bedrock (using Claude)
        bedrock_response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": summary_prompt
                }]
            })
        )
        
        response_body = json.loads(bedrock_response['body'].read())
        ai_response = json.loads(response_body['content'][0]['text'])
        
        # Save summary
        summary = Summary(
            call_id=call_id,
            summary_text=ai_response['summary'],
            key_topics=json.dumps(ai_response['topics']),
            sentiment=ai_response['sentiment']
        )
        db.add(summary)
        
        # Extract action items
        actions_prompt = f"""Extract action items from this call transcript. For each action item, provide:
- A clear description
- Priority (high/medium/low)

Transcript: {transcript_text}

Respond in JSON format:
{{
  "actions": [
    {{"text": "action description", "priority": "high/medium/low"}}
  ]
}}"""
        
        actions_response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": actions_prompt
                }]
            })
        )
        
        actions_body = json.loads(actions_response['body'].read())
        actions_data = json.loads(actions_body['content'][0]['text'])
        
        # Save action items to DynamoDB
        for i, action in enumerate(actions_data['actions']):
            action_items_table.put_item(
                Item={
                    'call_id': str(call_id),
                    'action_id': str(uuid.uuid4()),
                    'action_text': action['text'],
                    'priority': action['priority'],
                    'status': 'pending',
                    'created_at': datetime.utcnow().isoformat()
                }
            )
        
        # Update call status to completed
        call = db.query(Call).filter(Call.id == call_id).first()
        call.status = "completed"
        db.commit()
        
    except Exception as e:
        print(f"Error generating summary for call {call_id}: {str(e)}")
        call = db.query(Call).filter(Call.id == call_id).first()
        call.status = "failed"
        db.commit()

@app.get("/calls", response_model=List[CallResponse])
async def get_calls(db: Session = Depends(get_db)):
    """Get all calls"""
    calls = db.query(Call).order_by(Call.upload_timestamp.desc()).all()
    return [CallResponse(
        id=call.id,
        filename=call.filename,
        status=call.status,
        upload_timestamp=call.upload_timestamp,
        duration_seconds=call.duration_seconds
    ) for call in calls]

@app.get("/calls/{call_id}", response_model=CallDetail)
async def get_call_detail(call_id: int, db: Session = Depends(get_db)):
    """Get detailed call information with transcript, summary, and actions"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Get transcription
    transcription = db.query(Transcription).filter(Transcription.call_id == call_id).first()
    
    # Get summary
    summary = db.query(Summary).filter(Summary.call_id == call_id).first()
    
    # Get actions from DynamoDB
    actions = []
    try:
        response = action_items_table.query(
            KeyConditionExpression='call_id = :call_id',
            ExpressionAttributeValues={':call_id': str(call_id)}
        )
        actions = response.get('Items', [])
    except Exception as e:
        print(f"Error fetching actions: {str(e)}")
    
    return CallDetail(
        id=call.id,
        filename=call.filename,
        status=call.status,
        upload_timestamp=call.upload_timestamp,
        duration_seconds=call.duration_seconds,
        transcription=transcription.transcription_text if transcription else None,
        summary=summary.summary_text if summary else None,
        key_topics=json.loads(summary.key_topics) if summary and summary.key_topics else None,
        sentiment=summary.sentiment if summary else None,
        actions=actions
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)