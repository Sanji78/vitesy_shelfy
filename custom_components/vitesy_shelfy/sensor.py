from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, PERCENTAGE, UnitOfPressure
from .const import DOMAIN
from datetime import datetime, timezone
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
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
    "battery": {
        "name": "Battery Level",
        "unit": PERCENTAGE,
        "device_class": "battery",
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
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.data:
        device_id = device["id"].replace(":", "")
        device_type = device.get("type", "Unknown").capitalize()

        # Add flat sensors like battery, type, etc.
        for sensor_type in SENSOR_TYPES:
            if sensor_type in device and sensor_type != "program": 
                entities.append(VitesySensor(coordinator, device_id, device_type, sensor_type))
            elif "battery" in device and sensor_type in device["battery"]:                
                entities.append(VitesySensor(coordinator, device_id, device_type, sensor_type))
            elif "program" in device and sensor_type in device and sensor_type == "program":
                entities.append(VitesySensor(coordinator, device_id, device_type, sensor_type))
                entities.append(VitesySensor(coordinator, device_id, device_type, "programdescription"))
                entities.append(VitesySensor(coordinator, device_id, device_type, "programicon"))
                entities.append(VitesySensor(coordinator, device_id, device_type, "programfan"))
                entities.append(VitesySensor(coordinator, device_id, device_type, "programpower"))

        # Add from measurements
        if "measurements" in device and isinstance(device["measurements"], list) and device["measurements"]:
            latest_measurement = device["measurements"][0]
            for key in latest_measurement:
                if key in SENSOR_TYPES and key!="id":
                    entities.append(VitesySensor(coordinator, device_id, device_type, key))


        # Add from measurements -> sensors_data[].id
        for measurement in device.get("measurements", []):
            for sensor in measurement.get("sensors_data", []):
                sensor_id = sensor.get("id")
                if sensor_id in SENSOR_TYPES:
                    entities.append(VitesySensor(coordinator, device_id, device_type, sensor_id))

        #  Add from maintenance
        for maintenance_key in device.get("maintenance", {}):
            if maintenance_key in SENSOR_TYPES:
                entities.append(VitesySensor(coordinator, device_id, device_type, maintenance_key))
                entities.append(VitesySensor(coordinator, device_id, device_type, maintenance_key+"days"))

    async_add_entities(entities)


class VitesySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id, device_type, sensor_type):
        super().__init__(coordinator)
        self.device_id = device_id
        self.sensor_type = sensor_type
        self.device_type = device_type
        self._attr_unique_id = f"vitesy_{device_type.lower()}_{device_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        self._attr_icon = SENSOR_TYPES[sensor_type].get("icon")
        self._attr_translation_key = sensor_type
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
            if self.sensor_type=="score":
                return round(measurements[0][self.sensor_type]*100)
            elif self.sensor_type=="timestamp":
                try:
                    return datetime.fromisoformat(measurements[0][self.sensor_type].replace("Z", "+00:00"))
                except (KeyError, ValueError):
                    return None                
            elif self.sensor_type!="id":
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
        if self.sensor_type.replace("days","") in device.get("maintenance", {}):
            try:
                return (datetime.fromisoformat(device["maintenance"][self.sensor_type.replace("days","")].get("due_date").replace("Z", "+00:00"))-datetime.now(timezone.utc)).days
            except (KeyError, ValueError):
                return None                

        return None

