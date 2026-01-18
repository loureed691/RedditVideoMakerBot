"""
Utility module for generating word-level timing information for text-to-speech.
This module estimates word timings based on audio duration and word count.
"""
import json
import re
from pathlib import Path
from typing import List, Dict


def estimate_word_timings(text: str, audio_duration: float) -> List[Dict[str, any]]:
    """
    Estimate word-level timing based on text and audio duration.
    
    Args:
        text: The text that was spoken
        audio_duration: Duration of the audio in seconds
    
    Returns:
        List of dictionaries with 'word', 'start', and 'end' times
    """
    # Split text into words (removing extra whitespace and punctuation for timing)
    words = text.split()
    if not words:
        return []
    
    # Calculate average time per word
    time_per_word = audio_duration / len(words)
    
    timings = []
    current_time = 0.0
    
    for word in words:
        # Clean word for display but keep original for timing calculation
        clean_word = word.strip()
        if clean_word:
            timings.append({
                'word': clean_word,
                'start': current_time,
                'end': current_time + time_per_word
            })
            current_time += time_per_word
    
    return timings


def save_word_timings(timings: List[Dict[str, any]], filepath: str):
    """
    Save word timings to a JSON file.
    
    Args:
        timings: List of word timing dictionaries
        filepath: Path to save the JSON file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(timings, f, indent=2, ensure_ascii=False)


def load_word_timings(filepath: str) -> List[Dict[str, any]]:
    """
    Load word timings from a JSON file.
    
    Args:
        filepath: Path to the JSON file
    
    Returns:
        List of word timing dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_progressive_text_at_time(timings: List[Dict[str, any]], time: float) -> str:
    """
    Get the text that should be displayed at a given time.
    Returns all words that have started by the given time.
    
    Args:
        timings: List of word timing dictionaries
        time: Current time in seconds
    
    Returns:
        String containing all words that should be visible at the given time
    """
    visible_words = [
        timing['word'] 
        for timing in timings 
        if timing['start'] <= time
    ]
    return ' '.join(visible_words)
