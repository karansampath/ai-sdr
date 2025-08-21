import os
import time
import logging
from typing import Optional, Any

from dotenv import load_dotenv
from pydantic import ValidationError
from xai_sdk import Client
from xai_sdk.chat import system, user

from .models import (
    LeadQualificationRequest,
    LeadQualificationResponse,
    MessagePersonalizationRequest,
    MessagePersonalizationResponse
)
from .prompts.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class GrokServiceError(Exception):
    pass


class GrokRateLimitError(GrokServiceError):
    pass


class GrokValidationError(GrokServiceError):
    pass


class GrokClient:
    
    def __init__(self, api_key: Optional[str] = None, model: str = "grok-4", timeout: int = 3600):
        load_dotenv()

        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise GrokServiceError("XAI_API_KEY environment variable not set")
        
        self.model = model
        self.timeout = timeout
        self.client = Client(
            api_key=self.api_key,
            timeout=self.timeout
        )
        
        logger.info(f"Initialized GrokClient with model: {model}")
    
    def _create_chat(self):
        return self.client.chat.create(model=self.model)
    
    def _retry_on_error(self, func, max_retries: int = 2, backoff_factor: float = 1.0):
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limiting (429) or server errors (5xx)
                if "429" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise GrokRateLimitError(f"Rate limit exceeded after {max_retries + 1} attempts")
                
                elif any(code in error_msg for code in ["500", "502", "503", "504"]):
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Server error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise GrokServiceError(f"Server error after {max_retries + 1} attempts: {str(e)}")
                
                else:
                    # Non-retryable error, re-raise immediately
                    raise GrokServiceError(f"Grok API error: {str(e)}")
        
        raise GrokServiceError("Unexpected error in retry logic")
    
    def _validate_and_parse_response(self, response_tuple: tuple[Any, Any], expected_model: type) -> tuple[Any, Any]:
        try:
            response, parsed_object = response_tuple
            
            if not isinstance(parsed_object, expected_model):
                raise GrokValidationError(f"Expected {expected_model.__name__}, got {type(parsed_object).__name__}")
            
            logger.info(f"Successfully parsed {expected_model.__name__} response")
            return response, parsed_object
            
        except (ValidationError, ValueError) as e:
            raise GrokValidationError(f"Failed to validate response: {str(e)}")
        except Exception as e:
            raise GrokServiceError(f"Failed to parse response: {str(e)}")


class LeadQualificationService(GrokClient):
    
    def __init__(self, api_key: Optional[str] = None, model: str = "grok-4", timeout: int = 3600, scoring_criteria: Optional[list] = None):
        super().__init__(api_key, model, timeout)
        self.scoring_criteria = scoring_criteria or []
    
    def qualify_lead(self, request: LeadQualificationRequest, context: Optional[dict] = None) -> LeadQualificationResponse:
        """
        Qualify a lead using Grok AI and return structured results.
        
        Args:
            request: Lead qualification request with lead details
            
        Returns:
            LeadQualificationResponse: Structured qualification results
            
        Raises:
            GrokServiceError: When qualification fails
        """
        logger.info(f"Qualifying lead: {request.name} from {request.company}")
        
        def _perform_qualification():
            chat = self._create_chat()
            
            # Generate system prompt with context
            system_prompt = prompt_manager.get_system_prompt(
                "lead_qualification",
                scoring_criteria=self.scoring_criteria,
                company_context=context.get("company_context") if context else None,
                industry_insights=context.get("industry_insights") if context else None
            )
            chat.append(system(system_prompt))
            
            # Generate user prompt
            user_prompt = prompt_manager.get_user_prompt(
                "lead_qualification",
                name=request.name,
                email=request.email,
                company=request.company,
                job_title=request.job_title,
                industry=request.industry,
                company_size=request.company_size,
                website=request.website,
                additional_context=request.additional_context,
                previous_interactions=context.get("previous_interactions") if context else None,
                lead_source_context=context.get("lead_source_context") if context else None
            )
            chat.append(user(user_prompt))
            
            # Get structured response
            return chat.parse(LeadQualificationResponse)
        
        try:
            response_tuple = self._retry_on_error(_perform_qualification)
            response, qualification = self._validate_and_parse_response(
                response_tuple, LeadQualificationResponse
            )
            
            logger.info(f"Lead qualified successfully: {request.name} scored {qualification.score}")
            return qualification
            
        except Exception as e:
            logger.error(f"Lead qualification failed for {request.name}: {str(e)}")
            raise


class MessagePersonalizationService(GrokClient):
    
    def __init__(self, api_key: Optional[str] = None, model: str = "grok-4", timeout: int = 3600, message_guidelines: Optional[list] = None):
        super().__init__(api_key, model, timeout)
        self.message_guidelines = message_guidelines or []
    
    def personalize_message(self, request: MessagePersonalizationRequest, context: Optional[dict] = None) -> MessagePersonalizationResponse:
        logger.info(f"Personalizing message for: {request.lead_name} - {request.campaign_type}")
        
        def _perform_personalization():
            chat = self._create_chat()
            
            # Generate system prompt with context
            system_prompt = prompt_manager.get_system_prompt(
                "message_personalization",
                message_guidelines=self.message_guidelines,
                company_messaging=context.get("company_messaging") if context else None,
                industry_templates=context.get("industry_templates") if context else None
            )
            chat.append(system(system_prompt))
            
            # Generate user prompt
            user_prompt = prompt_manager.get_user_prompt(
                "message_personalization",
                lead_name=request.lead_name,
                lead_email=request.lead_email,
                company=request.company,
                job_title=request.job_title,
                industry=request.industry,
                lead_source=request.lead_source,
                previous_interactions=request.previous_interactions,
                campaign_type=request.campaign_type,
                message_tone=request.message_tone,
                campaign_context=context.get("campaign_context") if context else None,
                company_research=context.get("company_research") if context else None,
                pain_points=context.get("pain_points") if context else None,
                value_propositions=context.get("value_propositions") if context else None,
                variant_count=context.get("variant_count") if context else None
            )
            chat.append(user(user_prompt))
            
            # Get structured response
            return chat.parse(MessagePersonalizationResponse)
        
        try:
            response_tuple = self._retry_on_error(_perform_personalization)
            response, personalization = self._validate_and_parse_response(
                response_tuple, MessagePersonalizationResponse
            )
            
            logger.info(f"Message personalized successfully for {request.lead_name}: {len(personalization.variants)} variants")
            return personalization
            
        except Exception as e:
            logger.error(f"Message personalization failed for {request.lead_name}: {str(e)}")
            raise


# Service instances - can be imported and used directly
lead_qualification_service = LeadQualificationService()
message_personalization_service = MessagePersonalizationService()


def get_lead_qualification_service() -> LeadQualificationService:
    """Get the lead qualification service instance."""
    return lead_qualification_service


def get_message_personalization_service() -> MessagePersonalizationService:
    """Get the message personalization service instance."""
    return message_personalization_service
