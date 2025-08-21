#!/usr/bin/env python3
"""
Master script to run all evaluation tests using unified evaluation framework
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation import EvaluationSuite, evaluation_framework
from prompt_variations import test_prompt_variations
from failure_cases import run_all_failure_tests
from consistency_testing import run_consistency_tests
from performance_benchmarks import run_performance_benchmarks

async def run_comprehensive_evaluation():
    """Run all evaluation tests in sequence"""
    print("=" * 60)
    print("AI-SDR COMPREHENSIVE EVALUATION SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_results = []
    test_summaries = {}
    
    # 1. Test prompt variations
    try:
        print("\n🧪 Running Prompt Variations Test...")
        prompt_suite = await test_prompt_variations()
        all_results.extend(prompt_suite.results)
        test_summaries["prompt_variations"] = {
            "success_rate": prompt_suite.get_success_rate(),
            "avg_response_time": prompt_suite.get_average_response_time(),
            "total_tests": len(prompt_suite.results)
        }
        print(f"✅ Prompt variations test completed: {prompt_suite.get_success_rate():.1%} success rate")
    except Exception as e:
        print(f"❌ Prompt variations test failed: {e}")
        test_summaries["prompt_variations"] = {"error": str(e)}
    
    # 2. Test failure cases
    try:
        print("\n🔥 Running Failure Cases Test...")
        failure_suite = await run_all_failure_tests()
        all_results.extend(failure_suite.results)
        test_summaries["failure_cases"] = {
            "success_rate": failure_suite.get_success_rate(),
            "avg_response_time": failure_suite.get_average_response_time(),
            "total_tests": len(failure_suite.results)
        }
        print(f"✅ Failure cases test completed: {failure_suite.get_success_rate():.1%} success rate")
    except Exception as e:
        print(f"❌ Failure cases test failed: {e}")
        test_summaries["failure_cases"] = {"error": str(e)}
    
    # 3. Test consistency
    try:
        print("\n🎯 Running Consistency Tests...")
        consistency_suite = await run_consistency_tests()
        all_results.extend(consistency_suite.results)
        test_summaries["consistency"] = {
            "success_rate": consistency_suite.get_success_rate(),
            "avg_response_time": consistency_suite.get_average_response_time(),
            "total_tests": len(consistency_suite.results)
        }
        print(f"✅ Consistency tests completed: {consistency_suite.get_success_rate():.1%} success rate")
    except Exception as e:
        print(f"❌ Consistency tests failed: {e}")
        test_summaries["consistency"] = {"error": str(e)}
    
    # 4. Run performance benchmarks
    try:
        print("\n⚡ Running Performance Benchmarks...")
        performance_suite = await run_performance_benchmarks()
        all_results.extend(performance_suite.results)
        test_summaries["performance"] = {
            "success_rate": performance_suite.get_success_rate(),
            "avg_response_time": performance_suite.get_average_response_time(),
            "total_tests": len(performance_suite.results)
        }
        print(f"✅ Performance benchmarks completed: {performance_suite.get_success_rate():.1%} success rate")
    except Exception as e:
        print(f"❌ Performance benchmarks failed: {e}")
        test_summaries["performance"] = {"error": str(e)}
    
    # Create comprehensive evaluation suite
    comprehensive_suite = EvaluationSuite(
        suite_name="Comprehensive AI-SDR Evaluation",
        results=all_results,
        timestamp=datetime.now()
    )
    
    # Save results using the unified framework
    evaluation_framework.save_results(comprehensive_suite, "comprehensive_evaluation_results.json")
    
    # Generate final report
    generate_final_report(comprehensive_suite, test_summaries)
    
    print("\n" + "=" * 60)
    print("🎉 COMPREHENSIVE EVALUATION COMPLETED")
    print(f"📊 Overall Success Rate: {comprehensive_suite.get_success_rate():.1%}")
    print(f"⏱️  Average Response Time: {comprehensive_suite.get_average_response_time():.2f}s")
    print(f"📝 Total Tests: {len(comprehensive_suite.results)}")
    print("=" * 60)
    
    return comprehensive_suite

def generate_final_report(suite: EvaluationSuite, test_summaries: dict):
    """Generate a summary report using unified evaluation framework"""
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY REPORT")
    print("=" * 60)
    
    # Overall statistics
    print(f"Overall Success Rate: {suite.get_success_rate():.1%}")
    print(f"Total Individual Tests: {len(suite.results)}")
    print(f"Average Response Time: {suite.get_average_response_time():.2f}s")
    
    # Test suite summaries
    print("\n📋 DETAILED TEST SUITE SUMMARY:")
    suite_count = 0
    successful_suites = 0
    
    for test_name, summary in test_summaries.items():
        suite_count += 1
        if "error" in summary:
            print(f"❌ {test_name.replace('_', ' ').title()}: FAILED - {summary['error']}")
        else:
            successful_suites += 1
            print(f"✅ {test_name.replace('_', ' ').title()}: {summary['success_rate']:.1%} success")
            print(f"   └── {summary['total_tests']} tests, {summary['avg_response_time']:.2f}s avg response time")
    
    if suite_count > 0:
        print(f"\nTest Suite Success Rate: {successful_suites}/{suite_count} ({successful_suites/suite_count:.1%})")
    
    # Performance insights
    print("\n📈 PERFORMANCE INSIGHTS:")
    failed_tests = [r for r in suite.results if not r.success]
    if failed_tests:
        print(f"   • {len(failed_tests)} individual tests failed")
    
    consistency_tests = [r for r in suite.results if "consistency" in r.test_name]
    if consistency_tests:
        consistent_count = sum(1 for t in consistency_tests if t.success)
        print(f"   • Consistency: {consistent_count}/{len(consistency_tests)} tests passed")
    
    performance_tests = [r for r in suite.results if "benchmark" in r.test_name]
    if performance_tests:
        avg_perf = sum(r.metadata.get("avg_response_time", 0) for r in performance_tests if r.metadata and "avg_response_time" in r.metadata)
        if len([r for r in performance_tests if r.metadata and "avg_response_time" in r.metadata]) > 0:
            avg_perf = avg_perf / len([r for r in performance_tests if r.metadata and "avg_response_time" in r.metadata])
            print(f"   • Average performance: {avg_perf:.2f}s response time")
    
    # Recommendations
    print("\n🔍 RECOMMENDATIONS:")
    if suite.get_success_rate() < 0.8:
        print("   1. ⚠️  Low success rate - investigate failing test cases")
    if suite.get_average_response_time() > 5.0:
        print("   2. ⚠️  High response times - optimize API calls or add caching")
    
    print("   3. 💡 Monitor consistency metrics in production deployment")
    print("   4. 💡 Consider implementing retry mechanisms for failed requests")
    print("   5. 💡 Add more edge cases based on production data patterns")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_evaluation())
