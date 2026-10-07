output "ec2_id" {
  value = aws_instance.app_server.id
}

output "sg_id" {
  value = aws_security_group.app_sg.id
}

output "s3_bucket" {
  value = aws_s3_bucket.drift_bucket.bucket
}