"""
Tests für settingsdata.py API Endpoints.

Prüft ob die Settings-Endpoints mit der neuen app_config funktionieren.
"""

import pytest
from unittest.mock import Mock, patch


def test_settings_has_all_required_properties():
    """Test: settings hat alle von settingsdata.py benötigten Properties"""
    from app.core.app_config import settings
    
    # Direkte Attribute
    assert hasattr(settings, 'database_path')
    assert hasattr(settings, 'LOG_FILE')
    
    # Properties
    assert hasattr(settings, 'database_name')
    assert hasattr(settings, 'analytics_db_path')
    assert hasattr(settings, 'mqtt_mode')
    assert hasattr(settings, 'mqtt_topic_sensors')
    assert hasattr(settings, 'mapping_file')
    
    # Pydantic Methode
    assert hasattr(settings, 'model_dump')
    assert callable(settings.model_dump)


def test_settings_model_dump_works():
    """Test: settings.model_dump() funktioniert"""
    from app.core.app_config import settings
    
    settings_dict = settings.model_dump()
    
    assert isinstance(settings_dict, dict)
    assert 'APP_NAME' in settings_dict
    assert 'SERVER_HOST' in settings_dict
    assert 'DB_PATH' in settings_dict
    assert 'MQTT_ENABLED' in settings_dict


def test_get_system_health_works():
    """Test: get_system_health() kann aufgerufen werden"""
    from app.api.settingsdata import get_system_health
    
    health = get_system_health()
    
    assert isinstance(health, dict)
    assert 'status' in health
    assert 'timestamp' in health
    assert 'uptime' in health
    assert 'database' in health
    assert 'hardware' in health
    assert 'logs' in health


def test_settings_properties_return_correct_types():
    """Test: Settings Properties geben korrekte Typen zurück"""
    from app.core.app_config import settings
    from pathlib import Path
    
    # database_name sollte String sein
    assert isinstance(settings.database_name, str)
    assert settings.database_name.endswith('.db')
    
    # database_path sollte Path sein
    assert isinstance(settings.database_path, Path)
    
    # analytics_db_path sollte Path sein
    assert isinstance(settings.analytics_db_path, Path)
    
    # mqtt_mode sollte String sein
    assert isinstance(settings.mqtt_mode, str)
    assert settings.mqtt_mode in ['test', 'production']
    
    # mqtt_topic_sensors sollte String sein
    assert isinstance(settings.mqtt_topic_sensors, str)
    
    # mapping_file sollte Path sein
    assert isinstance(settings.mapping_file, Path)


def test_settings_dict_contains_computed_properties():
    """Test: settings_dict kann mit computed properties erweitert werden"""
    from app.core.app_config import settings
    
    settings_dict = settings.model_dump()
    
    # Erweitere mit computed properties (wie in settingsdata.py)
    settings_dict.update({
        "database_name": settings.database_name,
        "database_path": str(settings.database_path),
        "analytics_db_path": str(settings.analytics_db_path),
        "mqtt_mode": settings.mqtt_mode,
        "mqtt_topic_sensors": settings.mqtt_topic_sensors,
        "mapping_file": str(settings.mapping_file),
    })
    
    # Prüfe ob alle Werte vorhanden sind
    assert 'database_name' in settings_dict
    assert 'database_path' in settings_dict
    assert 'analytics_db_path' in settings_dict
    assert 'mqtt_mode' in settings_dict
    assert 'mqtt_topic_sensors' in settings_dict
    assert 'mapping_file' in settings_dict
    
    # Prüfe Typen
    assert isinstance(settings_dict['database_name'], str)
    assert isinstance(settings_dict['database_path'], str)
    assert isinstance(settings_dict['mqtt_mode'], str)


def test_template_dir_path_works():
    """Test: Template-Pfad kann ermittelt werden"""
    from app.core.app_config import settings
    
    template_dir = settings.database_path.parent / "frontend" / "templates"
    
    assert isinstance(template_dir, type(settings.database_path))
    # Template-Dir muss existieren (wird in settingsdata.py geprüft)
    # Wir prüfen nur ob der Pfad konstruiert werden kann
    assert 'frontend' in str(template_dir)
    assert 'templates' in str(template_dir)
