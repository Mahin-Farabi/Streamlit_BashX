import streamlit as st

st.set_page_config("BMI Calculator",layout="wide",page_icon="assets\\logo.ico")
st.title("BMI Calculator")

unit = st.selectbox("Height Unit",["Meter","Feet and Inches"])

if unit == "Meter":
    height = st.number_input("Height (m)", value=1.500, step=0.001, format="%.3f")
else:
    feet = st.number_input("Feet", step=1, min_value=0,value=4)
    inches = st.number_input("Inches", step=1, min_value=0, max_value=11)
    height = (feet * 12 + inches) * 0.0254

weight = st.number_input("Weight (kg)", step=1.00, format="%.2f",value=45.00)


bmi = weight / (height ** 2)

if bmi:
    st.write(f"Your BMI is: {bmi:.2f}")

if bmi < 18.5:
    st.write("Output Category: Underweight ")
    st.write("Health Context: This indicates the body weight is lower than what is considered healthy for the height. It may suggest a need for a nutritional assessment to ensure adequate caloric and nutrient intake.")

elif 18.5 <= bmi <= 24.9:
    st.write("Output Category: Normal / Healthy Weight")
    st.write("Health Context: This range is associated with the lowest statistical risk for developing weight-related chronic conditions (like type 2 diabetes or cardiovascular disease).")
elif 25 <= bmi <= 29.9:
    st.write("Output Category: Overweight")
    st.write("Health Context: Being in this category means carrying extra weight relative to height. It is often a signal to evaluate lifestyle habits, though it doesn't automatically mean a person is unhealthy, as muscle mass can skew this number.")
else:
    st.write("Output Category: Obesity")
    st.write("Health Context: This indicates a higher concentration of body fat relative to height, which statistically increases the risk of metabolic and cardiovascular health conditions.")