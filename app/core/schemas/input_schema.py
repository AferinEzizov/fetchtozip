from typing import Optional
from pydantic import BaseModel

class Input(BaseModel):
    name: Optional[str] = None
    column: Optional[int] = None
    change_order: Optional[int] = None

class Advanced(BaseModel):
    file_type: Optional[str] = None
    tmp_dir: Optional[str] = None
    rate_limit: Optional[int] = None
    page_limit: Optional[int] = None
    db_url : Optional[str] = None
