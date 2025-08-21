#!/usr/bin/env python3
"""
Test different prompt variations for lead qualification using unified evaluation framework
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation import (
    EvaluationResult,
    EvaluationSuite
)
from src.grok import LeadQualificationService
from src.models import LeadQualificationRequest

# Test different system prompt variations
PROMPT_VARIATIONS = {
    "aggressive": {
        "scoring_criteria": [
            {"name": "Revenue Potential", "weight": 40, "description": "Immediate revenue opportunity"},
            {"name": "Decision Speed", "weight": 30, "description": "Speed of decision making"},
            {"name": "Budget Authority", "weight": 30, "description": "Direct budget control"}
        ]
    },
    "conservative": {
        "scoring_criteria": [
            {"name": "Long-term Fit", "weight": 35, "description": "Strategic alignment for long-term partnership"},
            {"name": "Market Position", "weight": 25, "description": "Company stability and market position"},
            {"name": "Cultural Fit", "weight": 20, "description": "Cultural and value alignment"},
            {"name": "Growth Trajectory", "weight": 20, "description": "Company growth potential"}
        ]
    },
    "balanced": {
        "scoring_criteria": [
            {"name": "Company Fit", "weight": 25, "description": "Overall company alignment"},
            {"name": "Contact Quality", "weight": 25, "description": "Quality of contact information"},
            {"name": "Intent Signals", "weight": 25, "description": "Buying intent indicators"},
            {"name": "Market Timing", "weight": 25, "description": "Market timing factors"}
        ]
    }
}

TEST_LEADS = [
    LeadQualificationRequest(
        name="Enterprise CTO",
        email="cto@bigcorp.com", 
        company="Big Corp",
        job_title="Chief Technology Officer",
        industry="Technology",
        company_size="5000+ employees",
        additional_context="Looking for AI solutions, has budget approval authority"
    ),
    LeadQualificationRequest(
        name="Startup Founder",
        email="founder@startup.com",
        company="Early Startup",
        job_title="Founder & CEO", 
        industry="Technology",
        company_size="5-10 employees",
        additional_context="Bootstrap startup, limited budget but high growth potential"
    ),
    LeadQualificationRequest(
        name="Mid-level Manager",
        email="manager@company.com",
        company="Mid Corp",
        job_title="IT Manager",
        industry="Manufacturing", 
        company_size="200-500 employees",
        additional_context="Interested in automation but needs approval from above"
    )
]


class PromptVariationEvaluator:
    """Specialized evaluator for testing different prompt variations"""
    
    def __init__(self):
        self.variations = PROMPT_VARIATIONS
        self.test_leads = TEST_LEADS
    
    async def evaluate_prompt_variation(self, variation_name: str, config: dict, test_leads: list) -> EvaluationResult:
        """Evaluate a single prompt variation using the unified framework"""
        test_name = f"prompt_variation_{variation_name}"
        start_time = datetime.now()
        
        try:
            # Create service with custom scoring criteria
            service = LeadQualificationService(scoring_criteria=config["scoring_criteria"])
            
            results_data = []
            total_score = 0
            successful_evaluations = 0
            
            for lead in test_leads:
                try:
                    result = service.qualify_lead(lead)
                    lead_data = {
                        "lead": f"{lead.name} - {lead.company}",
                        "score": result.score,
                        "priority": result.priority_level,
                        "reasoning": result.reasoning[:200] + "..." if len(result.reasoning) > 200 else result.reasoning,
                        "key_factors_count": len(result.key_factors),
                        "recommended_actions_count": len(result.recommended_actions)
                    }
                    results_data.append(lead_data)
                    total_score += result.score
                    successful_evaluations += 1
                    
                except Exception as e:
                    results_data.append({
                        "lead": f"{lead.name} - {lead.company}",
                        "error": str(e)
                    })
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Consider success if all leads were processed successfully
            success = successful_evaluations == len(test_leads)
            average_score = total_score / successful_evaluations if successful_evaluations > 0 else 0
            
            return EvaluationResult(
                test_name=test_name,
                success=success,
                score=average_score,
                response_time=response_time,
                expected_output={"variation": variation_name, "criteria": config},
                actual_output={"results": results_data, "successful_evaluations": successful_evaluations},
                metadata={
                    "variation_name": variation_name,
                    "total_leads": len(test_leads),
                    "successful_evaluations": successful_evaluations,
                    "failed_evaluations": len(test_leads) - successful_evaluations,
                    "average_score": average_score,
                    "scoring_criteria": config["scoring_criteria"]
                }
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Prompt variation test failed: {str(e)}"
            )
    
    async def run_all_variations(self) -> EvaluationSuite:
        """Run all prompt variations using unified evaluation framework"""
        print("Starting prompt variation testing with unified framework...\n")
        
        results = []
        
        for variation_name, config in self.variations.items():
            print(f"=== Testing {variation_name.upper()} approach ===")
            
            try:
                result = await self.evaluate_prompt_variation(variation_name, config, self.test_leads)
                results.append(result)
                
                if result.success:
                    print(f"✅ {variation_name}: Average score {result.score:.1f}")
                    # Show individual lead results
                    for lead_result in result.actual_output["results"]:
                        if "score" in lead_result:
                            print(f"  {lead_result['lead']}: {lead_result['score']} ({lead_result['priority']})")
                        else:
                            print(f"  {lead_result['lead']}: ERROR - {lead_result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ {variation_name}: {result.error_message}")
                    
            except Exception as e:
                print(f"❌ {variation_name}: Failed - {str(e)}")
                error_result = EvaluationResult(
                    test_name=f"prompt_variation_{variation_name}",
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
        
        # Create evaluation suite
        suite = EvaluationSuite(
            suite_name="Prompt Variations Testing Suite",
            results=results,
            timestamp=datetime.now()
        )
        
        return suite


async def test_prompt_variations():
    """Test different prompt approaches using unified evaluation framework"""
    evaluator = PromptVariationEvaluator()
    suite = await evaluator.run_all_variations()
    
    # Save results using the framework
    from src.evaluation import evaluation_framework
    evaluation_framework.save_results(suite, "prompt_variation_results.json")
    
    # Print summary
    print(f"\n✅ Prompt variation testing complete! Success rate: {suite.get_success_rate():.1%}")
    print(f"Average response time: {suite.get_average_response_time():.2f}s")
    
    # Print variation comparison
    print("\n=== Variation Performance Comparison ===")
    for result in suite.results:
        if result.success:
            variation_name = result.metadata["variation_name"]
            avg_score = result.score
            successful_evals = result.metadata["successful_evaluations"]
            total_leads = result.metadata["total_leads"]
            print(f"{variation_name.capitalize()}: {avg_score:.1f} avg score ({successful_evals}/{total_leads} leads)")
    
    return suite

if __name__ == "__main__":
    asyncio.run(test_prompt_variations())
