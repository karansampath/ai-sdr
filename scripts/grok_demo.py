#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent)) # noqa: E402

from src.models import LeadQualificationRequest, MessagePersonalizationRequest
from src.grok import get_lead_qualification_service, get_message_personalization_service, GrokServiceError
from src.evaluation import evaluation_framework


load_dotenv()


# Demo data
DEMO_LEADS = [
    {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@enterprise-corp.com",
        "company": "Enterprise Corp",
        "job_title": "Chief Technology Officer", 
        "industry": "Technology",
        "company_size": "1000-5000 employees",
        "additional_context": "CTO at Fortune 500 company, actively looking for AI solutions to improve development workflows"
    },
    {
        "name": "Mike Chen",
        "email": "mike@startup-xyz.com",
        "company": "Startup XYZ",
        "job_title": "Founder",
        "industry": "FinTech",
        "company_size": "10-50 employees",
        "additional_context": "Early-stage startup focused on AI-powered financial analytics"
    },
    {
        "name": "Dr. Emily Rodriguez",
        "email": "e.rodriguez@healthsystem.org",
        "company": "Metro Health System",
        "job_title": "Chief Medical Officer",
        "industry": "Healthcare",
        "company_size": "500-1000 employees",
        "additional_context": "Leading digital transformation initiatives in healthcare, interested in AI for patient care optimization"
    }
]

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_subheader(title: str):
    """Print a formatted subheader."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def print_qualification_result(lead: dict[str, Any], result):
    """Print formatted lead qualification results."""
    print(f"Lead: {lead['name']} ({lead['company']})")
    print(f"Score: {result.score}/100")
    print(f"Priority: {result.priority_level.upper()}")
    print(f"Reasoning: {result.reasoning}")
    print("Key Factors:")
    for factor in result.key_factors:
        print(f"  • {factor}")
    print("Recommended Actions:")
    for action in result.recommended_actions:
        print(f"  • {action}")

def print_personalization_result(lead: dict[str, Any], result, campaign_type: str):
    """Print formatted message personalization results."""
    print(f"Lead: {lead['name']} ({lead['company']})")
    print(f"Campaign: {campaign_type}")
    print(f"Generated {len(result.variants)} message variant(s)")
    
    for i, variant in enumerate(result.variants, 1):
        print(f"\n  Variant {i} (Effectiveness: {variant.estimated_effectiveness}/100):")
        print(f"  Subject: {variant.subject}")
        print(f"  Body: {variant.body[:200]}{'...' if len(variant.body) > 200 else ''}")
    
    print("\nPersonalization Factors:")
    for factor in result.personalization_factors:
        print(f"  • {factor}")
    
    if result.best_send_time:
        print(f"Best Send Time: {result.best_send_time}")
    
    print(f"Follow-up Strategy: {result.follow_up_strategy}")

async def demo_lead_qualification():
    """Demonstrate lead qualification functionality."""
    print_header("GROK LEAD QUALIFICATION DEMO")
    
    qualification_service = get_lead_qualification_service()
    
    for i, lead_data in enumerate(DEMO_LEADS, 1):
        print_subheader(f"Lead {i}: {lead_data['name']}")
        
        try:
            # Create qualification request
            request = LeadQualificationRequest(**lead_data)
            
            # Qualify the lead
            print("Qualifying lead with Grok AI...")
            result = qualification_service.qualify_lead(request)
            
            print_qualification_result(lead_data, result)
            
        except GrokServiceError as e:
            print(f"❌ Grok service error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print()

async def demo_message_personalization():
    """Demonstrate message personalization functionality."""
    print_header("GROK MESSAGE PERSONALIZATION DEMO")
    
    personalization_service = get_message_personalization_service()
    
    # Different campaign scenarios
    campaigns = [
        ("cold_outreach", "professional"),
        ("follow_up", "friendly"),
        ("demo_request", "formal")
    ]
    
    for i, (campaign_type, tone) in enumerate(campaigns, 1):
        lead_data = DEMO_LEADS[i-1] if i <= len(DEMO_LEADS) else DEMO_LEADS[0]
        
        print_subheader(f"Campaign {i}: {campaign_type.replace('_', ' ').title()} - {tone.title()} Tone")
        
        try:
            # Create personalization request
            request = MessagePersonalizationRequest(
                lead_name=lead_data["name"],
                lead_email=lead_data["email"],
                company=lead_data["company"],
                job_title=lead_data["job_title"],
                industry=lead_data["industry"],
                campaign_type=campaign_type,
                message_tone=tone
            )
            
            # Generate personalized messages
            print("Generating personalized messages with Grok AI...")
            result = personalization_service.personalize_message(request)
            
            print_personalization_result(lead_data, result, campaign_type)
            
        except GrokServiceError as e:
            print(f"❌ Grok service error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print()

async def demo_evaluation_framework():
    """Demonstrate the evaluation framework."""
    print_header("GROK EVALUATION FRAMEWORK DEMO")
    
    print("Running comprehensive evaluation of all Grok services...")
    print("This tests consistency, accuracy, and robustness of AI responses.\n")
    
    try:
        # Run lead qualification evaluation
        print_subheader("Lead Qualification Evaluation")
        lead_suite = await evaluation_framework.lead_evaluator.run_evaluation_suite()
        
        summary = lead_suite.get_summary()
        print(f"✅ Tests completed: {summary['total_tests']}")
        print(f"✅ Success rate: {summary['success_rate']:.1%}")
        print(f"✅ Average response time: {summary['average_response_time']:.2f}s")
        print(f"✅ Average score: {summary['average_score']:.1f}")
        
        # Run message personalization evaluation
        print_subheader("Message Personalization Evaluation")
        message_suite = await evaluation_framework.message_evaluator.run_evaluation_suite()
        
        summary = message_suite.get_summary()
        print(f"✅ Tests completed: {summary['total_tests']}")
        print(f"✅ Success rate: {summary['success_rate']:.1%}")
        print(f"✅ Average response time: {summary['average_response_time']:.2f}s")
        print(f"✅ Average personalization score: {summary['average_score']:.1f}")
        
        print(f"\n📊 Detailed results saved to: {evaluation_framework.output_dir}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")

def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print_header("GROK ERROR HANDLING DEMO")
    
    print("Testing error handling with invalid data...")
    
    # Test with missing API key
    print_subheader("Invalid API Key Test")
    try:
        from src.grok import GrokClient
        
        # Temporarily save real API key
        real_key = os.environ.get("XAI_API_KEY")
        os.environ["XAI_API_KEY"] = "invalid_key"
        
        GrokClient()
        print("❌ Should have failed with invalid API key")
        
    except Exception as e:
        print(f"✅ Correctly handled invalid API key: {type(e).__name__}")
    finally:
        # Restore real API key if it existed
        if real_key:
            os.environ["XAI_API_KEY"] = real_key
        elif "XAI_API_KEY" in os.environ:
            del os.environ["XAI_API_KEY"]
    
    # Test with malformed request
    print_subheader("Invalid Request Test")
    try:
        get_lead_qualification_service()
        
        LeadQualificationRequest(
            name="",  # Empty name should still work
            email="invalid-email",  # Invalid email format
            company=None
        )
        
        print("Testing with potentially problematic data...")
        
    except Exception as e:
        print(f"✅ Correctly handled invalid request: {type(e).__name__}")

async def main():
    """Run the complete demo."""
    print("🤖 Welcome to the Grok AI-SDR System Demo!")
    print("This demo showcases advanced AI-powered sales development capabilities.")
    
    # Check if API key is set
    if not os.getenv("XAI_API_KEY"):
        print("\n❌ Error: XAI_API_KEY environment variable not set!")
        print("Please set your XAI API key: export XAI_API_KEY=your_api_key_here")
        return
    
    print("✅ XAI API Key configured")
    
    try:
        # Run demo sections
        await demo_lead_qualification()
        await demo_message_personalization()
        
        # Ask user if they want to run evaluations (they take longer)
        print("\n" + "="*60)
        response = input("Run comprehensive evaluation framework? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            await demo_evaluation_framework()
        
        # Demo error handling
        demo_error_handling()
        
        print_header("DEMO COMPLETE")
        print("🎉 Grok AI-SDR system demonstration completed!")
        print("\nKey Features Demonstrated:")
        print("  ✅ Structured lead qualification with 0-100 scoring")
        print("  ✅ Intelligent message personalization with multiple variants")
        print("  ✅ Comprehensive error handling and retry mechanisms")
        print("  ✅ Automated evaluation and testing framework")
        print("  ✅ Robust API integration with validation")
        
        print("\nNext Steps:")
        print("  🚀 Start the FastAPI server: python main.py")
        print("  🌐 Access the web interface at: http://localhost:8000")
        print("  📡 Use API endpoints for integration")
        print("  📊 Run evaluations via: POST /api/evaluate/all")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
