from unittest import mock
from db.models import Location

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from db.utils import get_loc_output_capacity
def test_get_loc_output_capacity():
    loc_id = 1
    loc_output_capacity = 1000

    session = UnifiedAlchemyMagicMock(data=[
    (
        [mock.call.query(Location.loc_output_capacity),
        mock.call.filter(Location.loc_id_auto == loc_id)],
        [[loc_output_capacity]]
    ) ])
    assert get_loc_output_capacity(session, loc_id) == loc_output_capacity



