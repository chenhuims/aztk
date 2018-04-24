from aztk.internal import ConfigurationBase
from aztk.error import InvalidModelError
from aztk.utils import constants

class ToolkitDefinition:
    def __init__(self, versions, environments):
        self.versions = versions
        self.environments = environments

class ToolkitEnvironmentDefinition:
    def __init__(self, versions=None, default=""):
        self.versions = versions or [""]
        self.default = default

TOOLKIT_MAP = dict(
    spark=ToolkitDefinition(
        versions=["1.6", "2.1", "2.2"],
        environments=dict(
            base=ToolkitEnvironmentDefinition(),
            python=ToolkitEnvironmentDefinition(),
            r=ToolkitEnvironmentDefinition(),
            anaconda=ToolkitEnvironmentDefinition(),
        )
    ),
)


class Toolkit(ConfigurationBase):
    """
    Toolkit for a cluster.
    This will help pick the docker image needed

    Args:
        name (str): Name of the toolkit
        version (str): Version of the toolkit
        environment (str): Which environment to use for this toolkit
        environment_version (str): If there is multiple version for an environment you can specify which one
    """
    def __init__(self, name: str, version: str, environment: str=None, environment_version: str=None, docker_repo=None):
        self.name = name
        self.version = version
        self.environment = environment
        self.environment_version = environment_version
        self.docker_repo = docker_repo


    def validate(self):
        self._validate_required(["name", "version"])

        if self.name not in TOOLKIT_MAP:
            raise InvalidModelError("Toolkit {0} is not in the list of allowed toolkits {1}".format(
                self.name, TOOLKIT_MAP.keys()))

        toolkit_def = TOOLKIT_MAP[self.name]

        if self.version not in toolkit_def.versions:
            raise InvalidModelError("Toolkit {0} with version {1} is not available. Use one of: {2}".format(
                self.name, self.version, TOOLKIT_MAP.keys()))

        if self.environment:
            if self.environment not in toolkit_def.environments:
                raise InvalidModelError("Environment {0} for toolkit {1} is not available. Use one of: {3}".format(
                    self.environment, self.name, toolkit_def.environments.keys()))

            env_def = toolkit_def.environments[self.environment]

            if self.environment_version and self.environment_version not in env_def.versions:
                raise InvalidModelError(
                    "Environment {0} version {1} for toolkit {2} is not available. Use one of: {4}".format(
                        self.environment, self.environment_version, self.name, env_def.versions))


    def get_docker_repo(self, gpu: bool):
        if self.docker_repo:
            return self.docker_repo

        repo = "aztk/{0}".format(self.name)

        return "{repo}:{tag}".format(
            repo=repo,
            tag=self._get_docker_tag(gpu),
        )

    def _get_docker_tag(self, gpu: bool):
        environment = self.environment or "base"
        environment_def = self._get_environent_definition()
        environment_version = self.environment_version or environment_def.default

        array = [
            "v{docker_image_version}".format(docker_image_version=constants.DOCKER_IMAGE_VERSION),
            "{toolkit}{version}".format(toolkit=self.name, version=self.version),
        ]
        if self.environment:
            array.append("{0}{1}".format(environment, environment_version))

        array.append("gpu" if gpu else "base")

        return '-'.join(array)


    def _get_environent_definition(self) -> ToolkitEnvironmentDefinition:
        return TOOLKIT_MAP[self.name].environments[self.environment or "base"]
