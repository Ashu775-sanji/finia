from collections import Counter,defaultdict
from statistics import mean,pstdev
import math

def _z_score(amount:float,values:list[float])->float:
    return min(1.0,abs(amount-mean(values))/(4*(pstdev(values) or 1))) if len(values)>2 else .12

def detect(amount:float,category:str,history:list[dict])->dict:
    """Ensemble anomaly score: robust Z-score + Isolation Forest + LOF."""
    values=[abs(float(x['amount'])) for x in history if x.get('category')==category]
    z=_z_score(abs(amount),values)
    iso=lof=z
    if len(values)>=8:
        try:
            import numpy as np
            from sklearn.ensemble import IsolationForest
            from sklearn.neighbors import LocalOutlierFactor
            x=np.array(values,dtype=float).reshape(-1,1); point=np.array([[abs(amount)]])
            model=IsolationForest(contamination='auto',random_state=42).fit(x)
            iso=float(1/(1+math.exp(3*float(model.decision_function(point)[0]))))
            neighbors=max(2,min(10,len(values)-1)); joined=np.vstack([x,point])
            labels=LocalOutlierFactor(n_neighbors=neighbors,contamination='auto').fit_predict(joined)
            raw=-float(LocalOutlierFactor(n_neighbors=neighbors,novelty=True).fit(x).decision_function(point)[0])
            lof=float(1/(1+math.exp(-raw))) if labels[-1]==-1 else max(.1,float(1/(1+math.exp(-raw)))-.2)
        except Exception: pass
    score=min(.99,.45*z+.35*iso+.20*lof);risk='high' if score>=.72 else 'medium' if score>=.42 else 'low'
    baseline=mean(values) if values else abs(amount);delta=((abs(amount)/baseline)-1)*100 if baseline else 0
    reasons=[]
    if abs(delta)>30: reasons.append(f'amount {abs(delta):.0f}% {"above" if delta>0 else "below"} category norm')
    if len(values)<3: reasons.append('limited merchant/category history')
    reasons.append(f'ensemble: Z {z:.2f}, IF {iso:.2f}, LOF {lof:.2f}')
    return {'score':round(score,3),'score_100':round(score*100),'risk_level':risk,'reason':' · '.join(reasons),'components':{'z_score':round(z,3),'isolation_forest':round(iso,3),'local_outlier_factor':round(lof,3)}}

def forecast(history:list[dict],months:int=3)->list[dict]:
    monthly=defaultdict(float)
    for x in history:
        if x.get('transaction_type')=='expense': monthly[str(x['date'])[:7]]+=abs(float(x['amount']))
    vals=list(monthly.values());base=mean(vals[-3:]) if vals else 0
    if len(vals)>=4:
        try:
            import numpy as np
            from sklearn.ensemble import RandomForestRegressor
            X=np.arange(len(vals)).reshape(-1,1);model=RandomForestRegressor(n_estimators=120,random_state=42,min_samples_leaf=1).fit(X,vals)
            preds=model.predict(np.arange(len(vals),len(vals)+months).reshape(-1,1)).tolist()
        except Exception: preds=[base]*months
    else:
        growth=((vals[-1]/vals[-2])-1) if len(vals)>1 and vals[-2] else 0
        preds=[base*((1+max(-.2,min(.2,growth)))**i) for i in range(1,months+1)]
    return [{'month_ahead':i+1,'predicted':round(v,2),'lower':round(v*.94,2),'upper':round(v*1.06,2),'confidence':round(max(.65,.94-(i+1)*.07),2),'model':'Random Forest' if len(vals)>=4 else 'Trend baseline'} for i,v in enumerate(preds)]

def guard_score(income:float,expenses:float,anomaly_rate:float=.08,budget_ratio:float=.75,volatility:float=.18)->dict:
    savings=max(0,min(1,(income-expenses)/income)) if income else 0
    parts={'savings_behavior':min(100,savings*220),'budget_adherence':max(0,100-budget_ratio*35),'spending_stability':max(0,100-volatility*160),'emergency_fund':78,'anomaly_frequency':max(0,100-anomaly_rate*300)}
    score=parts['savings_behavior']*.25+parts['budget_adherence']*.25+parts['spending_stability']*.20+parts['emergency_fund']*.15+parts['anomaly_frequency']*.15
    return {'guard_score':round(score),'components':{k:round(v) for k,v in parts.items()},'savings_rate':round(savings*100,1)}
