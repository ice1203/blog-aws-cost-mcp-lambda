# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# This file is based on code originally provided by Amazon Web Services and has been modified.

import json
import re
import csv
import io
from typing import Any, Dict, List, Optional, Union, Tuple

class ServiceInfo:
    """サービスコスト情報のコンテナ"""
    def __init__(self, name, estimated_cost, usage, unit_pricing=None, 
                 usage_quantities=None, calculation_details=None, free_tier_info=None):
        self.name = name
        self.estimated_cost = estimated_cost
        self.usage = usage
        self.unit_pricing = unit_pricing
        self.usage_quantities = usage_quantities
        self.calculation_details = calculation_details
        self.free_tier_info = free_tier_info

class CostAnalysisHelper:
    """コスト分析のヘルパークラス"""
    
    @staticmethod
    def parse_pricing_data(pricing_data: Any, service_name: str, related_services: Optional[List[str]] = None) -> Dict:
        """価格データを解析して構造化された情報を返す"""
        pricing_structure = {
            'service_name': service_name,
            'service_description': '',
            'unit_pricing': [],
            'free_tier': '',
            'usage_levels': {'low': {}, 'medium': {}, 'high': {}},
            'key_cost_factors': [],
            'projected_costs': {},
            'recommendations': {'immediate': [], 'best_practices': []},
            'assumptions': []
        }

        # APIデータかウェブスクレイピングデータかを判定
        if isinstance(pricing_data.get('data'), str):
            # ウェブスクレイピングデータの処理
            text_data = pricing_data.get('data', '')
            
            # サービス説明の抽出
            description_patterns = [
                rf'{service_name.title()} is a fully managed service that (.*?)\.',
                rf'{service_name.title()} is a serverless service that (.*?)\.',
                rf'{service_name.title()} is an AWS service that (.*?)\.',
            ]
            
            for pattern in description_patterns:
                if match := re.search(pattern, text_data, re.IGNORECASE):
                    pricing_structure['service_description'] = match.group(1)
                    break
            
            # 価格情報の抽出
            price_section_match = re.search(
                r'(?:Pricing|Price|Costs?|Fees?)(.*?)(?:Free Tier|Features|Benefits|FAQs)',
                text_data,
                re.DOTALL | re.IGNORECASE,
            )
            
            if price_section_match:
                price_text = price_section_match.group(1)
                price_patterns = [
                    r'\$([\d,.]+) per ([\w\s-]+)',
                    r'([\w\s-]+) costs? \$([\d,.]+)',
                    r'([\w\s-]+): \$([\d,.]+)',
                ]
                
                for pattern in price_patterns:
                    for match in re.findall(pattern, price_text, re.IGNORECASE):
                        if len(match) == 2:
                            if pattern == price_patterns[0]:
                                price, unit = match
                            else:
                                unit, price = match
                            pricing_structure['unit_pricing'].append({
                                'unit': unit.strip(),
                                'price': f'${price.strip()}'
                            })

        else:
            # AWS Price List APIデータの処理
            price_list = pricing_data.get('data', [])
            if isinstance(price_list, list):
                for price_item in price_list[:5]:
                    if isinstance(price_item, str):
                        try:
                            price_data = json.loads(price_item)
                            terms = price_data.get('terms', {})
                            product = price_data.get('product', {})
                            
                            # サービス説明の抽出
                            if not pricing_structure['service_description'] and 'attributes' in product:
                                attrs = product['attributes']
                                if 'productFamily' in attrs and 'description' in attrs:
                                    pricing_structure['service_description'] = (
                                        f"{attrs['productFamily']} that {attrs['description']}"
                                    )
                            
                            # 価格情報の抽出
                            for term_type, term_values in terms.items():
                                for _, price_dimensions in term_values.items():
                                    for _, dimension in price_dimensions.items():
                                        if 'pricePerUnit' in dimension and 'unit' in dimension:
                                            unit = dimension['unit']
                                            price = dimension.get('pricePerUnit', {}).get('USD', 'N/A')
                                            description = dimension.get('description', '')
                                            pricing_structure['unit_pricing'].append({
                                                'unit': unit,
                                                'price': f'${price}',
                                                'description': description
                                            })
                        except (json.JSONDecodeError, KeyError):
                            continue

        # デフォルト値の設定
        if not pricing_structure['service_description']:
            pricing_structure['service_description'] = f'provides {service_name} functionality in the AWS cloud'

        # 使用レベルごとのコスト計算
        if pricing_structure['unit_pricing']:
            multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
            for level, multiplier in multipliers.items():
                level_costs = {}
                for price_item in pricing_structure['unit_pricing']:
                    unit = price_item['unit']
                    try:
                        price_str = price_item['price'].replace('$', '').replace(',', '')
                        price = float(price_str)
                        level_costs[unit] = f'${price * multiplier:.2f}'
                    except (ValueError, TypeError):
                        level_costs[unit] = 'Calculation not available'
                pricing_structure['usage_levels'][level] = level_costs

        # キーコスト要因の設定
        pricing_structure['key_cost_factors'] = CostAnalysisHelper.get_default_cost_factors(service_name)

        # プロジェクションコストの計算
        months = [1, 3, 6, 12]
        growth_rates = {
            'steady': 1.0,
            'moderate': 1.1,
            'rapid': 1.2,
        }

        # 中程度の使用量をベースラインとして使用
        baseline = 0
        for unit, cost in pricing_structure['usage_levels']['medium'].items():
            try:
                if isinstance(cost, str) and '$' in cost:
                    baseline += float(cost.replace('$', '').replace(',', ''))
            except (ValueError, TypeError):
                pass

        if baseline == 0:
            baseline = 100

        for growth_name, growth_rate in growth_rates.items():
            monthly_costs = {}
            for month in months:
                factor = growth_rate ** month
                monthly_costs[f'Month {month}'] = f'${baseline * factor:.2f}'
            pricing_structure['projected_costs'][growth_name] = monthly_costs

        return pricing_structure

    @staticmethod
    def get_default_cost_factors(service_name: str) -> List[str]:
        """サービス名に基づいてデフォルトのコスト要因を返す"""
        service_name_lower = service_name.lower()
        if 'lambda' in service_name_lower:
            return [
                'Number of requests',
                'Duration of execution',
                'Memory allocated',
                'Data transfer out',
            ]
        elif 'dynamodb' in service_name_lower:
            return [
                'Read and write throughput',
                'Storage used',
                'Data transfer',
                'Backup and restore operations',
            ]
        elif 's3' in service_name_lower:
            return [
                'Storage used',
                'Requests made',
                'Data transfer',
                'Storage class transitions',
            ]
        elif 'bedrock' in service_name_lower:
            return [
                'Model used',
                'Input tokens processed',
                'Output tokens generated',
                'Request frequency',
            ]
        else:
            return [
                'Usage volume',
                'Resource allocation',
                'Data transfer',
                'Operation frequency',
            ]

    @staticmethod
    def generate_cost_table(pricing_structure: Dict) -> Dict:
        """コスト表を生成する"""
        # 単価詳細表の生成
        unit_pricing_details_table = '| Service | Resource Type | Unit | Price | Free Tier |\n|---------|--------------|------|-------|------------|\n'
        
        service_name = pricing_structure.get('service_name', 'AWS Service')
        free_tier_info = pricing_structure.get('free_tier', 'No free tier information available')
        
        if len(free_tier_info) > 50:
            free_tier_info = free_tier_info[:47] + '...'
        
        has_pricing_data = False
        for item in pricing_structure['unit_pricing']:
            has_pricing_data = True
            unit = item.get('unit', 'N/A')
            price = item.get('price', 'N/A')
            resource_type = item.get('description', unit).split(' ')[0]
            unit_pricing_details_table += f'| {service_name} | {resource_type} | {unit} | {price} | {free_tier_info} |\n'
        
        if not has_pricing_data:
            unit_pricing_details_table += f'| {service_name} | N/A | N/A | N/A | {free_tier_info} |\n'

        # コスト計算表の生成
        cost_calculation_table = '| Service | Usage | Calculation | Monthly Cost |\n|---------|--------|-------------|-------------|\n'
        
        for level, costs in pricing_structure['usage_levels'].items():
            if level != 'medium':
                continue
                
            total_cost = 0
            for unit, cost in costs.items():
                if isinstance(cost, str) and '$' in cost:
                    try:
                        cost_value = float(cost.replace('$', '').replace(',', ''))
                        total_cost += cost_value
                    except ValueError:
                        pass
            
            monthly_cost = f'${total_cost:.2f}' if total_cost > 0 else 'Varies'
            usage_description = f'{level.title()} usage level'
            calculation = 'See pricing details'
            
            cost_calculation_table += f'| {service_name} | {usage_description} | {calculation} | {monthly_cost} |\n'

        # 使用量ベースのコスト表の生成
        usage_cost_table = '| Service | Low Usage | Medium Usage | High Usage |\n|---------|------------|--------------|------------|\n'
        
        low_cost = pricing_structure['usage_levels']['low']
        med_cost = pricing_structure['usage_levels']['medium']
        high_cost = pricing_structure['usage_levels']['high']
        
        total_low = total_med = total_high = 0
        for unit in low_cost.keys():
            for cost_dict, total in [(low_cost, total_low), (med_cost, total_med), (high_cost, total_high)]:
                if unit in cost_dict and isinstance(cost_dict[unit], str) and '$' in cost_dict[unit]:
                    try:
                        cost_value = float(cost_dict[unit].replace('$', '').replace(',', ''))
                        total += cost_value
                    except ValueError:
                        pass
        
        low_display = f'${total_low:.2f}/month' if total_low > 0 else 'Varies'
        med_display = f'${total_med:.2f}/month' if total_med > 0 else 'Varies'
        high_display = f'${total_high:.2f}/month' if total_high > 0 else 'Varies'
        
        usage_cost_table += f'| {service_name} | {low_display} | {med_display} | {high_display} |\n'

        # プロジェクトコスト表の生成
        projected_costs_table = '| Growth Pattern |' + ' | '.join([f'Month {m}' for m in [1, 3, 6, 12]]) + ' |\n'
        projected_costs_table += '|---------------|' + '|'.join(['----' for _ in range(4)]) + '|\n'
        
        for pattern, costs in pricing_structure['projected_costs'].items():
            row = f'| {pattern.title()} |'
            for month in [1, 3, 6, 12]:
                key = f'Month {month}'
                cost = costs.get(key, 'N/A')
                row += f' {cost} |'
            projected_costs_table += row + '\n'

        return {
            'unit_pricing_details_table': unit_pricing_details_table,
            'cost_calculation_table': cost_calculation_table,
            'usage_cost_table': usage_cost_table,
            'projected_costs_table': projected_costs_table
        }

    @staticmethod
    def generate_well_architected_recommendations(service_names: List[str]) -> Dict:
        """Well-Architectedフレームワークに基づく推奨事項を生成する"""
        recommendations = {
            'immediate': [
                'Right-size resources based on actual usage patterns',
                'Implement cost allocation tags to track spending by component',
                'Set up AWS Budgets alerts to monitor costs',
            ],
            'best_practices': [
                'Regularly review and analyze cost patterns with AWS Cost Explorer',
                'Consider reserved capacity options for predictable workloads',
                'Implement automated scaling based on demand',
            ],
        }
        
        # サービス固有の推奨事項を追加
        services_lower = [s.lower() for s in service_names]
        
        if any('bedrock' in s for s in services_lower):
            recommendations['immediate'].insert(
                0, 'Optimize prompt engineering to reduce token usage in Bedrock models'
            )
            recommendations['best_practices'].append(
                'Monitor runtime metrics with CloudWatch filtered by application inference profile ARN'
            )
        
        if any('lambda' in s for s in services_lower):
            recommendations['immediate'].append(
                'Optimize Lambda memory settings based on function requirements'
            )
            recommendations['best_practices'].append(
                'Use AWS Lambda Power Tuning tool to find optimal memory settings'
            )
        
        if any('s3' in s for s in services_lower):
            recommendations['best_practices'].append(
                'Implement S3 lifecycle policies to transition older data to cheaper storage tiers'
            )
        
        if any('dynamodb' in s for s in services_lower):
            recommendations['best_practices'].append(
                'Use DynamoDB on-demand capacity for unpredictable workloads'
            )
        
        # 推奨事項の数を制限
        recommendations['immediate'] = recommendations['immediate'][:5]
        recommendations['best_practices'] = recommendations['best_practices'][:5]
        
        return recommendations

