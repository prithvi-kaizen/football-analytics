"""Run from this project directory: streamlit run app.py."""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from tacticai_lite.analysis import SPATIAL, summary
from tacticai_lite.models import cluster_corners, nearest_corners, usable_frames
from tacticai_lite.viz import pitch_figure, rate_plot

ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.environ.get('TACTICAI_OUTPUT', str(ROOT/'outputs')))
st.set_page_config(page_title='TacticAI Lite | Corner analysis', layout='wide')
st.markdown('''<style>
.block-container {max-width: 1440px; padding-top: 2rem;}
h1 {font-size: 2.3rem !important; letter-spacing: -.025em;}
:focus-visible {outline: 3px solid #176044 !important; outline-offset: 3px !important;}
button, input, [role="combobox"] {min-height: 44px;}
[data-rac][role="group"]:has(input[role="combobox"]), .stTextInput input {border: 1px solid #67736C !important;}
@media (max-width: 700px) {.block-container {padding-left: 1rem; padding-right: 1rem;}}
</style>''', unsafe_allow_html=True)
st.title('TacticAI Lite')
st.caption('Corner-kick evidence from public StatsBomb events and partial 360 snapshots. Research inspired by TacticAI.')


@st.cache_data(show_spinner=False)
def load_data(directory, signature):
    path = Path(directory)
    corners = pd.read_csv(path/'corners.csv')
    for col in ['has_360','goal','shot_created']:
        if col == 'shot_created':
            corners[col] = corners[col].map({True:True,False:False,'True':True,'False':False})
        else:
            corners[col] = corners[col].map({True:True,False:False,'True':True,'False':False}).fillna(False).astype(bool)
    if corners.empty or corners.corner_id.duplicated().any():
        raise ValueError('Corner table is empty or has duplicate IDs')
    detail = json.loads((path/'details.json').read_text())
    if set(corners.corner_id) != set(detail):
        raise ValueError('Corner table and detail records disagree; rebuild outputs together')
    return corners, detail, json.loads((path/'manifest.json').read_text()), json.loads((path/'model.json').read_text())


files = [OUTPUT/name for name in ['corners.csv','details.json','manifest.json','model.json']]
if not all(p.exists() for p in files):
    st.info('No processed dataset yet. Run the sample pipeline from the project directory, then reload this page.')
    st.code('python -m tacticai_lite --sample 1')
    st.stop()
try:
    with st.spinner('Loading verified corner records and their linked frames…'):
        corners, details, info, model = load_data(str(OUTPUT), tuple(p.stat().st_mtime_ns for p in files))
except (OSError,ValueError,KeyError,pd.errors.ParserError) as exc:
    st.error(f'Could not load the processed dataset: {exc}. Rerun python -m tacticai_lite --offline to rebuild it.')
    st.stop()

st.caption(f"{len(info['matches'])} matches · {len(corners)} corners · {info['horizon_seconds']:g}-second window · "
           f"{info['corners_with_360']}/{len(corners)} corners with a linked frame")
with st.expander('Outcome definition and data limits'):
    st.write(f"A positive outcome is at least one shot by the corner-taking team within {info['horizon_seconds']:g} seconds of the kick, "
             'in the same period and possession, before a restart or stoppage. The time boundary is inclusive. '
             'Early recording ends with no known terminal event remain unknown and are excluded from rates.')
    st.write(f"Short means a recorded pass length of at most {info['short_threshold_units']:g} StatsBomb units (or endpoint distance if length is absent). "
             'Swing uses the recorded technique. Both describe the observed delivery, not a pre-kick prediction.')
    st.write('All visible-player measures are partial. The shaded polygon marks camera coverage. Width is reflected so every corner comes from the top. '
             'The dotted straight line connects recorded pass endpoints; it is not ball flight. Counts exclude the attacking keeper and taker; defenders include the keeper. '
             'Near and far zones mean y<36 and y>44 within the standardized penalty area (x≥102, 18≤y≤62). '
             'Density counts defenders inside both the box and camera polygon per 100 visible square coordinate units; unknown visibility stays missing.')
    st.write('A usable configuration has at least four valid visible players, including one attacking outfielder other than the taker and one defender. '
             'Direct corner shots are retained for inspection but excluded from delivery comparisons and the classifier: they create a shot by definition.')
    st.write('Rates show 95% Wilson intervals as descriptive per-corner uncertainty. They do not account for within-match dependence or establish tactical superiority. '
             'No continuous tracking, marking assignments or causal recommendations are inferred.')

controls = st.columns([1.2,1.2,1])
with controls[0]:
    tournaments = st.multiselect('Tournament', sorted(corners.tournament.unique()),default=sorted(corners.tournament.unique()))
