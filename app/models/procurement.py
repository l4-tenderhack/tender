from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    __table_args__ = (
        CheckConstraint(
            "org_type IN ('buyer', 'supplier', 'both')",
            name="ck_organizations_org_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    region_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_type: Mapped[str] = mapped_column(String(16), nullable=False, default="both")

    buyer_contracts: Mapped[list["Contract"]] = relationship(
        back_populates="buyer_organization",
        foreign_keys="Contract.buyer_org_id",
    )
    supplier_contracts: Mapped[list["Contract"]] = relationship(
        back_populates="supplier_organization",
        foreign_keys="Contract.supplier_org_id",
    )


class Contract(Base):
    __tablename__ = "contracts"

    __table_args__ = (
        UniqueConstraint("contract_external_id", name="uq_contracts_contract_external_id"),
        Index("ix_contracts_signed_at", "signed_at"),
        Index("ix_contracts_buyer_org_id", "buyer_org_id"),
        Index("ix_contracts_supplier_org_id", "supplier_org_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_external_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purchase_name: Mapped[str] = mapped_column(Text, nullable=False)
    procurement_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    initial_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    final_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 5), nullable=True)
    vat_rate_text: Mapped[str | None] = mapped_column(String(32), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    buyer_org_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    supplier_org_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=True,
    )

    buyer_organization: Mapped[Organization | None] = relationship(
        back_populates="buyer_contracts",
        foreign_keys=[buyer_org_id],
    )
    supplier_organization: Mapped[Organization | None] = relationship(
        back_populates="supplier_contracts",
        foreign_keys=[supplier_org_id],
    )
    items: Mapped[list["ContractItem"]] = relationship(
        back_populates="contract",
        cascade="all, delete-orphan",
    )


class ContractItem(Base):
    __tablename__ = "contract_items"

    __table_args__ = (
        Index("ix_contract_items_contract_id", "contract_id"),
        Index("ix_contract_items_cte_id", "cte_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    cte_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cte_position_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)
    unit_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 5), nullable=True)

    contract: Mapped[Contract] = relationship(back_populates="items")


class CteCatalog(Base):
    __tablename__ = "cte_catalog"

    __table_args__ = (
        Index("ix_cte_catalog_category_name", "category_name"),
    )

    cte_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cte_name: Mapped[str] = mapped_column(Text, nullable=False)
    category_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    manufacturer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    characteristics_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    characteristics_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )


class CteCharacteristic(Base):
    __tablename__ = "cte_characteristics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cte_id: Mapped[str] = mapped_column(Text, nullable=False)
    char_name: Mapped[str] = mapped_column(Text, nullable=False)
    char_value: Mapped[str] = mapped_column(Text, nullable=False)


class RegionCoordinate(Base):
    __tablename__ = "regions_coordinates"

    region: Mapped[str | None] = mapped_column(Text, primary_key=True)
    latitude_dd: Mapped[float | None] = mapped_column(nullable=True)
    longitude_dd: Mapped[float | None] = mapped_column(nullable=True)


class CteMain(Base):
    __tablename__ = "cte_main"

    cte_id: Mapped[str] = mapped_column(Text, primary_key=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    manufacturer: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    price_normalized: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    region: Mapped[str | None] = mapped_column(Text, nullable=True)
    characteristics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
