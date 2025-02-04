import click

from build.utils import get_context, get_image_reference
from pathlib import Path
from python_on_whales import DockerClient, Builder


@click.command()
@click.option(
    "--docker-hub-username",
    envvar="DOCKER_HUB_USERNAME",
    help="Docker Hub username",
)
@click.option(
    "--docker-hub-password",
    envvar="DOCKER_HUB_PASSWORD",
    help="Docker Hub password",
)
@click.option(
    "--version-tag", envvar="GIT_TAG_NAME", required=True, help="Version tag"
)
@click.option(
    "--python-version",
    envvar="PYTHON_VERSION",
    required=True,
    help="Python version",
)
@click.option(
    "--os-variant",
    envvar="OS_VARIANT",
    required=True,
    help="Operating system variant",
)
@click.option(
    "--poetry-version",
    envvar="POETRY_VERSION",
    required=True,
    help="Poetry version",
)
@click.option(
    "--registry", envvar="REGISTRY", default="docker.io", help="Docker registry"
)
@click.option(
    "--use-local-cache-storage-backend",
    envvar="USE_LOCAL_CACHE_STORAGE_BACKEND",
    is_flag=True,
    help="Use local cache storage backend for docker builds",
)
def main(
    docker_hub_username: str,
    docker_hub_password: str,
    version_tag: str,
    poetry_version: str,
    python_version: str,
    os_variant: str,
    registry: str,
    use_local_cache_storage_backend: bool,
) -> None:
    context: Path = get_context()

    image_reference: str = get_image_reference(
        registry, version_tag, poetry_version, python_version, os_variant
    )

    platforms: list[str] = ["linux/amd64", "linux/arm64/v8"]
    cache_to: str = "type=gha,mode=max"
    cache_from: str = "type=gha"

    if use_local_cache_storage_backend:
        cache_to = "type=local,mode=max,dest=/tmp"
        cache_from = "type=local,src=/tmp"

    docker_client: DockerClient = DockerClient()
    builder: Builder = docker_client.buildx.create(
        driver="docker-container", driver_options=dict(network="host")
    )

    docker_client.login(
        server=registry,
        username=docker_hub_username,
        password=docker_hub_password,
    )

    docker_client.buildx.build(
        context_path=context,
        target="production-image",
        build_args={
            "POETRY_VERSION": poetry_version,
            "OFFICIAL_PYTHON_IMAGE": f"python:{python_version}-{os_variant}",
        },
        tags=image_reference,
        platforms=platforms,
        builder=builder,
        cache_to=cache_to,
        cache_from=cache_from,
        push=True,
    )

    # Cleanup
    docker_client.buildx.stop(builder)
    docker_client.buildx.remove(builder)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
