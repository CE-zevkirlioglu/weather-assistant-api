import gradio as gr, json
from predict import predict_rain
def advice(res):
    return ('🌧️ Şemsiye al! ' if res['label']=='Rain' else '☀️ Yağmur beklenmiyor. ')+ (f"(p={res['proba']:.2f})" if res['proba'] is not None else '')
def run(t,h,w,p,c):
    res=predict_rain({'temp':t,'humidity':h,'wind_speed':w,'pressure':p,'clouds':c})
    return json.dumps(res,ensure_ascii=False), advice(res)
with gr.Blocks() as app:
    gr.Markdown('# Personal Weather Assistant')
    t=gr.Number(value=22,label='Temp °C'); h=gr.Number(value=70,label='Humidity %')
    w=gr.Number(value=4.0,label='Wind m/s'); p=gr.Number(value=1010,label='Pressure hPa'); c=gr.Number(value=60,label='Clouds %')
    btn=gr.Button('Predict'); out1=gr.Textbox(label='Prediction'); out2=gr.Textbox(label='Advice')
    btn.click(run,[t,h,w,p,c],[out1,out2])
app.launch()
