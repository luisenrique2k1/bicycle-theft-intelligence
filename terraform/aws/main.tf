
# Private S3 bucket for bicycle theft raw data
resource "aws_s3_bucket" "bike_theft_data" {
  bucket_prefix = "bike-theft-intelligence-"

  tags = {
    Project     = "Bicycle Theft Intelligence"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "bike_theft_data" {
  bucket = aws_s3_bucket.bike_theft_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable bucket versioning
resource "aws_s3_bucket_versioning" "bike_theft_data" {
  bucket = aws_s3_bucket.bike_theft_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt stored objects with SSE-S3
resource "aws_s3_bucket_server_side_encryption_configuration" "bike_theft_data" {
  bucket = aws_s3_bucket.bike_theft_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
