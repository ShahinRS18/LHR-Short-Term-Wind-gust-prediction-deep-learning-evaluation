"""AI-generated for student review. Conservative retrospective EGLL baseline.
Source files are read-only. No models, imputation or feature selection.
"""
import sys, re, json, calendar, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
sys.path.insert(0,r'D:\Dissertation_ConvectiveEvents\LHR_Dissertation\tools\python_packages')
import pandas as pd
import numpy as np
from netCDF4 import Dataset, num2date
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
UTC=timezone.utc
START=datetime(2005,1,1,tzinfo=UTC); END=datetime(2025,1,1,tzinfo=UTC)
H=timedelta(hours=1); KT_MS=1852/3600
HEADER=re.compile(r'^(?:(METAR|SPECI)\s+)?(?:(COR)\s+)?([A-Z]{4})\s+(\d{6})Z(?:\s+|$)(.*)$')
WIND=re.compile(r'^(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(KT|MPS|KMH)$')
def iso(t): return t.isoformat().replace('+00:00','Z') if t is not None else ''
def origin(s):
    t=s.replace(minute=0,second=0,microsecond=0)
    return t-H if t==s else t

def header_date(p,code):
    dates=[]
    for off in [-1,0,1]:
        y,m=divmod(p.year*12+p.month-1+off,12)
        try: dates.append(datetime(y,m+1,int(code[:2]),int(code[2:4]),int(code[4:6]),tzinfo=UTC))
        except ValueError: pass
    return min(dates,key=lambda d:abs(d-p)) if dates else None

def parse(line,i,source='synthetic'):
    r=dict(source_id=f'EGLL:{i}',source_file=str(source),source_line=i,raw_report=line.strip(),
        station='',report_type='',auto=False,correction=False,archive_time_utc='',header_day_time='',
        header_candidate_time_utc='',observation_time_utc='',timestamp_status='unresolved',
        parser_status='unparsed',main_wind_group='',wind_unit='',mean_wind_native=None,
        gust_native=None,mean_wind_knots=None,gust_knots=None,gust_mps=None,gust_reported=False,
        cb_observed=None,tcu_observed=None,trend_text='',remarks_text='',accepted=False,
        version_status='not_selected',exclusion_reason='',availability_status='receipt_revision_times_absent',
        _time=None,_prefix=None,_candidate=None,_possible=[])
    m=re.match(r'^(\d{12})\s+(.*)$',r['raw_report'])
    if not m: r['exclusion_reason']='missing_archive_timestamp'; return r
    try: p=datetime.strptime(m[1],'%Y%m%d%H%M').replace(tzinfo=UTC)
    except ValueError: r['exclusion_reason']='invalid_archive_timestamp'; return r
    r['_prefix']=p; r['archive_time_utc']=iso(p); r['_possible']=[p]
    h=HEADER.fullmatch(m[2].rstrip('=').strip())
    if not h:
        partial=re.search(r'\b(\d{6})Z',m[2])
        if partial:
            c=header_date(p,partial[1]); r['_candidate']=c
            r['header_day_time']=partial[1]; r['header_candidate_time_utc']=iso(c)
            if c and c not in r['_possible']: r['_possible'].append(c)
        r['parser_status']='malformed_header'; r['exclusion_reason']='malformed_header'; return r
    r['station']=h[3]; r['report_type']=h[1] or 'unspecified'; r['correction']=bool(h[2]); r['header_day_time']=h[4]
    c=header_date(p,h[4]); r['_candidate']=c; r['header_candidate_time_utc']=iso(c)
    if c and c not in r['_possible']: r['_possible'].append(c)
    if c==p:
        r['_time']=c; r['observation_time_utc']=iso(c); r['timestamp_status']='prefix_header_agree'
    else: r['timestamp_status']='prefix_header_disagree' if c else 'invalid_header_time'
    remarks=re.split(r'\bRMK\b',h[5],maxsplit=1)
    r['remarks_text']=remarks[1].strip() if len(remarks)>1 else ''
    trend=re.search(r'\b(?:TEMPO|BECMG|NOSIG)\b',remarks[0])
    observed=remarks[0][:trend.start()] if trend else remarks[0]
    r['trend_text']=remarks[0][trend.start():].strip() if trend else ''
    tokens=observed.split()
    while tokens and tokens[0] in ['AUTO','COR']:
        marker=tokens.pop(0); r['auto']|=marker=='AUTO'; r['correction']|=marker=='COR'
    r['cb_observed']=bool(re.search(r'(?:FEW|SCT|BKN|OVC)(?:\d{3}|///)CB\b',observed))
    r['tcu_observed']=bool(re.search(r'(?:FEW|SCT|BKN|OVC)(?:\d{3}|///)TCU\b|/{3,}TCU\b',observed))
    r['main_wind_group']=tokens[0] if tokens else ''
    w=WIND.fullmatch(r['main_wind_group']); reasons=[]
    if r['station']!='EGLL': reasons.append('wrong_station')
    if r['report_type'] not in ['METAR','SPECI']: reasons.append('unestablished_report_type')
    if r['_time'] is None: reasons.append(r['timestamp_status'])
    if not w:
        r['parser_status']='missing_or_malformed_wind'; reasons.append('missing_or_malformed_wind')
    else:
        direction,mean,gust,unit=w.groups(); mean=int(mean); gust=int(gust) if gust is not None else None
        factor={'KT':1.0,'MPS':1/KT_MS,'KMH':1/1.852}[unit]
        r.update(wind_unit=unit,mean_wind_native=mean,gust_native=gust,mean_wind_knots=mean*factor,
            gust_knots=gust*factor if gust is not None else None,gust_mps=gust*factor*KT_MS if gust is not None else None,
            gust_reported=gust is not None,parser_status='valid_main_wind_with_gust' if gust is not None else 'valid_wind_no_gust_reported')
        if direction!='VRB' and int(direction)>360: reasons.append('invalid_direction')
        if gust is not None and gust<mean: reasons.append('gust_below_mean_review')
        # Provisional review screen, NOT a physical ceiling; no capping/repair.
        if mean*factor>80 or (gust is not None and gust*factor>80): reasons.append('speed_above_provisional_80kt_review_screen')
    r['exclusion_reason']=';'.join(reasons); r['accepted']=not reasons
    return r

