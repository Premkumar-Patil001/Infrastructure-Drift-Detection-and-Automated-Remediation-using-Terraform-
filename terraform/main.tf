resource "aws_security_group" "app_sg" {
  name        = "drift-demo-sg"
  description = "SG managed by Terraform - drift demo"

  # ONLY this SSH rule should exist
  # If ANY other rule appears = drift detected
  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.your_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "drift-demo-sg"
    ManagedBy   = "Terraform"    # ← Config rule uses this tag
    Environment = "lab"
  }
}
resource "aws_instance" "app_server" {
  ami             = "ami-0b6d9d3d33ba97d99"  
  instance_type   = "t3.micro"
  security_groups = [aws_security_group.app_sg.name]
  key_name     ="second"
  tags = {
    Name        = "drift-demo-ec2"
    ManagedBy   = "Terraform"
    Environment = "lab"
    # If someone adds Owner = "manual" via console
    # that is drift — Terraform didn't define it
  }
}

resource "aws_s3_bucket" "drift_bucket" {
  bucket = "drift-demo-bucket-prem-lab"

  tags = {
    Name      = "drift-demo-bucket"
    ManagedBy = "Terraform"
  }
}
