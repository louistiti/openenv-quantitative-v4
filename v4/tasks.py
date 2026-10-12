"""Fresh synthetic multi-stage models; grading state never enters worker."""
from dataclasses import dataclass
import itertools
import json
import math
import random

TASK_IDS=('constrained-schedule','selected-testing')
HELDOUT_IDS=('parallel-schedule','american-option')
EXCLUDED_IDS=('leveraged-cashflows','piecewise-reactor')

@dataclass
class Problem:
    task_id: str
    inputs: dict
    brief: str
    targets: dict
    @property
    def instruction(self):
        return (self.brief+'\nSynthetic case data: '+json.dumps(self.inputs)+
                '\nSubmit numeric JSON with exactly these keys: '+', '.join(self.targets)+
                '. Absolute tolerance 0.0001 or relative tolerance 0.00001, whichever is larger. '
                'Report at least 6 significant digits. Every key must be correct for full reward; '
                'partial numeric credit is capped at 0.15. No intermediate correctness feedback. '
                'Python calculations are available; variables do not persist across calls.')


def schedule_target(d):
    n=len(d['jobs']);best=None;seen={}
    def visit(mask,last,t,cost,path):
        nonlocal best
        state=(mask,last,t)
        if state in seen and seen[state] <= (cost,path): return
        seen[state]=(cost,path)
        if best and cost>best[0]: return
        if mask==(1<<n)-1:
            candidate=(cost,t,path)
            if best is None or candidate<best: best=candidate
            return
        for j,job in enumerate(d['jobs']):
            if mask>>j&1 or any(not(mask>>k&1) for k in job['after']): continue
            start=max(t,job['release'])
            setup=0 if last<0 else d['setup'][d['jobs'][last]['family']][job['family']]
            end=start+setup+job['duration']
            visit(mask|1<<j,j,end,cost+job['weight']*max(0,end-job['due']),path+(j,))
    visit(0,-1,0,0,())
    return dict(weighted_tardiness=best[0],makespan=best[1],**{'job_at_'+str(i):j for i,j in enumerate(best[2])})


def cash_target(d):
    n=len(d['months']);loan=d['loan'];rev=0.;loss=0.;cash=d['reserve'];dividends=[];taxes=0.;peak=0.
    principal=loan/n;depreciation=d['plant']/n
    for i,row in enumerate(d['months']):
        interest=loan*d['loan_monthly_rate']+rev*d['revolver_monthly_rate']
        taxable=row['revenue']-row['cost']-depreciation-interest+(d['salvage'] if i==n-1 else 0)
        if taxable<0: loss-=taxable;tax=0.
        else:
            taxable_after_loss=max(0,taxable-loss);loss=max(0,loss-taxable);tax=taxable_after_loss*d['tax_rate']
        taxes+=tax
        cash+=row['revenue']-row['cost']-interest-tax-principal
        loan-=principal
        if i==n-1: cash+=d['salvage']+d['working_capital']
        if cash<d['reserve']:
            draw=d['reserve']-cash;rev+=draw;cash+=draw;peak=max(peak,rev)
        excess=max(0,cash-d['reserve']);payment=min(rev,excess);rev-=payment;cash-=payment
        dividend=max(0,cash-d['reserve']);cash-=dividend
        if i==n-1: dividend+=cash-rev;cash=0.
        dividends.append(dividend)
    equity=d['plant']+d['working_capital']+d['reserve']-d['loan']
    monthly=(1+d['annual_equity_discount'])**(1/12)-1
    npv=-equity+sum(v/(1+monthly)**(i+1) for i,v in enumerate(dividends))
    return dict(equity_npv=npv,total_tax=taxes,peak_revolver=peak,total_net_distributions=sum(dividends),ending_loss_carry=loss)


def selection_target(d):
    # Four-state joint table for disease D and persistent sample condition Z.
    masses={};selected=0.;pattern=0.;disease_pattern=0.;next_positive=0.
    for g in d['groups']:
        for disease in (0,1):
            for z in (0,1):
                state=g['weight']*(g['disease'] if disease else 1-g['disease'])*(g['z_if_disease'] if disease else g['z_if_healthy'])**z*(1-(g['z_if_disease'] if disease else g['z_if_healthy']))**(1-z)
                inclusion=g['include_disease'] if disease else g['include_healthy']
                prior=state*inclusion;selected+=prior
                positive=d['test_positive'][disease][z]
                likelihood=math.prod(positive if x==1 else 1-positive for x in d['observed'])
                joint=prior*likelihood;pattern+=joint;disease_pattern+=joint*disease;next_positive+=joint*positive
    return dict(selection_probability=selected/sum(g['weight'] for g in d['groups']),pattern_probability_among_selected=pattern/selected,posterior_disease=disease_pattern/pattern,next_positive_probability=next_positive/pattern)


