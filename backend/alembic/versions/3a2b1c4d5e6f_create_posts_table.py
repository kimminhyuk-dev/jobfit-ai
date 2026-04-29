"""create posts table

Revision ID: 3a2b1c4d5e6f
Revises: 8dad372a1f24
Create Date: 2026-04-29 10:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a2b1c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "8dad372a1f24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "posts",
        sa.Column(
            "post_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="게시글 PK",
        ),
        sa.Column(
            "author_id",
            sa.BigInteger(),
            nullable=False,
            comment="작성자 user_id",
        ),
        sa.Column("title", sa.String(length=100), nullable=False, comment="제목"),
        sa.Column("content", sa.Text(), nullable=False, comment="본문"),
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
            nullable=False,
            server_default=sa.false(),
            comment="삭제 여부 (소프트 삭제)",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id"),
    )
    op.create_index(op.f("ix_posts_author_id"), "posts", ["author_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_posts_author_id"), table_name="posts")
    op.drop_table("posts")
