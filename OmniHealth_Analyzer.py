from google.cloud import aiplatform
import streamlit
import datetime
import plotly.graph_objects as go
from fpdf import FPDF

PROJECT_ID = "cardiovascular-ai-model"
REGION = "us-central1"   
CARDIO_ENDPOINT_ID = "1647445550896775168" 
METABOLIC_ENDPOINT_ID = "558753117538091008" 
RENAL_ENDPOINT_ID = "3922942039183851520"
SYSTEMIC_ENDPOINT_ID = "1707100653773389824"

cardio_score=0
metabolic_score=0
renal_score=0

aiplatform.init(project=PROJECT_ID, location=REGION)

cardioendpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{CARDIO_ENDPOINT_ID}"
)

metabolicendpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{METABOLIC_ENDPOINT_ID}"
)

renalendpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{RENAL_ENDPOINT_ID}"
)

systemicendpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{SYSTEMIC_ENDPOINT_ID}"
)

def draw_spider_chart(c, m, r, s):
    line_color = '#007BFF'
    fill_color = 'rgba(0, 123, 255, 0.3)'
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[float(c), float(m), float(r), float(s), float(c)],
        theta=['Cardiovascular', 'Metabolic', 'Renal', 'Systemic', 'Cardiovascular'],
        fill='toself',
        fillcolor=fill_color,
        line=dict(color=line_color, width=3),
        marker=dict(size=8, color=line_color),
        name='Health Scores'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#EEEEEE",
            ),
            angularaxis=dict(
                gridcolor="#EEEEEE",
                rotation=90,
                direction="clockwise"
            )
        ),
        showlegend=False,
        height=350,
        margin=dict(l=50, r=50, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def get_attr_str(response):
    try:
        if not hasattr(response, 'explanations') or not response.explanations:
            return "\nFeature Attribution: Not available"
        
        attrs = response.explanations[0].attributions[0].feature_attributions
        attr_dict = dict(attrs)
        
        sorted_attrs = sorted(attr_dict.items(), key=lambda x: abs(float(x[1])), reverse=True)
        
        return "\nFeature Attribution:\n" + "\n".join([f"- {k}: {float(v):.4f}" for k, v in sorted_attrs])
    except:
        return "\nFeature Attribution: Not available"

def bp_recommendation(sbp_str, dbp_str):
    try:
        sbp = float(sbp_str)
        dbp = float(dbp_str)
    except ValueError:
        return "Invalid", "Invalid blood pressure input. Please enter numeric values."

    if sbp >= 160 or dbp >= 100:
        return "Very High", (
            "Blood pressure is dangerously above healthy levels. Immediate medical evaluation is necessary."
        )

    elif sbp >= 140 or dbp >= 90:
        return "Stage 2 HTN", (
            "Blood pressure is significantly elevated and is a major driver for heart, kidney, and stroke risk. "
            "Lifestyle plus medical evaluation is highly recommended."
        )

    elif sbp >= 130 or dbp >= 80:
        return "Stage 1 HTN", (
            "Blood pressure is mildly high. Lifestyle changes should be prioritized including sodium reduction, "
            "regular aerobic exercise, weight control, and at-home BP tracking. If these levels are persistent, "
            "medical evaluation is advised."
        )

    elif sbp >= 120 and dbp < 80:
        return "Elevated", (
            "Blood pressure is slightly above ideal levels. However, this is a great stage to reverse risk with "
            "lifestyle habits such as reducing salty/processed foods, increasing activity, improving sleep, "
            "and managing stress."
        )

    else:
        return "Optimal", (
            "Blood pressure is in an excellent range. Maintain regular physical activity, a balanced diet, "
            "moderate sodium intake, good sleep, and stress control to keep it in this zone."
        )


def ldl_recommendation(ldl_str):
    try:
        ldl = float(ldl_str)    
    except ValueError:
        return "Invalid", "Invalid LDL input. Please enter numeric values."

    if ldl >= 190:
        return "Very High", (
            "LDL is high and significantly increases cardiovascular risk. Strong lifestyle changes and a medical "
            "review is recommended."
        )

    elif ldl >= 160:
        return "High", (
            "LDL is high and significantly increases cardiovascular risk. Strong lifestyle changes and a medical "
            "review is recommended."
        )

    elif ldl >= 130:
        return "Borderline High", (
            "LDL is above the ideal range. Reduce saturated and trans fats, increase soluble fiber, "
            "and monitor trends to prevent further risk."
        )

    elif ldl >= 100:
        return "Near Optimal", (
            "LDL is close to ideal levels. Slight dietary changes such as more plant fiber and fewer fried foods "
            "can shift this into the optimal range."
        )

    else:
        return "Optimal", (
            "LDL cholesterol is excellent. Continue eating fiber-rich foods, healthy fats, "
            "and engaging in regular activity."
        )


def crp_recommendation(crp_str):
    try:
        crp = float(crp_str)    
    except ValueError:
        return "Invalid", "Invalid CRP input. Please enter numeric values."

    if crp > 3:
        return "High", (
            "Chronic inflammation appears high. Medical review and lifestyle optimization are important "
            "and suggested."
        )

    elif crp >= 1:
        return "Moderate", (
            "Inflammation is slightly elevated. Lifestyle optimization may reduce long-term risk."
        )

    else:
        return "Low", (
            "Inflammation appears low. Maintain good sleep, activity, and nutrition."
        )

def fasting_glucose_recommendation(glucose):
    try:
        glucose = float(glucose)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
    if glucose >= 126:
        return "Diabetes", (
            "Fasting glucose is in the diabetic range. This level requires persistent glucose management "
            "and medical evaluation to prevent long-term systemic and organ damage."
        )

    elif glucose >= 100:
        return "Prediabetes", (
            "Fasting glucose is elevated into the prediabetes range. This is a critical stage where lifestyle "
            "changes such as reducing refined carbohydrates, increasing physical activity, improving sleep, "
            "and controlling weight are highly important towards slowing progression."
        )

    else:
        return "Optimal", (
            "Fasting glucose is currently in the healthy range. Maintain balanced nutrition, regular physical "
            "activity, good sleep, and stress management to continue retaining normal glucose control."
        )

def hba1c_recommendation(hba1c):
    try:
        hba1c = float(hba1c)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if hba1c >= 6.5:
        return "Diabetes", (
            "HbA1c is in the diabetic range, indicating chronic hyperglycemia. Medical supervision and a "
            "structured diabetes management plan is strongly advised."
        )

    elif hba1c >= 5.7:
        return "Prediabetes", (
            "HbA1c is in the prediabetes range, indicating prolonged elevated blood sugar. Targeted lifestyle "
            "improvements such as weight control and consistent exercise are strongly recommended to improve "
            "current health."
        )

    else:
        return "Normal", (
            "HbA1c levels reflect healthy long-term glucose control. Continue current diet, physical activity, "
            "and health habits."
        )

def homa_ir_recommendation(homa_ir):
    try:
        homa_ir = float(homa_ir)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if homa_ir > 3.0:
        return "Severe Resistance", (
            "Severe insulin resistance is present and is strongly associated with metabolic syndrome and "
            "diabetes risk. Strong lifestyle changes and a professional clinical metabolic evaluation is "
            "recommended."
        )

    elif homa_ir >= 2.0:
        return "Insulin Resistance", (
            "Insulin resistance is developing. Reducing refined carbohydrates, increasing resistance training, "
            "optimizing sleep, and managing stress can significantly improve insulin sensitivity."
        )

    else:
        return "Normal Sensitivity", (
            "Insulin sensitivity appears normal. Maintain healthy body composition, regular activity, and "
            "balanced nutrition to retain metabolic efficiency."
        )


def bmi_recommendation(bmi):
    try:
        bmi = float(bmi)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if bmi >= 30.0:
        return "Obese", (
            "Body weight is in the obesity range and significantly increases the risk of diabetes and "
            "cardiovascular issues. A structured weight reduction program and medical guidance is strongly "
            "recommended."
        )

    elif bmi >= 25.0:
        return "Overweight", (
            "Body weight is above the ideal range. Gradual weight reduction through nutrition optimization "
            "and increased physical activity is recommended to reduce metabolic strain."
        )

    else:
        return "Healthy", (
            "Body weight is in a healthy range. Continue current activity patterns and nutritional habits to "
            "maintain long-term metabolic health."
        )


def waist_circumference_recommendation(waist_cm):
    try:
        waist_cm = float(waist_cm)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if waist_cm >= 102:
        return "High Risk", (
            "Central obesity is elevated and is strongly linked to insulin resistance and metabolic syndrome. "
            "Targeted abdominal fat reduction via daily activity and dietary fixes is suggested."
        )
    else:
        return "Low Risk", (
            "Central body fat is at a healthy level. Maintain regular physical activity and balanced nutrition "
            "to retain low visceral fat levels."
        )

def egfr_recommendation(egfr):
    try:
        egfr = float(egfr)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if egfr < 15:
        return "Kidney Failure", (
            "Kidney function is critically compromised. Immediate medical management is required."
        )

    elif egfr < 30:
        return "Severely Decreased", (
            "Kidney filtration is severely under healthy ranges. This represents advanced chronic kidney "
            "disease and requires close medical supervision."
        )

    elif egfr < 60:
        return "Moderately Decreased", (
            "Moderate reduction in kidney function is present. This increases cardiovascular and metabolic "
            "risk. Medical monitoring, dietary sodium and protein moderation, and strict blood pressure and "
            "glucose control are advised."
        )

    elif egfr < 90:
        return "Mildly Decreased", (
            "Kidney filtration capabilities are slightly below healthy levels. This may reflect early kidney "
            "stress. Hydration, blood pressure control, glucose control, and regular monitoring are "
            "recommended in this stage."
        )

    else:
        return "Normal", (
            "Kidney filtration capabilities are in the healthy range. Maintain adequate hydration, balanced "
            "nutrition, blood pressure control, and avoid excessive NSAID use to retain current kidney "
            "function."
        )


def creatinine_recommendation(scr):
    try:
        scr = float(scr)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if scr >= 2.0:
        return "High", (
            "Creatinine is significantly elevated, indicating impaired kidney function. Medical evaluation "
            "and close monitoring is required."
        )

    elif scr >= 1.3:
        return "Mildly Elevated", (
            "Creatinine is mildly elevation, suggesting early kidney stress. Hydration, blood pressure "
            "control, and avoidance of nephrotoxic medications are recommended."
        )

    else:
        return "Normal", (
            "Creatinine levels are in the healthy range, indicating normal kidney filtration. Maintain "
            "hydration and avoid unnecessary kidney strain."
        )

def uric_acid_recommendation(uric_acid):
    try:
        uric_acid = float(uric_acid)    
    except ValueError:
        return "Invalid", "Invalid glucose input. Please enter numeric values."
   
    if uric_acid >= 9.0:
        return "High", (
            "Uric acid is significantly elevated and is associated with gout and kidney injury risk. "
            "Medical evaluation and dietary intervention is strongly recommended."
        )
    elif uric_acid >= 7.0:
        return "Elevated", (
            "Uric acid is elevated, increasing the risk of gout and kidney stress. Hydration, limiting red "
            "meat and sugary beverages, and moderating alcohol intake is recommended."
        )
    else:
        return "Normal", (
            "Uric acid is within a healthy range. Maintain hydration and balanced protein intake to retain "
            "renal and metabolic health."
        )

def cardio_recommendation(sbp, dbp, hr, crp, ldl):
    bp_cat, bp_msg = bp_recommendation(sbp, dbp)
    ldl_cat, ldl_msg = ldl_recommendation(ldl)
    crp_cat, crp_msg = crp_recommendation(crp)
    
    instances = [{
        "SBP_mean": str(float(sbp)),    
        "DBP_mean": str(float(dbp)),      
        "HR": str(float(hr)),      
        "CRP": str(float(crp)),   
        "LDL": str(float(ldl))  
    }]
    
    bounds = {"lower": "N/A", "upper": "N/A"}
    try:
        response = cardioendpoint.explain(instances=instances)
        pred = response.predictions[0]
        attr_text = get_attr_str(response)
        if isinstance(pred, dict):
            bounds["lower"] = pred.get("lower_bound", "N/A")
            bounds["upper"] = pred.get("upper_bound", "N/A")
    except Exception:
        try:
            response = cardioendpoint.predict(instances=instances)
            pred = response.predictions[0]
            attr_text = "\nFeature Attribution: Not available"
            if isinstance(pred, dict):
                bounds["lower"] = pred.get("lower_bound", "N/A")
                bounds["upper"] = pred.get("upper_bound", "N/A")
        except Exception as e:
            return "0.0", f"Cardio Endpoint Error: {str(e)}", "Not available", bounds

    predicted_score = pred["value"] if isinstance(pred, dict) else pred
    combined_msg = f"{bp_cat}: {bp_msg}\n{ldl_cat}: {ldl_msg}\n{crp_cat}: {crp_msg}"
    return str(predicted_score), combined_msg, attr_text, bounds


def metabolic_recommendation(glucose, hba1c, homa, bmi, waist):
    g_cat, glucose_msg = fasting_glucose_recommendation(glucose)
    a_cat, hba1c_msg = hba1c_recommendation(hba1c)
    h_cat, homa_msg = homa_ir_recommendation(homa)
    b_cat, bmi_msg = bmi_recommendation(bmi)
    w_cat, waist_msg = waist_circumference_recommendation(waist)
    
    instances = [{
        "Glucose": str(float(glucose)),
        "HbA1c": str(float(hba1c)),
        "HOMA_IR": str(float(homa)),
        "BMI": str(float(bmi)),
        "Waist": str(float(waist))
    }]
    
    bounds = {"lower": "N/A", "upper": "N/A"}
    try:
        response = metabolicendpoint.explain(instances=instances)
        pred = response.predictions[0]
        attr_text = get_attr_str(response)
        if isinstance(pred, dict):
            bounds["lower"] = pred.get("lower_bound", "N/A")
            bounds["upper"] = pred.get("upper_bound", "N/A")
    except Exception:
        try:
            response = metabolicendpoint.predict(instances=instances)
            pred = response.predictions[0]
            attr_text = "\nFeature Attribution: Not available"
            if isinstance(pred, dict):
                bounds["lower"] = pred.get("lower_bound", "N/A")
                bounds["upper"] = pred.get("upper_bound", "N/A")
        except Exception as e:
            return "0.0", f"Metabolic Endpoint Error: {str(e)}", "Not available", bounds

    predicted_score = pred["value"] if isinstance(pred, dict) else pred
    combined_msg = f"{g_cat}: {glucose_msg}\n{a_cat}: {hba1c_msg}\n{h_cat}: {homa_msg}\n{b_cat}: {bmi_msg}\n{w_cat}: {waist_msg}"
    return str(predicted_score), combined_msg, attr_text, bounds


def renal_recommendation(egfr, scr, ua):
    e_cat, egfr_msg = egfr_recommendation(egfr)
    s_cat, scr_msg = creatinine_recommendation(scr)
    u_cat, ua_msg = uric_acid_recommendation(ua)

    instances = [{
        "eGFR": str(float(egfr)),    
        "Scr": str(float(scr)), 
        "UA": str(float(ua))
    }]
    
    bounds = {"lower": "N/A", "upper": "N/A"}
    try:
        response = renalendpoint.explain(instances=instances)
        pred = response.predictions[0]
        attr_text = get_attr_str(response)
        if isinstance(pred, dict):
            bounds["lower"] = pred.get("lower_bound", "N/A")
            bounds["upper"] = pred.get("upper_bound", "N/A")
    except Exception:
        try:
            response = renalendpoint.predict(instances=instances)
            pred = response.predictions[0]
            attr_text = "\nFeature Attribution: Not available"
            if isinstance(pred, dict):
                bounds["lower"] = pred.get("lower_bound", "N/A")
                bounds["upper"] = pred.get("upper_bound", "N/A")
        except Exception as e:
            return "0.0", f"Renal Endpoint Error: {str(e)}", "Not available", bounds

    predicted_score = pred["value"] if isinstance(pred, dict) else pred
    combined_msg = f"{e_cat}: {egfr_msg}\n{s_cat}: {scr_msg}\n{u_cat}: {ua_msg}"
    return str(predicted_score), combined_msg, attr_text, bounds


def health_recommendation(sbp, dbp, hr, crp, ldl, glucose, hba1c, homa, bmi, waist, egfr, scr, ua, smoke, alcohol, pamet, sleep):
    cs, cardio, c_attr, c_bounds = cardio_recommendation(sbp, dbp, hr, crp, ldl)
    ms, metabolic, m_attr, m_bounds = metabolic_recommendation(glucose, hba1c, homa, bmi, waist)
    rs, renal, r_attr, r_bounds = renal_recommendation(egfr, scr, ua)
    cardiomessage=str(cs)+"\n\n"+cardio
    metabolicmessage=str(ms)+"\n\n"+metabolic
    renalmessage=str(rs)+"\n\n"+renal

    instances = [{
        "Cardio_Score_0_100": str(float(cs)),      
        "Metabolic_Score_0_100": str(float(ms)),      
        "Renal_Score_0_100": str(float(rs)),
        "Smoking_cat": str(float(smoke)),      
        "Alcohol_dpweek": str(float(alcohol)),      
        "PA_MET_min_week": str(float(pamet)),      
        "Sleep_hours": str(float(sleep)),        
        "Lifestyle_Modifier": "1.0"      
    }]

    s_bounds = {"lower": "N/A", "upper": "N/A"}
    try:
        response = systemicendpoint.explain(instances=instances)
        pred = response.predictions[0]
        s_attr = get_attr_str(response)
        if isinstance(pred, dict):
            s_bounds["lower"] = pred.get("lower_bound", "N/A")
            s_bounds["upper"] = pred.get("upper_bound", "N/A")
    except Exception:
        try:
            response = systemicendpoint.predict(instances=instances)
            pred = response.predictions[0]
            s_attr = "\nFeature Attribution: Not available"
            if isinstance(pred, dict):
                s_bounds["lower"] = pred.get("lower_bound", "N/A")
                s_bounds["upper"] = pred.get("upper_bound", "N/A")
        except Exception as e:
            return "0.0", f"Systemic Endpoint Error: {str(e)}", 0, 0, 0, "", "", "", {}, {}, {}, {}

    systemic_score = pred["value"] if isinstance(pred, dict) else pred
    
    if isinstance(pred, dict) and "Systemic_Score_0_100_LifestyleAdj" in pred:
        systemic_score = pred["Systemic_Score_0_100_LifestyleAdj"]

    report = f"""
PREDICTED OVERALL HEALTH SCORE: {systemic_score} 
{s_attr}

──────────────────────────────────────────────────
PREDICTED CARDIO SCORE: {cardiomessage} 
{c_attr}

──────────────────────────────────────────────────
PREDICTED METABOLIC SCORE: {metabolicmessage} 
{m_attr}

──────────────────────────────────────────────────
PREDICTED RENAL SCORE: {renalmessage}
{r_attr}
"""
    return str(systemic_score), report, cs, ms, rs, cardio, metabolic, renal, c_bounds, m_bounds, r_bounds, s_bounds
    

streamlit.set_page_config(page_title = "OmniHealth Analyzer", layout = "wide", page_icon = "🩺")
streamlit.title("OmniHealth Analyzer 🩺")
streamlit.markdown("AI-Driven Systemic Risk Scoring")
streamlit.info("Input clinical biomarkers and lifestyle information to recieve Organ-Specific and Systemic Health scoring")

col1, col2, col3, col4 = streamlit.columns(4)

with col1:
    streamlit.subheader("Cardiovascular")
    sbp_value = streamlit.text_input("Systolic BP", "120")
    dbp_value = streamlit.text_input("Diastolic BP", "80")
    hr_value = streamlit.text_input("Resting Heart Rate", "72")
    crp_value = streamlit.text_input("CRP", "1.0")
    ldl_value = streamlit.text_input("LDL", "100")

with col2:
    streamlit.subheader("Metabolic")
    glucose_value = streamlit.text_input("Glucose", "90")
    hba1c_value = streamlit.text_input("HbA1c", "5.4")
    homair_value = streamlit.text_input("HOMA-IR", "1.5")
    bmi_value = streamlit.text_input("BMI", "22.5")
    waist_value = streamlit.text_input("Waist (cm)", "85")

with col3:
    streamlit.subheader("Renal")
    egfr_value = streamlit.text_input("eGFR", "95")
    sc_value = streamlit.text_input("SCR", "0.9")
    ua_value = streamlit.text_input("UA", "5.0")

with col4:
    streamlit.subheader("Lifestyle")
    smoking_value = streamlit.text_input("Smoking Status: 1=No, 9=Yes", "0")
    alcohol_value = streamlit.text_input("Alcohol Drinks Per Week", "0")
    pamet_value = streamlit.text_input("Physical Activity MET Minutes Per Week", "600")
    sleephrs_value = streamlit.text_input("Sleep Hours", "8")

streamlit.divider()

if streamlit.button("Run Systemic Analysis", type = "primary", use_container_width=True):
    with streamlit.spinner("Running Analysis"):

        systemic_score, final_report, cs, ms, rs, cardio_msg, metabolic_msg, renal_msg, cb, mb, rb, sb = health_recommendation(
            sbp_value, dbp_value, hr_value, crp_value, ldl_value,
            glucose_value, hba1c_value, homair_value, bmi_value, waist_value,
            egfr_value, sc_value, ua_value, 
            smoking_value, alcohol_value, pamet_value, sleephrs_value
        )

        streamlit.success("Analysis Complete!")

        out_col1, out_col2, out_col3, out_col4 = streamlit.columns(4)
        with out_col1:
            streamlit.subheader("Systemic")
            streamlit.plotly_chart(draw_spider_chart(cs, ms, rs, systemic_score), use_container_width=True)
            streamlit.metric("SCORE", round(float(systemic_score)))

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Courier", size=10)
            
            pdf.cell(200, 10, txt=f"OMNIHEALTH ANALYZER REPORT", ln=True)
            pdf.cell(200, 10, txt=f"REPORT GENERATED: {now}", ln=True)
            pdf.cell(200, 10, txt="="*50, ln=True)
            pdf.set_font("Courier", 'B', 10)
            pdf.cell(200, 10, txt="INPUT BIOMARKERS & LIFESTYLE DATA:", ln=True)
            pdf.set_font("Courier", size=9)
            
            input_summary = [
                f"CARDIO: SBP: {sbp_value}, DBP: {dbp_value}, HR: {hr_value}, CRP: {crp_value}, LDL: {ldl_value}",
                f"METABOLIC: Glucose: {glucose_value}, HbA1c: {hba1c_value}, HOMA-IR: {homair_value}, BMI: {bmi_value}, Waist: {waist_value}",
                f"RENAL: eGFR: {egfr_value}, SCR: {sc_value}, UA: {ua_value}",
                f"LIFESTYLE: Smoker: {smoking_value}, Alcohol/wk: {alcohol_value}, PA METs: {pamet_value}, Sleep: {sleephrs_value}"
            ]
            
            for item in input_summary:
                pdf.cell(200, 5, txt=item, ln=True)
            
            pdf.cell(200, 10, txt="="*50, ln=True)
            pdf.set_font("Courier", size=10)

            pdf_lines = final_report.split('\n')
            for line in pdf_lines:
                clean_line = line.replace('──────────────────────────────────────────────────', '-'*50)
                
                if "OVERALL HEALTH SCORE" in clean_line:
                    pdf.multi_cell(0, 5, txt=f"{clean_line} (Bound: {sb['lower']} - {sb['upper']})".encode('latin-1', 'replace').decode('latin-1'))
                elif "CARDIO SCORE" in clean_line:
                    pdf.multi_cell(0, 5, txt=f"{clean_line} (Bound: {cb['lower']} - {cb['upper']})".encode('latin-1', 'replace').decode('latin-1'))
                elif "METABOLIC SCORE" in clean_line:
                    pdf.multi_cell(0, 5, txt=f"{clean_line} (Bound: {mb['lower']} - {mb['upper']})".encode('latin-1', 'replace').decode('latin-1'))
                elif "RENAL SCORE" in clean_line:
                    pdf.multi_cell(0, 5, txt=f"{clean_line} (Bound: {rb['lower']} - {rb['upper']})".encode('latin-1', 'replace').decode('latin-1'))
                else:
                    pdf.multi_cell(0, 5, txt=clean_line.encode('latin-1', 'replace').decode('latin-1'))
            
            pdf_output = pdf.output(dest='S').encode('latin-1')

            streamlit.download_button(
                label="Download PDF Report",
                data=pdf_output,
                file_name=f"OmniHealth_Report_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            streamlit.caption(f"Analysis valid as of {now}")

        with out_col2:
            streamlit.subheader("Cardiovascular")
            streamlit.metric("SCORE", round(float(cs)))
            formatted_cardio = cardio_msg.replace("\n", "\n\n")
            streamlit.info(formatted_cardio)

        with out_col3:
            streamlit.subheader("Metabolic")
            streamlit.metric("SCORE", round(float(ms)))
            formatted_metabolic = metabolic_msg.replace("\n", "\n\n")
            streamlit.info(formatted_metabolic)

        with out_col4:
            streamlit.subheader("Renal")
            streamlit.metric("SCORE", round(float(rs)))
            formatted_renal = renal_msg.replace("\n", "\n\n")
            streamlit.info(formatted_renal)

streamlit.divider()
streamlit.caption("OmniHealth Analyzer Clinical Report")