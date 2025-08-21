#!/usr/bin/env python3
"""
Test consistency and reliability of AI responses using unified evaluation framework
"""
import asyncio
import sys
import statistics
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation import (
    EvaluationResult, 
    EvaluationSuite, 
    LeadQualificationEvaluator,
    MessagePersonalizationEvaluator
)
from src.models import LeadQualificationRequest, MessagePersonalizationRequest


class ConsistencyEvaluator:
    """Specialized evaluator for testing consistency across multiple runs"""
    
    def __init__(self):
        self.lead_evaluator = LeadQualificationEvaluator()
        self.message_evaluator = MessagePersonalizationEvaluator()
    
    async def test_lead_qualification_consistency(self, request: LeadQualificationRequest, trials: int = 5) -> EvaluationResult:
        """Test lead qualification consistency using the unified framework"""
        test_name = f"lead_consistency_{trials}_trials"
        start_time = datetime.now()
        
        try:
            scores = []
            priorities = []
            responses = []
            
            # Run multiple trials
            for i in range(trials):
                response = self.lead_evaluator.service.qualify_lead(request)
                scores.append(response.score)
                priorities.append(response.priority_level)
                responses.append(response)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate consistency metrics
            score_std = statistics.stdev(scores) if len(scores) > 1 else 0
            score_range = max(scores) - min(scores)
            priority_consistent = len(set(priorities)) == 1
            
            # Consistency criteria: std dev < 10 and range < 20
            consistent = score_std < 10 and score_range < 20 and priority_consistent
            
            return EvaluationResult(
                test_name=test_name,
                success=consistent,
                score=statistics.mean(scores),
                response_time=response_time,
                metadata={
                    "trials": trials,
                    "scores": scores,
                    "priorities": priorities,
                    "score_std": score_std,
                    "score_range": score_range,
                    "priority_consistent": priority_consistent,
                    "unique_priorities": list(set(priorities)),
                    "score_mean": statistics.mean(scores),
                    "score_median": statistics.median(scores)
                }
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Consistency test failed: {str(e)}"
            )
    
    async def test_message_personalization_consistency(self, request: MessagePersonalizationRequest, trials: int = 3) -> EvaluationResult:
        """Test message personalization consistency using the unified framework"""
        test_name = f"message_consistency_{trials}_trials"
        start_time = datetime.now()
        
        try:
            variant_counts = []
            effectiveness_scores = []
            responses = []
            
            # Run multiple trials
            for i in range(trials):
                response = self.message_evaluator.service.personalize_message(request)
                variant_counts.append(len(response.variants))
                
                # Extract effectiveness scores from variants
                for variant in response.variants:
                    effectiveness_scores.append(variant.estimated_effectiveness)
                
                responses.append(response)
                
                # Longer delay for message personalization
                await asyncio.sleep(2)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate consistency metrics
            variant_count_std = statistics.stdev(variant_counts) if len(variant_counts) > 1 else 0
            effectiveness_std = statistics.stdev(effectiveness_scores) if len(effectiveness_scores) > 1 else 0
            variant_count_consistent = len(set(variant_counts)) == 1
            
            # Consistency criteria: consistent variant counts and effectiveness variation < 15
            consistent = variant_count_consistent and effectiveness_std < 15
            
            return EvaluationResult(
                test_name=test_name,
                success=consistent,
                score=statistics.mean(effectiveness_scores) if effectiveness_scores else 0,
                response_time=response_time,
                metadata={
                    "trials": trials,
                    "variant_counts": variant_counts,
                    "effectiveness_scores": effectiveness_scores,
                    "variant_count_std": variant_count_std,
                    "effectiveness_std": effectiveness_std,
                    "variant_count_consistent": variant_count_consistent,
                    "avg_variant_count": statistics.mean(variant_counts),
                    "avg_effectiveness": statistics.mean(effectiveness_scores) if effectiveness_scores else 0
                }
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Message consistency test failed: {str(e)}"
            )