with controls[1]:
    deliveries = st.multiselect('Delivery',sorted(corners.delivery.unique()),default=sorted(corners.delivery.unique()))
with controls[2]:
    search = st.text_input('Search team, taker or match',placeholder='Type a team or player')
extra = st.columns([1,1,1])
with extra[0]:
    cluster = st.selectbox('Configuration cluster',['All',*sorted(corners.cluster.unique())])
with extra[1]:
    outcome = st.selectbox('Observed outcome (inspection only)',['All','Shot created','No shot','Unknown'])
with extra[2]:
    frames_only = st.checkbox('Only corners with a usable frame',value=False)

filtered = corners[corners.tournament.isin(tournaments) & corners.delivery.isin(deliveries)].copy()
if search.strip():
    filtered = filtered[filtered[['team','taker','match']].fillna('').apply(lambda col: col.str.contains(search.strip(),case=False,regex=False)).any(axis=1)]
if cluster != 'All': filtered = filtered[filtered.cluster==cluster]
if frames_only: filtered = filtered[usable_frames(filtered)]
comparison_population = filtered.copy()
if outcome == 'Shot created': filtered = filtered[filtered.shot_created.eq(True)]
if outcome == 'No shot': filtered = filtered[filtered.shot_created.eq(False)]
if outcome == 'Unknown': filtered = filtered[filtered.shot_created.isna()]
if filtered.empty:
    st.info('No corners match these filters. Clear the search, select a tournament and delivery, or choose All outcomes.')
    st.stop()

observed = filtered[filtered.shot_created.notna()]
st.write(f"**{len(filtered)} corners in view** · {int(observed.shot_created.sum())} produced a shot from {len(observed)} observed outcomes · "
         f"{int(filtered.has_360.sum())} linked frames")
inspect, compare, validation = st.tabs(['Inspect corners','Compare patterns','Validation'])

with inspect:
    choices = filtered.corner_id.tolist()
    def corner_label(key):
        row = filtered.loc[filtered.corner_id==key].iloc[0]
        return f"{row['match']} | {row.minute:g}' P{row.period} | {row.taker} | {row.delivery} | {key[:8]}"
    selected = st.selectbox('Corner to inspect',choices,format_func=corner_label)
    row = filtered.loc[filtered.corner_id==selected].iloc[0]
    pitch_col, sequence_col = st.columns([1.3,1])
    with pitch_col:
        show_delivery = st.checkbox('Show recorded delivery endpoint',value=True)
        figure = pitch_figure(details[selected],show_delivery)
        st.pyplot(figure,width='stretch')
        plt.close(figure)
        if not row.has_360:
            st.info('This corner has no linked frame. The kick and delivery remain available from event data.')
        st.caption('Goal at top (x=120); width normalized so corners appear on the left. Circles: attackers. Open squares: defenders. K: keeper. Diamond: taker. Coordinates are standardized units.')
    with sequence_col:
        label = 'Unknown' if pd.isna(row.shot_created) else 'Shot created' if row.shot_created else 'No shot created'
        st.subheader(label)
        st.write(f"{row.team} · {row.delivery} · {row.cluster}")
        st.caption(f"Sequence stopped: {row.stop_reason}. Multiple shots count once for the binary outcome.")
        if pd.notna(row.first_shot_seconds):
            st.write(f"First shot: **{row.first_shot_seconds:.3f} seconds** after the kick.")
        st.dataframe(pd.DataFrame(details[selected]['sequence'])[['elapsed','event','team','player','detail']],
                     hide_index=True,width='stretch',column_config={'elapsed':st.column_config.NumberColumn('Seconds after kick',format='%.3f')})
        st.write('**Visible configuration at the kick**')
        labels = {'attackers_box':'Attackers in box','defenders_box':'Defenders in box','box_visible_fraction':'Box visible fraction',
                  'defenders_per_100_visible_units':'Defenders / 100 visible square units'}
        st.dataframe(pd.DataFrame([{'Measure':label,'Value':'Unknown' if pd.isna(row[key]) else f'{row[key]:.2f}'} for key,label in labels.items()]),hide_index=True,width='stretch')
    with st.expander('Similar configurations in the current filtered view'):
        _, _, prep, z = cluster_corners(corners)
        neighbours = nearest_corners(corners,selected,prep,z,n=len(corners))
        allowed = set(filtered.corner_id)
        neighbours = [r for r in neighbours if r['corner_id'] in allowed][:5]
        if neighbours:
            lookup = corners.set_index('corner_id')
            st.dataframe(pd.DataFrame([{'Match':lookup.loc[r['corner_id'],'match'],'Taker':lookup.loc[r['corner_id'],'taker'],
                'Delivery':lookup.loc[r['corner_id'],'delivery'],'Cluster':lookup.loc[r['corner_id'],'cluster'],
                'Distance':round(r['distance'],2),'Corner ID':r['corner_id']} for r in neighbours]),hide_index=True,width='stretch')
            st.caption('Euclidean distance in standardized spatial-feature space; smaller means more similar. Excludes the selected corner. It does not measure tactical quality.')
        else:
            st.info('No comparable frames in the current view. Select a usable frame or widen the filters.')

