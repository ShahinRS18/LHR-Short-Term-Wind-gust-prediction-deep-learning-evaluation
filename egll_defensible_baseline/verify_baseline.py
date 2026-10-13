"""AI-generated for student review. Executed boundary and provenance checks."""
import importlib.util,json
from pathlib import Path
from datetime import datetime,timedelta,timezone
import pandas as pd
p=Path(__file__).parent
spec=importlib.util.spec_from_file_location('baseline',p/'build_baseline.py'); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
checks=[]
def ok(name,condition):
    assert condition,name
    checks.append({'check':name,'passed':True})
def report(time,wind='24010G28KT',kind='METAR',markers='',tail='9999 SCT020 10/05 Q1010 NOSIG='):
    stamp=time.strftime('%Y%m%d%H%M'); header=time.strftime('%d%H%MZ')
    return b.parse(f'{stamp} {kind} {markers} EGLL {header} {wind} {tail}',len(checks)+1)
t=datetime(2020,1,1,tzinfo=timezone.utc)
r0=report(t); r1=report(t+timedelta(minutes=20)); rend=report(t+b.H)
ok('exact t excluded, exact t+1h included',b.origin(r0['_time'])==t-b.H and b.origin(rend['_time'])==t)
ok('00:20 belongs to future target at 00:00',b.origin(r1['_time'])==t)
ok('threshold inclusive without rounding',b.classify(t,[r1],[],[20,50])[0]=='positive')
forecast=report(t+timedelta(minutes=20),'24010KT',tail='9999 SCT020 10/05 Q1010 TEMPO 24020G40KT RMK PK WND 25050/20=')
ok('forecast and remarks are separate, not observed gust',forecast['accepted'] and forecast['gust_knots'] is None and 'G40' in forecast['trend_text'] and 'PK WND' in forecast['remarks_text'])
none20=report(t+timedelta(minutes=20),'24010KT'); none50=report(t+timedelta(minutes=50),'VRB03KT')
ok('missing numeric gust preserved while covered negative allowed',none20['gust_native'] is None and b.classify(t,[none20,none50],[],[20,50])[0]=='negative')
ok('missing routine report creates unknown',b.classify(t,[none20],[],[20,50])[0]=='unknown')
extra=report(t+timedelta(minutes=30),'24010KT',kind='SPECI')
ok('SPECI does not replace missing routine slot',b.classify(t,[none20,extra],[],[20,50])[0]=='unknown')
ok('unresolved record prevents negative',b.classify(t,[none20,none50],[{}],[20,50])[0]=='unknown')
ok('accepted positive survives coverage uncertainty',b.classify(t,[r1],[{}],[20,50],False)[0]=='positive')
ok('closed archive endpoint uncertain negative',b.classify(t,[none20,none50],[],[20,50],False)[0]=='unknown')
ok('unestablished cadence leaves nonpositive unknown',b.classify(t,[none20,none50],[],None)[0]=='unknown')
cor=report(t+timedelta(minutes=20),markers='COR',tail='AUTO 9999 SCT020 10/05 Q1010 NOSIG=')
auto=b.parse('202001010020 METAR COR EGLL 010020Z AUTO VRB10G28KT 9999 SCT020 10/05 Q1010 NOSIG=',999)
ok('COR AUTO and variable wind supported',auto['accepted'] and auto['correction'] and auto['auto'] and auto['gust_knots']==28)
mps=report(t+timedelta(minutes=20),'24010G15MPS')
kmh=report(t+timedelta(minutes=20),'24010G52KMH')
ok('MPS and KMH conversion',abs(mps['gust_mps']-15)<1e-10 and abs(kmh['gust_knots']-52/1.852)<1e-10)
suspect=report(t+timedelta(minutes=20),'24015G254KT')
ok('suspicious value retained but quarantined',not suspect['accepted'] and suspect['gust_native']==254)
malformed=report(t+timedelta(minutes=20),'24010G28T')
ok('malformed main wind quarantined',not malformed['accepted'])
original=report(t+timedelta(minutes=20),'24010G30KT'); corrected=report(t+timedelta(minutes=20),'24010KT',markers='COR')
b.versions([original,corrected])
ok('unique correction supersedes original retrospective report',corrected['accepted'] and not original['accepted'])
c1=report(t+timedelta(minutes=20),'24010KT',markers='COR'); c2=report(t+timedelta(minutes=20),'24010G30KT',markers='COR')
b.versions([c1,c2]); ok('conflicting corrections quarantined',not c1['accepted'] and not c2['accepted'])
d1=report(t+timedelta(minutes=20)); d2=dict(d1); d2['source_id']='duplicate'; b.versions([d1,d2])
ok('identical duplicate retained but not counted twice',d1['accepted'] and not d2['accepted'] and d2['version_status']=='identical_duplicate')
for date in [datetime(2019,12,31,23,50,tzinfo=timezone.utc),datetime(2020,2,29,23,50,tzinfo=timezone.utc),datetime(2020,3,1,tzinfo=timezone.utc)]:
    ok('month/year/leap boundary '+date.isoformat(),b.header_date(date,date.strftime('%d%H%M'))==date)
