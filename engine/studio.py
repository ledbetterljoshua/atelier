"""Housekeeping shared by every artist: where a finished board and its record go."""
import json
import time
from pathlib import Path

from PIL import Image

T0 = time.time()


def finish(board, here, **meta):
    here = Path(here)
    (here / "stages").mkdir(exist_ok=True)
    for old in (here / "stages").glob("*.jpg"):
        old.unlink()
    board.stage("finished")
    Image.fromarray(board.stages[-1][2]).save(here / "final.png")
    stages = []
    for i, (name, n, img) in enumerate(board.stages):
        fn = f"{i:02d}.jpg"
        im = Image.fromarray(img)
        im.thumbnail((1400, 1400))
        im.save(here / "stages" / fn, quality=86)
        stages.append({"name": name, "strokes": n, "file": f"stages/{fn}"})
    meta.update(strokes=board.n_strokes, size=[board.w, board.h], stages=stages,
                seconds=round(time.time() - T0, 1))
    (here / "work.json").write_text(json.dumps(meta, indent=2))
    print(f"{meta.get('title', here.name)}: {board.n_strokes} strokes, {meta['seconds']}s")