def _extract_services_info(custom_cost_data: Dict) -> Tuple[Dict, List[str]]:
    """サービス情報を抽出する"""
    services_info = {}
    services = []

    if 'services' in custom_cost_data:
        for name, info in custom_cost_data['services'].items():
            services_info[name] = ServiceInfo(
                name=name,
                estimated_cost=info.get('estimated_cost', 'N/A'),
                usage=info.get('usage', ''),
                unit_pricing=info.get('unit_pricing'),
                usage_quantities=info.get('usage_quantities'),
                calculation_details=info.get('calculation_details'),
                free_tier_info=info.get('free_tier_info'),
            )
            services.append(name)

    return services_info, services

def _process_recommendations(custom_cost_data: Dict, service_names: List[str]) -> Tuple[List[str], List[str]]:
    """推奨事項を処理する"""
    if recommendations := custom_cost_data.get('recommendations'):
        if isinstance(recommendations, dict):
            immediate_actions = recommendations.get('immediate', [])
            best_practices = recommendations.get('best_practices', [])
            if immediate_actions and best_practices:
                return immediate_actions, best_practices

    # Well-Architectedフレームワークに基づく推奨事項を生成
    wa_recommendations = CostAnalysisHelper.generate_well_architected_recommendations(service_names)
    return wa_recommendations['immediate'], wa_recommendations['best_practices']

