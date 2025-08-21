from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent)) # noqa: E402


from src.database import get_db_manager
from src.models import (
    Lead, LeadWithInteractions, Interaction, LeadCreate, LeadUpdate,
    LeadQualificationRequest, LeadQualificationResponse,
    MessagePersonalizationRequest, MessagePersonalizationResponse,
    ScoringCriteria, ScoringCriteriaCreate, ScoringCriteriaUpdate,
    PipelineStage, LeadPipelineHistory, LeadWithPipeline, SearchRequest
)
from src.grok import (
    get_lead_qualification_service,
    get_message_personalization_service,
    GrokServiceError
)
from src.evaluation import evaluation_framework
from src.services import scoring_criteria_service, pipeline_service, search_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI-SDR System",
    description="A Grok-powered Sales Development Representative system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_leads_from_db() -> list[Lead]:
    """Fetch all leads from the database."""
    with get_db_manager().get_connection() as conn:
        result = conn.execute("""
            SELECT id, name, email, company, job_title, phone, lead_source, 
                   status, score, notes, created_at, updated_at 
            FROM leads 
            ORDER BY updated_at DESC
        """).fetchall()
        
        leads = []
        for row in result:
            lead = Lead(
                id=row[0],
                name=row[1],
                email=row[2],
                company=row[3],
                job_title=row[4],
                phone=row[5],
                lead_source=row[6],
                status=row[7],
                score=row[8],
                notes=row[9],
                created_at=row[10],
                updated_at=row[11]
            )
            leads.append(lead)
        
        return leads


def get_lead_by_id(lead_id: int) -> LeadWithInteractions:
    """Fetch a specific lead with interactions from the database."""
    with get_db_manager().get_connection() as conn:
        # Get lead data
        lead_result = conn.execute("""
            SELECT id, name, email, company, job_title, phone, lead_source,
                   status, score, notes, created_at, updated_at
            FROM leads 
            WHERE id = ?
        """, (lead_id,)).fetchone()
        
        if not lead_result:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get interactions for this lead
        interactions_result = conn.execute("""
            SELECT id, lead_id, interaction_type, content, created_at
            FROM interactions 
            WHERE lead_id = ?
            ORDER BY created_at DESC
        """, (lead_id,)).fetchall()
        
        # Create lead object
        lead = Lead(
            id=lead_result[0],
            name=lead_result[1],
            email=lead_result[2],
            company=lead_result[3],
            job_title=lead_result[4],
            phone=lead_result[5],
            lead_source=lead_result[6],
            status=lead_result[7],
            score=lead_result[8],
            notes=lead_result[9],
            created_at=lead_result[10],
            updated_at=lead_result[11]
        )
        
        # Create interactions
        interactions = []
        for row in interactions_result:
            interaction = Interaction(
                id=row[0],
                lead_id=row[1],
                interaction_type=row[2],
                content=row[3],
                created_at=row[4]
            )
            interactions.append(interaction)
        
        return LeadWithInteractions(**lead.model_dump(), interactions=interactions)


@app.get("/")
async def root():
    """Root endpoint - redirect users to Streamlit frontend."""
    return JSONResponse({
        "message": "AI-SDR API Server",
        "status": "running",
        "frontend_url": "http://localhost:8501",
    })


# API Endpoints for Lead Management

@app.get("/api/leads", response_model=list[Lead])
async def get_all_leads():
    """Get all leads from the database."""
    try:
        leads = get_leads_from_db()
        return leads
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")


@app.post("/api/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    """Create a new lead."""
    try:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                INSERT INTO leads (name, email, company, job_title, phone, lead_source, status, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id, created_at, updated_at
            """, [
                lead.name, lead.email, lead.company, lead.job_title,
                lead.phone, lead.lead_source, lead.status, lead.score, lead.notes
            ]).fetchone()
            
            return Lead(
                id=result[0],
                created_at=result[1],
                updated_at=result[2],
                **lead.model_dump()
            )
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")


