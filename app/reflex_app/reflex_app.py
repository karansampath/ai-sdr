import reflex as rx
import httpx
from typing import Optional, Any


# Configuration
API_BASE_URL = "http://localhost:8000"


class LeadState(rx.State):
    """State management for lead data and UI interactions."""
    
    # Form data for new leads
    new_lead_name: str = ""
    new_lead_email: str = ""
    new_lead_company: str = ""
    new_lead_job_title: str = ""
    new_lead_phone: str = ""
    new_lead_source: str = "website"
    new_lead_notes: str = ""
    
    # All leads data
    leads: list[dict[str, Any]] = []
    selected_lead: Optional[dict[str, Any]] = None
    
    # Tab state
    active_tab: str = "qualification"
    
    # Qualification results
    qualification_result: Optional[dict[str, Any]] = None
    qualification_loading: bool = False
    
    # Message generation
    generated_messages: Optional[dict[str, Any]] = None
    message_loading: bool = False
    message_tone: str = "professional"
    campaign_type: str = "cold_outreach"
    selected_message: str = ""
    
    # Search and history
    search_query: str = ""
    search_results: list[dict[str, Any]] = []
    interaction_results: list[dict[str, Any]] = []
    
    # Meeting coordination
    meeting_times: list[dict[str, Any]] = []
    meeting_loading: bool = False
    
    # UI state
    show_success_message: str = ""
    show_error_message: str = ""
    
    async def load_leads(self):
        """Load all leads from the API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/leads")
                if response.status_code == 200:
                    self.leads = []
                    self.show_success_message = "Leads loaded successfully"
                else:
                    self.show_error_message = f"Failed to load leads: {response.status_code}"
        except Exception as e:
            self.show_error_message = f"Error loading leads: {str(e)}"
    
    async def create_lead(self):
        """Create a new lead."""
        if not self.new_lead_name or not self.new_lead_email:
            self.show_error_message = "Name and email are required"
            return
            
        try:
            lead_data = {
                "name": self.new_lead_name,
                "email": self.new_lead_email,
                "company": self.new_lead_company,
                "job_title": self.new_lead_job_title,
                "phone": self.new_lead_phone,
                "lead_source": self.new_lead_source,
                "notes": self.new_lead_notes,
                "status": "new",
                "score": 0
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE_URL}/api/leads", json=lead_data)
                if response.status_code == 200:
                    new_lead = response.json()
                    self.leads.append(new_lead)
                    self.clear_form()
                    self.show_success_message = f"Lead {self.new_lead_name} created successfully"
                else:
                    self.show_error_message = f"Failed to create lead: {response.status_code}"
        except Exception as e:
            self.show_error_message = f"Error creating lead: {str(e)}"
    
    def clear_form(self):
        """Clear the new lead form."""
        self.new_lead_name = ""
        self.new_lead_email = ""
        self.new_lead_company = ""
        self.new_lead_job_title = ""
        self.new_lead_phone = ""
        self.new_lead_source = "website"
        self.new_lead_notes = ""
    
    def select_lead(self, lead: dict[str, Any]):
        """Select a lead for detailed operations."""
        self.selected_lead = lead
        self.qualification_result = None
        self.generated_messages = None
        self.meeting_times = []
    
    def set_tab(self, tab: str):
        """Set the active tab."""
        self.active_tab = tab
    
    async def qualify_lead(self):
        """Qualify the selected lead."""
        if not self.selected_lead:
            self.show_error_message = "Please select a lead first"
            return
            
        self.qualification_loading = True
        try:
            request_data = {
                "name": self.selected_lead["name"],
                "email": self.selected_lead["email"],
                "company": self.selected_lead.get("company", ""),
                "job_title": self.selected_lead.get("job_title", ""),
                "additional_context": self.selected_lead.get("notes", "")
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE_URL}/api/leads/qualify", json=request_data)
                if response.status_code == 200:
                    self.qualification_result = response.json()
                    self.show_success_message = "Lead qualification completed"
                else:
                    self.show_error_message = f"Qualification failed: {response.status_code}"
        except Exception as e:
            self.show_error_message = f"Error qualifying lead: {str(e)}"
        finally:
            self.qualification_loading = False
    
    async def generate_message(self):
        """Generate personalized messages for the selected lead."""
        if not self.selected_lead:
            self.show_error_message = "Please select a lead first"
            return
            
        self.message_loading = True
        try:
            request_data = {
                "lead_name": self.selected_lead["name"],
                "lead_email": self.selected_lead["email"],
                "company": self.selected_lead.get("company", ""),
                "job_title": self.selected_lead.get("job_title", ""),
                "lead_source": self.selected_lead.get("lead_source", ""),
                "campaign_type": self.campaign_type,
                "message_tone": self.message_tone
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE_URL}/api/messages/personalize", json=request_data)
                if response.status_code == 200:
                    self.generated_messages = response.json()
                    if self.generated_messages.get("variants"):
                        self.selected_message = self.generated_messages["variants"][0]["body"]
                    self.show_success_message = "Messages generated successfully"
                else:
                    self.show_error_message = f"Message generation failed: {response.status_code}"
        except Exception as e:
            self.show_error_message = f"Error generating message: {str(e)}"
        finally:
            self.message_loading = False
    
    async def search_leads(self):
        """Search leads and interactions."""
        if not self.search_query:
            return
            
        try:
            search_data = {
                "query": self.search_query,
                "limit": 20,
                "offset": 0
            }
            
            async with httpx.AsyncClient() as client:
                # Search leads
                leads_response = await client.post(f"{API_BASE_URL}/api/search/leads", json=search_data)
                if leads_response.status_code == 200:
                    leads_data = leads_response.json()
                    self.search_results = leads_data.get("data", {}).get("leads", [])
                
                # Search interactions
                interactions_response = await client.post(f"{API_BASE_URL}/api/search/interactions", json=search_data)
                if interactions_response.status_code == 200:
                    interactions_data = interactions_response.json()
                    self.interaction_results = interactions_data.get("data", {}).get("interactions", [])
                
                self.show_success_message = f"Found {len(self.search_results)} leads and {len(self.interaction_results)} interactions"
                
        except Exception as e:
            self.show_error_message = f"Search failed: {str(e)}"
    
    async def coordinate_meeting(self):
        """Coordinate meeting times for the selected lead."""
        if not self.selected_lead:
            self.show_error_message = "Please select a lead first"
            return
            
        self.meeting_loading = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE_URL}/api/leads/{self.selected_lead['id']}/coordinate-meeting")
                if response.status_code == 200:
                    meeting_data = response.json()
                    self.meeting_times = meeting_data.get("data", {}).get("suggested_times", [])
                    self.show_success_message = "Meeting times suggested successfully"
                else:
                    self.show_error_message = f"Meeting coordination failed: {response.status_code}"
        except Exception as e:
            self.show_error_message = f"Error coordinating meeting: {str(e)}"
        finally:
            self.meeting_loading = False
    
    def clear_messages(self):
        """Clear success and error messages."""
        self.show_success_message = ""
        self.show_error_message = ""
    
    @rx.var
    def qualification_score_color(self) -> str:
        """Get color scheme for qualification score badge."""
        if not self.qualification_result:
            return "gray"
        score = self.qualification_result.get("score", 0)
        if score >= 70:
            return "green"
        elif score >= 40:
            return "yellow"
        else:
            return "red"
    
    @rx.var
    def priority_level_display(self) -> str:
        """Get formatted priority level for display."""
        if not self.qualification_result:
            return "Medium"
        priority = self.qualification_result.get("priority_level", "medium")
        return str(priority).title() if priority else "Medium"
    
    @rx.var
    def qualification_key_factors(self) -> list[str]:
        """Get key factors list for foreach rendering."""
        if not self.qualification_result:
            return []
        return self.qualification_result.get("key_factors", [])
    
    @rx.var
    def qualification_recommended_actions(self) -> list[str]:
        """Get recommended actions list for foreach rendering."""
        if not self.qualification_result:
            return []
        return self.qualification_result.get("recommended_actions", [])
    
    @rx.var
    def generated_message_variants(self) -> list[dict[str, Any]]:
        """Get message variants list for foreach rendering."""
        if not self.generated_messages:
            return []
        return self.generated_messages.get("variants", [])
    
    @rx.var
    def generated_personalization_factors(self) -> list[str]:
        """Get personalization factors list for foreach rendering."""
        if not self.generated_messages:
            return []
        return self.generated_messages.get("personalization_factors", [])


def sidebar() -> rx.Component:
    """Sidebar component with new lead form."""
    return rx.box(
        rx.heading("Add New Lead", size="6", mb="4"),
        
        # Form inputs
        rx.vstack(
            rx.input(
                placeholder="Full Name *",
                value=LeadState.new_lead_name,
                on_change=LeadState.set_new_lead_name,
                width="100%"
            ),
            rx.input(
                placeholder="Email Address *",
                value=LeadState.new_lead_email,
                on_change=LeadState.set_new_lead_email,
                width="100%",
                type="email"
            ),
            rx.input(
                placeholder="Company",
                value=LeadState.new_lead_company,
                on_change=LeadState.set_new_lead_company,
                width="100%"
            ),
            rx.input(
                placeholder="Job Title",
                value=LeadState.new_lead_job_title,
                on_change=LeadState.set_new_lead_job_title,
                width="100%"
            ),
            rx.input(
                placeholder="Phone",
                value=LeadState.new_lead_phone,
                on_change=LeadState.set_new_lead_phone,
                width="100%"
            ),
            rx.select(
                ["website", "linkedin", "conference", "referral", "email", "cold_outreach", "other"],
                placeholder="Lead Source",
                value=LeadState.new_lead_source,
                on_change=LeadState.set_new_lead_source,
                width="100%"
            ),
            rx.text_area(
                placeholder="Notes",
                value=LeadState.new_lead_notes,
                on_change=LeadState.set_new_lead_notes,
                width="100%",
                height="100px"
            ),
            rx.button(
                "Create Lead",
                on_click=LeadState.create_lead,
                color_scheme="blue",
                width="100%",
                size="3"
            ),
            spacing="3",
            width="100%"
        ),
        
        # Lead list
        rx.divider(mt="6", mb="4"),
        rx.heading("Recent Leads", size="5", mb="3"),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    LeadState.leads,
                    lambda lead: rx.card(
                        rx.vstack(
                            rx.text(lead["name"], weight="bold"),
                            rx.text(lead.get("company", "No company"), size="2", color="gray"),
                            rx.text(f"Score: {lead.get('score', 0)}/100", size="2"),
                            spacing="1"
                        ),
                        on_click=lambda: LeadState.select_lead(lead),
                        cursor="pointer",
                        _hover={"background": "gray.50"},
                        width="100%"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            height="300px"
        ),
        
        width="300px",
        height="100vh",
        p="4",
        bg="gray.50",
        overflow_y="auto"
    )


def qualification_tab() -> rx.Component:
    """Tab 1: Lead Qualification."""
    return rx.box(
        rx.cond(
            LeadState.selected_lead,
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading(f"Qualifying: {LeadState.selected_lead['name']}", size="5"),
                        rx.text(f"Company: {LeadState.selected_lead.get('company', 'N/A')}"),
                        rx.text(f"Role: {LeadState.selected_lead.get('job_title', 'N/A')}"),
                        rx.text(f"Current Score: {LeadState.selected_lead.get('score', 0)}/100"),
                        spacing="2"
                    ),
                    width="100%",
                    mb="4"
                ),
                
                rx.button(
                    rx.cond(
                        LeadState.qualification_loading,
                        rx.spinner(size="1"),
                        "Qualify Lead"
                    ),
                    on_click=LeadState.qualify_lead,
                    color_scheme="green",
                    size="3",
                    disabled=LeadState.qualification_loading
                ),
                
                rx.cond(
                    LeadState.qualification_result,
                    rx.card(
                        rx.vstack(
                            rx.heading("Qualification Results", size="4"),
                            rx.hstack(
                                rx.badge(f"Score: {LeadState.qualification_result['score']}/100", 
                                        color_scheme=LeadState.qualification_score_color),
                                rx.badge(LeadState.priority_level_display, 
                                        color_scheme="blue")
                            ),
                            rx.text("Reasoning:", weight="bold"),
                            rx.text(LeadState.qualification_result.get("reasoning", "")),
                            
                            rx.text("Key Factors:", weight="bold", mt="3"),
                            rx.unordered_list(
                                rx.foreach(
                                    LeadState.qualification_key_factors,
                                    lambda factor: rx.list_item(factor)
                                )
                            ),
                            
                            rx.text("Recommended Actions:", weight="bold", mt="3"),
                            rx.unordered_list(
                                rx.foreach(
                                    LeadState.qualification_recommended_actions,
                                    lambda action: rx.list_item(action)
                                )
                            ),
                            spacing="2"
                        ),
                        width="100%",
                        mt="4"
                    ),
                    rx.box()
                ),
                
                spacing="4",
                width="100%"
            ),
            rx.text("Please select a lead from the sidebar to qualify.", color="gray")
        ),
        p="4"
    )


def outreach_tab() -> rx.Component:
    """Tab 2: Personalized Outreach."""
    return rx.box(
        rx.cond(
            LeadState.selected_lead,
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading(f"Generate Message for: {LeadState.selected_lead['name']}", size="5"),
                        rx.hstack(
                            rx.select(
                                ["cold_outreach", "follow_up", "demo_request", "meeting_request"],
                                placeholder="Campaign Type",
                                value=LeadState.campaign_type,
                                on_change=LeadState.set_campaign_type
                            ),
                            rx.select(
                                ["professional", "casual", "friendly", "formal"],
                                placeholder="Message Tone",
                                value=LeadState.message_tone,
                                on_change=LeadState.set_message_tone
                            ),
                            spacing="3"
                        ),
                        spacing="3"
                    ),
                    width="100%",
                    mb="4"
                ),
                
                rx.button(
                    rx.cond(
                        LeadState.message_loading,
                        rx.spinner(size="1"),
                        "Generate Message"
                    ),
                    on_click=LeadState.generate_message,
                    color_scheme="blue",
                    size="3",
                    disabled=LeadState.message_loading
                ),
                
                rx.cond(
                    LeadState.generated_messages,
                    rx.vstack(
                        rx.heading("Generated Messages", size="4", mt="4"),
                        
                        rx.foreach(
                            LeadState.generated_message_variants,
                            lambda variant, idx: rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.badge(f"Variant {idx + 1}", color_scheme="blue"),
                                        rx.badge(f"Effectiveness: {variant.get('estimated_effectiveness', 0)}/100", 
                                                color_scheme="green"),
                                        justify="between",
                                        width="100%"
                                    ),
                                    rx.text("Subject:", weight="bold"),
                                    rx.text(variant.get("subject", "")),
                                    rx.text("Message:", weight="bold", mt="2"),
                                    rx.text_area(
                                        value=variant.get("body", ""),
                                        height="150px",
                                        width="100%",
                                        on_change=LeadState.set_selected_message
                                    ),
                                    spacing="2"
                                ),
                                width="100%",
                                mb="3"
                            )
                        ),
                        
                        rx.card(
                            rx.vstack(
                                rx.text("Personalization Factors:", weight="bold"),
                                rx.unordered_list(
                                    rx.foreach(
                                        LeadState.generated_personalization_factors,
                                        lambda factor: rx.list_item(factor)
                                    )
                                ),
                                rx.text(f"Best Send Time: {LeadState.generated_messages.get('best_send_time', 'N/A')}"),
                                rx.text(f"Follow-up Strategy: {LeadState.generated_messages.get('follow_up_strategy', 'N/A')}"),
                                spacing="2"
                            ),
                            width="100%",
                            mt="4"
                        ),
                        
                        spacing="3",
                        width="100%"
                    ),
                    rx.box()
                ),
                
                spacing="4",
                width="100%"
            ),
            rx.text("Please select a lead from the sidebar to generate messages.", color="gray")
        ),
        p="4"
    )


def history_tab() -> rx.Component:
    """Tab 3: History and Search."""
    return rx.box(
        rx.vstack(
            rx.card(
                rx.hstack(
                    rx.input(
                        placeholder="Search leads and conversations...",
                        value=LeadState.search_query,
                        on_change=LeadState.set_search_query,
                        width="300px"
                    ),
                    rx.button(
                        "Search",
                        on_click=LeadState.search_leads,
                        color_scheme="blue"
                    ),
                    spacing="3"
                ),
                width="100%",
                mb="4"
            ),
            
            rx.cond(
                LeadState.search_results,
                rx.card(
                    rx.vstack(
                        rx.heading(f"Lead Results ({LeadState.search_results.length()})", size="4"),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Name"),
                                    rx.table.column_header_cell("Company"),
                                    rx.table.column_header_cell("Score"),
                                    rx.table.column_header_cell("Status"),
                                    rx.table.column_header_cell("Actions")
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    LeadState.search_results,
                                    lambda lead: rx.table.row(
                                        rx.table.cell(lead["name"]),
                                        rx.table.cell(lead.get("company", "N/A")),
                                        rx.table.cell(f"{lead.get('score', 0)}/100"),
                                        rx.table.cell(
                                            rx.badge(str(lead.get("status", "new")).title(), color_scheme="blue")
                                        ),
                                        rx.table.cell(
                                            rx.button(
                                                "Select",
                                                on_click=lambda: LeadState.select_lead(lead),
                                                size="1"
                                            )
                                        )
                                    )
                                )
                            ),
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    width="100%",
                    mb="4"
                ),
                rx.box()
            ),
            
            rx.cond(
                LeadState.interaction_results,
                rx.card(
                    rx.vstack(
                        rx.heading(f"Interaction Results ({LeadState.interaction_results.length()})", size="4"),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Lead"),
                                    rx.table.column_header_cell("Type"),
                                    rx.table.column_header_cell("Content"),
                                    rx.table.column_header_cell("Date")
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    LeadState.interaction_results,
                                    lambda interaction: rx.table.row(
                                        rx.table.cell(interaction.get("lead_name", "N/A")),
                                        rx.table.cell(
                                            rx.badge(str(interaction.get("interaction_type", "")).title(), 
                                                   color_scheme="green")
                                        ),
                                        rx.table.cell(
                                            rx.text(
                                                interaction.get("content", ""),
                                                max_width="300px",
                                                overflow="hidden",
                                                text_overflow="ellipsis",
                                                white_space="nowrap"
                                            )
                                        ),
                                        rx.table.cell(interaction.get("created_at", ""))
                                    )
                                )
                            ),
                            width="100%"
                        ),
                        spacing="3"
                    ),
                    width="100%"
                ),
                rx.box()
            ),
            
            spacing="4",
            width="100%"
        ),
        p="4"
    )


def meeting_coordination() -> rx.Component:
    """Meeting coordination component."""
    return rx.cond(
        LeadState.selected_lead,
        rx.card(
            rx.vstack(
                rx.heading("Meeting Coordination", size="4"),
                rx.text(f"Schedule meeting with {LeadState.selected_lead['name']}"),
                
                rx.button(
                    rx.cond(
                        LeadState.meeting_loading,
                        rx.spinner(size="1"),
                        "Suggest Meeting Times"
                    ),
                    on_click=LeadState.coordinate_meeting,
                    color_scheme="purple",
                    disabled=LeadState.meeting_loading
                ),
                
                rx.cond(
                    LeadState.meeting_times,
                    rx.vstack(
                        rx.text("Suggested Times:", weight="bold", mt="3"),
                        rx.foreach(
                            LeadState.meeting_times,
                            lambda time: rx.card(
                                rx.vstack(
                                    rx.text(time.get("formatted", ""), weight="bold"),
                                    rx.text(f"Duration: {time.get('duration', 'N/A')}"),
                                    rx.text(f"Type: {str(time.get('meeting_type', 'N/A')).title()}"),
                                    rx.button("Book This Time", size="2", color_scheme="green"),
                                    spacing="2"
                                ),
                                width="100%"
                            )
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    rx.box()
                ),
                
                spacing="3",
                width="100%"
            )
        ),
        rx.box()
    )


def main_content() -> rx.Component:
    """Main content area with tabs."""
    return rx.box(
        # Tab navigation
        rx.hstack(
            rx.button(
                "Lead Qualification",
                color_scheme=rx.cond(LeadState.active_tab == "qualification", "blue", "gray"),
                variant=rx.cond(LeadState.active_tab == "qualification", "solid", "outline"),
                on_click=lambda: LeadState.set_tab("qualification")
            ),
            rx.button(
                "Personalized Outreach",
                color_scheme=rx.cond(LeadState.active_tab == "outreach", "blue", "gray"),
                variant=rx.cond(LeadState.active_tab == "outreach", "solid", "outline"),
                on_click=lambda: LeadState.set_tab("outreach")
            ),
            rx.button(
                "History",
                color_scheme=rx.cond(LeadState.active_tab == "history", "blue", "gray"),
                variant=rx.cond(LeadState.active_tab == "history", "solid", "outline"),
                on_click=lambda: LeadState.set_tab("history")
            ),
            spacing="2",
            mb="6",
            p="4"
        ),
        
        # Tab content
        rx.cond(
            LeadState.active_tab == "qualification",
            qualification_tab(),
            rx.cond(
                LeadState.active_tab == "outreach",
                outreach_tab(),
                history_tab()
            )
        ),
        
        # Meeting coordination (always visible when lead selected)
        meeting_coordination(),
        
        flex="1"
    )


def notifications() -> rx.Component:
    """Notification messages."""
    return rx.box(
        rx.cond(
            LeadState.show_success_message,
            rx.callout(
                LeadState.show_success_message,
                icon="check",
                color_scheme="green",
                mb="2"
            ),
            rx.box()
        ),
        rx.cond(
            LeadState.show_error_message,
            rx.callout(
                LeadState.show_error_message,
                icon="triangle_alert",
                color_scheme="red",
                mb="2"
            ),
            rx.box()
        ),
        position="fixed",
        top="20px",
        right="20px",
        z_index="1000",
        on_click=LeadState.clear_messages
    )


@rx.page(route="/", title="AI-SDR Dashboard")
def index():
    """Main application page."""
    return rx.box(
        notifications(),
        rx.hstack(
            sidebar(),
            main_content(),
            width="100vw",
            height="100vh",
            spacing="0"
        ),
        on_mount=LeadState.load_leads
    )


# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

# Add the index page
app.add_page(index)
