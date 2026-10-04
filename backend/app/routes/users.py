from fastapi import APIRouter
from typing import Annotated

from fastapi import Depends

from ..dependencies import get_current_user
from ..models import User
from ..schemas.auth import UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
