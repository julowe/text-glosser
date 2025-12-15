"""
StarDict dictionary file parser.

This module provides functionality to read and query StarDict format dictionaries.
"""

import gzip
import struct
from pathlib import Path


class StarDictParser:
    """
    Parser for StarDict format dictionaries.

    This class reads StarDict .ifo, .idx, and .dict files to provide
    word lookup functionality.

    Attributes
    ----------
    ifo_file : Path
        Path to the .ifo file
    idx_file : Path
        Path to the .idx file
    dict_file : Path
        Path to the .dict or .dict.dz file
    index : Dict[str, tuple]
        Index mapping words to (offset, size) in dict file
    """

    def __init__(self, ifo_path: str):
        """
        Initialize the StarDict parser.

        Parameters
        ----------
        ifo_path : str
            Path to the .ifo file
        """
        self.ifo_file = Path(ifo_path)
        base_path = self.ifo_file.parent / self.ifo_file.stem

        self.idx_file = base_path.with_suffix('.idx')

        # Check for compressed or uncompressed dict file
        dict_dz = base_path.with_suffix('.dict.dz')
        dict_plain = base_path.with_suffix('.dict')

        if dict_dz.exists():
            self.dict_file = dict_dz
            self.is_compressed = True
        elif dict_plain.exists():
            self.dict_file = dict_plain
            self.is_compressed = False
        else:
            raise FileNotFoundError(f"Dictionary file not found for {ifo_path}")

        self.index: dict[str, tuple] = {}
        self._load_index()

    def _load_index(self):
        """Load the index from the .idx file."""
        if not self.idx_file.exists():
            raise FileNotFoundError(f"Index file not found: {self.idx_file}")

        with open(self.idx_file, 'rb') as f:
            data = f.read()

        pos = 0
        while pos < len(data):
            # Find null terminator for word
            null_pos = data.find(b'\x00', pos)
            if null_pos == -1:
                break

            # Extract word
            word = data[pos:null_pos].decode('utf-8', errors='ignore')

            # Read offset and size (both 4-byte integers)
            if null_pos + 9 > len(data):
                break

            offset = struct.unpack('>I', data[null_pos+1:null_pos+5])[0]
            size = struct.unpack('>I', data[null_pos+5:null_pos+9])[0]

            self.index[word] = (offset, size)
            pos = null_pos + 9

    def lookup(self, word: str) -> str | None:
        """
        Look up a word in the dictionary.

        Parameters
        ----------
        word : str
            The word to look up

        Returns
        -------
        Optional[str]
            The definition if found, None otherwise
        """
        if word not in self.index:
            return None

        offset, size = self.index[word]

        try:
            if self.is_compressed:
                # Read compressed dict file
                with gzip.open(self.dict_file, 'rb') as f:
                    f.seek(offset)
                    data = f.read(size)
            else:
                # Read uncompressed dict file
                with open(self.dict_file, 'rb') as f:
                    f.seek(offset)
                    data = f.read(size)

            # Decode definition
            definition = data.decode('utf-8', errors='ignore')
            return definition
        except Exception as e:
            # Log error but don't crash
            print(f"Error reading definition for '{word}': {e}")
            return None

    def search(self, prefix: str, limit: int = 10) -> list[str]:
        """
        Search for words starting with a prefix.

        Parameters
        ----------
        prefix : str
            The prefix to search for
        limit : int, optional
            Maximum number of results (default: 10)

        Returns
        -------
        List[str]
            List of matching words
        """
        matches = [
            word for word in self.index.keys()
            if word.startswith(prefix)
        ]
        return matches[:limit]

    def get_all_words(self) -> list[str]:
        """
        Get all words in the dictionary.

        Returns
        -------
        List[str]
            List of all words
        """
        return list(self.index.keys())
