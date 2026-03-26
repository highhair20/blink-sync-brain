"""
Core components for Blink Lens system.

This package contains the main business logic components for the
Blink camera system enhancement. Modules are imported directly rather
than re-exported here to avoid pulling in role-specific dependencies
(e.g. cv2, face_recognition) on the wrong Pi.
"""