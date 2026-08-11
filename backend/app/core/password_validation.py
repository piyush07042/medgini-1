import re

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
)


def validate_password(
    password: str,
):

    if not PASSWORD_REGEX.match(password):

        raise ValueError(
            "Password must contain uppercase, lowercase, number and minimum 8 characters."
        )