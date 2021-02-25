"""
TONAS Loader

.. admonition:: Dataset Info
    :class: dropdown

    This dataset contains a music collection of 72 sung excerpts representative of three a cappella singing styles
    (Deblas, and two variants of Martinete). It has been developed within the COFLA research project context.
    The distribution is as follows:
    * 16 Deblas
    * 36 Martinete 1
    * 20 Martinete 2

    This collection was built in the context of a study on similarity and style classification of flamenco a cappella
    singing styles (Tonas) by the flamenco expert Dr. Joaquin Mora, Universidad de Sevilla.

    We refer to (Mora et al. 2010) for a comprehensive description of the considered styles and their musical
    characteristics. All 72 excerpts are monophonic, their average duration is 30 seconds and there is enough
    variability for a proper evaluation of our methods, including a variety of singers, recording conditions,
    presence of percussion, clapping, background voices and noise. We also provide manual melodic transcriptions,
    generated by the COFLA team and Cristina López Gómez.

    Using this dataset:
    TONAS dataset can be obtained upon request. Please refer to this link: https://zenodo.org/record/1290722 to
    request access and follow the indications of the .download() method for a proper storing and organization
    of the TONAS dataset.
    When TONAS is used for academic research, we would highly appreciate if scientific publications of works
    partly based on the TONAS dataset quote the following publication:

"""
import csv
import os
from typing import cast, Optional, TextIO, Tuple

import librosa
import numpy as np

from mirdata import download_utils
from mirdata import jams_utils
from mirdata import core
from mirdata import annotations
from mirdata import io


BIBTEX = """
@dataset{cofla_computational_analysis_of_flamenco_2013_1290722,
    author       = {COFLA (COmputational analysis of FLAmenco music) team},
    title        = {{TONAS: a dataset of flamenco a cappella sung 
                     melodies with corresponding manual transcriptions}},
    month        = mar,
    year         = 2013,
    publisher    = {Zenodo},
    version      = {1.0},
    doi          = {10.5281/zenodo.1290722},
    url          = {https://doi.org/10.5281/zenodo.1290722}
}
@inproceedings{inproceedings,
    author = {Mora, Joaquin and Gómez, Francisco and Gómez, Emilia
              and Borrego, Francisco Javier and Díaz-Báñez, José},
    year = {2010},
    month = {01},
    pages = {351-356},
    title = {Characterization and Similarity in A Cappella Flamenco Cantes.}
}
@ARTICLE{6791736,
    author = {E. {Gómez} and J. {Bonada}},
    journal = {Computer Music Journal},
    title = {Towards Computer-Assisted Flamenco Transcription: An Experimental 
           Comparison of Automatic Transcription Algorithms as Applied to A 
           Cappella Singing},
    year = {2013},
    volume = {37},
    number = {2},
    pages = {73-90},
    doi = {10.1162/COMJ_a_00180}}
"""


REMOTES = {}

DOWNLOAD_INFO = """
        Unfortunately, the TONAS dataset is not available to be shared openly. However,
        you can request access to the dataset in the following link, providing a brief
        explanation of what your are going to use the dataset for:
        ==> https://zenodo.org/record/1290722
        Then, unzip the dataset and locate it to {}. If you unzip it into a different path,
        please remember to set the right data_home when initializing the dataset.
"""

LICENSE_INFO = """
The TONAS dataset is offered free of charge for internal non-commercial use only. You can not redistribute it nor 
modify it. Dataset by COFLA team. Copyright © 2012 COFLA project, Universidad de Sevilla. Distribution rights granted 
to Music Technology Group, Universitat Pompeu Fabra. All Rights Reserved.
"""


class NoteDataTonas(annotations.NoteData):
    def __init__(self, intervals, notes, energies, confidence=None):
        super().__init__(intervals, notes, confidence)

        annotations.validate_array_like(intervals, np.ndarray, float)
        annotations.validate_array_like(notes, np.ndarray, float)
        annotations.validate_array_like(energies, np.ndarray, float)
        annotations.validate_array_like(
            confidence, np.ndarray, float, none_allowed=True
        )
        annotations.validate_lengths_equal([intervals, notes, energies, confidence])
        annotations.validate_intervals(intervals)
        annotations.validate_confidence(confidence)

        self.intervals = intervals
        self.notes = notes
        self.energies = energies
        self.confidence = confidence


class F0DataTonas(annotations.F0Data):
    def __init__(
        self, times, automatic_frequencies, frequencies, energies, confidence=None
    ):
        super().__init__(times, frequencies, confidence)

        annotations.validate_array_like(times, np.ndarray, float)
        annotations.validate_array_like(automatic_frequencies, np.ndarray, float)
        annotations.validate_array_like(frequencies, np.ndarray, float)
        annotations.validate_array_like(energies, np.ndarray, float)
        annotations.validate_array_like(
            confidence, np.ndarray, float, none_allowed=True
        )
        annotations.validate_lengths_equal(
            [times, automatic_frequencies, frequencies, energies, confidence]
        )
        annotations.validate_times(times)
        annotations.validate_confidence(confidence)

        self.times = times
        self.automatic_frequencies = automatic_frequencies
        self.frequencies = frequencies
        self.energies = energies
        self.confidence = confidence


