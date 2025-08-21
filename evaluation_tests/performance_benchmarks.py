#!/usr/bin/env python3
"""
Performance benchmarking for AI services using unified evaluation framework
"""
import asyncio
import sys
import time
import statistics
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation import (
    EvaluationResult,
    EvaluationSuite
)
from src.grok import LeadQualificationService, MessagePersonalizationService
from src.models import LeadQualificationRequest, MessagePersonalizationRequest

class PerformanceBenchmarkEvaluator:
    """Specialized evaluator for performance benchmarking using unified framework"""
    
    def __init__(self):
        self.lead_service = LeadQualificationService()
        self.message_service = MessagePersonalizationService()
    
    async def benchmark_lead_qualification_speed(self, num_requests=10) -> EvaluationResult:
        """Benchmark lead qualification response times using unified framework"""
        test_name = f"lead_qualification_speed_benchmark_{num_requests}_requests"
        overall_start = datetime.now()
        
        print(f"=== Benchmarking Lead Qualification ({num_requests} requests) ===")
        
        # Simple test lead
        test_lead = LeadQualificationRequest(
            name="Benchmark Test",
            email="test@benchmark.com",
            company="Benchmark Corp",
            job_title="Test Manager",
            industry="Technology"
        )
        
        individual_results = []
        response_times = []
        successful_requests = 0
        scores = []
        
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                result = self.lead_service.qualify_lead(test_lead)
                request_time = time.time() - request_start
                
                individual_results.append({
                    "request_id": i + 1,
                    "response_time": request_time,
                    "score": result.score,
                    "success": True
                })
                
                response_times.append(request_time)
                scores.append(result.score)
                successful_requests += 1
                
                print(f"  Request {i+1}: {request_time:.2f}s (Score: {result.score})")
                
            except Exception as e:
                request_time = time.time() - request_start
                individual_results.append({
                    "request_id": i + 1,
                    "response_time": request_time,
                    "error": str(e),
                    "success": False
                })
                response_times.append(request_time)
                
                print(f"  Request {i+1}: FAILED after {request_time:.2f}s - {str(e)}")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        total_time = (datetime.now() - overall_start).total_seconds()
        success_rate = successful_requests / num_requests
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        requests_per_second = num_requests / total_time if total_time > 0 else 0
        avg_score = statistics.mean(scores) if scores else 0
        
        # Success criteria: >80% success rate and avg response time < 10s
        success = success_rate >= 0.8 and avg_response_time < 10.0
        
        print("\nBenchmark Summary:")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Avg Response Time: {avg_response_time:.2f}s")
        print(f"  Requests/Second: {requests_per_second:.2f}")
        
        return EvaluationResult(
            test_name=test_name,
            success=success,
            score=avg_score,
            response_time=total_time,
            expected_output={"min_success_rate": 0.8, "max_avg_response_time": 10.0},
            actual_output={"individual_results": individual_results},
            metadata={
                "num_requests": num_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "requests_per_second": requests_per_second,
                "response_times": response_times,
                "scores": scores,
                "avg_score": avg_score
            }
        )
    
    async def run_all_performance_benchmarks(self) -> EvaluationSuite:
        """Run all performance benchmarks using unified evaluation framework"""
        print("Starting performance benchmarking with unified framework...\n")
        
        results = []
        
        # Speed benchmark with different request counts
        for num_requests in [5, 10]:
            try:
                result = await self.benchmark_lead_qualification_speed(num_requests)
                results.append(result)
                status = "✅ PASS" if result.success else "❌ FAIL"
                print(f"{status}: {result.test_name}")
                print(f"  Success Rate: {result.metadata['success_rate']:.1%}")
                print(f"  Avg Response Time: {result.metadata['avg_response_time']:.2f}s")
                print(f"  Requests/Second: {result.metadata['requests_per_second']:.2f}")
            except Exception as e:
                error_result = EvaluationResult(
                    test_name=f"lead_qualification_speed_benchmark_{num_requests}_requests_error",
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                print(f"❌ FAIL: Speed benchmark ({num_requests} requests) - {str(e)}")
        
        # Create evaluation suite
        suite = EvaluationSuite(
            suite_name="Performance Benchmarks Testing Suite",
            results=results,
            timestamp=datetime.now()
        )
        
        return suite
    
    async def benchmark_concurrent_requests(self, concurrent_requests=5):
        """Test concurrent request handling"""
        print(f"\n=== Benchmarking Concurrent Requests ({concurrent_requests} parallel) ===")
        
        test_leads = [
            LeadQualificationRequest(
                name=f"Concurrent Test {i}",
                email=f"test{i}@concurrent.com", 
                company="Concurrent Corp",
                job_title="Test Role"
            ) for i in range(concurrent_requests)
        ]
        
        start_time = time.time()
        
        # Run requests concurrently
        tasks = []
        for i, lead in enumerate(test_leads):
            tasks.append(self._qualify_lead_with_timing(lead, i))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Process results
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "request_id": i,
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        if successful_results:
            response_times = [r["response_time"] for r in successful_results]
            avg_response_time = sum(response_times) / len(response_times)
            
            concurrent_summary = {
                "concurrent_requests": concurrent_requests,
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": len(successful_results) / concurrent_requests,
                "total_time": total_time,
                "avg_response_time": avg_response_time,
                "effective_requests_per_second": len(successful_results) / total_time
            }
            
            print("Concurrent Summary:")
            print(f"  Success Rate: {concurrent_summary['success_rate']:.1%}")
            print(f"  Avg Response Time: {avg_response_time:.2f}s")
            print(f"  Effective RPS: {concurrent_summary['effective_requests_per_second']:.2f}")
            
        else:
            concurrent_summary = {"error": "No successful concurrent requests"}
        
        return {
            "test_name": "concurrent_requests",
            "successful_results": successful_results,
            "failed_results": failed_results,
            "summary": concurrent_summary
        }
    
    async def _qualify_lead_with_timing(self, lead, request_id):
        """Helper method for concurrent testing"""
        start_time = time.time()
        
        try:
            result = self.lead_service.qualify_lead(lead)
            response_time = time.time() - start_time
            
            return {
                "request_id": request_id,
                "response_time": response_time,
                "score": result.score,
                "success": True
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            raise Exception(f"Request {request_id} failed after {response_time:.2f}s: {str(e)}")
    
    async def benchmark_message_personalization_speed(self, num_requests=3):
        """Benchmark message personalization (fewer requests due to complexity)"""
        print(f"\n=== Benchmarking Message Personalization ({num_requests} requests) ===")
        
        test_request = MessagePersonalizationRequest(
            lead_name="Benchmark User",
            lead_email="benchmark@test.com",
            company="Benchmark Inc",
            job_title="Test Executive",
            campaign_type="cold_outreach"
        )
        
        results = []
        start_time = time.time()
        
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                result = self.message_service.personalize_message(test_request)
                request_time = time.time() - request_start
                
                results.append({
                    "request_id": i + 1,
                    "response_time": request_time,
                    "variant_count": len(result.variants),
                    "total_chars": sum(len(v.subject) + len(v.body) for v in result.variants),
                    "success": True
                })
                
                print(f"  Request {i+1}: {request_time:.2f}s ({len(result.variants)} variants)")
                
            except Exception as e:
                request_time = time.time() - request_start
                results.append({
                    "request_id": i + 1,
                    "response_time": request_time,
                    "error": str(e),
                    "success": False
                })
                print(f"  Request {i+1}: FAILED after {request_time:.2f}s")
            
            # Longer delay for message requests
            await asyncio.sleep(2)
        
        total_time = time.time() - start_time
        successful_requests = [r for r in results if r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            
            message_summary = {
                "total_requests": num_requests,
                "successful_requests": len(successful_requests),
                "success_rate": len(successful_requests) / num_requests,
                "avg_response_time": avg_response_time,
                "avg_variants_per_request": sum(r.get("variant_count", 0) for r in successful_requests) / len(successful_requests),
                "total_time": total_time
            }
            
            print("Message Personalization Summary:")
            print(f"  Success Rate: {message_summary['success_rate']:.1%}")
            print(f"  Avg Response Time: {avg_response_time:.2f}s")
            print(f"  Avg Variants: {message_summary['avg_variants_per_request']:.1f}")
            
        else:
            message_summary = {"error": "No successful message requests"}
        
        return {
            "test_name": "message_personalization_speed", 
            "results": results,
            "summary": message_summary
        }

async def run_performance_benchmarks():
    """Run all performance benchmarks using unified evaluation framework"""
    evaluator = PerformanceBenchmarkEvaluator()
    suite = await evaluator.run_all_performance_benchmarks()
    
    # Save results using the framework
    from src.evaluation import evaluation_framework
    evaluation_framework.save_results(suite, "performance_benchmark_results.json")
    
    # Print summary
    print(f"\n✅ Performance benchmarking complete! Success rate: {suite.get_success_rate():.1%}")
    print(f"Average response time: {suite.get_average_response_time():.2f}s")
    
    # Print detailed summary
    print("\n=== DETAILED PERFORMANCE SUMMARY ===")
    for result in suite.results:
        if result.success:
            test_name = result.test_name.replace("_", " ").title()
            avg_response = result.metadata.get("avg_response_time", 0)
            success_rate = result.metadata.get("success_rate", 0)
            print(f"✅ {test_name}: {success_rate:.1%} success, {avg_response:.2f}s avg")
        else:
            print(f"❌ {result.test_name}: {result.error_message}")
    
    return suite

if __name__ == "__main__":
    asyncio.run(run_performance_benchmarks())
