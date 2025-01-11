import io
import pdfplumber
import re
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = 'your_unique_secret_key'
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text
def extract_values(text):
    values = {
    "Haemoglobin": 0,
    "Total RBC Count": 0,
    "Packed Cell Volume / Hematocrit": 0,
    "MCV": 0,
    "MCH": 0,
    "MCHC": 0,
    "RDW": 0,
    "Total Leucocytes Count": 0,
    "Neutrophils": 0,
    "Lymphocytes": 0,
    "Eosinophils": 0,
    "Monocytes": 0,
    "Basophils": 0,
    "Absolute Neutrophil Count": 0,
    "Absolute Lymphocyte Count": 0,
    "Absolute Eosinophil Count": 0,
    "Absolute Monocyte Count": 0,
    "Platelet Count": 0,
    "Erythrocyte Sedimentation Rate": 0,
    "Fasting Plasma Glucose": 0,
    "Glycated Hemoglobin": 0,
    "Triglycerides": 0,
    "Total Cholesterol": 0,
    "LDL Cholesterol": 0,
    "HDL Cholesterol": 0,
    "VLDL Cholesterol": 0,
    "Total Cholesterol / HDL Cholesterol Ratio": 0,
    "LDL Cholesterol / HDL Cholesterol Ratio": 0,
    "Total Bilirubin": 0,
    "Direct Bilirubin": 0,
    "Indirect Bilirubin": 0,
    "SGPT/ALT": 0,
    "SGOT/AST": 0,
    "Alkaline Phosphatase": 0,
    "Total Protein": 0,
    "Albumin": 0,
    "Globulin": 0,
    "Protein A/G Ratio": 0,
    "Gamma Glutamyl Transferase": 0,
    "Creatinine": 0,
    "e-GFR (Glomerular Filtration Rate)": 0,
    "Urea": 0,
    "Blood Urea Nitrogen": 0,
    "Uric Acid": 0,
    "T3 Total": 0,
    "T4 Total": 0,
    "TSH Ultrasensitive": 0,
    "Vitamin B12": 0,
    "25 (OH) Vitamin D2 (Ergocalciferol)": 0,
    "25 (OH) Vitamin D3 (Cholecalciferol)": 0,
    "Vitamin D Total (D2 + D3)": 0,
    "Iron": 0,
    "Total Iron Binding Capacity": 0,
    "Transferrin Saturation": 0
}
    print(len(values))
    patterns = {
        "Haemoglobin": r"\s*(.*?Haemoglobin\b.*?|Hgb\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total RBC Count": r"\s*(.*?\bR.?B.?C\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Packed Cell Volume / Hematocrit": r"\s*(.*?Packed Cell Volume.*?|.*?Hematocrit.*?|.*?\bP.?C.?V\b.*?|.*?\bH.?c.?t\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "MCV": r"\s*(\bM.?C.?V\b.*?|.*?Mean Corpuscular Volume.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "MCH": r"\s*(\bMCH\b.*?|.*?Mean Corpuscular Hemoglobin.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "MCHC": r"\s*(\bMCHC\b.*?|.*?Mean Corpuscular Hemoglobin Concentration.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "RDW": r"\s*(\bR.?D.?W\b.*?|.*?Red Cell Distribution Width.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total Leucocytes Count": r"\s*(.*?Total Leucocytes Count.*?|.*?TLC.*?|\bWBC\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Neutrophils": r"\s*(Neutrophils|Neu)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Lymphocytes": r"\s*(Lymphocytes|Lym)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Eosinophils": r"\s*(Eosinophils|Eos)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Monocytes": r"\s*(Monocytes|Mono)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Basophils": r"\s*(Basophils|Baso)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Absolute Neutrophil Count": r"\s*(.*?Absolute Neutrophil Count.*?|.*?|Neutrophil\b.*?|ANC)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Absolute Lymphocyte Count": r"\s*(.*?Absolute Lymphocyte Count.*?|.*?Lymphocyte\b.*?|ALC)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Absolute Eosinophil Count": r"\s*(.*?Absolute Eosinophil Count.*?|.*?Eosinophil\b.*?|AEC)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Absolute Monocyte Count": r"\s*(.*?Absolute Monocyte Count.*?|.*?Monocyte\b.*?|AMC)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Platelet Count": r"\s*(Platelet Count|PLT)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Erythrocyte Sedimentation Rate": r"\s*(.*?Erythrocyte sedimentation.*?|.*?Erythrocyte Sedimentation Rate.*?|\bESR\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Fasting Plasma Glucose": r"\s*(.*?Fasting Plasma Glucose.*?|.*?Fasting.*?|.*?Fasting Blood Glucose.*?|.*?\bFPG\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Glycated Hemoglobin": r"\s*(.*?Glycated Haemoglobin.*?|.*?Glycated Hemoglobin.*?|\bHbA1C\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Triglycerides": r"\s*(.*?Triglycerides.*?|.*?TG\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total Cholesterol": r"\s*(Total Cholesterol|TC)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "LDL Cholesterol": r"\s*(L.?D.?L Cholesterol|\bL.?D.?L\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "HDL Cholesterol": r"\s*(H.?D.?L Cholesterol|\bH.?D.?L\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "VLDL Cholesterol": r"\s*(V.?L.?D.?L Cholesterol|\bV.?L.?D.?L\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total Cholesterol / HDL Cholesterol Ratio": r"\s*(.*?Total Cholesterol.?/.?HDL.*?|.*?Total Cholesterol.?/.?HDL Cholesterol Ratio.*?|.*?TC.?/.?HDL.?Ratio.*?|.*?CHOL.?/.?HDL\b.*?|.*?CHO.?/.?HDL\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "LDL Cholesterol / HDL Cholesterol Ratio": r"\s*(LDL Cholesterol / HDL Cholesterol Ratio|LDL/HDL Ratio)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total Bilirubin": r"\s*(.*?Total.?Bilirubin.?|.*?BILIRUBIN.*?Total.*?|.*?BIL-T.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Direct Bilirubin": r"\s*(.*?Direct.?Bilirubin.?|.*?BILIRUBIN.*?direct.*?|.*?BIL-D.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Indirect Bilirubin": r"\s*(.*?Indirect.?Bilirubin.?|.*?BILIRUBIN.*?indirect.*?|.*?BIL-I.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "SGPT/ALT": r"\s*(.*?S.?G.?P.?T.*?|.*?A.?L.?T.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "SGOT/AST": r"\s*(.*?S.?G.?O.?T.*?|.*?A.?S.?T.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Alkaline Phosphatase": r"\s*(.*?Alkaline.*?|.*?Alkaline Phosphatase.*?|ALP)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total Protein": r"\s*(.*?Total Protein.*?|.*?Protein\b.*?|PROTEIN, TOTAL|TP)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Albumin": r"\s*(Albumin|ALB)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Globulin": r"\s*(.*?Globulin.*?|.*?GLO.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Protein A/G Ratio": r"\s*(Protein A/G Ratio|A/G Ratio)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Gamma Glutamyl Transferase": r"\s*(Gamma Glutamyl Transferase|GAMMA GLUTAMYL|GAMMA GLUTAMYL TRANSPEPTIDASE\b.*?|G.?G.?T)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Creatinine": r"\s*(Creatinine\b.*?|Cr)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "e-GFR (Glomerular Filtration Rate)": r"\s*(\be-GFR\b.*?|.*?\beGFR\b.*?|.*?eGFR\b.*?|Glomerular Filtration Rate)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Urea": r"\s*(Urea|Urea.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Blood Urea Nitrogen": r"\s*(Blood Urea Nitrogen|.*?UREA NITROGEN.*?|Blood Urea Nitrogen.*?|.*?BUN.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Uric Acid": r"\s*(Uric Acid|Uric Acid.*?|UA)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "T3 Total": r"\s*(.*?T3.*?Total.*?|Triiodothyronine|.*?T3\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "T4 Total": r"\s*(.*?T4.*?Total.*?|.*?T4\b.*?|Thyroxine)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "TSH Ultrasensitive": r"\s*(\bTSH\b.*?|Ultrasensitive TSH)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Vitamin B12": r"\s*(Vitamin B12|\bB12\b.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "25 (OH) Vitamin D2 (Ergocalciferol)": r"\s*(25 \(OH\) |.*?Vitamin D2.*?|Ergocalciferol)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "25 (OH) Vitamin D3 (Cholecalciferol)": r"\s*(25 \(OH\) Vitamin D3|.*?Vitamin D3.*?|Cholecalciferol)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Vitamin D Total (D2 + D3)": r"\s*(.*?Vitamin D\b.*?|.*?Vitamin D Total.*?|D2\s*\+?\s*D3.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Iron": r"\s*(Iron)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Total Iron Binding Capacity": r"\s*(.*?Total Iron Binding Capacity.*?|.*?T.?I.?B.?C.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*",
        "Transferrin Saturation": r"\s*(.*?Transferrin Saturation.*?|.*?% OF SATURATION.*?|.*?Transferin.*?)\s*[:\-]?\s*(\d+(\.\d+)?)\s*"
    }
    for test, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            values[test] = float(match.group(2))
    return values

def give_health_advice(values):
    advice = []
    # Haemoglobin (range: 13.0-17.0 g/dL)
    if "Haemoglobin" in values:
        if values["Haemoglobin"] < 13.0:
            advice.append("""Low Hemoglobin

   Root Cause: 
     Iron Deficiency: Lack of sufficient iron for red blood cell production.
     Vitamin B12 or Folate Deficiency: Both are essential for red blood cell formation and maturation.
     Blood Loss: Heavy menstruation, gastrointestinal bleeding (e.g., ulcers, hemorrhoids), or surgery.
     Chronic Diseases: Kidney disease, chronic infections, or inflammation.
     Genetic Conditions: Thalassemia, sickle cell disease.
     Poor Diet: Inadequate intake of nutrients that support hemoglobin production.

   Tips: 
     Increase Iron Intake: Iron is critical for hemoglobin production. Iron supplements may be prescribed, but you should always follow the guidance of a healthcare provider.
     Address Vitamin B12 and Folate Deficiency: If low levels of vitamin B12 or folate are detected, supplements or dietary changes can help.
     Treat Underlying Conditions: If blood loss or a chronic disease is the cause, it’s important to address the root cause (e.g., treating ulcers, managing kidney disease).
     Avoid Tea/Coffee with Meals: Tannins in tea and coffee can inhibit iron absorption. 
     Consult a Doctor for Diagnosis: Persistent symptoms may require additional tests to diagnose specific causes of anemia.
   
   Foods to Eat:
     Iron-Rich Foods (heme iron from animal sources and non-heme iron from plant sources):
       Heme Iron: Red meat (beef, lamb), poultry (chicken, turkey), pork, fish, shellfish (clams, oysters, mussels).
       Non-Heme Iron: Spinach, lentils, beans, tofu, quinoa, chickpeas, fortified cereals, pumpkin seeds, and fortified plant-based milk.
     Vitamin B12-Rich Foods: Eggs, dairy products (milk, yogurt, cheese), meat, fish (salmon, tuna), shellfish, fortified cereals.
     Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, avocado, beans, peas, lentils, fortified cereals, and pasta.
     Vitamin C-Rich Foods (to enhance iron absorption):
       Citrus fruits (oranges, grapefruits), strawberries, bell peppers, broccoli, tomatoes, kiwi, and Brussels sprouts.

   Example Meal Plan to Boost Hemoglobin:
   Breakfast: Fortified cereal with almond milk, topped with fresh strawberries (rich in vitamin C) and a boiled egg.
   Lunch: Spinach and lentil salad with citrus dressing (for vitamin C absorption).
   Snack: A handful of pumpkin seeds and a citrus fruit (orange or kiwi).
   Dinner: Grilled chicken with quinoa and steamed broccoli (rich in iron and vitamin C).

By focusing on these dietary changes, you can support your body’s ability to increase hemoglobin levels and improve overall health. However, if symptoms persist, it’s crucial to consult with a healthcare provider for further evaluation and potential treatment.""")
        elif values["Haemoglobin"] > 17.0:
            advice.append("""High Hemoglobin (Polycythemia)

   Root Cause:
     Dehydration: When you're dehydrated, the plasma (liquid) component of your blood decreases, making the concentration of red blood cells appear higher.
     Chronic Lung or Heart Disease: Conditions like chronic obstructive pulmonary disease (COPD) or congenital heart defects can cause low oxygen levels in the blood, leading the body to produce more red blood cells to compensate.
     Living at High Altitudes: At higher altitudes, the oxygen level in the air is lower, and the body compensates by producing more red blood cells.
     Polycythemia Vera: A rare bone marrow disorder where the body makes too many red blood cells, often without a known cause.
     Smoking: Smoking can lead to lower oxygen levels in the blood, prompting the body to produce more red blood cells.
     Tumors or Hormonal Imbalances: Rarely, some tumors or conditions affecting the kidneys (e.g., renal cell carcinoma) can increase erythropoietin production, leading to more red blood cells being produced.

   Tips:
     Hydrate Well: Dehydration is a common cause of high hemoglobin levels. Make sure to drink plenty of water to stay hydrated and maintain proper blood volume.
     Monitor for Underlying Conditions: If you have chronic lung or heart disease, it’s essential to follow your treatment plan. If polycythemia vera is suspected, your healthcare provider will guide you through the necessary diagnostic tests and potential treatments.
     Quit Smoking: If you smoke, quitting can help reduce the body's need for extra red blood cell production. It also improves overall cardiovascular and lung health.
     Regular Check-Ups: If you live at high altitudes or have chronic conditions, regular monitoring of hemoglobin and other blood parameters will help manage your health more effectively.
     Consult a Doctor: If your hemoglobin is significantly high and there are symptoms like headaches, dizziness, or a reddened complexion, see a healthcare professional to rule out conditions like polycythemia vera or other blood disorders.

   Foods to Eat:
     Iron-Rich Foods: While high hemoglobin can sometimes be linked to excess iron (which is a concern in some cases), you should focus on eating a balanced diet and avoid iron-rich supplements unless advised by your doctor.
     Foods to Support Hydration: 
       Water-Rich Foods: Cucumbers, watermelon, celery, oranges, and strawberries can help keep you hydrated.
       Electrolyte-Rich Foods: Include potassium-rich foods like bananas, sweet potatoes, and leafy greens to maintain fluid balance and hydration.
     Avoid Excessive Iron: Since the body may already have sufficient iron, avoid excessive consumption of iron-rich foods or supplements unless prescribed. 

   Example Meal Plan for High Hemoglobin (Polycythemia):
   Breakfast: Oatmeal with almond milk and fresh fruit (e.g., strawberries and blueberries) for antioxidants, paired with a glass of water.
   Lunch: A salad with mixed greens (for hydration), cucumber, and tomato, with a light dressing. Add a source of lean protein (e.g., chicken or tofu) for balance.
   Snack: A water-based smoothie with hydrating fruits like watermelon or cucumber and a few spinach leaves for additional hydration.
   Dinner: Grilled salmon (rich in healthy fats but not iron-loaded) with steamed vegetables like broccoli and zucchini. Drink plenty of water during meals.

Note: While dietary adjustments can help manage some causes of high hemoglobin, underlying medical conditions (e.g., polycythemia vera or chronic lung disease) require specialized care and management by a healthcare provider.""")

    # Total RBC Count (range: 4.5-5.5 million cells/μL)
    if "Total RBC Count" in values:
        if values["Total RBC Count"] < 4.5:
            advice.append(""" Low Total RBC Count (Erythropenia)

Root Cause:
    Anemia: Low RBC count is often caused by anemia, which can result from iron, vitamin B12, or folate deficiencies, chronic disease, or blood loss.
    Nutritional Deficiencies: Lack of iron, vitamin B12, or folate can impair RBC production.
    Chronic Inflammatory Conditions: Chronic infections, autoimmune diseases, or kidney disease can suppress RBC production.
    Bone Marrow Disorders: Conditions like aplastic anemia or leukemia affect the bone marrow’s ability to produce RBCs.
    Excessive Blood Loss: Surgery, gastrointestinal bleeding (e.g., ulcers), or heavy menstrual periods.
    Kidney Disease: Since the kidneys produce erythropoietin (a hormone that stimulates RBC production), kidney dysfunction can result in low RBC count.
    Genetic Disorders: Conditions like thalassemia, sickle cell anemia, and other hereditary disorders can lead to low RBC production.

Tips:
    Increase Iron Intake: Iron is crucial for RBC production. Consider iron-rich foods or supplements as advised by your doctor.
    Supplement with Vitamin B12 and Folate: If these deficiencies are detected, your doctor may recommend supplements to support RBC production.
    Treat the Underlying Cause: If blood loss or a chronic disease is contributing to low RBC count, addressing the root cause is essential (e.g., treating ulcers, managing kidney disease).
    Monitor for Symptoms of Anemia: Symptoms like fatigue, pale skin, shortness of breath, and dizziness should be discussed with your healthcare provider.

Foods to Eat:
    Iron-Rich Foods (Heme and Non-Heme Iron):
    Heme Iron: Red meat (beef, lamb), poultry (chicken, turkey), fish (salmon, tuna), liver.
    Non-Heme Iron: Spinach, lentils, chickpeas, beans, quinoa, tofu, fortified cereals, pumpkin seeds.
    Vitamin B12-Rich Foods: Eggs, dairy (milk, yogurt, cheese), meat, fish (salmon, tuna), shellfish, fortified cereals.
    Folate-Rich Foods: Leafy greens (spinach, kale), avocado, beans, lentils, citrus fruits, fortified cereals.
    Vitamin C-Rich Foods (to enhance iron absorption): Citrus fruits, bell peppers, broccoli, strawberries, kiwi, and tomatoes.

Example Meal Plan for Low RBC Count:
    Breakfast: Fortified cereal with almond milk, topped with fresh strawberries (rich in vitamin C) and a boiled egg.
    Lunch: Spinach and lentil salad with citrus dressing to enhance iron absorption.
    Snack: A handful of pumpkin seeds and an orange for extra vitamin C.
    Dinner: Grilled chicken with quinoa and steamed broccoli.""")
        elif values["Total RBC Count"] > 5.5:
            advice.append("""High Total RBC Count (Polycythemia)

Root Cause:
    Dehydration: When the body is dehydrated, plasma (the liquid part of blood) decreases, making the concentration of RBCs appear higher.
    Polycythemia Vera: A rare blood disorder in which the bone marrow produces too many RBCs, often without an identifiable cause.
    Chronic Low Oxygen Levels: Conditions like chronic lung disease (COPD), heart disease, or living at high altitudes can cause the body to compensate by producing more RBCs to increase oxygen transport.
    Smoking: Smoking reduces oxygen levels in the blood, which may lead the body to produce more RBCs.
    Tumors: Certain tumors, especially kidney tumors, can secrete erythropoietin (a hormone that stimulates RBC production), leading to an elevated RBC count.

Tips:
    Hydrate Properly: Dehydration is a common cause of high RBC counts. Drink plenty of water throughout the day.
    Quit Smoking: Smoking can decrease oxygen levels in the blood, prompting the body to produce more RBCs. Quitting smoking can improve overall health.
    Follow Up with Your Doctor: High RBC counts should be evaluated further. If polycythemia vera or chronic diseases are suspected, your doctor will guide you through the necessary tests and treatments.
    Avoid Excessive Iron: If you are diagnosed with polycythemia, reducing iron intake may be necessary, as high iron levels could contribute to the overproduction of RBCs.

Foods to Eat:
    Water-Rich Foods: Cucumbers, watermelon, celery, oranges, strawberries, and bell peppers can help keep you hydrated.
    Electrolyte-Rich Foods: Bananas, sweet potatoes, spinach, and avocados to maintain hydration and electrolyte balance.
    Iron-Rich Foods (if advised): In some cases of high RBC count, it may be important to avoid excessive iron intake. However, balanced consumption of iron is fine unless your doctor advises otherwise.
    Antioxidant-Rich Foods: Foods high in antioxidants, like berries (blueberries, raspberries, blackberries), leafy greens, tomatoes, and nuts, may help reduce oxidative stress and inflammation.
    Low-Sodium Foods: Since high RBC counts can be associated with dehydration, avoid excessive salt, which can contribute to fluid retention.

Example Meal Plan for High RBC Count:
    Breakfast: Watermelon smoothie with spinach and chia seeds (rich in antioxidants and hydration).
    Lunch: Grilled chicken salad with cucumber, mixed greens, and avocado (hydrating and rich in healthy fats).
    Snack: Fresh strawberries and a handful of nuts.
    Dinner: Baked salmon with roasted sweet potatoes and steamed asparagus.""")

    # Packed Cell Volume / Hematocrit (range: 40-50%)
    if "Packed Cell Volume / Hematocrit" in values:
        if values["Packed Cell Volume / Hematocrit"] < 40:
            advice.append("""Low Packed Cell Volume (PCV) / Hematocrit (Anemia)

Root Cause:
    Iron Deficiency: Inadequate iron affects the production of hemoglobin, leading to a low hematocrit.
    Vitamin B12 or Folate Deficiency: These vitamins are essential for the production and maturation of red blood cells. A deficiency can result in a low hematocrit.
    Blood Loss: Chronic blood loss due to heavy menstruation, gastrointestinal bleeding (e.g., ulcers), or surgery can decrease the hematocrit.
    Chronic Diseases: Kidney disease, cancer, and chronic inflammatory conditions can impair RBC production and cause a low hematocrit.
    Bone Marrow Disorders: Aplastic anemia, leukemia, or other disorders affecting the bone marrow’s ability to produce RBCs can lead to a low hematocrit.
    Hemorrhage: Sudden blood loss, such as from an injury or surgery, can cause a decrease in hematocrit.
    Hydration Status: Overhydration (fluid overload) can dilute blood, artificially lowering hematocrit levels.

Tips:
    Increase Iron Intake: Iron is essential for RBC production. If iron deficiency is the cause, consider taking iron supplements as prescribed by your doctor.
    Supplement with Vitamin B12 and Folate: Deficiencies in these vitamins can contribute to low hematocrit. You may need supplements if your levels are low.
    Treat the Underlying Cause: If blood loss or a chronic disease is the cause, treat the underlying condition (e.g., managing ulcers, controlling kidney disease).
    Avoid Excessive Fluids: If low hematocrit is due to overhydration, limit your fluid intake and consult your doctor for advice on fluid balance.
    Monitor for Symptoms: Symptoms like fatigue, dizziness, pale skin, or shortness of breath should be reported to your healthcare provider.

Foods to Eat:
    Iron-Rich Foods
    Heme Iron (animal sources): Red meat, poultry, fish, shellfish, and liver.
    Non-Heme Iron (plant-based): Lentils, beans, tofu, quinoa, spinach, pumpkin seeds, and fortified cereals.
    Vitamin B12-Rich Foods: Eggs, dairy products, fish (salmon, tuna), poultry, fortified cereals.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, fortified cereals.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, broccoli, strawberries, and tomatoes to enhance iron absorption.

Example Meal Plan for Low Hematocrit:
    Breakfast: Fortified cereal with almond milk, topped with fresh strawberries (rich in vitamin C) and a boiled egg for protein.
    Lunch: Spinach and lentil salad with a citrus vinaigrette to help with iron absorption.
    Snack: A handful of pumpkin seeds and an orange.
    Dinner: Grilled chicken with quinoa and steamed broccoli.""")
        elif values["Packed Cell Volume / Hematocrit"] > 50:
            advice.append("""High Packed Cell Volume (PCV) / Hematocrit

Root Cause:
Dehydration: When the body is dehydrated, the plasma (liquid part of blood) decreases, leading to a relative increase in RBC concentration, causing high hematocrit.
Polycythemia Vera: A bone marrow disorder where the body overproduces red blood cells, resulting in a high hematocrit.
Chronic Lung Disease (COPD): Low oxygen levels in the blood can stimulate the bone marrow to produce more RBCs to increase oxygen transport.
Living at High Altitudes: The body compensates for lower oxygen levels in the air by producing more RBCs to improve oxygen delivery.
Smoking: Smoking reduces oxygen in the blood, leading to an increase in RBC production.
Heart Disease: Some heart conditions that result in low oxygen levels can lead to a high hematocrit as the body attempts to compensate for insufficient oxygen.
Tumors: Some tumors (especially kidney tumors) can secrete erythropoietin (EPO), which stimulates RBC production.

Tips:
Hydrate Properly: Dehydration is a common cause of high hematocrit. Drinking plenty of fluids can help reduce the concentration of red blood cells in the blood.
Avoid Smoking: Smoking reduces the amount of oxygen in the blood, stimulating the production of more RBCs. Quitting smoking can help normalize hematocrit levels.
Manage Underlying Conditions: If high hematocrit is due to chronic lung or heart disease, follow your treatment plan. If polycythemia vera is suspected, your healthcare provider may recommend blood donation or other treatments.
Consult Your Doctor: High hematocrit can be a sign of serious conditions like polycythemia vera or chronic lung disease. It’s important to consult your healthcare provider for proper diagnosis and management.
Regular Monitoring: If you live at high altitudes, regular monitoring of hematocrit levels is necessary. You may need to make lifestyle adjustments or take medications to manage high hematocrit.

Foods to Eat:
Hydrating Foods:
Water-Rich Foods: Cucumbers, watermelon, celery, oranges, strawberries, bell peppers, and lettuce help maintain hydration.
Electrolyte-Rich Foods: Bananas, sweet potatoes, spinach, and avocados can help balance fluids and electrolytes in the body.
Avoid Excessive Iron: If you have a high hematocrit, limit your intake of iron-rich foods unless advised otherwise, as high iron can exacerbate RBC production.
Anti-Inflammatory Foods: Foods rich in antioxidants and omega-3 fatty acids, like berries, nuts, and fatty fish (e.g., salmon, mackerel), can help manage inflammation and improve blood health.
Low-Sodium Foods: Since high hematocrit can be related to dehydration, avoid excess salt to prevent fluid retention.

Example Meal Plan for High Hematocrit:
    Breakfast: Oatmeal with fresh berries and chia seeds, paired with a large glass of water.
    Lunch: Grilled chicken salad with cucumber, avocado, mixed greens, and a light vinaigrette dressing.
    Snack: A handful of almonds and a glass of coconut water for hydration.
    Dinner: Grilled salmon with steamed sweet potatoes and roasted vegetables (zucchini, asparagus, bell peppers).
""")

    # MCV (range: 83-101 fL)
    if "MCV" in values:
        if values["MCV"] < 83:
            advice.append("""Low Mean Corpuscular Volume (MCV) / Microcytic Anemia

Root Cause:
    Iron Deficiency Anemia: The most common cause of low MCV is a lack of iron, which is essential for the production of hemoglobin in red blood cells.
    Chronic Blood Loss: Conditions like heavy menstruation, gastrointestinal bleeding (e.g., ulcers, hemorrhoids), or surgical blood loss can lead to iron deficiency and microcytic anemia.
    Thalassemia: A genetic disorder that leads to abnormal hemoglobin production, resulting in smaller-than-normal red blood cells.
    Sideroblastic Anemia: A condition in which the bone marrow produces ringed sideroblasts instead of healthy red blood cells due to ineffective iron utilization.
    Lead Poisoning: Lead toxicity can interfere with heme production, leading to microcytic anemia.
    Chronic Diseases: Some chronic illnesses (e.g., chronic inflammation) may interfere with RBC production, leading to low MCV.

Tips:
    Increase Iron Intake: Iron deficiency is a common cause of low MCV, so iron-rich foods or supplements may be necessary (follow your doctor's advice).
    Address Underlying Causes: If blood loss (e.g., ulcers, menstruation) is the cause, managing or treating the condition is crucial.
    Monitor for Thalassemia: If genetic causes like thalassemia are suspected, your doctor will guide you with appropriate tests and management.
    Check for Lead Exposure: If lead poisoning is suspected, immediate treatment and addressing the source of exposure are necessary.
    Ensure Adequate Vitamin C: Vitamin C enhances iron absorption, so consuming foods rich in vitamin C can help in increasing iron levels.

Foods to Eat:
    Iron-Rich Foods
    Heme Iron (from animal sources): Red meat (beef, lamb), poultry (chicken, turkey), liver, and fish.
    Non-Heme Iron (plant-based): Lentils, beans, tofu, quinoa, spinach, pumpkin seeds, and fortified cereals.
    Vitamin C-Rich Foods: Citrus fruits (oranges, grapefruit), bell peppers, strawberries, tomatoes, and broccoli to enhance iron absorption.
    Folate-Rich Foods: Leafy greens (spinach, kale), avocado, beans, lentils, citrus fruits, and fortified cereals.
    Vitamin B12-Rich Foods: Eggs, dairy, and fortified cereals to support overall blood health.

Example Meal Plan for Low MCV:
    Breakfast: Fortified cereal with almond milk, topped with fresh strawberries (rich in vitamin C) and a boiled egg.
    Lunch: Spinach and lentil salad with a citrus dressing to aid in iron absorption.
    Snack: A handful of pumpkin seeds and an orange.
    Dinner: Grilled chicken with quinoa and steamed broccoli.
""")
        elif values["MCV"] > 101:
            advice.append("""High Mean Corpuscular Volume (MCV) / Macrocytic Anemia

Root Cause:
    Vitamin B12 Deficiency: Low levels of vitamin B12 impair the maturation of red blood cells, leading to larger-than-normal cells (macrocytes).
    Folate Deficiency: Like B12, a deficiency in folate affects RBC production and can result in larger cells.
    Alcohol Abuse: Chronic alcohol consumption can interfere with the absorption of B12 and folate, leading to macrocytic anemia.
    Liver Disease: Liver diseases, such as cirrhosis, can lead to an increase in MCV due to changes in RBC production and metabolism.
    Hypothyroidism: An underactive thyroid can slow down red blood cell production, leading to larger red blood cells.
    Medications: Certain medications like chemotherapy drugs, antiretrovirals, and anticonvulsants may affect RBC production and lead to high MCV.
    Bone Marrow Disorders: Conditions like myelodysplastic syndromes can result in abnormal RBC production.

Tips:
    Increase Vitamin B12 and Folate Intake: If B12 or folate deficiency is the cause, your healthcare provider may recommend supplements or dietary changes.
    Limit Alcohol Consumption: Alcohol can interfere with nutrient absorption and exacerbate anemia, so reducing intake is recommended.
    Manage Thyroid Health: If hypothyroidism is the cause, follow the treatment plan prescribed by your doctor to restore normal thyroid function.
    Monitor for Medications: If your medication is affecting MCV, consult your doctor for alternatives or adjustments.
    Treat Underlying Conditions: For liver disease or bone marrow disorders, proper medical care is crucial.

Foods to Eat:
    Vitamin B12-Rich Foods: Eggs, dairy products (milk, yogurt, cheese), fish (salmon, tuna), poultry, shellfish, and fortified cereals.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, fortified cereals, and pasta.
    Iron-Rich Foods: While iron is often not a direct cause of high MCV, it’s still important for overall blood health. Sources include lean meat, beans, tofu, and fortified cereals.
    Healthy Fats and Proteins: Foods like salmon, eggs, nuts, seeds, and avocados support overall health and vitamin absorption.
    Avoid Alcohol: Alcohol can impair nutrient absorption, so reducing alcohol intake is essential for managing high MCV.

Example Meal Plan for High MCV:
    Breakfast: Scrambled eggs with spinach and fortified whole-grain toast (to provide B12 and folate).
    Lunch: Grilled salmon salad with avocado, mixed greens, and citrus dressing.
    Snack: A handful of almonds and a banana.
    Dinner: Roasted chicken with quinoa and steamed broccoli. """)

    # MCH (range: 27-33 pg)
    if "MCH" in values:
        if values["MCH"] < 27:
            advice.append("""Low Mean Corpuscular Hemoglobin (MCH) / Hypochromic Anemia

Root Cause:
    Iron Deficiency Anemia: Low iron levels result in a decrease in hemoglobin production, which leads to smaller and less hemoglobin-rich red blood cells, causing low MCH.
    Thalassemia: A genetic disorder that leads to defective hemoglobin production, resulting in smaller RBCs and low MCH.
    Chronic Blood Loss: Conditions like gastrointestinal bleeding, heavy menstruation, or surgery can result in iron loss, leading to low MCH.
    Vitamin B6 Deficiency: A deficiency in vitamin B6 can lead to impaired hemoglobin synthesis, affecting MCH levels.
    Lead Poisoning: Lead toxicity can interfere with heme production, leading to hypochromic (low MCH) anemia.
    Sideroblastic Anemia: A condition where the bone marrow produces abnormal red blood cells with insufficient hemoglobin.

Tips:
    Increase Iron Intake: Iron deficiency is the most common cause of low MCH, so iron supplements or iron-rich foods can help improve levels.
    Address Underlying Conditions: If chronic blood loss (e.g., from ulcers or heavy menstruation) is the cause, addressing the source of the blood loss is key.
    Increase Vitamin B6: Vitamin B6 is important for hemoglobin production, so ensure adequate intake of foods rich in B6, such as poultry, potatoes, and bananas.
    Check for Lead Exposure: If lead poisoning is suspected, immediate medical treatment and avoiding exposure to lead sources are essential.
    Genetic Counseling: If thalassemia is suspected, genetic counseling and further testing may be required for proper management.

Foods to Eat:
    Iron-Rich Foods
    Heme Iron: Red meat (beef, lamb), poultry (chicken, turkey), fish (salmon, tuna), liver.
    Non-Heme Iron: Lentils, beans, quinoa, tofu, spinach, pumpkin seeds, and fortified cereals.
    Vitamin B6-Rich Foods: Poultry (chicken, turkey), fish, potatoes, bananas, fortified cereals, and chickpeas.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, tomatoes, broccoli, and strawberries, as vitamin C enhances iron absorption.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, lentils, and fortified cereals.
Example Meal Plan for Low MCH:
    Breakfast: Fortified cereal with almond milk, topped with strawberries (rich in vitamin C) and a boiled egg.
    Lunch: Spinach and lentil salad with a citrus dressing to improve iron absorption.
    Snack: A handful of pumpkin seeds and an orange.
    Dinner: Grilled chicken with quinoa and steamed broccoli.""")
        elif values["MCH"] > 32:
            advice.append("""High Mean Corpuscular Hemoglobin (MCH) / Hyperchromic Anemia

Root Cause:
    Vitamin B12 Deficiency: A deficiency in vitamin B12 can impair red blood cell maturation, leading to the production of large, hyperchromic cells with more hemoglobin content.
    Folate Deficiency: Like B12, folate is essential for RBC production, and its deficiency can result in the formation of larger RBCs with a higher concentration of hemoglobin.
    Alcohol Abuse: Chronic alcohol consumption can interfere with the absorption of B12 and folate, leading to the production of larger RBCs with more hemoglobin.
    Liver Disease: Liver conditions like cirrhosis can lead to macrocytic RBCs, which often have a higher hemoglobin content.
    Hypothyroidism: An underactive thyroid can cause larger RBCs with increased hemoglobin, often leading to high MCH.
    Bone Marrow Disorders: Some bone marrow disorders like myelodysplastic syndromes result in the production of RBCs with abnormal characteristics, including high MCH.

Tips:
    Increase Folate and Vitamin B12 Intake: If a deficiency is causing high MCH, supplementation with B12 and folate-rich foods may help. Your healthcare provider may recommend supplements.
    Limit Alcohol Consumption: Alcohol interferes with nutrient absorption, so cutting back or eliminating alcohol may help normalize MCH levels.
    Treat Thyroid Dysfunction: If hypothyroidism is the cause, proper management with thyroid hormone replacement will help normalize MCH levels.
    Monitor Medications: If certain medications are affecting MCH, speak with your doctor about alternatives or adjustments.
    Manage Liver Disease: If liver disease is the cause, working with your healthcare provider to manage the condition is essential.

Foods to Eat:
    Vitamin B12-Rich Foods: Eggs, dairy (milk, yogurt, cheese), fish (salmon, tuna), poultry, shellfish, and fortified cereals.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.
    Iron-Rich Foods: Iron is still essential for overall blood health, so sources like lean meats, beans, tofu, and fortified cereals should be included.
    Healthy Fats: Omega-3 fatty acids from fish (salmon, sardines), flaxseeds, chia seeds, and walnuts can support overall health and vitamin absorption.
    Antioxidant-Rich Foods: Foods like berries (blueberries, raspberries), nuts, and leafy greens can reduce oxidative stress and support overall blood health.

Example Meal Plan for High MCH:
    Breakfast: Scrambled eggs with spinach and fortified whole-grain toast (rich in vitamin B12 and folate).
    Lunch: Grilled salmon salad with avocado, mixed greens, and citrus dressing.
    Snack: A handful of almonds and a banana.
    Dinner: Roasted chicken with quinoa and steamed broccoli.
""")

    # MCHC (range: 320-360 g/dL)
    if "MCHC" in values:
        if values["MCHC"] < 31.5:
            advice.append("""Low Mean Corpuscular Hemoglobin Concentration (MCHC) / Hypochromic Anemia

Root Cause:
    Iron Deficiency Anemia: Iron is essential for the production of hemoglobin in red blood cells. In iron deficiency, RBCs have reduced hemoglobin concentration, causing low MCHC.
    Hereditary Spherocytosis: A genetic condition where RBCs are abnormally shaped (spherical) and have a lower hemoglobin concentration, leading to low MCHC.
    Thalassemia: In thalassemia, defective hemoglobin production leads to a reduced MCHC, with red blood cells having less hemoglobin than normal.
    Chronic Blood Loss: Blood loss due to gastrointestinal bleeding, heavy menstruation, or surgery can lead to iron deficiency and lower hemoglobin levels, which reduces MCHC.
    Sideroblastic Anemia: A type of anemia where the body is unable to incorporate iron into hemoglobin properly, resulting in low MCHC.
    Lead Poisoning: Lead toxicity interferes with heme production, reducing the concentration of hemoglobin in red blood cells.

Tips:
    Increase Iron Intake: Iron is vital for hemoglobin production. Iron supplements or iron-rich foods (under the guidance of your doctor) can help normalize MCHC.
    Address Underlying Blood Loss: If chronic blood loss is the issue (e.g., from ulcers or menstruation), addressing and treating the source of blood loss is critical.
    Monitor for Sideroblastic Anemia or Thalassemia: If a genetic condition is suspected, further tests and appropriate management should be followed.
    Check for Lead Exposure: If lead exposure is the cause, seek medical treatment for lead poisoning and avoid further exposure.
    Ensure Adequate Vitamin C: Vitamin C enhances iron absorption, so it is important to consume vitamin C-rich foods alongside iron-rich meals.

Foods to Eat:
    Iron-Rich Foods:
    Heme Iron: Red meat (beef, lamb), poultry (chicken, turkey), fish (salmon, tuna), liver.
    Non-Heme Iron: Lentils, beans, tofu, quinoa, spinach, pumpkin seeds, and fortified cereals.
    Vitamin C-Rich Foods: Citrus fruits (oranges, grapefruit), bell peppers, tomatoes, broccoli, and strawberries to enhance iron absorption.
    Folate-Rich Foods: Leafy greens (spinach, kale), avocado, beans, lentils, citrus fruits, and fortified cereals.
    Vitamin B12-Rich Foods: Eggs, dairy products, fortified cereals, and fish to support overall blood health.

Example Meal Plan for Low MCHC:
    Breakfast: Fortified cereal with almond milk, topped with strawberries (rich in vitamin C) and a boiled egg.
    Lunch: Spinach and lentil salad with a citrus dressing to improve iron absorption.
    Snack: A handful of pumpkin seeds and an orange.
    Dinner: Grilled chicken with quinoa and steamed broccoli.
""")
        elif values["MCHC"] > 34.5:
            advice.append("""High Mean Corpuscular Hemoglobin Concentration (MCHC) / Hyperchromic Anemia

Root Cause:
    Hereditary Spherocytosis: A genetic condition causing red blood cells to be spherical and more concentrated with hemoglobin, leading to high MCHC.
    Dehydration: Dehydration reduces plasma volume, concentrating red blood cells and resulting in high MCHC values, though this is typically a relative increase.
    Cold Agglutinin Disease: A rare condition where cold temperatures cause the clumping of red blood cells, which can increase MCHC.
    Autoimmune Hemolytic Anemia: The immune system mistakenly attacks and destroys RBCs, leading to an increase in hemoglobin concentration in remaining cells.
    Burns or Severe Trauma: Severe injury or burns can cause fluid loss and hemoconcentration, which can elevate MCHC values.

Tips:
    Hydrate Properly: Dehydration is a common cause of high MCHC. Drink plenty of water throughout the day to maintain proper hydration levels.
    Address Underlying Conditions: If an autoimmune or hemolytic condition is present, work with your doctor to manage the disorder with appropriate medications or treatments.
    Monitor for Hereditary Spherocytosis: If you have a family history or symptoms of hereditary spherocytosis, discuss genetic counseling and management options with your doctor.
    Treat Dehydration: Proper fluid management is crucial to avoid falsely high MCHC due to dehydration. Ensure adequate fluid intake, especially during illness or physical activity.
    Consult for Cold Agglutinin Disease: If suspected, discuss the need for special tests to diagnose and manage cold agglutinin disease.

Foods to Eat:
    Hydrating Foods: Water-rich foods such as cucumbers, watermelon, oranges, and bell peppers can help maintain hydration.
    Electrolyte-Rich Foods: Bananas, sweet potatoes, spinach, and avocados can help balance fluids and electrolytes in the body.
    Anti-inflammatory Foods: To manage autoimmune conditions, include foods rich in omega-3 fatty acids and antioxidants, such as fatty fish (salmon, mackerel), berries, and leafy greens.
    Protein-Rich Foods: Protein supports overall recovery and immune function, so include lean meats, poultry, fish, eggs, and legumes in your diet.
    Avoid Excessive Salt: In cases of dehydration, limiting salt intake can help maintain a proper fluid balance.

Example Meal Plan for High MCHC:
    Breakfast: Oatmeal with chia seeds, blueberries, and almond butter for a hydrating, antioxidant-rich start.
    Lunch: Grilled chicken salad with mixed greens, cucumber, avocado, and a light vinaigrette.
    Snack: A handful of almonds and a banana.
    Dinner: Grilled salmon with quinoa and steamed asparagus.
""")

    # RDW (range: 11.5-14.5%)
    if "RDW" in values:
        if values["RDW"] < 11.6:
            advice.append("""Low Red Cell Distribution Width (RDW)

Root Cause:
    Normal Variation: A low RDW is often not concerning and may simply reflect uniformity in the size of red blood cells (RBCs), which is typically seen in healthy individuals.
    Recent Blood Transfusion: After a blood transfusion, the RDW may temporarily decrease because the transfused red blood cells are of similar size, reducing the overall variation in RBC size.
    Bone Marrow Disorders: Some bone marrow conditions might lead to uniform production of red blood cells, resulting in low RDW values.
    Chronic Diseases: Certain chronic conditions, like some liver diseases, can lead to uniformity in RBC size and, thus, a lower RDW.
    Nutritional Deficiencies (rare): In some cases, low RDW can be associated with mild deficiencies that don't significantly affect RBC production.

Tips:
    No Special Action Needed: In many cases, a low RDW is not a cause for concern and doesn't require treatment unless it is linked to a specific condition.
    Monitor for Transfusion Effects: If you've recently received a blood transfusion, the low RDW may be temporary and will normalize over time.
    Ensure Adequate Nutrition: Maintaining a balanced diet rich in vitamins and minerals supports overall red blood cell health.
    Consult Your Doctor: If low RDW is persistent or associated with other abnormal blood test results, it may warrant further evaluation by a healthcare professional.

Foods to Eat:
    Balanced Diet: Ensure you're getting adequate amounts of vitamins and minerals to support overall health, including B vitamins (B12, folate), iron, and vitamin C.

Example Meal Plan for Low RDW:
    Breakfast: Whole grain toast with avocado, a poached egg, and a side of orange slices for vitamin C.
    Lunch: Grilled chicken salad with mixed greens, tomatoes, carrots, and olive oil dressing for a balanced intake of nutrients.
    Snack: A handful of almonds and a small apple.
    Dinner: Baked salmon with quinoa and steamed broccoli for protein and micronutrients.""")
        elif values["RDW"] > 14:
            advice.append("""High Red Cell Distribution Width (RDW)

Root Cause:
    Iron Deficiency Anemia: One of the most common causes of high RDW is iron deficiency, which leads to the production of both small and large red blood cells, increasing RDW.
    Vitamin B12 or Folate Deficiency: Both B12 and folate are essential for RBC maturation. A deficiency can cause the production of larger-than-normal RBCs, contributing to high RDW.
    Anemia of Chronic Disease: Chronic diseases (such as kidney disease, cancer, or autoimmune disorders) can lead to a mixed population of small and large RBCs, resulting in increased RDW.
    Hemolytic Anemia: Conditions where RBCs are prematurely destroyed (hemolysis) can lead to an increased RDW due to the body producing new RBCs of different sizes.
    Liver Disease: Some liver conditions can cause changes in red blood cell production and lead to increased RDW.
    Bone Marrow Disorders: Conditions like myelodysplastic syndromes can result in abnormal RBC production with variability in cell size, causing high RDW.

Tips:
    Address Nutritional Deficiencies: If the high RDW is due to iron, vitamin B12, or folate deficiencies, work with your doctor to correct the deficiency through supplements or diet.
    Manage Chronic Conditions: If high RDW is associated with chronic diseases (e.g., kidney disease, cancer), proper management of the underlying condition is essential to normalize RDW.
    Monitor for Hemolytic or Bone Marrow Disorders: If hemolytic anemia or bone marrow problems are suspected, further diagnostic tests and treatments may be necessary.
    Hydration: Ensuring proper hydration is important, as dehydration can also affect RDW.

Foods to Eat:
    Iron-Rich Foods:
    Heme Iron: Red meat (beef, lamb), poultry (chicken, turkey), fish (salmon, tuna), liver.
    Non-Heme Iron: Lentils, beans, tofu, spinach, quinoa, fortified cereals, and pumpkin seeds.
    Vitamin B12-Rich Foods: Eggs, dairy (milk, yogurt, cheese), fish (salmon, tuna), and fortified cereals.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, tomatoes, broccoli, and strawberries to enhance iron absorption.
    Healthy Fats: Foods like fatty fish (salmon, sardines), flaxseeds, chia seeds, and walnuts can support overall health and help manage inflammation in chronic diseases.

Example Meal Plan for High RDW:
    Breakfast: Scrambled eggs with spinach and fortified whole-grain toast (to provide vitamin B12 and folate).
    Lunch: Grilled chicken salad with avocado, mixed greens, citrus dressing, and quinoa for a balanced nutrient profile.
    Snack: A handful of pumpkin seeds and a small orange.
    Dinner: Baked salmon with steamed broccoli and a side of quinoa or brown rice.
""")

    # Total Leucocytes Count (range: 4.0-11.0 x10⁹/L)
    if "Total Leucocytes Count" in values:
        if values["Total Leucocytes Count"] < 4000:
            advice.append("""Low Total Leucocyte Count (Leukopenia)

Root Cause:
    Viral Infections: Certain viral infections, such as HIV, influenza, and hepatitis, can suppress bone marrow function and lead to a decrease in white blood cell (WBC) count.
    Autoimmune Disorders: Conditions like lupus or rheumatoid arthritis can cause the immune system to attack the bone marrow, reducing WBC production.
    Bone Marrow Disorders: Disorders like aplastic anemia or myelodysplastic syndromes can affect the bone marrow’s ability to produce WBCs, leading to leukopenia.
    Medications: Some medications, such as chemotherapy, certain antibiotics, antipsychotics, and immunosuppressants, can cause bone marrow suppression, resulting in low WBC count.
    Severe Infections: In some severe or chronic infections, the body’s WBC count may initially rise, but eventually, the bone marrow can become overwhelmed and unable to produce sufficient white blood cells, leading to a drop.
    Nutritional Deficiencies: Deficiencies in essential nutrients like vitamin B12, folate, and copper can impair WBC production and cause low leucocyte counts.
    Radiation Exposure: Exposure to high levels of radiation can damage bone marrow and lead to leukopenia.

Tips:
    Increase Nutrient Intake: Ensure adequate intake of vitamin B12, folate, and zinc, as these are essential for healthy white blood cell production.
    Review Medications: If medications are causing leukopenia, consult with your doctor to adjust or find alternatives.
    Treat Underlying Infections or Conditions: Managing any underlying infections (bacterial or viral) or autoimmune conditions that are causing leukopenia is crucial.
    Avoid Exposure to Infections: A low WBC count increases susceptibility to infections, so take extra precautions to avoid exposure to illness.
    Monitor Bone Marrow Health: If bone marrow disorders are suspected, your doctor may recommend specific tests or treatments to support its function.

Foods to Eat:
    Vitamin B12-Rich Foods: Meat, fish, poultry, eggs, and dairy products to support WBC production.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals to promote healthy red and white blood cells.
    Zinc-Rich Foods: Shellfish (oysters, crab), lean meats (beef, lamb), pumpkin seeds, and beans to support immune function.
    Copper-Rich Foods: Shellfish, seeds, nuts, whole grains, and legumes to assist in the production of white blood cells.
    Protein-Rich Foods: Chicken, turkey, lean beef, eggs, and legumes to support overall immune health.

Example Meal Plan for Low Leucocytes:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in folate).
    Lunch: Grilled chicken with quinoa and a side of leafy greens, including kale and avocado (rich in B12 and folate).
    Snack: A handful of pumpkin seeds and a banana.
    Dinner: Salmon with roasted sweet potatoes and steamed broccoli (rich in zinc and B12).
""")
        elif values["Total Leucocytes Count"] > 10000:
            advice.append("""High Total Leucocyte Count (Leukocytosis)

Root Cause:
    Infections: Bacterial, fungal, or viral infections often trigger an increase in WBC production as the body fights the infection.
    Inflammatory Disorders: Conditions such as rheumatoid arthritis, inflammatory bowel disease, or vasculitis can lead to chronic inflammation and an elevated WBC count.
    Stress Responses: Physical or emotional stress (e.g., trauma, surgery, extreme temperatures) can cause a temporary increase in WBC count.
    Leukemia: Leukemias are cancers of the bone marrow and blood that lead to an overproduction of white blood cells, often causing extremely high WBC counts.
    Allergic Reactions: Severe allergic responses can elevate WBC counts, particularly eosinophils.
    Medications: Corticosteroids, epinephrine, or lithium can lead to increased WBC production.
    Smoking: Smoking can lead to a sustained elevation in white blood cell count, especially neutrophils.

Tips:
    Identify and Treat Infections: If an infection is the cause, appropriate treatment (antibiotics, antivirals, antifungals) should be administered.
    Manage Chronic Inflammatory Conditions: If chronic inflammation or autoimmune disorders are causing leukocytosis, medications to control inflammation may be required.
    Reduce Stress: Practicing stress-reducing techniques, such as meditation, yoga, or regular physical activity, can help lower WBC counts related to stress.
    Consult for Leukemia or Blood Disorders: If leukemia or another hematological disorder is suspected, further diagnostic tests such as bone marrow biopsy may be needed.
    Quit Smoking: Smoking cessation is important, as smoking can lead to long-term increases in WBC counts and worsen inflammation.

Foods to Eat:
    Anti-Inflammatory Foods: Foods like fatty fish (salmon, mackerel), olive oil, nuts (walnuts, almonds), and turmeric help reduce chronic inflammation.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, strawberries, and broccoli help support the immune system and reduce inflammation.
    Antioxidant-Rich Foods: Blueberries, spinach, kale, and other berries help fight oxidative stress and inflammation.
    Whole Grains: Brown rice, quinoa, oats, and barley are rich in fiber, which supports the immune system and reduces inflammation.
    Lean Proteins: Chicken, turkey, tofu, and legumes to maintain immune function without contributing to inflammation.

Example Meal Plan for High Leucocytes:
    Breakfast: Oatmeal with chia seeds, walnuts, and berries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, a side of steamed broccoli, and olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an apple.
    Dinner: Chicken stir-fry with kale, bell peppers, and carrots (rich in vitamin C and fiber).""")

    # Neutrophils (range: 40-70%)
    if "Neutrophils" in values:
        if values["Neutrophils"] < 40:
            advice.append("""Low Neutrophils (Neutropenia)

Root Cause:
    Infections: Viral infections like HIV, hepatitis, influenza, or the Epstein-Barr virus can suppress neutrophil production or lead to their destruction, resulting in neutropenia.
    Bone Marrow Disorders: Conditions such as aplastic anemia, myelodysplastic syndromes, or leukemia can impair bone marrow function, leading to a decrease in neutrophils.
    Autoimmune Diseases: Conditions like systemic lupus erythematosus (SLE) or rheumatoid arthritis can cause the body’s immune system to attack neutrophils, lowering their count.
    Medications: Certain drugs, including chemotherapy, immunosuppressive drugs, or antibiotics (e.g., penicillin), can suppress neutrophil production.
    Nutritional Deficiencies: Deficiencies in vitamin B12, folate, or copper can affect neutrophil production, leading to a low count.
    Severe Infections or Sepsis: In some severe or long-standing infections, the body may lose neutrophils faster than it can produce them, resulting in neutropenia.
    Congenital Disorders: Genetic conditions like cyclic neutropenia or Kostmann syndrome can cause chronic low neutrophil levels.

Tips:
    Increase Nutrient Intake: Ensure adequate intake of vitamin B12, folate, copper, and zinc, which are important for neutrophil production.
    Avoid Infections: With a low neutrophil count, your body’s ability to fight infections is reduced, so take extra precautions to avoid exposure to illness, including frequent hand washing and avoiding large crowds.
    Consult Your Doctor for Medication Adjustments: If medications are the cause of neutropenia, your doctor may suggest alternatives or modify dosages.
    Monitor Bone Marrow Health: If the cause is related to bone marrow disorders, your doctor may recommend further tests or treatments to manage the condition.
    Neutrophil-Stimulating Drugs: In some cases, medications like G-CSF (granulocyte-colony stimulating factor) can be prescribed to stimulate neutrophil production.

Foods to Eat:
    Vitamin B12-Rich Foods: Animal products such as meat, poultry, fish, eggs, and dairy.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.
    Zinc-Rich Foods: Shellfish (oysters, crab), lean meats (beef, lamb), nuts (almonds), and seeds.
    Copper-Rich Foods: Shellfish, nuts, seeds, whole grains, and legumes to support neutrophil production.
    Protein-Rich Foods: Chicken, turkey, tofu, and legumes to maintain overall immune health.

Example Meal Plan for Low Neutrophils:
    Breakfast: Scrambled eggs with spinach and whole-grain toast.
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in B12 and folate).
    Snack: A handful of pumpkin seeds and a small apple.
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli.
""")
        elif values["Neutrophils"] > 80:
            advice.append("""High Neutrophils (Neutrophilia)

Root Cause:
    Infections: Bacterial infections (e.g., pneumonia, appendicitis, sepsis) are a common cause of an elevated neutrophil count, as the body produces more neutrophils to fight the infection.
    Inflammatory Conditions: Chronic inflammation caused by conditions like rheumatoid arthritis, inflammatory bowel disease, or vasculitis can cause neutrophilia.
    Stress Responses: Physical or emotional stress (e.g., surgery, trauma, extreme temperatures) can cause a temporary rise in neutrophils.
    Leukemia: Chronic myelogenous leukemia (CML) and other forms of leukemia can cause an excessive production of neutrophils.
    Smoking: Smoking can increase neutrophil count, particularly neutrophils related to lung inflammation.
    Medications: Medications like corticosteroids, lithium, or epinephrine can stimulate neutrophil production.
    Tissue Damage: Conditions like burns or major trauma can lead to neutrophil production as part of the body’s response to tissue injury.

Tips:
    Treat Infections: If an infection is the underlying cause, work with your doctor to manage it with antibiotics or antiviral medications, as appropriate.
    Control Inflammation: If chronic inflammation is the cause, your doctor may recommend medications like corticosteroids or biologics to reduce inflammation.
    Address Stress: Engage in stress-reducing activities such as meditation, deep breathing exercises, or regular physical activity.
    Avoid Smoking: Smoking cessation can help normalize neutrophil counts and reduce inflammation.
    Monitor for Leukemia or Blood Disorders: If leukemia or other hematological disorders are suspected, your doctor may perform tests such as a bone marrow biopsy to determine the cause.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods such as fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds can help reduce inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts (almonds, walnuts) are high in antioxidants and can help combat oxidative stress.
    Fiber-Rich Foods: Whole grains (brown rice, oats, quinoa) and vegetables help regulate the immune system and reduce systemic inflammation.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, broccoli, and strawberries can help reduce inflammation and support immune function.
    Lean Proteins: Chicken, turkey, tofu, and legumes provide the building blocks for immune cells without contributing to inflammation.

Example Meal Plan for High Neutrophils:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants).
    Lunch: Grilled salmon with quinoa, a side of steamed broccoli, and a salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange.
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).""")

    # Lymphocytes (range: 20-40%)
    if "Lymphocytes" in values:
        if values["Lymphocytes"] < 20:
            advice.append("""Low Lymphocytes (Lymphocytopenia)

Root Cause:
    Viral Infections: Certain viral infections, such as HIV, hepatitis, influenza, and measles, can cause a reduction in lymphocyte count as they directly affect the immune system.
    Autoimmune Diseases: Conditions like systemic lupus erythematosus (SLE) or rheumatoid arthritis can result in low lymphocytes due to the immune system attacking the body's own tissues, including lymphocytes.
    Bone Marrow Disorders: Diseases such as aplastic anemia, leukemia, or myelodysplastic syndromes can affect the bone marrow, reducing the production of lymphocytes.
    Medications: Immunosuppressive drugs, chemotherapy, or corticosteroids can lower lymphocyte count by suppressing immune function.
    Malnutrition: Deficiencies in essential nutrients like protein, zinc, vitamin B12, and folate can impair lymphocyte production.
    Radiation Exposure: High levels of radiation can damage lymphocytes, resulting in a low count.
    Chronic Illnesses: Long-term diseases like chronic kidney disease, liver disease, or other chronic conditions can sometimes lead to a decrease in lymphocytes.

Tips:
    Boost Immune System with Nutrition: Ensure sufficient intake of vitamins and minerals, including vitamin B12, zinc, folate, and protein, to support lymphocyte production.
    Consult Your Doctor about Medications: If immunosuppressive drugs or chemotherapy are the cause, your doctor may adjust dosages or suggest alternatives.
    Treat Underlying Conditions: Effective management of autoimmune diseases, viral infections, or bone marrow disorders may help improve lymphocyte levels.
    Improve Lifestyle: Adequate sleep, regular exercise, and reducing stress can support immune health.
    Prevent Infections: With a low lymphocyte count, your body’s ability to fight infections is weakened, so take extra precautions to avoid exposure to illness, such as frequent hand washing and avoiding crowded places.

Foods to Eat:
    Protein-Rich Foods: Chicken, turkey, tofu, fish, and legumes to support the immune system.
    Vitamin B12 and Folate: Meat, eggs, dairy products, leafy greens (spinach, kale), beans, and lentils to enhance lymphocyte production.
    Zinc-Rich Foods: Shellfish (oysters), lean meats, seeds (pumpkin, sunflower), and nuts (cashews) to improve immune function.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), strawberries, bell peppers, and broccoli to enhance immune health.

Example Meal Plan for Low Lymphocytes:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in folate and B12).
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein, B12, and folate).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli (rich in zinc and vitamin B12).""")
        elif values["Lymphocytes"] > 40:
            advice.append("""High Lymphocytes (Lymphocytosis)

Root Cause:
    Viral Infections: Lymphocytosis is often a result of viral infections, especially those like mononucleosis (Epstein-Barr virus), cytomegalovirus (CMV), and hepatitis, where the body increases lymphocyte production to fight the virus.
    Chronic Inflammatory Conditions: Chronic inflammation or autoimmune diseases, such as rheumatoid arthritis or Crohn's disease, may cause an elevated lymphocyte count as the immune system is activated.
    Leukemia or Lymphoma: Certain types of cancer, such as chronic lymphocytic leukemia (CLL) or lymphoma, can cause a significant increase in lymphocyte count due to uncontrolled production of abnormal lymphocytes.
    Stress Responses: Physical or emotional stress, such as after trauma or surgery, can lead to a temporary increase in lymphocytes.
    Smoking: Smoking has been linked to higher levels of lymphocytes, likely due to inflammation or the body’s response to harmful chemicals in tobacco.
    Medications: Medications like corticosteroids, lithium, or theophylline can occasionally cause lymphocytosis.

Tips:
    Treat Infections: If an infection is identified as the cause, managing the infection with appropriate antiviral or antibiotic treatments is essential.
    Control Inflammation: For autoimmune diseases or chronic inflammatory conditions, medications like immunosuppressants or corticosteroids may be required.
    Monitor for Leukemia or Blood Disorders: If leukemia or lymphoma is suspected, your doctor may perform additional tests such as bone marrow biopsy, flow cytometry, or imaging.
    Manage Stress: Practice stress reduction techniques like meditation, yoga, or deep breathing exercises to help regulate lymphocyte levels.
    Quit Smoking: Smoking cessation can help lower lymphocyte count over time and reduce inflammation.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods such as fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds help reduce inflammation.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, broccoli, and strawberries can help manage inflammation and support immune function.
    Fiber-Rich Foods: Whole grains (brown rice, oats, quinoa) and vegetables like spinach and kale can help regulate the immune system and reduce inflammation.
    Lean Proteins: Chicken, turkey, tofu, and legumes provide the building blocks for immune cells without contributing to inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), green tea, and dark chocolate help combat oxidative stress and inflammation.

Example Meal Plan for High Lymphocytes:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, a side of steamed broccoli, and a salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).""")

        # Eosinophils (range: 1-4%)
    if "Eosinophils" in values:
        if values["Eosinophils"] < 1:
            advice.append("""Low Eosinophils (Eosinopenia)

Root Cause:
    Acute Infections: During acute bacterial or viral infections, the body’s immune system may redirect resources to fight the infection, resulting in a temporary reduction of eosinophils.
    Corticosteroid Medications: Use of corticosteroids or other immunosuppressive drugs can reduce eosinophil counts, as they inhibit the immune response.
    Cushing’s Syndrome: A disorder caused by high levels of cortisol in the body, which may lead to eosinopenia due to cortisol’s suppressive effect on the immune system.
    Stress Responses: Both physical and emotional stress can result in lower eosinophil levels, as stress hormones like cortisol can suppress immune functions.
    Bone Marrow Disorders: Disorders that affect the bone marrow’s ability to produce blood cells, such as aplastic anemia, can lead to low eosinophil counts.
    Hematologic Diseases: Conditions like leukemia or myelodysplastic syndromes may suppress the production of eosinophils in the bone marrow.
    Hypercortisolism: Conditions associated with an excess of cortisol, including tumors of the adrenal gland, can lead to lower eosinophil levels.

Tips:
    Review Medications: If corticosteroids or immunosuppressive drugs are causing eosinopenia, discuss with your doctor about adjusting doses or switching to alternative treatments.
    Manage Stress: Practice stress-reducing activities such as yoga, meditation, or deep breathing exercises to help balance cortisol levels.
    Treat Underlying Conditions: If eosinopenia is caused by a hormonal imbalance or bone marrow issue, specific treatments will be required to address the root cause.
    Avoid Infections: A lower eosinophil count can lead to a reduced immune defense against parasites and other infections, so take extra precautions to avoid illness.

Foods to Eat:
    Protein-Rich Foods: Lean meats, poultry, tofu, and legumes to support overall immune function.
    Vitamin C-Rich Foods: Citrus fruits, bell peppers, strawberries, and broccoli to support immune health.
    Magnesium-Rich Foods: Nuts, seeds, spinach, and whole grains to reduce stress and support cellular function.
    Zinc-Rich Foods: Shellfish (oysters, crab), lean meats, seeds, and legumes to support immune response.

Example Meal Plan for Low Eosinophils:
    Breakfast: Scrambled eggs with spinach and whole-grain toast.
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein and vitamin C).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled salmon with roasted sweet potatoes and steamed broccoli (rich in zinc and magnesium).""")
        elif values["Eosinophils"] > 6:
            advice.append("""High Eosinophils (Eosinophilia)

Root Cause:
    Allergic Reactions: Eosinophils are involved in allergic responses. Conditions like asthma, hay fever, or allergic rhinitis often cause an increase in eosinophil count.
    Parasitic Infections: Eosinophils play a key role in fighting parasitic infections, such as hookworm, roundworm, or giardia. An increase in eosinophils can be a response to these infections.
    Autoimmune Disorders: Conditions like eosinophilic esophagitis or eosinophilic granulomatosis with polyangiitis (EGPA) can cause chronic eosinophil elevation.
    Skin Disorders: Diseases like eczema or dermatitis can result in elevated eosinophils, as they are involved in the inflammatory response.
    Drug Reactions: Certain drugs, such as antibiotics, nonsteroidal anti-inflammatory drugs (NSAIDs), or antihistamines, can lead to drug-induced eosinophilia.
    Hematologic Diseases: Blood disorders such as chronic eosinophilic leukemia or myeloproliferative diseases can cause high eosinophil counts due to abnormal production in the bone marrow.
    Chronic Inflammatory Conditions: Chronic conditions like vasculitis, inflammatory bowel disease (IBD), or chronic rhinosinusitis with nasal polyps can increase eosinophil production.

Tips:
    Identify and Treat Allergies: If an allergy is the cause, managing the allergic response with antihistamines or other medications can help normalize eosinophil levels.
    Treat Parasitic Infections: If a parasitic infection is present, appropriate anti-parasitic treatments such as antiparasitic medications or deworming treatments should be administered.
    Control Inflammation: For autoimmune or inflammatory conditions, corticosteroids, immunosuppressants, or biologic therapies may be used to control eosinophil production.
    Monitor Drug Reactions: If a medication is causing eosinophilia, it may need to be replaced or adjusted by your doctor.
    Manage Underlying Conditions: If blood disorders like chronic eosinophilic leukemia are the cause, specialized treatments like chemotherapy or targeted therapies may be necessary.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), walnuts, and flaxseeds to reduce inflammation.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, strawberries, and broccoli to support immune function and reduce allergic responses.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts to combat oxidative stress.
    Fiber-Rich Foods: Whole grains, vegetables (broccoli, cauliflower), and legumes to support gut health and manage inflammatory bowel diseases.
    Probiotics: Foods like yogurt, kefir, and kimchi to help balance gut bacteria, which can influence inflammatory responses.

Example Meal Plan for High Eosinophils:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Monocytes (range: 2-8%)
    if "Monocytes" in values:
        if values["Monocytes"] < 2:
            advice.append("""Low Monocytes (Monocytopenia)

Root Cause:
    Bone Marrow Disorders: Conditions such as aplastic anemia, myelodysplastic syndromes, or leukemia can affect the bone marrow’s ability to produce monocytes.
    Acute Infections: Infections, especially viral infections (e.g., HIV, influenza, hepatitis), can lead to a decrease in monocytes as the immune system redirects resources to combat the infection.
    Immunosuppressive Drugs: Medications like corticosteroids, chemotherapy, or immunosuppressive drugs can reduce the production of monocytes.
    Corticosteroid Use: Long-term use of corticosteroids can decrease the number of monocytes in the bloodstream.
    Nutritional Deficiencies: Deficiencies in nutrients like folate, vitamin B12, or iron can result in a low monocyte count, as these are crucial for immune cell production.
    Severe Stress: Physical or emotional stress may suppress the production of monocytes, contributing to monocytopenia.
    Genetic Disorders: Rare genetic conditions like congenital neutropenia or other hematological disorders can affect monocyte production.

Tips:
    Consult with Your Doctor: If medications are the cause of monocytopenia, your healthcare provider may adjust dosages or recommend alternatives.
    Address Nutritional Deficiencies: Ensure adequate intake of vitamin B12, folate, and iron, which are essential for the production of monocytes.
    Treat Underlying Conditions: Conditions such as bone marrow disorders or infections may require specific treatments to boost monocyte levels.
    Reduce Stress: Engaging in stress-reduction techniques like meditation, yoga, and regular exercise can help maintain a balanced immune system.

Foods to Eat:
    Iron-Rich Foods: Lean meats, liver, spinach, beans, lentils, and fortified cereals help support blood cell production.
    Vitamin B12-Rich Foods: Animal products such as meat, poultry, fish, eggs, and dairy.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.
    Zinc-Rich Foods: Shellfish, lean meats, seeds, nuts, and legumes to support immune function.
    Protein-Rich Foods: Chicken, fish, tofu, and legumes to support overall immune system function.

Example Meal Plan for Low Monocytes:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in folate and vitamin B12).
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein, vitamin B12, and folate).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli (rich in iron, zinc, and vitamin B12).
""")
        elif values["Monocytes"] > 10:
            advice.append("""High Monocytes (Monocytosis)

Root Cause:
    Chronic Infections: Long-standing infections, especially bacterial infections like tuberculosis, subacute bacterial endocarditis, or brucellosis, can lead to an increase in monocytes.
    Autoimmune Disorders: Conditions such as rheumatoid arthritis, lupus, or inflammatory bowel disease (IBD) can cause chronic inflammation, leading to monocytosis.
    Hematological Disorders: Blood disorders like chronic myelomonocytic leukemia (CMML) or monocytic leukemia can result in elevated monocyte levels due to excessive production in the bone marrow.
    Cancer: Some cancers, including lymphoma and leukemia, can lead to monocytosis as part of the body's response to the malignancy.
    Inflammatory Conditions: Conditions such as vasculitis, sarcoidosis, or inflammatory bowel diseases can elevate monocyte levels.
    Recovery from Acute Infections: Following an acute infection, as the body recovers, monocyte levels may temporarily increase to aid tissue repair and immune system function.
    Stress or Trauma: Physical or emotional stress, major surgeries, or trauma can lead to an elevated monocyte count as part of the body’s immune response.

Tips:
    Identify and Treat Chronic Infections: If a bacterial or parasitic infection is present, antibiotics or other appropriate treatments can help lower monocyte levels.
    Control Autoimmune Diseases: Inflammatory conditions like rheumatoid arthritis or lupus may require corticosteroids or immunosuppressive drugs to reduce inflammation and normalize monocyte levels.
    Address Cancer or Blood Disorders: If cancer or a hematological disorder is the cause, your doctor will prescribe specific treatments, such as chemotherapy or targeted therapy.
    Manage Inflammation: For inflammatory conditions like IBD or vasculitis, anti-inflammatory drugs, including corticosteroids or biologics, can help control elevated monocyte counts.
    Monitor for Recovery from Infections: If monocytosis is a sign of recovery from an infection, regular monitoring of your blood counts can help track the progress.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), olive oil, and flaxseeds can help reduce chronic inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts can help combat oxidative stress and inflammation.
    Fiber-Rich Foods: Whole grains (oats, brown rice), vegetables (broccoli, cauliflower), and legumes to help reduce systemic inflammation.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, and broccoli to enhance immune function and reduce inflammation.
    Lean Proteins: Chicken, turkey, tofu, and legumes to provide necessary nutrients for immune health without promoting excessive inflammation.

Example Meal Plan for High Monocytes:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, a side of steamed broccoli, and a salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Basophils (range: 0.5-1%)
    if "Basophils" in values:
        if values["Basophils"] < 0.5:
            advice.append("""Low Basophils (Basopenia)

Root Cause:
    Acute Infections: During acute bacterial infections or viral infections (e.g., influenza), the body may divert resources toward combating the infection, leading to a temporary decrease in basophils.
    Corticosteroid Use: The use of corticosteroids or other immunosuppressive medications can suppress basophil production, causing a low count.
    Allergic Reactions: Basophils are involved in allergic responses, and during an active allergic reaction, they may migrate to the site of inflammation, leading to a temporary decrease in circulation.
    Severe Stress: Physical or emotional stress may increase the release of stress hormones like cortisol, which can lower basophil counts.
    Hyperthyroidism: An overactive thyroid can lead to changes in the immune system, sometimes reducing basophil levels.
    Bone Marrow Disorders: Conditions affecting the bone marrow's ability to produce cells, such as aplastic anemia or leukemia, can cause a low basophil count.
    Pregnancy: During the later stages of pregnancy, there may be a decrease in basophil count due to hormonal changes.

Tips:
    Review Medications: If corticosteroids or immunosuppressive drugs are causing basopenia, consult with your doctor about adjusting the dosage or finding alternative treatments.
    Manage Stress: Engage in stress-reducing activities such as meditation, yoga, or deep breathing exercises to help normalize cortisol levels.
    Address Thyroid Disorders: If hyperthyroidism is causing basopenia, proper treatment to manage thyroid function is essential.
    Monitor for Infections: During active infections, basophil counts can be temporarily low. Proper treatment of infections with antibiotics or antivirals can restore normal basophil levels.
    Nutritional Support: Ensure you’re consuming a balanced diet to support immune function, including adequate vitamins and minerals.

Foods to Eat:
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), strawberries, bell peppers, and broccoli can support the immune system.
    Protein-Rich Foods: Lean meats, fish, tofu, and legumes help support overall immune function.
    Zinc-Rich Foods: Shellfish (oysters), lean meats, nuts, and seeds for immune support.
    Magnesium-Rich Foods: Nuts, seeds, spinach, and whole grains to support immune system health and reduce stress.

Example Meal Plan for Low Basophils:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in vitamins and minerals).
    Lunch: Grilled chicken with quinoa and a side of steamed broccoli (rich in protein and vitamin C).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled salmon with roasted sweet potatoes and steamed broccoli (rich in zinc and omega-3).
""")
        elif values["Basophils"] > 2:
            advice.append("""High Basophils (Basophilia)

Root Cause:
    Allergic Reactions: Basophils are heavily involved in allergic responses. Conditions like asthma, hay fever, food allergies, or anaphylaxis often cause an increase in basophil counts.
    Chronic Inflammatory Diseases: Conditions such as rheumatoid arthritis, ulcerative colitis, or Crohn’s disease may cause elevated basophils due to chronic inflammation.
    Myeloproliferative Disorders: Disorders such as chronic myelogenous leukemia (CML) or other bone marrow disorders can lead to an excessive production of basophils.
    Hypothyroidism: An underactive thyroid can contribute to an increase in basophils as part of the body’s immune response to hormonal imbalance.
    Infections: Some chronic infections, such as tuberculosis, may cause elevated basophils as part of the body’s immune response.
    Chronic Urticaria: A condition that causes hives, where basophils may be elevated due to ongoing allergic reactions.
    Pregnancy: Basophils may be slightly elevated during pregnancy due to hormonal changes.

Tips:
    Identify and Treat Allergies: If allergies are the cause of high basophils, managing the allergic response with antihistamines, corticosteroids, or other allergy medications can help lower basophil levels.
    Treat Chronic Inflammatory Diseases: If the cause is an inflammatory condition, your doctor may recommend medications such as immunosuppressants, corticosteroids, or biologics.
    Monitor for Myeloproliferative Disorders: If a hematological disorder like chronic myelogenous leukemia (CML) is suspected, further investigation and targeted therapies (e.g., tyrosine kinase inhibitors) will be needed.
    Thyroid Management: If hypothyroidism is the underlying cause, thyroid hormone replacement therapy will help normalize basophil levels.
    Manage Infections: If chronic infections such as tuberculosis are causing elevated basophils, appropriate antimicrobial therapy can help resolve the infection and bring basophil levels back to normal.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds to reduce inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts to combat oxidative stress.
    Fiber-Rich Foods: Whole grains (oats, brown rice), vegetables (broccoli, cauliflower), and legumes to help reduce systemic inflammation.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, strawberries, and broccoli to help reduce inflammation and support immune function.
    Lean Proteins: Chicken, turkey, tofu, and legumes to provide necessary nutrients for immune health without promoting excessive inflammation.

Example Meal Plan for High Basophils:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Absolute Neutrophil Count (range: 1.5-8.0 x10⁹/L) cells/cumm
    if "Absolute Neutrophil Count" in values:
        if values["Absolute Neutrophil Count"] < 2000:
            advice.append("""Low Absolute Neutrophil Count (Neutropenia)

Root Cause:
    Bone Marrow Disorders: Conditions such as aplastic anemia, myelodysplastic syndromes, leukemia, or other bone marrow diseases can impair the production of neutrophils, resulting in neutropenia.
    Autoimmune Disorders: Autoimmune diseases like lupus or rheumatoid arthritis may cause the immune system to attack neutrophils, reducing their count.
    Infections: Certain viral infections (e.g., HIV, hepatitis, influenza) can suppress neutrophil production, leading to low counts.
    Chemotherapy or Radiation: Cancer treatments like chemotherapy and radiation therapy can significantly suppress bone marrow function, resulting in neutropenia.
    Medications: Certain drugs, such as antibiotics, antipsychotics, anticonvulsants, or immunosuppressive medications, can lower neutrophil levels.
    Vitamin Deficiencies: Deficiencies in folate, vitamin B12, or copper can impair the production of neutrophils.
    Severe Infections or Sepsis: In some severe infections, neutrophils are quickly used up, leading to temporarily low neutrophil levels.
    Congenital Conditions: Some inherited conditions, like cyclic neutropenia or congenital neutropenia, can result in chronically low neutrophil counts.

Tips:
    Infection Precautions: Since neutrophils are vital for fighting infections, take extra precautions to avoid infections (e.g., frequent hand washing, avoiding sick individuals, and wearing masks if necessary).
    Monitor for Infections: Regular monitoring of your health and seeking immediate medical attention for any symptoms of infection, such as fever, chills, or sore throat, is important.
    Avoid Certain Medications: If medications are causing neutropenia, your doctor may adjust the dosage or prescribe alternatives.
    Support Bone Marrow Health: A healthy diet rich in essential nutrients, including folate, vitamin B12, and copper, can support bone marrow function.
    Use of Growth Factors: In some cases, doctors may prescribe granulocyte-colony stimulating factors (G-CSF) to stimulate neutrophil production.

Foods to Eat:
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.
    Vitamin B12-Rich Foods: Animal products such as meat, poultry, fish, eggs, and dairy.
    Copper-Rich Foods: Shellfish (oysters, crab), nuts, seeds, whole grains, and legumes.
    Protein-Rich Foods: Lean meats, fish, tofu, and legumes to support overall immune health.

Example Meal Plan for Low Absolute Neutrophil Count:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in vitamin B12 and folate).
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein, vitamin B12, and folate).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli (rich in vitamin B12, copper, and protein).""")
        elif values["Absolute Neutrophil Count"] > 7000:
            advice.append("""High Absolute Neutrophil Count (Neutrophilia)

Root Cause:
    Infections: Acute bacterial infections, such as pneumonia, appendicitis, or urinary tract infections, often lead to an increase in neutrophil count as the body’s immune response activates to fight the infection.
    Inflammatory Conditions: Chronic inflammatory diseases like rheumatoid arthritis, inflammatory bowel disease (IBD), or vasculitis can lead to an elevated neutrophil count.
    Stress or Trauma: Physical or emotional stress, surgery, or trauma can temporarily elevate neutrophil levels due to the release of stress hormones like cortisol.
    Medications: Drugs like corticosteroids, epinephrine, or lithium can stimulate neutrophil production, causing neutrophilia.
    Smoking: Chronic smoking can elevate neutrophil levels, particularly in the lungs, as part of the body’s inflammatory response.
    Leukemia or Myeloproliferative Disorders: Certain cancers like chronic myelogenous leukemia (CML) or myeloproliferative disorders can cause the bone marrow to produce excessive neutrophils.
    Tissue Damage: Any form of tissue damage, including burns, heart attacks, or extensive trauma, can cause neutrophil counts to rise as part of the body’s healing process.

Tips:
    Identify and Treat Infections: If an infection is the cause of neutrophilia, appropriate antibiotics or antiviral medications may be required to treat the infection and normalize neutrophil counts.
    Manage Inflammatory Conditions: Medications such as corticosteroids, immunosuppressants, or biologics may be prescribed to reduce inflammation and lower neutrophil counts in conditions like rheumatoid arthritis or IBD.
    Minimize Stress: Engage in stress-reducing activities, such as yoga, meditation, or relaxation exercises, to help reduce the impact of stress on neutrophil production.
    Avoid Smoking: If smoking is the cause of elevated neutrophils, quitting smoking will help reduce the inflammatory response and normalize neutrophil levels.
    Monitor for Hematologic Conditions: If a blood disorder like leukemia is suspected, further diagnostic testing and treatments, such as chemotherapy or targeted therapies, may be necessary.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds to reduce inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts to combat oxidative stress and inflammation.
    Fiber-Rich Foods: Whole grains (oats, brown rice), vegetables (broccoli, cauliflower), and legumes to support gut health and reduce systemic inflammation.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, and broccoli to support immune health and reduce inflammation.

Example Meal Plan for High Absolute Neutrophil Count:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Absolute Lymphocyte Count (range: 1.0-4.0 x10⁹/L)
    if "Absolute Lymphocyte Count" in values:
        if values["Absolute Lymphocyte Count"] < 1000:
            advice.append("""Low Absolute Lymphocyte Count (Lymphocytopenia)

Root Cause:
    Infections: Certain viral infections, such as HIV, hepatitis, influenza, and measles, can cause lymphocytes to be temporarily or chronically low as the body focuses its immune resources elsewhere.
    Autoimmune Disorders: Conditions like lupus, rheumatoid arthritis, or Sjogren's syndrome can lead to the destruction of lymphocytes, resulting in lymphocytopenia.
    Bone Marrow Disorders: Disorders such as aplastic anemia, leukemia, or myelodysplastic syndromes can affect the production of lymphocytes in the bone marrow.
    Immunosuppressive Medications: Drugs like corticosteroids, chemotherapy, or immunosuppressive medications can reduce lymphocyte production, leading to a low count.
    Malnutrition: Severe deficiencies in nutrients, particularly protein, zinc, folate, and vitamin B12, can impair immune function and lead to low lymphocyte levels.
    Radiation Therapy: Exposure to radiation, either through cancer treatments or environmental factors, can reduce the production of lymphocytes in the bone marrow.
    Chronic Stress: Prolonged stress can elevate cortisol levels, which in turn can suppress lymphocyte production.
    Congenital Immunodeficiencies: Genetic disorders, such as DiGeorge syndrome, can result in lymphocytopenia by affecting the immune system’s development.

Tips:
    Monitor for Infections: Individuals with low lymphocyte counts should be extra cautious to avoid infections. If infections occur, they should be treated promptly.
    Boost Immune Function: Support the immune system by managing underlying conditions, taking prescribed medications, and avoiding immunosuppressive drugs when possible.
    Address Nutritional Deficiencies: Ensure a well-balanced diet rich in essential vitamins and minerals, especially those involved in immune function, such as zinc, folate, and vitamin B12.
    Stress Management: Engage in relaxation techniques such as meditation, yoga, or deep breathing exercises to manage stress and reduce its impact on the immune system.
    Regular Monitoring: Periodic blood tests to monitor lymphocyte counts can help track progress and adjust treatment accordingly.

Foods to Eat:
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), strawberries, bell peppers, and broccoli to support immune function.
    Zinc-Rich Foods: Shellfish (oysters), lean meats, legumes, nuts, and seeds to support immune health.
    Folate-Rich Foods: Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.
    Protein-Rich Foods: Lean meats, poultry, fish, tofu, and legumes to support immune cell production.
    Vitamin B12-Rich Foods: Animal products such as meat, poultry, fish, eggs, and dairy for immune support.

Example Meal Plan for Low Absolute Lymphocyte Count:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in vitamin B12 and folate).
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein, vitamin B12, and folate).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli (rich in vitamin B12, protein, and zinc).""")
        elif values["Absolute Lymphocyte Count"] > 3000:
            advice.append("""High Absolute Lymphocyte Count (Lymphocytosis)

Root Cause:
    Infections: Lymphocytosis is often seen in response to viral infections such as mononucleosis (Epstein-Barr virus), hepatitis, or cytomegalovirus. It may also occur during some bacterial infections like tuberculosis.
    Autoimmune Disorders: Conditions such as multiple sclerosis, rheumatoid arthritis, or Hashimoto's thyroiditis can cause an increase in lymphocytes due to chronic immune activation.
    Chronic Lymphocytic Leukemia (CLL): A form of leukemia where there is a malignant overproduction of lymphocytes, leading to elevated counts.
    Lymphoma: Certain types of lymphoma, such as Hodgkin's lymphoma and non-Hodgkin lymphoma, can lead to high lymphocyte counts.
    Stress: Physical stress or emotional trauma can cause a temporary increase in lymphocyte production as part of the body's response to stress.
    Smoking: Chronic smoking can lead to lymphocytosis, especially in the lungs, as part of the inflammatory response.
    Medication Response: Certain medications, such as those used in immunotherapy or immune-stimulants, may increase lymphocyte levels as part of an immune response.

Tips:
    Identify the Underlying Cause: Lymphocytosis can be indicative of infection, autoimmune disorders, or cancer. Seek appropriate medical evaluation to determine the cause and start treatment.
    Manage Chronic Infections or Inflammatory Conditions: If lymphocytosis is due to infections or chronic conditions, managing the underlying disease through medication, rest, and proper care can help normalize lymphocyte counts.
    Monitor for Leukemia or Lymphoma: If there is concern about blood cancers such as leukemia or lymphoma, further diagnostic testing, including a bone marrow biopsy or imaging studies, may be necessary.
    Avoid Smoking: Quitting smoking can reduce chronic inflammation and help normalize lymphocyte levels.
    Manage Stress: If stress is a contributing factor, incorporating stress-management strategies like relaxation exercises or therapy may help in reducing lymphocyte levels.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds to reduce inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts to combat oxidative stress and reduce inflammation.
    Fiber-Rich Foods: Whole grains (oats, brown rice), vegetables (broccoli, cauliflower), and legumes to support overall immune health.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, strawberries, and broccoli to help combat inflammation.
    Probiotic-Rich Foods: Yogurt, kefir, and fermented foods to support gut health and modulate immune function.

Example Meal Plan for High Absolute Lymphocyte Count:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Absolute Eosinophil Count (range: 0.02-0.5 x10⁹/L)
    if "Absolute Eosinophil Count" in values:
        if values["Absolute Eosinophil Count"] < 20:
            advice.append("""Low Absolute Eosinophil Count (Eosinopenia)

Root Cause:
    Acute Infections: During acute bacterial infections, particularly when the body is fighting severe infections such as sepsis or systemic infections, eosinophil levels can decrease.
    Corticosteroid Use: Medications like corticosteroids (prednisone, hydrocortisone) can suppress eosinophil production, leading to low counts.
    Cushing's Syndrome: This condition, caused by excessive cortisol in the body, can suppress eosinophil levels as cortisol directly impacts the immune system.
    Stress: Prolonged physical or emotional stress can lead to elevated cortisol levels, which in turn can reduce eosinophil counts.
    Bone Marrow Suppression: Conditions like aplastic anemia, leukemia, or myelodysplastic syndromes can affect the production of eosinophils in the bone marrow, leading to low levels.
    Acute Inflammatory Disorders: Inflammatory conditions such as acute infections, acute trauma, or shock may cause eosinophils to be used up rapidly, resulting in temporarily low counts.
    Severe Protein Malnutrition: Severe malnutrition can impair immune function, leading to reduced production of eosinophils.

Tips:
    Infection Management: Since eosinophils play a role in fighting infections, especially parasitic infections, it is important to address any underlying infection promptly.
    Medication Adjustment: If corticosteroids or other medications are causing eosinophil suppression, consult a healthcare provider about potential alternatives or dosage adjustments.
    Bone Marrow Monitoring: If bone marrow disorders are suspected, regular check-ups and diagnostic tests are necessary to monitor bone marrow health.
    Stress Reduction: Engage in stress-management techniques, such as yoga, meditation, or deep-breathing exercises, to help reduce cortisol levels.
    Nutritional Support: Ensure adequate nutrition, especially if malnutrition is a concern, by focusing on a balanced diet rich in protein and essential nutrients.

Foods to Eat:
    Protein-Rich Foods: Lean meats, poultry, fish, tofu, and legumes to support immune system function and overall health.
    Vitamin B12 and Folate-Rich Foods: Animal products such as meat, eggs, and dairy, as well as leafy greens (spinach, kale), beans, and lentils.
    Zinc-Rich Foods: Shellfish (oysters, crab), red meat, beans, nuts, and seeds for immune support.
    Healthy Fats: Olive oil, avocados, and fatty fish like salmon, which can help reduce inflammation and support immune function.

Example Meal Plan for Low Absolute Eosinophil Count:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in vitamin B12, folate, and protein).
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein, folate, and zinc).
    Snack: A handful of almonds and a boiled egg (rich in protein and zinc).
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli (rich in protein, zinc, and healthy fats).""")
        elif values["Absolute Eosinophil Count"] > 500:
            advice.append("""High Absolute Eosinophil Count (Eosinophilia)

Root Cause:
    Allergic Reactions: Conditions such as asthma, hay fever, eczema, and allergic rhinitis can cause an increase in eosinophil count, as these cells are involved in the body’s response to allergens.
    Parasitic Infections: Infections caused by parasites, such as hookworms, roundworms, and malaria, often result in an elevated eosinophil count as the body tries to combat the parasites.
    Autoimmune Diseases: Conditions like rheumatoid arthritis, vasculitis, or inflammatory bowel disease (IBD) may cause an increase in eosinophils as part of the immune system's inflammatory response.
    Eosinophilic Disorders: Eosinophilic esophagitis, eosinophilic pneumonia, or eosinophilic granulomatosis with polyangiitis (Churg-Strauss syndrome) are rare conditions in which eosinophils are abnormally elevated in the body.
    Chronic Infections: Long-term infections, including fungal infections, tuberculosis, or certain viral infections, can lead to eosinophilia.
    Drug Reactions: Certain medications, such as antibiotics, nonsteroidal anti-inflammatory drugs (NSAIDs), or some chemotherapy drugs, can trigger an allergic reaction leading to high eosinophil levels.
    Cancer: Some cancers, particularly lymphomas or certain types of leukemia, may cause an increase in eosinophil levels as part of the body's response to malignancy.
    Hypereosinophilic Syndrome: A rare condition characterized by persistently high eosinophil levels, which can affect various organs, including the heart, lungs, and skin.

Tips:
    Manage Allergies: If allergies are the cause, antihistamines, corticosteroids, or allergy shots (immunotherapy) may be recommended to control the allergic response.
    Treat Parasitic Infections: If eosinophilia is due to a parasitic infection, appropriate antiparasitic medications will be required to eliminate the infection and normalize eosinophil levels.
    Monitor for Autoimmune Disorders: If an autoimmune disorder is suspected, immunosuppressive medications or biologics may be used to reduce eosinophil levels.
    Medication Adjustment: If drugs are causing eosinophilia, consult with your doctor about adjusting or changing the medication.
    Avoid Environmental Triggers: For allergic eosinophilia, avoiding allergens like pollen, dust, or pet dander can help reduce eosinophil levels.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds to reduce inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts to combat oxidative stress and inflammation.
    Fiber-Rich Foods: Whole grains (oats, brown rice), vegetables (broccoli, cauliflower), and legumes to support overall immune health.
    Probiotic-Rich Foods: Yogurt, kefir, and fermented foods to support gut health and modulate immune function.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, strawberries, and broccoli to help combat inflammation.

Example Meal Plan for High Absolute Eosinophil Count:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Absolute Monocyte Count (range: 0.1-1.0 x10⁹/L)
    if "Absolute Monocyte Count" in values:
        if values["Absolute Monocyte Count"] < 200:
            advice.append("""Low Absolute Monocyte Count (Monocytopenia)
Root Cause:
    Acute Infections: During the initial stages of some infections, particularly viral infections (e.g., HIV, hepatitis), the monocyte count may decrease temporarily as the body prioritizes fighting the infection.
    Bone Marrow Disorders: Conditions like aplastic anemia, leukemia, or myelodysplastic syndromes can affect the bone marrow's ability to produce monocytes, leading to a low count.
    Corticosteroid Use: Corticosteroids (e.g., prednisone) and other immunosuppressive medications can suppress the production of monocytes, leading to monocytopenia.
    Chemotherapy or Radiation Therapy: These treatments, used for cancer or other conditions, can impair bone marrow function and decrease the production of monocytes.
    Severe Malnutrition: Nutritional deficiencies, particularly in proteins, vitamins, and minerals like vitamin B12 and folate, can impair the production of monocytes in the bone marrow.
    Autoimmune Diseases: Certain autoimmune diseases, such as lupus or rheumatoid arthritis, may lead to low monocyte counts as a result of immune dysregulation.
    Congenital or Genetic Disorders: Rare genetic conditions, like hereditary neutropenia, can lead to reduced production of monocytes and other white blood cells.

Tips:
    Monitor for Infections: Since monocytes are critical in fighting infections, a low count could make you more vulnerable to bacterial, fungal, and viral infections. It's important to prevent and manage infections with medical advice.
    Review Medications: If monocytopenia is linked to corticosteroids or chemotherapy, consult your doctor about possible adjustments in treatment or switching medications.
    Bone Marrow Function: If a bone marrow disorder is suspected, regular medical follow-up and tests are necessary to assess bone marrow health.
    Boost Nutritional Intake: Ensure an adequate intake of essential nutrients, particularly protein, vitamin B12, folate, and iron, to support the production of healthy blood cells.
    Stress Management: High levels of chronic stress can suppress monocyte production. Practice stress-reduction techniques such as deep breathing, meditation, and exercise.

Foods to Eat:
    Protein-Rich Foods: Lean meats, poultry, fish, eggs, tofu, and legumes to support immune cell production and overall health.
    Vitamin B12 and Folate-Rich Foods: Animal products like meat, eggs, and dairy, as well as leafy greens (spinach, kale), beans, and lentils.
    Iron-Rich Foods: Red meat, poultry, fish, lentils, and spinach to support red blood cell and immune cell production.
    Zinc-Rich Foods: Shellfish (oysters), lean meats, legumes, nuts, and seeds to enhance immune function.
    Healthy Fats: Olive oil, avocados, and fatty fish like salmon to reduce inflammation and support overall health.

Example Meal Plan for Low Absolute Monocyte Count:
    Breakfast: Scrambled eggs with spinach and whole-grain toast (rich in protein, vitamin B12, and folate).
    Lunch: Grilled chicken with quinoa and a side of leafy greens (rich in protein, folate, and zinc).
    Snack: A handful of almonds and a boiled egg (rich in protein and zinc).
    Dinner: Baked salmon with roasted sweet potatoes and steamed broccoli (rich in protein, zinc, and healthy fats).""")
        elif values["Absolute Monocyte Count"] > 1000:
            advice.append("""High Absolute Monocyte Count (Monocytosis)

Root Cause:
    Chronic Infections: Long-term infections, such as tuberculosis, brucellosis, syphilis, or fungal infections, can lead to elevated monocyte levels as the body’s immune response becomes chronically activated.
    Inflammatory Diseases: Conditions like inflammatory bowel disease (IBD), rheumatoid arthritis, or lupus can cause chronic inflammation, leading to an elevated monocyte count.
    Leukemia and Lymphoma: Certain cancers, particularly leukemia and lymphoma, can cause a marked increase in monocyte production in the bone marrow.
    Recovery from Acute Infection: After an acute infection, as the body starts to recover, monocytes can remain elevated for a period of time.
    Autoimmune Diseases: Conditions such as sarcoidosis, systemic lupus erythematosus (SLE), and vasculitis can result in elevated monocytes due to chronic immune activation.
    Myeloproliferative Disorders: Conditions like chronic myelomonocytic leukemia (CMML) and other blood cancers can cause persistent monocytosis.
    Stress: Physical or emotional stress can result in increased levels of monocytes as part of the body's stress response.
    Tissue Damage or Inflammation: When tissues are damaged due to injury, surgery, or inflammation, the body increases monocyte production to aid in healing and immune response.

Tips:
    Identify the Underlying Cause: It is crucial to determine the root cause of monocytosis, such as infection, cancer, or inflammatory diseases, so that appropriate treatment can be initiated.
    Treat Chronic Infections: If monocytosis is due to chronic infections, antimicrobial or antifungal medications will be necessary to eliminate the infection.
    Manage Inflammatory Diseases: If the cause is related to an autoimmune or inflammatory disease, immunosuppressive drugs or disease-modifying therapies may be prescribed to control inflammation and reduce monocytosis.
    Monitor for Blood Cancers: If leukemia or lymphoma is suspected, further diagnostic testing like bone marrow biopsies, imaging, and blood tests may be required to confirm the diagnosis.
    Reduce Stress: Chronic stress can exacerbate inflammation and elevate monocyte levels. Practice stress-reduction techniques such as exercise, mindfulness, and relaxation therapies.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), olive oil, walnuts, and flaxseeds to reduce inflammation.
    Antioxidant-Rich Foods: Berries (blueberries, strawberries), leafy greens (spinach, kale), and nuts to combat oxidative stress and inflammation.
    Fiber-Rich Foods: Whole grains (oats, brown rice), vegetables (broccoli, cauliflower), and legumes to support overall immune health.
    Probiotic-Rich Foods: Yogurt, kefir, and fermented foods to support gut health and modulate immune function.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), bell peppers, strawberries, and broccoli to help combat inflammation.

Example Meal Plan for High Absolute Monocyte Count:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing (anti-inflammatory foods).
    Snack: A handful of almonds and an orange (rich in vitamin C).
    Dinner: Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).
""")

    # Platelet Count (range: 150,000-410,000 cells/μL)
    if "Platelet Count" in values:
        if values["Platelet Count"] < 150000:
            advice.append("""Low Platelet Count (Thrombocytopenia)

Root Cause:
    Bone Marrow Disorders: Conditions such as aplastic anemia, leukemia, or myelodysplastic syndromes can reduce the bone marrow's ability to produce platelets, leading to thrombocytopenia.
    Autoimmune Diseases: Autoimmune conditions like lupus, rheumatoid arthritis, or idiopathic thrombocytopenic purpura (ITP) can cause the immune system to attack and destroy platelets.
    Viral Infections: Infections such as dengue, HIV, hepatitis C, or Epstein-Barr virus (EBV) can cause platelet destruction and a low count.
    Medications: Certain medications, including chemotherapy drugs, heparin (anticoagulants), and antibiotics, can lead to platelet destruction or inhibition of platelet production.
    Nutritional Deficiencies: Deficiencies in vitamin B12, folate, or iron can impair platelet production in the bone marrow.
    Alcohol Consumption: Chronic alcohol use can suppress bone marrow function and lead to low platelet counts.
    Sepsis or Infections: Severe systemic infections or sepsis can lead to disseminated intravascular coagulation (DIC), a condition that consumes platelets.
    Pregnancy: Some pregnant women may experience a mild decrease in platelets, particularly in the third trimester (gestational thrombocytopenia).
    Hypersplenism: An enlarged spleen (often due to liver disease or certain infections) can sequester platelets, leading to low levels in the blood.

Tips:
    Monitor for Bleeding: Individuals with thrombocytopenia may be more prone to bleeding or bruising easily. Be cautious of activities that could cause cuts or injuries, and seek medical attention if any unusual bleeding occurs.
    Medications Review: If medications are causing low platelet counts, consult a healthcare provider about alternatives or dosage adjustments.
    Manage Infections: In cases of viral infections or sepsis, addressing the infection through appropriate treatment (antivirals, antibiotics) is critical.
    Improve Nutrition: Make sure to consume a balanced diet that includes adequate amounts of vitamin B12, folate, and iron to support platelet production.
    Avoid Alcohol: Limit or avoid alcohol consumption, as it can suppress bone marrow activity and contribute to low platelet counts.
    Bone Marrow Monitoring: If a bone marrow disorder is suspected, follow-up tests and regular check-ups are necessary to monitor platelet production and overall health.

Foods to Eat:
    Iron-Rich Foods: Red meat, poultry, fish, beans, lentils, and spinach to support healthy red blood cell and platelet production.
    Folate-Rich Foods: Leafy greens (kale, spinach), citrus fruits, avocados, and legumes to promote platelet production.
    Vitamin B12-Rich Foods: Meat, eggs, dairy, and fortified cereals to help in red blood cell and platelet formation.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons), strawberries, and bell peppers to enhance iron absorption and immune health.
    Healthy Fats: Olive oil, avocado, and nuts to reduce inflammation and support overall health.

Example Meal Plan for Low Platelet Count:
    Breakfast: Scrambled eggs with spinach, whole-grain toast, and a glass of orange juice (rich in vitamin B12, folate, and vitamin C).
    Lunch: Grilled chicken with quinoa, steamed broccoli, and a side salad with avocado (rich in protein, iron, and healthy fats).
    Snack: A handful of almonds and a boiled egg (rich in protein and healthy fats).
    Dinner: Baked salmon with roasted sweet potatoes and steamed kale (rich in vitamin B12, folate, and healthy fats).""")
        elif values["Platelet Count"] > 410000:
            advice.append("""High Platelet Count (Thrombocytosis)

Root Cause:
    Reactive (Secondary) Thrombocytosis: This is the most common cause and is typically a response to another condition, such as:
    Infections: Bacterial, viral, or fungal infections can trigger an increase in platelet count as part of the inflammatory response.
    Inflammatory Disorders: Chronic inflammatory diseases, such as rheumatoid arthritis, inflammatory bowel disease (IBD), or vasculitis, can cause reactive thrombocytosis.
    Iron Deficiency Anemia: Iron deficiency can result in an increase in platelet count as a compensatory mechanism.
    Surgical Procedures or Trauma: Recovery from surgery or trauma can lead to transient thrombocytosis as part of the healing process.
    Myeloproliferative Disorders: Primary thrombocytosis, which occurs due to disorders of the bone marrow such as essential thrombocythemia (ET) or polycythemia vera, can lead to persistently elevated platelet counts.
    Cancer: Certain cancers, particularly lung, gastrointestinal, and ovarian cancers, can lead to thrombocytosis due to the body's inflammatory response to the tumor or as a direct effect of the cancer on the bone marrow.
    Splenectomy (Spleen Removal): Removal of the spleen (often due to injury or disease) can cause a prolonged increase in platelet count because the spleen plays a role in removing excess platelets from the bloodstream.

Tips:
    Identify and Treat Underlying Causes: Address any infections, iron deficiencies, or underlying conditions causing thrombocytosis. For reactive thrombocytosis, treating the underlying condition often resolves the high platelet count.
    Monitor for Clotting Disorders: A high platelet count can increase the risk of blood clots, leading to conditions like stroke, deep vein thrombosis (DVT), or pulmonary embolism. Regular check-ups and blood tests may be needed.
    Medications: For primary thrombocytosis or myeloproliferative disorders, medications such as low-dose aspirin, hydroxyurea, or interferon may be prescribed to reduce the risk of clotting.
    Avoid Smoking: Smoking can increase the risk of clot formation and should be avoided if platelet counts are high.
    Exercise Regularly: Regular exercise, under a healthcare provider's guidance, may help improve circulation and reduce the risk of clotting.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, mackerel), flaxseeds, walnuts, and olive oil to reduce inflammation and platelet aggregation.
    Vitamin E-Rich Foods: Nuts (almonds, hazelnuts), spinach, and avocados to help reduce the risk of clotting by promoting healthy blood circulation.
    Ginger and Turmeric: These have natural blood-thinning properties and can help reduce inflammation and platelet aggregation.
    Fruits and Vegetables: A variety of antioxidant-rich fruits (berries, citrus fruits) and vegetables (broccoli, kale) can support overall vascular health and reduce inflammation.
    Whole Grains: Brown rice, oats, quinoa, and whole wheat can provide fiber and antioxidants that support overall cardiovascular health.

Example Meal Plan for High Platelet Count:
    Breakfast: Oatmeal with chia seeds, walnuts, and blueberries (rich in omega-3s and antioxidants).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil and turmeric dressing (anti-inflammatory foods).
    Snack: A handful of almonds and a few slices of avocado (rich in vitamin E and healthy fats).
    Dinner: Stir-fried tofu with spinach, bell peppers, and ginger (rich in anti-inflammatory compounds).
""")

    # Erythrocyte Sedimentation Rate (range: 0-20 mm/hr)
    if "Erythrocyte Sedimentation Rate" in values:
        if values["Erythrocyte Sedimentation Rate"] < 0:
            advice.append("""Low Erythrocyte Sedimentation Rate (ESR)

Root Cause:
    Normal Variation: A low ESR can sometimes be a normal finding, especially in healthy individuals, as the rate is influenced by various factors such as age, sex, and individual health status.
    Polycythemia Vera: This is a condition where there is an overproduction of red blood cells, which increases blood viscosity and can lead to a lower ESR.
    Hyperviscosity Syndromes: Conditions that cause thickened blood, such as Waldenström macroglobulinemia or multiple myeloma, can reduce the ESR.
    Low Fibrinogen Levels: ESR is affected by proteins in the blood, particularly fibrinogen. Low fibrinogen levels, due to liver disease or certain genetic conditions, may result in a lower ESR.
    Leukocytosis: A very high white blood cell count, such as in leukemia or other blood cancers, can reduce the ESR.
    Severe Anemia: Certain types of severe anemia, particularly in the presence of low fibrinogen levels, may lead to a low ESR.
    Extremely Elevated Blood Sugar: Hyperglycemia (very high blood sugar levels), which may be seen in uncontrolled diabetes, can lower the ESR.

Tips:
    Monitor for Symptoms: While a low ESR may not be concerning in itself, monitor for symptoms related to potential underlying conditions, like polycythemia vera or hyperviscosity syndromes. Consult your doctor if you have symptoms of these disorders.
    Check Blood Viscosity: If you have conditions known to increase blood viscosity, such as polycythemia vera or myeloma, ensure proper treatment and management to prevent complications.
    Review Liver Function: If low fibrinogen levels are suspected, check liver function, as the liver is responsible for producing fibrinogen, and treatment may be needed to address any liver abnormalities.
    Evaluate Blood Glucose: If hyperglycemia is suspected as the cause, it is crucial to manage your blood sugar levels through diet, exercise, and medication as prescribed by your healthcare provider.
    Follow-up with Regular Monitoring: For individuals with blood disorders, anemia, or other underlying conditions, regular blood tests and check-ups are important to monitor changes in ESR and overall health.

Foods to Eat:
    Iron-Rich Foods: Red meat, poultry, beans, lentils, and spinach to help with anemia and support overall blood health.
    Healthy Fats: Olive oil, avocados, and fatty fish (salmon, mackerel) to reduce inflammation.
    Fiber-Rich Foods: Whole grains, vegetables, and fruits to support overall health and help control blood sugar levels.
    Vitamin B12 and Folate-Rich Foods: Animal products like meat, eggs, and dairy, as well as leafy greens, beans, and fortified cereals to help support red blood cell production and healthy blood viscosity.
    Antioxidant-Rich Foods: Berries, citrus fruits, and leafy greens to support immune function and reduce inflammation.

Example Meal Plan for Low ESR:
    Breakfast: Scrambled eggs with spinach, whole-grain toast, and a glass of orange juice (rich in vitamin B12, folate, and vitamin C).
    Lunch: Grilled chicken with quinoa, roasted sweet potatoes, and a side salad with avocado (rich in iron, vitamin B12, and healthy fats).
    Snack: A handful of almonds and a boiled egg (rich in protein and healthy fats).
    Dinner: Baked salmon with roasted broccoli and quinoa (rich in healthy fats, iron, and fiber).
""")
        elif values["Erythrocyte Sedimentation Rate"] > 15:
            advice.append("""High Erythrocyte Sedimentation Rate (ESR)

Root Cause:
    Chronic Inflammatory Diseases: Conditions such as rheumatoid arthritis, lupus, inflammatory bowel disease (IBD), or vasculitis are commonly associated with an elevated ESR due to the body's ongoing inflammatory response.
    Infections: Bacterial infections (e.g., tuberculosis, osteomyelitis) and some viral infections can cause a significant rise in ESR as part of the body's acute-phase response.
    Cancer: Certain cancers, especially lymphomas, leukemia, and solid tumors, can cause an elevated ESR as the body responds to tumor activity and inflammation.
    Kidney Disease: Chronic kidney disease, especially in its later stages, can lead to an elevated ESR due to inflammation and other systemic effects.
    Anemia: Particularly in cases of iron-deficiency anemia or anemia of chronic disease, ESR can be elevated as the body responds to decreased red blood cells and tissue hypoxia.
    Pregnancy: ESR is naturally elevated during pregnancy, particularly in the second and third trimesters, due to changes in the immune system and hormone levels.
    Temporal Arteritis (Giant Cell Arteritis): A condition affecting the large arteries, particularly the temporal arteries, often causes a significantly high ESR, which is used as a diagnostic marker.
    Tissue Injury: Severe trauma, surgery, or burns can cause an increase in ESR as part of the inflammatory healing process.

Tips:
    Investigate the Underlying Cause: A high ESR is typically a marker of inflammation, and it’s crucial to identify the underlying condition causing the elevated level. This may require further diagnostic tests, such as imaging, biopsy, or blood cultures.
    Manage Inflammatory Diseases: If the cause is an autoimmune or inflammatory condition, such as rheumatoid arthritis or lupus, medications to reduce inflammation (like corticosteroids or disease-modifying antirheumatic drugs) may be prescribed.
    Treat Infections: If the high ESR is due to an infection, appropriate antibiotics or antiviral treatments will be necessary to control the infection and reduce inflammation.
    Cancer Treatment: For cancers causing elevated ESR, a targeted treatment plan, including chemotherapy, radiation, or immunotherapy, will be required.
    Monitor Kidney Function: If kidney disease is the cause, monitoring kidney function through regular tests is critical, along with managing blood pressure and potential fluid imbalances.
    Address Anemia: Treating the underlying cause of anemia, whether it be iron deficiency or anemia of chronic disease, can help lower the ESR over time.
    Monitor Pregnancy: ESR naturally rises during pregnancy, and in most cases, this is not a cause for concern. However, it's important to monitor and discuss any abnormal increases with your doctor.

Foods to Eat:
    Anti-Inflammatory Foods: Omega-3-rich foods like fatty fish (salmon, sardines), flaxseeds, chia seeds, walnuts, and olive oil to help reduce inflammation.
    Fiber-Rich Foods: Whole grains (oats, quinoa, brown rice), vegetables (spinach, kale, broccoli), and fruits (berries, apples) to support overall health and reduce inflammation.
    Antioxidant-Rich Foods: Berries, citrus fruits, tomatoes, and leafy greens to combat oxidative stress and support immune health.
    Lean Protein: Skinless poultry, lean beef, tofu, and legumes to support immune function without exacerbating inflammation.
    Spices with Anti-Inflammatory Properties: Turmeric, ginger, and garlic can be added to meals to reduce inflammation.

Example Meal Plan for High ESR:
    Breakfast: Oatmeal with chia seeds, flaxseeds, and fresh blueberries (rich in omega-3s, fiber, and antioxidants).
    Lunch: Grilled salmon with quinoa, spinach salad with olive oil, and a side of roasted sweet potatoes (anti-inflammatory foods and healthy fats).
    Snack: A handful of walnuts and a green smoothie with spinach, ginger, and lemon (rich in anti-inflammatory compounds).
    Dinner: Stir-fried tofu with broccoli, bell peppers, and turmeric (anti-inflammatory and antioxidant-rich).
""")

    # Fasting Plasma Glucose (range: 70-100 mg/dL)
    if "Fasting Plasma Glucose" in values:
        if values["Fasting Plasma Glucose"] < 70:
            advice.append("""Low Fasting Plasma Glucose (Hypoglycemia)

Root Cause:
    Insulin Overdose: In people with diabetes, too much insulin or oral hypoglycemic medication can cause blood glucose levels to drop below normal levels.
    Prolonged Fasting or Starvation: Extended periods without eating can lead to a significant drop in blood glucose, as the body runs out of readily available energy from food.
    Alcohol Consumption: Excessive drinking, especially without eating, can impair the liver's ability to release glucose into the bloodstream, leading to hypoglycemia.
    Hormonal Imbalances: Conditions like adrenal insufficiency, hypothyroidism, or growth hormone deficiencies can result in low blood sugar levels.
    Insulinoma: A rare tumor of the pancreas that produces excessive insulin, leading to low blood sugar levels.
    Severe Liver Disease: Liver disease, such as cirrhosis or hepatitis, can impair the liver’s ability to produce glucose, leading to low blood sugar levels.
    Malnutrition: Lack of sufficient calories, particularly carbohydrates, can lead to hypoglycemia, especially in individuals with eating disorders or poor nutrition.
    Certain Medications: Medications such as sulfonylureas (used in type 2 diabetes) and other drugs can increase the risk of low blood sugar.

Tips:
    Eat Regular, Balanced Meals: Ensure regular meals and snacks throughout the day, especially those containing complex carbohydrates, protein, and healthy fats to stabilize blood sugar levels.
    Monitor Medication: If taking insulin or oral hypoglycemics, adjust the dosage with guidance from a healthcare provider to prevent hypoglycemia.
    Avoid Excessive Alcohol: Limit alcohol consumption, particularly on an empty stomach, to avoid hypoglycemia.
    Identify and Treat Underlying Conditions: Conditions like insulinoma, adrenal insufficiency, or liver disease may require specific treatment and monitoring.
    Carry Glucose: Always have a source of fast-acting carbohydrates, such as glucose tablets or sugary drinks, in case of an emergency hypoglycemic episode.

Foods to Eat:
    Complex Carbohydrates: Whole grains (brown rice, oats), sweet potatoes, and legumes (lentils, beans) to provide a steady source of glucose.
    Lean Protein: Chicken, turkey, eggs, and tofu to stabilize blood sugar and prevent rapid drops.
    Healthy Fats: Avocados, olive oil, and nuts to provide energy and slow down glucose absorption.
    Fibrous Vegetables: Leafy greens (spinach, kale), bell peppers, and broccoli to provide essential nutrients without causing rapid blood sugar spikes.
    Fruits: Berries, apples, and pears for natural sugars that can be combined with fiber to stabilize blood sugar levels.

Example Meal Plan for Low Fasting Plasma Glucose:
    Breakfast: Oatmeal with chia seeds, sliced almonds, and a handful of blueberries (complex carbs, fiber, and protein).
    Lunch: Grilled chicken with quinoa and a side of roasted vegetables (balanced meal with protein and fiber).
    Snack: A boiled egg with an apple (protein and natural sugars).
    Dinner: Baked salmon with steamed broccoli and a small baked sweet potato (healthy fats, protein, and complex carbs).
""")
        elif values["Fasting Plasma Glucose"] > 100:
            advice.append("""High Fasting Plasma Glucose (Hyperglycemia)

Root Cause:
    Diabetes Mellitus: The most common cause of high fasting plasma glucose is diabetes, particularly when blood glucose is not well controlled. This can happen in both Type 1 and Type 2 diabetes.
    Insulin Resistance: In conditions like obesity or metabolic syndrome, the body’s cells become less responsive to insulin, causing elevated blood glucose levels.
    Stress or Illness: Physical or emotional stress, as well as infections or other illnesses, can cause blood glucose levels to rise due to the release of stress hormones like cortisol.
    Medications: Certain medications, such as corticosteroids, thiazide diuretics, or beta-blockers, can increase blood glucose levels.
    Endocrine Disorders: Conditions like Cushing’s syndrome (excess cortisol), pheochromocytoma (tumors that release adrenaline), or acromegaly (growth hormone excess) can result in elevated blood sugar.
    Pregnancy (Gestational Diabetes): High blood glucose levels during pregnancy, due to insulin resistance, is known as gestational diabetes.
    Pancreatic Disorders: Diseases like pancreatitis, pancreatic cancer, or removal of part of the pancreas can reduce insulin production, leading to high blood sugar levels.
    Chronic Stress: Prolonged emotional or physical stress can raise cortisol levels, which in turn raises blood sugar levels.

Tips:
    Monitor Blood Sugar: Regular monitoring of blood glucose levels is crucial for individuals with diabetes or those at risk of developing diabetes.
    Follow a Diabetes Management Plan: If diagnosed with diabetes, work with your healthcare provider to create and stick to a blood sugar management plan, including medication, diet, and exercise.
    Stay Active: Regular physical activity can help increase insulin sensitivity and reduce blood sugar levels.
    Manage Stress: Practice stress management techniques like yoga, meditation, or deep breathing to lower cortisol levels and improve blood sugar control.
    Watch Your Diet: Avoid processed foods, sugary snacks, and beverages that cause rapid spikes in blood glucose. Focus on a balanced diet with whole foods.
    Weight Management: Achieving and maintaining a healthy weight through diet and exercise can help manage insulin resistance and lower blood sugar levels.

Foods to Eat:
    Whole Grains: Brown rice, quinoa, barley, and oats to provide fiber and help regulate blood sugar levels.
    Leafy Greens and Non-Starchy Vegetables: Spinach, kale, broccoli, cauliflower, and bell peppers to help manage glucose levels.
    Lean Proteins: Skinless poultry, fish, beans, and legumes for steady energy and to help manage hunger.
    Healthy Fats: Avocados, nuts, seeds, and olive oil to support blood sugar control and promote satiety.
    Cinnamon and Apple Cider Vinegar: Both have been shown to help in reducing blood sugar levels and improving insulin sensitivity.

Example Meal Plan for High Fasting Plasma Glucose:
    Breakfast: Scrambled eggs with spinach, a slice of whole-grain toast, and a side of fresh berries (protein, fiber, and healthy fats).
    Lunch: Grilled chicken with a quinoa salad, mixed vegetables (leafy greens, cucumber, tomatoes), and a drizzle of olive oil (balanced meal with complex carbs, lean protein, and healthy fats).
    Snack: A small handful of almonds and an apple (protein and fiber).
    Dinner: Baked salmon with roasted Brussels sprouts and cauliflower (healthy fats and non-starchy vegetables).
""")

    # Glycated Hemoglobin (HbA1C) (range: 4.0-5.6%)
    if "Glycated Hemoglobin" in values:
        if values["Glycated Hemoglobin"] < 5.7:
            advice.append("""Low Glycated Hemoglobin (HbA1c)

Root Cause:
    Good Blood Sugar Control: A low HbA1c usually indicates good control of blood glucose over the past 2-3 months. In individuals with diabetes, a low HbA1c can signify effective management through medication, lifestyle changes (diet and exercise), or both.
    Recent Hypoglycemia: If someone with diabetes experienced significant hypoglycemia (low blood sugar) recently, it can lower their HbA1c, but this is not typically a healthy sign, as it may indicate that blood sugar control has been unstable.
    Anemia: Certain types of anemia, such as iron-deficiency anemia or hemolytic anemia, can cause falsely low HbA1c readings. The shortened lifespan of red blood cells in these conditions leads to a reduced time for glucose to attach to hemoglobin.
    Chronic Blood Loss: Conditions such as gastrointestinal bleeding or other chronic blood loss can lead to lower HbA1c levels as new red blood cells are formed and have less time to become glycated.
    Pregnancy: Pregnancy, especially in the first trimester, can lower HbA1c levels due to changes in red blood cell turnover and increased blood volume.

Tips:
    Monitor Overall Blood Sugar Control: While a low HbA1c can be a positive indicator of good control, ensure it is not the result of frequent hypoglycemic episodes. If you have diabetes, it is essential to aim for a balance, avoiding both high and low extremes.
    Ensure Adequate Nutrition: Make sure you're getting enough essential nutrients, particularly iron, vitamin B12, and folic acid, as deficiencies in these can contribute to anemia, which might lower HbA1c readings.
    Avoid Hypoglycemia: If you're on diabetes medication, be cautious of taking too much insulin or other glucose-lowering medications. Regular monitoring of blood glucose levels can help avoid dangerous low blood sugar episodes.
    Regular Monitoring: Continue regular testing of blood glucose levels and HbA1c, especially if you have diabetes, to stay on top of your long-term blood sugar control.

Foods to Eat:
    Iron-Rich Foods: Red meat, poultry, beans, lentils, spinach, and fortified cereals to prevent or address anemia.
    Vitamin B12 and Folate-Rich Foods: Eggs, dairy, fortified cereals, leafy greens, beans, and lentils to prevent deficiencies that might affect red blood cell production.
    Complex Carbohydrates: Whole grains (oats, quinoa, brown rice) for stable glucose control and overall energy.
    Healthy Fats: Avocados, olive oil, and nuts for heart health and blood sugar stabilization.

Example Meal Plan for Low HbA1c:
    Breakfast: Oatmeal with chia seeds, almond butter, and sliced strawberries (iron and fiber).
    Lunch: Grilled chicken salad with spinach, quinoa, avocado, and olive oil dressing (iron, protein, healthy fats).
    Snack: A boiled egg and a small handful of almonds (protein and healthy fats).
    Dinner: Baked salmon with roasted sweet potatoes and broccoli (omega-3s, complex carbs, and fiber).
""")
        elif values["Glycated Hemoglobin"] >= 5.7:
            advice.append("""High Glycated Hemoglobin (HbA1c)

Root Cause:
    Poor Blood Sugar Control: A high HbA1c level is typically seen in individuals with poorly controlled diabetes, where blood glucose levels remain elevated over an extended period (usually 2-3 months).
    Diabetes: Most commonly associated with uncontrolled Type 1 and Type 2 diabetes. When blood sugar levels remain high, glucose binds to hemoglobin in red blood cells, raising HbA1c levels.
    Increased Red Blood Cell Turnover: Conditions that cause the destruction of red blood cells, such as hemolytic anemia, may lead to falsely high HbA1c levels. This is because the new red blood cells formed from this increased turnover have less time to be glycated.
    Kidney Disease: Chronic kidney disease can lead to impaired clearance of glucose from the blood, causing high blood sugar levels and, consequently, high HbA1c levels.
    Stress: Physical or emotional stress can lead to an increase in blood sugar levels due to the release of stress hormones (like cortisol), which raise glucose levels.
    Poor Diet: A diet high in refined carbohydrates and sugars can contribute to consistently high blood glucose, increasing HbA1c levels.
    Medications: Certain medications, such as corticosteroids, can raise blood glucose levels and increase HbA1c.

Tips:
    Improve Blood Sugar Control: If you have diabetes, work with your healthcare provider to adjust your medication (insulin, oral hypoglycemics) and improve blood sugar monitoring.
    Exercise Regularly: Physical activity helps to increase insulin sensitivity, lower blood glucose, and improve HbA1c.
    Dietary Modifications: Adopt a balanced diet rich in whole grains, vegetables, lean proteins, and healthy fats to stabilize blood sugar levels.
    Monitor for Complications: Elevated HbA1c levels over time can increase the risk of diabetes complications (e.g., neuropathy, kidney disease, cardiovascular issues). Regular check-ups are important to prevent or manage these issues.
    Manage Stress: Stress can worsen blood sugar control. Consider incorporating relaxation techniques, such as meditation, deep breathing exercises, and yoga.
    Track Your Progress: Keep a food journal, monitor blood glucose regularly, and work with your healthcare provider to adjust treatment plans as necessary.

Foods to Eat:
    Complex Carbohydrates: Whole grains like quinoa, barley, and brown rice to provide steady energy without spiking blood glucose.
    Non-Starchy Vegetables: Leafy greens (spinach, kale), broccoli, cauliflower, and bell peppers for fiber and low glycemic index (GI) options.
    Lean Protein: Skinless poultry, fish, beans, and legumes to stabilize blood sugar and support muscle repair.
    Healthy Fats: Avocados, olive oil, chia seeds, and walnuts to support heart health and prevent blood sugar spikes.
    Cinnamon and Turmeric: Both spices are believed to help with blood sugar regulation. Add them to meals or beverages for flavor and health benefits.

Example Meal Plan for High HbA1c:
    Breakfast: Scrambled eggs with spinach and a side of whole-grain toast (protein and complex carbs).
    Lunch: Grilled salmon with quinoa, a spinach salad, and olive oil dressing (lean protein, complex carbs, and healthy fats).
    Snack: A handful of almonds and an apple (healthy fats and fiber).
    Dinner: Grilled chicken with roasted Brussels sprouts and sweet potato (lean protein, non-starchy vegetables, and complex carbs).
""")

    # Triglycerides (range: 150 mg/dL)
    if "Triglycerides" in values:
        if values["Triglycerides"] > 150:
            advice.append("""High Triglycerides (Hypertriglyceridemia)

Root Cause:
    Obesity or Overweight: Being overweight or obese, especially with excess abdominal fat, is a primary cause of high triglycerides. It increases the production of triglycerides in the liver and reduces the clearance of these fats.
    Poor Diet: Diets high in refined carbohydrates, sugars, trans fats, and saturated fats can increase triglyceride levels.
    Diabetes: Poorly controlled diabetes, particularly type 2, can lead to elevated triglycerides due to insulin resistance, which reduces the body's ability to regulate fat metabolism.
    Excessive Alcohol Consumption: Drinking alcohol in excess can significantly increase triglyceride levels as the liver converts alcohol into fats.
    Hypothyroidism: Underactive thyroid (hypothyroidism) can lead to higher triglyceride levels due to slowed metabolism and impaired fat breakdown.
    Kidney Disease: Chronic kidney disease or nephrotic syndrome can result in higher triglyceride levels due to disturbances in lipid metabolism and kidney function.
    Genetic Factors: Familial hypertriglyceridemia is a genetic disorder that causes extremely high triglyceride levels in some people.
    Medications: Certain drugs, including corticosteroids, diuretics, beta-blockers, and some HIV medications, can raise triglyceride levels.

Tips:
    Adopt a Low-Carb, Low-Sugar Diet: Reducing intake of sugary foods, refined carbohydrates (white bread, pasta, pastries), and high-fructose corn syrup can help lower triglycerides.
    Exercise Regularly: Aim for at least 30 minutes of aerobic exercise (such as walking, swimming, or cycling) most days of the week. Exercise helps reduce triglyceride levels by improving metabolism.
    Lose Weight: Losing even a small amount of weight (5-10% of body weight) can have a significant effect on lowering triglyceride levels.
    Avoid Alcohol: Limit or avoid alcohol, as it can significantly increase triglyceride levels, particularly in individuals who are overweight or have diabetes.
    Increase Omega-3 Fatty Acids: Omega-3 fatty acids, found in fish, flaxseeds, and walnuts, have been shown to lower triglycerides. Consider adding more of these to your diet.
    Control Blood Sugar: If you have diabetes, work with your healthcare provider to keep blood glucose levels under control to prevent high triglycerides.
    Consider Medications: If lifestyle changes alone do not sufficiently reduce triglyceride levels, your doctor may recommend medications such as fibrates, statins, or omega-3 fatty acid supplements.

Foods to Eat:
    Omega-3 Fatty Acids: Fatty fish (salmon, mackerel), flaxseeds, chia seeds, walnuts to help lower triglycerides.
    Fiber-Rich Foods: Oats, barley, legumes, and vegetables that help lower cholesterol and triglycerides.
    Healthy Fats: Olive oil, avocado, and nuts (such as almonds and walnuts) to provide healthy monounsaturated and polyunsaturated fats.
    Leafy Greens and Vegetables: Spinach, kale, broccoli, cauliflower to provide antioxidants and fiber while lowering triglyceride levels.
    Whole Grains: Brown rice, quinoa, and whole wheat to replace refined grains and provide more fiber and nutrients.

Example Meal Plan for High Triglycerides:
    Breakfast: Oatmeal with chia seeds, flaxseeds, and fresh berries (fiber, omega-3s, and antioxidants).
    Lunch: Grilled salmon with a quinoa salad, avocado, and a mixed greens salad with olive oil dressing (lean protein, omega-3s, and healthy fats).
    Snack: A handful of walnuts and a pear (healthy fats and fiber).
    Dinner: Baked chicken with roasted Brussels sprouts and sweet potatoes (lean protein, complex carbs, and non-starchy vegetables).
""")

    # Total Cholesterol (range: 125-200 mg/dL)
    if "Total Cholesterol" in values:
        if values["Total Cholesterol"] < 125:
            advice.append("""Low Total Cholesterol (Hypocholesterolemia)

Root Cause:
    Good Diet and Lifestyle: A diet that is rich in fruits, vegetables, whole grains, and lean proteins, while low in saturated and trans fats, can contribute to low total cholesterol levels. Regular physical activity also helps maintain healthy cholesterol levels.
    Hyperthyroidism: An overactive thyroid gland speeds up metabolism and can lead to lower cholesterol levels.
    Liver Disease: Chronic liver disease or cirrhosis can impair the liver's ability to produce cholesterol, leading to low total cholesterol levels.
    Malnutrition or Starvation: Inadequate intake of fats and other essential nutrients due to malnutrition, anorexia, or prolonged fasting can cause low cholesterol.
    Genetic Factors: Some rare genetic conditions, such as familial hypocholesterolemia, can cause abnormally low cholesterol levels.
    Chronic Infections or Inflammatory Diseases: Conditions such as tuberculosis or severe systemic inflammation can lead to decreased cholesterol production by the liver.
    Medications: Certain medications, like statins or other cholesterol-lowering drugs, may result in lower total cholesterol levels, sometimes too low if not properly managed.

Tips:
    Ensure Adequate Caloric Intake: If you're experiencing low cholesterol due to malnutrition, it's important to consume a balanced diet with adequate calories, healthy fats, and proteins to restore normal cholesterol levels.
    Include Healthy Fats: Healthy fats (from sources like avocados, olive oil, nuts, seeds, and fatty fish) can help increase HDL (good) cholesterol and maintain overall cholesterol balance.
    Monitor Thyroid Function: If you have symptoms of hyperthyroidism (e.g., weight loss, rapid heartbeat), have your thyroid levels checked.
    Avoid Extreme Diets: If you are on a very restrictive or low-fat diet, consult with a nutritionist to ensure you're still getting the nutrients needed for healthy cholesterol production.
    Regular Check-Ups: If you have a medical condition (like liver disease or inflammatory disease), ensure regular medical check-ups to manage the condition effectively and monitor cholesterol levels.

Foods to Eat:
    Healthy Fats: Avocados, olive oil, nuts (such as almonds and walnuts), and seeds (like chia and flaxseeds) to boost healthy fat intake.
    Lean Proteins: Skinless poultry, fatty fish (like salmon and mackerel), tofu, and legumes to support overall health.
    Whole Grains: Brown rice, quinoa, oats, and barley to provide complex carbohydrates, fiber, and essential nutrients.
    Fruits and Vegetables: Dark leafy greens (spinach, kale), cruciferous vegetables (broccoli, cauliflower), and antioxidant-rich fruits (berries, oranges).

Example Meal Plan for Low Total Cholesterol:
    Breakfast: Oatmeal with chia seeds, ground flaxseeds, walnuts, and fresh berries (fiber, healthy fats, and antioxidants).
    Lunch: Grilled salmon salad with avocado, mixed greens, quinoa, and olive oil dressing (lean protein, omega-3s, and healthy fats).
    Snack: A handful of almonds and a banana (healthy fats and potassium).
    Dinner: Baked chicken with roasted sweet potatoes and steamed broccoli (lean protein, complex carbs, and non-starchy vegetables).
""")
        elif values["Total Cholesterol"] > 200:
            advice.append("""High Total Cholesterol (Hypercholesterolemia)

Root Cause:
    Unhealthy Diet: A diet high in saturated fats (from red meat, dairy products, and processed foods), trans fats, and refined carbohydrates (sugar, white bread, pastries) can increase total cholesterol levels, particularly LDL (bad cholesterol).
    Obesity: Excess body weight, especially abdominal fat, is a significant contributor to high cholesterol levels. Obesity reduces the body's ability to clear excess cholesterol and increases the production of triglycerides, leading to higher cholesterol.
    Sedentary Lifestyle: Lack of physical activity can contribute to elevated cholesterol levels, as exercise helps to increase HDL (good cholesterol) and lower LDL and triglycerides.
    Genetic Factors: Familial hypercholesterolemia, a genetic disorder, can lead to elevated cholesterol levels, particularly elevated LDL cholesterol, which can increase the risk of cardiovascular diseases.
    Diabetes: Uncontrolled diabetes or insulin resistance can lead to higher cholesterol levels. Insulin resistance affects lipid metabolism and increases production of VLDL (very-low-density lipoprotein) and LDL cholesterol.
    Hypothyroidism: An underactive thyroid can impair cholesterol metabolism, leading to elevated levels of LDL and total cholesterol.
    Kidney Disease: Chronic kidney disease can also lead to higher cholesterol levels due to disturbances in lipid metabolism.
    Medications: Certain medications like steroids, diuretics, and beta-blockers can contribute to elevated cholesterol levels.

Tips:
    Adopt a Heart-Healthy Diet: Focus on a diet rich in fiber, healthy fats (like omega-3 fatty acids), and low in saturated and trans fats. This helps lower LDL and raise HDL levels.
    Exercise Regularly: Engaging in at least 30 minutes of moderate-intensity aerobic activity, such as walking, cycling, or swimming, can help lower total cholesterol, particularly by boosting HDL.
    Lose Weight: Losing excess weight, especially abdominal fat, can help improve cholesterol levels, lower triglycerides, and reduce overall heart disease risk.
    Avoid Smoking: Quitting smoking can improve HDL cholesterol levels and reduce the risk of cardiovascular disease.
    Manage Stress: Chronic stress can contribute to poor diet choices and unhealthy cholesterol levels, so incorporating relaxation techniques, such as yoga or meditation, is helpful.
    Monitor Diabetes: If you have diabetes, work with your healthcare provider to control your blood sugar levels, as uncontrolled blood sugar can increase total cholesterol.

Foods to Eat:
    Omega-3 Fatty Acids: Fatty fish (salmon, mackerel, sardines), flaxseeds, chia seeds, and walnuts, which help lower LDL cholesterol and triglycerides while raising HDL cholesterol.
    Fiber-Rich Foods: Oats, barley, beans, lentils, and vegetables, as they help lower LDL cholesterol by binding with it in the digestive system.
    Healthy Fats: Olive oil, avocado, nuts (especially almonds, walnuts), and seeds, which help reduce LDL and raise HDL cholesterol.
    Fruits and Vegetables: Dark leafy greens (kale, spinach), cruciferous vegetables (broccoli, cauliflower), and antioxidant-rich fruits (berries, apples, citrus).
    Legumes and Whole Grains: Beans, lentils, quinoa, and whole grains to help reduce cholesterol and support overall cardiovascular health.

Example Meal Plan for High Total Cholesterol:
    Breakfast: Oatmeal with chia seeds, flaxseeds, and fresh berries (fiber and omega-3s).
    Lunch: Grilled salmon with a mixed greens salad, avocado, olive oil, and a side of quinoa (healthy fats, fiber, and lean protein).
    Snack: A small handful of almonds and an apple (healthy fats and fiber).
    Dinner: Grilled chicken with roasted Brussels sprouts and sweet potatoes (lean protein, complex carbs, and non-starchy vegetables).""")

    # LDL Cholesterol (range: < 100 mg/dL)
    if "LDL Cholesterol" in values:
        if values["LDL Cholesterol"] > 130:
            advice.append("""High LDL Cholesterol (Low-Density Lipoprotein Cholesterol)

Root Cause:
    Unhealthy Diet: A diet rich in saturated fats (found in red meat, butter, cheese, and full-fat dairy products) and trans fats (found in processed foods, baked goods, and fried foods) increases LDL cholesterol levels.
    Obesity: Excess weight, particularly abdominal fat, can lead to higher LDL cholesterol levels. Obesity affects lipid metabolism, leading to an increase in "bad" cholesterol (LDL) and triglycerides.
    Sedentary Lifestyle: Lack of physical activity reduces the body’s ability to break down LDL cholesterol and increase HDL cholesterol (the "good" cholesterol), leading to an imbalance.
    Genetic Factors (Familial Hypercholesterolemia): A genetic disorder that results in high cholesterol, particularly high LDL levels, and a higher risk of cardiovascular diseases at an early age.
    Diabetes: Insulin resistance and poorly controlled blood sugar can lead to an increase in LDL cholesterol and decrease HDL cholesterol, which can contribute to higher total cholesterol levels.
    Hypothyroidism: An underactive thyroid (hypothyroidism) slows down metabolism and cholesterol processing, resulting in higher LDL cholesterol levels.
    Kidney Disease: Chronic kidney disease can lead to dyslipidemia (abnormal levels of lipids in the blood), including high LDL cholesterol.
    Medications: Certain medications, such as corticosteroids, beta-blockers, and diuretics, can increase LDL cholesterol levels.
    Health Risks of High LDL Cholesterol:
    Atherosclerosis: High LDL levels can lead to the buildup of plaque in the arteries, narrowing and hardening them, which increases the risk of heart disease and stroke.
    Heart Disease: High LDL cholesterol is a significant risk factor for coronary artery disease (CAD), heart attacks, and other cardiovascular problems.
    Stroke: Increased LDL can also contribute to blocked blood vessels in the brain, raising the risk of stroke.

Tips:
    Adopt a Heart-Healthy Diet: Focus on eating foods that help lower LDL cholesterol while supporting overall heart health. This includes reducing your intake of saturated fats, trans fats, and cholesterol-rich foods.
    Exercise Regularly: Engage in at least 30 minutes of moderate-intensity exercise most days of the week. Aerobic activities, such as walking, swimming, cycling, and jogging, can help lower LDL cholesterol and raise HDL cholesterol.
    Maintain a Healthy Weight: Losing excess weight can help reduce LDL cholesterol levels and improve overall cardiovascular health.
    Quit Smoking: If you smoke, quitting can help improve your cholesterol levels and reduce the risk of heart disease and other health complications.
    Limit Alcohol Consumption: Excessive alcohol intake can raise LDL cholesterol and triglyceride levels, so it's important to limit consumption.
    Consider Medications: In some cases, lifestyle changes alone may not be enough to lower LDL cholesterol. Statins or other cholesterol-lowering medications may be prescribed by a healthcare provider.
    Manage Underlying Conditions: Control other conditions that can raise LDL levels, such as diabetes, hypothyroidism, and kidney disease, to better manage cholesterol levels.

Foods to Eat:
    Omega-3 Fatty Acids: Fatty fish (salmon, mackerel, sardines), flaxseeds, chia seeds, and walnuts can help lower LDL cholesterol while improving cardiovascular health.
    Fiber-Rich Foods: Soluble fiber (found in oats, barley, beans, lentils, apples, and carrots) helps lower LDL cholesterol by binding with cholesterol in the digestive system.
    Healthy Fats: Replace saturated fats with healthy monounsaturated and polyunsaturated fats. Foods like olive oil, avocado, nuts, and seeds support healthy cholesterol levels.
    Plant Sterols and Stanols: Found in fortified foods like margarine, orange juice, and yogurt drinks, these plant compounds can help lower LDL cholesterol.
    Whole Grains: Oats, quinoa, brown rice, and whole wheat bread are high in fiber and can help reduce LDL cholesterol levels.
    Fruits and Vegetables: Leafy greens (kale, spinach), cruciferous vegetables (broccoli, Brussels sprouts), and antioxidant-rich fruits (berries, citrus) help lower LDL cholesterol and provide essential nutrients.

Example Meal Plan for High LDL Cholesterol:
    Breakfast: Oatmeal with chia seeds, flaxseeds, and fresh berries (fiber and omega-3s).
    Lunch: Grilled salmon with a quinoa salad, mixed greens, avocado, and olive oil dressing (omega-3s, fiber, and healthy fats).
    Snack: A handful of almonds and an apple (healthy fats and fiber).
    Dinner: Baked chicken breast with roasted Brussels sprouts, sweet potatoes, and a side of mixed greens (lean protein, fiber, and antioxidants).""")

    # HDL Cholesterol (range: > 40 mg/dL for men, > 50 mg/dL for women)
    if "HDL Cholesterol" in values:
        if values["HDL Cholesterol"] < 40:
            advice.append("""Low HDL Cholesterol (High-Density Lipoprotein Cholesterol)

Root Cause:
    Unhealthy Diet: A diet high in refined sugars, trans fats, and unhealthy fats (saturated fats found in red meat, processed foods, and fried foods) can lead to low HDL cholesterol levels.
    Obesity: Excess body weight, especially abdominal fat, is associated with low levels of HDL cholesterol. Being overweight can also increase the levels of "bad" LDL cholesterol and triglycerides.
    Physical Inactivity: A sedentary lifestyle can lower HDL cholesterol levels. Regular exercise is crucial for raising HDL cholesterol.
    Smoking: Smoking damages blood vessels, reduces HDL cholesterol levels, and contributes to cardiovascular disease.
    Genetics: Some people are genetically predisposed to low HDL cholesterol, which can run in families. Genetic variations can affect how the body produces or breaks down HDL cholesterol.
    Type 2 Diabetes and Insulin Resistance: People with type 2 diabetes or insulin resistance often have lower HDL cholesterol levels because of metabolic imbalances that affect lipid metabolism.
    Chronic Inflammation: Inflammatory conditions like rheumatoid arthritis or chronic infections can contribute to reduced HDL cholesterol.
    Alcohol: While moderate alcohol consumption (especially red wine) may raise HDL cholesterol, heavy drinking can lead to lower HDL levels and other health problems.
    Medications: Some medications, such as anabolic steroids, beta-blockers, and certain diuretics, may lower HDL cholesterol levels.
    Health Risks of Low HDL Cholesterol:
    Cardiovascular Disease: Low HDL cholesterol is a major risk factor for heart disease. HDL helps remove excess cholesterol from the bloodstream, preventing plaque buildup in arteries.
    Increased Risk of Atherosclerosis: Low HDL levels are associated with an increased risk of plaque formation in arteries, leading to atherosclerosis and increasing the risk of heart attack and stroke.
    Metabolic Syndrome: Low HDL cholesterol is one of the markers for metabolic syndrome, a cluster of conditions that increase the risk of heart disease, stroke, and type 2 diabetes.

Tips:
    Adopt a Heart-Healthy Diet: A diet rich in healthy fats, particularly monounsaturated and polyunsaturated fats, can help increase HDL cholesterol. Avoid trans fats and limit saturated fats.
    Exercise Regularly: Aerobic exercises such as walking, jogging, cycling, and swimming can help raise HDL cholesterol levels. Aim for at least 30 minutes of moderate-intensity exercise most days of the week.
    Lose Excess Weight: Losing excess weight, particularly belly fat, can help raise HDL cholesterol and improve overall lipid profile.
    Quit Smoking: Stopping smoking can lead to a noticeable increase in HDL cholesterol levels, as smoking lowers HDL and damages blood vessels.
    Limit Alcohol Consumption: Moderate alcohol intake may help raise HDL cholesterol, but excessive alcohol consumption can harm the liver and overall health, leading to lower HDL levels.
    Manage Underlying Conditions: If you have conditions like type 2 diabetes, hypothyroidism, or metabolic syndrome, controlling them can help improve your HDL cholesterol levels.

Foods to Eat:
    Healthy Fats: Include monounsaturated fats (olive oil, avocado) and polyunsaturated fats (omega-3 fatty acids from fatty fish like salmon, walnuts, flaxseeds) in your diet to raise HDL cholesterol.
    Nuts and Seeds: Almonds, walnuts, flaxseeds, chia seeds, and sunflower seeds are rich in healthy fats and fiber, which can improve HDL cholesterol levels.
    Fatty Fish: Salmon, mackerel, sardines, and herring are excellent sources of omega-3 fatty acids, which help raise HDL cholesterol and improve heart health.
    Olive Oil: Extra virgin olive oil is rich in monounsaturated fats and antioxidants, which can help increase HDL cholesterol levels.
    Fiber-Rich Foods: Oats, barley, beans, lentils, and whole grains can help reduce LDL cholesterol and improve HDL levels by aiding in cholesterol excretion.
    Fruits and Vegetables: Berries, citrus fruits, dark leafy greens (spinach, kale), and cruciferous vegetables (broccoli, Brussels sprouts) are rich in antioxidants and fiber, which help improve HDL cholesterol.""")

    # VLDL Cholesterol (range: 2-30 mg/dL)
    if "VLDL Cholesterol" in values:
        if values["VLDL Cholesterol"] < 2:
            advice.append("""High VLDL Cholesterol (Very-Low-Density Lipoprotein Cholesterol)

Root Cause:
    Unhealthy Diet: A diet high in refined carbohydrates, sugars, and unhealthy fats (trans fats, saturated fats) can lead to high VLDL cholesterol levels. These fats increase the liver's production of VLDL, which is primarily composed of triglycerides.
    Obesity: Excess body weight, particularly abdominal fat, contributes to increased VLDL cholesterol. Obesity is associated with insulin resistance, which affects the liver’s ability to manage cholesterol production.
    Diabetes and Insulin Resistance: High blood sugar levels and insulin resistance can lead to increased production of VLDL, as the liver compensates by producing more triglycerides.
    Alcohol Consumption: Excessive alcohol intake can raise VLDL levels by increasing triglyceride production in the liver.
    Genetics: Some people inherit genetic conditions like familial hypertriglyceridemia, which leads to elevated VLDL cholesterol and triglycerides.
    Kidney Disease: Chronic kidney disease can lead to dyslipidemia, including high VLDL levels, due to impaired lipid metabolism.
    Hypothyroidism: An underactive thyroid can impair lipid metabolism, causing an increase in VLDL cholesterol.
    Health Risks of High VLDL Cholesterol:
    Atherosclerosis: VLDL cholesterol is rich in triglycerides, and its accumulation in the arteries can contribute to plaque formation, narrowing and hardening the arteries (atherosclerosis).
    Heart Disease: Elevated VLDL cholesterol can contribute to an increased risk of coronary artery disease (CAD), heart attacks, and stroke due to its impact on artery health.
    Metabolic Syndrome: High VLDL levels are a key feature of metabolic syndrome, a cluster of risk factors that increase the likelihood of heart disease, diabetes, and stroke.

Tips to Lower High VLDL Cholesterol:
    Limit Refined Carbs and Sugars: Reduce intake of refined sugars, white bread, pastries, and sugary beverages to decrease VLDL cholesterol levels.
    Reduce Saturated and Trans Fats: Cut back on saturated fats found in fatty meats, full-fat dairy, and processed foods, as well as trans fats in packaged baked goods, margarine, and fried foods.
    Increase Fiber Intake: High-fiber foods like oats, beans, lentils, and fruits can help lower VLDL cholesterol by binding with excess cholesterol and triglycerides in the digestive system.
    Exercise Regularly: Engage in aerobic activities such as walking, swimming, cycling, and jogging to improve lipid metabolism, raise HDL cholesterol (the "good" cholesterol), and lower triglycerides and VLDL.
    Lose Excess Weight: Maintaining a healthy weight, especially reducing abdominal fat, can lower VLDL cholesterol and reduce the risk of cardiovascular disease.
    Limit Alcohol Intake: Reduce alcohol consumption, as excessive drinking can increase VLDL cholesterol levels.
    Control Blood Sugar: If you have diabetes or insulin resistance, managing blood sugar levels with diet, exercise, and medications can help lower VLDL cholesterol.
    Consider Medications: In some cases, your healthcare provider may recommend medications, such as statins or fibrates, to help lower VLDL cholesterol and triglycerides.

Foods to Eat for High VLDL Cholesterol:
    Omega-3 Fatty Acids: Fatty fish like salmon, sardines, and mackerel, as well as flaxseeds and walnuts, can help lower VLDL cholesterol by reducing triglycerides.
    Soluble Fiber: Foods like oats, barley, beans, lentils, apples, and carrots help reduce triglyceride levels and improve overall lipid profile.
    Healthy Fats: Avocados, olive oil, and nuts (especially almonds and walnuts) are good sources of healthy monounsaturated fats that can improve lipid balance.
    Antioxidant-Rich Vegetables and Fruits: Leafy greens (spinach, kale), berries, citrus fruits, and cruciferous vegetables (broccoli, Brussels sprouts) can help improve lipid metabolism and reduce inflammation.
    Whole Grains: Quinoa, brown rice, and whole wheat bread are high in fiber and can help reduce triglycerides and lower VLDL cholesterol.""")
        elif values["VLDL Cholesterol"] > 11:
            advice.append("""Low VLDL Cholesterol

Root Cause:
    Very Low Fat Diet: A very restrictive diet that is extremely low in fats may result in low VLDL cholesterol levels, as VLDL is synthesized from triglycerides, which come from fat.
    Malnutrition or Starvation: A lack of essential fats in the diet due to malnutrition, anorexia, or prolonged fasting can lower VLDL cholesterol levels.
    Hyperthyroidism: An overactive thyroid can lead to a faster metabolism and reduced levels of cholesterol, including VLDL, due to altered lipid metabolism.
    Genetic Factors: Some rare genetic conditions, such as familial hypolipidemia, can lead to lower than normal levels of VLDL cholesterol.
    Certain Medications: Some medications, such as statins and fibrates (used to lower cholesterol and triglycerides), can lower VLDL cholesterol as part of their therapeutic effect.
    Liver Disease: In cases of severe liver dysfunction, the liver may not produce adequate amounts of lipoproteins like VLDL, leading to low levels.
    Health Considerations of Low VLDL Cholesterol:
    Nutrient Deficiency: Very low levels of VLDL cholesterol may suggest an inadequate intake of fats, which are essential for the absorption of fat-soluble vitamins (A, D, E, and K) and hormone production.
    Hormonal Imbalance: Cholesterol is vital for hormone production, including sex hormones, and very low cholesterol levels can lead to hormonal imbalances, affecting reproductive health and metabolism.
    Impaired Fat Metabolism: Very low VLDL cholesterol may indicate that the body is not metabolizing fats properly, which could result in fat-soluble nutrient deficiencies.

Tips to Increase Low VLDL Cholesterol:
    Increase Healthy Fats: Include more healthy fats in your diet, such as monounsaturated and polyunsaturated fats (from olive oil, avocados, nuts, and seeds) to boost VLDL levels.
    Ensure Adequate Caloric Intake: If you are not consuming enough calories or fats, consider increasing your calorie intake with nutrient-dense foods to support normal lipid metabolism.
    Incorporate Healthy Carbohydrates: Whole grains like quinoa, oats, and brown rice provide necessary energy and help regulate cholesterol and triglyceride levels.
    Avoid Very Low-Fat Diets: While it’s important to limit unhealthy fats, an excessively low-fat diet can also result in low VLDL cholesterol. Aim for a balanced intake of healthy fats.

Foods to Eat for Low VLDL Cholesterol:
    Healthy Fats: Include sources of healthy fats, such as avocados, olive oil, fatty fish (salmon, mackerel), nuts (almonds, walnuts), and seeds (flaxseeds, chia seeds).
    Lean Proteins: Lean meats (chicken, turkey), legumes, tofu, and low-fat dairy provide essential nutrients while supporting fat and cholesterol production.
    Whole Grains: Incorporate fiber-rich whole grains like quinoa, oats, and barley to support normal fat metabolism.
    Fruits and Vegetables: Focus on high-calorie fruits like bananas, avocados, and dried fruits, along with vegetables like sweet potatoes and carrots, to increase calorie intake in a healthy way.""")

    # Total Cholesterol / HDL Cholesterol Ratio (range: 3.5-5.0)
    if "Total Cholesterol / HDL Cholesterol Ratio" in values:
        if values["Total Cholesterol / HDL Cholesterol Ratio"] > 4.5:
            advice.append("""High Total Cholesterol / HDL Cholesterol Ratio

Root Cause:
    Unhealthy Diet: A diet high in saturated fats, trans fats, and cholesterol-rich foods can elevate total cholesterol levels while reducing HDL cholesterol, resulting in a higher ratio. Processed foods, fatty meats, fried foods, and full-fat dairy products contribute to this imbalance.
    Obesity: Excess body weight, particularly abdominal fat, increases total cholesterol levels and reduces HDL cholesterol, raising the total cholesterol to HDL ratio.
    Physical Inactivity: Lack of exercise can lead to high levels of total cholesterol and low levels of HDL cholesterol. Regular physical activity is essential for maintaining a healthy balance.
    Smoking: Smoking damages blood vessels and lowers HDL cholesterol, which increases the total cholesterol to HDL ratio and raises the risk of heart disease.
    Genetics: Familial hypercholesterolemia (a genetic condition) can result in high total cholesterol levels and a higher cholesterol ratio. Some people are genetically predisposed to have lower HDL levels, contributing to a higher ratio.
    Diabetes and Insulin Resistance: Poorly controlled diabetes or insulin resistance can increase total cholesterol levels while reducing HDL cholesterol, leading to a higher ratio.
    Chronic Stress: Long-term stress may negatively affect cholesterol metabolism, contributing to higher total cholesterol levels and lower HDL cholesterol.
    Hypothyroidism: An underactive thyroid can cause elevated total cholesterol levels and lower HDL cholesterol, increasing the cholesterol ratio.
    Health Risks of High Total Cholesterol / HDL Cholesterol Ratio:
    Cardiovascular Disease: A higher total cholesterol to HDL ratio is strongly associated with an increased risk of atherosclerosis, heart disease, stroke, and heart attacks. HDL cholesterol plays a protective role by removing excess cholesterol from the bloodstream, and low levels of HDL, combined with high total cholesterol, increase the risk of plaque buildup in arteries.
    Increased Risk of Stroke: High total cholesterol levels, particularly when paired with low HDL cholesterol, contribute to plaque formation in blood vessels, which can lead to a blockage in cerebral arteries, increasing the risk of stroke.
    Metabolic Syndrome: A high cholesterol ratio is a key marker for metabolic syndrome, a group of risk factors that increase the likelihood of developing heart disease, type 2 diabetes, and stroke.

Tips to Lower High Total Cholesterol / HDL Cholesterol Ratio:
    Eat a Heart-Healthy Diet: Focus on a diet rich in healthy fats (monounsaturated and polyunsaturated fats) and low in saturated fats and cholesterol. Increase fiber intake and avoid processed foods, trans fats, and refined sugars.
    Exercise Regularly: Regular aerobic exercise, such as walking, cycling, or swimming, can help lower total cholesterol and raise HDL cholesterol. Aim for at least 30 minutes of exercise most days of the week.
    Lose Weight: Reducing excess body fat, especially abdominal fat, can help improve your cholesterol balance and lower the cholesterol ratio.
    Quit Smoking: If you smoke, quitting can improve HDL cholesterol levels and lower your total cholesterol to HDL ratio.
    Limit Alcohol Intake: Excessive alcohol consumption can negatively impact cholesterol levels. While moderate alcohol intake may increase HDL cholesterol, heavy drinking raises total cholesterol and triglyceride levels.
    Control Diabetes and Insulin Resistance: Proper management of blood sugar levels, either through medication or lifestyle changes, can help improve your cholesterol balance and reduce the cholesterol ratio.
    Medications: In some cases, your healthcare provider may recommend cholesterol-lowering medications, such as statins, to reduce total cholesterol levels and improve the cholesterol ratio.

Foods to Eat for High Total Cholesterol / HDL Cholesterol Ratio:
    Healthy Fats: Replace unhealthy fats with healthy fats. Olive oil, avocados, nuts (such as almonds and walnuts), and seeds (like flaxseeds and chia seeds) help increase HDL cholesterol and reduce total cholesterol.
    Omega-3 Fatty Acids: Fatty fish (salmon, mackerel, sardines), walnuts, chia seeds, and flaxseeds are excellent sources of omega-3 fatty acids, which help reduce total cholesterol and triglyceride levels while boosting HDL cholesterol.
    Soluble Fiber: Foods rich in soluble fiber, such as oats, barley, beans, lentils, and fruits (apples, pears), help lower total cholesterol by binding to cholesterol in the digestive system and excreting it.
    Whole Grains: Quinoa, brown rice, and whole wheat bread are rich in fiber and help lower total cholesterol levels while supporting healthy cholesterol balance.
    Antioxidant-Rich Fruits and Vegetables: Leafy greens (spinach, kale), cruciferous vegetables (broccoli, Brussels sprouts), and antioxidant-rich fruits (berries, citrus) improve cholesterol metabolism and support overall heart health.

Example Meal Plan for High Total Cholesterol / HDL Cholesterol Ratio:
    Breakfast: Oatmeal with chia seeds, flaxseeds, walnuts, and fresh berries (fiber, omega-3s, and antioxidants).
    Lunch: Grilled salmon with quinoa, mixed greens, avocado, and olive oil dressing (omega-3s, healthy fats, and fiber).
    Snack: A handful of almonds and an apple (healthy fats and fiber).
    Dinner: Grilled chicken breast with roasted Brussels sprouts, sweet potatoes, and a side of mixed greens (lean protein, healthy fats, and antioxidants).""")

    # LDL Cholesterol / HDL Cholesterol Ratio (range: 1.0-3.5)
    if "LDL Cholesterol / HDL Cholesterol Ratio" in values:
        if values["LDL Cholesterol / HDL Cholesterol Ratio"] > 3:
            advice.append("""High LDL Cholesterol / HDL Cholesterol Ratio

Root Cause:
    Unhealthy Diet: A diet high in saturated fats (found in red meat, full-fat dairy, and processed foods) and trans fats (in fried and packaged foods) raises LDL (low-density lipoprotein) cholesterol levels while lowering HDL (high-density lipoprotein) cholesterol. This imbalance results in a high LDL/HDL ratio.
    Obesity: Excess body weight, especially visceral fat (fat around the abdomen), contributes to higher LDL cholesterol levels and lower HDL cholesterol levels, leading to an elevated ratio.
    Physical Inactivity: A lack of regular physical activity contributes to higher LDL cholesterol and lower HDL cholesterol levels, worsening the LDL/HDL ratio.
    Smoking: Smoking lowers HDL cholesterol, which in turn raises the LDL/HDL ratio, increasing the risk of heart disease and stroke.
    Genetics: Some individuals are genetically predisposed to having higher LDL cholesterol levels or lower HDL cholesterol levels, both of which contribute to a higher LDL/HDL ratio. Familial hypercholesterolemia is one such genetic condition.
    Diabetes and Insulin Resistance: Poorly controlled blood sugar, insulin resistance, and metabolic syndrome are often associated with higher LDL cholesterol levels and lower HDL cholesterol levels.
    Chronic Stress: Long-term stress may increase levels of LDL cholesterol and decrease HDL cholesterol, negatively affecting the LDL/HDL ratio.
    Hypothyroidism: An underactive thyroid slows down lipid metabolism, leading to elevated LDL cholesterol and lower HDL cholesterol.
    Health Risks of High LDL Cholesterol / HDL Cholesterol Ratio:
    Cardiovascular Disease: A high LDL/HDL ratio is strongly linked to an increased risk of heart disease. LDL cholesterol (the "bad" cholesterol) contributes to the buildup of plaque in the arteries, which can cause atherosclerosis (narrowing of arteries), leading to heart attacks, stroke, and other cardiovascular problems.
    Atherosclerosis: High levels of LDL cholesterol promote plaque buildup in blood vessels, which can obstruct blood flow and increase the risk of coronary artery disease, heart attack, and stroke.
    Increased Risk of Stroke: A high LDL/HDL ratio contributes to the formation of plaques that can break loose and form blood clots, blocking blood flow to the brain and causing a stroke.
    Metabolic Syndrome: An elevated LDL/HDL ratio is a key marker of metabolic syndrome, which increases the risk of type 2 diabetes, heart disease, and stroke.

Tips to Lower High LDL Cholesterol / HDL Cholesterol Ratio:
    Adopt a Heart-Healthy Diet: Focus on reducing saturated fats, trans fats, and cholesterol-rich foods while increasing your intake of healthy fats, fiber, and plant-based foods. Avoid processed and fried foods, and prioritize whole foods like fruits, vegetables, whole grains, and lean proteins.
    Exercise Regularly: Engage in aerobic activities like walking, swimming, cycling, or jogging to raise HDL cholesterol and lower LDL cholesterol. Aim for at least 30 minutes of moderate-intensity exercise on most days of the week.
    Lose Excess Weight: Reducing body fat, especially abdominal fat, can help lower LDL cholesterol levels and raise HDL cholesterol levels, improving the LDL/HDL ratio.
    Quit Smoking: Stopping smoking can help increase HDL cholesterol and improve your lipid profile by lowering LDL cholesterol.
    Limit Alcohol Intake: Excessive alcohol consumption can raise triglycerides and LDL cholesterol. Limiting alcohol can help improve the balance between LDL and HDL cholesterol.
    Control Blood Sugar and Insulin Resistance: If you have diabetes or metabolic syndrome, managing your blood sugar and insulin levels can help improve the LDL/HDL ratio.
    Consider Medications: In some cases, your healthcare provider may recommend medications such as statins or fibrates to help lower LDL cholesterol levels and improve the cholesterol ratio.

Foods to Eat for High LDL Cholesterol / HDL Cholesterol Ratio:
    Healthy Fats: Incorporate sources of healthy fats, such as olive oil, avocado, fatty fish (salmon, mackerel, sardines), and nuts (walnuts, almonds). These fats help increase HDL cholesterol and lower LDL cholesterol.
    Fiber-Rich Foods: Soluble fiber from oats, beans, lentils, apples, and other fruits and vegetables can help lower LDL cholesterol by binding to cholesterol and excreting it from the body.
    Omega-3 Fatty Acids: Fatty fish (salmon, mackerel, sardines), flaxseeds, chia seeds, and walnuts are rich in omega-3 fatty acids, which help reduce LDL cholesterol levels and raise HDL cholesterol.
    Whole Grains: Foods like quinoa, brown rice, and whole-wheat bread provide fiber and help lower LDL cholesterol levels while supporting overall heart health.
    Nuts and Seeds: Almonds, walnuts, chia seeds, and flaxseeds are great sources of healthy fats and fiber, which can help lower LDL cholesterol and improve HDL cholesterol.
    Antioxidant-Rich Vegetables and Fruits: Leafy greens (spinach, kale), berries, citrus fruits, and cruciferous vegetables (broccoli, Brussels sprouts) provide fiber, antioxidants, and essential nutrients that support cardiovascular health and improve cholesterol balance.
    Legumes and Plant-Based Proteins: Beans, lentils, tofu, and other plant-based protein sources are low in saturated fats and can help lower LDL cholesterol levels while supporting a balanced lipid profile.

Example Meal Plan for High LDL Cholesterol / HDL Cholesterol Ratio:
    Breakfast: Oatmeal with chia seeds, flaxseeds, walnuts, and fresh berries (fiber, healthy fats, and antioxidants).
    Lunch: Grilled salmon with quinoa, mixed greens, avocado, and olive oil dressing (omega-3s, healthy fats, and fiber).
    Snack: A handful of almonds and an apple (healthy fats and fiber).
    Dinner: Grilled chicken breast with roasted Brussels sprouts, sweet potatoes, and a side of mixed greens (lean protein, healthy fats, and antioxidants).""")

    # Total Bilirubin (range: 0.1-1.2 mg/dL)
    if "Total Bilirubin" in values:
        if values["Total Bilirubin"] > 1.2:
            advice.append("""High Total Bilirubin
Root Cause:
    Liver Disease: Elevated total bilirubin levels can indicate liver dysfunction. Conditions such as hepatitis (inflammation of the liver), cirrhosis (scarring of the liver tissue), and liver tumors can impair the liver’s ability to process and excrete bilirubin.
    Hemolysis (Increased Red Blood Cell Breakdown): Excessive breakdown of red blood cells can overwhelm the liver's capacity to process the bilirubin released from hemoglobin. This can occur due to hemolytic anemia, certain genetic conditions, or blood disorders.
    Gallbladder Disease: Blockages in the bile ducts or gallbladder issues (such as gallstones) can prevent bilirubin from being excreted, leading to increased bilirubin levels in the blood.
    Gilbert’s Syndrome: A genetic disorder where the liver has a reduced ability to process bilirubin efficiently, leading to temporary mild elevations in bilirubin, especially during times of stress, illness, or fasting.
    Biliary Obstruction: Any condition that obstructs the bile ducts, such as tumors or gallstones, can prevent bilirubin from being properly excreted, causing a buildup in the bloodstream.
    Alcoholism: Chronic alcohol consumption can lead to liver damage, which can impair bilirubin processing, resulting in higher bilirubin levels.
    Infections: Certain infections affecting the liver, such as viral hepatitis, malaria, or sepsis, can cause elevated bilirubin due to liver inflammation or cell destruction.
    Medications: Some medications (such as acetaminophen in large doses, certain antibiotics, and chemotherapy drugs) can cause liver toxicity and interfere with bilirubin metabolism.
    Health Risks of High Total Bilirubin:
    Jaundice: The most noticeable sign of high bilirubin levels is jaundice, a yellowing of the skin and eyes. This occurs because bilirubin, when accumulated in excess, starts to deposit in tissues, particularly in the skin.
    Liver Dysfunction: Persistently high levels of bilirubin may indicate an ongoing issue with liver function, which can lead to chronic liver disease or failure if not addressed.
    Gallbladder Issues: High bilirubin can be a sign of gallstones or bile duct obstruction, which may require surgical intervention.
    Anemia: If high bilirubin is due to hemolysis (destruction of red blood cells), it may lead to anemia, causing fatigue, weakness, and shortness of breath.
    Severe Complications: If not treated, persistently high bilirubin levels can result in further liver damage, bile duct injury, or complications in blood flow to and from the liver, all of which can be life-threatening.

Tips to Lower High Total Bilirubin Levels:
    Seek Medical Attention: If elevated bilirubin levels are due to liver disease, bile duct obstructions, or hemolysis, it's essential to identify and treat the underlying cause. Consult with a healthcare provider to assess liver function and determine the appropriate course of treatment.
    Avoid Alcohol: If high bilirubin levels are due to liver dysfunction caused by alcohol consumption, it is critical to stop drinking to prevent further liver damage.
    Manage Infections: If bilirubin levels are elevated due to infection (such as hepatitis), proper medical treatment, including antiviral medications and supportive care, is essential.
    Consider Gallbladder Health: If a gallbladder or bile duct blockage is the cause, addressing the issue through procedures such as surgery or medication may be necessary.
    Stay Hydrated: Adequate water intake helps the liver flush out toxins and process waste products like bilirubin more efficiently.
    Limit Medication Use: If medications are contributing to liver damage and elevated bilirubin, discuss alternatives with your doctor. Avoid self-medicating and follow the prescribed dosage and treatment plan.
    Monitor Blood Cell Health: If hemolysis (red blood cell destruction) is the cause of high bilirubin, managing underlying conditions (like autoimmune diseases or blood disorders) and preventing infections can help reduce hemolysis.

Foods to Eat for High Total Bilirubin:
    Liver-Friendly Foods: The liver plays a central role in processing bilirubin, so eating foods that support liver function can help. These include:
    Leafy Greens: Kale, spinach, and other dark leafy vegetables are rich in antioxidants and chlorophyll, which help detoxify the liver and improve its function.
    Cruciferous Vegetables: Broccoli, Brussels sprouts, and cabbage contain compounds that support liver detoxification pathways and reduce liver inflammation.
    Berries: Blueberries, strawberries, and raspberries are rich in antioxidants that protect liver cells from damage.
    Turmeric: This spice contains curcumin, which has anti-inflammatory properties and supports liver detoxification.
    Beets: Beets are rich in antioxidants and fiber, which help cleanse the liver and improve its ability to process bilirubin.
    Garlic: Garlic has sulfur compounds that support liver detoxification and may help reduce inflammation in liver tissue.
    Green Tea: Rich in antioxidants, particularly catechins, green tea has been shown to support liver function and detoxification.
    Lemon and Lime: These citrus fruits are rich in vitamin C and antioxidants that support liver health and enhance the liver’s detoxifying abilities.
    High-Fiber Foods: Foods rich in fiber (such as whole grains, oats, beans, and legumes) support overall digestion and bile flow, aiding in the processing and elimination of waste products like bilirubin.
    Healthy Fats: Include healthy fats like olive oil, nuts, seeds, and fatty fish (salmon, mackerel) in your diet. These fats support liver function and have anti-inflammatory effects.

Example Meal Plan for High Total Bilirubin:
    Breakfast: Oatmeal with chia seeds, blueberries, and a drizzle of honey (fiber, antioxidants, and liver-supporting compounds).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side of mixed greens with olive oil and lemon dressing (omega-3s, antioxidants, and fiber).
    Snack: A handful of walnuts and a small apple (healthy fats and fiber).
    Dinner: Grilled chicken breast with roasted beets, sautéed spinach with garlic, and a side of brown rice (protein, antioxidants, and liver-supporting vegetables).""")

    # Direct Bilirubin (range: 0.0-0.4 mg/dL)
    if "Direct Bilirubin" in values:
        if values["Direct Bilirubin"] > 0.2:
            advice.append("""High Direct Bilirubin (Conjugated Bilirubin)

Root Cause:
Liver Disease: Direct bilirubin is produced when unconjugated (indirect) bilirubin is processed in the liver and conjugated with glucuronic acid. If the liver is unable to properly conjugate bilirubin or if there is liver damage, direct bilirubin levels can rise. Conditions such as:
Hepatitis: Inflammation of the liver can impair its ability to conjugate and excrete bilirubin.
Cirrhosis: Scarring of the liver tissue can obstruct bile flow and hinder bilirubin processing.
Liver Cancer: Tumors or malignancy in the liver can disrupt the normal metabolic process, leading to elevated direct bilirubin levels.
Biliary Obstruction: Blockage in the bile ducts (from gallstones, bile duct tumors, or strictures) can prevent conjugated bilirubin from being excreted into the intestine, leading to a buildup of direct bilirubin in the blood.
Cholestasis: A condition where bile flow is impaired due to either intrahepatic (within the liver) or extrahepatic (outside the liver) causes. This can be seen in diseases like primary biliary cirrhosis or primary sclerosing cholangitis, leading to high direct bilirubin levels.
Gallstones: When gallstones obstruct the bile ducts, it prevents bile from flowing properly, causing the buildup of bilirubin in the bloodstream.
Dubin-Johnson Syndrome: A rare inherited disorder where the liver is unable to secrete conjugated bilirubin properly, resulting in its buildup in the bloodstream. This condition leads to mild to moderate increases in direct bilirubin.
Rotor Syndrome: Another rare inherited condition similar to Dubin-Johnson syndrome, causing elevated direct bilirubin levels due to improper bilirubin storage and transport.
Liver Toxicity from Medications: Certain medications, such as anabolic steroids, acetaminophen in high doses, or some antibiotics, can cause liver damage, impairing bilirubin metabolism and resulting in high direct bilirubin levels.
Health Risks of High Direct Bilirubin:
Jaundice: The primary symptom of high direct bilirubin levels is jaundice, which causes the skin and the whites of the eyes to turn yellow. This occurs due to the accumulation of bilirubin in the tissues.
Liver Dysfunction: Persistent high levels of direct bilirubin often point to liver dysfunction or bile duct obstruction. If left untreated, this could lead to further liver damage or complications such as cirrhosis or liver failure.
Cholestasis: If the bilirubin rise is due to cholestasis, it can result in bile buildup, causing itching, fatigue, and digestive issues.
Gallbladder or Bile Duct Issues: If high direct bilirubin is caused by gallstones or a blockage in the bile ducts, these conditions may require surgical or medical intervention to restore proper bile flow and prevent further complications.

Tips to Lower High Direct Bilirubin Levels:
Treat Underlying Conditions: The primary approach to lowering direct bilirubin levels is addressing the root cause. For example, treating hepatitis or cirrhosis, relieving bile duct obstructions, or addressing cholestasis can help lower direct bilirubin.
Avoid Alcohol: Alcohol can worsen liver damage, so if high direct bilirubin levels are due to liver disease, abstaining from alcohol is essential.
Control Infections: If high direct bilirubin is caused by infections (such as hepatitis or liver abscesses), it is crucial to receive appropriate treatment, such as antiviral or antibacterial medications.
Medications to Address Obstruction: In cases of bile duct obstruction, medications (such as ursodeoxycholic acid) or surgical interventions (such as gallstone removal or stent placement) may be needed to restore bile flow.
Cholestasis Management: For conditions like primary biliary cirrhosis or primary sclerosing cholangitis, medications that improve bile flow and reduce liver inflammation, such as ursodeoxycholic acid or immunosuppressive drugs, may be prescribed.
Regular Monitoring: For conditions like Dubin-Johnson syndrome or Rotor syndrome, regular monitoring of bilirubin levels and liver function is necessary to ensure that the condition remains stable and does not worsen.
Manage Medications: If high bilirubin is due to medication-induced liver damage, consult a healthcare provider about changing or adjusting the medications.

Foods to Eat for High Direct Bilirubin:
    Liver-Supportive Foods: Eating foods that support liver function and reduce inflammation is key in managing high direct bilirubin levels:
    Leafy Greens: Vegetables like spinach, kale, and Swiss chard provide antioxidants and help detoxify the liver.
    Cruciferous Vegetables: Broccoli, Brussels sprouts, and cauliflower promote liver detoxification and bile flow.
    Beets: Rich in antioxidants, beets support liver detoxification and bile processing.
    Garlic and Onions: These foods contain sulfur compounds that support liver detoxification and help reduce liver inflammation.
    Turmeric: Contains curcumin, which has anti-inflammatory properties and supports liver function.
    Green Tea: Packed with antioxidants, particularly catechins, green tea helps support liver health and can aid in detoxification.
    Berries: Blueberries, strawberries, and raspberries are rich in antioxidants that protect liver cells from oxidative stress.
    Healthy Fats: Incorporate sources of omega-3 fatty acids (such as salmon, walnuts, and flaxseeds) to reduce liver inflammation and support overall health.
    High-Fiber Foods: Fiber helps with overall digestion and detoxification. Include whole grains, oats, legumes, and vegetables in your diet.
    Bile-Stimulating Foods: Foods like artichokes, beets, and dandelion greens stimulate bile production, which can help with bile flow and reduce the buildup of bilirubin in the blood.

Example Meal Plan for High Direct Bilirubin:
    Breakfast: Oatmeal with chia seeds, blueberries, and a handful of walnuts (fiber, antioxidants, and healthy fats).
    Lunch: Grilled salmon with quinoa, steamed broccoli, and a side of kale salad with olive oil and lemon dressing (omega-3s, liver-supporting vegetables).
    Snack: A small handful of almonds and a green tea (healthy fats and antioxidants).
    Dinner: Grilled chicken breast with roasted beets, sautéed spinach with garlic, and a side of brown rice (protein, liver-supporting foods, and fiber).""")

    # Indirect Bilirubin (range: 0.1-0.7 mg/dL)
    if "Indirect Bilirubin" in values:
        if values["Indirect Bilirubin"] > 1:
            advice.append("""High Indirect Bilirubin (Unconjugated Bilirubin)

Root Cause:
    Hemolysis (Increased Red Blood Cell Breakdown): The most common cause of elevated indirect bilirubin is the accelerated breakdown of red blood cells. When red blood cells are destroyed prematurely, they release hemoglobin, which is then broken down into heme and bilirubin. The liver can only process a limited amount of unconjugated bilirubin, so an excess can build up in the blood. Hemolysis can be caused by:
    Hemolytic Anemia: Conditions like sickle cell anemia, thalassemia, autoimmune hemolytic anemia, or certain infections can cause excessive destruction of red blood cells.
    Infections: Certain infections, such as malaria, can lead to the destruction of red blood cells, releasing more heme and indirectly increasing bilirubin levels.
    Transfusion Reactions: If a person receives a blood transfusion with incompatible blood, it can cause the destruction of red blood cells (hemolysis) and raise indirect bilirubin levels.
    Liver Dysfunction: While the liver primarily processes unconjugated bilirubin, severe liver damage can impair its ability to process and clear indirect bilirubin. Conditions like cirrhosis, hepatitis, and alcoholic liver disease can contribute to high indirect bilirubin levels.
    Gilbert’s Syndrome: A common genetic disorder where the liver has a reduced ability to process bilirubin. It typically leads to mild elevations in indirect bilirubin, especially during stress, illness, or fasting.
    Crigler-Najjar Syndrome: A rare inherited disorder in which the liver is unable to conjugate bilirubin due to a deficiency in the enzyme UDP-glucuronosyltransferase. This leads to high levels of unconjugated bilirubin.
    Neonatal Jaundice: In newborns, high indirect bilirubin levels can occur as a result of the immature liver’s inability to process bilirubin effectively. This condition usually resolves with phototherapy or other treatments.
    Sepsis or Other Systemic Infections: Infections can lead to hemolysis, liver dysfunction, or both, contributing to elevated indirect bilirubin levels.
    Medications: Certain drugs, like chemotherapy agents, some antibiotics, and anti-inflammatory drugs, can contribute to hemolysis or liver damage, leading to higher indirect bilirubin levels.
    Health Risks of High Indirect Bilirubin:
    Jaundice: One of the most common symptoms of high indirect bilirubin is jaundice, which manifests as a yellowing of the skin and eyes. This occurs when the liver cannot efficiently process and excrete excess bilirubin.
    Anemia: When hemolysis is the cause of elevated indirect bilirubin, the destruction of red blood cells can lead to anemia. Symptoms of anemia include fatigue, weakness, dizziness, and shortness of breath.
    Liver Dysfunction: In cases where liver disease is causing high indirect bilirubin, liver function may decline, leading to symptoms such as nausea, loss of appetite, abdominal pain, and swelling.
    Neurotoxicity in Neonates: In newborns, very high levels of indirect bilirubin (often referred to as "kernicterus") can cause brain damage. This condition is preventable and treatable when diagnosed early.
    Fatigue and Weakness: If high indirect bilirubin is caused by hemolytic anemia, the excessive breakdown of red blood cells leads to fatigue, weakness, and overall reduced oxygen-carrying capacity in the blood.

Tips to Lower High Indirect Bilirubin Levels:
    Treat Underlying Causes: The most effective way to reduce indirect bilirubin is to treat the underlying cause, whether it's managing hemolytic anemia, addressing liver dysfunction, or treating infections.
    Address Hemolysis: If hemolysis is the cause, it’s important to manage the underlying condition causing the breakdown of red blood cells. This may involve:
    Blood Transfusions: In severe cases, a blood transfusion may be necessary to replace destroyed red blood cells.
    Immunosuppressive Therapy: In cases of autoimmune hemolytic anemia, corticosteroids or other immunosuppressive drugs may be used.
    Iron Supplementation: If anemia is caused by blood loss or hemolysis, iron supplements may be necessary to restore red blood cell production.
    Manage Liver Disease: If liver dysfunction is contributing to high indirect bilirubin, appropriate treatments may include antiviral medications for hepatitis, alcohol cessation for alcoholic liver disease, and other supportive therapies.
    Avoid Stress and Fasting: For individuals with Gilbert’s syndrome, avoiding prolonged fasting, stress, or dehydration can help prevent further increases in bilirubin levels. It's important to maintain a well-balanced diet and avoid situations that can trigger elevated bilirubin.
    Medications Adjustment: If medications are causing increased bilirubin, speak with a healthcare provider about switching to alternative drugs that do not affect bilirubin processing or cause hemolysis.
    Monitor Bilirubin Levels in Newborns: For newborns, regular monitoring of bilirubin levels is essential. Phototherapy or exchange transfusion may be required to manage high indirect bilirubin and prevent brain damage.

Foods to Eat for High Indirect Bilirubin:
    Liver-Supporting Foods: The liver is involved in processing bilirubin, so eating foods that support liver function can help. These include:
    Leafy Greens: Spinach, kale, and other dark green vegetables contain antioxidants that support liver health and detoxification.
    Cruciferous Vegetables: Broccoli, cauliflower, and Brussels sprouts are rich in compounds that help improve liver detoxification.
    Garlic and Onions: These contain sulfur compounds that promote liver detoxification and improve bile flow.
    Beets: Rich in antioxidants and fiber, beets help cleanse the liver and promote efficient bilirubin processing.
    Turmeric: Contains curcumin, which supports liver health by reducing inflammation and promoting detoxification.
    Green Tea: Packed with antioxidants, green tea helps the liver process toxins and supports overall liver function.
    Berries: Blueberries, strawberries, and raspberries are high in antioxidants that help protect liver cells from oxidative damage.
    Foods Rich in Vitamin C: Vitamin C supports liver function and detoxification. Include citrus fruits, strawberries, kiwi, and bell peppers in your diet.
    Iron-Rich Foods: If hemolysis is contributing to anemia, eating iron-rich foods (such as red meat, lentils, and spinach) can help replenish red blood cells.
    High-Fiber Foods: Fiber supports digestion and helps with detoxification, which can aid in reducing bilirubin levels. Include whole grains, oats, and legumes in your diet.
    Healthy Fats: Healthy fats, such as those from avocados, olive oil, and fatty fish like salmon, reduce inflammation and support liver health.

Example Meal Plan for High Indirect Bilirubin:
    Breakfast: Oatmeal with chia seeds, fresh berries, and a sprinkle of flaxseeds (fiber, antioxidants, and omega-3s).
    Lunch: Grilled salmon with steamed broccoli, quinoa, and a spinach salad with olive oil and lemon (omega-3s, liver-friendly vegetables).
    Snack: A handful of almonds and an orange (healthy fats and vitamin C).
    Dinner: Grilled chicken breast with roasted beets, sautéed kale with garlic, and a side of brown rice (protein, liver support, and fiber).""")

    # SGPT/ALT (range: 7-56 U/L)
    if "SGPT/ALT" in values:
        if values["SGPT/ALT"] > 50:
            advice.append("""High SGPT/ALT (Serum Glutamic Pyruvic Transaminase / Alanine Aminotransferase)

Root Cause:
    Liver Damage or Disease: SGPT/ALT is an enzyme found mainly in the liver. Elevated levels typically indicate liver injury or disease, as this enzyme is released into the bloodstream when liver cells are damaged. Common causes include:
    Hepatitis: Both viral (e.g., Hepatitis B, C, A) and non-viral (e.g., autoimmune hepatitis) can lead to liver inflammation and elevated SGPT levels.
    Fatty Liver Disease: Fat accumulation in liver cells can cause non-alcoholic fatty liver disease (NAFLD), which may lead to elevated ALT/SGPT levels.
    Cirrhosis: Advanced liver scarring (due to chronic liver conditions like hepatitis or excessive alcohol use) can cause high ALT levels.
    Liver Toxicity from Medications: Certain drugs (like acetaminophen in large doses, statins, some antibiotics, and antifungals) can cause liver damage and elevated ALT levels.
    Alcoholic Liver Disease: Excessive alcohol consumption can lead to liver inflammation, fat deposition, and liver cell damage, resulting in increased SGPT levels.
    Liver Cancer: Cancer in the liver can cause liver cells to break down, releasing ALT into the bloodstream.
    Hemochromatosis: This is a condition in which excess iron accumulates in the body, potentially leading to liver damage and elevated ALT levels.
    Wilson’s Disease: A genetic disorder that causes copper buildup in the liver, leading to liver damage and increased SGPT/ALT levels.
    Mononucleosis (Infectious Mono): Viral infections such as mononucleosis can lead to inflammation of the liver and elevated SGPT.
    Cholestasis (Bile Flow Blockage): Conditions such as gallstones or bile duct obstruction can cause a buildup of bile, leading to liver stress and increased ALT levels.
    Health Risks of High SGPT/ALT:
    Liver Dysfunction: Persistently elevated SGPT/ALT levels may signal ongoing liver damage, which can lead to further liver complications such as cirrhosis or liver failure if untreated.
    Jaundice: A sign of liver dysfunction, where bilirubin builds up in the bloodstream, causing yellowing of the skin and eyes.
    Fatigue and Weakness: When the liver is inflamed or damaged, the body may have difficulty processing nutrients and toxins, leading to feelings of fatigue or weakness.
    Ascites: A condition where fluid accumulates in the abdomen due to advanced liver disease, which can occur with high SGPT/ALT levels related to cirrhosis or liver failure.
    Abdominal Pain: Liver inflammation or liver damage often causes discomfort in the upper right side of the abdomen.

Tips to Lower High SGPT/ALT Levels:
    Treat Underlying Liver Conditions: The key to lowering ALT levels is addressing the root cause of liver damage, whether it’s treating hepatitis, managing fatty liver disease, stopping alcohol consumption, or using specific treatments for liver-related conditions.
    Antiviral Medications: For hepatitis infections, antiviral medications (like interferons or nucleoside analogs) may be prescribed.
    Weight Loss: In cases of non-alcoholic fatty liver disease (NAFLD), gradual weight loss (5-10% of body weight) can reduce fat in the liver and lower ALT levels.
    Control Blood Sugar: If diabetes or insulin resistance is contributing to fatty liver disease, controlling blood sugar through diet and medications (like metformin) can help reduce ALT levels.
    Avoid Alcohol: Alcohol consumption exacerbates liver damage and can significantly increase ALT levels, especially in those with alcoholic liver disease or fatty liver disease.
    Discontinue Medications that Harm the Liver: If medications are contributing to elevated ALT levels, consult a healthcare provider to adjust the treatment plan or switch to medications with fewer liver side effects.
    Manage Iron Overload: For conditions like hemochromatosis, where excess iron damages the liver, therapeutic phlebotomy (blood removal) or iron chelation therapy can help reduce iron levels and protect the liver.
    Reduce Liver Inflammation: Use of medications like corticosteroids or other immunosuppressive drugs may be necessary for autoimmune hepatitis or liver inflammation.
    Follow a Liver-Friendly Diet: Certain foods can help support liver function and reduce ALT levels.

Foods to Eat for High SGPT/ALT:
    Antioxidant-Rich Foods: Antioxidants help reduce oxidative stress in the liver, improving liver function and supporting recovery:
    Leafy Greens: Spinach, kale, and collard greens are rich in vitamins and minerals that promote liver health and detoxification.
    Berries: Blueberries, strawberries, and raspberries provide antioxidants that reduce liver inflammation.
    Beets: High in antioxidants and fiber, beets help detoxify the liver and support its natural cleansing processes.
    Green Tea: Contains catechins, powerful antioxidants that help protect liver cells from damage and support liver function.
    Healthy Fats: Fatty fish (like salmon and mackerel), olive oil, and flaxseeds contain omega-3 fatty acids that reduce liver inflammation and help repair liver cells.
    Cruciferous Vegetables: Broccoli, Brussels sprouts, and cauliflower help improve liver detoxification and bile production.
    Garlic and Onion: Rich in sulfur compounds, these foods help the liver detoxify and improve bile flow.
    Turmeric: Contains curcumin, a powerful anti-inflammatory compound that supports liver health and reduces liver inflammation.
    Fiber-Rich Foods: High-fiber foods like oats, legumes, and whole grains promote liver detoxification and reduce fat buildup in the liver.
    Vitamin C-Rich Foods: Citrus fruits (oranges, lemons, grapefruits), bell peppers, and kiwi are all rich in vitamin C, which supports detoxification and liver health.
    Fresh Ginger: Known for its anti-inflammatory properties, ginger can support the liver in reducing inflammation and promoting digestion.

Example Meal Plan for High SGPT/ALT:
    Breakfast: Oatmeal with chia seeds, a handful of mixed berries (blueberries, strawberries), and a teaspoon of ground flaxseeds (fiber, antioxidants, omega-3s).
    Lunch: Grilled salmon with steamed broccoli, quinoa, and a spinach salad with olive oil and lemon dressing (omega-3s, liver-friendly vegetables).
    Snack: A handful of almonds and a cup of green tea (healthy fats and antioxidants).
    Dinner: Stir-fried vegetables (beets, kale, and cauliflower) with garlic and turmeric, served with brown rice and a side of roasted chicken (detoxifying foods and lean protein).""")

    # SGOT/AST (range: 5-40 U/L)
    if "SGOT/AST" in values:
        if values["SGOT/AST"] > 50:
            advice.append("""High SGOT/AST (Serum Glutamic Oxaloacetic Transaminase / Aspartate Aminotransferase)

Root Cause:
    Liver Damage or Disease: Like SGPT/ALT, SGOT/AST is an enzyme found in the liver and other tissues, such as the heart, muscles, kidneys, and brain. Elevated AST levels indicate damage to these tissues, with the liver being the most common source.
    Hepatitis: Both viral (e.g., Hepatitis B, C, A) and non-viral (e.g., autoimmune hepatitis) can cause liver inflammation, leading to increased AST levels.
    Fatty Liver Disease (NAFLD): Non-alcoholic fatty liver disease is caused by fat buildup in the liver, which may lead to liver inflammation and elevated AST.
    Cirrhosis: Advanced liver scarring (from chronic conditions such as alcohol use or hepatitis) can cause a significant increase in AST levels.
    Alcoholic Liver Disease: Chronic alcohol consumption can damage liver cells, resulting in increased AST.
    Liver Cancer: Liver malignancy (either primary or metastasized) can damage liver cells, releasing AST into the bloodstream.
    Muscle Injury or Damage: AST is also present in muscles. Muscle injuries, trauma, or conditions like rhabdomyolysis (severe muscle breakdown) can cause AST to increase.
    Heart Conditions: AST is found in high concentrations in the heart, so conditions like myocardial infarction (heart attack) or heart failure can lead to elevated AST levels.
    Hemochromatosis: A condition characterized by excessive iron buildup in the body, leading to liver damage and higher AST levels.
    Wilson’s Disease: Genetic disorder leading to copper accumulation in the liver, which can cause AST to rise.
    Mononucleosis (Infectious Mono): Viral infections can lead to liver inflammation, causing elevated AST.
    Cholestasis: Obstruction in the bile ducts or gallstones can impair bile flow, stress the liver, and cause an increase in AST levels.
    Medications and Toxins: Drugs like acetaminophen (in overdose), statins, antibiotics, and antifungals can cause liver damage, raising AST levels.

Health Risks of High SGOT/AST:
    Liver Dysfunction: High AST levels often suggest liver injury, which can lead to further liver damage if the underlying cause is not addressed.
    Muscle Damage: If elevated AST is due to muscle injury (e.g., rhabdomyolysis), it can lead to muscle weakness, pain, and potentially kidney failure.
    Heart Damage: Elevated AST levels due to heart-related issues (e.g., myocardial infarction) can indicate a heart attack or heart failure, requiring urgent medical attention.
    Fatigue and Weakness: Elevated AST levels associated with liver or muscle damage often lead to fatigue, muscle weakness, and overall reduced energy.
    Jaundice: Liver dysfunction associated with high AST levels can lead to jaundice, where the skin and eyes turn yellow due to an accumulation of bilirubin.
    Abdominal Pain: In liver diseases or gallbladder problems, high AST levels can be accompanied by abdominal pain or discomfort, especially in the upper right side.

Tips to Lower High SGOT/AST Levels:
    Treat Underlying Liver Conditions: Addressing the root cause of liver dysfunction is essential in lowering AST levels.
    Antiviral Treatments: If hepatitis is the cause of high AST levels, antiviral medications (such as interferons or nucleoside analogs) may help reduce inflammation.
    Fatty Liver Management: Gradual weight loss (5-10% of body weight) can reduce liver fat and inflammation, lowering AST levels. A balanced diet, exercise, and managing insulin resistance can help.
    Alcohol Cessation: Stopping alcohol consumption is critical if alcohol-related liver disease or cirrhosis is present.
    Managing Iron Overload: If hemochromatosis is present, treatment through phlebotomy (blood removal) or iron chelation therapy may help reduce iron buildup and lower AST.
    Medications Adjustment: Discontinuing or switching medications that may be causing liver toxicity can prevent further elevation in AST.
    Heart Treatment: If high AST is due to heart damage, appropriate treatments for heart disease, such as medications for heart failure, or interventions for myocardial infarction, may be needed.
    Muscle Injury Treatment: If muscle damage is contributing to elevated AST, rest, hydration, and appropriate medical care for conditions like rhabdomyolysis are necessary to prevent kidney damage and muscle breakdown.
    Avoid Toxins and Harmful Substances: Avoid exposure to substances that could harm the liver, such as alcohol, certain drugs, and toxins.

Foods to Eat for High SGOT/AST:
    Liver-Supporting Foods: Focus on foods that promote liver health and detoxification:
    Leafy Greens: Spinach, kale, and other greens are rich in nutrients that help detoxify the liver and improve its function.
    Cruciferous Vegetables: Broccoli, cauliflower, and Brussels sprouts support liver detoxification and reduce fat buildup.
    Beets: High in antioxidants, beets help cleanse the liver and reduce oxidative stress.
    Turmeric: Contains curcumin, which has anti-inflammatory properties and helps reduce liver inflammation.
    Green Tea: Rich in antioxidants, green tea supports liver health and helps detoxify the body.
    Berries: Blueberries, strawberries, and raspberries are high in antioxidants, which help protect liver cells from oxidative damage.
    Omega-3 Fatty Acids: Fatty fish (like salmon, mackerel, and sardines), walnuts, and flaxseeds provide omega-3 fatty acids, which reduce liver inflammation and support liver function.
    Garlic and Onion: These contain sulfur compounds that enhance liver detoxification and promote bile production.
    Fiber-Rich Foods: Oats, quinoa, and legumes are rich in fiber, which supports liver function by aiding digestion and improving detoxification processes.
    Vitamin C-Rich Foods: Citrus fruits (oranges, grapefruits), bell peppers, and kiwi support liver function and act as antioxidants.
    Healthy Fats: Incorporate healthy fats from olive oil, avocados, and nuts, which are good for liver health and help reduce inflammation.

Example Meal Plan for High SGOT/AST:
    Breakfast: Oatmeal topped with chia seeds, mixed berries (blueberries and strawberries), and a sprinkle of flaxseeds (fiber, antioxidants, and omega-3s).
    Lunch: Grilled salmon with a side of steamed broccoli and quinoa, along with a spinach salad with olive oil and lemon (healthy fats, liver-friendly vegetables, and lean protein).
    Snack: A handful of almonds and a cup of green tea (healthy fats and antioxidants).
    Dinner: Stir-fried vegetables (beets, kale, and Brussels sprouts) with garlic and turmeric, served with brown rice and grilled chicken (detoxifying foods and protein).""")

    # Alkaline Phosphatase (range: 44-147 U/L)
    if "Alkaline Phosphatase" in values:
        if values["Alkaline Phosphatase"] > 115:
            advice.append("""High Alkaline Phosphatase (ALP)

Root Cause:
    Liver Conditions:
        Bile Duct Obstruction (Cholestasis): Blockages in the bile ducts, such as from gallstones, tumors, or strictures, can cause elevated ALP as it is involved in bile secretion. Conditions like primary biliary cirrhosis or primary sclerosing cholangitis may also raise ALP levels.
        Hepatitis: Liver inflammation caused by viral or autoimmune hepatitis can elevate ALP.
        Liver Tumors: Primary or metastatic liver cancer can lead to high ALP levels due to liver cell damage.
        Fatty Liver Disease: Non-alcoholic fatty liver disease (NAFLD) can cause mild elevation in ALP levels due to liver inflammation.
        Bone Conditions
        Osteomalacia and Rickets: These are bone diseases caused by vitamin D deficiency, leading to abnormal bone mineralization and elevated ALP levels.
        Paget’s Disease of Bone: This disorder involves abnormal bone remodeling, which can cause elevated ALP.
        Bone Fractures or Healing: When bones are healing, ALP levels can temporarily rise due to increased bone activity.
        Osteoporosis: In severe cases of bone loss, ALP may be elevated.
        Bone Cancer or Metastasis: If cancer has spread to the bones, it can increase ALP production.
    Other Causes:
        Hyperparathyroidism: Overactivity of the parathyroid glands can lead to increased calcium and ALP levels due to bone resorption.
        Pregnancy: ALP levels are often higher during pregnancy, particularly in the third trimester, due to placental production.
        Infections: Some infections like osteomyelitis (bone infection) or infectious mononucleosis can elevate ALP levels.
        Health Risks of High ALP:
        Liver Dysfunction: Persistently high ALP may indicate liver damage or bile duct obstruction, leading to jaundice, abdominal pain, or more severe liver conditions.
        Bone Weakness or Pain: If the cause of high ALP is related to bone disease (e.g., Paget's disease, osteomalacia), it can result in bone deformities, fractures, or pain.
        Hypercalcemia: Conditions like hyperparathyroidism or osteolytic bone disease can lead to elevated calcium levels in the blood, causing symptoms like nausea, fatigue, kidney stones, and bone pain.

Tips to Lower High ALP:
    Treat Underlying Liver Diseases: Address liver conditions, such as viral hepatitis, cirrhosis, or fatty liver disease, to prevent further liver damage and restore normal ALP levels.
    Manage Bone Conditions: Correct vitamin D deficiency or manage diseases like Paget’s disease and osteomalacia with appropriate medications, supplements (like calcium or vitamin D), and lifestyle changes.
    Surgical Intervention for Blockages: For bile duct obstructions (e.g., gallstones or tumors), surgical or non-surgical treatments to remove the blockage can help lower ALP levels.
    Avoid Alcohol: Alcohol can worsen liver conditions and lead to higher ALP levels. Reducing alcohol consumption can help support liver health.
    Calcium Regulation: If hyperparathyroidism or bone loss is the cause, treatment to normalize calcium levels (via medications or surgery) can lower ALP levels.

Foods to Eat for High ALP:
        Liver-Supportive Foods
        Leafy Greens: Spinach, kale, and other dark leafy greens are excellent for supporting liver health.
        Berries: Blueberries and strawberries contain antioxidants that protect the liver and reduce inflammation.
        Garlic and Turmeric: Both are anti-inflammatory and help improve liver detoxification.
        Fatty Fish: Omega-3-rich fish like salmon, mackerel, and sardines help reduce inflammation in the liver and bones.
        Bone-Healthy Foods:
        Dairy: Calcium-rich foods like milk, yogurt, and cheese support bone health.
        Fortified Foods: Vitamin D-fortified foods (e.g., fortified cereals or plant-based milk) are essential for healthy bone metabolism.
        Nuts and Seeds: Almonds, chia seeds, and flaxseeds provide magnesium, which supports both bone and muscle health.
    """)

    # Total Protein (range: 6.0-8.3 g/dL)
    if "Total Protein" in values:
        if values["Total Protein"] < 6.6:
            advice.append("""Low Total Protein

Root Cause:
    Malnutrition or Poor Diet
    Protein Deficiency: Inadequate protein intake from the diet can cause a reduction in total protein levels. This is common in malnutrition, eating disorders (e.g., anorexia nervosa), or insufficient dietary intake.
    Starvation: Prolonged lack of food or calorie intake can result in a decrease in the body's ability to produce proteins.
    Liver Cirrhosis: Severe liver damage from conditions like cirrhosis or hepatitis can impair the liver’s ability to produce proteins like albumin, leading to low total protein levels.
    Acute Hepatitis: Acute liver inflammation can temporarily impair protein synthesis in the liver, causing a decrease in total protein levels.
    Nephrotic Syndrome: A kidney condition in which protein is excessively lost through urine, leading to low protein levels in the blood (hypoalbuminemia).
    Chronic Kidney Disease: Impaired kidney function can result in protein loss in urine, leading to low protein levels in the blood.
    Malabsorption Syndromes: Conditions like celiac disease, Crohn’s disease, or chronic diarrhea can prevent the absorption of proteins and nutrients, leading to low total protein levels.
    Protein-Losing Enteropathy: A condition in which proteins are lost through the intestines, leading to low protein levels in the blood.
    Sepsis: Severe infections or systemic inflammation (such as in sepsis) can cause a decrease in total protein levels.
    Burns or Trauma: Major injuries or burns can cause protein loss as the body uses proteins for tissue repair and healing.
    Hypothyroidism:An underactive thyroid can sometimes lead to low total protein levels, affecting protein metabolism in the body.

Health Risks of Low Total Protein:
    Edema: One of the most common symptoms of low total protein, especially low albumin, is edema (fluid retention) in the legs, abdomen, and other areas.
    Weak Immune Function: Proteins, especially antibodies, are crucial for immune function. Low protein levels can weaken the immune system, increasing susceptibility to infections.
    Muscle Weakness: Protein is essential for muscle structure and function. Low total protein levels can result in muscle weakness, fatigue, and poor recovery after exertion.
    Wound Healing Issues: Since proteins are key in tissue repair, low levels can delay healing after surgery or injury.
    Malnutrition and Growth Problems: In children, low protein levels can impair growth and development, while in adults, it may lead to fatigue and other health issues.

Tips to Raise Low Total Protein:
    Increase Protein Intake: Ensure a diet rich in high-quality protein sources. Aim for sources such as lean meats, fish, eggs, dairy products, legumes, and nuts.
    Lean Meats: Chicken, turkey, and lean cuts of beef are great protein-rich foods.
    Legumes: Beans, lentils, and chickpeas are plant-based protein sources that can supplement the diet.
    Dairy: Incorporating milk, cheese, and yogurt can help boost protein levels.
    Eggs: Eggs are one of the most complete sources of protein and can easily be added to meals.
    Address Malabsorption Issues: If gastrointestinal conditions like celiac disease or Crohn’s disease are contributing to protein deficiency, work with a healthcare provider to manage the condition and improve nutrient absorption.
    Liver Disease: Treat liver conditions with appropriate medications or lifestyle changes (e.g., avoiding alcohol) to improve protein production.
    Kidney Disease: If protein loss due to kidney disease is a concern, managing kidney function and using medications as prescribed will help retain protein in the body.
    Hypothyroidism: Treatment with thyroid hormones (e.g., levothyroxine) can improve overall metabolism and protein production.

Foods to Eat for Low Total Protein:
    Eggs and Lean Meats: As mentioned, these are excellent sources of complete protein.
    Fish and Shellfish: Salmon, tuna, and shrimp are all rich in protein and healthy fats.
    Nuts and Seeds: Almonds, chia seeds, and sunflower seeds provide protein and healthy fats.
    Dairy Products: Greek yogurt, milk, and cheese are protein-packed options.
    Legumes: Lentils, black beans, and chickpeas are good plant-based proteins.
    Vegetables and Fruits for Supporting Metabolism:
    Leafy Greens: Kale, spinach, and Swiss chard help support overall health and protein metabolism.
    Sweet Potatoes and Squash: High in carbohydrates and micronutrients, these can help boost overall nutrition.
""")
        elif values["Total Protein"] > 8.3:
            advice.append("""High Total Protein

Root Cause:
    Chronic Infections (e.g., tuberculosis, HIV/AIDS) or inflammatory conditions (e.g., rheumatoid arthritis, systemic lupus erythematosus) can lead to an increase in the production of certain proteins like immunoglobulins (antibodies), which can elevate total protein levels.
    Multiple Myeloma: A type of blood cancer that causes an abnormal increase in plasma cells, leading to high levels of immunoglobulins (particularly monoclonal proteins, or M-proteins).
    Chronic Liver Disease: In some cases of chronic liver disease (e.g., cirrhosis), the liver may produce more proteins in an attempt to repair itself, resulting in high total protein levels.
    Dehydration:Dehydration can cause a relative increase in total protein levels. When the body is dehydrated, there is less fluid in the blood, making the concentration of proteins appear higher than it actually is. It does not necessarily reflect an increase in protein production but rather a decreased volume of plasma.
    Monoclonal Gammopathy:Monoclonal Gammopathy of Undetermined Significance (MGUS): A condition in which abnormal proteins (monoclonal proteins) are produced, leading to increased total protein levels without symptoms. Waldenström’s 
    Macroglobulinemia: A rare type of cancer that causes high production of IgM (an antibody), resulting in increased total protein levels.
    Liver Conditions:Liver cirrhosis or liver failure: In some cases, these conditions may lead to an increase in certain proteins, particularly the liver's production of clotting factors.
    Hepatitis: Inflammation of the liver can also lead to an increase in protein levels in some cases.
    Nephrotic Syndrome: This kidney disorder can cause the body to produce higher-than-normal levels of proteins, leading to elevated total protein levels.
    
Health Risks of High Total Protein:
    Multiple Myeloma and Blood Disorders: High total protein due to abnormal immunoglobulin levels (M-proteins) can indicate plasma cell disorders, such as multiple myeloma or Waldenström’s macroglobulinemia.
    Chronic Dehydration: Long-term dehydration can lead to electrolyte imbalances and kidney strain, affecting overall health.
    Liver and Kidney Diseases: High protein levels in the blood may indicate worsening liver or kidney function and the need for treatment or closer monitoring.

Tips to Lower High Total Protein:
    Address Underlying Conditions: Treatment for multiple myeloma, infections, liver disease, or dehydration is necessary to normalize protein levels.
    Multiple Myeloma: Chemotherapy, stem cell therapy, or other treatments for blood cancers can help reduce the abnormal proteins.
    Chronic Liver or Kidney Disease: Medications to manage liver or kidney function, or specific interventions (e.g., diuretics for fluid balance), may help.
    Hydration: Proper hydration is essential to reduce apparent increases in total protein levels due to dehydration. Aim for 6-8 cups of water daily, or more depending on individual needs.
    Monitor and Manage Inflammation: Anti-inflammatory medications may help control underlying inflammatory conditions that contribute to high protein levels.

Foods to Eat for High Total Protein:
    Antioxidant-Rich Foods: Berries (e.g., blueberries, strawberries) and leafy greens (e.g., spinach, kale) may help reduce inflammation.
    Anti-Inflammatory Fats: Omega-3-rich foods such as salmon, mackerel, walnuts, and flaxseeds may help reduce inflammation and support overall protein metabolism.
    Hydration: Drink adequate water to help manage dehydration-related protein concentration.""")

    # Albumin (range: 3.5-5.0 g/dL)
    if "Albumin" in values:
        if values["Albumin"] < 3.5:
            advice.append("""Low Albumin (Hypoalbuminemia)

Root Cause:
    Cirrhosis or Hepatitis: Chronic liver conditions can impair the liver’s ability to produce albumin, leading to low levels in the blood.
    Acute Liver Failure: Sudden liver damage, possibly due to toxins, viral infections, or medications, can also cause a sharp drop in albumin production.
    Nephrotic Syndrome: This kidney disorder leads to significant loss of albumin through urine. In nephrotic syndrome, the kidneys are damaged, allowing proteins like albumin to leak out.
    Chronic Kidney Disease: Progressive kidney damage can also lead to decreased albumin levels as the kidneys cannot retain proteins.
    Protein Deficiency: Inadequate intake of protein from the diet can result in decreased production of albumin, leading to low levels. This is commonly seen in cases of severe malnutrition or eating disorders.
    Inflammation and Infection:
    Chronic Inflammatory States: Conditions such as rheumatoid arthritis, systemic lupus erythematosus, or sepsis can lead to low albumin levels due to inflammatory cytokines reducing albumin synthesis.
    Acute Infections: Severe infections can result in low albumin as part of the body’s acute-phase response.
    Malabsorption Syndromes: Conditions like Celiac disease, Crohn's disease, and Chronic diarrhea can impair the absorption of nutrients and proteins, leading to low albumin levels.
    Protein-Losing Enteropathy: A condition in which protein is lost through the intestines, leading to a decrease in albumin levels.
    Congestive Heart Failure (CHF): This condition can cause fluid retention and edema, diluting albumin levels in the blood.
    Extensive burns or trauma can lead to the loss of proteins, including albumin, from the blood and tissues, resulting in low levels.

Health Risks of Low Albumin:
    Edema: Low albumin levels can lead to fluid buildup in the tissues, resulting in swelling (edema), particularly in the legs, abdomen (ascites), and around the eyes.
    Weakened Immune System: Albumin carries essential immune factors. Low levels can impair immune function, leading to increased risk of infections.
    Muscle Weakness: Reduced protein levels can affect muscle function, leading to weakness, fatigue, and delayed recovery after physical exertion or illness.
    Impaired Wound Healing: Albumin is vital for tissue repair, and low levels may delay healing from injuries, surgeries, or illnesses.
    Hypotension: Low albumin levels may lead to low blood pressure (hypotension), as the blood’s ability to retain fluid in the bloodstream is compromised.

Tips to Raise Low Albumin:
    Increase Protein Intake: Ensure a diet rich in high-quality protein sources to support albumin production.
    Animal-Based Proteins: Include lean meats (chicken, turkey), fish, eggs, and dairy products (milk, yogurt, cheese).
    Plant-Based Proteins: Beans, lentils, quinoa, tofu, nuts, and seeds are excellent protein sources.
    Treat Underlying Liver or Kidney Diseases: If low albumin is due to liver or kidney disease, specific medical treatments such as medications, lifestyle changes (e.g., avoiding alcohol for liver disease), or dialysis (for kidney disease) may be necessary.
    Address Malabsorption or Inflammatory Conditions: Work with a healthcare provider to manage conditions like celiac disease, Crohn’s disease, or inflammatory conditions that impair nutrient absorption and protein production.
    Hydration: While dehydration is not a direct cause of low albumin, it can exacerbate symptoms of edema and low protein concentrations in the blood. Ensure adequate hydration but avoid excessive fluid intake in the case of kidney or heart conditions.

Foods to Eat for Low Albumin:
    Protein-Rich Foods:Eggs, lean meats, fish, and dairy products (milk, cheese, yogurt) are some of the best sources of protein.
    Nuts and Seeds (almonds, chia seeds, sunflower seeds) and legumes (lentils, chickpeas, beans) are also good plant-based protein options.
    Vitamins and Minerals:Leafy greens like spinach and kale help improve overall nutrition.
    Sweet potatoes, carrots, and citrus fruits provide antioxidants and micronutrients that support immune health and protein metabolism.""")
        elif values["Albumin"] > 5.2:
            advice.append("""High Albumin (Hyperalbuminemia)

Root Cause:
    Severe Dehydration: The most common cause of high albumin levels is dehydration. When the body loses fluid, such as in cases of excessive vomiting, diarrhea, or sweating, the concentration of albumin in the blood can increase because the blood volume decreases.
    Excessive Protein Intake: In rare cases, very high levels of protein intake from supplements or food can contribute to slightly elevated albumin levels.
    Gastrointestinal Bleeding:Blood Loss from the gastrointestinal tract can increase albumin levels due to a reduction in plasma volume, resulting in a relative increase in albumin concentration.
    HIV/AIDS:In some cases, HIV/AIDS can cause elevated albumin levels due to the body's efforts to fight the infection and replenish proteins.
    Anabolic Steroid Use:The use of anabolic steroids or excessive use of certain medications can lead to elevated protein levels in the blood, including albumin.
    Certain Bone Marrow Disorders like Polycythemia Vera: A blood disorder causing an overproduction of red blood cells, which can result in a relative increase in albumin levels due to reduced plasma volume.

Health Risks of High Albumin:
    Dehydration: Chronic dehydration can lead to other health complications, such as kidney stones, electrolyte imbalances, and kidney damage.
    Increased Blood Viscosity: Excessive albumin levels due to dehydration can increase blood viscosity (thickness), leading to higher risks of blood clot formation and cardiovascular complications.
    Impaired Circulation: High albumin levels in the blood may reduce the flow of oxygen and nutrients to tissues, leading to poor circulation and possible organ dysfunction.

Tips to Lower High Albumin:
    Increase Fluid Intake: Hydration is key in managing high albumin levels. Drink sufficient water, especially in cases of dehydration. A good target is 6-8 cups of water per day or more based on individual needs and health conditions.
    Monitor Protein Intake: If excessive protein intake is contributing to high albumin, consider adjusting the amount of protein in your diet to more moderate levels, especially if you're taking protein supplements.
    Address Underlying Conditions: Treat the underlying causes such as dehydration or gastrointestinal bleeding to normalize albumin levels.

Foods to Eat for High Albumin:
    Hydration: Focus on water, coconut water, and herbal teas to rehydrate.
    Electrolyte-Rich Foods: Consider foods like bananas, oranges, spinach, and potatoes to help balance electrolytes and maintain proper hydration.
""")

    # Globulin (range: 2.0-3.5 g/dL)
    if "Globulin" in values:
        if values["Globulin"] < 1.8:
            advice.append("""Low Globulin (Hypoglobulinemia)

Root Cause:
    Liver Cirrhosis: The liver produces most of the globulins. When the liver is damaged due to cirrhosis or hepatitis, its ability to produce these proteins may be impaired, leading to low globulin levels.
    Acute Liver Failure: In severe liver damage, the liver may fail to produce enough globulins, contributing to low levels.
    Nephrotic Syndrome: This kidney disorder causes significant protein loss through urine, including globulins, which results in low levels in the blood.
    Gastrointestinal Disorders: Conditions like protein-losing enteropathy (where proteins are lost through the intestines) can result in low globulin levels.
    Severe Burns or Trauma: Protein loss due to burns or trauma can also lower globulin levels as the body loses proteins needed for tissue repair.
    Primary Immunodeficiencies: Some inherited conditions (like X-linked agammaglobulinemia) impair the production of globulins, particularly immunoglobulins (antibodies), resulting in low globulin levels.
    Immunosuppressive Therapy: Medications used to suppress the immune system (e.g., for autoimmune diseases or organ transplants) can lead to decreased globulin production.
    Protein Deficiency: Inadequate intake of protein or severe malnutrition can lead to a lack of building blocks required for globulin synthesis, resulting in low globulin levels.
    Aplastic Anemia: This condition involves the bone marrow not producing enough blood cells, including the globulins, which can result in low globulin levels.
    Acute and Chronic Infections:
    Some infections, especially chronic ones, can affect the liver and immune system, leading to reduced globulin levels.
    Chronic Inflammatory Diseases:Conditions like rheumatoid arthritis or lupus can lead to a decrease in globulin production over time due to altered immune function.

Health Risks of Low Globulin:
    Weakened Immune System: Globulins, especially immunoglobulins, are essential for immune defense. Low levels can leave the body more susceptible to infections.
    Edema: Since globulins help maintain fluid balance, low globulin levels can lead to fluid accumulation in the tissues (edema), especially in the legs and abdomen.
    Delayed Healing: Globulins, particularly the immunoglobulins (antibodies), are vital for infection defense and tissue repair, so low levels may result in delayed healing of wounds or injuries.
    Increased Risk of Blood Clots: Globulins play a role in blood clotting. Low levels can affect the body’s ability to form proper blood clots, increasing the risk of bleeding.

Tips to Raise Low Globulin:
    Increase Protein Intake: Globulins are proteins, so increasing dietary protein intake can help the body produce more globulins.
    Animal-Based Proteins: Include sources like lean meats, fish, eggs, and dairy products (milk, cheese, yogurt).
    Plant-Based Proteins: Consider beans, lentils, quinoa, tofu, nuts, and seeds.
    Treat Underlying Conditions:If liver disease, kidney disease, or a bone marrow disorder is causing low globulin levels, treatments for those conditions (e.g., antiviral therapy for hepatitis, dialysis for nephrotic syndrome, or immunosuppressive drugs for autoimmune diseases) may help improve globulin levels.
    Malnutrition: A proper diet or nutritional supplements can help address protein deficiencies and support globulin production.
    Immunoglobulin Replacement: In cases where there is a deficiency in immunoglobulins (such as in immunodeficiency disorders), immunoglobulin replacement therapy may be recommended by a healthcare provider.
    Manage Inflammatory Conditions: Treat chronic inflammatory diseases (such as rheumatoid arthritis or lupus) with appropriate medications (e.g., anti-inflammatory drugs, biologics) to help restore normal globulin levels.

Foods to Eat for Low Globulin:
    Protein-Rich Foods: Eggs, lean meats, fish, poultry, tofu, and dairy products are good sources of protein to support globulin production.
    Nuts (almonds, walnuts) and seeds (sunflower seeds, chia seeds) are also rich in protein.
    Legumes (lentils, chickpeas, beans) and whole grains (quinoa, oats) provide plant-based protein.
    Vitamins and Minerals:Leafy greens like spinach and kale, and fruits such as citrus fruits, provide antioxidants and vitamins that support the immune system.
    """)
        elif values["Globulin"] > 3.6:
            advice.append("""High Globulin (Hyperglobulinemia)

Root Cause:
    Chronic Bacterial Infections: Infections such as tuberculosis, chronic sinusitis, or endocarditis can trigger the immune system to produce more globulins, especially antibodies (immunoglobulins).
    Viral Infections: Some viral infections, including hepatitis, HIV, and chronic Epstein-Barr virus (EBV) infection, may lead to elevated globulin levels.
    Rheumatoid Arthritis: This condition leads to chronic inflammation and immune system activation, resulting in elevated globulin levels.
    Systemic Lupus Erythematosus (SLE): Lupus is another autoimmune disease that triggers increased production of globulins, especially immunoglobulins.
    Multiple Myeloma:Multiple Myeloma is a type of cancer that affects plasma cells in the bone marrow, leading to overproduction of certain types of immunoglobulins (known as monoclonal proteins or M proteins), which can significantly increase globulin levels.
    Chronic Liver Disease:Cirrhosis or other chronic liver conditions can lead to an increase in globulin production as part of the body’s response to ongoing inflammation and tissue damage.
    Monoclonal Gammopathy:Monoclonal Gammopathy of Undetermined Significance (MGUS) is a condition in which abnormal proteins are produced, leading to elevated globulin levels without the typical symptoms of cancer.
    Dehydration:Like other proteins, dehydration can cause a relative increase in globulin concentration due to a decreased plasma volume, making the globulins appear higher than they actually are.
    Bone Marrow Disorders:Waldenström's Macroglobulinemia: A cancerous condition involving abnormal production of IgM immunoglobulin (macroglobulin) by plasma cells, which can increase globulin levels.
    Polycythemia Vera: A blood disorder that can also lead to high globulin levels.
    
Health Risks of High Globulin:
    Chronic Inflammation and Immune Dysregulation: Elevated globulin levels due to chronic infections or autoimmune diseases can lead to excessive immune system activity, potentially damaging tissues and organs.
    Multiple Myeloma: High globulin levels due to excessive immunoglobulin production (particularly M proteins) can lead to kidney damage, bone pain, and anemia in multiple myeloma.
    Blood Clotting Issues: High levels of immunoglobulins can alter blood viscosity, leading to increased clotting risks, particularly in conditions like Waldenström's macroglobulinemia.

Tips to Lower High Globulin:
    Treat Underlying Conditions:For chronic infections or autoimmune diseases, managing the root cause with medications (antibiotics, antivirals, immunosuppressants, or biologics) can help normalize globulin levels.
    Cancer Treatment: If multiple myeloma or Waldenström's macroglobulinemia is the cause, chemotherapy, stem cell therapy, or targeted therapies may be necessary.
    Manage Dehydration:Ensure proper hydration to dilute the concentration of globulins in the blood. Drink adequate amounts of water or electrolyte-rich beverages.
    Monitor and Manage Chronic Conditions:If elevated globulins are due to chronic inflammatory conditions (e.g., rheumatoid arthritis, lupus), anti-inflammatory treatments or biologics may help normalize globulin levels.
    Dialysis or Plasmapheresis:In some cases, particularly with blood disorders like multiple myeloma, plasmapheresis or dialysis may be needed to remove excess proteins from the blood.

Foods to Eat for High Globulin:
    Anti-Inflammatory Diet:Omega-3 fatty acids: Foods like salmon, walnuts, and flaxseeds help reduce inflammation.
    Antioxidant-Rich Fruits and Vegetables: Berries, leafy greens, and cruciferous vegetables (broccoli, cauliflower) can help fight chronic inflammation.
    Spices: Turmeric, ginger, and garlic have anti-inflammatory properties that may help manage chronic inflammation.""")


        # Protein A/G Ratio (range: 1.0-2.5)
    if "Protein A/G Ratio" in values:
        if values["Protein A/G Ratio"] < 0.8:
            advice.append("""Low Protein A/G Ratio
A low A/G ratio occurs when the globulin levels are higher than albumin levels. This imbalance may indicate an underlying health problem.

Root Cause:
    Chronic Inflammatory Diseases: Conditions like rheumatoid arthritis or systemic lupus erythematosus (SLE) may result in increased globulin levels due to chronic immune system activation and inflammation.
    Chronic Infections: Tuberculosis, chronic hepatitis, or viral infections can increase globulin production (specifically immunoglobulins), leading to a decrease in the A/G ratio.
    Cirrhosis: Cirrhosis and other chronic liver diseases can affect the liver’s ability to produce albumin, leading to lower albumin levels and, consequently, a reduced A/G ratio. At the same time, liver disease may lead to increased production of certain types of globulins.
    Hepatitis: Hepatitis or liver inflammation may also contribute to a reduced albumin synthesis, lowering the A/G ratio.
    Nephrotic Syndrome: In this condition, there is significant protein loss through the kidneys, particularly albumin. This can lead to a lower A/G ratio due to the relative increase in globulins compared to albumin.
    Multiple Myeloma: A cancer of the plasma cells in the bone marrow, which produces immunoglobulins (antibodies), can significantly increase globulin levels, leading to a lower A/G ratio.
    Waldenström's Macroglobulinemia: A condition that involves the production of excess immunoglobulin M (IgM), also elevates globulin levels and can result in a low A/G ratio.
    Autoimmune Diseases:Lupus and Rheumatoid Arthritis: Autoimmune diseases trigger the immune system to produce more globulins (especially antibodies), which can overwhelm albumin production, leading to a low A/G ratio.
    Protein Deficiency: Insufficient dietary protein intake can lead to low albumin production, while globulin levels may remain normal or even rise due to inflammation or immune response, lowering the A/G ratio.
    Protein-Losing Enteropathy: Conditions like Crohn’s disease or celiac disease, which cause protein loss from the intestines, may result in decreased albumin levels while globulin levels remain normal or increase.
    Acute Inflammatory Conditions: Acute infections or inflammatory conditions (e.g., sepsis) can cause a temporary drop in albumin levels while globulins rise as part of the body’s immune response.

Health Risks of Low A/G Ratio:
    Weakened Immune System: A high globulin level (due to chronic inflammation or infection) may indicate overactivation of the immune system, which can cause tissue damage.
    Liver Dysfunction: Low albumin levels suggest impaired liver function, which can result in edema, ascites, and poor nutrient absorption.
    Kidney Problems: Low albumin levels due to kidney conditions can lead to fluid retention, edema, and complications such as high blood pressure or heart failure.
    Chronic Inflammation: A prolonged low A/G ratio may reflect persistent inflammatory or autoimmune disorders, which can lead to damage to tissues and organs.

Tips to Raise A/G Ratio (Normalize Albumin Levels):
    Increase Protein Intake:Ensure a sufficient intake of high-quality proteins to boost albumin levels.
    Animal-Based Proteins: Include eggs, lean meats (chicken, turkey), fish, and dairy products.
    Plant-Based Proteins: Lentils, beans, tofu, quinoa, and nuts are good sources.
    Manage Underlying Conditions:Treat liver diseases (e.g., hepatitis or cirrhosis) or kidney diseases (e.g., nephrotic syndrome) with appropriate medications.
    For autoimmune diseases like lupus or rheumatoid arthritis, immunosuppressive drugs may help reduce inflammation and restore the A/G ratio.
    Anti-Inflammatory Diet:Focus on anti-inflammatory foods such as fatty fish (salmon, mackerel), olive oil, and turmeric.
    Avoid processed foods and excessive sugar intake to prevent chronic inflammation.
    Hydration and Electrolyte Balance:Maintain proper hydration to support kidney and liver function, and to prevent fluid retention, which could affect albumin production.

Foods to Eat for Low A/G Ratio:
    Protein-Rich Foods: Chicken, fish, eggs, legumes (lentils, beans), tofu, quinoa, and nuts.
    Anti-Inflammatory Foods: Leafy greens, citrus fruits, fatty fish, turmeric, and ginger.
    Liver-Supportive Foods: Garlic, cruciferous vegetables (broccoli, cauliflower), and green tea.""")
        elif values["Protein A/G Ratio"] > 2:
            advice.append("""High Protein A/G Ratio
A high A/G ratio occurs when the albumin levels are disproportionately higher than globulin levels, often because globulin levels are abnormally low.

Root Cause:
    Severe Dehydration: In cases of dehydration, the blood volume decreases, which can result in an increase in the concentration of albumin relative to globulins. This can cause a higher A/G ratio.
    Chronic Liver Disease (in early stages):Early stages of liver disease may result in a decrease in globulin production while albumin production is maintained or slightly reduced, leading to a higher A/G ratio.
    Malnutrition (with low globulin levels):Severe malnutrition or protein deficiency might lead to low globulin production, which can raise the A/G ratio if albumin levels are adequate.
    Genetic Disorders:Certain rare genetic disorders, such as selective immunoglobulin deficiencies (e.g., IgA deficiency), may cause low globulin levels, leading to an elevated A/G ratio.
    Kidney Disease (with protein loss):In some kidney diseases like Minimal Change Disease or Focal Segmental Glomerulosclerosis (FSGS), the loss of globulins from the body might lead to a higher A/G ratio, although this is rare.
    Multiple Myeloma (Early Stages):In the early stages of multiple myeloma, there may be a relative decrease in globulins, especially in the absence of hyperviscosity symptoms, leading to an elevated A/G ratio.
    Diabetes:In some cases of diabetes, particularly poorly managed diabetes, high albumin levels relative to globulins may be observed due to the body’s metabolic changes affecting protein levels.
    Hyperthyroidism:In hyperthyroidism, where the metabolism is increased, albumin production may remain high while globulin levels may not increase as much, causing a higher A/G ratio.

Health Risks of High A/G Ratio:
    Dehydration: The most common cause of a high A/G ratio, dehydration, can lead to complications like kidney stones, blood clots, and electrolyte imbalances.
    Nutritional Deficiencies: If malnutrition is causing low globulin levels, this can increase the risk of infections and delayed healing due to an impaired immune system.
    Immune Deficiencies: Low globulin levels can result in an increased risk of infections as there are fewer antibodies available to fight pathogens.

Tips to Lower A/G Ratio (Normalize Globulin Levels):
    Hydrate Properly:Drink adequate water to ensure proper fluid balance and to help prevent the concentration of albumin due to dehydration.
    Address Malnutrition:If malnutrition or protein deficiency is the cause, ensure adequate intake of essential nutrients and proteins, focusing on protein-rich foods (like eggs, meats, legumes) to help normalize globulin levels.
    Treat Underlying Conditions:Manage conditions like liver disease, kidney disease, and hyperthyroidism to ensure that globulin production is not impaired and the A/G ratio is normalized.
    Manage Inflammatory or Immune Conditions:If autoimmune conditions or infections are causing changes in globulin levels, treat the underlying condition to bring globulin levels back to a normal range.

Foods to Eat for High A/G Ratio:
    Hydration: Drink water, coconut water, and electrolyte-rich beverages.
    Protein-Rich Foods: Increase protein intake with lean meats, fish, legumes, tofu, and nuts.
    Anti-Inflammatory Foods: Incorporate foods like turmeric, ginger, and green leafy vegetables to help manage immune response and inflammation.
    """)

    # Creatinine (range: 0.6-1.2 mg/dL)
    if "Creatinine" in values:
        if values["Creatinine"] < 0.7:
            advice.append("""Low Creatinine (Hypocreatininemia)
A low creatinine level is typically rare and is often associated with specific medical conditions or factors that affect muscle mass, kidney function, or hydration.

Root Causes of Low Creatinine:
    Reduced Muscle Mass
    Aging: As people age, muscle mass tends to decrease, which can result in lower creatinine production.
    Muscle Wasting Conditions: Diseases such as muscular dystrophy, sarcopenia (age-related muscle loss), or polymyositis can result in reduced muscle mass and, consequently, low creatinine production.
    Malnutrition: Inadequate nutrition, particularly a deficiency in proteins and calories, can lead to muscle loss and lower creatinine levels.
    Severe Weight Loss: Unintentional or rapid weight loss due to illness or extreme dieting can also reduce muscle mass, causing lower creatinine levels.
    Pregnancy:Increased Blood Volume during pregnancy, blood volume increases, and the kidneys filter more blood. This can lead to a dilution of creatinine levels, causing them to appear lower than normal.
    Chronic Liver Disease:In advanced liver cirrhosis or other liver conditions, muscle protein synthesis is often reduced, leading to lower muscle mass and lower creatinine production.
    Overhydration:Excessive fluid intake or hyperhydration can dilute blood creatinine levels, making them appear lower than usual.
    Acute and Chronic Kidney Disease (in very early stages):In rare cases, especially in the early stages of kidney disease, the kidneys may not filter creatinine efficiently, causing blood creatinine levels to remain at lower levels. However, this is less common as creatinine typically rises as kidney function worsens.
    Use of Certain Medications:Corticosteroids or anabolic steroids can cause a shift in muscle mass and might lower creatinine levels, though this is not common.
    Dietary Factors:A vegetarian or vegan diet might result in slightly lower creatinine levels because plant-based diets often contain less creatine than meat-based diets. Creatine is the precursor to creatinine, and without sufficient intake, creatinine production may be lower.

Health Risks of Low Creatinine:
    Muscle Loss: Low creatinine levels can indicate decreased muscle mass, which can result in weakness, frailty, and decreased mobility, particularly in elderly individuals.
    Nutritional Deficiencies: Chronic low creatinine levels due to poor nutrition can signal deficiencies in essential nutrients like protein.
    Potential Kidney Dysfunction: Although less common, abnormally low creatinine can sometimes be seen in the early stages of kidney disease. This requires further investigation to determine the cause.

Tips to Increase Creatinine Levels:
    Increase Muscle Mass:Engage in strength training or resistance exercises to build muscle mass. This can naturally increase creatinine production.
    Protein Intake:Ensure adequate protein intake to support muscle growth. Include animal-based proteins (like lean meats, eggs, and dairy) or plant-based proteins (like legumes, tofu, and quinoa) in your diet.
    Balanced Nutrition:Focus on a nutrient-dense diet that includes vitamins and minerals to support muscle health and overall well-being.
    Manage Hydration:While adequate hydration is important, avoid excessive fluid intake that may dilute creatinine levels.
""")
        elif values["Creatinine"] > 1.2:
            advice.append("""High Creatinine (Hypercreatininemia)
High creatinine levels are more commonly seen and typically indicate impaired kidney function or other factors that affect kidney health. The kidneys are responsible for filtering creatinine, so high levels are often a sign that the kidneys are not working properly.

Root Causes of High Creatinine:
    Acute Kidney Injury (AKI): Sudden damage to the kidneys (due to trauma, infection, or dehydration) can result in a rapid rise in creatinine levels.
    Chronic Kidney Disease: Long-term kidney diseases, such as diabetic nephropathy or hypertensive nephropathy, impair kidney function, leading to elevated creatinine levels.
    Dehydration:Inadequate Fluid Intake: When the body is dehydrated, the kidneys retain water to compensate, which can result in concentrated creatinine in the blood, causing elevated levels.
    Rhabdomyolysis: This is a serious condition where muscle tissue breaks down rapidly due to injury, extreme physical exertion, or certain medications (e.g., statins), releasing creatine and creatinine into the bloodstream.
    Severe Burns or Trauma: Extensive muscle damage from burns or trauma can lead to high creatinine levels as muscles release more creatinine into the blood.
    Medications:Certain Drugs and Some medications, such as nonsteroidal anti-inflammatory drugs (NSAIDs), ACE inhibitors, and diuretics, can affect kidney function, leading to increased creatinine levels.
    Chemotherapy: Chemotherapy drugs, especially in high doses, can cause kidney damage and elevate creatinine levels.
    High Protein Diet:Excessive Meat Consumption: A high-protein diet, especially one rich in red meat, can increase the production of creatinine, as creatine (which is found in muscle tissues) is broken down into creatinine.
    Heart Failure:Reduced Kidney Perfusion: In heart failure, the kidneys may not receive enough blood flow due to low cardiac output, which can impair their ability to filter waste and elevate creatinine levels.
    Hypothyroidism: Low thyroid hormone levels can reduce kidney function, leading to elevated creatinine levels.
    Cushing’s Syndrome: Elevated cortisol levels can impair kidney function, causing high creatinine levels.
    Glomerulonephritis:Inflammation of the glomeruli (the filtering units of the kidneys) can impair kidney function and increase creatinine levels. This condition may be due to an autoimmune response or infection.
    Kidney Dysfunction: High creatinine is one of the most important markers for kidney dysfunction. Elevated levels indicate that the kidneys are not filtering waste effectively, which can lead to a buildup of toxins in the body.
    Fluid Imbalance: Poor kidney function can result in fluid retention, causing swelling, high blood pressure, and electrolyte imbalances.
    Progression of Kidney Disease: Elevated creatinine levels can indicate the progression of kidney disease. Early intervention is critical to slow disease progression and prevent further damage.
    Cardiovascular Risk: Chronic kidney disease and elevated creatinine levels are closely associated with an increased risk of cardiovascular events, such as heart attacks and strokes.

Tips to Lower Creatinine Levels:
    Treat Kidney Disease:Work with a healthcare provider to manage underlying kidney disease, whether it’s diabetic nephropathy, hypertension, or glomerulonephritis. Proper medication, diet adjustments, and lifestyle changes can help manage creatinine levels.
    Hydration:Stay adequately hydrated, but avoid excessive fluid intake, as this can stress the kidneys. Balance hydration with kidney health.
    Limit Protein Intake:Reducing the intake of animal proteins and focusing on plant-based proteins can help reduce the workload on the kidneys and prevent further increases in creatinine levels.
    Manage Blood Pressure and Blood Sugar:Controlling hypertension and diabetes is crucial in preventing kidney damage and managing creatinine levels. Aim for a healthy weight, exercise, and take prescribed medications.
    Avoid Harmful Medications:Avoid medications or substances that can cause kidney damage, including certain over-the-counter pain relievers (NSAIDs) and some prescription medications. Always consult a healthcare provider before taking new medications.
    Dietary Modifications:A kidney-friendly diet includes limiting salt intake, reducing phosphorus and potassium-rich foods (if advised by a healthcare provider), and eating foods that support overall kidney health, like blueberries, leafy greens, and whole grains.
    """)

    # Blood Urea Nitrogen (BUN) (range: 7-20 mg/dL)
    if "Blood Urea Nitrogen" in values:
        if values["Blood Urea Nitrogen"] < 8:
            advice.append("""Low BUN (Hypoazotemia)
A low BUN level indicates that the kidneys are not filtering urea nitrogen properly or that there is an issue affecting protein breakdown. Though less common than high BUN levels, low levels can still point to specific health issues.

Root Causes of Low BUN:
    Malnutrition or Low Protein Intake:If the body does not have enough dietary protein to break down, urea production decreases, leading to low BUN levels. This can occur in cases of severe malnutrition, eating disorders (e.g., anorexia), or very low-protein diets.
    Liver Disease:Since urea is produced in the liver, any condition that impairs liver function, such as cirrhosis or acute liver failure, can result in decreased urea production, leading to low BUN levels.
    Overhydration:Excessive fluid intake or overhydration can dilute the blood, resulting in low concentrations of waste products, including urea, in the bloodstream.
    Severe Anemia:Certain types of severe anemia, particularly those associated with a low red blood cell count, can lead to low BUN levels. Anemia decreases the body’s metabolic demand for protein, which results in less urea being produced.
    Pregnancy:Pregnancy increases the blood volume, which can dilute waste products like BUN in the bloodstream. This is particularly common in the second and third trimesters.
    Nephrotic Syndrome:In rare cases, nephrotic syndrome (a kidney disorder characterized by excessive protein loss in the urine) can result in a decreased BUN level due to altered kidney function and reduced urea production.
    Excessive Anabolic Steroid Use:Anabolic steroids, which are used for muscle growth and recovery, can lower BUN levels by enhancing muscle protein synthesis, leading to reduced breakdown of proteins and, consequently, less urea production.
    Diabetes (in the early stages):Although more commonly associated with high BUN, in the early stages of diabetes, low BUN can sometimes be observed, especially if the patient has experienced significant weight loss or poor nutrition.

Health Risks of Low BUN:
    Malnutrition: A low BUN level might indicate an insufficient intake of protein, leading to nutritional deficiencies and muscle wasting.
    Liver Disease: Low BUN may indicate that the liver is not functioning properly, which can affect overall metabolic and detoxification processes.
    Kidney Dysfunction: In some cases, kidney problems may contribute to low BUN, but it is less common than elevated levels.
    Fluid Imbalance: Overhydration can result in diluted blood, which may mask other important biomarkers and distort the overall picture of kidney function.

Tips to Increase BUN Levels:
    Increase Protein Intake:Incorporate more lean meats, fish, eggs, and dairy products into the diet. For vegetarians, lentils, beans, and tofu are excellent sources of protein.
    Address Nutritional Deficiencies:Consider working with a nutritionist to ensure you are getting an adequate, balanced diet to support overall health and liver function.
    Monitor Hydration:While staying hydrated is important, avoid excessive fluid intake, especially in cases of low BUN due to overhydration.
    Treat Liver Conditions:If liver disease is diagnosed, managing it with proper medical care, such as medications or lifestyle changes, may help increase BUN levels indirectly by improving liver function.
    Exercise Regularly:Engage in regular physical activity to increase muscle mass and metabolism, which can increase urea production.
""")
        elif values["Blood Urea Nitrogen"] > 20:
            advice.append("""High BUN (Azotemia)
A high BUN level is more common and typically indicates that the kidneys are not functioning properly or that there are issues related to hydration, diet, or muscle metabolism.

Root Causes of High BUN:
    Chronic Kidney Disease (CKD), Acute Kidney Injury (AKI), or glomerulonephritis (inflammation of the kidney filters) can impair the kidneys' ability to filter out urea, causing a buildup in the blood.
    Dehydration:Insufficient Fluid Intake: When a person is dehydrated, the kidneys conserve water, which results in the concentration of waste products like urea in the bloodstream.
    Excessive Fluid Loss: Conditions that cause excessive fluid loss, such as vomiting, diarrhea, or fever, can lead to dehydration and a subsequent increase in BUN levels.
    High Protein Diet:Consuming excessive amounts of protein, especially animal protein, increases the breakdown of proteins into amino acids, which in turn increases urea production. This can cause elevated BUN levels.
    Heart Failure:Reduced Kidney Perfusion: In heart failure, the heart is unable to pump blood effectively, which reduces blood flow to the kidneys, impairing their ability to filter waste products like urea.
    Gastrointestinal Bleeding:Internal Bleeding: When there is bleeding in the gastrointestinal tract (e.g., ulcers, varices, or gastric bleeding), proteins from the blood are digested in the intestines, leading to increased nitrogen levels and elevated BUN.
    Shock:Sepsis or Hypovolemic Shock: A state of low blood pressure or shock reduces blood flow to the kidneys, which impairs their ability to filter waste products properly, leading to elevated BUN levels.
    Diabetes:Uncontrolled Diabetes: When blood sugar levels are very high and the kidneys are under stress, kidney function may decline, causing high BUN levels.
    Medication Use:Certain medications can cause kidney damage or dehydration, leading to increased BUN levels. Examples include NSAIDs, diuretics, and some antibiotics.
    Increased Muscle Breakdown:Conditions like rhabdomyolysis, where there is significant muscle breakdown, can lead to a release of large amounts of urea nitrogen into the bloodstream, raising BUN levels.

Health Risks of High BUN:
    Kidney Dysfunction: Elevated BUN is often one of the first indicators of impaired kidney function. Long-term kidney issues, such as chronic kidney disease, need to be addressed to prevent progression to kidney failure.
    Dehydration: Persistent dehydration can lead to kidney damage and elevated BUN, which can increase the risk of further complications like kidney stones.
    Cardiovascular Risk: High BUN levels can be linked to heart disease, especially in people with existing heart or kidney conditions.
    Gastrointestinal Problems: If high BUN is caused by gastrointestinal bleeding, it is a serious medical emergency and requires immediate treatment.

Tips to Lower BUN Levels:
    Improve Hydration:Stay well-hydrated by drinking an adequate amount of water throughout the day. However, be mindful of the recommended fluid intake if you have kidney disease or any fluid retention issues.
    Manage Kidney Health:Control underlying conditions like hypertension, diabetes, or heart disease to prevent further damage to the kidneys.
    Medications or lifestyle changes may be necessary to support kidney function and prevent BUN from rising.
    Moderate Protein Intake:If BUN is high due to excessive protein intake, try to reduce your consumption of high-protein foods (particularly red meat) and focus on moderate portions of lean proteins, such as chicken, fish, or plant-based protein sources.
    Treat Underlying Conditions:If high BUN is related to conditions like gastrointestinal bleeding, shock, or muscle breakdown, work with healthcare providers to treat the underlying cause promptly.
    Monitor Kidney Function:If BUN levels are high and you have kidney disease or other risk factors, regular monitoring of kidney function is crucial to ensure proper treatment and avoid complications.""")

    # Uric Acid (range: 3.5-7.2 mg/dL)
    if "Uric Acid" in values:
        if values["Uric Acid"] < 3.5:
            advice.append("""Low Uric Acid (Hypouricemia)
A low uric acid level is less common than a high level but can still be indicative of specific health issues.

Root Causes of Low Uric Acid:
    Kidney Dysfunction: Certain kidney diseases, particularly those that impair the renal tubules' ability to filter waste, can result in low uric acid levels in the blood. This happens because the kidneys might excrete too much uric acid rather than filtering and reabsorbing it.
    Dietary Factors: A diet that is extremely low in purines (found in red meat, organ meats, and seafood) can result in low uric acid levels. This is uncommon but may occur in strict vegetarian or low-purine diets.
    Overuse of Certain Medications:
    Diuretics (e.g., Thiazides): Diuretic medications are used to treat conditions like high blood pressure or edema, and they can lead to low uric acid levels by increasing its excretion in the urine.
    Losartan (blood pressure medication): Interestingly, Losartan, a medication used for managing hypertension, can lower uric acid levels.
    Vitamin C Overuse: High doses of Vitamin C supplements can lower uric acid levels by increasing the renal clearance (excretion) of uric acid.
    Low Estrogen: In women, low estrogen levels, especially during menopause, can result in decreased uric acid levels.
    Fanconi Syndrome:This is a rare disorder that affects kidney function, leading to the loss of important substances, including uric acid, in urine.
    Wilson's Disease:A genetic disorder that causes copper buildup in the body, which can lead to low uric acid levels due to impaired purine metabolism.
    Health Risks of Low Uric Acid:
    Kidney Dysfunction: Low uric acid can be a sign of kidney problems or renal tubular dysfunction.
    Gout Prevention: While low uric acid is not typically linked to gout, it can sometimes reflect abnormal kidney function, which, if untreated, could lead to other complications.
    Metabolic Problems: Decreased levels might indicate metabolic imbalances, such as issues with purine metabolism or absorption.

Tips to Increase Uric Acid Levels:
    Increase Purine-Rich Foods:Foods such as red meat, shellfish, organ meats, and alcohol (especially beer) are high in purines and can increase uric acid production in the body.
    Proper Kidney Function:Ensure adequate hydration and proper kidney function to help maintain normal uric acid levels. Stay well-hydrated, but avoid excessive intake of fluids.
    Monitor Medication Use:If you're taking diuretics or Vitamin C supplements, discuss with your doctor whether adjustments are needed.
    Consult a Healthcare Provider:If low uric acid is related to conditions such as Wilson's disease or Fanconi syndrome, seek specialized care and treatment options.
    """)
        elif values["Uric Acid"] > 7.2:
            advice.append("""High Uric Acid (Hyperuricemia)
High uric acid levels are more commonly discussed and can result from various factors that either increase uric acid production or decrease its excretion. If left untreated, high uric acid can lead to gout, a form of arthritis caused by the crystallization of uric acid in the joints, as well as kidney stones.

Root Causes of High Uric Acid:
    Purine-Rich Foods: Excessive consumption of foods high in purines, such as red meat, seafood, organ meats, alcohol (especially beer), and sugary drinks, can increase uric acid levels. Alcohol inhibits uric acid excretion, and high sugar intake, especially fructose, can lead to higher uric acid production.
    Kidney Impairment: The kidneys are responsible for excreting uric acid. If kidney function is impaired (as in CKD), uric acid may build up in the bloodstream.
    Obesity:Increased Uric Acid Production: People who are overweight or obese often have higher levels of uric acid because excess body fat increases uric acid production and decreases its excretion through the kidneys.
    Dehydration:Insufficient Fluid Intake: Dehydration or not drinking enough water leads to a more concentrated urine, reducing the kidneys' ability to excrete uric acid and contributing to elevated levels in the blood.
    Genetic Factors:A family history of hyperuricemia or gout can increase the likelihood of having elevated uric acid levels. Certain genetic variations can affect the body's ability to process and excrete uric acid properly.
    Medications:Diuretics (e.g., Thiazides): Although diuretics can lower uric acid in some cases, they are more commonly known to raise uric acid levels by causing dehydration and reducing renal clearance.
    Aspirin and Immunosuppressants: These medications can also reduce uric acid excretion, contributing to higher levels.
    Medical Conditions such as
    Gout: This is a disorder where uric acid builds up in the joints and forms crystals, causing inflammation and severe pain.
    Psoriasis: People with psoriasis may have higher rates of cell turnover, which increases the breakdown of purines and subsequently leads to higher uric acid production.
    Hypothyroidism: Low thyroid hormone levels can decrease kidney clearance of uric acid, leading to increased blood levels.
    Leukemia or Lymphoma: Certain cancers or blood disorders can increase cell turnover, leading to more purine breakdown and, consequently, higher uric acid production.
    Lead Poisoning:Lead exposure can impair kidney function and raise uric acid levels, leading to hyperuricemia.

Health Risks of High Uric Acid:
    Gout: High uric acid levels can lead to the formation of crystals in the joints, causing painful gout attacks, usually affecting the big toe or other joints.
    Kidney Stones: Uric acid can form crystals in the kidneys, contributing to the formation of uric acid kidney stones.
    Cardiovascular Disease: Chronic hyperuricemia is associated with an increased risk of hypertension, heart disease, and stroke.
    Kidney Damage: Long-term elevated uric acid can contribute to kidney disease and renal failure due to the deposition of uric acid crystals in kidney tissues.

Tips to Lower Uric Acid Levels:
    Limit Purine-Rich Foods:Avoid or limit the intake of foods high in purines, such as red meats, organ meats, seafood, and alcohol, especially beer.
    Stay Hydrated:Drink plenty of water throughout the day to help the kidneys excrete uric acid efficiently. Aim for at least 8 glasses of water per day.
    Limit Alcohol:Alcohol, especially beer, can increase uric acid production and impair kidney excretion. Limit alcohol consumption or avoid it altogether if you have gout or high uric acid levels.
    Maintain a Healthy Weight:Losing weight, especially belly fat, can help reduce uric acid levels and the risk of developing gout and kidney stones. Engage in regular physical activity and eat a balanced, healthy diet.

Medications:
    If uric acid levels are high due to gout, kidney issues, or other medical conditions, medications such as allopurinol or febuxostat can help lower uric acid levels. Always consult a doctor before starting or adjusting medications.
    Avoid Sugary Beverages:Fructose (found in sugary drinks and processed foods) increases uric acid production. Avoid sodas and other sugar-laden beverages to manage uric acid levels.
    Manage Underlying Health Conditions:Effectively treat conditions like hypertension, diabetes, and kidney disease to help lower uric acid levels.
    Eat More Low-Purine Foods:Incorporate foods that are lower in purines, such as low-fat dairy, whole grains, vegetables, and fruits (especially cherries, which may help reduce uric acid levels)""")

    
    # Bilirubin (range: 0.1-1.2 mg/dL)
    if "Bilirubin" in values:
        if values["Bilirubin"] > 1.2:
            advice.append("""High Bilirubin (Hyperbilirubinemia)
High bilirubin levels can indicate a variety of health conditions, ranging from liver diseases to blood disorders. Jaundice (yellowing of the skin and eyes) is a visible symptom of high bilirubin levels.

Root Causes of High Bilirubin:
    Liver Disease:Hepatitis, cirrhosis, liver failure, and other liver conditions can impair the liver's ability to conjugate and excrete bilirubin, resulting in elevated levels of total bilirubin, especially the indirect form.
    Hemolysis (Increased Red Blood Cell Breakdown):Hemolytic anemia or sickle cell disease causes an accelerated breakdown of red blood cells, which increases bilirubin production. The indirect (unconjugated) bilirubin levels rise as a result.
    Bile Duct Obstruction:Blockages in the bile ducts, such as those caused by gallstones, bile duct cancer, or pancreatitis, can prevent bilirubin from being excreted properly, causing direct (conjugated) bilirubin to build up in the bloodstream.
    Gilbert's Syndrome:This is a common, inherited condition in which the liver has a reduced ability to process bilirubin. It usually results in mildly elevated indirect bilirubin, but the condition is generally harmless.
    Neonatal Jaundice:Newborns, especially premature babies, often experience elevated bilirubin levels because their liver is immature and less able to process bilirubin efficiently. This condition is called physiological jaundice and usually resolves on its own.
    Infections or Sepsis:Severe infections can affect liver function and red blood cell turnover, leading to increased bilirubin production and reduced excretion.
    Alcohol Consumption:Excessive alcohol consumption can damage the liver and impair its ability to conjugate bilirubin, leading to higher bilirubin levels.
    Hemoglobinopathies:Disorders like thalassemia and sickle cell anemia can lead to increased red blood cell breakdown, raising bilirubin levels, particularly the indirect fraction.

Health Risks of High Bilirubin:
    Jaundice: The most common symptom of high bilirubin levels is jaundice, which manifests as yellowing of the skin and eyes. This is due to the accumulation of bilirubin in the tissues.
    Liver Damage: Persistent high bilirubin levels, particularly the direct (conjugated) form, often indicate liver dysfunction and may be associated with conditions like cirrhosis, hepatitis, or bile duct obstructions.
    Gallstones: A significant amount of conjugated bilirubin can form gallstones if it accumulates in the gallbladder.
    Chronic Conditions: Long-term elevated bilirubin can indicate an underlying chronic condition, such as hemolytic anemia, that requires management.

Tips to Lower Bilirubin Levels:
    Hydration:Staying well-hydrated is essential to help the kidneys process excess bilirubin and reduce the risk of jaundice.
    Treat Underlying Conditions:If the high bilirubin is due to liver disease, gallstones, or hemolysis, treating the underlying condition is crucial. This may involve medications, lifestyle changes, or in some cases, surgery.
    Avoid Alcohol:Reducing or eliminating alcohol consumption can help the liver function more efficiently and reduce bilirubin production.
    Manage Hemolytic Conditions:If high bilirubin is due to hemolytic anemia or other blood disorders, managing the condition with appropriate medications (such as folic acid supplementation or immunosuppressive therapy) and blood transfusions may be required.
    Phototherapy for Neonatal Jaundice:For newborns with high bilirubin, phototherapy (light therapy) is commonly used to break down excess bilirubin in the skin. This is a standard treatment for neonatal jaundice.
    Balanced Diet:A healthy diet rich in fruits, vegetables, whole grains, and lean proteins can support liver health and the overall detoxification process.

Medications:
    In some cases, medications like ursodeoxycholic acid may be prescribed to help improve bile flow and reduce bilirubin levels.
    Monitor for Signs of Liver Damage:
    If high bilirubin is linked to liver disease, regular monitoring of liver function tests and imaging studies may be necessary to assess the extent of liver damage.
    """)
        # Gamma Glutamyl Transferase (range: 9-48 U/L)
    if "Gamma Glutamyl Transferase" in values:
        if values["Gamma Glutamyl Transferase"] < 9:
            advice.append("""Low Gamma Glutamyl Transferase (GGT)
While low GGT levels are less common and less frequently discussed, they can still occur under certain circumstances. Generally, low GGT levels are not typically a cause for concern, but they can indicate specific health scenarios.

Root Causes of Low GGT:
    Hypothyroidism:Low thyroid function (hypothyroidism) can result in a decrease in GGT production. This is often due to slower metabolic processes that occur when the thyroid gland is underactive.
    Malnutrition or Protein Deficiency:
    Protein deficiency or inadequate nutrition can reduce GGT levels. Since GGT is produced by the liver and requires certain nutrients to be synthesized properly, malnutrition can affect its levels.
    Diabetes and Insulin Resistance:In some cases, insulin resistance and diabetes may be associated with low GGT levels, though the relationship is still not entirely clear. It might be related to changes in liver enzyme production or insulin's effects on liver function.
    Certain Medications:Certain medications, such as oral contraceptives or statins, can result in lower GGT levels. These medications may have indirect effects on liver function and enzyme production.
    Hypervitaminosis (Excessive Vitamin Intake):Excessive intake of certain vitamins, such as Vitamin C, can lower GGT levels due to the antioxidant effects on liver function and enzyme activity.
    Genetics:Some individuals may naturally have lower GGT levels due to genetic factors. This is not necessarily a concern unless there are other signs of liver dysfunction.

Health Implications of Low GGT:
    Generally, low GGT levels are not of major concern unless they are associated with significant underlying conditions like hypothyroidism, nutritional deficiencies, or other liver issues.
    Low GGT can be a marker of overall good liver health, indicating that the liver is not under stress and is functioning normally.

Tips to Maintain or Increase GGT Levels:
    Maintain Thyroid Health:Thyroid function should be monitored regularly, and any signs of hypothyroidism should be addressed through appropriate treatment.
    Proper Nutrition:Eat a balanced diet rich in proteins, vitamins, and minerals to support liver function. Foods such as lean meats, fish, beans, eggs, and dairy products are important for enzyme production.
    Manage Diabetes and Insulin Sensitivity:Regular physical activity and a healthy diet to manage blood sugar levels can help improve overall metabolic function and potentially maintain optimal GGT levels.
    Avoid Excessive Vitamin Intake:Ensure you're not consuming excessive amounts of vitamins, especially Vitamin C, unless prescribed by a healthcare provider, as this can reduce GGT production.
    Regular Medical Check-Ups:Regular health check-ups can help detect underlying conditions like hypothyroidism, diabetes, or liver diseases early and ensure you are following the appropriate treatment.
    """)
        elif values["Gamma Glutamyl Transferase"] > 48:
            advice.append("""High Gamma Glutamyl Transferase (GGT)
Elevated GGT levels are more commonly observed and can be associated with a variety of conditions, particularly those involving the liver, bile ducts, and alcohol consumption. High GGT levels can serve as a marker for liver dysfunction, and its levels often correlate with the degree of liver damage.

Root Causes of High GGT:
    Hepatitis (inflammation of the liver), cirrhosis, fatty liver disease, and liver fibrosis can significantly elevate GGT levels due to liver cell damage and reduced liver function.
    Liver tumors or liver metastasis from other cancers can also cause elevated GGT.
    Bile Duct Obstruction:Blockages in the bile ducts (such as from gallstones, pancreatitis, or bile duct strictures) can cause a buildup of bile, leading to elevated GGT levels. This is particularly associated with cholestasis (impaired bile flow).
    Alcohol Consumption:Chronic alcohol use is a major cause of elevated GGT levels. Even moderate drinking can raise GGT levels, but heavy drinking significantly elevates the enzyme.
    Alcohol-induced liver damage can lead to conditions such as fatty liver or alcoholic hepatitis, which are associated with elevated GGT levels.
    Non-Alcoholic Fatty Liver Disease (NAFLD):This condition, often related to obesity, diabetes, or metabolic syndrome, leads to the accumulation of fat in the liver, which can result in elevated GGT levels.
    Medications:Certain medications, such as phenytoin (used for epilepsy), barbiturates, statins, antibiotics, and acetaminophen (paracetamol), can increase GGT levels due to their effects on liver metabolism.
    Chronic Pancreatitis:Inflammation of the pancreas (often due to alcohol or gallstones) can lead to increased GGT levels as part of a broader liver-pancreas dysfunction.
    Cardiovascular Disease:Elevated GGT levels have been associated with an increased risk of cardiovascular diseases such as heart attacks, strokes, and heart failure. This might be due to the enzyme’s role in oxidative stress and inflammation.
    Diabetes and Obesity:Metabolic syndrome and insulin resistance, which are often associated with diabetes and obesity, can lead to increased GGT levels due to their impact on liver fat metabolism and bile flow.
    Gilbert's Syndrome:This inherited disorder, which affects bilirubin processing in the liver, can lead to mild elevations in GGT levels.

Health Implications of High GGT:
    Liver Dysfunction: Elevated GGT levels are most commonly associated with liver diseases such as hepatitis, cirrhosis, fatty liver disease, and alcoholic liver disease.
    Bile Duct Obstruction: High GGT is often seen in cholestasis or bile duct blockages, which prevent bile from flowing properly and can lead to damage.
    Alcohol Abuse: Chronic alcohol consumption significantly raises GGT levels and is often used as an indicator of alcohol-induced liver damage.
    Cardiovascular Disease Risk: Elevated GGT levels are associated with increased oxidative stress and inflammation, both of which are involved in cardiovascular disease.
    Pancreatic Issues: Chronic pancreatitis can raise GGT levels as part of the broader dysfunction of the liver and pancreas.

Tips to Lower High GGT Levels:
    Stop or Reduce Alcohol Consumption:Limiting or completely avoiding alcohol is crucial in lowering GGT levels, especially if alcohol-related liver disease or fatty liver is contributing to the increase.
    Healthy Diet:Focus on a liver-friendly diet rich in antioxidants, such as fruits, vegetables, and whole grains. Incorporating healthy fats (e.g., omega-3 fatty acids) and lean proteins can support liver function.
    Avoid foods high in refined sugars and trans fats, which can worsen fatty liver and overall liver health.
    Exercise and Weight Loss:Maintaining a healthy weight and engaging in regular physical activity can help reduce liver fat and improve overall liver function, lowering GGT levels in the process.
    Aim for 150 minutes of moderate exercise per week.

Treat Underlying Conditions:
    If high GGT is due to diabetes, obesity, high cholesterol, or hypertension, treating these conditions effectively can help lower GGT levels.
    Medications for conditions like fatty liver disease or cholestasis may be necessary, depending on the underlying cause.
    Medication Management:If medications are contributing to elevated GGT, discuss alternatives with your doctor to reduce liver stress. Medications like statins or antiepileptic drugs may need to be adjusted or changed.
    Regular Medical Check-Ups:Regular monitoring of GGT and other liver enzymes, especially in people with risk factors for liver disease (e.g., heavy drinkers, those with obesity or metabolic syndrome), can help detect liver issues early.
    Hydration and Detox:Drinking plenty of water and consuming liver-supportive herbs like milk thistle or dandelion may help detoxify the liver and support normal enzyme function. However, always consult a healthcare provider before starting supplements.
    """)

    # e-GFR (Glomerular Filtration Rate) (range: > 60 mL/min/1.73m²)
    if "e-GFR (Glomerular Filtration Rate)" in values:
        if values["e-GFR (Glomerular Filtration Rate)"] < 60:
            advice.append("""Low e-GFR (Kidney Dysfunction)
A low e-GFR generally suggests that the kidneys are not functioning optimally and may be at risk of progressing to chronic kidney disease (CKD). The lower the e-GFR, the worse the kidney function.

Root Causes of Low e-GFR:
    Chronic Kidney Disease (CKD):The most common cause of a low e-GFR is chronic kidney disease, which often results from long-term conditions such as diabetes, high blood pressure (hypertension), or glomerulonephritis (inflammation of the kidney’s filtering units).
    Acute Kidney Injury (AKI):Acute kidney injury, caused by sudden damage to the kidneys (e.g., from severe dehydration, medications, infections, or trauma), can cause a temporary drop in e-GFR.
    Diabetes:Diabetic nephropathy is a common complication of diabetes and can lead to gradual damage to the kidneys, reducing their ability to filter waste products effectively, leading to a low e-GFR.
    High Blood Pressure (Hypertension):Hypertension is another major risk factor for kidney disease and can cause damage to the kidneys over time, resulting in reduced e-GFR levels.
    Glomerulonephritis:Inflammation of the glomeruli (the kidneys' filtering units) can reduce kidney function, leading to a drop in e-GFR. This may be caused by infections, autoimmune diseases, or certain medications.
    Obstructions in the Urinary Tract:Conditions like kidney stones, prostate enlargement, or bladder problems that obstruct urine flow can reduce kidney function and lower the e-GFR.
    Kidney Infections or Inflammation:Pyelonephritis (kidney infection) or other inflammatory conditions of the kidney can impair filtration and reduce e-GFR levels.
    Age-Related Decline:Kidney function naturally declines with age. Older adults may have lower e-GFR due to age-related kidney changes, even in the absence of major diseases.
    Genetic Disorders:Conditions such as polycystic kidney disease (PKD) can lead to kidney damage over time, lowering the e-GFR.

Health Implications of Low e-GFR:
    Progression of Kidney Disease: A low e-GFR, especially if it’s persistently low, is a sign that kidney function is impaired and may be progressing toward end-stage renal disease (ESRD).
    Toxin Build-Up: With a low e-GFR, the kidneys may not be able to filter out waste and toxins from the body effectively, leading to uremia (build-up of waste in the blood).
    Electrolyte Imbalances: Reduced kidney function may cause imbalances in electrolytes like sodium, potassium, and calcium, which can lead to serious complications such as heart arrhythmias.
    Fluid Retention: The kidneys may also have trouble excreting excess fluid, leading to swelling in the legs, ankles, and other parts of the body.

Tips to Improve or Manage Low e-GFR:
    Control Blood Sugar (Diabetes Management):Keep blood sugar levels under control if you have diabetes to reduce the risk of diabetic nephropathy and protect kidney function. Aim for tight glucose control through medication, diet, and exercise.
    Control Blood Pressure:Manage blood pressure through a healthy diet, regular exercise, and medications such as ACE inhibitors, ARBs, or diuretics to protect kidney health.
    Maintain a Kidney-Friendly Diet:Focus on a low-protein diet, as excessive protein can stress the kidneys.
    Reduce sodium intake to help control blood pressure and reduce fluid retention.
    Increase intake of fruits and vegetables rich in potassium and fiber to support kidney function.
    Stay Hydrated:Drink plenty of water, but be mindful not to overhydrate if you have kidney disease with fluid retention issues. Follow your doctor’s advice on how much fluid to consume.
    Avoid Smoking and Alcohol:Quit smoking and limit alcohol consumption, as these can worsen kidney function and contribute to hypertension and other kidney-damaging conditions.
    Manage Underlying Health Conditions:Take medications as prescribed to treat underlying conditions such as high cholesterol, obesity, or heart disease that can contribute to kidney damage.
    Monitor Kidney Function:Regularly monitor kidney function through blood tests (serum creatinine) and urine tests to detect any decline in e-GFR early. Early detection of kidney issues allows for timely intervention.
    Avoid Nephrotoxic Drugs:Avoid overuse of medications that can harm the kidneys, such as non-steroidal anti-inflammatory drugs (NSAIDs), and consult your doctor before taking any new medications.
    """)
        elif values["e-GFR (Glomerular Filtration Rate)"] > 90:
            advice.append("""High e-GFR (Hyperfiltration)
A high e-GFR is usually a sign of increased kidney filtration and can sometimes be indicative of excessive kidney function. Though less common, a high e-GFR may occur under certain conditions.

Root Causes of High e-GFR:
    Hyperfiltration in Early Kidney Disease:In the early stages of chronic kidney disease (CKD), the kidneys may compensate for the loss of nephrons (filtering units) by increasing their filtration rate. This results in an initially high e-GFR, which may be followed by a decline in kidney function over time.
    Pregnancy:Pregnancy can lead to increased blood volume and changes in kidney function, leading to higher e-GFR values, especially in the second trimester. This is a normal physiological adaptation.
    High Protein Intake:A high-protein diet can temporarily increase the workload on the kidneys, leading to a higher e-GFR as the kidneys filter more waste products. However, long-term high-protein intake may stress the kidneys, especially in people with preexisting kidney conditions.
    Exercise:Strenuous physical activity can lead to temporary increases in e-GFR due to an increase in blood flow to the kidneys. This is usually short-term and resolves after exercise.
    Increased Renal Blood Flow:Conditions that increase blood flow to the kidneys, such as arteriovenous fistulas (created for dialysis access) or renal artery dilation, can result in an elevated e-GFR.
    Diabetes (Early Stage):In early-stage diabetes, the kidneys may experience hyperfiltration as they try to process the excess glucose in the blood. This can lead to a temporarily elevated e-GFR, though over time, this can contribute to kidney damage.
    Severe Hypertension (Stage 1):Early stages of high blood pressure can cause the kidneys to filter more fluid in an attempt to cope with the increased systemic blood pressure, leading to a higher e-GFR.

Health Implications of High e-GFR:
    Potential Risk of Kidney Damage: Prolonged hyperfiltration can lead to kidney damage over time, as the kidneys are overworking to compensate for the loss of filtering capacity. This can eventually lead to nephron damage, worsening kidney function.
    Underlying Health Conditions: High e-GFR values may be a sign of an underlying condition that requires monitoring and intervention, such as diabetes, high blood pressure, or high protein intake.
    Short-Term Effects: In cases like pregnancy, high e-GFR is often temporary and not a cause for concern.

Tips to Manage or Lower High e-GFR:
    Monitor Kidney Function Regularly:Regular testing can help identify early signs of kidney damage and ensure timely intervention to prevent further complications.
    Control Blood Sugar (For Diabetics):Maintain optimal blood sugar levels to prevent kidney hyperfiltration from progressing into diabetic nephropathy.
    Control Blood Pressure:Lowering blood pressure to safe levels can reduce the strain on kidneys, especially in those with hypertension or early signs of kidney disease.
    Adopt a Balanced Diet:Consider reducing protein intake if high protein consumption is contributing to kidney strain. A balanced diet that supports kidney health is crucial.
    Avoid Overuse of Kidney-Stressing Substances:Avoid substances that can put extra strain on the kidneys, such as excessive alcohol or NSAIDs (non-steroidal anti-inflammatory drugs).
    Weight Management:Maintaining a healthy weight can help reduce the risk of diabetes, hypertension, and kidney disease, all of which can affect kidney function and e-GFR.
    Stay Hydrated:Drink plenty of water, especially if you're increasing protein intake or exercising regularly, to support kidney function and prevent dehydration.""")

    # Urea (range: 7-20 mg/dL)
    if "Urea" in values:
        if values["Urea"] < 7:
            advice.append("""Low Urea (Hypouremia)
Low urea levels in the blood can occur due to several factors that influence its production or clearance.

Root Causes of Low Urea:
    Liver Disease:Liver dysfunction or diseases such as cirrhosis, hepatitis, or liver failure can result in low urea production. The liver is responsible for converting ammonia into urea, so if the liver is not functioning properly, this process is impaired, leading to lower urea levels.
    Malnutrition:Malnutrition, particularly a protein-deficient diet, can result in low urea levels. This is because urea is produced from the breakdown of proteins, and insufficient protein intake leads to reduced urea production.
    Overhydration:Excessive fluid intake (overhydration) can dilute the urea concentration in the blood, leading to a lower urea level. This is often seen in cases of polydipsia (excessive thirst) or excessive intravenous fluid administration.
    Severe Bone Marrow Depression:Conditions that severely suppress the bone marrow, such as aplastic anemia or certain chemotherapies, may lead to low urea levels, as the breakdown of proteins in muscles and tissues is reduced.
    Pregnancy:Pregnancy, particularly in the later stages, can lead to lower urea levels due to increased blood volume and the kidneys filtering more efficiently during pregnancy.
    Acute or Chronic Renal Failure (rare):In rare cases, advanced kidney disease can lead to decreased production of urea due to reduced protein metabolism or other kidney dysfunctions.
    High Carbohydrate Diet:A high carbohydrate diet with little protein intake may reduce urea production since carbohydrates are not metabolized into urea.

Health Implications of Low Urea:
    Indication of Liver Dysfunction: Low urea levels may point to liver disease, as the liver produces urea. This can be indicative of significant liver damage or dysfunction.
    Malnutrition: Extremely low urea levels can also be a sign of poor nutrition or malnutrition, where the body isn’t breaking down enough proteins.
    Electrolyte Imbalance: In cases of overhydration, dilution of urea may be associated with disturbances in other electrolytes, which can have negative effects on the heart, muscles, and other organs.

Tips to Improve or Manage Low Urea:
    Support Liver Health:Avoid alcohol and other substances that can damage the liver.
    Follow a liver-healthy diet rich in antioxidants, fruits, vegetables, and healthy fats to support liver function.
    Consult your doctor for regular liver function tests to catch liver problems early.
    Improve Nutrition:Increase protein intake if malnutrition is the cause. Include lean meats, fish, eggs, legumes, and dairy in your diet to ensure sufficient protein.
    A balanced, nutrient-rich diet supports overall health and urea production.
    Monitor Fluid Intake:Avoid excessive water consumption. Drink fluids in moderation based on your body’s needs, especially if you're in a condition where fluid retention is not a concern.
    Consult a Doctor for Kidney Function:If kidney dysfunction is suspected, monitoring kidney function with blood tests and urinalysis is crucial.""")
        elif values["Urea"] > 20:
            advice.append("""High Urea (Hyperuremia)
High urea levels in the blood typically indicate that the kidneys are not efficiently clearing urea from the bloodstream. It can also be a sign of excess protein breakdown in the body.

Root Causes of High Urea:
    Kidney Dysfunction (Chronic Kidney Disease CKD):Chronic kidney disease is the most common cause of high urea levels. As kidney function declines, the kidneys' ability to filter out waste products like urea is compromised, leading to elevated blood urea nitrogen (BUN) levels.
    Dehydration:Dehydration leads to concentrated blood due to reduced fluid intake or excessive fluid loss (e.g., vomiting, diarrhea). In dehydrated states, the kidneys conserve water, but this can also result in higher urea levels in the bloodstream.
    Excessive Protein Intake:High-protein diets, especially red meats, cheese, and protein supplements, can increase urea production, leading to elevated levels in the blood due to excess protein breakdown.
    Acute Kidney Injury (AKI):Acute kidney injury can cause a sudden rise in urea levels due to kidney damage from dehydration, infections, medications, or other factors that impair kidney function.
    Heart Failure:Heart failure can cause poor kidney perfusion (blood flow to the kidneys), which may lead to reduced kidney function and increased urea levels.
    Gastrointestinal Bleeding:Gastrointestinal bleeding (such as in the stomach or intestines) can lead to increased protein breakdown in the digestive tract, raising urea levels.
    Burns or Severe Trauma:Severe burns, trauma, or conditions that result in tissue breakdown can increase protein catabolism and, consequently, urea production.
    High Blood Pressure (Hypertension):Uncontrolled hypertension can damage the kidneys over time, leading to reduced kidney filtration and high urea levels.
    Medications:Some medications, such as diuretics and antibiotics, can lead to increased urea levels, either by promoting dehydration or by affecting kidney function.
    Infections:Severe infections, particularly those affecting the kidneys (like pyelonephritis), can lead to kidney dysfunction and higher urea levels.

Health Implications of High Urea:
    Kidney Disease: High urea levels, especially if persistent, can indicate chronic kidney disease or acute kidney injury, where kidney filtration capacity is reduced.
    Dehydration: Elevated urea levels may point to dehydration, which can lead to electrolyte imbalances, kidney damage, and other complications if not addressed.
    Heart and Blood Pressure Issues: Conditions like heart failure or high blood pressure can lead to impaired kidney function and elevated urea levels.
    
Tips to Manage or Lower High Urea:
    Hydration:Ensure adequate hydration, especially if dehydration is the cause of high urea. Drink enough water daily to maintain proper kidney function and help flush out toxins.
    Manage Kidney Health:If kidney disease is diagnosed, follow your doctor’s advice for dialysis, medications, and lifestyle changes to slow down kidney deterioration.
    Take medications as prescribed to help manage underlying conditions like hypertension, diabetes, or heart failure.
    Dietary Modifications:Reduce protein intake to lower the metabolic burden on the kidneys. This is especially important for people with kidney disease or those on dialysis.
    Limit salt and processed foods, as they can contribute to high blood pressure, which in turn can worsen kidney function and increase urea levels.
    Control Blood Pressure:Keeping your blood pressure within normal limits can help prevent kidney damage and decrease urea levels. Regularly monitor your blood pressure and manage it with lifestyle changes and medications if necessary.
    Avoid Nephrotoxic Substances:Avoid NSAIDs, certain antibiotics, and other nephrotoxic drugs that can worsen kidney function and increase urea levels. Always consult your doctor before taking any new medications.
    Address Underlying Conditions:Manage conditions like heart failure, diabetes, or gastrointestinal bleeding, as they can contribute to elevated urea levels and kidney dysfunction.
    """)

    # T3 Total (range: 80-180 ng/dL)
    if "T3 Total" in values:
        if values["T3 Total"] < 0.6:
            advice.append("""Low T3 Total (Hypothyroidism)
Low levels of T3 can occur when the thyroid gland is underactive and fails to produce enough thyroid hormones. This condition is called hypothyroidism.

Root Causes of Low T3 Total:
    Hypothyroidism:The most common cause of low T3 levels is hypothyroidism, where the thyroid gland doesn't produce enough hormones, including T3. This can be due to autoimmune diseases like Hashimoto's thyroiditis, iodine deficiency, or surgery that removes part or all of the thyroid.
    Severe Illness or Stress:Severe illnesses or high levels of physical stress can lead to low T3 levels. This is sometimes referred to as "non-thyroidal illness syndrome" or "sick euthyroid syndrome." In this case, T3 levels drop even though there is no thyroid dysfunction, often as a response to the body’s stress response.
    Pituitary Dysfunction:The pituitary gland produces thyroid-stimulating hormone (TSH), which regulates the thyroid’s hormone production. If the pituitary is not functioning properly, it can result in insufficient T3 production. This could be due to pituitary tumors or other pituitary disorders.
    Iodine Deficiency:Iodine deficiency is a common cause of hypothyroidism in certain parts of the world. The thyroid requires iodine to produce T3 and T4 hormones. A lack of iodine in the diet can lead to reduced T3 levels.
    Medications:Certain medications, such as amiodarone, lithium, and beta-blockers, can interfere with thyroid function and result in low T3 levels.
    Nutritional Deficiencies:Deficiencies in zinc, selenium, or iron can affect thyroid function and lead to low T3 levels, as these nutrients are necessary for optimal thyroid hormone production.
    Starvation or Extreme Weight Loss:In cases of starvation, extreme calorie restriction, or anorexia nervosa, the body may conserve energy by lowering the production of T3 to reduce metabolic rate.

Health Implications of Low T3 Total:
    Slowed Metabolism: Low T3 levels can lead to a slower metabolic rate, causing symptoms like fatigue, weight gain, cold intolerance, constipation, and dry skin.
    Thyroid Disease: Prolonged low T3 levels are typically associated with hypothyroidism, which requires medical treatment to regulate hormone levels.
    Cardiovascular Risk: Severe hypothyroidism can lead to high cholesterol levels, heart disease, and other cardiovascular complications.

Tips to Improve or Manage Low T3 Total:
    Thyroid Hormone Replacement:If you have hypothyroidism, your doctor may prescribe levothyroxine (synthetic T4) or liothyronine (synthetic T3) to normalize hormone levels. Follow your doctor’s advice and have your thyroid levels monitored regularly.
    Manage Stress:Chronic stress can contribute to low T3 levels. Implementing stress management techniques such as meditation, deep breathing exercises, yoga, or mindfulness can help improve your thyroid function.
    Improve Nutrition:Ensure adequate iodine intake by consuming iodized salt, seafood, and dairy products. Also, consider eating foods rich in selenium (such as Brazil nuts, sunflower seeds, and fish) and zinc (found in meat, shellfish, legumes, and seeds).
    Ensure you are consuming sufficient amounts of protein to support thyroid hormone production.
    Avoid Goitrogenic Foods:If you have thyroid problems, avoid excess intake of goitrogenic foods such as soy products, cruciferous vegetables (e.g., cabbage, cauliflower), and millet, which can interfere with thyroid hormone production.
    Regular Exercise:Engage in regular moderate exercise to help support metabolism and improve thyroid function. This can also help mitigate weight gain associated with hypothyroidism.
    Monitor Medications:If you are taking medications that affect thyroid function, such as beta-blockers or amiodarone, discuss alternatives or adjustments with your healthcare provider.
    """)
        elif values["T3 Total"] > 1.81:
            advice.append("""High T3 Total (Hyperthyroidism)
High levels of T3 typically indicate an overactive thyroid, a condition known as hyperthyroidism.

Root Causes of High T3 Total:
    Graves' Disease:The most common cause of high T3 levels is Graves' disease, an autoimmune disorder where the body produces antibodies that stimulate the thyroid gland to produce excess T3 and T4 hormones.
    Toxic Multinodular Goiter:In this condition, multiple nodules in the thyroid gland become overactive and secrete excess thyroid hormones, leading to elevated T3 levels.
    Thyroiditis:Thyroiditis, including subacute thyroiditis and Hashimoto’s thyroiditis, can cause temporary increases in thyroid hormone production, including T3. This often occurs in the early stages of the condition before the thyroid becomes underactive (hypothyroidism).
    Excessive Iodine Intake:Excessive iodine intake from supplements or foods (like iodine-rich seaweed) can cause an increase in thyroid hormone production, resulting in higher T3 levels.
    Thyroid Cancer:Thyroid cancer can cause abnormal production of thyroid hormones, including high T3 levels.
    Medications:Some medications, such as thyroid hormone replacement therapy (if overused) or amiodarone, can lead to excessive thyroid hormone levels, including high T3.
    Pituitary Tumor:Rarely, pituitary tumors (e.g., thyrotropinoma) can cause overproduction of thyroid-stimulating hormone (TSH), leading to increased thyroid hormone production, including T3.

Health Implications of High T3 Total:
    Increased Metabolism: High T3 levels accelerate metabolism, leading to symptoms such as weight loss, nervousness, tremors, heat intolerance, increased heart rate, and high blood pressure.
    Thyroid Storm: In severe cases, uncontrolled hyperthyroidism can lead to thyroid storm, a life-threatening condition that causes fever, confusion, and cardiovascular collapse.
    Osteoporosis: Chronic high T3 levels can increase the risk of bone loss and osteoporosis.
    Cardiovascular Issues: Hyperthyroidism increases the risk of heart conditions like atrial fibrillation and heart failure.

Tips to Manage or Lower High T3 Total:
    Antithyroid Medications:Methimazole or propylthiouracil can be prescribed to block thyroid hormone production in conditions like Graves' disease or toxic goiters. Follow your doctor’s guidance closely.
    Radioactive Iodine Therapy:In cases of toxic multinodular goiter or Graves’ disease, radioactive iodine therapy may be used to shrink the thyroid or destroy overactive thyroid tissue.
    Beta-Blockers:Beta-blockers (such as propranolol) may be used to control symptoms like increased heart rate and tremors associated with high T3 levels.
    Thyroidectomy:In cases where medication and radioactive iodine therapy are ineffective, a partial or total thyroidectomy (removal of part or all of the thyroid) may be necessary.
    Monitor Iodine Intake:If you have hyperthyroidism, avoid excessive intake of iodine, which can exacerbate the condition. Be cautious with iodine-rich supplements and foods like seaweed.
    Stress Management:Stress can exacerbate hyperthyroidism, so managing stress through relaxation techniques and lifestyle changes is beneficial.
    """)

    # T4 Total (range: 5.0-12.0 µg/dL)
    if "T4 Total" in values:
        if values["T4 Total"] < 3.2:
            advice.append("""Low T4 Total (Hypothyroidism)
Low levels of T4 can indicate an underactive thyroid (hypothyroidism), where the thyroid fails to produce adequate amounts of thyroid hormones.

Root Causes of Low T4 Total:
    Hypothyroidism (Primary):Primary hypothyroidism is the most common cause of low T4 levels. It occurs when the thyroid gland itself is not functioning properly. This can be due to autoimmune diseases like Hashimoto's thyroiditis, iodine deficiency, or thyroid surgery.
    Pituitary Dysfunction:Pituitary gland dysfunction can result in low T4 levels. The pituitary gland produces thyroid-stimulating hormone (TSH), which signals the thyroid to release T4. If the pituitary is not working properly (due to tumors, injury, or other disorders), it can lead to insufficient stimulation of the thyroid, causing low T4 levels.
    Iodine Deficiency:Iodine deficiency is a common cause of hypothyroidism, especially in regions where the diet lacks adequate iodine. Since iodine is a key component of T4 and T3 hormones, its deficiency can lead to low T4 levels.
    Medications:Certain medications, such as lithium, amiodarone, and antithyroid drugs like methimazole, can interfere with thyroid hormone production and cause low T4 levels.
    Thyroiditis:Inflammation of the thyroid (such as Hashimoto’s thyroiditis or subacute thyroiditis) can result in an initial increase in thyroid hormones followed by a drop in T4 levels.
    Starvation or Extreme Calorie Restriction:During periods of starvation or severe caloric restriction, the body reduces the production of T4 as part of a mechanism to conserve energy.
    Pregnancy (Hypothyroidism in Pregnancy):In pregnant women, especially during the first trimester, there may be an increased need for thyroid hormone, and insufficient thyroid production can lead to low T4 levels.

Health Implications of Low T4 Total:
    Slowed Metabolism: Symptoms include weight gain, fatigue, cold intolerance, constipation, and dry skin.
    Mental Health: Low T4 can lead to depression, memory issues, and brain fog.
    Cardiovascular Impact: Low T4 may contribute to high cholesterol levels and an increased risk of cardiovascular disease.
    Growth and Development: In children, untreated hypothyroidism can result in delayed growth and cognitive development.

Tips to Improve or Manage Low T4 Total:
    Thyroid Hormone Replacement:Levothyroxine (synthetic T4) is the standard treatment for low T4 levels. It helps normalize hormone levels and alleviate symptoms of hypothyroidism. Regular blood tests to monitor T4 and TSH levels are essential to adjust the dosage.
    Nutrition:
    Iodine: Ensure adequate iodine intake by consuming iodized salt, seafood, and dairy products.
    Selenium: Foods such as Brazil nuts, fish, and seeds are good sources of selenium, which supports thyroid function.
    Zinc: Meat, shellfish, and legumes are rich in zinc, another essential mineral for thyroid health.
    Manage Stress:High levels of stress can negatively impact thyroid function. Incorporate stress management techniques such as yoga, meditation, and regular exercise.
    Avoid Goitrogens:Limit the intake of goitrogenic foods (e.g., soy, cruciferous vegetables) that may interfere with thyroid hormone production.
    Regular Monitoring:If you are on thyroid medication, ensure regular check-ups with your healthcare provider to monitor T4 and TSH levels and adjust treatment as needed.
    """)
        elif values["T4 Total"] > 12.6:
            advice.append("""High T4 Total (Hyperthyroidism)
High levels of T4 indicate an overactive thyroid (hyperthyroidism), where the thyroid produces excessive thyroid hormones, speeding up the body’s metabolic processes.

Root Causes of High T4 Total:
    Graves' Disease:Graves' disease is the most common cause of hyperthyroidism. It’s an autoimmune disorder where the immune system produces antibodies that stimulate the thyroid gland to produce excessive amounts of T4.
    Toxic Multinodular Goiter:In a toxic multinodular goiter, multiple nodules in the thyroid become overactive and secrete excess thyroid hormones, leading to high T4 levels.
    Thyroiditis:Thyroiditis, especially subacute thyroiditis or Hashimoto’s thyroiditis, can cause a temporary increase in thyroid hormone production, including T4. This can occur in the early stages of thyroid inflammation before the thyroid becomes underactive.
    Excessive Iodine Intake:Excessive iodine intake, particularly from supplements or iodine-rich foods (such as seaweed), can lead to increased thyroid hormone production, causing high T4 levels.
    Thyroid Hormone Overuse:If you are on thyroid hormone replacement therapy (e.g., levothyroxine) and take too much, it can lead to high T4 levels.
    Pituitary Tumor (Thyrotropinoma):Rarely, pituitary tumors (thyrotropinoma) can produce excess thyroid-stimulating hormone (TSH), which in turn stimulates the thyroid to produce excess T4.
    Thyroid Cancer:Thyroid cancer can sometimes cause overproduction of thyroid hormones, leading to high T4 levels.

Health Implications of High T4 Total:
    Increased Metabolism: Symptoms include weight loss, nervousness, tremors, heat intolerance, increased heart rate, and high blood pressure.
    Cardiovascular Issues: Hyperthyroidism can lead to arrhythmias (e.g., atrial fibrillation), high blood pressure, and increased risk of heart disease.
    Bone Health: Long-term hyperthyroidism can lead to osteoporosis and bone fractures due to increased metabolic activity.
    Thyroid Storm: In severe cases, thyroid storm (a life-threatening condition) can occur, causing fever, delirium, tachycardia, and heart failure.

Tips to Manage or Lower High T4 Total:
    Antithyroid Medications:Methimazole or propylthiouracil can be prescribed to block thyroid hormone production. These medications help to control hyperthyroidism.
    Radioactive Iodine Therapy:Radioactive iodine therapy may be used to shrink the thyroid or destroy overactive thyroid tissue, which reduces hormone production.
    Beta-Blockers:Beta-blockers, such as propranolol, can be prescribed to control symptoms like tachycardia and tremors that occur with high T4 levels.
    Surgical Treatment (Thyroidectomy):In cases of toxic multinodular goiter or Graves' disease that do not respond to medication or radioactive iodine, surgical removal of part or all of the thyroid may be necessary.
    Monitor Iodine Intake:Limit excessive intake of iodine through supplements or foods like seaweed if you have hyperthyroidism, as this can worsen the condition.
    Stress Management:Reducing stress can help manage hyperthyroid symptoms. Engage in relaxation techniques, yoga, and mindfulness practices.
    """)

    # TSH Ultrasensitive (range: 0.4-4.0 µIU/mL)
    if "TSH Ultrasensitive" in values:
        if values["TSH Ultrasensitive"] < 0.55:
            advice.append("""Low TSH (Hypothyroidism or Secondary Hypothyroidism)
A low TSH level typically indicates hyperthyroidism or thyroid overactivity, where the thyroid produces excessive amounts of thyroid hormones (T3 and T4). In rare cases, low TSH can also indicate secondary hypothyroidism, which occurs due to issues with the pituitary gland or hypothalamus.

Root Causes of Low TSH:
    Hyperthyroidism:Graves' disease, toxic multinodular goiter, and thyroiditis are common causes of hyperthyroidism. In this condition, excessive thyroid hormone production leads to a suppression of TSH secretion, resulting in low TSH levels.
    Graves' disease: An autoimmune condition where the immune system mistakenly stimulates the thyroid to produce too much thyroid hormone.
    Toxic Multinodular Goiter: A condition where multiple overactive thyroid nodules secrete excess thyroid hormones.
    Thyroiditis: Inflammation of the thyroid gland can cause an initial surge in thyroid hormones (including T3 and T4), leading to low TSH levels.
    Secondary Hypothyroidism (Pituitary or Hypothalamic Dysfunction):Secondary hypothyroidism occurs when the pituitary gland or hypothalamus fails to produce enough TSH or Thyroid-Releasing Hormone (TRH), leading to insufficient stimulation of the thyroid gland. This can result from pituitary tumors, pituitary surgery, or trauma.
    Thyroid Hormone Overuse (Excessive Thyroid Medication):If someone is being treated for hypothyroidism (low thyroid function) and takes too much thyroid hormone replacement, it can suppress TSH production and result in low TSH levels.
    Severe Illness or Stress (Non-thyroidal Illness Syndrome):Critical illness, severe stress, or surgery can lead to low TSH levels, even without thyroid dysfunction. This phenomenon is sometimes called non-thyroidal illness syndrome or sick euthyroid syndrome, where low TSH is observed as a response to the body's stress reaction.
    Excessive Iodine Intake:In some cases, excessive iodine intake from supplements or foods can cause an increase in thyroid hormone production, leading to suppressed TSH levels.

Health Implications of Low TSH:
    Increased Metabolism: Symptoms of hyperthyroidism include weight loss, increased heart rate, nervousness, tremors, heat intolerance, and insomnia.
    Cardiovascular Risks: Persistent low TSH due to hyperthyroidism increases the risk of arrhythmias (e.g., atrial fibrillation), high blood pressure, and heart failure.
    Osteoporosis: Long-term hyperthyroidism can lead to bone loss and osteoporosis due to the accelerated metabolism of bone tissue.

Tips to Manage Low TSH:
    Treat Underlying Hyperthyroidism:Medications like methimazole or propylthiouracil (antithyroid drugs) can help reduce thyroid hormone production.
    Radioactive iodine therapy may be used to shrink the thyroid or destroy overactive thyroid tissue.
    In some cases, surgery (thyroidectomy) may be necessary for large goiters or unresponsive cases.
    Beta-Blockers:Beta-blockers (e.g., propranolol) may be prescribed to manage symptoms like tremors, tachycardia, and anxiety.
    Monitoring Thyroid Hormone Replacement:If taking thyroid hormone replacement for hypothyroidism, ensure you’re not taking an excessive dose. Regular monitoring of TSH and free T4 levels is essential to avoid overtreatment.
    Stress Management:Since severe stress or illness can contribute to low TSH levels, consider stress reduction techniques such as meditation, yoga, and breathing exercises.
    """)
        elif values["TSH Ultrasensitive"] > 4.78:
            advice.append("""High TSH (Hypothyroidism or Pituitary Overactivity)
High TSH typically indicates an underactive thyroid (hypothyroidism), where the thyroid fails to produce enough thyroid hormones, and the pituitary gland compensates by producing more TSH in an attempt to stimulate thyroid hormone production. However, in some rare cases, high TSH may result from pituitary tumors or pituitary dysfunction.

Root Causes of High TSH:
    Primary Hypothyroidism:In primary hypothyroidism, the thyroid gland is not producing enough thyroid hormones (T3 and T4), leading the pituitary to produce more TSH in an attempt to stimulate the thyroid. This is the most common cause of high TSH.
    Hashimoto's thyroiditis: An autoimmune disease in which the immune system attacks the thyroid, leading to its dysfunction and low thyroid hormone levels.
    Iodine deficiency: Insufficient iodine intake can result in reduced thyroid hormone production, leading to elevated TSH levels.
    Thyroidectomy: If part or all of the thyroid gland is removed, TSH levels may increase due to decreased thyroid hormone production.
    Secondary Hypothyroidism (Pituitary Dysfunction):In some cases, a pituitary tumor or pituitary dysfunction may result in excessive production of TSH, leading to elevated TSH levels even when thyroid hormone levels are normal. This condition is known as thyrotropinoma.
    Medications (Thyroid Hormone Withdrawal):Abrupt withdrawal of thyroid hormone therapy (e.g., levothyroxine) can cause an increase in TSH levels as the body tries to compensate for the lack of thyroid hormones.
    Congenital Hypothyroidism:In rare cases, a newborn can be born with a non-functioning thyroid, leading to high TSH levels.

Health Implications of High TSH:
    Slowed Metabolism: Symptoms of hypothyroidism include weight gain, fatigue, cold intolerance, dry skin, constipation, and hair thinning.
    Mental Health: High TSH levels can contribute to depression, memory issues, and difficulty concentrating.
    Cardiovascular Risks: Chronic high TSH and low thyroid hormone levels can lead to high cholesterol and an increased risk of heart disease.

Tips to Manage High TSH:
    Thyroid Hormone Replacement:The most common treatment for high TSH levels due to hypothyroidism is levothyroxine, a synthetic form of T4. It helps normalize thyroid hormone levels and reduce TSH secretion.
    Regular monitoring of TSH and free T4 is essential to ensure appropriate dosage adjustments.
    Iodine Supplementation:If iodine deficiency is the cause of elevated TSH, iodine supplementation or dietary adjustments (e.g., consuming iodized salt or seafood) may be recommended.
    Pituitary Tumor Management:If a pituitary tumor (thyrotropinoma) is causing elevated TSH levels, treatment may include surgery, radiation therapy, or medications (such as dopamine agonists).
    Medication Review:If high TSH levels are due to withdrawal from thyroid hormone therapy, ensure you are taking the appropriate dosage of levothyroxine as prescribed by your healthcare provider.
    Regular Monitoring:Regular check-ups with an endocrinologist are necessary to monitor thyroid function, especially if you are on thyroid hormone replacement therapy.
    """)

    # Vitamin B12 (range: 200-900 pg/mL)
    if "Vitamin B12" in values:
        if values["Vitamin B12"] < 211:
            advice.append("""Low Vitamin B12 (Cobalamin Deficiency)
A low vitamin B12 level can lead to a range of health issues because B12 is essential for nerve health, blood cell formation, and the metabolism of homocysteine (an amino acid linked to heart disease). B12 deficiency can also cause neurological and cognitive symptoms.

Root Causes of Low Vitamin B12:
    Poor Dietary Intake:A vegetarian or vegan diet, which excludes animal-based foods, is a common cause of vitamin B12 deficiency because B12 is found primarily in animal products like meat, fish, eggs, and dairy.
    Malabsorption Disorders:Celiac disease, Crohn’s disease, gastric bypass surgery, and other digestive conditions can impair the absorption of vitamin B12 in the intestines.
    Atrophic gastritis (reduced stomach acid production) or pernicious anemia (an autoimmune disorder that affects the stomach's ability to produce intrinsic factor, which is necessary for B12 absorption) can also cause malabsorption.
    Aging:As people age, the body's ability to absorb vitamin B12 from food can decline due to reduced stomach acid production or other digestive changes.
    Medications:Certain medications, such as proton pump inhibitors (PPIs), H2 blockers, and metformin, can interfere with B12 absorption or utilization.
    Alcoholism:Chronic alcohol consumption can impair vitamin B12 absorption and contribute to deficiency over time.
    Pregnancy and Breastfeeding:Pregnant and breastfeeding women may have increased vitamin B12 requirements, and a deficiency can occur if their intake or absorption is insufficient.

Symptoms of Low Vitamin B12:
    Fatigue, weakness, and anemia (pale skin and shortness of breath)
    Numbness, tingling, or burning sensations in hands and feet (due to nerve damage)
    Cognitive issues such as memory loss, confusion, or difficulty concentrating
    Depression or mood changes
    Glossitis (inflamed, red tongue) and mouth ulcers
    Vision problems due to nerve damage in the eyes (optic neuropathy)
    Pale or jaundiced skin due to anemia

Tips to Increase Vitamin B12:
    Dietary Sources are as follows
    Include more animal-based foods in the diet, such as:
    Meat (especially liver and red meats)
    Fish (salmon, tuna, mackerel)
    Dairy products (milk, cheese, yogurt)
    Eggs
    For vegetarians and vegans, consider fortified foods such as:
    Fortified cereals
    Fortified plant-based milks (soy, almond, oat)
    Nutritional yeast
    Vitamin B12 Supplements:Oral B12 supplements are widely available, either as a daily pill or a sublingual (under-the-tongue) form.
    Injections or nasal sprays may be recommended for severe deficiencies or those with malabsorption issues.
    Address Malabsorption Issues:If you have a malabsorption disorder (e.g., celiac disease, Crohn’s disease), work with your healthcare provider to manage the condition and ensure proper absorption of nutrients.
    Pernicious anemia may require B12 injections or high-dose oral supplements due to the body's inability to absorb B12.
    Check Medications:If you're on medications like metformin, PPIs, or H2 blockers, speak with your healthcare provider to see if a B12 deficiency is contributing to symptoms.""")
        elif values["Vitamin B12"] > 911:
            advice.append("""High Vitamin B12 (Cobalamin Excess)
While vitamin B12 toxicity is rare (since it is a water-soluble vitamin), high levels of B12 can sometimes be associated with certain medical conditions or excess supplementation. The body typically excretes excess B12 through urine.

Root Causes of High Vitamin B12:
    Excessive Supplementation:Taking high doses of B12 supplements without medical supervision can lead to high levels of vitamin B12 in the blood.
    People using B12 injections or high-dose oral supplements should monitor their levels regularly to avoid excessive intake.
    Liver Disease:Conditions such as liver cirrhosis or hepatitis can lead to high B12 levels, as the liver stores a large amount of vitamin B12 and releases it into the bloodstream when damaged.
    Kidney Dysfunction:In cases of kidney disease or chronic renal failure, the body may have difficulty excreting excess B12, leading to elevated levels.
    Leukemia or Myeloproliferative Disorders:Certain blood cancers, like leukemia or polycythemia vera, can cause high B12 levels due to the increased production of white blood cells, which consume and release B12.
    Intestinal Issues:Certain intestinal conditions, such as small intestine bacterial overgrowth (SIBO), can alter the balance of vitamin B12 in the gut and lead to higher levels in the blood.
    Excessive Intake of Animal Products:While it's uncommon, very high consumption of animal products (especially organ meats like liver) could lead to elevated B12 levels.

Symptoms of High Vitamin B12:
    Acne or skin rashes (rare but reported)
    Nausea or vomiting
    Headaches or dizziness
    Fatigue or weakness (though high B12 itself typically doesn’t cause these symptoms directly, they could be related to the underlying condition causing elevated levels)
    Increased risk of blood clots or cardiovascular issues (in some individuals with high B12 related to underlying conditions like liver disease or myeloproliferative disorders)

Tips for Managing High Vitamin B12:
    Review Supplementation:If you are taking B12 supplements, consider reducing the dose or stopping supplementation under the guidance of your healthcare provider.
    Ensure your B12 intake is within the recommended daily allowance (RDA) unless instructed otherwise by a doctor.
    Monitor Medical Conditions:If you have conditions like liver disease, kidney problems, or blood disorders, closely monitor your B12 levels and work with your healthcare provider to manage underlying conditions.
    Test for Underlying Conditions:High B12 levels may indicate a serious underlying health condition, so it's important to consult your healthcare provider if you have elevated levels. Additional tests may be needed to rule out liver disease, kidney dysfunction, or hematologic disorders.""")

    # 25 (OH) Vitamin D2 (Ergocalciferol) (range: 20-50 ng/mL)
    if "25 (OH) Vitamin D2 (Ergocalciferol)" in values:
        if values["25 (OH) Vitamin D2 (Ergocalciferol)"] < 20:
            advice.append("""Low 25(OH) Vitamin D2 (Deficiency)
Low levels of 25(OH) Vitamin D2 can occur due to insufficient sunlight exposure, poor dietary intake, or conditions that impair absorption or metabolism of vitamin D. It can lead to vitamin D deficiency and associated health problems.

Root Causes of Low Vitamin D2:
    Inadequate Sunlight Exposure:Vitamin D is produced in the skin upon exposure to sunlight. Insufficient exposure to sunlight (e.g., in areas with long winters, indoor lifestyles, or use of sunscreen) can lead to low vitamin D levels.
    Dietary Deficiency:Vitamin D2 is found in plant-based foods and fortified products, but it is not as readily available in the diet as Vitamin D3 (found in animal-based foods). If your diet is low in these sources, you might have low levels of D2.
    Malabsorption Disorders:Celiac disease, Crohn’s disease, and other conditions that impair nutrient absorption in the gut can contribute to vitamin D deficiency.
    Liver or Kidney Disease:The liver is responsible for converting vitamin D into its active form. Conditions like liver cirrhosis or chronic kidney disease can impair the conversion of vitamin D2 to its active form, leading to deficiency.
    Obesity:Individuals with higher body fat may have lower circulating levels of vitamin D because vitamin D is fat-soluble and can become sequestered in fat tissue, reducing its availability in the bloodstream.
    Age:Older adults have a reduced ability to synthesize vitamin D in the skin and absorb it efficiently from food, making them more vulnerable to deficiency.
    Medications:Certain medications, such as antiepileptic drugs (e.g., phenytoin), steroids, and weight-loss surgery medications, can reduce vitamin D absorption or metabolism.

Health Implications of Low Vitamin D2:
    Bone Health: Osteomalacia (softening of bones) and osteoporosis (brittle bones), which increase the risk of fractures.
    Muscle Weakness: Low vitamin D can cause muscle weakness and increase the risk of falls, especially in the elderly.
    Immune Function: Vitamin D plays a role in immune system regulation, and deficiency may contribute to an increased risk of infections or autoimmune conditions.
    Mood Disorders: Depression, fatigue, and other mood-related disorders have been linked to vitamin D deficiency.
    Increased Risk of Chronic Diseases: Deficiency in vitamin D is associated with increased risks for cardiovascular disease, diabetes, and certain cancers.

Tips to Increase Vitamin D2:
    Sunlight Exposure:10-30 minutes of direct sunlight exposure several times a week, depending on skin tone and geographic location, is often enough to stimulate the production of vitamin D.
    Vitamin D2-Rich Foods:Plant-based sources of vitamin D2 include:
    Mushrooms (especially varieties exposed to UV light like maitake mushrooms).
    Fortified foods such as fortified plant-based milks (soy, almond, oat), fortified orange juice, and fortified cereals.
    Supplements:Vitamin D2 supplements can help restore levels, especially for those who have limited sunlight exposure or difficulty absorbing vitamin D from food.
    Address Underlying Conditions:Treat or manage underlying conditions like malabsorption disorders and liver or kidney disease that can impair vitamin D absorption or activation.
    Weight Management:Maintaining a healthy weight may improve the availability of vitamin D in the bloodstream, especially for people with obesity.
    """)
        elif values["25 (OH) Vitamin D2 (Ergocalciferol)"] > 50:
            advice.append("""High 25(OH) Vitamin D2 (Toxicity or Excess)
High levels of 25(OH) Vitamin D2 (known as vitamin D toxicity) are rare but can occur due to excessive supplementation or intake of vitamin D2.

Root Causes of High Vitamin D2:
    Excessive Supplementation:Taking too much vitamin D2 from supplements is the most common cause of vitamin D toxicity. Typically, high doses of supplements (often greater than 10,000 IU per day) are required to cause toxicity.
    Excessive Fortified Foods:While fortified foods contain small amounts of vitamin D, consuming large quantities of these foods alongside supplements could contribute to elevated levels.
    Supplementing with Vitamin D3:If a person is supplementing with vitamin D3 (another form of vitamin D) along with vitamin D2, the total vitamin D intake could lead to elevated levels.
    Granulomatous Diseases:Certain conditions, such as sarcoidosis, tuberculosis, and histoplasmosis, can cause the body to convert more vitamin D into its active form, potentially leading to elevated levels of circulating vitamin D.
    Hyperparathyroidism:Primary hyperparathyroidism, a condition where the parathyroid glands overproduce parathyroid hormone (PTH), can increase calcium absorption and lead to higher vitamin D levels.
    Health Implications of High Vitamin D2:
    Hypercalcemia: Excess vitamin D can lead to elevated levels of calcium in the blood, which can cause symptoms such as:
    Nausea, vomiting
    Fatigue, weakness
    Confusion or disorientation
    Kidney stones or kidney damage (due to excess calcium)
    Bone pain and calcification of soft tissues
    Risk of Cardiovascular Problems: Chronic hypercalcemia due to vitamin D toxicity can increase the risk of heart disease and arterial calcification.
    Renal Dysfunction: Kidney damage or kidney stones may result from the excess calcium that accompanies vitamin D toxicity.

Tips for Managing High Vitamin D2:
    Discontinue Supplements:If you are taking high doses of vitamin D2 or vitamin D3, stop supplementation immediately and consult your healthcare provider to manage levels.
    Monitor Blood Calcium Levels:Blood tests should be performed to check calcium levels. If calcium levels are high, further steps will be necessary to prevent kidney damage.
    Hydration:Ensure adequate hydration and drink plenty of fluids to help flush excess calcium from the body.
    Address Underlying Conditions:If vitamin D toxicity is linked to an underlying condition such as sarcoidosis or hyperparathyroidism, treat the underlying disease and manage vitamin D intake accordingly.
    Gradual Reduction of Vitamin D Intake:In some cases, a gradual reduction in vitamin D intake might be recommended to safely lower vitamin D levels without causing further complications.""")

    # 25 (OH) Vitamin D3 (Cholecalciferol) (range: 20-50 ng/mL)
    if "25 (OH) Vitamin D3 (Cholecalciferol)" in values:
        if values["25 (OH) Vitamin D3 (Cholecalciferol)"] < 20:
            advice.append("""Low 25(OH) Vitamin D3 (Deficiency)
Low levels of 25(OH) Vitamin D3 can occur due to inadequate sun exposure, poor dietary intake, or conditions that impair the absorption or metabolism of vitamin D. This can lead to vitamin D deficiency, resulting in a range of health problems.

Root Causes of Low Vitamin D3:
    Inadequate Sunlight Exposure:Vitamin D3 is primarily produced in the skin when exposed to sunlight (UVB rays). Limited sun exposure, especially during the winter months, or living in northern latitudes, can lead to vitamin D3 deficiency.
    Sunscreen can also block UVB rays, reducing the body’s ability to produce vitamin D3.
    Dietary Deficiency:Vitamin D3 is found in animal-based foods such as:
    Fatty fish (salmon, mackerel, tuna)
    Egg yolks
    Fortified dairy products
    Liver
    People who follow a strict vegetarian or vegan diet may be at risk for deficiency since vitamin D3 is mostly found in animal products.
    Malabsorption Disorders:Conditions like celiac disease, Crohn's disease, celiac disease, and gastrointestinal surgeries can impair vitamin D absorption in the intestines.
    Aging:Older adults may have a reduced ability to synthesize vitamin D from sunlight and absorb it from food.
    Obesity:People with higher body fat percentages may experience lower circulating vitamin D levels because vitamin D is fat-soluble and can be stored in fat tissue, making it less available for the body to use.
    Liver or Kidney Disease:Liver disease (cirrhosis) and kidney disease can affect the body’s ability to activate vitamin D3, resulting in low levels of circulating 25(OH) Vitamin D3.
    Medications:Some medications, such as antiepileptic drugs and steroids, can affect vitamin D metabolism and lower its levels.

Health Implications of Low Vitamin D3:
    Bone Health: Deficiency in vitamin D3 can lead to osteomalacia (softening of bones) and osteoporosis (fragile bones), increasing the risk of fractures.
    Muscle Weakness: Low vitamin D3 is associated with muscle weakness and an increased risk of falls, especially in older adults.
    Weakened Immune System: Vitamin D3 plays a crucial role in regulating immune function. Deficiency may lead to an increased susceptibility to infections.
    Mood Disorders: There is a correlation between low vitamin D3 and depression, anxiety, and other mood disorders.
    Increased Risk of Chronic Diseases: Low vitamin D3 levels have been linked to cardiovascular diseases, type 2 diabetes, and autoimmune conditions like multiple sclerosis.

Tips to Increase Vitamin D3:
    Sunlight Exposure:Spend 10–30 minutes a few times a week in direct sunlight, depending on skin type and geographical location. Expose large areas of skin (arms, face, and legs) without sunscreen to facilitate vitamin D production.
    Dietary Sources:Increase consumption of animal-based foods that are rich in vitamin D3, such as:
    Fatty fish (salmon, sardines, mackerel)
    Egg yolks
    Fortified dairy and plant-based milks
    Liver from animals
    Supplements:Vitamin D3 supplements are often recommended for individuals at risk of deficiency. A healthcare provider can determine the appropriate dosage.
    Treat Underlying Conditions:If you have conditions like malabsorption disorders (e.g., celiac disease) or liver/kidney disease, treating or managing these conditions may improve vitamin D absorption and activation.
    Regular Monitoring:People at risk of deficiency, such as the elderly, those with darker skin, or those living in northern climates, should have their vitamin D3 levels checked regularly to prevent deficiency.
    """)
        elif values["25 (OH) Vitamin D3 (Cholecalciferol)"] > 50:
            advice.append("""High 25(OH) Vitamin D3 (Toxicity or Excess)
High levels of 25(OH) Vitamin D3 can be caused by excessive supplementation or excessive consumption of fortified foods, leading to vitamin D toxicity. This is much less common than deficiency, but it can have serious health consequences.

Root Causes of High Vitamin D3:
    Excessive Supplementation:Taking high doses of vitamin D3 supplements (typically more than 4,000 IU per day) can lead to vitamin D toxicity. Very high doses (10,000 IU or more) can be dangerous and cause harmful effects.
    Fortified Foods:While unlikely, excessive consumption of foods that are fortified with vitamin D3 (e.g., fortified cereals, milk, or juices) alongside high-dose supplements could lead to elevated levels.
    Granulomatous Diseases:Conditions like sarcoidosis, tuberculosis, and histoplasmosis can cause an increase in vitamin D levels by enhancing the body’s ability to convert vitamin D into its active form, leading to elevated blood levels of 25(OH) Vitamin D3.
    Hyperparathyroidism:In cases of primary hyperparathyroidism, the parathyroid glands overproduce parathyroid hormone (PTH), which can affect calcium and vitamin D metabolism, leading to elevated vitamin D levels.

Health Implications of High Vitamin D3:
    Hypercalcemia:High vitamin D3 levels can cause elevated calcium levels in the blood (hypercalcemia), leading to:
    Nausea, vomiting
    Weakness, fatigue
    Confusion, and disorientation
    Kidney stones or kidney damage due to calcium deposits.
    Kidney Damage:Excess calcium can cause kidney stones and may lead to renal failure if not addressed.
    Bone Pain:High vitamin D levels can cause bone pain or calcification of soft tissues, leading to pain and reduced flexibility.
    Cardiovascular Problems:Prolonged high levels of vitamin D can lead to arterial calcification, heart disease, and an increased risk of stroke or other cardiovascular issues.

Tips for Managing High Vitamin D3:
    Discontinue Supplements:If you are taking high doses of vitamin D3 supplements, stop supplementation immediately and consult your healthcare provider for further evaluation.
    Monitor Calcium Levels:Blood tests should be performed to check for elevated calcium levels (hypercalcemia). Treatment may involve fluids and medications to reduce calcium levels if necessary.
    Hydration:Drink plenty of fluids to help flush excess calcium from the kidneys and reduce the risk of kidney stones.
    Monitor for Underlying Conditions:If elevated vitamin D3 levels are caused by an underlying condition such as sarcoidosis or hyperparathyroidism, addressing the root cause is crucial. Treatment for these conditions may involve medications to manage calcium and vitamin D metabolism.
    Gradual Reduction in Vitamin D Intake:If vitamin D toxicity is suspected, it may be necessary to gradually reduce vitamin D intake rather than stopping abruptly, under the supervision of a healthcare provider.""")

    if "Vitamin D Total (D2 + D3)" in values:
        if values["Vitamin D Total (D2 + D3)"] < 20:
            advice.append("""Low Vitamin D Total (D2 + D3) – Deficiency
Low levels of Vitamin D Total (D2 + D3) indicate vitamin D deficiency, which can have a negative impact on bone health, immune function, and overall well-being.

Root Causes of Low Vitamin D Total (D2 + D3):
    Inadequate Sunlight Exposure:Sunlight is the most natural source of Vitamin D3. Lack of sun exposure—particularly in regions with long winters, or due to lifestyle factors like spending most of the time indoors—can result in low levels of Vitamin D.
    Dietary Deficiency:Vitamin D-rich foods (like fatty fish, egg yolks, and fortified foods) may be lacking in the diet, leading to deficiency, particularly in people who avoid animal products or have strict vegan diets.
    Malabsorption Disorders:Conditions like Crohn's disease, celiac disease, and IBS can interfere with the absorption of Vitamin D from the digestive tract.
    Aging:As people age, their skin becomes less efficient at producing Vitamin D when exposed to sunlight, and their kidneys become less effective at converting Vitamin D to its active form.
    Obesity:Vitamin D is fat-soluble, and in individuals with higher body fat, Vitamin D may be stored in fat tissue, rendering it less bioavailable to the body.
    Liver or Kidney Disease:The liver and kidneys play a crucial role in converting Vitamin D to its active form. Liver diseases (like cirrhosis) or kidney diseases can impair this conversion, resulting in lower active Vitamin D levels in the body.
    Medications:Certain medications, such as anticonvulsants or steroids, can interfere with Vitamin D metabolism and lower levels.

Health Implications of Low Vitamin D Total:
    Bone Health: Osteomalacia (softening of bones) and osteoporosis (fragile bones) can result from chronic Vitamin D deficiency.
    Muscle Weakness: Low levels of Vitamin D can contribute to muscle weakness, especially in older adults.
    Weakened Immune System: Insufficient Vitamin D impairs the immune system, increasing the risk of infections.
    Mood Disorders: Vitamin D deficiency is linked to depression and anxiety.
    Chronic Conditions: There may be an increased risk of developing chronic conditions, including cardiovascular diseases and type 2 diabetes.

Tips to Increase Vitamin D Total (D2 + D3):
    Increase Sun Exposure:Spend 10–30 minutes in direct sunlight several times a week, depending on skin type and geographical location. Ensure large areas of skin (face, arms, and legs) are exposed for optimal Vitamin D synthesis.
    Dietary Sources:Incorporate Vitamin D-rich foods into your diet, such as:
    Fatty fish (salmon, sardines, mackerel)
    Egg yolks
    Fortified foods (dairy products, plant-based milks, cereals)
    Liver (chicken or beef)
    Supplements:Vitamin D supplements (D3 is usually recommended over D2 for better efficacy) may be needed for individuals at risk of deficiency. A healthcare provider should determine the correct dosage.
    Manage Malabsorption Conditions:If you have digestive disorders like celiac disease or Crohn's disease, addressing these conditions may improve your ability to absorb Vitamin D.
    Monitor and Consult Healthcare Providers:Regular blood tests can help determine if you are getting sufficient Vitamin D, particularly if you are in a higher-risk category (e.g., elderly, obese, living in areas with limited sunlight).
    """)
        elif values["Vitamin D Total (D2 + D3)"] > 100:
            advice.append("""High Vitamin D Total (D2 + D3) – Toxicity or Excess
High levels of Vitamin D Total (D2 + D3) indicate Vitamin D toxicity or excessive intake, which is usually caused by excessive supplementation rather than food or sun exposure.

Root Causes of High Vitamin D Total (D2 + D3):
    Excessive Supplementation:The most common cause of high Vitamin D levels is taking high doses of supplements (typically above 4,000 IU per day), especially without medical supervision. Very high doses of Vitamin D3 (10,000 IU or more daily) can lead to toxicity.
    Fortified Foods:Overconsumption of fortified foods—such as cereals, milk, or juices—alongside high-dose Vitamin D supplements can contribute to elevated Vitamin D levels.
    Granulomatous Diseases:Certain diseases, like sarcoidosis, tuberculosis, or histoplasmosis, can increase the conversion of Vitamin D to its active form, raising blood levels beyond normal limits.
    Hyperparathyroidism:In primary hyperparathyroidism, excessive parathyroid hormone (PTH) leads to an increase in calcium and Vitamin D levels.

Health Implications of High Vitamin D Total:
    Hypercalcemia: High Vitamin D levels can cause elevated calcium levels, leading to symptoms like:
    Nausea, vomiting
    Weakness, fatigue
    Confusion, and disorientation
    Kidney stones and calcification of soft tissues.
    Kidney Damage: The excess calcium can cause kidney stones, and in severe cases, it can lead to kidney failure.
    Bone Pain and Mineralization Issues: Prolonged excess Vitamin D can lead to bone pain or calcification of soft tissues like the kidneys, lungs, or blood vessels.
    Cardiovascular Issues: High Vitamin D levels can lead to vascular calcification, increasing the risk of heart disease, stroke, and hypertension.

Tips to Manage High Vitamin D Total (D2 + D3):
    Stop Supplementation:If you suspect you are taking too much Vitamin D, stop supplements immediately and consult a healthcare provider. Do not attempt to correct high levels without professional guidance.
    Monitor Calcium Levels:A blood test to check calcium levels (hypercalcemia) is crucial. Elevated calcium levels can indicate that the body is absorbing too much calcium due to high Vitamin D levels. Immediate steps might be needed to correct the imbalance.
    Increase Fluid Intake:Stay hydrated to help flush out excess calcium through the kidneys and reduce the risk of kidney stones.
    Treat Underlying Conditions:If the high Vitamin D levels are caused by an underlying condition like sarcoidosis or hyperparathyroidism, addressing the primary disease may help normalize vitamin D levels.
    Gradual Reduction:In some cases, it may be necessary to gradually reduce the Vitamin D intake under medical supervision instead of stopping abruptly.""")

    # Iron (range: 50-170 µg/dL)
    if "Iron" in values:
        if values["Iron"] < 70:
            advice.append("""Low Iron – Iron Deficiency
Low iron levels typically indicate iron deficiency, which can lead to various health complications.

Root Causes of Low Iron:
    Inadequate Dietary Intake:Iron is found in both heme (animal-based) and non-heme (plant-based) forms. A diet lacking in iron-rich foods, such as red meat, poultry, fish, legumes, and leafy greens, can cause low iron levels.
    Blood Loss:Heavy menstruation or bleeding ulcers, gastric bleeding, or hemorrhoids can lead to blood loss, depleting iron levels over time. This can also occur with frequent blood donations.
    Malabsorption:Conditions like celiac disease, Crohn's disease, or gastric bypass surgery can impair the body’s ability to absorb iron from food, leading to deficiencies.
    Pregnancy:During pregnancy, the body’s demand for iron increases to support the growing fetus, often leading to iron deficiency if not supplemented.
    Chronic Conditions:Chronic conditions like chronic kidney disease or heart failure can affect iron metabolism or cause blood loss, resulting in low iron levels.
    Vegetarian or Vegan Diets:Non-heme iron, found in plant-based foods, is not absorbed as efficiently as heme iron from animal sources. Vegans and vegetarians are at higher risk of iron deficiency without careful dietary planning.
    Health Implications of Low Iron:Iron-deficiency anemia: Fatigue, weakness, and paleness due to reduced hemoglobin production.
    Impaired oxygen transport: Leads to shortness of breath, dizziness, and heart palpitations.
    Weakened immune system: Iron deficiency can impair immune function, leading to increased susceptibility to infections.
    Hair loss: Insufficient iron may result in hair thinning or brittle hair.
    Cold intolerance: Low iron levels may make you feel colder than usual due to decreased blood flow.

Tips to Increase Iron Levels:
    Increase Iron-Rich Foods such as
    Heme iron (animal-based sources) is more easily absorbed:
    Red meat, poultry, fish, and shellfish
    Non-heme iron (plant-based sources) include:
    Spinach, lentils, beans, tofu, quinoa, fortified cereals
    Iron-fortified bread and pasta
    Pair with Vitamin C-rich foods (like citrus fruits, tomatoes, and bell peppers) to enhance iron absorption.
    Iron Supplements:Iron supplements (usually in the form of ferrous sulfate) may be necessary for individuals with severe deficiency or malabsorption issues. Always take supplements under the guidance of a healthcare provider to avoid iron overload.
    Cook in Cast Iron Pans:Cooking acidic foods (e.g., tomatoes) in cast iron pans can increase the iron content of meals.
    Avoid Iron Blockers:Limit the intake of substances that inhibit iron absorption, such as:
    Coffee and tea (due to tannins)
    Calcium-rich foods (when consumed with iron-rich meals)
    High-fiber foods (when eaten in excess with iron-rich foods)
    Manage Menstrual Flow:If heavy periods are causing significant blood loss, consult a doctor about potential treatment options (e.g., hormone therapy, iron supplementation).""")
        elif values["Iron"] > 180:
            advice.append("""High Iron – Iron Overload (Hemochromatosis)
High iron levels can indicate iron overload, a condition where too much iron accumulates in the body, potentially causing damage to organs.

Root Causes of High Iron:
    Hereditary Hemochromatosis:A genetic disorder where the body absorbs excessive amounts of iron from food. This leads to iron buildup in tissues and organs such as the liver, heart, and pancreas, causing long-term damage.
    Excessive Iron Supplementation:Overuse of iron supplements or taking supplements without proper medical supervision can lead to iron toxicity. This is particularly common in individuals who don’t have a deficiency but consume excess iron.
    Frequent Blood Transfusions:Individuals with anemia or other blood disorders who require frequent blood transfusions (e.g., thalassemia or sickle cell anemia) can accumulate excess iron.
    Liver Disease:Certain liver conditions, such as chronic hepatitis or cirrhosis, can result in impaired iron metabolism and iron overload.
    Chronic Alcoholism:Excessive alcohol consumption can cause liver damage, affecting iron metabolism and leading to iron buildup.
    Health Implications of High Iron:Liver Damage: Accumulated iron can damage the liver, leading to conditions like cirrhosis, liver fibrosis, or even liver cancer.
    Heart Problems: Excessive iron can accumulate in the heart, causing conditions like arrhythmias, heart failure, and cardiomyopathy.
    Diabetes: High iron levels can impair the pancreas and interfere with insulin production, potentially leading to diabetes.
    Joint Pain: Iron buildup in joints can lead to arthritis and joint pain.
    Endocrine Disorders: Excess iron can also affect other organs, including the thyroid, adrenal glands, and pituitary gland, disrupting hormone production and leading to other health issues.

Tips to Manage High Iron Levels:
    Phlebotomy (Blood Donation):For individuals with hereditary hemochromatosis or iron overload, regular blood donation or therapeutic phlebotomy can help reduce iron levels.
    Iron Chelation Therapy:For people who cannot donate blood (e.g., those with anemia), iron chelation therapy (using medications like deferoxamine or deferasirox) may be necessary to help the body excrete excess iron.
    Avoid Iron-Rich Foods and Supplements:Limit the consumption of iron-rich foods, such as red meat, liver, and iron-fortified cereals, if your iron levels are high.
    Avoid iron supplements unless advised by a healthcare provider.
    Limit Vitamin C Intake:Vitamin C increases iron absorption, so avoid high amounts of Vitamin C with iron-rich meals if you're dealing with iron overload.
    Avoid Alcohol:Excessive alcohol can worsen liver damage, so it's essential to limit alcohol intake if dealing with high iron levels.
    Monitor Iron Levels Regularly:Regular monitoring of serum ferritin and transferrin saturation is essential for individuals with iron overload conditions or those at risk, to prevent damage to organs.
    """)

    # Transferrin Saturation (range: 20-50%)
    if "Transferrin Saturation" in values:
        if values["Transferrin Saturation"] < 18:
            advice.append("""Low Transferrin Saturation – Iron Deficiency
Low transferrin saturation indicates that the amount of iron bound to transferrin is lower than normal, which usually suggests iron deficiency. This is the most common cause of low transferrin saturation.

Root Causes of Low Transferrin Saturation:
    Iron Deficiency:Inadequate dietary intake of iron or poor absorption can result in iron deficiency anemia, leading to low transferrin saturation.
    Chronic Blood Loss:Conditions that cause chronic bleeding, such as heavy menstruation, gastric ulcers, or hemorrhoids, can lead to a decrease in iron levels, causing low transferrin saturation.
    Malabsorption Syndromes:Diseases like celiac disease, Crohn’s disease, or gastric bypass surgery can impair the absorption of iron, leading to low iron levels and low transferrin saturation.
    Pregnancy:Increased iron requirements during pregnancy can cause a decrease in transferrin saturation, especially if iron intake is insufficient.
    Acute or Chronic Inflammation:Inflammatory conditions (e.g., infections, chronic kidney disease, or rheumatoid arthritis) can lead to anemia of chronic disease, which often presents with low transferrin saturation. This occurs because the body prioritizes iron storage and limits iron availability in the bloodstream.
    Hypoproteinemia:Conditions causing low protein levels (such as liver disease or malnutrition) can reduce transferrin production, leading to a decrease in transferrin saturation.
    Health Implications of Low Transferrin Saturation:Iron-Deficiency Anemia: Symptoms of fatigue, paleness, shortness of breath, dizziness, and headaches.
    Weak Immune System: Iron is essential for immune function, and deficiency can lead to increased susceptibility to infections.
    Hair Loss: Insufficient iron can cause brittle hair and hair thinning.
    Cognitive Impairments: Prolonged low transferrin saturation may result in concentration problems and memory difficulties.

Tips to Increase Transferrin Saturation (for Iron Deficiency):
    Increase Iron-Rich Foods such as
    Heme iron (from animal sources) is more readily absorbed by the body:
    Red meat, poultry, fish, shellfish
    Non-heme iron (from plant-based sources) can also improve iron status:
    Spinach, lentils, tofu, beans, quinoa, and fortified cereals
    Pair iron-rich foods with Vitamin C (e.g., citrus fruits, tomatoes) to enhance absorption.
    Iron Supplements:For more severe deficiencies, iron supplements (usually in the form of ferrous sulfate) may be necessary. Always consult a healthcare provider for appropriate dosage and form.
    Cook with Cast Iron Cookware:Cooking acidic foods (like tomatoes) in a cast iron pan can increase the iron content of meals.
    Treat Underlying Conditions:If there are issues like chronic blood loss (heavy periods, ulcers), addressing the root cause can help improve iron levels.
    """)
        elif values["Transferrin Saturation"] > 40:
            advice.append("""High Transferrin Saturation – Iron Overload
High transferrin saturation suggests that a larger percentage of transferrin is bound to iron, which could indicate iron overload. This may be seen in conditions where the body has too much iron, such as hereditary hemochromatosis.

Root Causes of High Transferrin Saturation:
    Hereditary Hemochromatosis:A genetic disorder where excessive iron is absorbed from the diet, leading to iron overload and high transferrin saturation. Iron builds up in organs such as the liver, heart, and pancreas, causing damage.
    Excessive Iron Supplementation:Overuse of iron supplements or taking iron supplements unnecessarily can lead to high transferrin saturation.
    Frequent Blood Transfusions:Conditions such as thalassemia or sickle cell disease, which require frequent blood transfusions, can result in iron accumulation, leading to high transferrin saturation.
    Chronic Liver Disease:Conditions such as cirrhosis, hepatitis, or alcoholism can impair iron metabolism and lead to high transferrin saturation.
    Iron Overload Due to Other Disorders:Chronic blood diseases like thalassemia or sickle cell disease can lead to increased iron storage, which can result in high transferrin saturation.
    Excessive Vitamin C Intake:High levels of Vitamin C may increase iron absorption and exacerbate iron overload in individuals with high transferrin saturation.

Health Implications of High Transferrin Saturation:
    Iron Toxicity: Accumulation of excess iron can damage organs, including the liver, heart, and pancreas, leading to cirrhosis, heart disease, and diabetes.
    Joint Pain: Iron overload can lead to joint pain or arthritis due to iron deposition in the joints.
    Endocrine Dysfunction: Excess iron can affect the pancreas, leading to diabetes, and may also impact the thyroid, adrenal glands, and pituitary gland.
    Cardiac Issues: Excess iron can accumulate in the heart, leading to conditions like arrhythmias, heart failure, and cardiomyopathy.

Tips to Manage High Transferrin Saturation (for Iron Overload):
    Phlebotomy (Blood Donation):Regular blood donations or therapeutic phlebotomy can help reduce the iron levels and improve transferrin saturation. This is often the first line of treatment for hereditary hemochromatosis.
    Iron Chelation Therapy:In cases of severe iron overload (especially if phlebotomy isn’t possible), iron chelation therapy using medications like deferoxamine or deferasirox can help the body excrete excess iron.
    Limit Iron-Rich Foods:Reduce the intake of iron-rich foods like red meat, liver, and iron-fortified cereals if iron overload is a concern.
    Avoid Vitamin C Supplements:Since Vitamin C increases iron absorption, it may be important to avoid high doses of Vitamin C supplements if you have high transferrin saturation.
    Monitor Iron Levels Regularly:For individuals with known iron overload disorders, regular monitoring of serum ferritin and transferrin saturation is crucial to prevent organ damage and manage iron levels effectively.""")

    return advice if advice else ["No specific advice. Keep maintaining a healthy lifestyle!"]

@app.route("/", methods=["GET", "POST"])
def homepage():
    return render_template("index.html")

@app.route("/uploads", methods=["GET", "POST"])
def home():
    if 'values' not in session:
        session['values'] = {
    "Haemoglobin": 0,
    "Total RBC Count": 0,
    "Packed Cell Volume / Hematocrit": 0,
    "MCV": 0,
    "MCH": 0,
    "MCHC": 0,
    "RDW": 0,
    "Total Leucocytes Count": 0,
    "Neutrophils": 0,
    "Lymphocytes": 0,
    "Eosinophils": 0,
    "Monocytes": 0,
    "Basophils": 0,
    "Absolute Neutrophil Count": 0,
    "Absolute Lymphocyte Count": 0,
    "Absolute Eosinophil Count": 0,
    "Absolute Monocyte Count": 0,
    "Platelet Count": 0,
    "Erythrocyte Sedimentation Rate": 0,
    "Fasting Plasma Glucose": 0,
    "Glycated Hemoglobin": 0,
    "Triglycerides": 0,
    "Total Cholesterol": 0,
    "LDL Cholesterol": 0,
    "HDL Cholesterol": 0,
    "VLDL Cholesterol": 0,
    "Total Cholesterol / HDL Cholesterol Ratio": 0,
    "LDL Cholesterol / HDL Cholesterol Ratio": 0,
    "Total Bilirubin": 0,
    "Direct Bilirubin": 0,
    "Indirect Bilirubin": 0,
    "SGPT/ALT": 0,
    "SGOT/AST": 0,
    "Alkaline Phosphatase": 0,
    "Total Protein": 0,
    "Albumin": 0,
    "Globulin": 0,
    "Protein A/G Ratio": 0,
    "Gamma Glutamyl Transferase": 0,
    "Creatinine": 0,
    "e-GFR (Glomerular Filtration Rate)": 0,
    "Urea": 0,
    "Blood Urea Nitrogen": 0,
    "Uric Acid": 0,
    "T3 Total": 0,
    "T4 Total": 0,
    "TSH Ultrasensitive": 0,
    "Vitamin B12": 0,
    "25 (OH) Vitamin D2 (Ergocalciferol)": 0,
    "25 (OH) Vitamin D3 (Cholecalciferol)": 0,
    "Vitamin D Total (D2 + D3)": 0,
    "Iron": 0,
    "Total Iron Binding Capacity": 0,
    "Transferrin Saturation": 0
}

        session.modified = True

    values = session.get('values', {
    "Haemoglobin": 0,
    "Total RBC Count": 0,
    "Packed Cell Volume / Hematocrit": 0,
    "MCV": 0,
    "MCH": 0,
    "MCHC": 0,
    "RDW": 0,
    "Total Leucocytes Count": 0,
    "Neutrophils": 0,
    "Lymphocytes": 0,
    "Eosinophils": 0,
    "Monocytes": 0,
    "Basophils": 0,
    "Absolute Neutrophil Count": 0,
    "Absolute Lymphocyte Count": 0,
    "Absolute Eosinophil Count": 0,
    "Absolute Monocyte Count": 0,
    "Platelet Count": 0,
    "Erythrocyte Sedimentation Rate": 0,
    "Fasting Plasma Glucose": 0,
    "Glycated Hemoglobin": 0,
    "Triglycerides": 0,
    "Total Cholesterol": 0,
    "LDL Cholesterol": 0,
    "HDL Cholesterol": 0,
    "VLDL Cholesterol": 0,
    "Total Cholesterol / HDL Cholesterol Ratio": 0,
    "LDL Cholesterol / HDL Cholesterol Ratio": 0,
    "Total Bilirubin": 0,
    "Direct Bilirubin": 0,
    "Indirect Bilirubin": 0,
    "SGPT/ALT": 0,
    "SGOT/AST": 0,
    "Alkaline Phosphatase": 0,
    "Total Protein": 0,
    "Albumin": 0,
    "Globulin": 0,
    "Protein A/G Ratio": 0,
    "Gamma Glutamyl Transferase": 0,
    "Creatinine": 0,
    "e-GFR (Glomerular Filtration Rate)": 0,
    "Urea": 0,
    "Blood Urea Nitrogen": 0,
    "Uric Acid": 0,
    "T3 Total": 0,
    "T4 Total": 0,
    "TSH Ultrasensitive": 0,
    "Vitamin B12": 0,
    "25 (OH) Vitamin D2 (Ergocalciferol)": 0,
    "25 (OH) Vitamin D3 (Cholecalciferol)": 0,
    "Vitamin D Total (D2 + D3)": 0,
    "Iron": 0,
    "Total Iron Binding Capacity": 0,
    "Transferrin Saturation": 0
})
    advice = None

    if request.method == "POST":
        if "pdf_file" in request.files:
            pdf_file = request.files["pdf_file"]
            extracted_text = extract_text_from_pdf(pdf_file)
            values = extract_values(extracted_text)
            
            session['values'] = values
            session.modified = True  

            advice = give_health_advice(values)
            return render_template("results.html", values=values, advice=advice)

        elif request.form:
            updated_values = {}

            for test, original_value in values.items():
                updated_value = request.form.get(test)
                if updated_value:
                    updated_values[test] = float(updated_value)
                else:
                    updated_values[test] = original_value
            
            session['values'] = updated_values
            session.modified = True  
            advice = give_health_advice(updated_values)
            return render_template("results.html", values=updated_values, advice=advice)

    return render_template("index.html", values={}, advice=advice)

if __name__ == "__main__":
    app.run(debug=True)
