"""
Test für MQTT Discovery in MQTTPublisher.

Prüft ob die Discovery-Methoden korrekt funktionieren.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json


def test_mqtt_publisher_has_discovery_methods():
    """Test: MQTTPublisher hat publish_discovery und unpublish_discovery Methoden"""
    from app.services.mqtt_publisher import MQTTPublisher
    
    # Mock SensorStore
    mock_store = Mock()
    publisher = MQTTPublisher(mock_store)
    
    assert hasattr(publisher, 'publish_discovery')
    assert hasattr(publisher, 'unpublish_discovery')
    assert callable(publisher.publish_discovery)
    assert callable(publisher.unpublish_discovery)


def test_settings_device_exists():
    """Test: settings.device ist korrekt initialisiert"""
    from app.core.app_config import settings
    
    assert hasattr(settings, 'device')
    assert settings.device is not None
    assert hasattr(settings.device, 'device_id')
    assert hasattr(settings.device, 'name')
    assert hasattr(settings.device, 'manufacturer')
    assert hasattr(settings.device, 'model')
    assert hasattr(settings.device, 'firmware')


def test_publish_discovery_structure():
    """Test: publish_discovery verwendet korrekte Struktur"""
    from app.services.mqtt_publisher import MQTTPublisher
    from app.core.app_config import settings
    
    # Mock SensorStore
    mock_store = Mock()
    mock_store.get_all.return_value = {}
    
    # Mock MQTT Client
    mock_client = MagicMock()
    
    publisher = MQTTPublisher(mock_store)
    publisher.client = mock_client
    publisher.connected = True
    
    # Discovery publizieren
    publisher.publish_discovery()
    
    # Prüfe ob publish aufgerufen wurde
    assert mock_client.publish.called
    
    # Prüfe ob mindestens Home-Entity publiziert wurde
    calls = mock_client.publish.call_args_list
    home_config_published = any(
        'homeassistant/sensor/smartmeter/home/config' in str(call)
        for call in calls
    )
    assert home_config_published, "Home Discovery Config wurde nicht publiziert"


def test_publish_discovery_uses_settings_device():
    """Test: publish_discovery verwendet settings.device Werte"""
    from app.services.mqtt_publisher import MQTTPublisher
    from app.core.app_config import settings
    
    mock_store = Mock()
    mock_client = MagicMock()
    
    publisher = MQTTPublisher(mock_store)
    publisher.client = mock_client
    publisher.connected = True
    
    # Discovery publizieren
    publisher.publish_discovery()
    
    # Finde Home Config Payload
    home_payload = None
    for call in mock_client.publish.call_args_list:
        args = call[0]
        if 'homeassistant/sensor/smartmeter/home/config' in args[0]:
            home_payload = json.loads(args[1])
            break
    
    assert home_payload is not None, "Home Config nicht gefunden"
    assert 'device' in home_payload
    
    device = home_payload['device']
    assert device['identifiers'] == [settings.device.device_id]
    assert device['name'] == settings.device.name
    assert device['manufacturer'] == settings.device.manufacturer
    assert device['model'] == settings.device.model
    assert device['sw_version'] == settings.device.firmware


def test_unpublish_discovery_clears_configs():
    """Test: unpublish_discovery löscht alle Discovery Configs"""
    from app.services.mqtt_publisher import MQTTPublisher
    import app.domain.house as house
    
    mock_store = Mock()
    mock_client = MagicMock()
    
    publisher = MQTTPublisher(mock_store)
    publisher.client = mock_client
    publisher.connected = True
    
    # Unpublish
    publisher.unpublish_discovery()
    
    # Prüfe ob publish mit leerem Payload aufgerufen wurde
    assert mock_client.publish.called
    
    # Prüfe ob Home Config gelöscht wurde
    calls = mock_client.publish.call_args_list
    home_deleted = any(
        'homeassistant/sensor/smartmeter/home/config' in str(call[0][0]) and
        call[0][1] == ""
        for call in calls
    )
    assert home_deleted, "Home Discovery Config wurde nicht gelöscht"


def test_discovery_not_called_when_disconnected():
    """Test: Discovery wird nicht publiziert wenn nicht verbunden"""
    from app.services.mqtt_publisher import MQTTPublisher
    
    mock_store = Mock()
    mock_client = MagicMock()
    
    publisher = MQTTPublisher(mock_store)
    publisher.client = mock_client
    publisher.connected = False  # Nicht verbunden!
    
    # Discovery versuchen
    publisher.publish_discovery()
    
    # Sollte nicht publiziert werden
    assert not mock_client.publish.called


def test_discovery_called_on_connect():
    """Test: Discovery wird automatisch bei on_connect aufgerufen"""
    from app.services.mqtt_publisher import MQTTPublisher
    
    mock_store = Mock()
    publisher = MQTTPublisher(mock_store)
    
    # Mock client
    mock_client = MagicMock()
    publisher.client = mock_client
    
    # Mock publish_discovery
    with patch.object(publisher, 'publish_discovery') as mock_discovery:
        # Simuliere on_connect
        publisher._on_connect(mock_client, None, None, 0)
        
        # Discovery sollte aufgerufen worden sein
        mock_discovery.assert_called_once()


def test_discovery_topics_hierarchy():
    """Test: Discovery erstellt hierarchische Topics"""
    from app.services.mqtt_publisher import MQTTPublisher
    import app.domain.house as house
    
    mock_store = Mock()
    mock_client = MagicMock()
    
    publisher = MQTTPublisher(mock_store)
    publisher.client = mock_client
    publisher.connected = True
    
    publisher.publish_discovery()
    
    # Sammle alle Topics
    topics = [call[0][0] for call in mock_client.publish.call_args_list]
    
    # Prüfe ob verschiedene Ebenen existieren
    has_home = any('home/config' in t for t in topics)
    has_area = any('area_' in t for t in topics)
    has_room = any('room_' in t for t in topics)
    has_sensor = any('/smartmeter/S' in t for t in topics)
    
    assert has_home, "Home Topic fehlt"
    assert has_area, "Area Topics fehlen"
    assert has_room, "Room Topics fehlen"
    assert has_sensor, "Sensor Topics fehlen"


def test_discovery_payload_structure():
    """Test: Discovery Payloads haben korrekte Struktur"""
    from app.services.mqtt_publisher import MQTTPublisher
    
    mock_store = Mock()
    mock_client = MagicMock()
    
    publisher = MQTTPublisher(mock_store)
    publisher.client = mock_client
    publisher.connected = True
    
    publisher.publish_discovery()
    
    # Prüfe ersten Sensor Config
    sensor_payload = None
    for call in mock_client.publish.call_args_list:
        args = call[0]
        if '/smartmeter/S' in args[0] and '/config' in args[0]:
            sensor_payload = json.loads(args[1])
            break
    
    if sensor_payload:  # Nur wenn Sensoren existieren
        # Pflichtfelder für HA Discovery
        assert 'name' in sensor_payload
        assert 'unique_id' in sensor_payload
        assert 'state_topic' in sensor_payload
        assert 'unit_of_measurement' in sensor_payload
        assert 'device_class' in sensor_payload
        assert 'state_class' in sensor_payload
        assert 'value_template' in sensor_payload
        assert 'device' in sensor_payload
        
        # Device muss identifiers haben
        assert 'identifiers' in sensor_payload['device']
