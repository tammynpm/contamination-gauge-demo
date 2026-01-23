from datetime import datetime
from pydantic import BaseModel, PositiveInt

class User(BaseModel):
    id: int
    name: str = 'john'
    signup_ts: datetime | None
    tastes: dict[str, PositiveInt]

external_data= {
    'id': 123,
    'signup_ts': '2019',
    
}