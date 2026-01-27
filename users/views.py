                logger.info(
                    "Password reset requested",
                    extra={"user_id": user.id}
                )
            else:
                logger.info(
                    "Password reset requested for non-existent email",
                    extra={"reason": "email_not_found"}
                )