def _generate_csv_report(pricing_data: Dict, service_name: str) -> str:
    """CSVフォーマットのレポートを生成する"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー情報
    writer.writerow(['AWS Cost Analysis Report'])
    writer.writerow([])
    writer.writerow(['Service Information'])
    writer.writerow(['Name', service_name])
    writer.writerow(['Description', pricing_data.get('service_description', 'N/A')])
    writer.writerow([])
    
    # 価格情報
    writer.writerow(['Unit Pricing'])
    writer.writerow(['Resource Type', 'Unit', 'Price'])
    for price_info in pricing_data.get('unit_pricing', []):
        writer.writerow([
            price_info.get('description', 'N/A'),
            price_info.get('unit', 'N/A'),
            price_info.get('price', 'N/A')
        ])
    writer.writerow([])
    
    # 使用量ベースのコスト
    writer.writerow(['Usage Based Costs'])
    writer.writerow(['Usage Level', 'Monthly Cost'])
    for level, costs in pricing_data.get('usage_levels', {}).items():
        total_cost = 0
        for cost in costs.values():
            if isinstance(cost, str) and '$' in cost:
                try:
                    cost_value = float(cost.replace('$', '').replace(',', ''))
                    total_cost += cost_value
                except ValueError:
                    pass
        writer.writerow([level.title(), f'${total_cost:.2f}' if total_cost > 0 else 'Varies'])
    writer.writerow([])
    
    # コスト要因
    writer.writerow(['Key Cost Factors'])
    for factor in pricing_data.get('key_cost_factors', []):
        writer.writerow(['', factor])
    writer.writerow([])
    
    # 推奨事項
    recommendations = pricing_data.get('recommendations', {})
    writer.writerow(['Immediate Actions'])
    for action in recommendations.get('immediate', []):
        writer.writerow(['', action])
    writer.writerow([])
    
    writer.writerow(['Best Practices'])
    for practice in recommendations.get('best_practices', []):
        writer.writerow(['', practice])
    
    return output.getvalue()

def generate_cost_report(pricing_data: Dict[str, Any], service_name: str,
                        related_services: Optional[List[str]] = None,
                        params: Optional[Dict] = None,
                        format: str = 'markdown') -> str:
    """コスト分析レポートを生成する"""
    # 価格データを解析
    pricing_structure = CostAnalysisHelper.parse_pricing_data(
        pricing_data, service_name, related_services
    )
    
    # レポート形式に応じて適切なフォーマットで生成
    if format.lower() == 'csv':
        return _generate_csv_report(pricing_structure, service_name)
    
    # コスト表を生成
    cost_tables = CostAnalysisHelper.generate_cost_table(pricing_structure)
    
    # マークダウンレポートを生成
    report = f"""# {service_name} Cost Analysis