@app.put("/api/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, lead_update: LeadUpdate):
    """Update an existing lead."""
    try:
        # Get existing lead
        existing_lead = get_lead_by_id(lead_id)
        
        # Prepare update data
        update_data = lead_update.model_dump(exclude_unset=True)
        if not update_data:
            return existing_lead
        
        # Build dynamic update query
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(lead_id)
        
        with get_db_manager().get_connection() as conn:
            conn.execute(f"""
                UPDATE leads 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            # Return updated lead
            return get_lead_by_id(lead_id)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lead")


# AI Services API Endpoints

@app.post("/api/leads/qualify", response_model=LeadQualificationResponse)
async def qualify_lead_endpoint(request: LeadQualificationRequest):
    """Qualify a lead using Grok AI and return structured scoring."""
    try:
        qualification_service = get_lead_qualification_service()
        result = qualification_service.qualify_lead(request)
        
        logger.info(f"Lead qualification completed for {request.name}: score {result.score}")
        return result
        
    except GrokServiceError as e:
        logger.error(f"Grok service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in lead qualification: {str(e)}")
        raise HTTPException(status_code=500, detail="Lead qualification failed")


@app.post("/api/leads/{lead_id}/qualify")
async def qualify_existing_lead(lead_id: int):
    """Qualify an existing lead and update their score."""
    try:
        # Get existing lead
        lead = get_lead_by_id(lead_id)
        
        # Create qualification request
        qualification_request = LeadQualificationRequest(
            name=lead.name,
            email=lead.email,
            company=lead.company,
            job_title=lead.job_title,
            additional_context=lead.notes
        )
        
        # Get qualification
        qualification_service = get_lead_qualification_service()
        result = qualification_service.qualify_lead(qualification_request)
        
        # Update lead score in database
        with get_db_manager().get_connection() as conn:
            conn.execute("""
                UPDATE leads 
                SET score = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [result.score, f"{lead.notes or ''}\n\nAI Qualification: {result.reasoning}", lead_id])
        
        return JSONResponse({
            "success": True,
            "message": "Lead qualified successfully",
            "data": {
                "lead_id": lead_id,
                "previous_score": lead.score,
                "new_score": result.score,
                "qualification": result.model_dump()
            }
        })
        
    except HTTPException:
        raise
    except GrokServiceError as e:
        logger.error(f"Grok service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error qualifying existing lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Lead qualification failed")


@app.post("/api/messages/personalize", response_model=MessagePersonalizationResponse)
async def personalize_message_endpoint(request: MessagePersonalizationRequest):
    """Generate personalized messages using Grok AI."""
    try:
        personalization_service = get_message_personalization_service()
        result = personalization_service.personalize_message(request)
        
        logger.info(f"Message personalization completed for {request.lead_name}: {len(result.variants)} variants")
        return result
        
    except GrokServiceError as e:
        logger.error(f"Grok service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in message personalization: {str(e)}")
        raise HTTPException(status_code=500, detail="Message personalization failed")


@app.post("/api/leads/{lead_id}/personalize")
async def personalize_message_for_lead(lead_id: int, campaign_type: str = "cold_outreach", message_tone: str = "professional"):
    """Generate personalized messages for an existing lead."""
    try:
        # Get existing lead
        lead = get_lead_by_id(lead_id)
        
        # Get previous interactions for context
        previous_interactions = [
            interaction.content for interaction in lead.interactions 
            if interaction.content
        ][-3:]  # Last 3 interactions
        
        # Create personalization request
        personalization_request = MessagePersonalizationRequest(
            lead_name=lead.name,
            lead_email=lead.email,
            company=lead.company,
            job_title=lead.job_title,
            lead_source=lead.lead_source,
            previous_interactions=previous_interactions,
            campaign_type=campaign_type,
            message_tone=message_tone
        )
        
        # Get personalization
        personalization_service = get_message_personalization_service()
        result = personalization_service.personalize_message(personalization_request)
        
        return JSONResponse({
            "success": True,
            "message": "Messages personalized successfully",
            "data": {
                "lead_id": lead_id,
                "campaign_type": campaign_type,
                "personalization": result.model_dump()
            }
        })
        
    except HTTPException:
        raise
    except GrokServiceError as e:
        logger.error(f"Grok service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error personalizing message for lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Message personalization failed")


# Evaluation Endpoints

@app.post("/api/evaluate/all")
async def run_full_evaluation():
    """Run comprehensive evaluation of all Grok services."""
    try:
        logger.info("Starting full evaluation suite")
        results = await evaluation_framework.run_full_evaluation()
        
        # Extract summaries for response
        summaries = {}
        for suite_name, suite in results.items():
            summaries[suite_name] = suite.get_summary()
        
        return JSONResponse({
            "success": True,
            "message": "Full evaluation completed",
            "data": {
                "evaluation_results": summaries,
                "overall_success_rate": sum(s["success_rate"] for s in summaries.values()) / len(summaries) if summaries else 0,
                "total_tests": sum(s["total_tests"] for s in summaries.values()),
                "results_saved_to": str(evaluation_framework.output_dir)
            }
        })
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/api/evaluate/lead-qualification")
async def run_lead_qualification_evaluation():
    """Run evaluation specifically for lead qualification service."""
    try:
        logger.info("Starting lead qualification evaluation")
        suite = await evaluation_framework.lead_evaluator.run_evaluation_suite()
        evaluation_framework.save_results(suite)
        
        return JSONResponse({
            "success": True,
            "message": "Lead qualification evaluation completed",
            "data": suite.get_summary()
        })
        
    except Exception as e:
        logger.error(f"Lead qualification evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/api/evaluate/message-personalization")
async def run_message_personalization_evaluation():
    """Run evaluation specifically for message personalization service."""
    try:
        logger.info("Starting message personalization evaluation")
        suite = await evaluation_framework.message_evaluator.run_evaluation_suite()
        evaluation_framework.save_results(suite)
        
        return JSONResponse({
            "success": True,
            "message": "Message personalization evaluation completed",
            "data": suite.get_summary()
        })
        
    except Exception as e:
        logger.error(f"Message personalization evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# Scoring Criteria Management Endpoints

@app.get("/api/scoring-criteria", response_model=list[ScoringCriteria])
async def get_scoring_criteria():
    """Get all active scoring criteria."""
    try:
        criteria = scoring_criteria_service.get_active_criteria()
        return criteria
    except Exception as e:
        logger.error(f"Error fetching scoring criteria: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scoring criteria")

@app.post("/api/scoring-criteria", response_model=ScoringCriteria)
async def create_scoring_criteria(criteria: ScoringCriteriaCreate):
    """Create new scoring criteria."""
    try:
        new_criteria = scoring_criteria_service.create_criteria(criteria)
        return new_criteria
    except Exception as e:
        logger.error(f"Error creating scoring criteria: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scoring criteria")

@app.put("/api/scoring-criteria/{criteria_id}", response_model=ScoringCriteria)
async def update_scoring_criteria(criteria_id: int, update: ScoringCriteriaUpdate):
    """Update existing scoring criteria."""
    try:
        updated_criteria = scoring_criteria_service.update_criteria(criteria_id, update)
        if not updated_criteria:
            raise HTTPException(status_code=404, detail="Scoring criteria not found")
        return updated_criteria
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scoring criteria: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scoring criteria")


# Pipeline Management Endpoints

@app.get("/api/pipeline/stages", response_model=list[PipelineStage])
async def get_pipeline_stages():
    """Get all active pipeline stages."""
    try:
        stages = pipeline_service.get_active_stages()
        return stages
    except Exception as e:
        logger.error(f"Error fetching pipeline stages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pipeline stages")

@app.post("/api/leads/{lead_id}/pipeline/move")
async def move_lead_to_stage(lead_id: int, stage_id: int, notes: Optional[str] = None):
    """Move a lead to a different pipeline stage."""
    try:
        # Verify lead exists
        get_lead_by_id(lead_id)
        
        # Move lead to new stage
        history_entry = pipeline_service.move_lead_to_stage(lead_id, stage_id, notes)
        
        return JSONResponse({
            "success": True,
            "message": "Lead moved to new stage successfully",
            "data": {
                "lead_id": lead_id,
                "stage_id": stage_id,
                "history_entry_id": history_entry.id,
                "entered_at": history_entry.entered_at.isoformat()
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving lead {lead_id} to stage {stage_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to move lead to stage")

@app.get("/api/leads/{lead_id}/pipeline", response_model=LeadWithPipeline)
async def get_lead_with_pipeline(lead_id: int):
    """Get lead with full pipeline history."""
    try:
        # Get basic lead data
        lead = get_lead_by_id(lead_id)
        
        # Get current stage
        current_stage = pipeline_service.get_lead_current_stage(lead_id)
        
        # Get pipeline history
        with get_db_manager().get_connection() as conn:
            history_result = conn.execute("""
                SELECT id, lead_id, stage_id, previous_stage_id, entered_at, exited_at, notes
                FROM lead_pipeline_history
                WHERE lead_id = ?
                ORDER BY entered_at DESC
            """, (lead_id,)).fetchall()
        
        pipeline_history = [
            LeadPipelineHistory(
                id=row[0], lead_id=row[1], stage_id=row[2], 
                previous_stage_id=row[3], entered_at=row[4], 
                exited_at=row[5], notes=row[6]
            ) for row in history_result
        ]
        
        return LeadWithPipeline(
            **lead.model_dump(),
            current_stage=current_stage,
            pipeline_history=pipeline_history,
            interactions=lead.interactions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lead pipeline data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lead pipeline data")


# Search Endpoints

@app.post("/api/search/leads")
async def search_leads_endpoint(search_request: SearchRequest):
    """Search leads by query and filters."""
    try:
        results = search_service.search_leads(
            query=search_request.query,
            filters=search_request.filters,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        return {
            "success": True,
            "data": {
                "leads": results,  # Let FastAPI handle serialization automatically
                "query": search_request.query,
                "filters": search_request.filters,
                "count": len(results),
                "limit": search_request.limit,
                "offset": search_request.offset
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching leads: {e}")
        raise HTTPException(status_code=500, detail="Lead search failed")

@app.post("/api/search/interactions")
async def search_interactions_endpoint(search_request: SearchRequest):
    """Search interactions and conversations."""
    try:
        results = search_service.search_interactions(
            query=search_request.query,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        return JSONResponse({
            "success": True,
            "data": {
                "interactions": results,
                "query": search_request.query,
                "count": len(results),
                "limit": search_request.limit,
                "offset": search_request.offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching interactions: {e}")
        raise HTTPException(status_code=500, detail="Interaction search failed")


# Enhanced Lead Management with Custom Scoring

@app.post("/api/leads/{lead_id}/rescore")
async def rescore_lead_with_custom_criteria(lead_id: int):
    """Re-score a lead using current custom scoring criteria."""
    try:
        # Get lead and current scoring criteria
        lead = get_lead_by_id(lead_id)
        criteria = scoring_criteria_service.get_active_criteria()
        
        # Create enhanced qualification service with custom criteria
        criteria_data = [
            {"name": c.name, "description": c.description, "weight": c.weight}
            for c in criteria
        ]
        qualification_service = get_lead_qualification_service()
        qualification_service.scoring_criteria = criteria_data
        
        # Create qualification request
        qualification_request = LeadQualificationRequest(
            name=lead.name,
            email=lead.email,
            company=lead.company,
            job_title=lead.job_title,
            additional_context=lead.notes
        )
        
        # Get new qualification with custom criteria
        result = qualification_service.qualify_lead(qualification_request)
        
        # Update lead score in database
        with get_db_manager().get_connection() as conn:
            conn.execute("""
                UPDATE leads 
                SET score = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [
                result.score, 
                f"{lead.notes or ''}\n\nCustom Re-scoring: {result.reasoning}",
                lead_id
            ])
        
        return JSONResponse({
            "success": True,
            "message": "Lead re-scored with custom criteria",
            "data": {
                "lead_id": lead_id,
                "previous_score": lead.score,
                "new_score": result.score,
                "custom_criteria_used": len(criteria_data),
                "qualification": result.model_dump()
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-scoring lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Lead re-scoring failed")


# Meeting Coordination Endpoint
@app.post("/api/leads/{lead_id}/coordinate-meeting")
async def coordinate_meeting(lead_id: int, preferred_times: Optional[list[str]] = None):
    """Suggest meeting times for a lead."""
    try:
        # Get lead for context
        lead = get_lead_by_id(lead_id)
        
        # Generate suggested meeting times (simplified logic)
        from datetime import datetime, timedelta
        
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        suggested_times = []
        
        for i in range(5):  # Suggest 5 time slots
            time_slot = base_time + timedelta(days=i+1, hours=i%3*2)  # Vary hours
            suggested_times.append({
                "datetime": time_slot.isoformat(),
                "formatted": time_slot.strftime("%A, %B %d at %I:%M %p"),
                "duration": "30 minutes",
                "meeting_type": "discovery_call" if lead.score < 50 else "demo"
            })
        
        # Save interaction record
        with get_db_manager().get_connection() as conn:
            conn.execute("""
                INSERT INTO interactions (lead_id, interaction_type, content)
                VALUES (?, ?, ?)
            """, [lead_id, "note", f"Meeting coordination requested - suggested {len(suggested_times)} time slots"])
        
        return JSONResponse({
            "success": True,
            "message": "Meeting times suggested successfully",
            "data": {
                "lead_id": lead_id,
                "lead_name": lead.name,
                "suggested_times": suggested_times,
                "meeting_link": f"https://calendly.com/your-company/{lead.name.lower().replace(' ', '-')}",
                "instructions": "Please select your preferred time slot and we'll send a calendar invite."
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error coordinating meeting for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Meeting coordination failed")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-sdr"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
