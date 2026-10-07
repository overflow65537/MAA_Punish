import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'resource/base/pipeline'


def test_readonly_tasks_are_imported_by_the_official_interface():
    interface=json.loads((ROOT/'interface.json').read_text(encoding='utf-8'))
    for name in ('每日领奖状态查看','战令领奖状态查看'):
        assert f'./tasks/{name}.json' in interface['import']
        task=json.loads((ROOT/'tasks'/f'{name}.json').read_text(encoding='utf-8'))['task'][0]
        assert set(task['group']) <= {group['name'] for group in interface['group']}


def test_readonly_entries_default_off_and_never_enter_original_claim_branches():
    pipeline=json.loads((BASE/'Readonly_Reward_Status.jsonc').read_text(encoding='utf-8'))
    for name in ('每日领奖状态查看','战令领奖状态查看'):
        task=json.loads((ROOT/'tasks'/f'{name}.json').read_text(encoding='utf-8'))['task'][0]
        assert task['default_check'] is False
        pending=[task['entry']]; visited=set()
        while pending:
            key=pending.pop()
            if key in visited: continue
            visited.add(key)
            node=pipeline[key]
            assert 'on_error' not in node
            pending.extend(node.get('next',[]))
            if 'action' in node:
                assert node['action']['type'] == 'Click'
                assert key in {'PGR只读_打开任务','PGR只读_选择每日','PGR只读_每日返回主页',
                               'PGR只读_打开战令','PGR只读_战令返回主页'}
        assert len(visited) == (6 if name == '每日领奖状态查看' else 5)
        phases=[pipeline[key]['recognition']['param']['custom_recognition_param']['phase']
                for key in visited if pipeline[key].get('recognition',{}).get('type') == 'Custom']
        assert sorted(phases) == ['begin','end']


def test_navigation_uses_the_exact_official_recognition_and_action():
    pipeline=json.loads((BASE/'Readonly_Reward_Status.jsonc').read_text(encoding='utf-8'))
    for added,filename,original in (
        ('PGR只读_打开任务','Collect_Quest.jsonc','打开任务'),
        ('PGR只读_选择每日','Collect_Quest.jsonc','每日任务'),
        ('PGR只读_每日返回主页','General.jsonc','返回主菜单'),
        ('PGR只读_打开战令','Battle_Pass.jsonc','打开通行证'),
        ('PGR只读_战令返回主页','General.jsonc','返回主菜单'),
    ):
        source=json.loads((BASE/filename).read_text(encoding='utf-8'))[original]
        assert pipeline[added]['recognition'] == source['recognition']
        assert pipeline[added]['action'] == source['action']