def versions(records):
    groups=defaultdict(list)
    for r in records:
        if r['_time'] is not None: groups[r['_time']].append(r)
    for group in groups.values():
        unique={}
        for r in group:
            text=' '.join(r['raw_report'].split())
            if text in unique:
                r['accepted']=False; r['version_status']='identical_duplicate'; r['duplicate_of']=unique[text]['source_id']
            else: unique[text]=r
        rows=list(unique.values()); cor=[r for r in rows if r['correction']]; preferred=cor or rows
        if len(preferred)==1:
            chosen=preferred[0]; chosen['version_status']='selected_correction' if cor else 'selected_only_version'
            for r in rows:
                if r is not chosen:
                    r['accepted']=False; r['version_status']='superseded_by_correction'; r['superseded_by']=chosen['source_id']
        else:
            for r in rows:
                r['accepted']=False; r['version_status']='unresolved_version_conflict'
                r['exclusion_reason']=';'.join(filter(None,[r['exclusion_reason'],'unresolved_version_conflict']))

def classify(t,reports,unresolved,slots,boundary_ok=True):
    assert all(t<r['_time']<=t+H for r in reports)
    seen={r['_time'].minute for r in reports if r['report_type']=='METAR'}
    covered=slots is not None and all(s in seen for s in slots)
    if any(r['gust_knots'] is not None and r['gust_knots']>=28 for r in reports): return 'positive',covered,''
    reason=[]
    if slots is None: reason.append('unestablished_routine_cadence')
    elif not covered: reason.append('missing_or_invalid_routine_slot')
    if unresolved: reason.append('unresolved_record_may_affect_target')
    if not boundary_ok: reason.append('archive_closed_endpoint_not_covered')
    return ('unknown',covered,';'.join(reason)) if reason else ('negative',True,'')

def table(name,rows,gzip=False):
    df=pd.DataFrame(rows)
    df.to_csv(OUT/(name+('.csv.gz' if gzip else '.csv')),index=False,
        compression={'method':'gzip','compresslevel':3,'mtime':0} if gzip else None)
    return df

