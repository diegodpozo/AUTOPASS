import sys
from sqlalchemy.orm import Session
from coldfusion import TrustedBrand  # dummy; we only list
# just verify method presence on the repos we plan to use
from repositories.access_log_repository import AccessRepository
from repositories.branch_repository import BranchRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.reservation_repository import ReservationRepository
from repositories.user_repository import UserRepository

checks = [
    ('Acc.last_entry', hasattr(AccessRepository, 'get_last_entry')),
    ('Acc.exit_after', hasattr(AccessRepository, 'get_exit_after')),
    ('Acc.get_en_predio_ids', hasattr(AccessRepository, 'get_en_predio_ids')),
    ('Acc.last_for_plate_sucursal', hasattr(AccessRepository, 'get_last_by_patente_and_sucursal')),
    ('Acc.get_exit_after_detected', hasattr(AccessRepository, 'get_exit_after_detected')),
    ('Branch.get_all', hasattr(BranchRepository, 'get_all')),
    ('Branch.get_by_name_like', hasattr(BranchRepository, 'get_by_name_like')),
    ('Branch.get_floor_by_id', hasattr(BranchRepository, 'get_floor_by_id')),
    ('Branch.get_by_name_with_floors', hasattr(BranchRepository, 'get_by_name_with_floors')),
    ('Branch.get_aforo_by_sucursal', hasattr(BranchRepository, 'get_aforo_by_sucursal')),
    ('Vehicle.get_by_patente', hasattr(VehicleRepository, 'get_by_patente')),
    ('Vehicle.get_by_normalized_patente', hasattr(VehicleRepository, 'get_by_normalized_patente')),
    ('Vehicle.get_by_normalized_patente_and_user', hasattr(VehicleRepository, 'get_by_user_and_normalized_patente')),
    ('Res.get_by_id', hasattr(ReservationRepository, 'get_by_id')),
    ('Res.get_active_in_range_by_normalized_patente', hasattr(ReservationRepository, 'get_active_in_range_by_normalized_patente')),
    ('User.get_by_id', hasattr(UserRepository, 'get_by_id')),
    ('User.get_active_by_id', hasattr(UserRepository, 'get_active_by_id')),
]
for name, ok in checks:
    print(f'{name}={ok}')
