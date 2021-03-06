"""Initial

Revision ID: b3ec0dadec0b
Revises:
Create Date: 2022-01-17 23:18:08.594313

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = 'b3ec0dadec0b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    user_role = postgresql.ENUM(
        'super_admin', 'admin', 'user', name='user_role'
    )
    user_role.create(op.get_bind())

    op.create_table(
        'clothes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column(
            'color',
            sa.Enum('pink', 'black', 'white', 'yellow', name='colorenum'),
            nullable=False,
        ),
        sa.Column(
            'size',
            sa.Enum('xs', 's', 'm', 'll', 'xl', 'xxl', name='sizeenum'),
            nullable=False,
        ),
        sa.Column('photo_url', sa.String(length=255), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'last_modified_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=13), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'last_modified_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'role',
            sa.Enum('super_admin', 'admin', 'user', name='userrole'),
            server_default='user',
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('clothes')
    # ### end Alembic commands ###
