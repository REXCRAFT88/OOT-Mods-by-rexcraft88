"""Freeze the existing Hero asset inventory used to avoid double-scaling."""
from pathlib import Path
import json
report=json.load(open('outputs/OOT-Hero-Mode-AI-v0.4/balance-report.json'))
life=set();projectiles=set()
for pack in report['packs']:
 name=pack['pack'].removesuffix('.pack.zs')
 if pack['type']=='enemy projectile':projectiles.add(name)
 for c in pack['changes']:
  if c['field']=='MaxLife':life.add((name,int(c['stock']),int(c['new'])))
assert all(len(n)<72 for n,*_ in life) and all(len(n)<72 for n in projectiles)
out=['/* Generated from the qualified 2x/ceil(1.5x) Hero asset report. */',
     'struct HeroLifeRule { char name[72]; unsigned stock, legacy; };',
     'static const struct HeroLifeRule hero_life_rules[] = {']
out += [' {'+json.dumps(n)+','+str(stock)+','+str(legacy)+'},' for n,stock,legacy in sorted(life)]
out += ['};','static const char hero_projectile_names[][72] = {']
out += [' '+json.dumps(n)+',' for n in sorted(projectiles)]
out += ['};','#define HERO_LIFE_RULES (sizeof(hero_life_rules)/sizeof(hero_life_rules[0]))',
        '#define HERO_PROJECTILES (sizeof(hero_projectile_names)/sizeof(hero_projectile_names[0]))']
(Path(__file__).resolve().parent/'combat_inventory.h').write_text('\n'.join(out)+'\n')
print(len(life),'known life rules;',len(projectiles),'legacy doubled projectile actors')
ambiguous=[(n,s,other) for n,s,old in life for n2,other,old2 in life if n==n2 and s!=other and s*2==old2]
print('ambiguous within-pack phase maxima:',ambiguous)
