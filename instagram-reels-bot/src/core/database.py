"""
Instagram Reels Bot - Database Module
SQLite database for managing accounts, proxies, videos, and uploads
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent.parent.parent / "data" / "instagram_bot.db"


def get_connection():
    """Get database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            email_password TEXT,
            
            -- Country/Region targeting
            country_code TEXT NOT NULL,  -- us, gb, de, etc.
            country_name TEXT,
            language TEXT,               -- en-US, en-GB, de-DE
            timezone TEXT,               -- America/New_York, Europe/London
            
            -- Proxy settings
            proxy_host TEXT,
            proxy_port INTEGER,
            proxy_user TEXT,
            proxy_pass TEXT,
            
            -- Browser fingerprint (JSON)
            fingerprint TEXT,
            
            -- Chrome profile path
            chrome_profile_path TEXT,
            
            -- Session data
            cookies TEXT,                -- JSON cookies after login
            session_id TEXT,
            
            -- Status
            status TEXT DEFAULT 'new',   -- new, warming, active, banned, paused
            last_login TIMESTAMP,
            last_action TIMESTAMP,
            login_attempts INTEGER DEFAULT 0,
            
            -- Statistics
            total_uploads INTEGER DEFAULT 0,
            successful_uploads INTEGER DEFAULT 0,
            failed_uploads INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            viral_videos INTEGER DEFAULT 0,   -- videos with 100k+ views
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Notes
            notes TEXT
        )
    """)
    
    # Proxies table (for managing proxy pool)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            username TEXT,
            password TEXT,
            proxy_type TEXT DEFAULT 'residential',  -- residential, mobile, datacenter
            country_code TEXT,
            
            -- Status
            is_active BOOLEAN DEFAULT 1,
            last_check TIMESTAMP,
            last_ip TEXT,
            
            -- Usage stats
            total_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            traffic_used_mb REAL DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(host, port, username)
        )
    """)
    
    # Videos table (master videos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            
            -- Video metadata
            duration_seconds REAL,
            file_size_mb REAL,
            resolution TEXT,
            
            -- Content info
            country_code TEXT,           -- Target country
            language TEXT,               -- Video language
            description_template TEXT,
            hashtags TEXT,               -- JSON array
            
            -- Uniquification
            is_master BOOLEAN DEFAULT 1,
            master_video_id INTEGER,     -- Reference to master if this is a clone
            clone_number INTEGER,        -- 1-10 for clones
            uniquification_params TEXT,  -- JSON with applied effects
            
            -- Status
            status TEXT DEFAULT 'pending',  -- pending, processing, ready, used
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (master_video_id) REFERENCES videos(id)
        )
    """)
    
    # Uploads table (upload history and queue)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            
            -- Upload details
            description TEXT,
            hashtags TEXT,
            
            -- Scheduling
            scheduled_time TIMESTAMP,
            
            -- Status
            status TEXT DEFAULT 'queued',  -- queued, uploading, success, failed, retry
            attempt_count INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            
            -- Result
            instagram_video_id TEXT,
            instagram_url TEXT,
            error_message TEXT,
            
            -- Stats (updated by monitoring)
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            last_stats_update TIMESTAMP,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_at TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)
    
    # Fingerprints table (pre-generated fingerprints per country)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            
            -- Browser info
            user_agent TEXT NOT NULL,
            platform TEXT,
            vendor TEXT,
            
            -- Screen
            screen_width INTEGER,
            screen_height INTEGER,
            color_depth INTEGER,
            pixel_ratio REAL,
            
            -- Timezone & Language
            timezone TEXT,
            timezone_offset INTEGER,
            languages TEXT,  -- JSON array
            
            -- Hardware
            hardware_concurrency INTEGER,
            device_memory INTEGER,
            
            -- WebGL
            webgl_vendor TEXT,
            webgl_renderer TEXT,
            
            -- Canvas hash (unique per fingerprint)
            canvas_noise_seed INTEGER,
            
            -- Audio context
            audio_context_hash TEXT,
            
            -- Fonts (JSON array)
            fonts TEXT,
            
            -- Full fingerprint JSON
            full_fingerprint TEXT,
            
            -- Usage
            is_used BOOLEAN DEFAULT 0,
            assigned_account_id INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (assigned_account_id) REFERENCES accounts(id)
        )
    """)
    
    # Account activity log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,  -- login, upload, like, comment, follow, etc.
            details TEXT,               -- JSON with action details
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    return True


# ============== Account Functions ==============