with compare:
    st.subheader('Shot creation by observed delivery')
    pass_corners = comparison_population[comparison_population.delivery.ne('Direct shot')]
    rates = summary(pass_corners)
    if not rates.empty:
        st.plotly_chart(rate_plot(rates),width='stretch',config={'displaylogo':False})
        st.caption(f'Points and 95% Wilson intervals; hover for counts. {len(pass_corners)} pass-corners in the comparison population. '
                   'The inspection outcome filter is ignored here to preserve the rate denominator. Direct shots are excluded.')
        st.download_button('Download this aggregate summary',rates.to_csv(index=False),'corner-delivery-summary.csv','text/csv')
        with st.expander('Delivery counts and intervals'):
            display = rates.copy()
            for key in ['rate','low','high']:
                display[key] = display[key].map(lambda value: f'{value:.1%}')
            st.dataframe(display.rename(columns={'rate':'Shot rate','low':'95% lower','high':'95% upper'}),hide_index=True,width='stretch')
    else:
        st.info('No pass-corners in the comparison population. Direct shots are excluded because their shot outcome is automatic. Select another delivery to compare rates.')
    st.subheader('Configuration clusters')
    st.caption('K-means on visible spatial features, after median imputation and standardization. Outcomes are excluded from fitting. Cluster labels are descriptive IDs, not named tactics; missing/very small frames remain unassigned.')
    cluster_rates = summary(pass_corners,('tournament','cluster'))
    if not cluster_rates.empty:
        st.plotly_chart(rate_plot(cluster_rates,'cluster'),width='stretch',config={'displaylogo':False})
    profiles = pass_corners[pass_corners.cluster.ne('No usable frame')].groupby('cluster').agg(
        corners=('corner_id','size'), attackers_box=('attackers_box','mean'), defenders_box=('defenders_box','mean'),
        attacker_mean_x=('attacker_mean_x','mean'), box_visible_fraction=('box_visible_fraction','mean')).round(2)
    st.dataframe(profiles,width='stretch')
    st.caption('Cluster profiles show available feature means for assigned frames only; counts are pass-corners in the comparison population.')
    with st.expander('Matching corner records (local research view)'):
        st.dataframe(filtered[['match','team','taker','minute','delivery','cluster','shot_created','has_360']],hide_index=True,width='stretch')

with validation:
    st.subheader('At-kick frame baseline')
    st.caption('The evaluation below always describes the complete loaded dataset, independent of exploration filters.')
    if model['status']=='evaluated':
        st.write(f"Training: {model['train_corners']} corners in {len(model['train_matches'])} matches. "
                 f"Holdout: {model['test_corners']} corners in {len(model['test_matches'])} different matches.")
        st.dataframe(pd.DataFrame(model['metrics']).T.round(4),width='stretch')
        st.write('Lower Brier score and log loss are better; higher ROC AUC and average precision are better. '
                 'The constant baseline uses only the training-set shot rate. Logistic regression uses the linked corner-frame features, with training-only imputation and scaling.')
        st.caption('One fixed split, no test-set tuning. Visibility selection and team overlap across different matches limit generalization. Delivery technique, pass endpoint, identity, clusters and outcomes are excluded from inputs.')
    else:
        st.info(model.get('reason','Insufficient matches for a meaningful held-out model.'))
    with st.expander('Reproducibility and source manifest'):
        st.write(f"Source revision: `{info['revision']}`")
        st.write(f"Unknown outcomes: {info['censored']}. Invalid player coordinates excluded: {info['invalid_players']}.")
        st.dataframe(pd.DataFrame(info['matches']),hide_index=True,width='stretch')
        st.write('Frame-model features: '+', '.join(SPATIAL))
        st.json({key:model[key] for key in ['train_matches','test_matches','seed'] if key in model})
        st.code('python -m tacticai_lite --all --offline\npython -m pytest -q\npython -m tacticai_lite.report')
    st.write('[StatsBomb source and terms](https://github.com/statsbomb/open-data) · '
             '[TacticAI paper](https://doi.org/10.1038/s41467-024-45965-x)')

st.divider()
st.image(str(ROOT/'assets'/'SB - Icon Lockup - Colour positive.png'),width=165)
st.caption('Data: StatsBomb Open Data. Local research tool. StatsBomb data and branding retain their original terms. '
           'Inspired by TacticAI; this is a simplified open-data analysis, not a reproduction of its model.')
