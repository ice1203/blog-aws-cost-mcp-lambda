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
      description: 'Get pricing information from AWS pricing webpage',
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
      description: 'Get pricing information from AWS Price List API',
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
      description: 'Generate a detailed cost analysis report',
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