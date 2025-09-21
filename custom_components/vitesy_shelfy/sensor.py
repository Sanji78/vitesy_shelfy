from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    UnitOfPressure,
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)
from .const import DOMAIN
from datetime import datetime, timezone
import logging

_LOGGER = logging.getLogger(__name__)

def extend_shared(extra: dict) -> dict:
    return {**SHARED_SENSOR_TYPES, **extra}

SHARED_SENSOR_TYPES = {
    "id": {
        "name": "Mac Address",
        "unit": None,
        "device_class": None,
        "icon": "mdi:lan-connect",
    },
    "apikey": {
        "name": "API Key",
        "unit": None,
        "device_class": None,
        "icon": "mdi:key-variant",
    },
    "type": {
        "name": "Type",
        "unit": None,
        "device_class": None,
        "icon": "mdi:devices",
    },
    "model": {
        "name": "Model",
        "unit": None,
        "device_class": None,
        "icon": "mdi:chip",
    },
    "firmware_version": {
        "name": "Firmware Version",
        "unit": None,
        "device_class": None,
        "icon": "mdi:update",
    },
    "wifi_SSID": {
        "name": "WiFi SSID",
        "unit": None,
        "device_class": None,
        "icon": "mdi:wifi",
    },
    "connected": {
        "name": "Connected",
        "unit": None,
        "device_class": None,
        "icon": "mdi:connection",
    },
    "score": {
        "name": "Air Quality Score",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:air-filter",
    },
    "timestamp": {
        "name": "Last Update",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
    },
    "program": {
        "name": "Program",
        "unit": None,
        "device_class": None,
        "icon": "mdi:play-circle",
    },
    "programdescription": {
        "name": "Program Description",
        "unit": None,
        "device_class": None,
        "icon": "mdi:text-box-outline",
    },
    "programicon": {
        "name": "Program Icon",
        "unit": None,
        "device_class": None,
        "icon": "mdi:image-outline",
    },
}

SHELFY_SENSOR_TYPES = extend_shared({
    "battery": {
        "name": "Battery Level",
        "unit": PERCENTAGE,
        "device_class": "battery",
    },
    "charging": {
        "name": "Charging",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-charging",
    },    
    "TMP01-SY": {
        "name": "Fridge Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
    },
    "DOC-SY": {
        "name": "Door Opening Times",
        "unit": None,
        "device_class": None,
        "icon": "mdi:door-open",
    },
    "DOT-SY": {
        "name": "Door Opening Seconds",
        "unit": "s",
        "device_class": None,
        "icon": "mdi:timer",
    }, 
    "timestamp": {
        "name": "Last Update",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
    },      
    "programfan": {
        "name": "Program Fan",
        "unit": None,
        "device_class": None,
        "icon": "mdi:fan",
    },     
    "programpower": {
        "name": "Program Power",
        "unit": None,
        "device_class": None,
        "icon": "mdi:lightning-bolt",
    },    
    "filter": {
        "name": "Next Filter Cleaning Date",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "icon": "mdi:calendar-clock",
    },  
    "fridge": {
        "name": "Next Fridge Cleaning Date",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "icon": "mdi:calendar-clock",
    },   
    "filterdays": {
        "name": "Remaining Filter Cleaning Days",
        "unit": None,
        "device_class": None,
        "icon": "mdi:calendar-minus",
    },  
    "fridgedays": {
        "name": "Remaining Fridge Cleaning Days",
        "unit": None,
        "device_class": None,
        "icon": "mdi:calendar-minus",
    },
})

NATEDE_SENSOR_TYPES = extend_shared({
    "TD01TP-N2": {
        "name": "Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class":  SensorDeviceClass.TEMPERATURE,
    },
    "SN01HU-N2": {
        "name": "Humidity",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.HUMIDITY
    },
    "SN02VD-N2": {
        "name": "VOC",
        "unit": CONCENTRATION_PARTS_PER_MILLION,
        "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS
    },
    "SN02C2-N2": {
        "name": "CO2",
        "unit": CONCENTRATION_PARTS_PER_MILLION,
        "device_class": SensorDeviceClass.CO2
    },
    "SY01DS-N2": {
        "name": "PM2.5",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.PM25
    },
})

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.data:
        device_id = device["id"].replace(":", "")
        device_type = device.get("type", "Unknown").capitalize()
        sensor_types = NATEDE_SENSOR_TYPES if "NATEDE" in device_type.upper() else SHELFY_SENSOR_TYPES

        # Add flat sensors like battery, type, etc.
        for sensor_type in sensor_types:
            if sensor_type in device and sensor_type != "program": 
                entities.append(VitesySensor(coordinator, device_id, device_type, sensor_type, sensor_types))
            elif "battery" in device and sensor_type in device["battery"]:                
                entities.append(VitesySensor(coordinator, device_id, device_type, sensor_type, sensor_types))
            elif "program" in device and sensor_type in device and sensor_type == "program":
                entities.append(VitesySensor(coordinator, device_id, device_type, sensor_type, sensor_types))

                for extra_key in ["programdescription", "programicon", "programfan", "programpower"]:
                    if extra_key in sensor_types:
                        entities.append(VitesySensor(coordinator, device_id, device_type, extra_key, sensor_types))

        # Add from measurements
        if "measurements" in device and isinstance(device["measurements"], list) and device["measurements"]:
            latest_measurement = device["measurements"][0]
            for key in latest_measurement:
                if key in sensor_types and key!="id":
                    entities.append(VitesySensor(coordinator, device_id, device_type, key, sensor_types))

        # Add from measurements -> sensors_data[].id
        for measurement in device.get("measurements", []):
            for sensor in measurement.get("sensors_data", []):
                sensor_id = sensor.get("id")
                if sensor_id in sensor_types:
                    entities.append(VitesySensor(coordinator, device_id, device_type, sensor_id, sensor_types))

        #  Add from maintenance
        for maintenance_key in device.get("maintenance", {}):
            if maintenance_key in sensor_types:
                entities.append(VitesySensor(coordinator, device_id, device_type, maintenance_key, sensor_types))
                entities.append(VitesySensor(coordinator, device_id, device_type, maintenance_key+"days", sensor_types))

    async_add_entities(entities)


class VitesySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id, device_type, sensor_type, sensor_types):
        super().__init__(coordinator)
        self.device_id = device_id
        self.sensor_type = sensor_type
        self.device_type = device_type
        self._sensor_types = sensor_types
        self._attr_unique_id = f"vitesy_{device_type.lower()}_{device_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = self._sensor_types[sensor_type]["unit"]
        self._attr_device_class = self._sensor_types[sensor_type]["device_class"]
        self._attr_icon = self._sensor_types[sensor_type].get("icon")
        self._attr_translation_key = sensor_type.replace("_","-").lower()
        self._attr_has_entity_name = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "manufacturer": "Vitesy",
            "model": self.device_type,
            "name": f"Vitesy {self.device_type.title()}",
        }
        
    @property
    def native_value(self):
        device = next(d for d in self.coordinator.data if d["id"].replace(":", "") == self.device_id)
        
        def _get_program_data_field(device, field):
            program_ref = device.get("program", {}).get("ref")
            if program_ref:
                # Try multiple fallbacks for ambiguous refs like "boost-s0"
                fallback_ids = {
                    "boost-s0": ["boost-s0", "performance-s0"],
                    "eco-s0": ["eco-s0"],
                    "shelf-s0": ["shelf-s0"]
                }.get(program_ref, [program_ref])

                for p in device.get("programs", []):
                    if p.get("id") in fallback_ids:
                        return p.get(field)
            return None

        def _get_program_metadata_field(device, meta_field):
            program_ref = device.get("program", {}).get("ref")
            if program_ref:
                fallback_ids = {
                    "boost-s0": ["boost-s0", "performance-s0"],
                    "eco-s0": ["eco-s0"],
                    "shelf-s0": ["shelf-s0"]
                }.get(program_ref, [program_ref])

                for p in device.get("programs", []):
                    if p.get("id") in fallback_ids:
                        return p.get("metadata", {}).get(meta_field)
            return None
    
        # Case: Battery (from top-level or status_data)
        if self.sensor_type == "battery":
            return device.get("battery", {}).get("level")
        elif self.sensor_type == "charging":
            return device.get("battery", {}).get("charging")
        elif self.sensor_type == "program":
            if "data" in device.get("program", {}):
                return device["program"]["data"].get("name")
            else:
                return _get_program_data_field(device, "name")

        elif self.sensor_type == "programdescription":
            if "data" in device.get("program", {}):
                return device["program"]["data"].get("description")
            else:
                return _get_program_data_field(device, "description")

        elif self.sensor_type == "programicon":
            if "data" in device.get("program", {}):
                return device["program"]["data"].get("icon")
            else:
                return _get_program_data_field(device, "icon")

        elif self.sensor_type == "programfan":
            if "data" in device.get("program", {}):
                return device["program"]["data"].get("metadata", {}).get("fan")
            else:
                return _get_program_metadata_field(device, "fan")

        elif self.sensor_type == "programpower":
            if "data" in device.get("program", {}):
                return device["program"]["data"].get("metadata", {}).get("power")
            else:
                return _get_program_metadata_field(device, "power")

        # Case: Flat attributes
        if self.sensor_type in device:
            return device[self.sensor_type]

        # Case: From measurements
        measurements = device.get("measurements", [])
        if measurements and self.sensor_type in measurements[0]:
            if self.sensor_type == "score":
                return round(measurements[0][self.sensor_type] * 100)
            elif self.sensor_type == "timestamp":
                try:
                    return datetime.fromisoformat(measurements[0][self.sensor_type].replace("Z", "+00:00"))
                except (KeyError, ValueError):
                    return None                
            elif self.sensor_type != "id":
                return measurements[0][self.sensor_type]

        # Case: From measurements → sensors_data[]
        for measurement in device.get("measurements", []):
            for sensor in measurement.get("sensors_data", []):
                if sensor.get("id") == self.sensor_type:
                    return sensor["value"].get("avg")

        # Case: From maintenance
        if self.sensor_type in device.get("maintenance", {}):
            try:
                return datetime.fromisoformat(device["maintenance"][self.sensor_type].get("due_date").replace("Z", "+00:00"))
            except (KeyError, ValueError):
                return None                
        if self.sensor_type.replace("days", "") in device.get("maintenance", {}):
            try:
                return (
                    datetime.fromisoformat(
                        device["maintenance"][self.sensor_type.replace("days", "")].get("due_date").replace("Z", "+00:00")
                    ) - datetime.now(timezone.utc)
                ).days
            except (KeyError, ValueError):
                return None                

        return None
