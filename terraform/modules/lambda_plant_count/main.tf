resource "aws_lambda_function" "plant_count_lambda" {
  function_name = "plant_count_lambda"
  handler       = "count_plants.lambda_handler"
  runtime       = "python3.9"
  timeout       = 10
  memory_size   = 128

  role     = aws_iam_role.lambda_execution_role.arn
  filename = data.archive_file.plant_count_lambda.output_path

  source_code_hash = data.archive_file.plant_count_lambda.output_base64sha256

  layers = [var.python_dependencies_layer_arn]

  environment {
    variables = {
      KASVISLUETTELO_CREDS = var.kasvisluettelo_creds,      
    }
  }
}


resource "aws_iam_role" "lambda_execution_role" {
  name = "plant_count_lambda_lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "plant_count_lambda_lambda_policy"
  role   = aws_iam_role.lambda_execution_role.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution_role.name
}


data "archive_file" "plant_count_lambda" {
  type        = "zip"
  source_dir  = "src/count_plants/"
  output_path = "deployment_zips/count_plants.zip"
}

data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = ["*"]
  }
  
}
