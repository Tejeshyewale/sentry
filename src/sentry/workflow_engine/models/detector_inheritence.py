from sentry.workflow_engine.models import Detector


class MetricDetector(Detector):
    class Meta:
        proxy = True

    # Any MetricDetector-specific methods can go here
    def evaluate(self, data):
        pass


class UptimeDetector(Detector):
    class Meta:
        proxy = True

    # Any UptimeDetector-specific methods can go here
    def evaluate(self, data):
        pass


def get_detector_subclass(detector):
    # We end up needing a registry here anyway to map the detectors to type
    handlers = {
        "metric": MetricDetector,
        "uptime": UptimeDetector,
    }
    detector_subclass = handlers.get(detector.type)

    if detector_subclass:
        if "database method":
            # Sucks because we have to make another query
            return detector_subclass.objects.get(id=detector.id)
        elif "Copy data method":
            # This isn't great since we already need to add more fields
            return detector_subclass(id=detector.id, name=detector.name, ...)
        elif "hack class":
            # Hack the detector itself to load the appropriate type. I'm sure this will play havok with typing
            class Detector:
                def __init__(self):
                    for _class in Detector.__subclasses__():
                        if self.check_type == _class.__name__:
                            self.__class__ = _class
                            break

    else:
        raise ValueError(f"Unknown detector type: {detector.type}")
