"""Observe current-client identity on supplied recognizer frames, without input.

This optional read-only task binds its opening home page to its closing home
page. It does not identify a configured named account or assert any claim.
"""
import json
import math
import re

from maa.custom_recognition import CustomRecognition


class ReadonlyCurrentAccount(CustomRecognition):
    def __init__(self):
        super().__init__()
        self._opening_uids = {}

    def analyze(self, context, argv):
        failed = CustomRecognition.AnalyzeResult(box=None, detail={'mode':'current_client_observation',
            'accountIdentityConfirmed':False, 'reason':'current_client_identity_unavailable'})
        try:
            params=json.loads(argv.custom_recognition_param)
            phase=params['phase']
            task_id=argv.task_detail.task_id
            if set(params) != {'phase'} or phase not in ('begin','end') or type(task_id) is not int or task_id <= 0:
                return failed
            if argv.image.shape != (720,1280,3):
                return failed
            home=context.run_recognition('主界面_战斗节点',argv.image)
            if home is None or home.hit is not True:
                return failed
            result=context.run_recognition('PGR只读_UID文字',argv.image)
            hits=result.filtered_results if result is not None and result.hit is True else []
            if len(hits) != 1:
                return failed
            hit=hits[0]
            text=re.sub(r'\s+','',hit.text)
            match=re.fullmatch(r'ID[:：]?([1-9][0-9]{6,9})',text)
            if match is None or not math.isfinite(hit.score) or not .8 <= hit.score <= 1:
                return failed
            box=list(hit.box)
            if len(box) != 4 or any(type(value) is not int for value in box):
                return failed
            x,y,w,h=box
            if not (125 <= x < x+w <= 285 and 78 <= y < y+h <= 121):
                return failed
            uid=match.group(1)
            if phase == 'begin':
                if task_id in self._opening_uids and self._opening_uids[task_id] != uid:
                    self._opening_uids.pop(task_id,None)
                    return failed
                if len(self._opening_uids) >= 128 and task_id not in self._opening_uids:
                    return failed
                self._opening_uids[task_id]=uid
            elif self._opening_uids.pop(task_id,None) != uid:
                return failed
            return CustomRecognition.AnalyzeResult(box=box, detail={
                'mode':'current_client_observation','phase':phase,'observedUid':uid,
                'accountIdentityConfirmed':phase == 'end','observationOnly':True,
                'taskId':task_id,'uidBox':box,'uidConfidence':hit.score,
                'uidRecognitionId':getattr(result,'reco_id',None)})
        except (ValueError,KeyError,TypeError,AttributeError):
            return failed
