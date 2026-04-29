"""add categories and admin role

Revision ID: 4f6a7b8c9d10
Revises: 3a2b1c4d5e6f
Create Date: 2026-04-29 11:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f6a7b8c9d10"
down_revision: Union[str, Sequence[str], None] = "3a2b1c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            server_default="USER",
            nullable=False,
            comment="권한: USER / ADMIN",
        ),
    )

    op.create_table(
        "categories",
        sa.Column(
            "category_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="카테고리 PK",
        ),
        sa.Column("name", sa.String(length=50), nullable=False, comment="카테고리 이름"),
        sa.Column(
            "slug",
            sa.String(length=60),
            nullable=False,
            comment="카테고리 고유 슬러그",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="카테고리 설명"),
        sa.Column(
            "sort_order",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
            comment="노출 순서",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
            comment="활성 여부",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="생성 시각",
        ),
        sa.Column(
            "created_by",
            sa.BigInteger(),
            nullable=True,
            comment="생성자 user_id (회원가입 시에는 null)",
        ),
        sa.Column(
            "created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="최종 수정 시각",
        ),
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"
        ),
        sa.Column(
            "updated_ip",
            sa.String(length=45),
            nullable=True,
            comment="최종 수정 요청 IP",
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
            comment="삭제 여부 (소프트 삭제)",
        ),
        sa.PrimaryKeyConstraint("category_id"),
    )
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)

    op.execute(
        """
        INSERT INTO categories (
            category_id, name, slug, description, sort_order, is_active
        )
        VALUES (
            1, '일반', 'general', '기본 Q&A 카테고리', 0, true
        )
        """
    )

    op.add_column(
        "posts",
        sa.Column(
            "category_id",
            sa.BigInteger(),
            nullable=True,
            comment="카테고리 PK",
        ),
    )
    op.execute("UPDATE posts SET category_id = 1 WHERE category_id IS NULL")
    op.alter_column("posts", "category_id", nullable=False)
    op.create_index(op.f("ix_posts_category_id"), "posts", ["category_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_posts_category_id_categories"),
        "posts",
        "categories",
        ["category_id"],
        ["category_id"],
        ondelete="RESTRICT",
    )

    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('categories', 'category_id'),
            COALESCE((SELECT MAX(category_id) FROM categories), 1)
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("fk_posts_category_id_categories"), "posts", type_="foreignkey")
    op.drop_index(op.f("ix_posts_category_id"), table_name="posts")
    op.drop_column("posts", "category_id")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_table("categories")
    op.drop_column("users", "role")
