from maa.context import Context
from maa.custom_action import CustomAction
from PIL import Image
import time
import os

class ScreenShot(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()

        
        
        pil_image = Image.fromarray(image)
        r, g, b = pil_image.split()
        pil_image = Image.merge("RGB", (r, g, b))

        current_time = time.strftime("%Y%m%d%H%M%S") + ".png"
        debug_path = os.path.join("debug", current_time)
        pil_image.save(debug_path, 'PNG')
        return CustomAction.RunResult(success=True)
