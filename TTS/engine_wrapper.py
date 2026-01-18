import json
import os
import re
from pathlib import Path
from typing import Tuple

import numpy as np
import translators
from moviepy import AudioFileClip
from moviepy.audio.AudioClip import AudioClip
from moviepy.audio.fx import MultiplyVolume
from rich.progress import track

from utils import settings
from utils.console import print_step, print_substep
from utils.voice import sanitize_text
from utils.word_timing import estimate_word_timings, save_word_timings

DEFAULT_MAX_LENGTH: int = (
    50  # Video length variable, edit this on your own risk. It should work, but it's not supported
)


class TTSEngine:
    """Calls the given TTS engine to reduce code duplication and allow multiple TTS engines.

    Args:
        tts_module            : The TTS module. Your module should handle the TTS itself and saving to the given path under the run method.
        reddit_object         : The reddit object that contains the posts to read.
        path (Optional)       : The unix style path to save the mp3 files to. This must not have leading or trailing slashes.
        max_length (Optional) : The maximum length of the mp3 files in total.

    Notes:
        tts_module must take the arguments text and filepath.
    """

    def __init__(
        self,
        tts_module,
        reddit_object: dict,
        path: str = "assets/temp/",
        max_length: int = DEFAULT_MAX_LENGTH,
        last_clip_length: int = 0,
    ):
        self.tts_module = tts_module()
        self.reddit_object = reddit_object

        self.redditid = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
        self.path = path + self.redditid + "/mp3"
        self.max_length = max_length
        self.length = 0
        self.last_clip_length = last_clip_length

    def add_periods(
        self,
    ):  # adds periods to the end of paragraphs (where people often forget to put them) so tts doesn't blend sentences
        for comment in self.reddit_object["comments"]:
            # remove links
            regex_urls = r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"
            comment["comment_body"] = re.sub(regex_urls, " ", comment["comment_body"])
            comment["comment_body"] = comment["comment_body"].replace("\n", ". ")
            comment["comment_body"] = re.sub(r"\bAI\b", "A.I", comment["comment_body"])
            comment["comment_body"] = re.sub(r"\bAGI\b", "A.G.I", comment["comment_body"])
            if comment["comment_body"][-1] != ".":
                comment["comment_body"] += "."
            comment["comment_body"] = comment["comment_body"].replace(". . .", ".")
            comment["comment_body"] = comment["comment_body"].replace(".. . ", ".")
            comment["comment_body"] = comment["comment_body"].replace(". . ", ".")
            comment["comment_body"] = re.sub(r'\."\.', '".', comment["comment_body"])

    def run(self) -> Tuple[int, int]:
        Path(self.path).mkdir(parents=True, exist_ok=True)
        print_step("Saving Text to MP3 files...")

        self.add_periods()
        self.call_tts("title", process_text(self.reddit_object["thread_title"]))
        # processed_text = ##self.reddit_object["thread_post"] != ""
        idx = 0

        if settings.config["settings"]["storymode"]:
            if settings.config["settings"]["storymodemethod"] == 0:
                if len(self.reddit_object["thread_post"]) > self.tts_module.max_chars:
                    self.split_post(self.reddit_object["thread_post"], "postaudio")
                else:
                    self.call_tts("postaudio", process_text(self.reddit_object["thread_post"]))
            elif settings.config["settings"]["storymodemethod"] == 1:
                for idx, text in track(enumerate(self.reddit_object["thread_post"])):
                    self.call_tts(f"postaudio-{idx}", process_text(text))

        else:
            for idx, comment in track(enumerate(self.reddit_object["comments"]), "Saving..."):
                # ! Stop creating mp3 files if the length is greater than max length.
                if self.length > self.max_length and idx > 1:
                    self.length -= self.last_clip_length
                    idx -= 1
                    break
                if (
                    len(comment["comment_body"]) > self.tts_module.max_chars
                ):  # Split the comment if it is too long
                    self.split_post(comment["comment_body"], idx)  # Split the comment
                else:  # If the comment is not too long, just call the tts engine
                    self.call_tts(f"{idx}", process_text(comment["comment_body"]))

        print_substep("Saved Text to MP3 files successfully.", style="bold green")
        return self.length, idx

    def split_post(self, text: str, idx):
        split_files = []
        split_timings = []  # Store timing files for merging
        split_text = [
            x.group().strip()
            for x in re.finditer(
                r" *(((.|\n){0," + str(self.tts_module.max_chars) + "})(\.|.$))", text
            )
        ]
        self.create_silence_mp3()

        for idy, text_cut in enumerate(split_text):
            newtext = process_text(text_cut)
            # print(f"{idx}-{idy}: {newtext}\n")

            if not newtext or newtext.isspace():
                print("newtext was blank because sanitized split text resulted in none")
                continue
            else:
                self.call_tts(f"{idx}-{idy}.part", newtext)
                with open(f"{self.path}/list.txt", "w") as f:
                    for idz in range(0, len(split_text)):
                        f.write("file " + f"'{idx}-{idz}.part.mp3'" + "\n")
                    split_files.append(str(f"{self.path}/{idx}-{idy}.part.mp3"))
                    f.write("file " + f"'silence.mp3'" + "\n")

                # Track timing files for merging
                timing_file = f"{self.path}/{idx}-{idy}.part_timings.json"
                if os.path.exists(timing_file):
                    split_timings.append(timing_file)

                os.system(
                    "ffmpeg -f concat -y -hide_banner -loglevel panic -safe 0 "
                    + "-i "
                    + f"{self.path}/list.txt "
                    + "-c copy "
                    + f"{self.path}/{idx}.mp3"
                )

        # Merge timing files if word-by-word feature is enabled
        if settings.config["settings"].get("word_by_word_text", False) and split_timings:
            self._merge_timing_files(split_timings, f"{self.path}/{idx}_timings.json")

        try:
            for i in range(0, len(split_files)):
                os.unlink(split_files[i])
                # Also clean up part timing files
                timing_file = split_files[i].replace(".mp3", "_timings.json")
                if os.path.exists(timing_file):
                    os.unlink(timing_file)
        except FileNotFoundError as e:
            print("File not found: " + e.filename)
        except OSError:
            print("OSError")

    def call_tts(self, filename: str, text: str):
        if settings.config["settings"]["tts"]["voice_choice"] == "googletranslate":
            # GTTS does not have the argument 'random_voice'
            self.tts_module.run(
                text,
                filepath=f"{self.path}/{filename}.mp3",
            )
        else:
            self.tts_module.run(
                text,
                filepath=f"{self.path}/{filename}.mp3",
                random_voice=settings.config["settings"]["tts"]["random_voice"],
            )
        # try:
        #     self.length += MP3(f"{self.path}/{filename}.mp3").info.length
        # except (MutagenError, HeaderNotFoundError):
        #     self.length += sox.file_info.duration(f"{self.path}/{filename}.mp3")
        try:
            clip = AudioFileClip(f"{self.path}/{filename}.mp3")
            self.last_clip_length = clip.duration
            self.length += clip.duration

            # Generate and save word timing information if word-by-word feature is enabled
            if settings.config["settings"].get("word_by_word_text", False):
                try:
                    timings = estimate_word_timings(text, clip.duration)
                    timing_path = f"{self.path}/{filename}_timings.json"
                    save_word_timings(timings, timing_path)
                except (OSError, ValueError, TypeError) as e:
                    print(
                        f"Warning: Could not generate word timings for {filename} "
                        f"({type(e).__name__}: {e})"
                    )

            clip.close()
        except Exception:
            self.length = 0

    def create_silence_mp3(self):
        silence_duration = settings.config["settings"]["tts"]["silence_duration"]
        silence = AudioClip(
            frame_function=lambda t: np.sin(440 * 2 * np.pi * t),
            duration=silence_duration,
            fps=44100,
        )
        silence = silence.with_effects([MultiplyVolume(0)])
        silence.write_audiofile(f"{self.path}/silence.mp3", fps=44100, logger=None)

    def _merge_timing_files(self, timing_files: list, output_file: str):
        """
        Merge multiple timing files from split posts into a single timing file.
        Adjusts timing offsets to account for concatenated audio.

        Args:
            timing_files: List of paths to timing JSON files to merge
            output_file: Path to save the merged timing file
        """
        merged_timings = []
        current_offset = 0.0

        for timing_file in timing_files:
            try:
                with open(timing_file, "r", encoding="utf-8") as f:
                    timings = json.load(f)

                # Add offset to all timings and append
                for timing in timings:
                    merged_timings.append(
                        {
                            "word": timing["word"],
                            "start": timing["start"] + current_offset,
                            "end": timing["end"] + current_offset,
                        }
                    )

                # Update offset for next segment (using the last word's end time)
                if timings:
                    current_offset = merged_timings[-1]["end"]
                    # Add silence duration between segments
                    silence_duration = settings.config["settings"]["tts"]["silence_duration"]
                    current_offset += silence_duration

            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not read timing file {timing_file}: {e}")
                continue

        # Save merged timings
        if merged_timings:
            save_word_timings(merged_timings, output_file)


def process_text(text: str, clean: bool = True):
    lang = settings.config["reddit"]["thread"]["post_lang"]
    new_text = sanitize_text(text) if clean else text
    if lang:
        print_substep("Translating Text...")
        translated_text = translators.translate_text(text, translator="google", to_language=lang)
        new_text = sanitize_text(translated_text)
    return new_text
