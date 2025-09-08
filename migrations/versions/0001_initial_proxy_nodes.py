"""initial proxy nodes

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-07
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'proxy_nodes',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('protocol', sa.String(length=16), nullable=False, index=True),
        sa.Column('anonymity', sa.String(length=16), nullable=False, index=True),
        sa.Column('country', sa.String(length=2), nullable=True, index=True),
        sa.Column('region', sa.String(length=64), nullable=True),
        sa.Column('city', sa.String(length=64), nullable=True),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('isp', sa.String(length=255), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=64), nullable=True),
        sa.Column('source_url', sa.String(length=512), nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('score', sa.Float, nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
    )

    op.create_index('ix_proxy_nodes_host_port', 'proxy_nodes', ['host', 'port'], unique=True)
    op.create_index('ix_proxy_nodes_protocol', 'proxy_nodes', ['protocol'])
    op.create_index('ix_proxy_nodes_anonymity', 'proxy_nodes', ['anonymity'])
    op.create_index('ix_proxy_nodes_country', 'proxy_nodes', ['country'])
    op.create_index('ix_proxy_nodes_score', 'proxy_nodes', ['score'])
    op.create_index('ix_proxy_nodes_last_checked', 'proxy_nodes', ['last_checked'])


def downgrade() -> None:
    op.drop_index('ix_proxy_nodes_last_checked', table_name='proxy_nodes')
    op.drop_index('ix_proxy_nodes_score', table_name='proxy_nodes')
    op.drop_index('ix_proxy_nodes_country', table_name='proxy_nodes')
    op.drop_index('ix_proxy_nodes_anonymity', table_name='proxy_nodes')
    op.drop_index('ix_proxy_nodes_protocol', table_name='proxy_nodes')
    op.drop_index('ix_proxy_nodes_host_port', table_name='proxy_nodes')
    op.drop_table('proxy_nodes')


