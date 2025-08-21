#!/usr/bin/env python3
"""
Test edge cases and potential failure scenarios using unified evaluation framework
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation import (
    EvaluationResult,
    EvaluationSuite
)
from src.grok import LeadQualificationService, MessagePersonalizationService, GrokServiceError
from src.models import LeadQualificationRequest, MessagePersonalizationRequest

# Edge case test data
EDGE_CASE_LEADS = [
    # Empty/minimal data
    LeadQualificationRequest(
        name="John Doe",
        email="john@email.com"
    ),
    
    # Conflicting information
    LeadQualificationRequest(
        name="Senior Student",
        email="student@university.edu",
        company="Fortune 500 Corp",
        job_title="CEO", 
        industry="Education",
        company_size="1 employee",
        additional_context="Student looking for internship opportunities"
    ),
    
    # Extremely long content
    LeadQualificationRequest(
        name="Very Long Name With Many Words That Goes On And On",
        email="extremely.long.email.address.that.should.test.limits@very-long-company-domain-name-that-exceeds-normal-lengths.enterprise.corporation.international.global.com",
        company="A" * 1000,  # Very long company name
        job_title="Senior Executive Vice President of Strategic Initiatives and Business Development Operations Worldwide Global International",
        industry="Technology, Healthcare, Finance, Manufacturing, Education, Entertainment, Sports, Travel, Food, Automotive",
        additional_context="A" * 5000  # Very long context
    ),
    
    # Special characters and encoding
    LeadQualificationRequest(
        name="François José María-García",
        email="françois.josé@maría-garcía.企業.com",
        company="Société Française & García Co. 株式会社",
        job_title="Développeur Principal / 主任開発者",
        industry="Technologie & Innovation 技術革新",
        additional_context="Contact speaks multiple languages: English, Français, Español, 日本語. Special requirements: ñ, ç, ü, 漢字"
    ),
    
    # Suspicious/spam-like data
    LeadQualificationRequest(
        name="URGENT BUY NOW!!!",
        email="spam@suspicious-domain.tk",
        company="GET RICH QUICK SCHEMES LLC",
        job_title="Make Money Fast Expert",
        additional_context="CLICK HERE NOW!!! FREE MONEY!!! NO SCAM!!! 100% GUARANTEED!!!"
    ),
    
    # Unrealistic data
    LeadQualificationRequest(
        name="Five Year Old CEO",
        email="toddler@impossible.com",
        company="Alphabet Inc",
        job_title="Chief Executive Officer",
        industry="Technology",
        company_size="100,000+ employees",
        additional_context="5 years old, runs Google, has $1 trillion budget, needs enterprise AI solution immediately"
    )
]

# Invalid message personalization requests
INVALID_MESSAGE_REQUESTS = [
    # Empty name
    MessagePersonalizationRequest(
        lead_name="",
        lead_email="test@email.com",
        campaign_type="cold_outreach"
    ),
    
    # Invalid email format
    MessagePersonalizationRequest(
        lead_name="John Doe",
        lead_email="not-an-email",
        campaign_type="follow_up"
    ),
    
    # Extremely long previous interactions
    MessagePersonalizationRequest(
        lead_name="Test User",
        lead_email="test@email.com",
        previous_interactions=["A very long interaction that goes on and on" * 100] * 50,
        campaign_type="demo_request"
    )
]


class FailureCaseEvaluator:
    """Specialized evaluator for testing edge cases and failure scenarios"""
    
    def __init__(self):
        self.lead_service = LeadQualificationService()
        self.message_service = MessagePersonalizationService()
    
    async def evaluate_edge_case_leads(self, test_leads: list) -> list:
        """Evaluate edge case leads and return individual results"""
        results = []
        
        for i, lead in enumerate(test_leads):
            test_name = f"edge_case_lead_{i+1}"
            start_time = datetime.now()
            
            try:
                result = self.lead_service.qualify_lead(lead)
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Success criteria: response received and score is valid
                success = (0 <= result.score <= 100 and 
                          result.priority_level in ["high", "medium", "low"] and
                          len(result.reasoning) > 0)
                
                eval_result = EvaluationResult(
                    test_name=test_name,
                    success=success,
                    score=result.score,
                    response_time=response_time,
                    expected_output={"test_type": "edge_case", "lead_name": lead.name[:50]},
                    actual_output=result.model_dump(),
                    metadata={
                        "case_index": i+1,
                        "lead_name": lead.name[:50],
                        "score_valid": 0 <= result.score <= 100,
                        "priority_valid": result.priority_level in ["high", "medium", "low"],
                        "reasoning_length": len(result.reasoning),
                        "factors_count": len(result.key_factors),
                        "actions_count": len(result.recommended_actions)
                    }
                )
                results.append(eval_result)
                
            except GrokServiceError as e:
                response_time = (datetime.now() - start_time).total_seconds()
                eval_result = EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message=f"Grok service error: {str(e)}",
                    metadata={
                        "case_index": i+1,
                        "lead_name": lead.name[:50],
                        "error_type": "grok_service_error"
                    }
                )
                results.append(eval_result)
                
            except Exception as e:
                response_time = (datetime.now() - start_time).total_seconds()
                eval_result = EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message=f"Unexpected error: {str(e)}",
                    metadata={
                        "case_index": i+1,
                        "lead_name": lead.name[:50],
                        "error_type": "unexpected_error"
                    }
                )
                results.append(eval_result)
        
        return results
    
    async def evaluate_message_failure_cases(self, test_requests: list) -> list:
        """Evaluate message personalization failure cases"""
        results = []
        
        for i, request in enumerate(test_requests):
            test_name = f"message_fail_case_{i+1}"
            start_time = datetime.now()
            
            try:
                result = self.message_service.personalize_message(request)
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Success criteria: response received with valid variants
                success = (len(result.variants) > 0 and
                          all(variant.subject and variant.body for variant in result.variants) and
                          result.follow_up_strategy)
                
                eval_result = EvaluationResult(
                    test_name=test_name,
                    success=success,
                    score=len(result.variants),  # Use variant count as score
                    response_time=response_time,
                    expected_output={"test_type": "message_failure", "lead_name": request.lead_name},
                    actual_output=result.model_dump(),
                    metadata={
                        "case_index": i+1,
                        "lead_name": request.lead_name,
                        "variants_count": len(result.variants),
                        "has_follow_up_strategy": bool(result.follow_up_strategy),
                        "personalization_factors_count": len(result.personalization_factors)
                    }
                )
                results.append(eval_result)
                
            except GrokServiceError as e:
                response_time = (datetime.now() - start_time).total_seconds()
                eval_result = EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message=f"Grok service error: {str(e)}",
                    metadata={
                        "case_index": i+1,
                        "lead_name": request.lead_name,
                        "error_type": "grok_service_error"
                    }
                )
                results.append(eval_result)
                
            except Exception as e:
                response_time = (datetime.now() - start_time).total_seconds()
                eval_result = EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message=f"Unexpected error: {str(e)}",
                    metadata={
                        "case_index": i+1,
                        "lead_name": request.lead_name,
                        "error_type": "unexpected_error"
                    }
                )
                results.append(eval_result)
        
        return results
    
    async def run_all_failure_tests(self) -> EvaluationSuite:
        """Run all failure case tests using unified evaluation framework"""
        print("Starting failure case testing with unified framework...\n")
        
        all_results = []
        
        # Test edge case leads
        print("=== Testing Lead Qualification Edge Cases ===")
        edge_results = await self.evaluate_edge_case_leads(EDGE_CASE_LEADS)
        all_results.extend(edge_results)
        
        for result in edge_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            lead_name = result.metadata["lead_name"]
            if result.success:
                print(f"{status}: {lead_name} - Score: {result.score}")
            else:
                print(f"{status}: {lead_name} - {result.error_message}")
        
        # Test message failure cases
        print("\n=== Testing Message Personalization Failure Cases ===")
        message_results = await self.evaluate_message_failure_cases(INVALID_MESSAGE_REQUESTS)
        all_results.extend(message_results)
        
        for result in message_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            lead_name = result.metadata["lead_name"]
            if result.success:
                print(f"{status}: {lead_name} - Variants: {int(result.score)}")
            else:
                print(f"{status}: {lead_name} - {result.error_message}")
        
        # Create evaluation suite
        suite = EvaluationSuite(
            suite_name="Failure Cases Testing Suite",
            results=all_results,
            timestamp=datetime.now()
        )
        
        return suite


async def test_edge_cases():
    """Test edge cases for lead qualification using unified framework"""
    evaluator = FailureCaseEvaluator()
    edge_results = await evaluator.evaluate_edge_case_leads(EDGE_CASE_LEADS)
    
    print("=== Lead Qualification Edge Cases Results ===")
    for result in edge_results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        lead_name = result.metadata["lead_name"]
        if result.success:
            print(f"{status}: {lead_name} - Score: {result.score}")
        else:
            print(f"{status}: {lead_name} - {result.error_message}")
    
    return edge_results

async def test_message_failures():
    """Test message personalization failure scenarios using unified framework"""
    evaluator = FailureCaseEvaluator()
    message_results = await evaluator.evaluate_message_failure_cases(INVALID_MESSAGE_REQUESTS)
    
    print("=== Message Personalization Failure Cases Results ===")
    for result in message_results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        lead_name = result.metadata["lead_name"]
        if result.success:
            print(f"{status}: {lead_name} - Variants: {int(result.score)}")
        else:
            print(f"{status}: {lead_name} - {result.error_message}")
    
    return message_results

async def test_rate_limiting():
    """Test rate limiting behavior with rapid requests"""
    print("\n=== Testing Rate Limiting ===")
    
    service = LeadQualificationService()
    simple_lead = LeadQualificationRequest(
        name="Rate Test Lead",
        email="rate@test.com",
        company="Test Corp"
    )
    
    results = {"successful": 0, "rate_limited": 0, "errors": 0}
    
    # Make rapid requests
    tasks = []
    for i in range(10):  # Adjust number based on rate limits
        tasks.append(test_single_request(service, simple_lead, i))
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for response in responses:
        if isinstance(response, Exception):
            if "rate limit" in str(response).lower():
                results["rate_limited"] += 1
            else:
                results["errors"] += 1
        else:
            results["successful"] += 1
    
    print(f"Rate limiting test results: {results}")
    return results

async def test_single_request(service, lead, request_id):
    """Helper function for rate limiting test"""
    try:
        result = service.qualify_lead(lead)
        print(f"  Request {request_id}: Success (Score: {result.score})")
        return result
    except Exception as e:
        print(f"  Request {request_id}: Error - {str(e)}")
        raise e

async def run_all_failure_tests():
    """Run all failure scenario tests using unified evaluation framework"""
    evaluator = FailureCaseEvaluator()
    suite = await evaluator.run_all_failure_tests()
    
    # Save results using the framework
    from src.evaluation import evaluation_framework
    evaluation_framework.save_results(suite, "failure_test_results.json")
    
    # Print summary
    print(f"\n✅ Failure testing complete! Success rate: {suite.get_success_rate():.1%}")
    print(f"Average response time: {suite.get_average_response_time():.2f}s")
    
    # Print detailed summary by test type
    edge_cases = [r for r in suite.results if r.test_name.startswith("edge_case")]
    message_cases = [r for r in suite.results if r.test_name.startswith("message_fail")]
    
    print("\n=== DETAILED SUMMARY ===")
    if edge_cases:
        edge_success = sum(1 for r in edge_cases if r.success)
        print(f"Edge Cases: {edge_success}/{len(edge_cases)} handled gracefully")
    
    if message_cases:
        msg_success = sum(1 for r in message_cases if r.success)
        print(f"Message Failures: {msg_success}/{len(message_cases)} handled gracefully")
    
    return suite

if __name__ == "__main__":
    asyncio.run(run_all_failure_tests())
