"""Dependency injection container using dependency-injector.

This container wires all dependencies and provides them to application.
"""

from dependency_injector import containers, providers

from alphasnob.application.services.message_handling_service import MessageHandlingService
from alphasnob.domain.decisions.services.decision_engine import DecisionEngine
from alphasnob.domain.users.value_objects.user_id import UserId
from alphasnob.infrastructure.config.settings import Settings, get_settings
from alphasnob.infrastructure.persistence.database import Database
from alphasnob.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserProfileRepository,
)


class Container(containers.DeclarativeContainer):  # type: ignore[misc]
    """Main DI container for AlphaSnobAI.

    Provides all dependencies for the application using dependency injection.

    Usage:
        container = Container()
        container.wire(modules=[__name__])

        # Use with @inject decorator
        @inject
        def my_function(service: MessageHandlingService = Provide[Container.message_handling_service]):
            ...
    """

    # Configuration
    config: providers.Singleton[Settings] = providers.Singleton(
        get_settings,
    )

    # Database
    database: providers.Singleton[Database] = providers.Singleton(
        Database,
        database_url=providers.Factory(
            lambda settings: f"sqlite+aiosqlite:///{settings.paths.database}",
            settings=config,
        ),
        echo=providers.Factory(
            lambda settings: settings.debug,
            settings=config,
        ),
    )

    # Repositories
    user_profile_repository = providers.Factory(
        SQLAlchemyUserProfileRepository,
        session=database.provided.session,
    )

    # Domain Services
    decision_engine: providers.Singleton[DecisionEngine] = providers.Singleton(
        DecisionEngine,
        base_probability=providers.Factory(
            lambda settings: settings.bot.response_probability,
            settings=config,
        ),
    )

    # Bot user ID (will be set after authentication)
    bot_user_id: providers.Object[UserId | None] = providers.Object(None)

    # Application Services
    message_handling_service = providers.Factory(
        MessageHandlingService,
        message_repository=None,  # TODO: implement
        user_profile_repository=user_profile_repository,
        decision_engine=decision_engine,
        bot_user_id=bot_user_id,
        bot_username=providers.Factory(
            lambda settings: settings.telegram.session_name,
            settings=config,
        ),
    )


def create_container() -> Container:
    """Create and configure DI container.

    Returns:
        Configured Container instance
    """
    return Container()
