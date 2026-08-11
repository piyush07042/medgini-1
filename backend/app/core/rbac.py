from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.models import User


class RoleChecker:

    def __init__(
        self,
        allowed_roles: list[str],
    ):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(
            get_current_user
        ),
    ):

        role = str(current_user.role)

        if role not in self.allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )

        return current_user