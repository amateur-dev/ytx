import sys
from ytx.config import YtxConfig
from ytx.cli import process_url

def test_video_1():
    print("=== Testing Video 1 (Claude Code) -> English Cleanup ===")
    config = YtxConfig(
        urls=["https://youtu.be/fl1DSmwQKKY"],
        translation_method="cli_opencode",
        target_lang="English",
        output_format="srt",
        verbose=False
    )
    process_url("https://youtu.be/fl1DSmwQKKY", config)

def test_video_2a():
    print("\n=== Testing Video 2 (Hindi) -> Hindi Cleanup ===")
    config = YtxConfig(
        urls=["https://youtu.be/W5mhWHgobz4"],
        translation_method="cli_opencode",
        target_lang="Hindi",
        output_format="srt",
        verbose=False
    )
    process_url("https://youtu.be/W5mhWHgobz4", config)

def test_video_2b():
    print("\n=== Testing Video 2 (Hindi) -> English Translation ===")
    config = YtxConfig(
        urls=["https://youtu.be/W5mhWHgobz4"],
        translation_method="cli_opencode",
        target_lang="English",
        output_format="srt",
        verbose=False
    )
    process_url("https://youtu.be/W5mhWHgobz4", config)

if __name__ == "__main__":
    test_video_1()
    test_video_2a()
    test_video_2b()
