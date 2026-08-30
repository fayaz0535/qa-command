from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Platform(BaseModel):
    """Top of the queryable tree. Metrics roll up Platform <- Module <- SubModule."""
    __tablename__ = "platforms"
    __table_args__ = (UniqueConstraint("name", name="uq_platform_name"),)

    name = Column(String(255), nullable=False)

    modules = relationship("Module", back_populates="platform", cascade="all, delete-orphan")


class Module(BaseModel):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("platform_id", "name", name="uq_module_platform_name"),)

    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    name = Column(String(255), nullable=False)

    platform = relationship("Platform", back_populates="modules")
    sub_modules = relationship("SubModule", back_populates="module", cascade="all, delete-orphan")


class SubModule(BaseModel):
    __tablename__ = "sub_modules"
    __table_args__ = (UniqueConstraint("module_id", "name", name="uq_submodule_module_name"),)

    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    name = Column(String(255), nullable=False)

    module = relationship("Module", back_populates="sub_modules")


async def get_or_create_hierarchy(session, platform: str, module: str | None, sub_module: str | None):
    """Upsert Platform / Module / SubModule rows for one CSV row's hierarchy strings."""
    from sqlalchemy import select

    platform = (platform or "Unclassified").strip()
    result = await session.execute(select(Platform).where(Platform.name == platform))
    platform_row = result.scalar_one_or_none()
    if not platform_row:
        platform_row = Platform(name=platform)
        session.add(platform_row)
        await session.flush()

    module_row = None
    if module:
        module = module.strip()
        result = await session.execute(
            select(Module).where(Module.platform_id == platform_row.id, Module.name == module)
        )
        module_row = result.scalar_one_or_none()
        if not module_row:
            module_row = Module(platform_id=platform_row.id, name=module)
            session.add(module_row)
            await session.flush()

    sub_module_row = None
    if module_row and sub_module:
        sub_module = sub_module.strip()
        result = await session.execute(
            select(SubModule).where(SubModule.module_id == module_row.id, SubModule.name == sub_module)
        )
        sub_module_row = result.scalar_one_or_none()
        if not sub_module_row:
            sub_module_row = SubModule(module_id=module_row.id, name=sub_module)
            session.add(sub_module_row)
            await session.flush()

    return platform_row, module_row, sub_module_row
