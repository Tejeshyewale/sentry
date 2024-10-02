from sentry.snuba.models import SnubaQuery
from sentry.testutils.cases import TestCase
from sentry.workflow_engine.models import DataSource
from sentry.workflow_engine.processors import process_data_sources


class TestProcessDataSources(TestCase):
    def create_snuba_query(self, **kwargs):
        return SnubaQuery.objects.create(
            type=SnubaQuery.Type.ERROR.value,
            dataset="events",
            aggregate="count()",
            time_window=60,
            resolution=60,
            **kwargs,
        )

    def setUp(self):
        self.query = self.create_snuba_query()
        self.query_two = self.create_snuba_query()

        self.detector_one = self.create_detector(name="test_detector1")
        self.detector_two = self.create_detector(name="test_detector2")

        self.ds1 = self.create_data_source(query_id=self.query.id, type=DataSource.Type.SNUBA_QUERY)
        self.ds1.detectors.set([self.detector_one])

        self.ds2 = self.create_data_source(
            query_id=self.query_two.id, type=DataSource.Type.SNUBA_QUERY
        )
        self.ds2.detectors.set([self.detector_two])

        self.data_packets = [self.query, self.query_two]

    def test_single_data_packet(self):
        self.data_packets = [self.query]
        assert process_data_sources(self.data_packets, DataSource.Type.SNUBA_QUERY) == [
            (self.query, [self.detector_one])
        ]

    def test_multiple_data_packets(self):
        assert process_data_sources(self.data_packets, DataSource.Type.SNUBA_QUERY) == [
            (self.query, [self.detector_one]),
            (self.query_two, [self.detector_two]),
        ]

    def test_multiple_detectors(self):
        self.detector_three = self.create_detector(name="test_detector3")
        self.ds2.detectors.add(self.detector_three)

        assert process_data_sources(self.data_packets, DataSource.Type.SNUBA_QUERY) == [
            (self.query, [self.detector_one]),
            (self.query_two, [self.detector_two, self.detector_three]),
        ]

    def test_no_results(self):
        self.ds1.detectors.clear()
        self.ds2.detectors.clear()

        assert process_data_sources(self.data_packets, DataSource.Type.SNUBA_QUERY) == [
            (self.query, []),
            (self.query_two, []),
        ]

    def test_different_data_packet_type__no_results(self):
        assert process_data_sources(
            self.data_packets, DataSource.Type.SNUBA_QUERY_SUBSCRIPTION
        ) == [
            (self.query, []),
            (self.query_two, []),
        ]

    def test_different_data_packet_type__with_results(self):
        self.ds1.type = DataSource.Type.SNUBA_QUERY_SUBSCRIPTION
        self.ds1.save()

        self.ds2.type = DataSource.Type.SNUBA_QUERY_SUBSCRIPTION
        self.ds2.save()

        assert process_data_sources(
            self.data_packets, DataSource.Type.SNUBA_QUERY_SUBSCRIPTION
        ) == [
            (self.query, [self.detector_one]),
            (self.query_two, [self.detector_two]),
        ]
