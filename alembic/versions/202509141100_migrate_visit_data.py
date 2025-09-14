"""
Data migration for visit model consolidation

Revision ID: migrate_visit_data
Create Date: 2025-09-14 11:00:00
"""

import sqlalchemy as sa
from alembic import op
import json
from datetime import datetime


def upgrade():
    # Get connection
    conn = op.get_bind()
    
    # 1. Migrate document visits
    conn.execute("""
        INSERT INTO document_visits (
            session_id, device_fingerprint, ip_address, user_agent,
            browser_name, browser_version, os_name, os_version,
            device_type, screen_resolution, referrer, referrer_domain,
            utm_source, utm_medium, utm_campaign, utm_term, utm_content,
            country, region, city, timezone, duration, bounce, bounce_type,
            time_on_page_seconds, active_time_seconds, scroll_depth,
            clicks_count, session_quality_score, engagement_depth,
            ab_test_group, ab_test_variant, ab_test_performance,
            created_at, last_interaction_at, metadata,
            document_id, visit_type, download_completed, time_reading,
            scroll_coverage, interactions
        )
        SELECT 
            v.session_id, v.visitor_id, v.visitor_ip, v.visitor_user_agent,
            v.browser, NULL, v.os, NULL,
            v.device_type, v.screen_resolution, v.referrer, NULL,
            v.utm_source, v.utm_medium, v.utm_campaign, NULL, NULL,
            v.visitor_country, NULL, v.visitor_city, NULL,
            v.duration, v.bounce, NULL,
            0, 0, 0, 0, 0, 0,
            NULL, NULL, NULL,
            v.created_at, v.visited_at, v.visit_metadata,
            v.document_id, v.visit_type, FALSE, 
            v.duration, 0, NULL
        FROM visits v
    """)
    
    # 2. Migrate landing page visits to new table
    conn.execute("""
        INSERT INTO landing_visits (
            session_id, device_fingerprint, ip_address, user_agent,
            browser_name, browser_version, os_name, os_version,
            device_type, screen_resolution, referrer, referrer_domain,
            utm_source, utm_medium, utm_campaign, utm_term, utm_content,
            country, region, city, timezone, duration, bounce, bounce_type,
            time_on_page_seconds, active_time_seconds, scroll_depth,
            clicks_count, session_quality_score, engagement_depth,
            ab_test_group, ab_test_variant, ab_test_performance,
            created_at, last_interaction_at, metadata,
            entry_page, exit_page, pages_viewed, viewed_templates,
            searched_terms, template_interactions, templates_viewed_count,
            searches_performed, form_interactions, form_completion,
            form_abandonment, last_interaction_field, funnel_stage,
            created_document, registered, downloaded_document,
            converted_to_paid, conversion_probability
        )
        SELECT 
            lpv.session_id, lpv.device_fingerprint, lpv.ip_address, lpv.user_agent,
            lpv.browser_name, lpv.browser_version, lpv.os_name, lpv.os_version,
            lpv.device_type, lpv.screen_resolution, lpv.referrer, lpv.referrer_domain,
            lpv.utm_source, lpv.utm_medium, lpv.utm_campaign, lpv.utm_term, lpv.utm_content,
            lpv.country, lpv.region, lpv.city, lpv.timezone,
            lpv.time_on_page_seconds, lpv.bounce, lpv.bounce_type,
            lpv.time_on_page_seconds, lpv.active_time_seconds, lpv.scroll_depth,
            lpv.clicks_count, lpv.session_quality_score, lpv.engagement_depth,
            lpv.ab_test_group, lpv.ab_test_variant, lpv.ab_test_performance,
            lpv.created_at, lpv.last_interaction_at, NULL,
            lpv.entry_page, lpv.exit_page, lpv.pages_viewed, lpv.viewed_templates,
            lpv.searched_terms, lpv.template_interactions, lpv.templates_viewed_count,
            lpv.searches_performed, lpv.form_interactions, lpv.form_completion,
            lpv.form_abandonment, lpv.last_interaction_field, lpv.funnel_stage,
            lpv.created_document, lpv.registered, lpv.downloaded_document,
            lpv.converted_to_paid, lpv.conversion_probability
        FROM landing_page_visits lpv
    """)
    
    # 3. Migrate page visits to new table
    conn.execute("""
        INSERT INTO page_visits (
            session_id, device_fingerprint, ip_address, user_agent,
            browser_name, browser_version, os_name, os_version,
            device_type, screen_resolution, referrer, referrer_domain,
            utm_source, utm_medium, utm_campaign, utm_term, utm_content,
            country, region, city, timezone, duration, bounce, bounce_type,
            time_on_page_seconds, active_time_seconds, scroll_depth,
            clicks_count, session_quality_score, engagement_depth,
            ab_test_group, ab_test_variant, ab_test_performance,
            created_at, last_interaction_at, metadata,
            path, query_params, user_id, page_load_time,
            dom_interactive_time, first_paint_time,
            navigation_type, was_cached
        )
        SELECT 
            pv.session_id, NULL, pv.ip_address, pv.user_agent,
            pv.browser, NULL, NULL, NULL,
            pv.device_type, NULL, pv.referrer, NULL,
            NULL, NULL, NULL, NULL, NULL,
            pv.country, NULL, pv.city, NULL,
            pv.visit_duration, FALSE, NULL,
            pv.visit_duration, 0, 0, 0, 0, 0,
            NULL, NULL, NULL,
            pv.created_at, pv.created_at, NULL,
            pv.page_path, NULL, pv.user_id, NULL,
            NULL, NULL, NULL, FALSE
        FROM page_visits pv
    """)


def downgrade():
    conn = op.get_bind()
    
    # Clear migrated data
    conn.execute("DELETE FROM document_visits")
    conn.execute("DELETE FROM landing_visits")
    conn.execute("DELETE FROM page_visits")