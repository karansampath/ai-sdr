from typing import List, Optional, Dict, Any
import logging

from .database import get_db_manager
from .models import (
    ScoringCriteria, ScoringCriteriaCreate, ScoringCriteriaUpdate,
    PipelineStage, LeadPipelineHistory, Lead
)

logger = logging.getLogger(__name__)


class ScoringCriteriaService:
    @staticmethod
    def get_active_criteria() -> List[ScoringCriteria]:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                SELECT id, name, description, weight, is_active, created_at, updated_at
                FROM scoring_criteria 
                WHERE is_active = true
                ORDER BY weight DESC
            """).fetchall()
            
            return [
                ScoringCriteria(
                    id=row[0], name=row[1], description=row[2], 
                    weight=row[3], is_active=row[4], created_at=row[5], updated_at=row[6]
                ) for row in result
            ]
    
    @staticmethod
    def create_criteria(criteria: ScoringCriteriaCreate) -> ScoringCriteria:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                INSERT INTO scoring_criteria (name, description, weight, is_active)
                VALUES (?, ?, ?, ?)
                RETURNING id, created_at, updated_at
            """, [criteria.name, criteria.description, criteria.weight, criteria.is_active]).fetchone()
            
            return ScoringCriteria(
                id=result[0], created_at=result[1], updated_at=result[2], **criteria.model_dump()
            )
    
    @staticmethod
    def update_criteria(criteria_id: int, update: ScoringCriteriaUpdate) -> Optional[ScoringCriteria]:
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            return ScoringCriteriaService.get_by_id(criteria_id)
        
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(criteria_id)
        
        with get_db_manager().get_connection() as conn:
            conn.execute(f"""
                UPDATE scoring_criteria 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
        
        return ScoringCriteriaService.get_by_id(criteria_id)
    
    @staticmethod
    def get_by_id(criteria_id: int) -> Optional[ScoringCriteria]:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                SELECT id, name, description, weight, is_active, created_at, updated_at
                FROM scoring_criteria WHERE id = ?
            """, (criteria_id,)).fetchone()
            
            if not result:
                return None
                
            return ScoringCriteria(
                id=result[0], name=result[1], description=result[2], 
                weight=result[3], is_active=result[4], created_at=result[5], updated_at=result[6]
            )


