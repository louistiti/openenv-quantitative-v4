"""Synthetic quantitative problems. Targets never enter the calculation subprocess."""
from dataclasses import dataclass
import heapq
import itertools
import math
import random

TASK_IDS = ('resource-allocation', 'diagnostic-bayes', 'finite-sampling', 'markov-rewards',
            'network-routing', 'bond-cashflows', 'project-after-tax', 'loan-balloon',
            'currency-hedge', 'portfolio-risk', 'thermal-balance', 'decay-chain',
            'fall-with-drag', 'reaction-temperature', 'inventory-decision', 'network-reliability')
HELDOUT_IDS = ('sequential-testing', 'binomial-option', 'weighted-regression', 'tank-dilution')

@dataclass
class Problem:
    task_id: str
    inputs: dict
    brief: str
    targets: dict

    @property
    def instruction(self):
        return (self.brief + '\nInputs (all synthetic): ' + __import__('json').dumps(self.inputs) +
                '\nRequired answer keys: ' + ', '.join(self.targets) +
                '. Return a JSON object of numeric values using submit. Use at least 6 significant digits; tolerance max(0.0001, 0.00001*abs(target)). '
                'Full reward requires every key correct, no extra keys. Partial credit is at most 0.15 and only for correct numeric subresults. '
                'You may run Python calculations first. Check units and assumptions. No intermediate correctness feedback.')


