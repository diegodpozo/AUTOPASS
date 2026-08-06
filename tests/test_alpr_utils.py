import pytest
from routes.parking.utils import normalize_plate, format_plate, normalize_dni

def test_normalize_plate():
    assert normalize_plate("aa-123-bb") == "AA123BB"
    assert normalize_plate(" abc 123 ") == "ABC123"
    assert normalize_plate("") == ""

def test_format_plate_mercosur_arg():
    # AB 123 CD -> MERCOSUR Argentina
    assert format_plate("AB123CD") == "AB 123 CD"

def test_format_plate_old_arg():
    # AAA 111 -> Antigua Argentina
    assert format_plate("AAA111") == "AAA 111"

def test_format_plate_mercosur_brasil():
    # ABC 1D23 -> MERCOSUR Brasil
    assert format_plate("ABC1D23") == "ABC 1D23"

def test_normalize_dni():
    assert normalize_dni("12345678") == "12.345.678"
    assert normalize_dni("7654321") == "7.654.321"
