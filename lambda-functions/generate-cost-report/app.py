import json
import re
from typing import Any, Dict, List, Optional, Union

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
        """価格データを解析する"""
        return {
            'service_description': f'Cost analysis for {service_name}',
            'assumptions': [
                'Standard ON DEMAND pricing model',
                'No caching or optimization applied',
                'Average request size of 4KB'
            ],
            'free_tier': 'AWS offers a Free Tier for many services. Check the AWS Free Tier page for current offers and limitations.',
            'key_cost_factors': [
                'Request volume and frequency',
                'Data storage requirements',
                'Data transfer between services',
                'Compute resources utilized'
            ],
            'recommendations': {
                'immediate': [
                    'Optimize resource usage based on actual requirements',
                    'Implement cost allocation tags',
                    'Set up AWS Budgets alerts'
                ],
                'best_practices': [
                    'Regularly review costs with AWS Cost Explorer',
                    'Consider reserved capacity for predictable workloads',
                    'Implement automated scaling based on demand'
                ]
            }
        }
    
    @staticmethod
    def generate_cost_table(pricing_structure: Dict) -> Dict:
        """コスト表を生成する"""
        return {
            'unit_pricing_details_table': 'No detailed unit pricing information available.',
            'cost_calculation_table': 'No cost calculation details available.',
            'usage_cost_table': 'Cost scaling information not available.',
            'projected_costs_table': 'Insufficient data to generate cost projections.'
        }
    
    @staticmethod
    def generate_well_architected_recommendations(service_names: List[str]) -> Dict:
        """Well-Architectedフレームワークに基づく推奨事項を生成する"""
        return {
            'immediate': [
                'Optimize resource usage based on actual requirements',
                'Implement cost allocation tags',
                'Set up AWS Budgets alerts'
            ],
            'best_practices': [
                'Regularly review costs with AWS Cost Explorer',
                'Consider reserved capacity for predictable workloads',
                'Implement automated scaling based on demand'
            ]
        }

def _extract_services_info(custom_cost_data: Dict) -> tuple:
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

def _process_recommendations(custom_cost_data: Dict, service_names: List[str]) -> tuple:
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

def generate_cost_report(pricing_data: Dict[str, Any], service_name: str,
                        related_services: Optional[List[str]] = None,
                        params: Optional[Dict] = None,
                        format: str = 'markdown') -> str:
    """コスト分析レポートを生成する"""
    # 価格データを解析
    pricing_structure = CostAnalysisHelper.parse_pricing_data(
        pricing_data, service_name, related_services
    )
    
    # コスト表を生成
    cost_tables = CostAnalysisHelper.generate_cost_table(pricing_structure)
    
    # リッチなマークダウンレポートを生成
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
