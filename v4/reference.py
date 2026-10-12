"""Independent formulations for validation; excluded from eventual runtime image."""
import math
import inspect

def solve_schedule(d):
    n=len(d['jobs']);states={(0,-1,0):(0,())}
    for size in range(n):
        nxt={}
        for (mask,last,clock),(cost,path) in states.items():
            for j,row in enumerate(d['jobs']):
                if mask&(1<<j) or any(not(mask&(1<<p)) for p in row['after']): continue
                setup=d['setup'][d['jobs'][last]['family']][row['family']] if last!=-1 else 0
                finish=max(clock,row['release'])+setup+row['duration']
                key=(mask|1<<j,j,finish);value=(cost+max(finish-row['due'],0)*row['weight'],path+(j,))
                if key not in nxt or value<nxt[key]: nxt[key]=value
        states=nxt
    best=min((cost,t,path) for (mask,last,t),(cost,path) in states.items())
    return dict(weighted_tardiness=best[0],makespan=best[1],**{'job_at_'+str(i):j for i,j in enumerate(best[2])})


def solve_cash(d):
    count=len(d['months']);depreciation=d['plant']/count
    facility=0.;loss=0.;taxsum=0.;peak=0.;flows=[]
    for index,row in enumerate(d['months']):
        balance=d['loan']*(1-index/count)
        interest=balance*d['loan_monthly_rate']+facility*d['revolver_monthly_rate']
        sale=d['salvage'] if index==count-1 else 0.
        income=row['revenue']-row['cost']-interest-depreciation+sale
        net=income-loss;tax=max(net,0)*d['tax_rate'];loss=max(-net,0)
        taxsum+=tax
        available=row['revenue']-row['cost']-interest-tax-d['loan']/count+sale
        if index==count-1: available+=d['working_capital']
        # Reserve is constant until liquidation, so available is surplus over reserve.
        newfacility=max(0,facility-available)
        distribution=max(0,available-facility)
        facility=newfacility;peak=max(peak,facility)
        if index==count-1: distribution+=d['reserve']-facility
        flows.append(distribution)
    initial=d['plant']+d['working_capital']+d['reserve']-d['loan']
    pv=-initial+sum(v*(1+d['annual_equity_discount'])**(-(i+1)/12) for i,v in enumerate(flows))
    return dict(equity_npv=pv,total_tax=taxsum,peak_revolver=peak,total_net_distributions=sum(flows),ending_loss_carry=loss)


def solve_selection(d):
    weights=[]
    for row in d['groups']:
        for disease in (0,1):
            pd=row['disease'] if disease else 1-row['disease']
            inc=row['include_disease'] if disease else row['include_healthy']
            pz=row['z_if_disease'] if disease else row['z_if_healthy']
            for z in (0,1): weights.append([disease,z,row['weight']*pd*inc*(pz if z else 1-pz)])
    inclusion=sum(x[2] for x in weights);pattern=1.
    for observed in d['observed']:
        before=sum(x[2] for x in weights)
        for state in weights:
            p=d['test_positive'][state[0]][state[1]]
            state[2]*=p if observed else 1-p
        after=sum(x[2] for x in weights);pattern*=after/before
    posterior=sum(x[2] for x in weights)
    return dict(selection_probability=inclusion/sum(x['weight'] for x in d['groups']),pattern_probability_among_selected=pattern,posterior_disease=sum(x[2]*x[0] for x in weights)/posterior,next_positive_probability=sum(x[2]*d['test_positive'][x[0]][x[1]] for x in weights)/posterior)


def solve_reactor(d):
    volume=d['initial_volume_L'];a=d['initial_A_mol']/volume;b=d['initial_B_mol']/volume;discharged=0.
    for seg in d['segments']:
        steps=6000;h=seg['minutes']/steps;t=0.;y=[a,b,discharged]
        def deriv(t,y):
            v=volume+(seg['in_L_min']-seg['out_L_min'])*t
            ca,cb,_=y
            return [seg['in_L_min']/v*(seg['feed_A_mol_L']-ca)-seg['k_per_min']*ca,seg['k_per_min']*ca-seg['in_L_min']/v*cb,seg['out_L_min']*cb]
        for i in range(steps):
            s1=deriv(t,y);s2=deriv(t+h/2,[x+h*s/2 for x,s in zip(y,s1)])
            s3=deriv(t+h/2,[x+h*s/2 for x,s in zip(y,s2)]);s4=deriv(t+h,[x+h*s for x,s in zip(y,s3)])
            y=[x+h*(a+2*b+2*c+e)/6 for x,a,b,c,e in zip(y,s1,s2,s3,s4)];t=(i+1)*h
        volume+=seg['minutes']*(seg['in_L_min']-seg['out_L_min'])
        f=seg['replace_fraction'];discharged=y[2]+volume*y[1]*f
        a=y[0]*(1-f)+f*seg['replace_A_mol_L'];b=y[1]*(1-f)
    return dict(final_volume_L=volume,final_A_mol=a*volume,final_B_mol=b*volume,total_B_discharged_mol=discharged)


def solve_parallel(d):
    n=len(d['jobs']);best=sum(j['duration'] for j in d['jobs'])+max(j['release'] for j in d['jobs'])
    # Independent global priority orders + machine-assignment enumeration.
    def orders(path,remaining):
        if not remaining: return [path]
        out=[]
        for j in remaining:
            if all(k in path for k in d['jobs'][j]['after']): out.extend(orders(path+[j],[k for k in remaining if k!=j]))
        return out
    for order in orders([],list(range(n))):
        for assignment in range(1<<n):
            clocks=[0,0];ends={}
            for j in order:
                m=(assignment>>j)&1;row=d['jobs'][j]
                clocks[m]=max(clocks[m],row['release'],max([ends[k] for k in row['after']]+[0]))+row['duration'];ends[j]=clocks[m]
            best=min(best,max(clocks))
    return dict(minimum_makespan=best,total_processing=sum(j['duration'] for j in d['jobs']))


def solve_option(d):
    n=d['steps'];dt=d['years']/n;up=math.exp(d['volatility']*math.sqrt(dt));down=1/up
    prob=(math.exp((d['rate']-d['yield'])*dt)-down)/(up-down);discount=math.exp(-d['rate']*dt);cache={}
    def price(i,j):
        if (i,j) in cache: return cache[(i,j)]
        exercise=max(d['strike']-d['spot']*up**j*down**(i-j),0)
        value=exercise if i==n else max(exercise,discount*((1-prob)*price(i+1,j)+prob*price(i+1,j+1)))
        cache[(i,j)]=value;return value
    american=price(0,0)
    european=discount**n*sum(math.comb(n,j)*prob**j*(1-prob)**(n-j)*max(d['strike']-d['spot']*up**j*down**(n-j),0) for j in range(n+1))
    return dict(american_put=american,european_put=european,early_exercise_premium=american-european)

SOLVERS={'constrained-schedule':solve_schedule,'leveraged-cashflows':solve_cash,'selected-testing':solve_selection,'piecewise-reactor':solve_reactor,'parallel-schedule':solve_parallel,'american-option':solve_option}

def solve(p): return SOLVERS[p.task_id](p.inputs)

def program(p):
    function=SOLVERS[p.task_id]
    return 'import math\n'+inspect.getsource(function)+'\nd='+repr(p.inputs)+'\nprint('+function.__name__+'(d))'