async def test_consistency_lead_qualification():
    """Test consistency of lead qualification across multiple runs using unified framework"""
    print("=== Testing Lead Qualification Consistency ===")
    
    # Test lead that should consistently score in medium range
    test_lead = LeadQualificationRequest(
        name="Marketing Manager Jane",
        email="jane@mediumcorp.com",
        company="Medium Corp",
        job_title="Marketing Manager", 
        industry="Technology",
        company_size="100-500 employees",
        additional_context="Interested in marketing automation tools, needs approval for purchases over $10k"
    )
    
    evaluator = ConsistencyEvaluator()
    result = await evaluator.test_lead_qualification_consistency(test_lead, trials=5)
    
    print("\nConsistency Analysis:")
    if result.success:
        print(f"  ✅ CONSISTENT: Score Range: {result.metadata['score_range']:.1f}, StdDev: {result.metadata['score_std']:.2f}")
        print(f"  Priority Consistent: {result.metadata['priority_consistent']}")
        print(f"  Average Score: {result.score:.1f}")
    else:
        print(f"  ❌ INCONSISTENT: {result.error_message}")
        if result.metadata:
            print(f"  Score Range: {result.metadata.get('score_range', 'N/A')}")
            print(f"  StdDev: {result.metadata.get('score_std', 'N/A')}")
    
    return result

async def test_consistency_message_personalization():
    """Test consistency of message personalization using unified framework"""
    print("\n=== Testing Message Personalization Consistency ===")
    
    test_request = MessagePersonalizationRequest(
        lead_name="John Smith",
        lead_email="john@techstartup.com",
        company="TechStartup Inc",
        job_title="CTO",
        industry="Technology",
        lead_source="linkedin",
        campaign_type="cold_outreach",
        message_tone="professional"
    )
    
    evaluator = ConsistencyEvaluator()
    result = await evaluator.test_message_personalization_consistency(test_request, trials=3)
    
    print("\nMessage Consistency Analysis:")
    if result.success:
        print(f"  ✅ CONSISTENT: Variant Count Consistent: {result.metadata['variant_count_consistent']}")
        print(f"  Effectiveness StdDev: {result.metadata['effectiveness_std']:.2f}")
        print(f"  Average Effectiveness: {result.score:.1f}")
    else:
        print(f"  ❌ INCONSISTENT: {result.error_message}")
        if result.metadata:
            print(f"  Effectiveness StdDev: {result.metadata.get('effectiveness_std', 'N/A')}")
    
    return result

async def run_consistency_tests():
    """Run all consistency tests using unified evaluation framework"""
    print("Starting consistency testing with unified framework...\n")
    
    results = []
    
    # Test lead qualification consistency
    try:
        lead_result = await test_consistency_lead_qualification()
        results.append(lead_result)
        print(f"✅ Lead qualification consistency: {'PASS' if lead_result.success else 'FAIL'}")
    except Exception as e:
        print(f"❌ Lead qualification consistency test failed: {e}")
        error_result = EvaluationResult(
            test_name="lead_qualification_consistency",
            success=False,
            error_message=str(e)
        )
        results.append(error_result)
    
    # Test message personalization consistency
    try:
        message_result = await test_consistency_message_personalization()
        results.append(message_result)
        print(f"✅ Message personalization consistency: {'PASS' if message_result.success else 'FAIL'}")
    except Exception as e:
        print(f"❌ Message personalization consistency test failed: {e}")
        error_result = EvaluationResult(
            test_name="message_personalization_consistency",
            success=False,
            error_message=str(e)
        )
        results.append(error_result)
    
    # Create evaluation suite
    suite = EvaluationSuite(
        suite_name="Consistency Testing Suite",
        results=results,
        timestamp=datetime.now()
    )
    
    # Save results using the framework
    from src.evaluation import evaluation_framework
    evaluation_framework.save_results(suite, "consistency_test_results.json")
    
    print(f"\n✅ Consistency testing complete! Success rate: {suite.get_success_rate():.1%}")
    print(f"Average response time: {suite.get_average_response_time():.2f}s")
    
    return suite

if __name__ == "__main__":
    asyncio.run(run_consistency_tests())
