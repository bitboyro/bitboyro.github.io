"""NativePath article figures. Python 3 + matplotlib + numpy.
Run beside measurements.json; outputs SVG, PNG and PDF under assets/images/nativepath.
Input contains the retained three rounds and one-second soak observations, not new measurements.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'images' / 'nativepath'
OUT.mkdir(parents=True, exist_ok=True)
D = json.loads((HERE / 'measurements.json').read_text())
BG, INK, MUTED, GRID = '#FDFCFB', '#2C2825', '#71665C', '#E8E0D8'
NP, JDK, SCAN = '#26776F', '#B07C45', '#B45449'
plt.rcParams.update({'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG,
    'font.family': 'DejaVu Sans', 'font.size': 12, 'text.color': INK, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.edgecolor': GRID,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold',
    'axes.titlelocation': 'left', 'grid.color': GRID, 'svg.fonttype': 'path', 'pdf.fonttype': 42})

def save(fig, name, title, foot):
    fig.suptitle(title, x=.085, y=.97, ha='left', fontsize=21, fontweight='bold')
    fig.text(.085, .025, foot, fontsize=10, color=MUTED, va='bottom')
    fig.savefig(OUT / f'{name}.svg', metadata={'Title': title, 'Description': foot})
    fig.savefig(OUT / f'{name}.png', dpi=180)
    fig.savefig(OUT / f'{name}.pdf')
    plt.close(fig)

# 1. Conceptual ownership diagram; no implied measurement of copy counts.
fig, ax = plt.subplots(figsize=(12, 6.3)); fig.subplots_adjust(left=.03,right=.98,top=.84,bottom=.13)
ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis('off')
ax.text(.1,4.8,'CONVENTIONAL MATERIALIZATION',fontsize=11,color=JDK,fontweight='bold')
ax.text(.1,2.6,'PROTECTED PATH',fontsize=11,color=NP,fontweight='bold')
for y,color,labels in [(3.9,JDK,['Secret source','HTTP / TLS buffers','Java String / byte[]','Application objects']),
                       (1.7,NP,['Native secret source','Rust I/O buffers','NativeSecret / view','Native-aware consumer'])]:
 for i,label in enumerate(labels):
  x=.1+i*3
  ax.add_patch(FancyBboxPatch((x,y-.42),2.65,.84,boxstyle='round,pad=.05,rounding_size=.08',facecolor=color+'15',edgecolor=color,lw=1.1))
  ax.text(x+1.325,y,label,ha='center',va='center',fontsize=11)
  if i<3:ax.add_patch(FancyArrowPatch((x+2.72,y),(x+2.94,y),arrowstyle='-|>',mutation_scale=14,color=MUTED))
ax.text(.1,3.05,'Unreachable objects do not imply that their former bytes have been overwritten.',fontsize=11,color=MUTED)
ax.text(.1,.78,'Owned native buffers: explicit wipe / cleanup. Java heap conversion remains an application boundary.',fontsize=11,color=MUTED)
ax.text(.1,.22,'Same process. Same privileges. A live native secret is still readable; an escaped view needs a valid lifetime.',fontsize=10,color=SCAN)
save(fig,'secret-journey','Where does the secret become a Java object?', 'Conceptual data-flow diagram · not a measured copy count · NativePath is not a hardware enclave')

# 2. Three observed rounds. Two separate output contracts; no inferred confidence intervals.
fig, axes=plt.subplots(2,2,figsize=(12,8.2));fig.subplots_adjust(left=.085,right=.97,top=.85,bottom=.16,hspace=.48,wspace=.28)
sizes=[256,8192,65536,524288]; labels=['256 B','8 KB','64 KB','512 KB']
for col,pair in enumerate([('jdk','nativepath'),('rest_jdk','rest_nativepath')]):
 for metric,row in [('rps',0),('heap_b_req',1)]:
  ax=axes[row,col]
  for name,offset,color,label in zip(pair,[-.1,.1],[JDK,NP],['JDK','NativePath']):
   means=[]
   for i,size in enumerate(sizes):
    vals=[r[metric] for r in D['client'] if r['config']==name and r['scenario']==f'{size}B_t16']
    assert len(vals)==3
    ax.scatter(np.array([i+offset]*3)+np.array([-.025,0,.025]),vals,s=22,alpha=.7,color=color,zorder=3)
    means.append(np.mean(vals))
   ax.plot(np.arange(4)+offset,means,color=color,lw=1.5,label=label,alpha=.85)
  ax.set_xticks(range(4),labels);ax.grid(axis='y',alpha=.7);ax.set_axisbelow(True)
  ax.set_ylabel('Successful requests / second' if metric=='rps' else 'Java allocation / request (bytes)')
  if row==0:
   ax.set_title('Direct: byte[] vs native body' if col==0 else 'Spring: byte[] on both paths',fontsize=13,pad=16)
   ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x/1000:g}k'));ax.set_ylim(bottom=0)
  else:ax.set_yscale('log');ax.set_ylim(200,3e6)
  if row==0 and col==0:ax.legend(frameon=False,fontsize=10,loc='upper right')
save(fig,'client-tradeoffs','Less Java allocation. A different performance story.', '20 Oct 2026 · separate Linux VMs · 16 client threads · dots = 3 rounds, lines = means (not confidence intervals)\nDirect outputs differ; Spring returns byte[] on both paths. Java allocation excludes Rust memory. Ordinary HTTP, not secret-header traffic.')

# 3. Raw-server comparison, normalized throughput plus absolute CPU costs.
fig,axes=plt.subplots(1,2,figsize=(12,6.1));fig.subplots_adjust(left=.255,right=.96,top=.81,bottom=.22,wspace=.48)
scenarios=['hello_c16','hello_c64','payload64k_c16','json_c16'];yl=['Hello · 16 connections','Hello · 64 connections','64 KB · 16 connections','JSON echo · 16 connections'];yy=np.arange(4)
means={}
for cfg in ['engine_java','raw_netty']:
 means[cfg]={s:{m:np.mean([r[m] for r in D['server'] if r['config']==cfg and r['scenario']==s]) for m in ['rps','cpu_us_req']} for s in scenarios}
ratios=[means['engine_java'][s]['rps']/means['raw_netty'][s]['rps'] for s in scenarios]
ax=axes[0];ax.hlines(yy,0,ratios,color=NP,lw=3,alpha=.4);ax.scatter(ratios,yy,color=NP,s=55,zorder=3);ax.axvline(1,color=JDK,ls='--',lw=1.2)
for y,r in zip(yy,ratios):ax.text(r-.025,y-.18,f'{(r-1)*100:.0f}%',ha='right',color=NP,fontsize=11)
ax.set_yticks(yy,yl);ax.invert_yaxis();ax.set_xlim(0,1.1);ax.set_xlabel('Throughput ratio · Netty = 1');ax.set_title('NativePath + Java / raw Netty',fontsize=12,pad=16);ax.grid(axis='x',alpha=.5)
ax=axes[1]
for cfg,offset,color,label in [('engine_java',-.12,NP,'NativePath + Java'),('raw_netty',.12,JDK,'Raw Netty')]:
 ax.scatter([means[cfg][s]['cpu_us_req'] for s in scenarios],yy+offset,color=color,label=label,s=45)
ax.set_yticks(yy,['']*4);ax.invert_yaxis();ax.set_xlim(left=0);ax.grid(axis='x',alpha=.5);ax.set_xlabel('Server CPU · µs / request');ax.set_title('CPU cost is a separate outcome',fontsize=12,pad=16);ax.legend(frameon=False,fontsize=10,loc='lower right')
save(fig,'server-tradeoffs','The raw server comparison includes losses.', '20 Oct 2026 · separate Linux VMs · means of 3 rounds · raw Java workers vs explicitly instantiated raw Netty\nJSON routes echo bytes. Spring-selected server and TLS-provider comparisons excluded.')

# 4. Entire retained sample/tick series, no smoothing of the latency tail.
soak=D['soak']; ticks=soak['ticks'];samples=soak['samples'];scans=soak['scans']
t=np.array([r['seconds']/60 for r in ticks]);st=np.array([r['seconds']/60 for r in samples]);p99=np.array([r['p99_us']/1000 for r in ticks])
fig,axes=plt.subplots(3,1,figsize=(12,8.8),sharex=True);fig.subplots_adjust(left=.095,right=.96,top=.86,bottom=.15,hspace=.22)
axes[0].plot(st,[r['rss_mb'] for r in samples],color=NP,lw=1.5,label='Process RSS')
axes[0].plot(st,[r['heap_used_mb'] for r in samples],color=JDK,lw=.7,alpha=.7,label='Used JVM heap');axes[0].axvspan(st[-1]-60,st[-1],color=NP,alpha=.06);axes[0].set_ylabel('Memory · MB');axes[0].set_ylim(0,760);axes[0].legend(frameon=False,ncol=2,fontsize=10,loc='upper left')
axes[0].text(72,690,'Final-hour RSS trend: +0.33 MB/h',color=NP,fontsize=10)
axes[1].plot(t,p99,color=NP,lw=.8);axes[1].set_yscale('log');axes[1].set_ylabel('Tick p99 · ms');axes[1].set_ylim(.5,10000)
axes[2].plot(t,[r['rps'] for r in ticks],color=NP,lw=.6);axes[2].axhline(20892,color=JDK,lw=1,ls='--',label='Target: 20,892 req/s');axes[2].set_ylabel('Requests / s');axes[2].set_xlabel('Elapsed minutes');axes[2].legend(frameon=False,fontsize=10,loc='lower right')
for ax in axes:
 ax.grid(axis='y',alpha=.5);ax.set_xlim(0,120)
 for scan in scans:ax.axvline(scan['seconds']/60,color=SCAN,alpha=.35,lw=.8)
axes[1].text(2,4000,'Vertical marks: scan completions',color=SCAN,fontsize=10)
save(fig,'soak-overview','150 million requests. Read the tail as well.', '20 Oct 2026 · NativePath Spring HTTPS · 120 min · 64 connections · 0 reported errors · content verification disabled\nLatency is the p99 within each one-second tick, not an aggregate request percentile. Final-hour trend is not whole-run growth.')

# 5. A declared descriptive window. Show one event and ALL ticks (no omitted outlier).
fig,axes=plt.subplots(1,2,figsize=(12,5.7));fig.subplots_adjust(left=.085,right=.96,top=.79,bottom=.23,wspace=.31)
near=np.array([any(s['seconds']-s['ms']/1000-1<=r['seconds']<=s['seconds']+10 for s in scans) for r in ticks])
axes[0].scatter(t[~near],p99[~near],color=NP,s=5,alpha=.3,label='Outside association windows')
axes[0].scatter(t[near],p99[near],color=SCAN,s=13,alpha=.75,label='Within association windows');axes[0].set_yscale('log');axes[0].set_ylim(.5,10000);axes[0].set_xlabel('Elapsed minutes');axes[0].set_ylabel('Tick p99 · ms');axes[0].set_title('All 7,200 measurement ticks',fontsize=13);axes[0].legend(frameon=False,fontsize=9,loc='lower right')
scan=scans[1]; end=scan['seconds']; start=end-scan['ms']/1000;relative=np.array([r['seconds']-end for r in ticks]);mask=(relative>=-15)&(relative<=22)
ax=axes[1];ax.axvspan(-scan['ms']/1000-1,10,color=SCAN,alpha=.07,label='Association window');ax.axvspan(-scan['ms']/1000,0,color=SCAN,alpha=.25,label='Inferred actual scan');ax.plot(relative[mask],p99[mask],color=NP,marker='o',ms=3,lw=1);ax.set_yscale('log');ax.set_ylim(.5,10000);ax.set_title('One protected scan · around minute 15',fontsize=13);ax.set_xlabel('Seconds relative to scan completion');ax.set_ylabel('Tick p99 · ms');ax.legend(frameon=False,fontsize=9,loc='upper right')
for ax in axes:ax.grid(axis='y',alpha=.5)
save(fig,'scan-and-tail','All 27 ticks above one second fall near scans.', 'Association, not causation · windows cover 113 / 7,200 ticks (~1.6%); start −1 s through scan end +10 s\nExact scan durations inferred from recorded end time and elapsed ms. No matched scan-disabled run; no aggregate latency removed.')

# 6. All controls and negative observations. No zero on a logarithmic count axis.
fig,ax=plt.subplots(figsize=(12,5.6));fig.subplots_adjust(left=.25,right=.95,top=.78,bottom=.18)
scenarios=['control','secure','error','abort','timeout'];labels=['Retained-string control','Protected request','Handler-error scenario','Mid-body abort scenario','Timeout scenario'];z=np.zeros((5,6));texts=[]
for i,scenario in enumerate(scenarios):
 for j,cycle in enumerate([1,2,3]):
  entry=next(r for r in D['scans'] if r['scenario']==scenario and r['cycle']==cycle)
  z[i,2*j]=entry['found_token'];z[i,2*j+1]=entry['found_password']
from matplotlib.colors import ListedColormap,BoundaryNorm
cmap=ListedColormap(['#EAF2EF','#E7CDAE']);ax.imshow((z>0).astype(int),cmap=cmap,aspect='auto',vmin=0,vmax=1)
for i in range(5):
 for j in range(6):ax.text(j,i,str(int(z[i,j])),ha='center',va='center',fontsize=16,color=INK)
ax.set_yticks(range(5),labels);ax.set_xticks(range(6),['C1 token','C1 password','C2 token','C2 password','C3 token','C3 password'],fontsize=10);ax.tick_params(length=0);ax.set_xticks(np.arange(-.5,6,1),minor=True);ax.set_yticks(np.arange(-.5,5,1),minor=True);ax.grid(which='minor',color=BG,lw=3);ax.tick_params(which='minor',bottom=False,left=False)
save(fig,'scan-observations','What the scanner actually found.', '20 Oct 2026 · counts of exact marker matches, not unique objects · controls deliberately retain Java strings\nSender output/status not enforced by the under-load harness: clean observations do not establish every intended failure transition.')
print('Generated 6 figures in SVG, PNG and PDF:', OUT)
