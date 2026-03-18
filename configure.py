from pathlib import Path

import shutil

assets_dir = Path(__file__).parent / "assets"


def configure_ocr_model():
    shutil.copytree(
        assets_dir / "MaaCommonAssets" / "OCR" / "ppocr_v5" / "zh_cn",
        assets_dir / "resource" / "base" / "model" / "ocr",
        dirs_exist_ok=True,
    )
    rm_dir = assets_dir / "resource" / "base" / "model" / "ocr" / "det.onnx"
    if rm_dir.exists():
        rm_dir.unlink()
    shutil.copyfile(
        assets_dir / "MaaCommonAssets" / "OCR" / "ppocr_v4" / "zh_cn"/"det.onnx",
        assets_dir / "resource" / "base" / "model" / "ocr"/"det.onnx",
    )

if __name__ == "__main__":
    configure_ocr_model()