class Track(core.Track):
    """TONAS track class

    Args:
        track_id (str): track id of the track
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets/TONAS`

    Attributes:
        f0_path (str): local path where f0 melody annotation file is stored
        notes_path = local path where notation annotation file is stored
        audio_path = local path where audio file is stored

    Properties:
        track_id (str): track id
        singer (str): performing singer (cantaor)
        title (str): title of the track song
        tuning_frequency (float): tuning frequency of the symbolic notation

    Cached Properties:
        melody (F0DataTonas): annotated melody in extended F0Data format
        notes (NoteData): annotated notes

    """

    def __init__(
        self,
        track_id,
        data_home,
        dataset_name,
        index,
        metadata,
    ):
        super().__init__(
            track_id,
            data_home,
            dataset_name,
            index,
            metadata,
        )

        self.f0_path = self.get_path("f0")
        self.notes_path = self.get_path("notes")

        self.audio_path = self.get_path("audio")

    @property
    def style(self):
        return self._track_metadata.get("style")

    @property
    def singer(self):
        return self._track_metadata.get("singer")

    @property
    def title(self):
        return self._track_metadata.get("title")

    @property
    def tuning_frequency(self):
        return load_notes(self.notes_path)[1]

    @property
    def audio(self) -> Tuple[np.ndarray, float]:
        """The track's audio

        Returns:
            * np.ndarray - audio signal
            * float - sample rate

        """
        return load_audio(self.audio_path)

    @core.cached_property
    def f0(self) -> Optional[annotations.F0Data]:
        return load_f0(self.f0_path)

    @core.cached_property
    def notes(self) -> Optional[annotations.NoteData]:
        return load_notes(self.notes_path)[0]

    def to_jams(self):
        """Get the track's data in jams format

        Returns:
            jams.JAMS: the track's data in jams format

        """
        return jams_utils.jams_converter(
            audio_path=self.audio_path,
            f0_data=[(self.f0, "pitch_contour")],
            note_data=[(self.notes, "note_hz")],
            metadata=self._track_metadata,
        )


def load_audio(fhandle: str) -> Tuple[np.ndarray, float]:
    """Load a TONAS audio file.

    Args:
        fhandle (str): path to an audio file

    Returns:
        * np.ndarray - the mono audio signal
        * float - The sample rate of the audio file

    """
    return librosa.load(fhandle, sr=44100, mono=True)


@io.coerce_to_string_io
def load_f0(fhandle: TextIO) -> F0DataTonas:
    """Load TONAS f0 annotations

    Args:
        fhandle (str or file-like): path or file-like object pointing to f0 annotation file

    Returns:
        F0DataTonas: predominant f0 melody

    """
    times = []
    freqs = []
    freqs_corr = []
    energies = []
    reader = np.genfromtxt(fhandle)
    for line in reader:
        times.append(float(line[0]))
        energies.append(float(line[1]))
        freqs.append(float(line[2]))
        freqs_corr.append(float(line[3]))

    times = np.array(times)
    freqs = np.array(freqs)
    freqs_corr = np.array(freqs_corr)
    energies = np.array(energies)
    confidence = (cast(np.ndarray, freqs_corr) > 0).astype(float)

    return F0DataTonas(times, freqs, freqs_corr, energies, confidence)


@io.coerce_to_string_io
def load_notes(fhandle: TextIO) -> [NoteDataTonas, float]:
    """Load note data from the annotation files

    Args:
        fhandle (str or file-like): path or file-like object pointing to a notes annotation file

    Returns:
        NoteData: note annotations

    """
    intervals = []
    pitches = []
    energy = []
    confidence = []
    tuning_freq = 0

    reader = csv.reader(fhandle, delimiter=",")
    tuning = next(reader)[0]
    for line in reader:
        intervals.append([line[0], float(line[0]) + float(line[1])])
        # Convert midi value to frequency
        note_hz, tuning_freq = midi_to_hz(float(line[2]), float(tuning))
        pitches.append(note_hz)
        energy.append(float(line[3]))
        confidence.append(1.0)

    return (
        NoteDataTonas(
            np.array(intervals, dtype="float"),
            np.array(pitches, dtype="float"),
            np.array(energy, dtype="float"),
            np.array(confidence, dtype="float"),
        ),
        tuning_freq,
    )


# Function to convert MIDI to Hz with certain tuning freq
def midi_to_hz(midi_note, tuning_deviation):
    tuning_frequency = 440 * (
        2 ** (tuning_deviation / 1200)
    )  # Frequency of A (common value is 440Hz)
    return (tuning_frequency / 32) * (2 ** ((midi_note - 9) / 12)), tuning_frequency


@core.docstring_inherit(core.Dataset)
class Dataset(core.Dataset):
    """
    The TONAS dataset
    """

    def __init__(self, data_home=None):
        super().__init__(
            data_home,
            name="TONAS",
            track_class=Track,
            bibtex=BIBTEX,
            remotes=REMOTES,
            download_info=DOWNLOAD_INFO,
            license_info=LICENSE_INFO,
        )

    @core.cached_property
    def _metadata(self):
        metadata_path = os.path.join(self.data_home, "TONAS-Metadata.txt")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError("Metadata not found. Did you run .download()?")

        metadata = {}
        with open(metadata_path, "r", errors="ignore") as f:
            reader = csv.reader(
                (x.replace("\0", "") for x in f), delimiter="\t"
            )  # Fix wrong byte
            for line in reader:
                if line:  # Do not consider empty lines
                    index = line[0].replace(".wav", "")
                    metadata[index] = {
                        "style": line[1],
                        "title": line[2],
                        "singer": line[3],
                    }

        return metadata

    @core.copy_docs(load_audio)
    def load_audio(self, *args, **kwargs):
        return load_audio(*args, **kwargs)

    @core.copy_docs(load_f0)
    def load_f0(self, *args, **kwargs):
        return load_f0(*args, **kwargs)

    @core.copy_docs(load_notes)
    def load_notes(self, *args, **kwargs):
        return load_notes(*args, **kwargs)
