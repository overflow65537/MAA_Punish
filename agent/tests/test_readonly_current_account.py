from types import SimpleNamespace
import json
import numpy as np

from recognition.exclusives.ReadonlyCurrentAccount import ReadonlyCurrentAccount


class Context:
    def __init__(self, *, uid='ID: 12345678', score=.99, home=True):
        self.uid, self.score, self.home = uid, score, home
        self.calls = []

    def run_recognition(self, node, image, pipeline_override=None):
        self.calls.append(node)
        if node == '主界面_战斗节点':
            return SimpleNamespace(hit=self.home)
        hit = SimpleNamespace(text=self.uid, score=self.score, box=[130, 80, 140, 32])
        return SimpleNamespace(hit=True, filtered_results=[hit])


def args(mode, task_id=1):
    return SimpleNamespace(task_detail=SimpleNamespace(task_id=task_id),
        custom_recognition_param=json.dumps({'phase':mode}), image=np.zeros((720,1280,3),dtype=np.uint8))


def test_begin_end_requires_same_observed_native_uid_and_task():
    reader = ReadonlyCurrentAccount()
    assert reader.analyze(Context(), args('begin')).box is not None
    assert reader.analyze(Context(), args('end',task_id=2)).box is None
    assert reader.analyze(Context(uid='ID: 87654321'),args('end')).box is None
    assert reader.analyze(Context(),args('end')).box is None
    assert reader.analyze(Context(),args('begin')).box is not None
    result = reader.analyze(Context(),args('end'))
    assert result.box is not None and result.detail['accountIdentityConfirmed'] is True
    assert reader.analyze(Context(),args('end')).box is None


def test_wrong_screen_ambiguous_or_low_confidence_uid_does_not_bind():
    for context in (Context(home=False), Context(uid='unknown'),Context(score=.79),Context(uid='ID: 01234567')):
        reader = ReadonlyCurrentAccount()
        assert reader.analyze(context,args('begin')).box is None
        assert reader.analyze(Context(),args('end')).box is None
    class Ambiguous(Context):
        def run_recognition(self,*values,**kwargs):
            output=super().run_recognition(*values,**kwargs)
            if hasattr(output,'filtered_results'): output.filtered_results *= 2
            return output
    assert ReadonlyCurrentAccount().analyze(Ambiguous(),args('begin')).box is None


def test_readonly_recognition_uses_the_supplied_image_and_never_input():
    context = Context()
    output=ReadonlyCurrentAccount().analyze(context,args('begin'))
    assert output.box is not None
    assert context.calls == ['主界面_战斗节点','PGR只读_UID文字']
    assert output.detail['accountIdentityConfirmed'] is False
    assert output.detail['mode'] == 'current_client_observation'
