import streamlit as st
import requests
from typing import Dict, List, Optional

# Configure the page
st.set_page_config(
    page_title="Grok SDR Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'selected_lead_id' not in st.session_state:
    st.session_state.selected_lead_id = None
if 'generated_message' not in st.session_state:
    st.session_state.generated_message = ""
if 'leads' not in st.session_state:
    st.session_state.leads = []

def create_lead(name: str, company: str, email: str, job_title: str = "", phone: str = "", lead_source: str = "website", notes: str = "") -> bool:
    """Create a new lead via API"""
    try:
        lead_data = {
            "name": name,
            "email": email,
            "company": company,
            "job_title": job_title,
            "phone": phone,
            "lead_source": lead_source,
            "status": "new",
            "score": 0,
            "notes": notes
        }
        
        response = requests.post(f"{API_BASE_URL}/api/leads", json=lead_data)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Failed to create lead: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error creating lead: {str(e)}")
        return False

def qualify_lead(name: str, email: str, company: str, job_title: str = "", additional_context: str = "") -> Optional[Dict]:
    """Qualify a lead using the AI service"""
    try:
        qualification_data = {
            "name": name,
            "email": email,
            "company": company,
            "job_title": job_title,
            "additional_context": additional_context
        }
        
        response = requests.post(f"{API_BASE_URL}/api/leads/qualify", json=qualification_data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to qualify lead: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error qualifying lead: {str(e)}")
        return None

def generate_message(lead_name: str, lead_email: str, company: str, job_title: str = "", campaign_type: str = "cold_outreach", message_tone: str = "professional") -> Optional[Dict]:
    """Generate personalized message using AI service"""
    try:
        message_data = {
            "lead_name": lead_name,
            "lead_email": lead_email,
            "company": company,
            "job_title": job_title,
            "campaign_type": campaign_type,
            "message_tone": message_tone
        }
        
        response = requests.post(f"{API_BASE_URL}/api/messages/personalize", json=message_data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to generate message: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error generating message: {str(e)}")
        return None

def search_leads_and_interactions(query: str) -> tuple[List[Dict], List[Dict]]:
    """Search leads and interactions"""
    leads, interactions = [], []
    
    try:
        search_data = {
            "query": query,
            "limit": 20,
            "offset": 0
        }
        
        # Search leads
        leads_response = requests.post(f"{API_BASE_URL}/api/search/leads", json=search_data)
        if leads_response.status_code == 200:
            leads_data = leads_response.json()
            leads = leads_data.get("data", {}).get("leads", [])
        
        # Search interactions
        interactions_response = requests.post(f"{API_BASE_URL}/api/search/interactions", json=search_data)
        if interactions_response.status_code == 200:
            interactions_data = interactions_response.json()
            interactions = interactions_data.get("data", {}).get("interactions", [])
            
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
    
    return leads, interactions

def coordinate_meeting(lead_id: int) -> Optional[Dict]:
    """Coordinate meeting times for a lead"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/leads/{lead_id}/coordinate-meeting")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to coordinate meeting: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error coordinating meeting: {str(e)}")
        return None

def load_leads() -> List[Dict]:
    """Load all leads from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/leads")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to load leads: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error loading leads: {str(e)}")
        return []

# Main app layout
st.title("🤖 Grok SDR Demo")
st.markdown("---")

# Sidebar for new lead input
with st.sidebar:
    st.header("📝 Add New Lead")
    
    # Input form for new lead
    with st.form("new_lead_form"):
        name = st.text_input("Full Name *", placeholder="Enter full name")
        email = st.text_input("Email Address *", placeholder="Enter email address")
        company = st.text_input("Company", placeholder="Enter company name")
        job_title = st.text_input("Job Title", placeholder="Enter job title")
        phone = st.text_input("Phone", placeholder="Enter phone number")
        
        lead_source = st.selectbox(
            "Lead Source",
            ["website", "linkedin", "conference", "referral", "email", "cold_outreach", "other"]
        )
        
        # Define scoring criteria
        st.markdown("**Define scoring criteria:** Budget, Need, Authority, Timeline")
        notes = st.text_area("Notes / Additional Context", placeholder="Enter any additional information about the lead")
        
        submitted = st.form_submit_button("Create Lead", type="primary")
        
        if submitted:
            if name and email:
                with st.spinner("Creating lead..."):
                    if create_lead(name, company, email, job_title, phone, lead_source, notes):
                        st.success(f"✅ Lead {name} created successfully!")
                        # Reload leads
                        st.session_state.leads = load_leads()
            else:
                st.error("Name and email are required!")
    
    # Display recent leads
    st.markdown("---")
    st.header("📋 Recent Leads")
    
    if st.button("🔄 Refresh Leads"):
        st.session_state.leads = load_leads()
    
    # Load leads on first run
    if not st.session_state.leads:
        st.session_state.leads = load_leads()
    
    # Display leads list
    for lead in st.session_state.leads[-10:]:  # Show last 10 leads
        with st.container():
            st.write(f"**{lead.get('name', 'Unknown')}**")
            st.write(f"🏢 {lead.get('company', 'No company')}")
            st.write(f"📊 Score: {lead.get('score', 0)}/100")
            if st.button("Select", key=f"select_{lead.get('id')}"):
                st.session_state.selected_lead_id = lead.get('id')
                st.rerun()
            st.markdown("---")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["🎯 Lead Qualification", "💬 Personalized Outreach", "📚 History"])

# Tab 1: Lead Qualification
with tab1:
    st.header("Lead Qualification")
    
    # Manual qualification form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("qualification_form"):
            qual_name = st.text_input("Lead Name", placeholder="Enter lead name")
            qual_email = st.text_input("Lead Email", placeholder="Enter lead email")
            qual_company = st.text_input("Company", placeholder="Enter company name")
            qual_job_title = st.text_input("Job Title", placeholder="Enter job title")
            qual_context = st.text_area("Additional Context", placeholder="Enter any additional context about the lead")
            
            qualify_submitted = st.form_submit_button("🎯 Qualify Lead", type="primary")
    
    with col2:
        st.info("💡 **Tip**: Fill in as much information as possible for better qualification results.")
    
    if qualify_submitted and qual_name and qual_email:
        with st.spinner("Qualifying lead..."):
            result = qualify_lead(qual_name, qual_email, qual_company, qual_job_title, qual_context)
            
            if result:
                st.success("✅ Lead qualification completed!")
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score = result.get('score', 0)
                    if score >= 70:
                        st.metric("📈 Qualification Score", f"{score}/100", delta="High Priority", delta_color="normal")
                    elif score >= 40:
                        st.metric("📊 Qualification Score", f"{score}/100", delta="Medium Priority", delta_color="normal")
                    else:
                        st.metric("📉 Qualification Score", f"{score}/100", delta="Low Priority", delta_color="inverse")
                
                with col2:
                    priority = result.get('priority_level', 'medium').title()
                    st.metric("🏆 Priority Level", priority)
                
                with col3:
                    st.metric("🤖 AI Confidence", "High")
                
                # Reasoning
                st.markdown("### 💭 AI Reasoning")
                st.write(result.get('reasoning', 'No reasoning provided'))
                
                # Key factors
                if result.get('key_factors'):
                    st.markdown("### 🔍 Key Factors")
                    for factor in result.get('key_factors', []):
                        st.write(f"• {factor}")
                
                # Recommended actions
                if result.get('recommended_actions'):
                    st.markdown("### ✅ Recommended Actions")
                    for action in result.get('recommended_actions', []):
                        st.write(f"• {action}")

# Tab 2: Personalized Outreach
with tab2:
    st.header("Personalized Outreach")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("message_form"):
            msg_name = st.text_input("Lead Name", placeholder="Enter lead name")
            msg_email = st.text_input("Lead Email", placeholder="Enter lead email") 
            msg_company = st.text_input("Company", placeholder="Enter company name")
            msg_job_title = st.text_input("Job Title", placeholder="Enter job title")
            
            col_a, col_b = st.columns(2)
            with col_a:
                campaign_type = st.selectbox("Campaign Type", ["cold_outreach", "follow_up", "demo_request", "meeting_request"])
            with col_b:
                message_tone = st.selectbox("Message Tone", ["professional", "casual", "friendly", "formal"])
            
            generate_submitted = st.form_submit_button("💬 Generate Message", type="primary")
    
    with col2:
        st.info("🎨 **Tip**: Choose the right tone and campaign type for better personalization.")
    
    if generate_submitted and msg_name and msg_email:
        with st.spinner("Generating personalized message..."):
            result = generate_message(msg_name, msg_email, msg_company, msg_job_title, campaign_type, message_tone)
            
            if result and result.get('variants'):
                st.success("✅ Messages generated successfully!")
                
                # Display message variants
                for i, variant in enumerate(result.get('variants', [])[:2]):  # Show first 2 variants
                    st.markdown(f"### 📧 Message Variant {i+1}")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text_input(f"Subject Line {i+1}", value=variant.get('subject', ''), key=f"subject_{i}")
                    with col2:
                        effectiveness = variant.get('estimated_effectiveness', 0)
                        st.metric("Effectiveness", f"{effectiveness}/100")
                    
                    # Editable message body
                    message_body = st.text_area(
                        f"Message Body {i+1}",
                        value=variant.get('body', ''),
                        height=150,
                        key=f"message_{i}"
                    )
                    
                    if st.button(f"📋 Copy Message {i+1}", key=f"copy_{i}"):
                        st.session_state.generated_message = message_body
                        st.success("Message copied!")
                
                # Display personalization factors
                if result.get('personalization_factors'):
                    st.markdown("### 🎯 Personalization Factors")
                    for factor in result.get('personalization_factors', []):
                        st.write(f"• {factor}")
                
                # Additional info
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📅 **Best Send Time**: {result.get('best_send_time', 'N/A')}")
                with col2:
                    st.info(f"🔄 **Follow-up Strategy**: {result.get('follow_up_strategy', 'N/A')}")

# Tab 3: History
with tab3:
    st.header("Search History")
    
    # Search functionality
    search_query = st.text_input("🔍 Search leads and conversations...", placeholder="Enter search term")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        search_clicked = st.button("🔍 Search", type="primary")
    
    if search_clicked and search_query:
        with st.spinner("Searching..."):
            leads, interactions = search_leads_and_interactions(search_query)
            
            # Display lead results
            if leads:
                st.markdown(f"### 👥 Lead Results ({len(leads)} found)")
                
                # Create a more compact table
                lead_data = []
                for lead in leads:
                    lead_data.append({
                        "Name": lead.get('name', 'N/A'),
                        "Company": lead.get('company', 'N/A'),
                        "Score": f"{lead.get('score', 0)}/100",
                        "Status": lead.get('status', 'new').title(),
                        "Email": lead.get('email', 'N/A')
                    })
                
                st.dataframe(lead_data, use_container_width=True)
            
            # Display interaction results
            if interactions:
                st.markdown(f"### 💬 Conversation Results ({len(interactions)} found)")
                
                interaction_data = []
                for interaction in interactions:
                    interaction_data.append({
                        "Lead": interaction.get('lead_name', 'N/A'),
                        "Type": interaction.get('interaction_type', '').title(),
                        "Content": interaction.get('content', '')[:100] + "..." if len(interaction.get('content', '')) > 100 else interaction.get('content', ''),
                        "Date": interaction.get('created_at', 'N/A')
                    })
                
                st.dataframe(interaction_data, use_container_width=True)
            
            if not leads and not interactions:
                st.info("No results found for your search query.")

# Meeting Coordination Section (always visible)
st.markdown("---")
st.header("📅 Meeting Coordination")

col1, col2 = st.columns([1, 2])

with col1:
    meeting_lead_id = st.number_input("Lead ID", min_value=1, value=1, help="Enter the ID of the lead to coordinate meeting with")
    
    if st.button("📅 Suggest Meeting Times", type="primary"):
        with st.spinner("Coordinating meeting times..."):
            meeting_result = coordinate_meeting(meeting_lead_id)
            
            if meeting_result and meeting_result.get('data'):
                st.success("✅ Meeting times suggested successfully!")
                
                data = meeting_result.get('data', {})
                st.write(f"**Lead**: {data.get('lead_name', 'Unknown')}")
                
                # Display suggested times
                suggested_times = data.get('suggested_times', [])
                if suggested_times:
                    st.markdown("### 🕐 Suggested Meeting Times")
                    
                    for i, time_slot in enumerate(suggested_times):
                        with st.container():
                            col_a, col_b, col_c = st.columns([2, 1, 1])
                            
                            with col_a:
                                st.write(f"**{time_slot.get('formatted', 'N/A')}**")
                                st.write(f"Duration: {time_slot.get('duration', 'N/A')}")
                            
                            with col_b:
                                meeting_type = time_slot.get('meeting_type', 'N/A').replace('_', ' ').title()
                                st.write(f"Type: {meeting_type}")
                            
                            with col_c:
                                if st.button(f"Book Time {i+1}", key=f"book_{i}"):
                                    st.success(f"Meeting {i+1} booked!")
                            
                            st.markdown("---")
                
                # Meeting link
                meeting_link = data.get('meeting_link', '')
                if meeting_link:
                    st.markdown(f"🔗 **Calendar Link**: {meeting_link}")

with col2:
    st.info("""
    💡 **Meeting Coordination Tips:**
    - Enter a valid Lead ID from your leads list
    - The system will suggest optimal meeting times based on the lead's profile
    - Higher scored leads get priority meeting slots
    - Different meeting types are suggested based on lead qualification
    """)

# Footer
st.markdown("---")
st.markdown("*Powered by Grok AI - Your intelligent sales development assistant* 🤖")
