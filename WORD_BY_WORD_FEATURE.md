# Word-by-Word Text Display Feature

## Overview

This feature enables text to appear word by word synchronized with the spoken audio in your Reddit videos. As the TTS reads each word, it will progressively appear on screen, creating a more engaging viewing experience similar to karaoke-style subtitles.

## How It Works

1. **Word Timing Estimation**: When TTS audio is generated, the system estimates when each word is spoken based on the total audio duration and word count.

2. **Timing Storage**: Word timing information is saved as JSON files alongside the MP3 audio files (e.g., `title_timings.json`, `0_timings.json`, etc.).

3. **Progressive Text Overlay**: During video rendering, FFmpeg's `drawtext` filter is used to display text progressively, showing only the words that have been spoken up to that point in time.

## Configuration

To enable word-by-word text display, add the following to your `config.toml`:

```toml
[settings]
word_by_word_text = true
```

### Configuration Options

- **word_by_word_text** (boolean, default: false)
  - `true`: Enable word-by-word text display
  - `false`: Use standard full-text display

## Best Use Cases

This feature works best with:
- **Story Mode** (especially `storymodemethod = 1`): The progressive text appears over the generated images
- **Longer text segments**: More words provide better synchronization
- **Clear, paced speech**: Works better with TTS voices that have consistent pacing

## Technical Details

### Text Positioning
- Text appears in the lower portion of the video (at 70% height)
- Centered horizontally
- Semi-transparent black background box for readability

### Font Settings
- Font: Roboto Bold
- Size: Automatically scaled based on video resolution (H/30)
- Color: White text with black background box

### Compatibility
- Works with all TTS providers (GoogleTranslate, AWS Polly, TikTok, etc.)
- Compatible with both story mode and comment mode
- Works with different video resolutions

## File Structure

When word-by-word text is enabled, additional JSON files are created:

```
assets/temp/{reddit_id}/mp3/
  ├── title.mp3
  ├── title_timings.json          # New: Word timings for title
  ├── 0.mp3
  ├── 0_timings.json              # New: Word timings for comment 0
  ├── postaudio-0.mp3
  ├── postaudio-0_timings.json    # New: Word timings for story segment 0
  └── ...
```

### Timing JSON Format

```json
[
  {
    "word": "This",
    "start": 0.0,
    "end": 0.5
  },
  {
    "word": "is",
    "start": 0.5,
    "end": 1.0
  },
  ...
]
```

## Example Usage

1. Enable the feature in your config:
   ```toml
   [settings]
   word_by_word_text = true
   storymode = true
   storymodemethod = 1
   ```

2. Run the bot as usual:
   ```bash
   python main.py
   ```

3. The generated video will show text appearing word by word as it's spoken!

## Troubleshooting

### Text not appearing
- Check that `word_by_word_text = true` in your config
- Verify that timing JSON files are being created in the mp3 directory
- Ensure FFmpeg is properly installed and up to date

### Timing seems off
- The timing is estimated based on average word duration
- For better timing, consider using TTS providers that support word-level timing natively (future enhancement)
- Longer audio segments generally have better timing accuracy

### Text overlaps with other elements
- Text is positioned at 70% height by default
- If needed, you can adjust the position by modifying the `y_pos` value in `apply_word_by_word_text()` function in `video_creation/final_video.py`

## Future Enhancements

Potential improvements for this feature:
- Support for word-level timing from TTS providers that offer it (e.g., AWS Polly Speech Marks)
- Configurable text position and styling
- Word highlighting instead of progressive display
- Support for multiple text overlay positions
