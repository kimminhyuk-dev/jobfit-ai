"""seed demo admin teams and assignments

Revision ID: t2u3v4w5x6y7
Revises: s1t2u3v4w5x6
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "t2u3v4w5x6y7"
down_revision = "s1t2u3v4w5x6"
branch_labels = None
depends_on = None


TEAMS = [
    ("채용운영팀", "채용공고와 지원자 운영을 담당하는 데모 팀"),
    ("회원지원팀", "회원 지원과 관리자 업무를 담당하는 데모 팀"),
    ("플랫폼관리팀", "플랫폼 운영과 내부 결재를 담당하는 데모 팀"),
]


def upgrade() -> None:
    bind = op.get_bind()

    for name, description in TEAMS:
        bind.execute(
            sa.text(
                """
                INSERT INTO teams (name, description, is_active, is_deleted)
                SELECT CAST(:name AS VARCHAR), CAST(:description AS VARCHAR), true, false
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM teams
                    WHERE name = :name
                      AND is_deleted = false
                )
                """
            ),
            {"name": name, "description": description},
        )

    # B등급은 팀장, C등급은 팀원으로 3개 데모 팀에 고르게 배정한다.
    bind.execute(
        sa.text(
            """
            WITH ordered_teams AS (
                SELECT
                    team_id,
                    row_number() OVER (ORDER BY team_id) AS team_no,
                    count(*) OVER () AS team_count
                FROM teams
                WHERE name IN ('채용운영팀', '회원지원팀', '플랫폼관리팀')
                  AND is_deleted = false
            ),
            ordered_admins AS (
                SELECT
                    user_id,
                    admin_level,
                    row_number() OVER (PARTITION BY admin_level ORDER BY user_id) AS admin_no
                FROM users
                WHERE role = 'ADMIN'
                  AND admin_level IN ('B', 'C')
                  AND is_deleted = false
            )
            UPDATE users u
            SET
                team_id = ot.team_id,
                team_role = CASE WHEN oa.admin_level = 'B' THEN 'LEAD' ELSE 'MEMBER' END,
                updated_at = now()
            FROM ordered_admins oa
            JOIN ordered_teams ot
              ON ot.team_no = ((oa.admin_no - 1) % ot.team_count) + 1
            WHERE u.user_id = oa.user_id
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE users
            SET team_id = NULL,
                team_role = NULL,
                updated_at = now()
            WHERE role = 'ADMIN'
              AND admin_level IN ('B', 'C')
              AND team_id IN (
                  SELECT team_id
                  FROM teams
                  WHERE name IN ('채용운영팀', '회원지원팀', '플랫폼관리팀')
              )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM teams
            WHERE name IN ('채용운영팀', '회원지원팀', '플랫폼관리팀')
            """
        )
    )
