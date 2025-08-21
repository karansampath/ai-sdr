import duckdb
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = "data/ai_sdr.db"

class DatabaseManager:
    """Manages DuckDB connection and operations."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.ensure_data_directory()
        self._init_database()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get a database connection."""
        return duckdb.connect(self.db_path)
    
    def _init_database(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            self._create_leads_table(conn)
            self._create_interactions_table(conn)
            self._create_scoring_criteria_table(conn)
            self._create_pipeline_stages_table(conn)
            self._create_lead_pipeline_history_table(conn)
            self._seed_sample_data(conn)
    
    def _create_leads_table(self, conn):
        """Create the leads table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                company VARCHAR,
                job_title VARCHAR,
                phone VARCHAR,
                lead_source VARCHAR,
                status VARCHAR DEFAULT 'new',
                score INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_interactions_table(self, conn):
        """Create the interactions table for tracking lead communications."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY,
                lead_id INTEGER NOT NULL,
                interaction_type VARCHAR NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)
    
    def _seed_sample_data(self, conn):
        """Add some sample leads for demo purposes."""
        # Check if data already exists
        result = conn.execute("SELECT COUNT(*) FROM leads").fetchone()
        if result[0] > 0:
            return
        
        sample_leads = [
            {
                'name': 'John Smith',
                'email': 'john.smith@techcorp.com',
                'company': 'TechCorp Inc.',
                'job_title': 'VP of Engineering',
                'phone': '+1-555-0123',
                'lead_source': 'LinkedIn',
                'status': 'qualified',
                'score': 85,
                'notes': 'High-value prospect, interested in AI solutions'
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.j@innovate.co',
                'company': 'Innovate Co.',
                'job_title': 'CTO',
                'phone': '+1-555-0456',
                'lead_source': 'Website',
                'status': 'new',
                'score': 70,
                'notes': 'Downloaded whitepaper on AI automation'
            },
            {
                'name': 'Mike Chen',
                'email': 'm.chen@startupxyz.com',
                'company': 'StartupXYZ',
                'job_title': 'Founder',
                'phone': '+1-555-0789',
                'lead_source': 'Conference',
                'status': 'contacted',
                'score': 90,
                'notes': 'Met at AI conference, very interested in demo'
            }
        ]
        
        for lead in sample_leads:
            conn.execute("""
                INSERT INTO leads (name, email, company, job_title, phone, lead_source, status, score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                lead['name'], lead['email'], lead['company'], lead['job_title'],
                lead['phone'], lead['lead_source'], lead['status'], lead['score'], lead['notes']
            ])
    
    def _create_scoring_criteria_table(self, conn):
        """Create table for custom scoring criteria."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scoring_criteria (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                weight INTEGER NOT NULL CHECK (weight > 0 AND weight <= 100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_pipeline_stages_table(self, conn):
        """Create table for pipeline stages."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_stages (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                description TEXT,
                stage_order INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT true,
                auto_progression_rules TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_lead_pipeline_history_table(self, conn):
        """Create table to track lead progression through pipeline."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lead_pipeline_history (
                id INTEGER PRIMARY KEY,
                lead_id INTEGER NOT NULL,
                stage_id INTEGER NOT NULL,
                previous_stage_id INTEGER,
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exited_at TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (stage_id) REFERENCES pipeline_stages(id),
                FOREIGN KEY (previous_stage_id) REFERENCES pipeline_stages(id)
            )
        """)
        
        # Seed default pipeline stages
        default_stages = [
            ("New", "Newly acquired lead", 1),
            ("Contacted", "Initial contact made", 2),
            ("Qualified", "Lead has been qualified", 3),
            ("Proposal", "Proposal sent", 4),
            ("Negotiation", "In negotiation phase", 5),
            ("Closed Won", "Successfully closed deal", 6),
            ("Closed Lost", "Deal was lost", 7)
        ]
        
        # Check if stages already exist
        result = conn.execute("SELECT COUNT(*) FROM pipeline_stages").fetchone()
        if result[0] == 0:
            for name, description, order in default_stages:
                conn.execute("""
                    INSERT INTO pipeline_stages (name, description, stage_order)
                    VALUES (?, ?, ?)
                """, [name, description, order])
        
        # Seed default scoring criteria
        default_criteria = [
            ("Company Size", "Relevance of company size to our target market", 25),
            ("Decision Authority", "Level of decision-making authority", 20),
            ("Budget Fit", "Likelihood of having appropriate budget", 20),
            ("Industry Fit", "Relevance of industry to our solutions", 15),
            ("Engagement Level", "Level of engagement and interest shown", 10),
            ("Timing", "Urgency and timing of their needs", 10)
        ]
        
        # Check if criteria already exist
        result = conn.execute("SELECT COUNT(*) FROM scoring_criteria").fetchone()
        if result[0] == 0:
            for name, description, weight in default_criteria:
                conn.execute("""
                    INSERT INTO scoring_criteria (name, description, weight)
                    VALUES (?, ?, ?)
                """, [name, description, weight])

# Global database manager instance - initialized lazily
db_manager = None

def get_db_manager():
    """Get the global database manager instance, initializing if needed."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