keys=pd.read_csv(p/'weather_feature_keys.csv'); targets=pd.read_csv(p/'hourly_gust_targets.csv',low_memory=False)
keys['origin_utc']=pd.to_datetime(keys.origin_utc,utc=True); targets['origin_utc']=pd.to_datetime(targets.origin_utc,utc=True)
joined=keys.sample(frac=1,random_state=42).merge(targets[['station','origin_utc','target_state']],on=['station','origin_utc'],validate='one_to_one',how='outer',indicator=True)
ok('shuffled source rows retain full keyed alignment',len(joined)==len(targets) and joined._merge.eq('both').all())
missing=keys.drop(index=[100]).merge(targets[['station','origin_utc']],on=['station','origin_utc'],validate='one_to_one',how='outer',indicator=True)
ok('missing row is detected, never truncated',missing._merge.eq('right_only').sum()==1)
duplicate=pd.concat([keys.iloc[:3],keys.iloc[[0]]])
try:
    duplicate.merge(targets[['station','origin_utc']],on=['station','origin_utc'],validate='one_to_one')
except pd.errors.MergeError: caught=True
else: caught=False
ok('duplicate source key fails cardinality validation',caught)
pred=pd.read_csv(p/'metar_predictor_candidates.csv'); origins=pd.to_datetime(pred.origin_utc,utc=True); observed=pd.to_datetime(pred.observation_time_utc,utc=True)
ok('actual predictors never exceed origin',((observed<=origins)|observed.isna()).all())
ok('actual predictor age is within declared tolerance',pred.report_age_minutes.dropna().between(0,60).all())
ok('future target and coverage fields excluded from predictor table',not any(c in pred for c in ['target_y','target_state','max_accepted_reported_gust_knots','coverage_status','cb_observed','tcu_observed']))
ok('actual unknown targets have no binary label',targets.loc[targets.target_state=='unknown','target_y'].isna().all())
ok('actual negative windows meet two-slot coverage and have no unresolved records',targets.loc[targets.target_state=='negative','coverage_status'].eq('both_verified_routine_slots_valid').all() and targets.loc[targets.target_state=='negative','unresolved_record_count'].eq(0).all())
# Independently reparse actual main wind and count threshold reports for a
# cross-check against the production summary, excluding malformed headers.
raw=(b.ROOT/'metar_raw/EGLL_complete.txt').read_text().splitlines()
production=json.loads((p/'execution_summary.json').read_text())
count=0; gust_count=0
for line in raw:
    m=__import__('re').match(r'^\d{12}\s+METAR(?:\s+COR)?\s+EGLL\s+\d{6}Z\s+(?:AUTO\s+)?(?:COR\s+)?(?:\d{3}|VRB)\d{2,3}G(\d{2,3})KT(?=\s|=|$)',line)
    if m:
        gust_count+=1; count+=int(m[1])>=28
ok('independent raw main-gust count',gust_count==production['accepted_gust_report_rows'])
ok('independent raw threshold-report count',count==production['accepted_exceedance_report_rows'])
manifest=pd.read_csv(p/'source_manifest.csv')
ok('source manifest hashes unchanged',all(__import__('hashlib').sha256(Path(r.source_file).read_bytes()).hexdigest()==r.sha256 for r in manifest.itertuples()))
ok('all states reconcile to full study grid',sum(production['target_states'].values())==175320)
positive_times=[]
for line in raw:
    m=__import__('re').match(r'^(\d{12})\s+METAR(?:\s+COR)?\s+EGLL\s+\d{6}Z\s+(?:AUTO\s+)?(?:COR\s+)?(?:\d{3}|VRB)\d{2,3}G(\d{2,3})KT(?=\s|=|$)',line)
    if m and int(m[2])>=28: positive_times.append(m[1])
expected_origins=set(pd.to_datetime(pd.Series(positive_times),format='%Y%m%d%H%M',utc=True).dt.ceil('h')-pd.Timedelta(hours=1))
actual_origins=set(targets.loc[targets.target_state=='positive','origin_utc'])
ok('independent positive hourly origins with closed-right windows',expected_origins==actual_origins)
(p/'verification_results.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Passed',len(checks),'checks')


