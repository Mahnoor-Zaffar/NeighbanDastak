from __future__ import annotations

import argparse
import base64
import hashlib
import os
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.db.models.user import User
from app.db.session import SessionLocal


@dataclass(frozen=True)
class DoctorSeed:
    full_name: str
    specialty: str


DOCTOR_SEEDS: tuple[DoctorSeed, ...] = (
    DoctorSeed(full_name="Dr. Ayesha Khan", specialty="Family Medicine"),
    DoctorSeed(full_name="Dr. Hamza Qureshi", specialty="Internal Medicine"),
    DoctorSeed(full_name="Dr. Sana Malik", specialty="Pediatrics"),
    DoctorSeed(full_name="Dr. Bilal Ahmed", specialty="Cardiology"),
    DoctorSeed(full_name="Dr. Hina Raza", specialty="Dermatology"),
    DoctorSeed(full_name="Dr. Usman Farooq", specialty="Orthopedics"),
    DoctorSeed(full_name="Dr. Nimra Saeed", specialty="Neurology"),
    DoctorSeed(full_name="Dr. Ali Hassan", specialty="General Surgery"),
    DoctorSeed(full_name="Dr. Fatima Tariq", specialty="Gynecology"),
    DoctorSeed(full_name="Dr. Zain Abbas", specialty="ENT"),
    DoctorSeed(full_name="Dr. Maryam Iqbal", specialty="Ophthalmology"),
    DoctorSeed(full_name="Dr. Omar Siddiqui", specialty="Psychiatry"),
    DoctorSeed(full_name="Dr. Rabia Javed", specialty="Endocrinology"),
    DoctorSeed(full_name="Dr. Danish Amin", specialty="Pulmonology"),
    DoctorSeed(full_name="Dr. Noor-ul-Huda", specialty="Nephrology"),
)


def hash_password(password: str, *, iterations: int = 240_000) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
    digest_b64 = base64.urlsafe_b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def upsert_user(
    session: Session,
    *,
    email: str,
    full_name: str,
    role: Role,
    password: str,
    specialty: str | None = None,
    license_number: str | None = None,
    reset_passwords: bool,
) -> tuple[bool, bool]:
    user = session.scalar(select(User).where(User.email == email))
    is_created = user is None
    password_changed = False

    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            password_hash=hash_password(password),
            is_active=True,
            specialty=specialty,
            license_number=license_number,
        )
        session.add(user)
        password_changed = True
    else:
        user.full_name = full_name
        user.role = role
        user.is_active = True
        user.specialty = specialty
        user.license_number = license_number
        if reset_passwords:
            user.password_hash = hash_password(password)
            password_changed = True

    return is_created, password_changed


def seed_users(*, admin_password: str, doctor_password: str, reset_passwords: bool) -> None:
    created = 0
    updated = 0
    passwords_rotated = 0
    active_doctors: list[User] = []

    with SessionLocal() as session:
        admin_created, admin_pw_changed = upsert_user(
            session,
            email="admin@nigehbaandastak.local",
            full_name="System Administrator",
            role=Role.ADMIN,
            password=admin_password,
            reset_passwords=reset_passwords,
        )
        if admin_created:
            created += 1
        else:
            updated += 1
        if admin_pw_changed:
            passwords_rotated += 1

        for index, doctor in enumerate(DOCTOR_SEEDS, start=1):
            doctor_created, doctor_pw_changed = upsert_user(
                session,
                email=f"doctor{index:02d}@nigehbaandastak.local",
                full_name=doctor.full_name,
                role=Role.DOCTOR,
                password=doctor_password,
                specialty=doctor.specialty,
                license_number=f"ND-DOC-{index:04d}",
                reset_passwords=reset_passwords,
            )
            if doctor_created:
                created += 1
            else:
                updated += 1
            if doctor_pw_changed:
                passwords_rotated += 1

        session.commit()
        active_doctors = list(
            session.scalars(
                select(User)
                .where(
                    User.role == Role.DOCTOR,
                    User.is_active.is_(True),
                )
                .order_by(User.full_name.asc(), User.email.asc())
            )
        )

    print("Seed complete.")
    print(f"Created users: {created}")
    print(f"Updated users: {updated}")
    print(f"Passwords set/rotated: {passwords_rotated}")
    print("Active doctor profiles:")
    for doctor in active_doctors:
        print(f"- {doctor.full_name} | {doctor.email} | profile_id={doctor.id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed admin and doctor users for local development.")
    parser.add_argument(
        "--admin-password",
        default="Admin123!ChangeMe",
        help="Password to set for the admin account.",
    )
    parser.add_argument(
        "--doctor-password",
        default="Doctor123!ChangeMe",
        help="Password to set for all seeded doctor accounts.",
    )
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="Rotate existing seeded user password hashes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_users(
        admin_password=args.admin_password,
        doctor_password=args.doctor_password,
        reset_passwords=args.reset_passwords,
    )


if __name__ == "__main__":
    main()