def run():
    source=ROOT/'metar_raw/EGLL_complete.txt'
    lines=source.read_text(encoding='utf-8').splitlines()
    print('Parsing',len(lines),'EGLL records',flush=True)
    reports=[parse(line,i,source) for i,line in enumerate(lines,1)]; versions(reports)
    public=[]
    for r in reports:
        d={k:v for k,v in r.items() if not k.startswith('_')}
        d['possible_times_utc']=';'.join(iso(t) for t in r['_possible']); public.append(d)
    table('report_extraction_quality',public,True)
    monthcounts=defaultdict(Counter)
    for r in reports:
        if r['_time'] and r['report_type']=='METAR' and r['version_status'] not in ['identical_duplicate','superseded_by_correction']:
            monthcounts[r['_time'].strftime('%Y-%m')][r['_time'].minute]+=1
    cadence=[]; slotmap={}
    for month,c in sorted(monthcounts.items()):
        top=c.most_common(2); slots=sorted(m for m,n in top); hours=calendar.monthrange(int(month[:4]),int(month[5:]))[1]*24
        share=sum(n for m,n in top)/sum(c.values())
        established=len(slots)==2 and share>=.98 and all(c[s]/hours>=.90 for s in slots)
        slotmap[month]=slots if established else None
        cadence.append(dict(month=month,expected_routine_minutes=';'.join(map(str,slots)),cadence_established=established,
            modal_two_slot_share=share,slot_counts=json.dumps(dict(sorted(c.items()))),monthly_report_count=sum(c.values())))
    table('monthly_reporting_cadence',cadence)
    accepted=[r for r in reports if r['accepted']]; byorigin=defaultdict(list); affected=defaultdict(list); ledger=[]
    for r in reports:
        if r['accepted']: byorigin[origin(r['_time'])].append(r)
        elif r['version_status'] not in ['identical_duplicate','superseded_by_correction']:
            possible=sorted({origin(s) for s in r['_possible']})
            for t in possible:
                if START<=t<END: affected[t].append(r)
            ledger.append(dict(source_id=r['source_id'],source_line=r['source_line'],raw_report=r['raw_report'],
                archive_time_utc=r['archive_time_utc'],header_candidate_time_utc=r['header_candidate_time_utc'],
                reason=r['exclusion_reason'],possible_target_origins_utc=';'.join(iso(t) for t in possible),
                disposition='quarantined_unresolved',adjacent_records=json.dumps(lines[max(0,r['source_line']-3):r['source_line']+2]),
                archive_provenance='README says NOAA; no source download or receipt manifest'))
    table('unresolved_case_ledger',ledger)
    origins=pd.DataFrame({'station':'EGLL','origin_utc':pd.date_range(START,END,freq='h',inclusive='left')})
    maxarchive=max(r['_prefix'] for r in reports if r['_prefix']); targets=[]
    for t in origins.origin_utc:
        t=t.to_pydatetime(); rows=sorted(byorigin[t],key=lambda r:r['_time']); unresolved=affected[t]; slots=slotmap.get(t.strftime('%Y-%m'))
        boundary_ok=t+H<END or maxarchive>=t+H
        state,coverage,reason=classify(t,rows,unresolved,slots,boundary_ok)
        gusts=[r for r in rows if r['gust_knots'] is not None]; maximum=max(gusts,key=lambda r:r['gust_knots']) if gusts else None
        targets.append(dict(station='EGLL',origin_utc=iso(t),window_start_exclusive_utc=iso(t),window_end_inclusive_utc=iso(t+H),
            target_state=state,target_y=1 if state=='positive' else 0 if state=='negative' else None,
            coverage_status='both_verified_routine_slots_valid' if coverage else 'inadequate_or_unestablished_routine_coverage',
            expected_routine_minutes=';'.join(map(str,slots)) if slots else '',accepted_report_count=len(rows),
            accepted_metar_count=sum(r['report_type']=='METAR' for r in rows),accepted_speci_count=sum(r['report_type']=='SPECI' for r in rows),
            gust_report_count=len(gusts),exceedance_report_count=sum(r['gust_knots']>=28 for r in gusts),
            max_accepted_reported_gust_knots=maximum['gust_knots'] if maximum else None,
            max_accepted_reported_gust_mps=maximum['gust_mps'] if maximum else None,
            max_gust_observation_time_utc=iso(maximum['_time']) if maximum else '',max_gust_source_id=maximum['source_id'] if maximum else '',
            accepted_source_ids=';'.join(r['source_id'] for r in rows),excluded_possible_source_ids=';'.join(r['source_id'] for r in unresolved),
            unresolved_record_count=len(unresolved),eligibility_reason=reason,
            excluded_record_reasons=';'.join(sorted({r['exclusion_reason'] for r in unresolved})),archive_boundary_coverage=boundary_ok))
    targetdf=table('hourly_gust_targets',targets)
    unknown=targetdf[targetdf.target_state=='unknown']; unknown.to_csv(OUT/'unknown_hourly_windows.csv',index=False)
    targetdf.assign(year=pd.to_datetime(targetdf.origin_utc).dt.year).groupby(['year','target_state']).size().unstack(fill_value=0).to_csv(OUT/'yearly_target_counts.csv')
    # Candidate predictors only: no demonstrated receipt/revision availability.
    cols=['observation_time_utc','source_id','correction','auto','mean_wind_knots','gust_knots','gust_mps','cb_observed','tcu_observed']
    candidates=pd.DataFrame([{k:r[k] for k in cols} for r in accepted])
    candidates['observation_time_utc']=pd.to_datetime(candidates.observation_time_utc,utc=True)
    pred=pd.merge_asof(origins,candidates.sort_values('observation_time_utc'),left_on='origin_utc',right_on='observation_time_utc',
        direction='backward',tolerance=pd.Timedelta(minutes=60))
    pred['report_age_minutes']=(pred.origin_utc-pred.observation_time_utc).dt.total_seconds()/60
    pred['availability_status']=np.where(pred.observation_time_utc.isna(),'no_recent_candidate','receipt_revision_availability_unverified')
    pred['freshness_status']=np.where(pred.observation_time_utc.isna(),'no_valid_report_within_provisional_60_minutes','within_provisional_60_minutes')
    pred['operationally_verified']=False; pred['unresolved_recent_record']=False
    for r in reports:
        if r['accepted'] or r['version_status'] in ['identical_duplicate','superseded_by_correction']: continue
        for s in r['_possible']:
            first=s.replace(minute=0,second=0,microsecond=0)
            if first<s: first+=H
            for t in [first,first+H]:
                if START<=t<END and timedelta(0)<=t-s<=H: pred.loc[pred.origin_utc==t,'unresolved_recent_record']=True
    assert ((pred.observation_time_utc<=pred.origin_utc)|pred.observation_time_utc.isna()).all()
    assert pred.report_age_minutes.dropna().between(0,60).all()
    pred[['station','origin_utc','observation_time_utc','source_id','cb_observed','tcu_observed']].to_csv(OUT/'cloud_indicator_candidates.csv',index=False)
    pred=pred.drop(columns=['cb_observed','tcu_observed'])
    pred.to_csv(OUT/'metar_predictor_candidates.csv',index=False)
    alignment=[]; keys=[]; manifest=[]
    for year in range(2005,2025):
        print('Cross-checking source times',year,flush=True)
        file=ROOT/'LHR/sounding_results'/f'sounding_compute_{year}_LHR_all.csv'
        df=pd.read_csv(file,usecols=['timestamp','filename'])
        recovered=pd.to_datetime(df.filename.str.extract(r'LHR_(\d{4}-\d{2}-\d{2}_\d{6})\.nc$',expand=False),format='%Y-%m-%d_%H%M%S',utc=True,errors='raise')
        assert recovered.notna().all() and not recovered.duplicated().any()
        expected=pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='h',inclusive='left',tz='UTC')
        for variable in ['temperature','relative_humidity','u_component_of_wind','v_component_of_wind']:
            ncfile=ROOT/'LHR'/variable/f'{year}_{variable}.nc'
            with Dataset(ncfile) as nc:
                tv=nc.variables['time']; units=tv.units; cal=getattr(tv,'calendar','standard')
                decoded=num2date(tv[:],units,calendar=cal,only_use_cftime_datetimes=False,only_use_python_datetimes=True)
                times=pd.DatetimeIndex(pd.to_datetime(list(decoded),utc=True))
            assert not times.duplicated().any()
            row=dict(year=year,variable=variable,source_file=str(ncfile),time_units=units,calendar=cal,
                missing_expected=len(expected.difference(times)),extra_hours=len(times.difference(expected)),
                sounding_unmatched=len(set(recovered)-set(times)),netcdf_unmatched=len(set(times)-set(recovered)),ordered=times.is_monotonic_increasing,
                old_numeric_timestamp_unique=int(df.timestamp.nunique()),old_numeric_timestamp_values=';'.join(map(str,df.timestamp.unique())))
            assert not any(row[k] for k in ['missing_expected','extra_hours','sounding_unmatched','netcdf_unmatched'])
            alignment.append(row)
            manifest.append(dict(source_file=str(ncfile),bytes=ncfile.stat().st_size,sha256=hashlib.sha256(ncfile.read_bytes()).hexdigest()))
        for rownum,(time,name) in enumerate(zip(recovered,df.filename),2):
            keys.append(dict(station='EGLL',origin_utc=time,sounding_validity_time_utc=time,source_sounding_file=str(file),
                source_sounding_csv_row=rownum,source_sounding_filename=name,weather_availability_status='retrospective_reanalysis_unavailable_at_origin'))
        manifest.append(dict(source_file=str(file),bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    table('netcdf_sounding_alignment',alignment)
    keydf=origins.merge(pd.DataFrame(keys),on=['station','origin_utc'],how='outer',validate='one_to_one',indicator=True)
    assert (keydf._merge=='both').all(); keydf=keydf.drop(columns='_merge')
    keydf.to_csv(OUT/'weather_feature_keys.csv',index=False)
    # Minimal seasonal key exports reference the unchanged annual feature values.
    for season,months in [('hot',[4,5,6,7,8,9]),('cold',[10,11,12,1,2,3])]:
        keydf[keydf.origin_utc.dt.month.isin(months)].to_csv(OUT/f'weather_feature_keys_{season}.csv',index=False)
    join=keydf.merge(targetdf.assign(origin_utc=pd.to_datetime(targetdf.origin_utc,utc=True)),on=['station','origin_utc'],how='outer',validate='one_to_one',indicator=True)
    assert (join._merge=='both').all()
    for file in [source,ROOT/'audit/gust_timestamp_audit.md']:
        manifest.append(dict(source_file=str(file),bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    table('source_manifest',manifest)
    summary=dict(raw_report_rows=len(reports),accepted_retrospective_report_rows=len(accepted),
        excluded_report_rows=sum(not r['accepted'] for r in reports),unresolved_report_rows=len(ledger),
        identical_duplicate_rows=sum(r['version_status']=='identical_duplicate' for r in reports),
        superseded_report_rows=sum(r['version_status']=='superseded_by_correction' for r in reports),
        correction_marked_rows=sum(r['correction'] for r in reports),
        accepted_gust_report_rows=sum(r['gust_reported'] for r in accepted),
        accepted_exceedance_report_rows=sum(r['gust_knots'] is not None and r['gust_knots']>=28 for r in accepted),
        suspicious_speed_rows=sum('review' in r['exclusion_reason'] for r in reports),
        hourly_origins=len(targetdf),target_states=targetdf.target_state.value_counts().to_dict(),
        unknown_reason_counts=unknown.eligibility_reason.value_counts().to_dict(),
        verified_months=sum(r['cadence_established'] for r in cadence),netcdf_files_rechecked=len(alignment),sounding_keys=len(keydf),
        predictor_rows_without_recent_candidate=int(pred.observation_time_utc.isna().sum()),
        predictor_rows_with_unresolved_recent_record=int(pred.unresolved_recent_record.sum()),
        last_archive_time_utc=iso(maxarchive),independent_event_count=None,
        independent_event_count_status='not defined: hourly positives are not independent events')
    (OUT/'execution_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__': run()

