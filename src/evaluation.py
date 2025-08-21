import json
import asyncio
import logging
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


from .models import (
    LeadQualificationRequest,
    LeadQualificationResponse,
    MessagePersonalizationRequest,
    MessagePersonalizationResponse
)
from .grok import (
    get_lead_qualification_service,
    get_message_personalization_service,
    GrokServiceError
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of a single evaluation test."""
    test_name: str
    success: bool
    score: Optional[float] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    expected_output: Optional[Dict[str, Any]] = None
    actual_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EvaluationSuite:
    """Collection of evaluation results with summary statistics."""
    suite_name: str
    results: List[EvaluationResult]
    timestamp: datetime
    
    def get_success_rate(self) -> float:
        """Calculate success rate of the evaluation suite."""
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.success) / len(self.results)
    
    def get_average_response_time(self) -> float:
        """Calculate average response time for successful tests."""
        times = [r.response_time for r in self.results if r.response_time is not None]
        return statistics.mean(times) if times else 0.0
    
    def get_average_score(self) -> float:
        """Calculate average score for tests that have scores."""
        scores = [r.score for r in self.results if r.score is not None]
        return statistics.mean(scores) if scores else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the evaluation suite."""
        return {
            "suite_name": self.suite_name,
            "timestamp": self.timestamp.isoformat(),
            "total_tests": len(self.results),
            "successful_tests": sum(1 for r in self.results if r.success),
            "failed_tests": sum(1 for r in self.results if not r.success),
            "success_rate": self.get_success_rate(),
            "average_response_time": self.get_average_response_time(),
            "average_score": self.get_average_score()
        }


class LeadQualificationEvaluator:
    """Evaluator for lead qualification service."""
    
    def __init__(self):
        self.service = get_lead_qualification_service()
    
    def get_test_cases(self) -> List[Tuple[str, LeadQualificationRequest, Dict[str, Any]]]:
        """Get predefined test cases for lead qualification evaluation."""
        return [
            (
                "high_value_enterprise_lead",
                LeadQualificationRequest(
                    name="Sarah Johnson",
                    email="sarah.johnson@enterprise-corp.com",
                    company="Enterprise Corp",
                    job_title="Chief Technology Officer",
                    industry="Technology",
                    company_size="1000-5000 employees",
                    additional_context="CTO at Fortune 500 company, actively looking for AI solutions"
                ),
                {"expected_score_range": (80, 100), "expected_priority": "high"}
            ),
            (
                "medium_value_startup_lead",
                LeadQualificationRequest(
                    name="Mike Chen",
                    email="mike@startup-xyz.com",
                    company="Startup XYZ",
                    job_title="Founder",
                    industry="Technology",
                    company_size="10-50 employees",
                    additional_context="Early-stage startup, limited budget but high potential"
                ),
                {"expected_score_range": (60, 85), "expected_priority": ["medium", "high"]}
            ),
            (
                "low_value_individual_lead",
                LeadQualificationRequest(
                    name="John Doe",
                    email="john.doe@gmail.com",
                    company="",
                    job_title="Student",
                    industry="Education",
                    company_size="",
                    additional_context="College student interested in learning about AI"
                ),
                {"expected_score_range": (0, 40), "expected_priority": "low"}
            ),
            (
                "incomplete_lead_data",
                LeadQualificationRequest(
                    name="Jane Smith",
                    email="jane@company.com",
                    company="Unknown Company",
                    job_title="",
                    industry="",
                    additional_context=""
                ),
                {"expected_score_range": (20, 60), "expected_priority": ["low", "medium"]}
            ),
            (
                "decision_maker_healthcare",
                LeadQualificationRequest(
                    name="Dr. Robert Williams",
                    email="r.williams@healthsystem.org",
                    company="Metro Health System",
                    job_title="Chief Medical Officer",
                    industry="Healthcare",
                    company_size="500-1000 employees",
                    additional_context="Leading digital transformation initiatives in healthcare"
                ),
                {"expected_score_range": (70, 95), "expected_priority": "high"}
            )
        ]
    
    async def evaluate_single_case(self, test_name: str, request: LeadQualificationRequest, 
                                  expected: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a single lead qualification case."""
        start_time = datetime.now()
        
        try:
            # Make the qualification request
            response = self.service.qualify_lead(request)
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Validate response structure
            if not isinstance(response, LeadQualificationResponse):
                return EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message="Invalid response type"
                )
            
            # Check score is in valid range
            if not (0 <= response.score <= 100):
                return EvaluationResult(
                    test_name=test_name,
                    success=False,
                    score=response.score,
                    response_time=response_time,
                    error_message=f"Score {response.score} is outside valid range (0-100)"
                )
            
            # Check expected score range if provided
            score_valid = True
            if "expected_score_range" in expected:
                min_score, max_score = expected["expected_score_range"]
                score_valid = min_score <= response.score <= max_score
            
            # Check expected priority if provided
            priority_valid = True
            if "expected_priority" in expected:
                expected_priority = expected["expected_priority"]
                if isinstance(expected_priority, list):
                    priority_valid = response.priority_level in expected_priority
                else:
                    priority_valid = response.priority_level == expected_priority
            
            # Check required fields are present and meaningful
            fields_valid = (
                len(response.reasoning) >= 10 and
                len(response.key_factors) > 0 and
                len(response.recommended_actions) > 0 and
                response.priority_level in ["high", "medium", "low"]
            )
            
            success = score_valid and priority_valid and fields_valid
            
            return EvaluationResult(
                test_name=test_name,
                success=success,
                score=response.score,
                response_time=response_time,
                expected_output=expected,
                actual_output=response.model_dump(),
                metadata={
                    "score_valid": score_valid,
                    "priority_valid": priority_valid,
                    "fields_valid": fields_valid,
                    "reasoning_length": len(response.reasoning),
                    "key_factors_count": len(response.key_factors),
                    "recommended_actions_count": len(response.recommended_actions)
                }
            )
            
        except GrokServiceError as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Grok service error: {str(e)}"
            )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def evaluate_consistency(self, request: LeadQualificationRequest, trials: int = 3) -> EvaluationResult:
        """Test consistency of lead qualification across multiple runs."""
        test_name = f"consistency_test_{trials}_trials"
        start_time = datetime.now()
        
        try:
            scores = []
            responses = []
            
            for _ in range(trials):
                response = self.service.qualify_lead(request)
                scores.append(response.score)
                responses.append(response)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate consistency metrics
            score_std = statistics.stdev(scores) if len(scores) > 1 else 0
            score_range = max(scores) - min(scores)
            
            # Consider it consistent if standard deviation is < 10 and range < 20
            consistent = score_std < 10 and score_range < 20
            
            return EvaluationResult(
                test_name=test_name,
                success=consistent,
                score=statistics.mean(scores),
                response_time=response_time,
                metadata={
                    "scores": scores,
                    "score_std": score_std,
                    "score_range": score_range,
                    "trials": trials
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
    
    async def run_evaluation_suite(self) -> EvaluationSuite:
        """Run complete evaluation suite for lead qualification."""
        logger.info("Starting lead qualification evaluation suite")
        results = []
        
        # Test individual cases
        test_cases = self.get_test_cases()
        for test_name, request, expected in test_cases:
            result = await self.evaluate_single_case(test_name, request, expected)
            results.append(result)
            logger.info(f"Test '{test_name}': {'PASS' if result.success else 'FAIL'}")
        
        # Test consistency with a medium-value lead
        consistency_request = LeadQualificationRequest(
            name="Test User",
            email="test@company.com",
            company="Test Company",
            job_title="Manager",
            industry="Technology",
            company_size="100-500 employees"
        )
        consistency_result = await self.evaluate_consistency(consistency_request)
        results.append(consistency_result)
        logger.info(f"Consistency test: {'PASS' if consistency_result.success else 'FAIL'}")
        
        suite = EvaluationSuite(
            suite_name="Lead Qualification Evaluation",
            results=results,
            timestamp=datetime.now()
        )
        
        logger.info(f"Lead qualification evaluation completed: {suite.get_success_rate():.1%} success rate")
        return suite


class MessagePersonalizationEvaluator:
    """Evaluator for message personalization service."""
    
    def __init__(self):
        self.service = get_message_personalization_service()
    
    def get_test_cases(self) -> List[Tuple[str, MessagePersonalizationRequest, Dict[str, Any]]]:
        """Get predefined test cases for message personalization evaluation."""
        return [
            (
                "cold_outreach_enterprise_cto",
                MessagePersonalizationRequest(
                    lead_name="Sarah Johnson",
                    lead_email="sarah.johnson@enterprise-corp.com",
                    company="Enterprise Corp",
                    job_title="Chief Technology Officer",
                    industry="Technology",
                    lead_source="linkedin",
                    campaign_type="cold_outreach",
                    message_tone="professional"
                ),
                {"min_variants": 1, "required_elements": ["subject", "body"], "max_body_length": 500}
            ),
            (
                "follow_up_startup_founder",
                MessagePersonalizationRequest(
                    lead_name="Mike Chen",
                    lead_email="mike@startup-xyz.com",
                    company="Startup XYZ",
                    job_title="Founder",
                    industry="Technology",
                    lead_source="conference",
                    previous_interactions=["Met at AI conference", "Showed interest in demo"],
                    campaign_type="follow_up",
                    message_tone="friendly"
                ),
                {"min_variants": 1, "required_elements": ["subject", "body"], "personalization_required": True}
            ),
            (
                "demo_request_healthcare_cmo",
                MessagePersonalizationRequest(
                    lead_name="Dr. Robert Williams",
                    lead_email="r.williams@healthsystem.org",
                    company="Metro Health System",
                    job_title="Chief Medical Officer",
                    industry="Healthcare",
                    lead_source="website",
                    campaign_type="demo_request",
                    message_tone="formal"
                ),
                {"min_variants": 1, "required_elements": ["subject", "body"], "industry_specific": True}
            )
        ]
    
    async def evaluate_single_case(self, test_name: str, request: MessagePersonalizationRequest,
                                  expected: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a single message personalization case."""
        start_time = datetime.now()
        
        try:
            # Make the personalization request
            response = self.service.personalize_message(request)
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Validate response structure
            if not isinstance(response, MessagePersonalizationResponse):
                return EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message="Invalid response type"
                )
            
            # Check minimum variants
            min_variants = expected.get("min_variants", 1)
            if len(response.variants) < min_variants:
                return EvaluationResult(
                    test_name=test_name,
                    success=False,
                    response_time=response_time,
                    error_message=f"Expected at least {min_variants} variants, got {len(response.variants)}"
                )
            
            # Check required elements in each variant
            required_elements = expected.get("required_elements", [])
            for i, variant in enumerate(response.variants):
                for element in required_elements:
                    if not getattr(variant, element, None):
                        return EvaluationResult(
                            test_name=test_name,
                            success=False,
                            response_time=response_time,
                            error_message=f"Variant {i} missing required element: {element}"
                        )
            
            # Check body length constraints
            max_body_length = expected.get("max_body_length")
            if max_body_length:
                for i, variant in enumerate(response.variants):
                    if len(variant.body) > max_body_length:
                        return EvaluationResult(
                            test_name=test_name,
                            success=False,
                            response_time=response_time,
                            error_message=f"Variant {i} body too long: {len(variant.body)} > {max_body_length}"
                        )
            
            # Check personalization quality
            personalization_score = 0
            if expected.get("personalization_required", False):
                # Check if lead name is mentioned
                name_mentioned = any(request.lead_name.split()[0] in variant.body for variant in response.variants)
                if name_mentioned:
                    personalization_score += 25
                
                # Check if company is mentioned
                if request.company:
                    company_mentioned = any(request.company in variant.body for variant in response.variants)
                    if company_mentioned:
                        personalization_score += 25
                
                # Check if job title context is used
                if request.job_title:
                    title_context = any(request.job_title.lower() in variant.body.lower() for variant in response.variants)
                    if title_context:
                        personalization_score += 25
                
                # Check if personalization factors are provided
                if response.personalization_factors:
                    personalization_score += 25
            else:
                personalization_score = 100  # Not required
            
            # Overall success criteria
            success = (
                len(response.variants) >= min_variants and
                all(variant.subject and variant.body for variant in response.variants) and
                personalization_score >= 75 and
                response.follow_up_strategy and
                len(response.personalization_factors) > 0
            )
            
            return EvaluationResult(
                test_name=test_name,
                success=success,
                score=personalization_score,
                response_time=response_time,
                expected_output=expected,
                actual_output=response.model_dump(),
                metadata={
                    "variants_count": len(response.variants),
                    "personalization_score": personalization_score,
                    "avg_subject_length": statistics.mean([len(v.subject) for v in response.variants]),
                    "avg_body_length": statistics.mean([len(v.body) for v in response.variants]),
                    "personalization_factors_count": len(response.personalization_factors)
                }
            )
            
        except GrokServiceError as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Grok service error: {str(e)}"
            )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return EvaluationResult(
                test_name=test_name,
                success=False,
                response_time=response_time,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def run_evaluation_suite(self) -> EvaluationSuite:
        """Run complete evaluation suite for message personalization."""
        logger.info("Starting message personalization evaluation suite")
        results = []
        
        # Test individual cases
        test_cases = self.get_test_cases()
        for test_name, request, expected in test_cases:
            result = await self.evaluate_single_case(test_name, request, expected)
            results.append(result)
            logger.info(f"Test '{test_name}': {'PASS' if result.success else 'FAIL'}")
        
        suite = EvaluationSuite(
            suite_name="Message Personalization Evaluation",
            results=results,
            timestamp=datetime.now()
        )
        
        logger.info(f"Message personalization evaluation completed: {suite.get_success_rate():.1%} success rate")
        return suite


class EvaluationFramework:
    """Main evaluation framework that orchestrates all evaluations."""
    
    def __init__(self, output_dir: str = "evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.lead_evaluator = LeadQualificationEvaluator()
        self.message_evaluator = MessagePersonalizationEvaluator()
    
    def save_results(self, suite: EvaluationSuite, filename: Optional[str] = None):
        """Save evaluation results to JSON file."""
        if not filename:
            timestamp = suite.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{suite.suite_name.lower().replace(' ', '_')}_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Convert results to serializable format
        serializable_results = []
        for result in suite.results:
            result_dict = asdict(result)
            # Handle datetime serialization
            if isinstance(result_dict.get('timestamp'), datetime):
                result_dict['timestamp'] = result_dict['timestamp'].isoformat()
            serializable_results.append(result_dict)
        
        output_data = {
            "summary": suite.get_summary(),
            "results": serializable_results
        }
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Evaluation results saved to {filepath}")
    
    async def run_full_evaluation(self) -> Dict[str, EvaluationSuite]:
        """Run complete evaluation across all services."""
        logger.info("Starting full evaluation framework")
        
        results = {}
        
        # Run lead qualification evaluation
        try:
            lead_suite = await self.lead_evaluator.run_evaluation_suite()
            results["lead_qualification"] = lead_suite
            self.save_results(lead_suite)
        except Exception as e:
            logger.error(f"Lead qualification evaluation failed: {str(e)}")
        
        # Run message personalization evaluation
        try:
            message_suite = await self.message_evaluator.run_evaluation_suite()
            results["message_personalization"] = message_suite
            self.save_results(message_suite)
        except Exception as e:
            logger.error(f"Message personalization evaluation failed: {str(e)}")
        
        # Generate combined summary
        self._generate_summary_report(results)
        
        logger.info("Full evaluation completed")
        return results
    
    def _generate_summary_report(self, results: Dict[str, EvaluationSuite]):
        """Generate a summary report of all evaluations."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"evaluation_summary_{timestamp}.json"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_stats": {
                "total_suites": len(results),
                "successful_suites": sum(1 for suite in results.values() if suite.get_success_rate() > 0.7),
            },
            "suite_summaries": {name: suite.get_summary() for name, suite in results.items()}
        }
        
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Summary report saved to {report_file}")


# Global evaluation framework instance
evaluation_framework = EvaluationFramework()


async def run_evaluations():
    """Convenience function to run all evaluations."""
    return await evaluation_framework.run_full_evaluation()


if __name__ == "__main__":
    # Run evaluations when script is executed directly
    asyncio.run(run_evaluations())