def make_task(task_id, seed):
    if task_id not in TASK_IDS + HELDOUT_IDS: raise ValueError('Unknown task_id')
    r = random.Random(f'{task_id}:{seed}')
    if task_id == 'resource-allocation':
        d = dict(a=[r.randint(2,5),r.randint(2,5)],b=[r.randint(1,4),r.randint(1,4)],
                 capacity=[r.randint(25,45),r.randint(18,30)],profit=[r.randint(13,23),r.randint(11,25)],
                 limits=[r.randint(8,16),r.randint(8,16)])
        feasible=[(d['profit'][0]*x+d['profit'][1]*y,x,y) for x in range(d['limits'][0]+1) for y in range(d['limits'][1]+1)
                  if d['a'][0]*x+d['a'][1]*y<=d['capacity'][0] and d['b'][0]*x+d['b'][1]*y<=d['capacity'][1]]
        profit,x,y=max(feasible,key=lambda v:(v[0],-v[1],-v[2]))
        text='Choose integer production x,y >=0. Resource A uses a[0]*x+a[1]*y, B uses b[0]*x+b[1]*y; capacities correspond to A,B. Each product has its own upper limit. Maximize profit[0]*x+profit[1]*y. Ties: smallest x, then smallest y. Report x, y and profit.'
        out=dict(x=x,y=y,profit=profit)
    elif task_id == 'diagnostic-bayes':
        d=dict(weights=[r.randint(2,8) for _ in range(3)],prevalence=[r.randint(1,18)/100 for _ in range(3)],
               sensitivity=r.randint(80,98)/100,specificity=r.randint(85,99)/100,population=r.randint(10,30)*1000)
        p=sum(w*v for w,v in zip(d['weights'],d['prevalence']))/sum(d['weights']); pos=p*d['sensitivity']+(1-p)*(1-d['specificity'])
        out=dict(prevalence=p,positive_probability=pos,positive_predictive_value=p*d['sensitivity']/pos,expected_false_positives=d['population']*(1-p)*(1-d['specificity']))
        text='A population has three subgroups with relative weights (not percentages) and corresponding disease prevalences. A screening test has sensitivity=P(+|disease), specificity=P(-|no disease). Report overall prevalence, positive probability, positive predictive value=P(disease|+), and expected false positives in the stated population.'
    elif task_id == 'finite-sampling':
        n=r.randint(24,45); k=r.randint(7,16); draws=r.randint(5,9); threshold=r.randint(2,4)
        d=dict(total=n,marked=k,draws=draws,threshold=threshold)
        den=math.comb(n,draws); probs={j:math.comb(k,j)*math.comb(n-k,draws-j)/den for j in range(max(0,draws-(n-k)),min(draws,k)+1)}
        out=dict(tail_probability=sum(p for j,p in probs.items() if j>=threshold),mean=draws*k/n,variance=draws*k/n*(1-k/n)*(n-draws)/(n-1))
        text='Draw draws distinct items uniformly without replacement from total items, of which marked are marked. X is the marked count. Report P(X>=threshold), E[X], and Var(X).'
    elif task_id == 'markov-rewards':
        rows=[[r.randint(1,7) for _ in range(3)] for _ in range(3)]; matrix=[[v/sum(row) for v in row] for row in rows]
        d=dict(transition=matrix,start=r.randrange(3),steps=r.randint(4,9),rewards=[r.randint(-2,8) for _ in range(3)])
        p=[float(i==d['start']) for i in range(3)]; reward=0
        for _ in range(d['steps']):
            p=[sum(p[i]*matrix[i][j] for i in range(3)) for j in range(3)]
            reward+=sum(p[j]*d['rewards'][j] for j in range(3))
        out=dict(final_state2_probability=p[2],expected_total_reward=reward)
        text='States are indexed 0,1,2. Each transition row gives probabilities from that state. Start in start at time zero. After each of steps transitions, collect the reward of the NEW state, excluding time-zero reward. Report probability of state 2 at the end and expected accumulated reward.'
    elif task_id == 'network-routing':
        edges=[[i,i+1,r.randint(3,15)] for i in range(6)]+[[i,j,r.randint(5,28)] for i in range(5) for j in range(i+2,7) if r.random()<.65]
        d=dict(nodes=7,edges=edges,source=0,target=6)
        dist=[math.inf]*7; dist[0]=0; ways=[0]*7;ways[0]=1
        for node in range(7):
            for a,b,w in edges:
                if a!=node: continue
                val=dist[a]+w
                if val<dist[b]: dist[b]=val;ways[b]=ways[a]
                elif val==dist[b]: ways[b]+=ways[a]
        out=dict(shortest_distance=dist[6],shortest_path_count=ways[6])
        text='Edges are directed triples [from,to,cost]. Find minimum source-to-target cost and the number of distinct paths achieving that minimum. Edges always point to a larger node index. Report shortest_distance and shortest_path_count.'
    elif task_id == 'bond-cashflows':
        d=dict(face=r.choice([1000,2500,5000]),annual_coupon=r.randint(3,9)/100,annual_nominal_yield=r.randint(3,10)/100,
               frequency=r.choice([2,4]),remaining_periods=r.randint(5,14),elapsed_fraction=r.randint(1,8)/10)
        f=d['frequency'];c=d['face']*d['annual_coupon']/f;y=d['annual_nominal_yield']/f;e=d['elapsed_fraction'];n=d['remaining_periods']
        cash=[c+(d['face'] if k==n else 0) for k in range(1,n+1)];pv=[v/(1+y)**(k-e) for k,v in enumerate(cash,1)];dirty=sum(pv)
        out=dict(dirty_price=dirty,clean_price=dirty-c*e,macaulay_duration_years=sum((k-e)/f*v for k,v in enumerate(pv,1))/dirty)
        text='Price a fixed-coupon bond between coupon dates. Annual coupon and annual nominal yield are fractions; yield compounds frequency times/year. remaining_periods includes the next coupon and final redemption. elapsed_fraction is fraction of current coupon period already elapsed, so next payment occurs in (1-elapsed_fraction)/frequency years. Use fractional-exponent discounting; accrued interest=coupon_per_period*elapsed_fraction. Report dirty price, clean price and Macaulay duration in years.'
    elif task_id == 'project-after-tax':
        d=dict(cost=r.randint(8,20)*10000,years=r.randint(3,7),annual_revenue=r.randint(7,12)*10000,
               annual_cost=r.randint(2,5)*10000,tax_rate=r.randint(20,35)/100,discount_rate=r.randint(7,16)/100,
               salvage=r.randint(1,5)*10000,working_capital=r.randint(1,3)*10000)
        n=d['years'];depr=d['cost']/n;ocf=(d['annual_revenue']-d['annual_cost']-depr)*(1-d['tax_rate'])+depr;sal=d['salvage']*(1-d['tax_rate'])
        npv=-d['cost']-d['working_capital']+sum(ocf/(1+d['discount_rate'])**t for t in range(1,n+1))+(sal+d['working_capital'])/(1+d['discount_rate'])**n
        out=dict(annual_operating_cashflow=ocf,after_tax_salvage=sal,npv=npv)
        text='Evaluate a project. Pay cost and working capital at time zero. Straight-line depreciate cost to zero over years, no salvage deduction in depreciation. Annual revenue/cost occur at each year end. Tax rate applies to EBIT; assume tax losses immediately offset other income. Sell for salvage at final year end, taxed against zero book value, and fully recover working capital then. Report annual operating cash flow, after-tax salvage, and NPV.'
    elif task_id == 'loan-balloon':
        d=dict(principal=r.randint(10,40)*1000,annual_nominal_rate=r.randint(4,12)/100,months=r.choice([24,36,48,60]),balloon=r.randint(1,5)*1000)
        p=d['principal'];i=d['annual_nominal_rate']/12;n=d['months'];b=d['balloon'];payment=(p-b/(1+i)**n)*i/(1-(1+i)**(-n))
        out=dict(monthly_payment=payment,total_interest=n*payment+b-p,balance_after_half=p*(1+i)**(n//2)-payment*((1+i)**(n//2)-1)/i)
        text='A loan makes equal end-of-month payments for months months, plus an additional balloon at the final payment date. Interest is nominal annual/12 monthly. No fees or intermediate rounding. Report payment (excluding balloon), total interest over life, and outstanding balance immediately after half the monthly payments, before any balloon.'
    elif task_id == 'currency-hedge':
        d=dict(receivable_foreign=r.randint(5,20)*10000,months=r.choice([3,6,9]),spot_domestic_per_foreign=r.randint(90,150)/100,
               domestic_annual_simple=r.randint(2,8)/100,foreign_annual_simple=r.randint(1,7)/100,forward_domestic_per_foreign=r.randint(95,145)/100)
        t=d['months']/12;p=d['receivable_foreign']/(1+d['foreign_annual_simple']*t);mm=p*d['spot_domestic_per_foreign']*(1+d['domestic_annual_simple']*t);forward=d['receivable_foreign']*d['forward_domestic_per_foreign']
        out=dict(foreign_borrow_now=p,money_market_domestic_at_maturity=mm,forward_domestic_at_maturity=forward,advantage_money_market=mm-forward)
        text='Hedge a known foreign-currency receivable. Rates are simple annual fractions over months/12 years, quotes are domestic per one foreign. Money-market hedge: borrow enough foreign NOW to repay principal+interest with the receivable; immediately convert to domestic at spot and invest at domestic rate. Forward hedge: sell entire receivable at forward rate at maturity. Report foreign borrowing now, both locked domestic maturity amounts, and money-market amount minus forward amount.'
    elif task_id == 'portfolio-risk':
        d=dict(expected_returns=[r.randint(3,15)/100 for _ in range(2)],volatilities=[r.randint(8,30)/100 for _ in range(2)],correlation=r.randint(-7,8)/10)
        a,b=d['volatilities'];cov=d['correlation']*a*b;w=max(0,min(1,(b*b-cov)/(a*a+b*b-2*cov)));variance=w*w*a*a+(1-w)**2*b*b+2*w*(1-w)*cov
        out=dict(weight_asset0=w,expected_return=w*d['expected_returns'][0]+(1-w)*d['expected_returns'][1],standard_deviation=math.sqrt(variance))
        text='Find the minimum-variance fully invested two-asset portfolio with no short selling (weights in [0,1]). Returns and standard deviations are annual fractions, correlation is between assets. Report weight_asset0, expected_return, standard_deviation of that portfolio.'
    elif task_id == 'thermal-balance':
        d=dict(hot_mass_g=r.randint(250,800),hot_C=r.randint(65,95),cold_mass_g=r.randint(150,500),cold_C=r.randint(8,22),
               cup_heat_capacity_J_per_K=r.randint(50,180),loss_J=r.randint(1000,4000),water_cp_J_per_g_K=4.18)
        cp=d['water_cp_J_per_g_K'];temp=(d['hot_mass_g']*cp*d['hot_C']+(d['cold_mass_g']*cp+d['cup_heat_capacity_J_per_K'])*d['cold_C']-d['loss_J'])/((d['hot_mass_g']+d['cold_mass_g'])*cp+d['cup_heat_capacity_J_per_K'])
        out=dict(final_C=temp,hot_heat_released_J=d['hot_mass_g']*cp*(d['hot_C']-temp))
        text='Mix hot and cold liquid water in a cup initially at cold_C. No phase changes, constant stated water cp. The cup heat capacity is separate from water; a fixed loss_J escapes to surroundings during mixing. Masses in grams. Report equilibrium final_C and heat released by hot water in joules.'
    elif task_id == 'decay-chain':
        d=dict(initial_A=r.randint(2,9)*1000,half_life_A_hours=r.randint(2,8),half_life_B_hours=r.randint(10,18),time_hours=r.randint(3,15))
        la=math.log(2)/d['half_life_A_hours'];lb=math.log(2)/d['half_life_B_hours'];a=d['initial_A']*math.exp(-la*d['time_hours']);b=d['initial_A']*la/(lb-la)*(math.exp(-la*d['time_hours'])-math.exp(-lb*d['time_hours']))
        out=dict(amount_A=a,amount_B=b,amount_stable=d['initial_A']-a-b)
        text='A decays to B, B decays to a stable product, both first-order. Initial A is initial_A atoms in a continuum expectation model, initial B and stable product are zero. Each decay creates exactly one daughter; no other processes. Half-lives and time are in hours. Report expected amounts of A, B, stable product at time_hours.'
    elif task_id == 'fall-with-drag':
        d=dict(mass_kg=r.randint(3,12),drag_kg_per_s=r.randint(2,7),g_m_per_s2=9.81,terminal_fraction=r.randint(65,90)/100)
        tau=d['mass_kg']/d['drag_kg_per_s'];v=d['g_m_per_s2']*tau;t=-tau*math.log(1-d['terminal_fraction']);s=v*(t-tau*(1-math.exp(-t/tau)))
        out=dict(terminal_speed_m_per_s=v,time_s=t,distance_m=s)
        text='An object starts from rest and falls vertically with linear drag F_drag=-drag_kg_per_s*v. Down is positive; ignore buoyancy. Find terminal speed, time to first reach terminal_fraction times terminal speed, and distance fallen by that time. Use SI units.'
    elif task_id == 'reaction-temperature':
        d=dict(k_reference_per_min=r.randint(5,20)/100,reference_C=r.randint(15,30),target_C=r.randint(40,65),activation_kJ_per_mol=r.randint(35,70),conversion=r.randint(75,95)/100,R_J_per_mol_K=8.314)
        k=d['k_reference_per_min']*math.exp(d['activation_kJ_per_mol']*1000/d['R_J_per_mol_K']*(1/(d['reference_C']+273.15)-1/(d['target_C']+273.15)))
        out=dict(k_target_per_min=k,time_to_conversion_min=-math.log(1-d['conversion'])/k,half_life_min=math.log(2)/k)
        text='A first-order isothermal reaction follows Arrhenius kinetics. k_reference applies at reference_C. Convert Celsius to Kelvin and activation energy kJ to J. Compute k at target_C, time to stated conversion from fresh reactant, and half-life, all time in minutes.'
    elif task_id == 'inventory-decision':
        weights=[r.randint(1,9) for _ in range(5)];d=dict(demands=[r.randint(2,5)+i*5 for i in range(5)],probabilities=[w/sum(weights) for w in weights],purchase=r.randint(5,9),sale=r.randint(15,24),salvage=r.randint(0,4),shortage_penalty=r.randint(2,6),max_order=30)
        def profit(q): return sum(p*(d['sale']*min(q,v)+d['salvage']*max(q-v,0)-d['purchase']*q-d['shortage_penalty']*max(v-q,0)) for p,v in zip(d['probabilities'],d['demands']))
        q=max(range(31),key=lambda q:(profit(q),-q))
        out=dict(order_quantity=q,expected_profit=profit(q),expected_shortage=sum(p*max(v-q,0) for p,v in zip(d['probabilities'],d['demands'])))
        text='Choose integer order quantity 0..max_order before uncertain demand. Earn sale per unit sold, salvage per leftover unit; pay purchase for every ordered unit and shortage_penalty per unmet demand unit. Demands and probabilities correspond. Maximize expected profit; tie chooses smaller order. Report order quantity, expected profit, expected shortage units.'
    elif task_id == 'network-reliability':
        d=dict(component_probabilities=[r.randint(65,95)/100 for _ in range(5)],paths=[[0,1],[0,2,3],[4,3]])
        success=0;expected=0
        for bits in itertools.product([0,1],repeat=5):
            p=math.prod(q if z else 1-q for q,z in zip(d['component_probabilities'],bits));working=sum(all(bits[i] for i in path) for path in d['paths']);success+=p*(working>0);expected+=p*working
        out=dict(system_success_probability=success,expected_working_paths=expected)
        text='Five components work independently with corresponding probabilities. A path works iff all its listed component indices work. The system works iff at least one listed path works. Shared components make path events dependent. Report system_success_probability and expected_working_paths.'
    elif task_id == 'sequential-testing':
        d=dict(prior=r.randint(3,20)/100,sensitivities=[r.randint(75,97)/100 for _ in range(3)],specificities=[r.randint(80,98)/100 for _ in range(3)],results=[1,0,1])
        ld=math.prod(s if z else 1-s for s,z in zip(d['sensitivities'],d['results']));ln=math.prod(1-s if z else s for s,z in zip(d['specificities'],d['results']));e=d['prior']*ld+(1-d['prior'])*ln
        out=dict(posterior=d['prior']*ld/e,evidence_probability=e)
        text='Three tests are conditionally independent GIVEN disease status (not marginally independent). Each result is 1 for positive, 0 for negative. Given prior disease probability, sensitivities and specificities, report posterior disease probability after all results and marginal probability of this exact result sequence.'
    elif task_id == 'binomial-option':
        d=dict(spot=r.randint(70,120),strike=r.randint(75,115),up=1.2,down=.85,annual_continuous_rate=r.randint(2,8)/100,years=1,steps=r.randint(3,6))
        dt=d['years']/d['steps'];q=(math.exp(d['annual_continuous_rate']*dt)-d['down'])/(d['up']-d['down']);values=[max(d['spot']*d['up']**j*d['down']**(d['steps']-j)-d['strike'],0) for j in range(d['steps']+1)]
        for n in range(d['steps'],0,-1): values=[math.exp(-d['annual_continuous_rate']*dt)*(q*values[j+1]+(1-q)*values[j]) for j in range(n)]
        out=dict(risk_neutral_up_probability=q,european_call_price=values[0])
        text='Price a European call using a recombining binomial tree. Each of steps equal intervals multiplies stock by up or down. No dividends. Continuously compounded annual risk-free rate, maturity years. Report risk-neutral up probability per step and call price using backward induction or equivalent risk-neutral expectation.'
    elif task_id == 'weighted-regression':
        x=list(range(1,7));y=[r.randint(2,8)*i+r.randint(-3,5) for i in x];w=[r.randint(1,5) for _ in x];d=dict(x=x,y=y,weights=w,predict_x=8)
        sx=sum(a*b for a,b in zip(w,x));sy=sum(a*b for a,b in zip(w,y));xx=sum(a*b*b for a,b in zip(w,x));xy=sum(a*b*c for a,b,c in zip(w,x,y));sw=sum(w);b=(xy-sx*sy/sw)/(xx-sx*sx/sw);a=(sy-b*sx)/sw
        out=dict(intercept=a,slope=b,prediction=a+b*d['predict_x'])
        text='Fit y=intercept+slope*x by minimizing sum(weights[i]*(y[i]-intercept-slope*x[i])**2). Weights are direct least-squares weights, not square roots. Report intercept, slope, prediction at predict_x.'
    else:
        d=dict(volume_L=r.randint(100,250),initial_salt_kg=r.randint(5,15),inflow_L_per_min=r.randint(3,8),outflow_L_per_min=r.randint(1,2),incoming_kg_per_L=r.randint(1,5)/100,time_min=r.randint(10,30))
        v=d['volume_L'];q=d['inflow_L_per_min'];o=d['outflow_L_per_min'];t=d['time_min'];c=d['incoming_kg_per_L'];vt=v+(q-o)*t;m=c*vt+(d['initial_salt_kg']-c*v)*(v/vt)**(o/(q-o))
        out=dict(final_volume_L=vt,final_salt_kg=m,final_concentration_kg_per_L=m/vt)
        text='A perfectly mixed tank initially has volume_L liquid and initial_salt_kg salt. Constant inflow with incoming_kg_per_L concentration and outflow at the stated L/min rates. Volume changes; do not assume constant volume. No precipitation/overflow. Report volume, salt mass and concentration at time_min.'
    return Problem(task_id,d,text,out)
