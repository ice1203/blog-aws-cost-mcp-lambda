import json
import httpx
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    """AWS Lambda function to retrieve pricing information from AWS pricing webpage.
    
    Args:
        event (dict): The Lambda event object containing the service code
                      Expected format: {"service_code": "lambda"}
        context (dict): AWS Lambda context object
        
    Returns:
        dict: Pricing information if found, otherwise an error message
    """
    try:
        # Extract service code from the event
        service_code = event.get('service_code')
        
        if not service_code:
            return {
                'status': 'error',
                'message': 'Missing service_code parameter'
            }
            
        # サービスコードの前処理
        for prefix in ['Amazon', 'AWS']:
            if service_code.startswith(prefix):
                service_code = service_code[len(prefix):].lower()
        service_code = service_code.lower().strip()
        
        # AWSの価格ページにアクセス
        url = f'https://aws.amazon.com/{service_code}/pricing'
        response = httpx.get(url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
        
        # HTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # スクリプトとスタイル要素を削除
        for script in soup(['script', 'style']):
            script.decompose()
            
        # テキストコンテンツを抽出
        text = soup.get_text()
        
        # 行に分割して各行の先頭と末尾の空白を削除
        lines = (line.strip() for line in text.splitlines())
        
        # 複数行の見出しを1行ずつに分割
        chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
        
        # 空行を削除
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 結果を返す
        return {
            'status': 'success',
            'service_name': service_code,
            'data': text,
            'message': f'Retrieved pricing for {service_code} from AWS Pricing url',
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }
