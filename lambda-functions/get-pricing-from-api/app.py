import json
import boto3

def lambda_handler(event, context):
    """AWS Lambda function to retrieve pricing information from AWS Price List API.
    
    Args:
        event (dict): The Lambda event object containing the service code and region
                      Expected format: {"service_code": "AmazonS3", "region": "us-east-1"}
        context (dict): AWS Lambda context object
        
    Returns:
        dict: Pricing information if found, otherwise an error message
    """
    try:
        # Extract parameters from the event
        service_code = event.get('service_code')
        region = event.get('region')
        
        if not service_code:
            return {
                'status': 'error',
                'error_type': 'missing_parameter',
                'message': 'Missing service_code parameter'
            }
            
        if not region:
            return {
                'status': 'error',
                'error_type': 'missing_parameter',
                'message': 'Missing region parameter'
            }
        
        # AWS Pricing APIクライアントを初期化
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        
        # APIリクエスト
        response = pricing_client.get_products(
            ServiceCode=service_code,
            Filters=[{'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region}],
            MaxResults=100,
        )
        
        # 結果の確認
        if not response['PriceList']:
            return {
                'status': 'error',
                'error_type': 'empty_results',
                'message': f'The service code "{service_code}" did not return any pricing data. AWS service codes typically follow patterns like "AmazonS3", "AmazonEC2", "AmazonES", etc. Please check the exact service code and try again.',
                'examples': {
                    'OpenSearch': 'AmazonES',
                    'Lambda': 'AWSLambda',
                    'DynamoDB': 'AmazonDynamoDB',
                    'Bedrock': 'AmazonBedrock',
                },
            }
        
        # 結果を返す
        return {
            'status': 'success',
            'service_name': service_code,
            'data': response['PriceList'],
            'message': f'Retrieved pricing for {service_code} in {region} from AWS Pricing API',
        }
    except Exception as e:
        error_msg = str(e)
        return {
            'status': 'error',
            'error_type': 'api_error',
            'message': error_msg,
            'service_code': service_code,
            'region': region,
            'note': 'AWS service codes typically follow patterns like "AmazonS3", "AmazonEC2", "AmazonES" (for OpenSearch), etc.',
        }