def add_account(
    username: str,
    password: str,
    email: str,
    email_password: str,
    country_code: str,
    proxy_config: Dict[str, Any],
    fingerprint: Optional[Dict] = None
) -> int:
    """Add new Instagram account"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Country configurations
    country_configs = {
        'us': {'name': 'United States', 'language': 'en-US', 'timezone': 'America/New_York'},
        'gb': {'name': 'United Kingdom', 'language': 'en-GB', 'timezone': 'Europe/London'},
        'de': {'name': 'Germany', 'language': 'de-DE', 'timezone': 'Europe/Berlin'},
    }
    
    config = country_configs.get(country_code, {})
    
    cursor.execute("""
        INSERT INTO accounts (
            username, password, email, email_password,
            country_code, country_name, language, timezone,
            proxy_host, proxy_port, proxy_user, proxy_pass,
            fingerprint, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
    """, (
        username, password, email, email_password,
        country_code,
        config.get('name', ''),
        config.get('language', 'en-US'),
        config.get('timezone', 'UTC'),
        proxy_config.get('host'),
        proxy_config.get('port'),
        proxy_config.get('user'),
        proxy_config.get('password'),
        json.dumps(fingerprint) if fingerprint else None
    ))
    
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return account_id


def get_account(account_id: int) -> Optional[Dict]:
    """Get account by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_accounts_by_country(country_code: str) -> List[Dict]:
    """Get all accounts for a specific country"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE country_code = ?", (country_code,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_accounts() -> List[Dict]:
    """Get all accounts"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts ORDER BY country_code, id")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def update_account_status(account_id: int, status: str, notes: str = None):
    """Update account status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if notes:
        cursor.execute("""
            UPDATE accounts 
            SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, notes, account_id))
    else:
        cursor.execute("""
            UPDATE accounts 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, account_id))
    
    conn.commit()
    conn.close()


def update_account_cookies(account_id: int, cookies: List[Dict]):
    """Save cookies after successful login"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE accounts 
        SET cookies = ?, last_login = CURRENT_TIMESTAMP, status = 'active', updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (json.dumps(cookies), account_id))
    conn.commit()
    conn.close()


# ============== Proxy Functions ==============

def add_proxy(host: str, port: int, username: str, password: str, country_code: str, proxy_type: str = 'residential'):
    """Add proxy to pool"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO proxies (host, port, username, password, country_code, proxy_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (host, port, username, password, country_code, proxy_type))
    
    conn.commit()
    conn.close()


# ============== Video Functions ==============

def add_video(filepath: str, country_code: str, is_master: bool = True, master_id: int = None, clone_number: int = None):
    """Add video to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    filename = Path(filepath).name
    
    cursor.execute("""
        INSERT INTO videos (filename, filepath, country_code, is_master, master_video_id, clone_number, status)
        VALUES (?, ?, ?, ?, ?, ?, 'ready')
    """, (filename, filepath, country_code, is_master, master_id, clone_number))
    
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return video_id


# ============== Upload Functions ==============

def queue_upload(account_id: int, video_id: int, description: str, hashtags: List[str], scheduled_time: datetime = None):
    """Queue video for upload"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO uploads (account_id, video_id, description, hashtags, scheduled_time, status)
        VALUES (?, ?, ?, ?, ?, 'queued')
    """, (account_id, video_id, description, json.dumps(hashtags), scheduled_time))
    
    upload_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return upload_id


def get_pending_uploads(limit: int = 10) -> List[Dict]:
    """Get pending uploads ready to process"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.*, a.username, a.proxy_host, a.proxy_port, a.cookies, v.filepath
        FROM uploads u
        JOIN accounts a ON u.account_id = a.id
        JOIN videos v ON u.video_id = v.id
        WHERE u.status = 'queued' 
        AND (u.scheduled_time IS NULL OR u.scheduled_time <= CURRENT_TIMESTAMP)
        AND a.status = 'active'
        ORDER BY u.scheduled_time ASC, u.created_at ASC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ============== Statistics ==============

def get_stats() -> Dict:
    """Get overall statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Account stats
    cursor.execute("SELECT COUNT(*) FROM accounts")
    stats['total_accounts'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
    stats['active_accounts'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'banned'")
    stats['banned_accounts'] = cursor.fetchone()[0]
    
    # Upload stats
    cursor.execute("SELECT COUNT(*) FROM uploads WHERE status = 'success'")
    stats['successful_uploads'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM uploads WHERE status = 'failed'")
    stats['failed_uploads'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM uploads WHERE status = 'queued'")
    stats['queued_uploads'] = cursor.fetchone()[0]
    
    # Video stats
    cursor.execute("SELECT COUNT(*) FROM videos WHERE is_master = 1")
    stats['master_videos'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE is_master = 0")
    stats['clone_videos'] = cursor.fetchone()[0]
    
    conn.close()
    
    return stats


if __name__ == "__main__":
    init_database()
    print("\n📊 Database tables created!")
    print(f"📁 Database location: {DB_PATH}")
