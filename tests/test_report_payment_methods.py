import pytest
from repositories.report_repository import _canonical_method


@pytest.mark.parametrize("stored", ["CAJA", "Caja", "Efectivo", "EFECTIVO"])
def test_metodos_de_efectivo_se_normalizan_como_caja(stored):
    assert _canonical_method(stored) == "CAJA"
