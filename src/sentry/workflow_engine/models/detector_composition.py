class MetricDetectorHandler:
    def __init__(self, detector):
        self.detector = detector

    def evaluate(self, data_packet):
        # Specific logic for metric detectors
        pass


class UptimeDetectorHandler:
    def __init__(self, detector):
        self.detector = detector

    def evaluate(self, data_packet):
        # Specific logic for uptime detectors
        pass


def get_detector_handler(detector):
    # We'd probably use a registry pattern here, but just to illustrate it I'll hard code
    handlers = {
        "metric": MetricDetectorHandler,
        "uptime": UptimeDetectorHandler,
    }
    handler_class = handlers.get(detector.type)

    if handler_class:
        return handler_class(detector)
    else:
        raise ValueError(f"Unknown detector type: {detector.type}")
