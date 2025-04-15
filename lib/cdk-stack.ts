import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaPython from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export class CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Lambda関数のデプロイ
    
    // 1. get-pricing-from-web Lambda関数
    const getPricingFromWebLambda = new lambdaPython.PythonFunction(this, 'GetPricingFromWebLambda', {
      entry: path.join(__dirname, '../lambda-functions/get-pricing-from-web'),
      index: 'app.py',
      handler: 'lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      functionName: 'get_pricing_from_web',
      description: 'Retrieves pricing information from AWS pricing webpages. Input: service_code (required). Output: status, service_name, data, message. Example: {"service_code":"lambda"}. Note: Requires internet access. Use when structured API data is unavailable.',
      environment: {
        // 必要に応じて環境変数を追加
      },
    });
    cdk.Tags.of(getPricingFromWebLambda).add('MCP_Tool', 'cost-analysis') 

    // 2. get-pricing-from-api Lambda関数
    const getPricingFromApiLambda = new lambdaPython.PythonFunction(this, 'GetPricingFromApiLambda', {
      entry: path.join(__dirname, '../lambda-functions/get-pricing-from-api'),
      index: 'app.py',
      handler: 'lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      functionName: 'get_pricing_from_api',
      description: 'Fetches pricing data from AWS Price List API. Input: service_code (required), region (required). Output: status, service_name, data, message. Example: {"service_code":"AWSLambda","region":"us-east-1"}. Provides structured pricing information.',
      environment: {
        // 必要に応じて環境変数を追加
      },
    });
    cdk.Tags.of(getPricingFromApiLambda).add('MCP_Tool', 'cost-analysis') 

    // AWS Price List APIへのアクセス権限を追加
    getPricingFromApiLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['pricing:GetProducts'],
        resources: ['*'],
      })
    );

    // 3. generate-cost-report Lambda関数
    const generateCostReportLambda = new lambdaPython.PythonFunction(this, 'GenerateCostReportLambda', {
      entry: path.join(__dirname, '../lambda-functions/generate-cost-report'),
      index: 'app.py',
      handler: 'lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
      memorySize: 512,
      timeout: cdk.Duration.seconds(60),
      functionName: 'generate_cost_report',
      description: 'Generates detailed cost analysis reports from AWS pricing data. Input: pricing_data (required), service_name (required), optional parameters. Output: status, report, message. Includes cost breakdown, scaling analysis, and optimization recommendations.',
      environment: {
        // 必要に応じて環境変数を追加
      },
    });
    cdk.Tags.of(generateCostReportLambda).add('MCP_Tool', 'cost-analysis') 


    // Lambda関数のARNをスタック出力として追加
    new cdk.CfnOutput(this, 'GetPricingFromWebLambdaArn', {
      value: getPricingFromWebLambda.functionArn,
      description: 'ARN of the GetPricingFromWeb Lambda function',
      exportName: 'GetPricingFromWebLambdaArn',
    });

    new cdk.CfnOutput(this, 'GetPricingFromApiLambdaArn', {
      value: getPricingFromApiLambda.functionArn,
      description: 'ARN of the GetPricingFromApi Lambda function',
      exportName: 'GetPricingFromApiLambdaArn',
    });

    new cdk.CfnOutput(this, 'GenerateCostReportLambdaArn', {
      value: generateCostReportLambda.functionArn,
      description: 'ARN of the GenerateCostReport Lambda function',
      exportName: 'GenerateCostReportLambdaArn',
    });
  }
}
