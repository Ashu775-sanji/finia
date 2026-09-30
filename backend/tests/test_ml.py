from app.ml.engine import detect,forecast
def test_detect_low_without_history():assert detect(20,'Food',[])['risk_level']=='low'
def test_forecast_shape():assert len(forecast([{'amount':100,'date':'2026-08-01','transaction_type':'expense'}]))==3
