"""
Phone Tracking Controller Service Implementation
Implements IPhoneTrackingController interface using existing PhoneTrackingController
"""

from typing import Optional
from core.interfaces.controller_service import IPhoneTrackingController
from assistance.controllers.phone_tracking_controller import PhoneTrackingController


class PhoneTrackingControllerService(IPhoneTrackingController):
    """Phone tracking controller service implementation"""
    
    def __init__(self, config: dict):
        self.phone_tracking_controller = PhoneTrackingController(config)
    
    def start_tracking(self, mode) -> bool:
        """Start phone tracking"""
        return self.phone_tracking_controller.start_tracking(mode)
    
    def stop_tracking(self) -> bool:
        """Stop phone tracking"""
        return self.phone_tracking_controller.stop_tracking()
    
    def get_current_location(self) -> Optional[dict]:
        """Get current phone location"""
        return self.phone_tracking_controller.get_current_location()
    
    def get_tracking_status(self) -> str:
        """Get tracking status"""
        return self.phone_tracking_controller.get_tracking_status()
    
    def register_alert_callback(self, callback):
        """Register callback for alerts"""
        self.phone_tracking_controller.register_alert_callback(callback)