def reactor_target(d,steps=3000):
    # Segment-aligned RK4 so coefficient jumps never contaminate a step.
    a=d['initial_A_mol'];b=d['initial_B_mol'];discharged=0.;volume=d['initial_volume_L']
    for seg in d['segments']:
        h=seg['minutes']/steps
        def rhs(t,y):
            v=volume+(seg['in_L_min']-seg['out_L_min'])*t
            aa,bb,_=y
            reaction=seg['k_per_min']*aa
            return [seg['in_L_min']*seg['feed_A_mol_L']-seg['out_L_min']*aa/v-reaction,reaction-seg['out_L_min']*bb/v,seg['out_L_min']*bb/v]
        y=[a,b,discharged];t=0.
        for _ in range(steps):
            k1=rhs(t,y);k2=rhs(t+h/2,[x+h*v/2 for x,v in zip(y,k1)])
            k3=rhs(t+h/2,[x+h*v/2 for x,v in zip(y,k2)]);k4=rhs(t+h,[x+h*v for x,v in zip(y,k3)])
            y=[x+h*(p+2*q+2*r+s)/6 for x,p,q,r,s in zip(y,k1,k2,k3,k4)];t+=h
        a,b,discharged=y;volume+=(seg['in_L_min']-seg['out_L_min'])*seg['minutes']
        # At segment end, drain then replace with B-free A solution (instantaneous).
        f=seg['replace_fraction'];a=a*(1-f)+volume*f*seg['replace_A_mol_L'];discharged+=b*f;b*=1-f
    return dict(final_volume_L=volume,final_A_mol=a,final_B_mol=b,total_B_discharged_mol=discharged)


def parallel_target(d):
    # Exhaustive assignment/order via two completion clocks, eliminate machine swaps.
    n=len(d['jobs']);best=None
    def visit(mask,times,ends):
        nonlocal best
        if best and max(times)>best: return
        if mask==(1<<n)-1:
            if best is None or max(times)<best: best=max(times)
            return
        for j,job in enumerate(d['jobs']):
            if mask>>j&1 or any(not(mask>>k&1) for k in job['after']): continue
            for machine in (0,1):
                if machine==1 and times[0]==times[1]: continue
                finish=max(times[machine],job['release'],max((ends[k] for k in job['after']),default=0))+job['duration']
                updated=list(times);updated[machine]=finish
                newends=dict(ends);newends[j]=finish
                visit(mask|1<<j,updated,newends)
    visit(0,[0,0],{})
    return dict(minimum_makespan=best,total_processing=sum(j['duration'] for j in d['jobs']))


def option_target(d):
    dt=d['years']/d['steps'];u=math.exp(d['volatility']*math.sqrt(dt));dn=1/u
    p=(math.exp((d['rate']-d['yield'])*dt)-dn)/(u-dn);discount=math.exp(-d['rate']*dt)
    levels=[];v=[max(d['strike']-d['spot']*u**j*dn**(d['steps']-j),0) for j in range(d['steps']+1)]
    for i in reversed(range(d['steps'])):
        v=[max(d['strike']-d['spot']*u**j*dn**(i-j),discount*(p*v[j+1]+(1-p)*v[j])) for j in range(i+1)]
        levels.append(v)
    eu=[max(d['strike']-d['spot']*u**j*dn**(d['steps']-j),0) for j in range(d['steps']+1)]
    for i in reversed(range(d['steps'])): eu=[discount*(p*eu[j+1]+(1-p)*eu[j]) for j in range(i+1)]
    return dict(american_put=v[0],european_put=eu[0],early_exercise_premium=v[0]-eu[0])


