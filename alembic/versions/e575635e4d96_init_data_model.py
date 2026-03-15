"""init_data_model

Revision ID: e575635e4d96
Revises: 
Create Date: 2026-03-13 21:31:15.262914
"""
from alembic import op
import sqlalchemy as sa


revision = 'e575635e4d96'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('cte_catalog',
    sa.Column('cte_id', sa.BigInteger(), nullable=False),
    sa.Column('cte_name', sa.Text(), nullable=False),
    sa.Column('category_name', sa.Text(), nullable=True),
    sa.Column('manufacturer_name', sa.Text(), nullable=True),
    sa.Column('characteristics_raw', sa.Text(), nullable=True),
    sa.Column('characteristics_json', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('cte_id')
    )
    op.create_index('ix_cte_catalog_category_name', 'cte_catalog', ['category_name'], unique=False)
    op.create_table('organizations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('inn', sa.String(length=12), nullable=False),
    sa.Column('region_name', sa.Text(), nullable=True),
    sa.Column('org_type', sa.String(length=16), nullable=False),
    sa.CheckConstraint("org_type IN ('buyer', 'supplier', 'both')", name='ck_organizations_org_type'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('inn')
    )
    op.create_table('contracts',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('contract_external_id', sa.BigInteger(), nullable=False),
    sa.Column('purchase_name', sa.Text(), nullable=False),
    sa.Column('procurement_method', sa.Text(), nullable=True),
    sa.Column('initial_price', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('final_price', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('discount_percent', sa.Numeric(precision=8, scale=5), nullable=True),
    sa.Column('vat_rate_text', sa.String(length=32), nullable=True),
    sa.Column('signed_at', sa.DateTime(), nullable=True),
    sa.Column('buyer_org_id', sa.BigInteger(), nullable=True),
    sa.Column('supplier_org_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['buyer_org_id'], ['organizations.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['supplier_org_id'], ['organizations.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('contract_external_id', name='uq_contracts_contract_external_id')
    )
    op.create_index('ix_contracts_buyer_org_id', 'contracts', ['buyer_org_id'], unique=False)
    op.create_index('ix_contracts_signed_at', 'contracts', ['signed_at'], unique=False)
    op.create_index('ix_contracts_supplier_org_id', 'contracts', ['supplier_org_id'], unique=False)
    op.create_table('contract_items',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('contract_id', sa.BigInteger(), nullable=False),
    sa.Column('cte_id', sa.BigInteger(), nullable=False),
    sa.Column('cte_position_name', sa.Text(), nullable=True),
    sa.Column('quantity', sa.Numeric(precision=18, scale=5), nullable=True),
    sa.Column('unit_name', sa.String(length=64), nullable=True),
    sa.Column('unit_price', sa.Numeric(precision=18, scale=5), nullable=True),
    sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contract_items_contract_id', 'contract_items', ['contract_id'], unique=False)
    op.create_index('ix_contract_items_cte_id', 'contract_items', ['cte_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_contract_items_cte_id', table_name='contract_items')
    op.drop_index('ix_contract_items_contract_id', table_name='contract_items')
    op.drop_table('contract_items')
    op.drop_index('ix_contracts_supplier_org_id', table_name='contracts')
    op.drop_index('ix_contracts_signed_at', table_name='contracts')
    op.drop_index('ix_contracts_buyer_org_id', table_name='contracts')
    op.drop_table('contracts')
    op.drop_table('organizations')
    op.drop_index('ix_cte_catalog_category_name', table_name='cte_catalog')
    op.drop_table('cte_catalog')
