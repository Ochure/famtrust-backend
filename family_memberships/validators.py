"""
Mixins to validate the data given before creating or updating a family
membership or family group.
"""

from rest_framework import status

from family_memberships import models
from famtrust import utils


class FamilyGroupValidatorMixin:
    """Mixin to validate the data given before creating or
    updating a family group."""

    def get_user_data(self):
        """Get the user data from the request."""
        return self.context["request"].ft_user

    def validate(self, data):
        """Validate the data given before creating or updating a
        family group."""
        self.validate_user_is_admin()
        self.validate_default_group_exists(data)
        self.validate_unique_together(data)

        print("no errors")
        return data

    def validate_default_group_exists(self, data):
        """Validate that only one family group can be the default group."""
        user_data = self.get_user_data()
        user_default_group = models.FamilyGroup.objects.filter(
            owner_id=user_data.get("id"),
            is_default=True,
        )
        if data.get("is_default") and user_default_group.exists():
            raise utils.HTTPException(
                detail={
                    "error": "A default group already exists for this "
                    "user."
                },
                status_code=status.HTTP_409_CONFLICT,
            )

        elif not user_default_group.exists() and not data.get("is_default"):
            raise utils.HTTPException(
                detail={
                    "error": "A default group must exist before creating a "
                    "new group."
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def validate_user_is_admin(self):
        """Validate that the user is an admin before creating a
        family group."""
        user = self.get_user_data()
        if user.get("role").get("id") != "admin":
            raise utils.HTTPException(
                detail={
                    "error": "The user must be an admin to create a family "
                    "group."
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

    def validate_unique_together(self, data):
        """Validate that the name and owner_id of the family group are
        unique together."""
        family_group = models.FamilyGroup.objects.filter(
            name=data.get("name"), owner_id=self.get_user_data().get("id")
        )

        print(family_group)
        if family_group.exists():
            raise utils.HTTPException(
                detail={
                    "error": "A family group with the same name already "
                    "exists for this user."
                },
                status_code=status.HTTP_409_CONFLICT,
            )


class FamilyMembershipValidatorMixin:
    """Mixin to validate the data given before creating or updating a
    family membership."""

    def get_user_data(self):
        """Get the user data from the request."""
        return self.context["request"].ft_user

    def validate(self, data):
        """Validate the data given before creating or updating a
        family membership."""
        self.validate_user_is_admin()
        self.validate_user_is_not_already_in_group(data)

        return data

    def validate_user_is_admin(self):
        """Validate that the user is an admin before creating a
        family membership."""
        user = self.get_user_data()
        if user.get("role").get("id") != "admin":
            raise utils.HTTPException(
                detail={
                    "error": "The user must be an admin to create a family "
                    "membership."
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

    @staticmethod
    def validate_user_is_not_already_in_group(data):
        """Validate that the user is not already a member of the
        family group."""
        user_id = data.get("user_id")
        family_group = data.get("family_group")
        group_memberships = family_group.members.values_list(
            "user_id", flat=True
        )

        if user_id in group_memberships:
            raise utils.HTTPException(
                detail={"error": "User already exists in the family group."},
                status_code=status.HTTP_409_CONFLICT,
            )

    def validate_user_is_part_of_default_group(self, data):
        """Validate that the user is part of the default group."""
        user_id = data.get("user_id")
        user = self.get_user_data()
        default_group = models.FamilyGroup.objects.filter(
            owner_id=user.get("id"), is_default=True
        ).first()

        if not default_group:
            raise utils.HTTPException(
                detail={
                    "error": "The user must be part of the default group "
                    "before joining another group."
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        group_memberships = default_group.family_members.values_list(
            "user_id", flat=True
        )

        if user_id not in group_memberships:
            raise utils.HTTPException(
                detail={
                    "error": "The user must be part of the default group "
                    "before joining another group."
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