def make_task(task_id,seed):
    if task_id not in TASK_IDS+HELDOUT_IDS+EXCLUDED_IDS: raise ValueError('Unknown task_id')
    r=random.Random(f'v2:{task_id}:{seed}')
    if task_id=='constrained-schedule':
        n=r.randint(7,9)
        jobs=[dict(duration=r.randint(2,7),release=r.randint(0,15),due=r.randint(10,40),weight=r.randint(1,7),family=r.randrange(3),after=([r.randrange(j)] if j>1 and r.random()<.35 else [])) for j in range(n)]
        d=dict(jobs=jobs,setup=[[0 if i==j else r.randint(1,5) for j in range(3)] for i in range(3)])
        text='Plan all zero-indexed jobs on one machine initially idle at minute zero. Each job runs once without interruption. Its predecessors must finish and its release time must be reached before its setup starts. After a job, the next setup takes the matrix entry from previous family to new family; the first job has no setup. Processing starts immediately after setup. Do not deliberately idle except to wait for releases or predecessors. Minimize the sum over jobs of weight times positive lateness of completion beyond due. Break ties by earliest final completion, then lexicographically smallest sequence of job IDs. Report weighted tardiness, makespan, and each job ID in sequence.'
        out=schedule_target(d)
    elif task_id=='leveraged-cashflows':
        n=r.choice([12,18,24]);plant=r.randint(80,150)*1000
        d=dict(plant=plant,working_capital=r.randint(5,15)*1000,reserve=r.randint(3,8)*1000,loan=plant*r.choice([.5,.65,.75]),loan_monthly_rate=r.randint(4,10)/1000,revolver_monthly_rate=r.randint(10,18)/1000,tax_rate=r.choice([.2,.25,.3]),annual_equity_discount=r.randint(9,17)/100,salvage=r.randint(10,35)*1000,months=[dict(revenue=r.randint(3,22)*1000,cost=r.randint(5,12)*1000) for _ in range(n)])
        text='Model a project in currency units. At time zero, equity funds plant, working capital and reserve minus the term loan. Depreciate the plant straight-line to zero over the listed months. Each month first pay interest on opening term-loan and revolver balances. Interest and depreciation reduce taxable operating income. Losses carry forward without expiration; offset later positive taxable income before paying tax, no refunds. Repay exactly original loan divided by number of months each month. Add salvage and full working-capital recovery in the final month; salvage is taxable then because book value is zero, working-capital recovery is not taxable. After these flows, draw unlimited revolver if needed to restore reserve, then use any cash above reserve to repay revolver, then distribute any remaining excess to equity. In final month additionally distribute reserve less any remaining revolver (a negative terminal distribution is an equity contribution). No cash interest earned. Discount equity flows at the effective annual rate converted to monthly. Report equity NPV including initial contribution, total tax, largest outstanding revolver after a draw, total undiscounted net equity distributions excluding time zero, and ending carried tax loss.'
        out=cash_target(d)
    elif task_id=='selected-testing':
        groups=[dict(weight=r.randint(2,9),disease=r.randint(3,28)/100,z_if_disease=r.randint(20,75)/100,z_if_healthy=r.randint(5,40)/100,include_disease=r.randint(45,95)/100,include_healthy=r.randint(10,60)/100) for _ in range(r.randint(2,4))]
        d=dict(groups=groups,test_positive=[[r.randint(1,8)/100,r.randint(25,50)/100],[r.randint(75,94)/100,r.randint(40,70)/100]],observed=[r.choice([0,1]) for _ in range(r.randint(3,6))])
        text='A person is sampled with prior group probabilities proportional to weights. Disease probability varies by group. A persistent sample condition Z is drawn once with the stated conditional probabilities, and persists for every test. Inclusion in a study depends on disease and group through include_disease/include_healthy, independent of Z conditional on disease and group. We observe an included person with ordered binary test outcomes (1 positive, 0 negative). Tests are independent conditional on disease and Z, NOT marginally independent. test_positive is indexed [disease=0 or 1][Z=0 or 1], same for all groups. The person remains in the same disease/Z state. Report population selection probability, probability of this exact ordered pattern among included people, posterior disease probability, and probability the next test is positive.'
        out=selection_target(d)
    elif task_id=='piecewise-reactor':
        d=dict(initial_volume_L=r.randint(80,160),initial_A_mol=r.randint(20,65),initial_B_mol=r.randint(5,20),segments=[dict(minutes=r.randint(8,20),in_L_min=r.randint(3,7),out_L_min=r.randint(1,4),feed_A_mol_L=r.randint(1,5)/10,k_per_min=r.randint(2,9)/100,replace_fraction=r.choice([0,.1,.25]),replace_A_mol_L=r.randint(1,4)/10) for _ in range(3)])
        text='A well-mixed liquid reactor converts A to B one-to-one by first-order reaction: per-minute reaction amount is k_per_min times current moles of A. A-only feed enters; well-mixed liquid leaves at the stated rate. Track changing volume, both molar inventories and cumulative B leaving. Follow the segments in order with rates constant within each. At the END of EVERY segment, including the last, instantaneously drain replace_fraction of the mixed liquid and replace the same volume with fresh B-free solution of concentration replace_A_mol_L. Drained B counts in cumulative discharge; drained A does not react after leaving. No overflow, precipitation, evaporation or other reactions. Report final volume, moles A, moles B and total discharged B. Integrate accurately enough for the stated tolerance.'
        out=reactor_target(d)
    elif task_id=='parallel-schedule':
        d=dict(jobs=[dict(duration=r.randint(2,8),release=r.randint(0,8),after=([r.randrange(j)] if j>1 and r.random()<.5 else [])) for j in range(6)])
        text='Schedule all zero-indexed jobs once on two identical initially idle machines. No setup or preemption. A job cannot start before release time or before all predecessor jobs finish, even if they run on the other machine. Minimize time when all jobs have finished. Deliberate idle time is allowed. Report optimal makespan and sum of processing durations.'
        out=parallel_target(d)
    else:
        d=dict(spot=r.randint(75,125),strike=r.randint(80,120),rate=r.randint(3,9)/100,**{'yield':r.randint(0,5)/100},volatility=r.randint(15,40)/100,years=r.choice([.5,1,1.5]),steps=r.randint(12,24))
        text='Price American and European puts on a synthetic asset using a Cox-Ross-Rubinstein tree with the stated number of equal time steps. Rate and continuous dividend yield are continuously compounded per year; volatility is annual. American exercise is available at every tree node including time zero. Use risk-neutral valuation. Report both put values and American minus European premium.'
        out=option_target(d)
    return Problem(task_id,d,text,out)
