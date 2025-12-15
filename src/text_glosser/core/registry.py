"""
Dictionary and resource registry.

This module manages the registration and retrieval of linguistic resources,
including built-in dictionaries and user-uploaded resources.
"""

from pathlib import Path

from ..core.models import DictionaryFormat, DictionaryResource, ResourceType


class ResourceRegistry:
    """
    Registry for managing linguistic resources and dictionaries.

    This class provides methods to register, retrieve, and manage
    dictionaries and linguistic resources organized by language.

    Attributes
    ----------
    resources : Dict[str, DictionaryResource]
        Dictionary of resources keyed by resource ID
    resources_dir : Path
        Base directory for resource files
    """

    def __init__(self, resources_dir: str = "./language_resources"):
        """
        Initialize the resource registry.

        Parameters
        ----------
        resources_dir : str, optional
            Path to the resources directory (default: "./language_resources")
        """
        self.resources: dict[str, DictionaryResource] = {}
        self.resources_dir = Path(resources_dir)
        self._load_builtin_resources()

    def _load_builtin_resources(self):
        """Load built-in resources from the language_resources directory."""
        # StarDict - Monier-Williams Sanskrit-English
        mw_path = self.resources_dir / "sa" / "monier-williams-cologne"
        if mw_path.exists():
            self.register_resource(
                DictionaryResource(
                    id="mw-sanskrit-english",
                    name="Monier-Williams Sanskrit-English Dictionary (Cologne)",
                    format=DictionaryFormat.STARDICT,
                    resource_type=ResourceType.DICTIONARY,
                    primary_language="sa",
                    secondary_languages=["en"],
                    file_paths=[
                        str(mw_path / "mw-cologne.ifo"),
                        str(mw_path / "mw-cologne.idx"),
                        str(mw_path / "mw-cologne.dict.dz"),
                    ],
                    source_url="https://www.sanskrit-lexicon.uni-koeln.de/",
                    is_user_provided=False,
                )
            )

        # StarDict - Lane's Arabic-English Lexicon
        lane_path = self.resources_dir / "ar" / "lane-lexicon"
        if lane_path.exists():
            self.register_resource(
                DictionaryResource(
                    id="lane-arabic-english",
                    name="Lane's Arabic-English Lexicon",
                    format=DictionaryFormat.STARDICT,
                    resource_type=ResourceType.DICTIONARY,
                    primary_language="ar",
                    secondary_languages=["en"],
                    file_paths=[
                        str(lane_path / "Lane-Arabic-English-Lexicon.ifo"),
                        str(lane_path / "Lane-Arabic-English-Lexicon.idx"),
                        str(lane_path / "Lane-Arabic-English-Lexicon.dict.dz"),
                    ],
                    is_user_provided=False,
                )
            )

        # StarDict - Salmone's Arabic-English Lexicon
        salmone_path = self.resources_dir / "ar" / "salmone-lexicon"
        if salmone_path.exists():
            self.register_resource(
                DictionaryResource(
                    id="salmone-arabic-english",
                    name="Salmone's Arabic-English Lexicon",
                    format=DictionaryFormat.STARDICT,
                    resource_type=ResourceType.DICTIONARY,
                    primary_language="ar",
                    secondary_languages=["en"],
                    file_paths=[
                        str(salmone_path / "Salmone-Ara-Eng-Lexicon.ifo"),
                        str(salmone_path / "Salmone-Ara-Eng-Lexicon.idx"),
                        str(salmone_path / "Salmone-Ara-Eng-Lexicon.dict.dz"),
                    ],
                    is_user_provided=False,
                )
            )

        # hanzipy library
        self.register_resource(
            DictionaryResource(
                id="hanzipy-chinese",
                name="HanziPy - Chinese Character Information",
                format=DictionaryFormat.HANZIPY,
                resource_type=ResourceType.LIBRARY,
                primary_language="zh",
                secondary_languages=["en"],
                is_user_provided=False,
                source_url="https://pypi.org/project/hanzipy/",
            )
        )

    def register_resource(self, resource: DictionaryResource):
        """
        Register a new resource.

        Parameters
        ----------
        resource : DictionaryResource
            The resource to register
        """
        self.resources[resource.id] = resource

    def get_resource(self, resource_id: str) -> DictionaryResource | None:
        """
        Get a resource by ID.

        Parameters
        ----------
        resource_id : str
            The resource ID

        Returns
        -------
        Optional[DictionaryResource]
            The resource if found, None otherwise
        """
        return self.resources.get(resource_id)

    def get_resources_by_language(self, language_code: str) -> list[DictionaryResource]:
        """
        Get all resources for a specific language.

        Parameters
        ----------
        language_code : str
            ISO 639 language code

        Returns
        -------
        List[DictionaryResource]
            List of resources for the language
        """
        return [
            res
            for res in self.resources.values()
            if res.primary_language == language_code
        ]

    def get_all_languages(self) -> list[str]:
        """
        Get all language codes that have resources.

        Returns
        -------
        List[str]
            List of unique language codes
        """
        languages = set()
        for res in self.resources.values():
            languages.add(res.primary_language)
            languages.update(res.secondary_languages)
        return sorted(languages)

    def get_resources_grouped_by_language(self) -> dict[str, list[DictionaryResource]]:
        """
        Get all resources grouped by primary language.

        Returns
        -------
        Dict[str, List[DictionaryResource]]
            Dictionary mapping language codes to resource lists
        """
        grouped = {}
        for res in self.resources.values():
            lang = res.primary_language
            if lang not in grouped:
                grouped[lang] = []
            grouped[lang].append(res)
        return grouped

    def get_all_resources(self) -> list[DictionaryResource]:
        """
        Get all registered resources.

        Returns
        -------
        List[DictionaryResource]
            List of all resources
        """
        return list(self.resources.values())

    def verify_resource_accessible(self, resource_id: str) -> bool:
        """
        Verify that a resource's files are accessible.

        Parameters
        ----------
        resource_id : str
            The resource ID to verify

        Returns
        -------
        bool
            True if resource is accessible, False otherwise
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return False

        # Library-based resources don't have files
        if resource.resource_type == ResourceType.LIBRARY:
            return True

        # Check if all files exist
        if resource.file_paths:
            return all(Path(fp).exists() for fp in resource.file_paths)

        return True


# Global registry instance
_global_registry: ResourceRegistry | None = None


def get_registry(resources_dir: str = "./language_resources") -> ResourceRegistry:
    """
    Get or create the global resource registry instance.

    Parameters
    ----------
    resources_dir : str, optional
        Path to resources directory (default: "./language_resources")

    Returns
    -------
    ResourceRegistry
        The global registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ResourceRegistry(resources_dir)
    return _global_registry