class PipelineService:
    @staticmethod
    def get_active_stages() -> List[PipelineStage]:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                SELECT id, name, description, stage_order, is_active, auto_progression_rules, created_at, updated_at
                FROM pipeline_stages 
                WHERE is_active = true
                ORDER BY stage_order
            """).fetchall()
            
            return [
                PipelineStage(
                    id=row[0], name=row[1], description=row[2], stage_order=row[3],
                    is_active=row[4], auto_progression_rules=row[5], created_at=row[6], updated_at=row[7]
                ) for row in result
            ]
    
    @staticmethod
    def move_lead_to_stage(lead_id: int, stage_id: int, notes: Optional[str] = None) -> LeadPipelineHistory:
        with get_db_manager().get_connection() as conn:
            # Get current stage
            current_stage = conn.execute("""
                SELECT stage_id FROM lead_pipeline_history 
                WHERE lead_id = ? AND exited_at IS NULL
                ORDER BY entered_at DESC LIMIT 1
            """, (lead_id,)).fetchone()
            
            current_stage_id = current_stage[0] if current_stage else None
            
            # Exit current stage if exists
            if current_stage_id:
                conn.execute("""
                    UPDATE lead_pipeline_history 
                    SET exited_at = CURRENT_TIMESTAMP 
                    WHERE lead_id = ? AND stage_id = ? AND exited_at IS NULL
                """, [lead_id, current_stage_id])
            
            # Enter new stage
            result = conn.execute("""
                INSERT INTO lead_pipeline_history (lead_id, stage_id, previous_stage_id, notes)
                VALUES (?, ?, ?, ?)
                RETURNING id, entered_at
            """, [lead_id, stage_id, current_stage_id, notes]).fetchone()
            
            # Update lead status if needed
            stage_name = conn.execute("SELECT name FROM pipeline_stages WHERE id = ?", (stage_id,)).fetchone()[0]
            conn.execute("""
                UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, [stage_name.lower().replace(" ", "_"), lead_id])
            
            return LeadPipelineHistory(
                id=result[0], lead_id=lead_id, stage_id=stage_id, 
                previous_stage_id=current_stage_id, entered_at=result[1], notes=notes
            )
    
    @staticmethod
    def get_lead_current_stage(lead_id: int) -> Optional[PipelineStage]:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                SELECT s.id, s.name, s.description, s.stage_order, s.is_active, s.auto_progression_rules, s.created_at, s.updated_at
                FROM pipeline_stages s
                JOIN lead_pipeline_history h ON s.id = h.stage_id
                WHERE h.lead_id = ? AND h.exited_at IS NULL
                ORDER BY h.entered_at DESC LIMIT 1
            """, (lead_id,)).fetchone()
            
            if not result:
                return None
                
            return PipelineStage(
                id=result[0], name=result[1], description=result[2], stage_order=result[3],
                is_active=result[4], auto_progression_rules=result[5], created_at=result[6], updated_at=result[7]
            )


class SearchService:
    @staticmethod
    def search_leads(query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Lead]:
        with get_db_manager().get_connection() as conn:
            where_clauses = ["1=1"]
            params = []
            
            # Text search across multiple fields
            if query.strip():
                where_clauses.append("""(
                    LOWER(name) LIKE LOWER(?) OR 
                    LOWER(email) LIKE LOWER(?) OR 
                    LOWER(company) LIKE LOWER(?) OR 
                    LOWER(job_title) LIKE LOWER(?) OR
                    LOWER(notes) LIKE LOWER(?)
                )""")
                search_term = f"%{query}%"
                params.extend([search_term] * 5)
            
            # Apply filters
            if filters:
                if filters.get("status"):
                    where_clauses.append("status = ?")
                    params.append(filters["status"])
                
                if filters.get("lead_source"):
                    where_clauses.append("lead_source = ?")
                    params.append(filters["lead_source"])
                
                if filters.get("min_score"):
                    where_clauses.append("score >= ?")
                    params.append(filters["min_score"])
                
                if filters.get("max_score"):
                    where_clauses.append("score <= ?")
                    params.append(filters["max_score"])
            
            params.extend([limit, offset])
            
            result = conn.execute(f"""
                SELECT id, name, email, company, job_title, phone, lead_source, 
                       status, score, notes, created_at, updated_at 
                FROM leads 
                WHERE {' AND '.join(where_clauses)}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, params).fetchall()
            
            return [
                Lead(
                    id=row[0], name=row[1], email=row[2], company=row[3],
                    job_title=row[4], phone=row[5], lead_source=row[6],
                    status=row[7], score=row[8], notes=row[9],
                    created_at=row[10], updated_at=row[11]
                ) for row in result
            ]
    
    @staticmethod
    def search_interactions(query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        with get_db_manager().get_connection() as conn:
            result = conn.execute("""
                SELECT i.id, i.lead_id, i.interaction_type, i.content, i.created_at,
                       l.name as lead_name, l.email as lead_email, l.company
                FROM interactions i
                JOIN leads l ON i.lead_id = l.id
                WHERE LOWER(i.content) LIKE LOWER(?)
                ORDER BY i.created_at DESC
                LIMIT ? OFFSET ?
            """, [f"%{query}%", limit, offset]).fetchall()
            
            return [
                {
                    "interaction_id": row[0], "lead_id": row[1], "interaction_type": row[2],
                    "content": row[3], "created_at": row[4], "lead_name": row[5],
                    "lead_email": row[6], "lead_company": row[7]
                } for row in result
            ]


# Service instances
scoring_criteria_service = ScoringCriteriaService()
pipeline_service = PipelineService()
search_service = SearchService()
