from pydub import AudioSegment
import json
import glob

timeline = []

for file in sorted(glob.glob("audio/*.mp3")):

    audio = AudioSegment.from_mp3(file)

    timeline.append({"file": file, "duration": len(audio) / 1000})

json.dump(timeline, open("build/timeline.json", "w"), indent=2)
