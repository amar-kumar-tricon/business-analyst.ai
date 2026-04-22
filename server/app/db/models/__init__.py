"""
Import every model so `Base.metadata` knows about them at startup / migrations.
Add a new model → import it here.
"""
from app.db.base import Base  # noqa: F401
from app.db.models.project import Project  # noqa: F401
from app.db.models.document import Document  # noqa: F401
from app.db.models.stage_output import StageOutput  # noqa: F401
from app.db.models.discovery_qa import DiscoveryQA  # noqa: F401
from app.db.models.change_event import ChangeEvent  # noqa: F401
from app.db.models.version import ProjectVersion  # noqa: F401
from app.db.models.llm_config import LLMConfigRow  # noqa: F401
