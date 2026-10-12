"""Independent reference calculations; excluded from the runtime image."""
import inspect
import json
import math


def bisect(f,lo,hi):
    for _ in range(90):
        mid=(lo+hi)/2
        if f(mid)>0: hi=mid
        else: lo=mid
    return (lo+hi)/2


def rk4(f,y,stop,n=6000):
    h=stop/n;t=0
    for _ in range(n):
        k1=f(t,y);k2=f(t+h/2,[a+h*b/2 for a,b in zip(y,k1)])
        k3=f(t+h/2,[a+h*b/2 for a,b in zip(y,k2)]);k4=f(t+h,[a+h*b for a,b in zip(y,k3)])
        y=[a+h*(b+2*c+2*d+e)/6 for a,b,c,d,e in zip(y,k1,k2,k3,k4)];t+=h
    return y


def solve(ident,d):
    if ident=='resource-allocation':
        best=None
        for x in range(d['limits'][0]+1):
            ys=[y for y in range(d['limits'][1]+1) if all(row[0]*x+row[1]*y<=cap for row,cap in zip([d['a'],d['b']],d['capacity']))]
            if ys:
                y=max(ys);p=x*d['profit'][0]+y*d['profit'][1]
                if best is None or (p,-x,-y)>(best[0],-best[1],-best[2]): best=(p,x,y)
        return dict(x=best[1],y=best[2],profit=best[0])
    if ident=='diagnostic-bayes':
        diseased=sum(w*p for w,p in zip(d['weights'],d['prevalence']))/sum(d['weights'])
        tp=diseased*d['sensitivity'];fp=(1-diseased)*(1-d['specificity'])
        return dict(prevalence=diseased,positive_probability=tp+fp,positive_predictive_value=tp/(tp+fp),expected_false_positives=fp*d['population'])
    if ident=='finite-sampling':
        # Distribution from sequential draws, tracking count; no combinatorial formula.
        n=d['total'];k=d['marked'];pmf={0:1.0}
        for draw in range(d['draws']):
            new={}
            for successes,p in pmf.items():
                hit=(k-successes)/(n-draw);new[successes+1]=new.get(successes+1,0)+p*hit
                new[successes]=new.get(successes,0)+p*(1-hit)
            pmf=new
        mean=sum(j*p for j,p in pmf.items())
        return dict(tail_probability=sum(p for j,p in pmf.items() if j>=d['threshold']),mean=mean,variance=sum((j-mean)**2*p for j,p in pmf.items()))
    if ident=='markov-rewards':
        # Recursive conditional value functions, opposite direction to forward distribution.
        final=[0,0,1];total=[0,0,0]
        for _ in range(d['steps']):
            final=[sum(p*v for p,v in zip(row,final)) for row in d['transition']]
            total=[sum(p*(reward+old) for p,reward,old in zip(row,d['rewards'],total)) for row in d['transition']]
        return dict(final_state2_probability=final[d['start']],expected_total_reward=total[d['start']])
    if ident=='network-routing':
        def paths(node):
            if node==d['target']: return [0]
            return [w+rest for a,b,w in d['edges'] if a==node for rest in paths(b)]
        costs=paths(d['source']);minimum=min(costs)
        return dict(shortest_distance=minimum,shortest_path_count=costs.count(minimum))
    if ident=='bond-cashflows':
        rate=d['annual_nominal_yield']/d['frequency'];coupon=d['face']*d['annual_coupon']/d['frequency'];dirty=0;moment=0
        for k in range(d['remaining_periods']):
            years=(k+1-d['elapsed_fraction'])/d['frequency'];flow=coupon+(d['face'] if k==d['remaining_periods']-1 else 0)
            value=flow*math.exp(-d['frequency']*years*math.log1p(rate));dirty+=value;moment+=years*value
        return dict(dirty_price=dirty,clean_price=dirty-coupon*d['elapsed_fraction'],macaulay_duration_years=moment/dirty)
    if ident=='project-after-tax':
        book=d['cost'];npv=-book-d['working_capital'];annual=0;after_sale=0
        for year in range(1,d['years']+1):
            depreciation=d['cost']/d['years'];book-=depreciation
            annual=d['annual_revenue']-d['annual_cost']-d['tax_rate']*(d['annual_revenue']-d['annual_cost']-depreciation)
            flow=annual
            if year==d['years']:
                after_sale=d['salvage']-d['tax_rate']*(d['salvage']-book)
                flow+=after_sale+d['working_capital']
            npv+=flow/(1+d['discount_rate'])**year
        return dict(annual_operating_cashflow=annual,after_tax_salvage=after_sale,npv=npv)
    if ident=='loan-balloon':
        rate=d['annual_nominal_rate']/12
        def balance(payment):
            b=d['principal']
            for _ in range(d['months']): b=b*(1+rate)-payment
            return b
        payment=bisect(lambda x:d['balloon']-balance(x),0,d['principal'])
        b=d['principal'];interest=0;half=0
        for m in range(1,d['months']+1):
            i=b*rate;interest+=i;b+=i-payment
            if m==d['months']//2: half=b
        return dict(monthly_payment=payment,total_interest=interest,balance_after_half=half)
    if ident=='currency-hedge':
        t=d['months']/12;foreign=d['receivable_foreign']/(1+d['foreign_annual_simple']*t)
        domestic=foreign*d['spot_domestic_per_foreign'];mm=domestic+domestic*d['domestic_annual_simple']*t
        forward=d['receivable_foreign']*d['forward_domestic_per_foreign']
        return dict(foreign_borrow_now=foreign,money_market_domestic_at_maturity=mm,forward_domestic_at_maturity=forward,advantage_money_market=mm-forward)
    if ident=='portfolio-risk':
        a,b=d['volatilities'];cov=a*b*d['correlation']
        def derivative(w): return 2*w*a*a-2*(1-w)*b*b+2*(1-2*w)*cov
        w=0 if derivative(0)>=0 else (1 if derivative(1)<=0 else bisect(derivative,0,1))
        variance=(w*a)**2+((1-w)*b)**2+2*w*(1-w)*cov
        return dict(weight_asset0=w,expected_return=sum(x*y for x,y in zip([w,1-w],d['expected_returns'])),standard_deviation=math.sqrt(variance))
    if ident=='thermal-balance':
        def energy(t): return (d['hot_mass_g']*d['water_cp_J_per_g_K']*(t-d['hot_C'])+d['cold_mass_g']*d['water_cp_J_per_g_K']*(t-d['cold_C'])+d['cup_heat_capacity_J_per_K']*(t-d['cold_C'])+d['loss_J'])
        t=bisect(energy,-100,200)
        return dict(final_C=t,hot_heat_released_J=-d['hot_mass_g']*d['water_cp_J_per_g_K']*(t-d['hot_C']))
    if ident=='decay-chain':
        a=math.log(2)/d['half_life_A_hours'];b=math.log(2)/d['half_life_B_hours']
        final=rk4(lambda t,y:[-a*y[0],a*y[0]-b*y[1],b*y[1]],[d['initial_A'],0,0],d['time_hours'])
        return dict(amount_A=final[0],amount_B=final[1],amount_stable=final[2])
    if ident=='fall-with-drag':
        terminal=d['g_m_per_s2']*d['mass_kg']/d['drag_kg_per_s'];decay=d['drag_kg_per_s']/d['mass_kg']
        t=bisect(lambda t:1-math.exp(-decay*t)-d['terminal_fraction'],0,100)
        final=rk4(lambda t,y:[d['g_m_per_s2']-decay*y[0],y[0]],[0,0],t)
        return dict(terminal_speed_m_per_s=terminal,time_s=t,distance_m=final[1])
    if ident=='reaction-temperature':
        loga=math.log(d['k_reference_per_min'])+d['activation_kJ_per_mol']*1000/(d['R_J_per_mol_K']*(d['reference_C']+273.15))
        k=math.exp(loga-d['activation_kJ_per_mol']*1000/(d['R_J_per_mol_K']*(d['target_C']+273.15)))
        return dict(k_target_per_min=k,time_to_conversion_min=math.log(1/(1-d['conversion']))/k,half_life_min=math.log(2)/k)
    if ident=='inventory-decision':
        values=[]
        for q in range(d['max_order']+1):
            cost=d['purchase']*q;revenue=0;shortage=0
            for p,v in zip(d['probabilities'],d['demands']):
                sold=min(q,v);revenue+=p*(sold*d['sale']+(q-sold)*d['salvage']);shortage+=p*(v-sold)
            values.append((revenue-cost-shortage*d['shortage_penalty'],shortage))
        best=max(v[0] for v in values);q=next(i for i,v in enumerate(values) if abs(v[0]-best)<1e-9)
        return dict(order_quantity=q,expected_profit=values[q][0],expected_shortage=values[q][1])
    if ident=='network-reliability':
        # Inclusion-exclusion of overlapping path events, not component enumeration.
        success=0;expected=0
        for mask in range(1,2**len(d['paths'])):
            selected=[path for i,path in enumerate(d['paths']) if mask&(1<<i)];components=set(i for path in selected for i in path)
            prob=math.prod(d['component_probabilities'][i] for i in components)
            success+=prob*(1 if len(selected)%2 else -1)
            if len(selected)==1: expected+=prob
        return dict(system_success_probability=success,expected_working_paths=expected)
    if ident=='sequential-testing':
        disease=d['prior'];healthy=1-d['prior']
        for s,c,z in zip(d['sensitivities'],d['specificities'],d['results']):
            disease*=s if z else 1-s;healthy*=1-c if z else c
        return dict(posterior=disease/(disease+healthy),evidence_probability=disease+healthy)
    if ident=='binomial-option':
        dt=d['years']/d['steps'];q=(math.exp(d['annual_continuous_rate']*dt)-d['down'])/(d['up']-d['down']);value=0;n=d['steps']
        for j in range(n+1):
            probability=math.comb(n,j)*q**j*(1-q)**(n-j);stock=d['spot']*d['up']**j*d['down']**(n-j)
            value+=probability*max(stock-d['strike'],0)
        return dict(risk_neutral_up_probability=q,european_call_price=value*math.exp(-d['annual_continuous_rate']*d['years']))
    if ident=='weighted-regression':
        meanx=sum(w*x for w,x in zip(d['weights'],d['x']))/sum(d['weights']);meany=sum(w*y for w,y in zip(d['weights'],d['y']))/sum(d['weights'])
        slope=sum(w*(x-meanx)*(y-meany) for w,x,y in zip(d['weights'],d['x'],d['y']))/sum(w*(x-meanx)**2 for w,x in zip(d['weights'],d['x']))
        a=meany-slope*meanx
        return dict(intercept=a,slope=slope,prediction=a+slope*d['predict_x'])
    if ident=='tank-dilution':
        v=d['volume_L'];q=d['inflow_L_per_min'];o=d['outflow_L_per_min'];t=d['time_min'];salt=rk4(lambda t,y:[q*d['incoming_kg_per_L']-o*y[0]/(v+(q-o)*t)],[d['initial_salt_kg']],t)[0];volume=v+(q-o)*t
        return dict(final_volume_L=volume,final_salt_kg=salt,final_concentration_kg_per_L=salt/volume)
    raise ValueError('Unknown reference task')


def program(problem):
    # Send only the relevant independent calculation, not all twenty solvers.
    import ast
    tree=ast.parse(inspect.getsource(solve))
    function=tree.body[0]
    branch=next(node for node in function.body if isinstance(node,ast.If) and node.test.comparators[0].value==problem.task_id)
    function.body=branch.body
    source='import math\n'+inspect.getsource(bisect)+'\n'+inspect.getsource(rk4)+'\n'+ast.unparse(tree)
    return source+'\nprint(solve('+repr(problem.task_id)+','+repr(problem.inputs)+'))\n'
