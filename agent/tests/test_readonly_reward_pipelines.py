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
            assert node['on_error'] == []
            pending.extend(node.get('next',[]))
            if 'action' in node:
                if node['action']['type'] == 'Click':
                    assert key in {'PGR只读_打开任务','PGR只读_选择每日','PGR只读_每日返回主页',
                                   'PGR只读_打开战令','PGR只读_战令返回主页'}
                else:
                    assert node['action']['type'] == 'Swipe'
                    assert key.startswith('PGR只读_战令历史_')
                    assert node['action']['param'] == {'begin':[650,300],'end':[1060,300],'duration':700}
        assert len(visited) == (6 if name == '每日领奖状态查看' else 14)
        phases=[pipeline[key]['recognition']['param']['custom_recognition_param']['phase']
                for key in visited if pipeline[key].get('recognition',{}).get('type') == 'Custom']
        assert sorted(phases) == ['begin','end']


def test_battle_pass_history_is_bounded_and_requires_first_free_level_before_exit():
    pipeline=json.loads((BASE/'Readonly_Reward_Status.jsonc').read_text(encoding='utf-8'))
    pages=[key for key in pipeline if key.startswith('PGR只读_战令历史_')]
    assert len(pages)==8
    assert pipeline['PGR只读_战令状态']['next']==['PGR只读_战令历史_0']
    assert pipeline['PGR只读_战令历史_7']['next']==['PGR只读_战令首档']
    first=pipeline['PGR只读_战令首档']
    assert first['recognition']['type']=='OCR'
    assert first['recognition']['param']=={'roi':[575,220,540,47],'expected':'^1级$','threshold':0.8}
    assert first['next']==['PGR只读_战令返回主页']


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


def test_daily_fraction_and_failed_observation_do_not_inherit_home_recovery():
    import re
    pipeline=json.loads((BASE/'Readonly_Reward_Status.jsonc').read_text(encoding='utf-8'))
    defaults=json.loads((ROOT/'resource/base/default_pipeline.json').read_text(encoding='utf-8'))
    assert defaults['Default']['on_error'] == ['返回主菜单_err']
    assert all(node['on_error'] == [] for node in pipeline.values())
    param=pipeline['PGR只读_每日状态']['recognition']['param']
    assert param['threshold']==0.8
    assert param['roi']==[278,645,145,70]
    for text in ('95 /100','95/100','100 / 100','20','0'):
        assert re.fullmatch(param['expected'],text)
    for text in ('每日任务','领取','95/200','失败95',''):
        assert not re.fullmatch(param['expected'],text)
    assert pipeline['PGR只读_选择每日']['timeout']==5000
