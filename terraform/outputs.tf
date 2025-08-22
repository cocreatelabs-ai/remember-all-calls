output "s3_bucket_name" {
  description = "S3 bucket name for audio files"
  value       = aws_s3_bucket.call_audio.id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.main.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for action items"
  value       = aws_dynamodb_table.action_items.name
}