## Overview

{pricing_structure['service_description']}

This cost analysis is based on the following pricing model:
- **ON DEMAND** pricing (pay-as-you-go)
- Standard service configurations without reserved capacity or savings plans
- No caching or optimization techniques applied

## Assumptions

{chr(10).join(f'- {assumption}' for assumption in pricing_structure['assumptions'])}

## Unit Pricing Details

{cost_tables['unit_pricing_details_table']}

## Cost Calculation

{cost_tables['cost_calculation_table']}

## Free Tier Information

{pricing_structure['free_tier']}

## Cost Scaling with Usage

{cost_tables['usage_cost_table']}

## Key Cost Factors

{chr(10).join(f'- {factor}' for factor in pricing_structure['key_cost_factors'])}

## Projected Costs Over Time

{cost_tables['projected_costs_table']}

## AWS Well-Architected Cost Optimization Recommendations

### Immediate Actions

{chr(10).join(f'- {action}' for action in pricing_structure['recommendations']['immediate'])}

### Best Practices

{chr(10).join(f'- {practice}' for practice in pricing_structure['recommendations']['best_practices'])}

## Conclusion

By following the recommendations in this report, you can optimize your {service_name} costs while maintaining performance and reliability.
Regular monitoring and adjustment of your usage patterns will help ensure cost efficiency as your workload evolves.
"""
    return report

def lambda_handler(event, context):
    """AWS Lambda function to generate a cost analysis report.
    
    Args:
        event (dict): The Lambda event object containing pricing data and other parameters
                      Expected format: {
                          "pricing_data": {...},
                          "service_name": "AWS Service Name",
                          "related_services": ["Service1", "Service2"],
                          "pricing_model": "ON DEMAND",
                          "assumptions": [...],
                          "exclusions": [...],
                          "detailed_cost_data": {...},
                          "format": "markdown"
                      }
        context (dict): AWS Lambda context object
        
    Returns:
        dict: Generated cost report or error message
    """
    try:
        # イベントからパラメータを抽出
        pricing_data = event.get('pricing_data')
        service_name = event.get('service_name')
        related_services = event.get('related_services')
        pricing_model = event.get('pricing_model', 'ON DEMAND')
        assumptions = event.get('assumptions')
        exclusions = event.get('exclusions')
        detailed_cost_data = event.get('detailed_cost_data')
        format = event.get('format', 'markdown')
        
        # 必須パラメータの確認
        if not pricing_data:
            return {
                'status': 'error',
                'message': 'Missing pricing_data parameter'
            }
            
        if not service_name:
            return {
                'status': 'error',
                'message': 'Missing service_name parameter'
            }

        # パラメータの準備
        params = {
            'pricing_model': pricing_model,
            'assumptions': assumptions,
            'exclusions': exclusions,
        }

        # レポートを生成
        report = generate_cost_report(
            pricing_data=pricing_data,
            service_name=service_name,
            related_services=related_services,
            params=params,
            format=format,
        )
        
        # 結果を返す
        return {
            'status': 'success',
            'report': report,
            'message': f'Generated cost report for {service_name}',
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error generating cost report: {str(e)}',
        }
